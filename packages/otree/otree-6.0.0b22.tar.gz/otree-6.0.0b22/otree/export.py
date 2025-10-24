import collections
import csv
import logging
import numbers
from collections import OrderedDict
from collections import defaultdict
from html import escape
from typing import List

from sqlalchemy.sql.functions import func

import otree
from otree.common import get_models_module, inspect_field_names, get_constants
from otree.common2 import TimeSpentRow, write_page_completion_buffer
from otree.currency import Currency, RealWorldCurrency
from otree.database import dbq, values_flat
from otree.models.group import BaseGroup
from otree.models.participant import Participant
from otree.models.player import BasePlayer
from otree.models.session import Session
from otree.models.subsession import BaseSubsession
from otree.models_concrete import PageTimeBatch
from otree.session import SessionConfig
from otree import settings

logger = logging.getLogger(__name__)


def get_fields_for_monitor():
    return _get_table_fields(Participant, for_export=False)


def get_fields_for_csv(Model):
    return _get_table_fields(Model, for_export=True)


def _get_table_fields(Model, custom_fields=None, for_export=False):

    if Model is Session:
        # only data export
        return [
            'code',
            'label',
            'mturk_HITId',
            'mturk_HITGroupId',
            'comment',
            'is_demo',
        ]

    if Model is Participant:
        if for_export:
            return [
                'id_in_session',
                'code',
                'label',
                '_is_bot',
                '_index_in_pages',
                '_max_page_index',
                '_current_app_name',
                # this could be confusing because it will be in every row,
                # even rows for different rounds.
                #'_round_number',
                '_current_page_name',
                'time_started_utc',
                'visited',
                'mturk_worker_id',
                'mturk_assignment_id',
                # last so that it will be next to payoff_plus_participation_fee
                'payoff',
            ]
        else:
            return [
                'id_in_session',
                'code',
                'label',
                '_current_page_of_total',
                '_current_app_name',
                '_round_number',
                '_current_page_name',
                '_presence',
                '_monitor_note_json',
                '_last_page_timestamp',
            ]

    specs = [
        ('player', BasePlayer, ['id_in_group', 'role', 'payoff']),
        ('group', BaseGroup, ['id_in_subsession']),
        ('subsession', BaseSubsession, ['round_number']),
    ]

    for model_name_lower, BaseModel, fields in specs:
        if issubclass(Model, BaseModel):
            if custom_fields:
                subclass_fields = custom_fields.get(model_name_lower, [])
            else:
                subclass_fields = [
                    f
                    for f in inspect_field_names(Model)
                    if f not in fields and f not in dir(BaseModel)
                ]
            fields = list(dict.fromkeys(fields + subclass_fields))
            if for_export:
                return fields
            return fields


def sanitize_for_csv(value):
    if value is None:
        return ''
    if value is True:
        return 1
    if value is False:
        return 0
    if isinstance(value, (Currency, RealWorldCurrency)):
        # not decimal since that can't be json serialized
        return float(value)
    if isinstance(value, numbers.Number):
        return value
    # Only convert to string and replace if needed
    if isinstance(value, str):
        if '\n' in value or '\r' in value:
            return value.replace('\n', ' ').replace('\r', ' ')
        return value
    return value


def tweak_player_values_dict(player: dict, group_id_in_subsession=None):
    '''because these are actually properties, the DB field starts with _.'''
    player['payoff'] = player['_payoff']
    player['role'] = player['_role']
    if group_id_in_subsession:
        player['group'] = group_id_in_subsession


_MAX_LENGTH_FOR_LIVE_UPDATE = 30


def sanitize_for_live_update(value):
    value = sanitize_for_csv(value)
    if isinstance(value, str):
        value = escape(value)
        if len(value) > _MAX_LENGTH_FOR_LIVE_UPDATE:
            value = value[:_MAX_LENGTH_FOR_LIVE_UPDATE] + '…'
    return value


def get_installed_apps_with_data() -> list:
    """
    this is just important for devserver.
    on prodserver there should never be an inconsistency between
    currently installed apps and apps with data, because you resetdb each time
    """
    app_names_with_data = set()
    for session in dbq(Session):
        for app_name in session.config['app_sequence']:
            if app_name in settings.OTREE_APPS:
                app_names_with_data.add(app_name)
    return list(sorted(app_names_with_data))


def _get_best_app_order(sessions):
    # heuristic to get the most relevant order of apps
    app_sequences = collections.Counter()
    for session in sessions:
        # we loaded the config earlier
        app_sequence = session.config['app_sequence']
        app_sequences[tuple(app_sequence)] += session.num_participants
    most_common_app_sequence = app_sequences.most_common(1)[0][0]

    app_names_with_data = get_installed_apps_with_data()

    apps_not_in_popular_sequence = [
        app for app in app_names_with_data if app not in most_common_app_sequence
    ]

    return list(most_common_app_sequence) + apps_not_in_popular_sequence


def get_rows_for_wide_csv(session_code):
    if session_code:
        sessions = [Session.objects_get(code=session_code)]
    else:
        sessions = dbq(Session).order_by('id').all()
    session_fields = get_fields_for_csv(Session)
    participant_fields = get_fields_for_csv(Participant)

    session_ids = [session.id for session in sessions]
    pps = (
        Participant.objects_filter(Participant.session_id.in_(session_ids))
        .order_by(Participant.id)
        .all()
    )
    session_cache = {row.id: row for row in sessions}

    session_config_fields = ['name']
    seen = {'name'}
    for session in sessions:
        for field_name in SessionConfig(session.config).editable_fields():
            if field_name not in seen:
                session_config_fields.append(field_name)
                seen.add(field_name)

    if not pps:
        # 1 empty row
        return [[]]

    header_row = [f'participant.{fname}' for fname in participant_fields]
    header_row += [f'participant.{fname}' for fname in settings.PARTICIPANT_FIELDS]
    header_row += [f'session.{fname}' for fname in session_fields]
    header_row += [f'session.config.{fname}' for fname in session_config_fields]
    header_row += [f'session.{fname}' for fname in settings.SESSION_FIELDS]
    rows = [header_row]

    for pp in pps:
        session = session_cache[pp.session_id]
        row = [getattr(pp, fname) for fname in participant_fields]
        row += [pp.vars.get(fname, None) for fname in settings.PARTICIPANT_FIELDS]
        row += [getattr(session, fname) for fname in session_fields]
        row += [session.config.get(fname) for fname in session_config_fields]
        row += [session.vars.get(fname, None) for fname in settings.SESSION_FIELDS]
        rows.append(row)

    order_of_apps = _get_best_app_order(sessions)

    rounds_per_app = OrderedDict()
    for app_name in order_of_apps:
        try:
            models_module = get_models_module(app_name)
        except ModuleNotFoundError:
            # this should only happen with devserver because on production server,
            # you would need to resetdb after renaming an app.
            logger.warning(
                f'Cannot export data for app {app_name}, which existed when the session was run '
                f'but no longer exists.'
            )
            continue

        highest_round_number = dbq(
            func.max(models_module.Subsession.round_number)
        ).scalar()

        if highest_round_number is not None:
            rounds_per_app[app_name] = highest_round_number

    for app_name in rounds_per_app:
        app_rows = get_rows_for_wide_csv_app(
            app_name, rounds_per_app[app_name], sessions
        )
        for i in range(len(rows)):
            rows[i].extend(app_rows[i])

    return [[sanitize_for_csv(v) for v in row] for row in rows]


def get_rows_for_wide_csv_app(app_name, max_round_number, sessions: List[Session]):
    """Optimized version that loads all rounds for an app at once"""
    models_module = otree.common.get_models_module(app_name)
    Player: BasePlayer = models_module.Player
    Group: BaseGroup = models_module.Group
    Subsession: BaseSubsession = models_module.Subsession
    pfields = get_fields_for_csv(Player)
    gfields = get_fields_for_csv(Group)
    sfields = get_fields_for_csv(Subsession)

    # Load ALL data for this app at once
    all_groups = Group.values_dicts()
    groups_by_round = defaultdict(dict)
    for g in all_groups:
        groups_by_round[g['round_number']][g['id']] = g

    session_ids = [s.id for s in sessions]
    all_subsessions = Subsession.values_dicts()
    subsessions_by_session_round = {}
    for s in all_subsessions:
        subsessions_by_session_round[(s['session_id'], s['round_number'])] = s

    all_players = Player.values_dicts(order_by='id')
    players_by_subsession = defaultdict(list)
    for p in all_players:
        players_by_subsession[p['subsession_id']].append(p)

    # Now build rows for each round
    all_app_rows = []
    for round_number in range(1, max_round_number + 1):
        rows = []
        group_cache = groups_by_round.get(round_number, {})

        # Build header
        header_row = []
        for model_name, fields in [
            ('player', pfields),
            ('group', gfields),
            ('subsession', sfields),
        ]:
            for fname in fields:
                header_row.append(f'{app_name}.{round_number}.{model_name}.{fname}')
        rows.append(header_row)
        empty_row = ['' for _ in range(len(header_row))]

        # Process each session
        for session in sessions:
            subsession = subsessions_by_session_round.get((session.id, round_number))
            if not subsession:
                subsession_rows = [empty_row for _ in range(session.num_participants)]
            else:
                players = players_by_subsession.get(subsession['id'], [])

                if len(players) != session.num_participants:
                    msg = (
                        f"Session {session.code} has {session.num_participants} participants, "
                        f"but round {round_number} of app '{app_name}' "
                        f"has {len(players)} players. The number of players in the subsession "
                        "should always match the number of players in the session. "
                        "Please report this issue and then reset the database."
                    )
                    raise AssertionError(msg)

                subsession_rows = []
                for player in players:
                    group = group_cache[player['group_id']]
                    tweak_player_values_dict(player)

                    row = [player[fname] for fname in pfields]
                    row += [group[fname] for fname in gfields]
                    row += [subsession[fname] for fname in sfields]

                    subsession_rows.append(row)
            rows.extend(subsession_rows)
        all_app_rows.append(rows)

    # Transpose: convert from list of (rounds × rows) to list of (rows × rounds)
    # all_app_rows structure: [[round1_header, round1_data_row1, round1_data_row2, ...], [round2_header, round2_data_row1, ...], ...]
    # We want: [all_headers_combined, all_data_row1_combined, all_data_row2_combined, ...]
    if not all_app_rows:
        return []

    num_rows = len(all_app_rows[0])
    transposed = [[] for _ in range(num_rows)]

    for round_rows in all_app_rows:
        # Each round_rows has: [header, data_row_1, data_row_2, ...]
        # We skip the header (index 0) for data rows, only concatenate headers at index 0
        for i in range(len(round_rows)):
            if i == 0:
                # This is a header row - extend with this round's header
                transposed[0].extend(round_rows[0])
            else:
                # This is a data row - extend with this round's data (skip header)
                transposed[i].extend(round_rows[i])

    return transposed


def get_rows_for_csv(app_name, session_code=None):
    # need to use app_name and not app_label because the app might have been
    # removed from SESSION_CONFIGS
    models_module = otree.common.get_models_module(app_name)
    Player = models_module.Player
    Group = models_module.Group
    Subsession = models_module.Subsession

    columns_for_models = {
        Model.__name__.lower(): get_fields_for_csv(Model)
        for Model in [Player, Group, Subsession, Participant, Session]
    }

    if session_code:
        session_ids = [Session.objects_get(code=session_code).id]
    else:
        session_ids = values_flat(dbq(Subsession), Subsession.session_id)

    # Helper to filter by session
    def values_for_session(Model):
        if session_ids:
            return Model.values_dicts(Model.session_id.in_(session_ids))
        return Model.values_dicts()

    players = list(values_for_session(Player))
    # Sort after filtering to maintain order
    players.sort(key=lambda p: p['id'])

    value_dicts = dict(
        group={row['id']: row for row in values_for_session(Group)},
        subsession={row['id']: row for row in values_for_session(Subsession)},
        participant={row['id']: row for row in values_for_session(Participant)},
        session={
            row['id']: row for row in Session.values_dicts(Session.id.in_(session_ids))
        },
    )

    model_order = ['participant', 'player', 'group', 'subsession', 'session']

    # header row
    rows = [[f'{m}.{col}' for m in model_order for col in columns_for_models[m]]]

    for player in players:
        tweak_player_values_dict(player)
        row = []

        for model_name in model_order:
            if model_name == 'player':
                obj = player
            else:
                obj = value_dicts[model_name][player[f'{model_name}_id']]
            for colname in columns_for_models[model_name]:
                row.append(sanitize_for_csv(obj[colname]))
        rows.append(row)

    return rows


def get_rows_for_monitor(participants) -> list:
    field_names = get_fields_for_monitor()
    callable_fields = {'_numeric_label', '_current_page_of_total'}
    rows = []
    for pp in participants:
        row = {}
        for field_name in field_names:
            value = getattr(pp, field_name)
            if field_name in callable_fields:
                value = value()
            row[field_name] = value
        row['id_in_session'] = pp.id_in_session
        row['status'] = pp.status
        if pp.is_on_wait_page:
            if pp._waitpage_is_connected:
                if pp._waitpage_tab_hidden:
                    icon = '🟡'
                else:
                    icon = '🟢'
            else:
                icon = '⚪'
            row['_presence'] = icon
        rows.append(row)
    return rows


def get_rows_for_data_tab(session):
    for app_name in session.config['app_sequence']:
        yield from get_rows_for_data_tab_app(session, app_name)


def get_fields_for_data_tab(app_name):
    C = get_constants(app_name)
    custom_fields = getattr(C, ADMIN_VIEW_FIELDS, {})
    parse_custom_fields(custom_fields)
    models_module = get_models_module(app_name)
    for Model in [models_module.Player, models_module.Group, models_module.Subsession]:
        yield _get_table_fields(Model, for_export=False, custom_fields=custom_fields)


def parse_custom_fields(custom_fields):
    for k in custom_fields:
        if k not in ['player', 'group', 'subsession']:
            msg = f"{ADMIN_VIEW_FIELDS} dict contains invalid key: {k}. "
            raise Exception(msg)
    return custom_fields


ADMIN_VIEW_FIELDS = 'ADMIN_VIEW_FIELDS'


def get_rows_for_data_tab_app(session, app_name):
    models_module = get_models_module(app_name)
    Player = models_module.Player
    Group = models_module.Group
    Subsession = models_module.Subsession
    C = get_constants(app_name)
    custom_fields = getattr(C, ADMIN_VIEW_FIELDS, None)
    pfields, gfields, sfields = get_fields_for_data_tab(app_name)

    players = Player.values_dicts(session=session, order_by='id')

    # Load just participant id and label
    participant_labels = {
        p_id: label
        for p_id, label in dbq(Participant)
        .filter(Participant.session_id == session.id)
        .with_entities(Participant.id, Participant.label)
        .all()
    }

    players_by_round = defaultdict(list)
    for p in players:
        players_by_round[p['round_number']].append(p)

    groups = {g['id']: g for g in Group.values_dicts(session=session)}
    subsessions = {s['id']: s for s in Subsession.values_dicts(session=session)}

    for round_number in range(1, len(subsessions) + 1):
        table = []
        for p in players_by_round[round_number]:
            participant_label = participant_labels[p['participant_id']]
            g = groups[p['group_id']]
            tweak_player_values_dict(p, g['id_in_subsession'])
            s = subsessions[p['subsession_id']]
            try:
                row = (
                    [participant_label]
                    + [p[fname] for fname in pfields]
                    + [g[fname] for fname in gfields]
                    + [s[fname] for fname in sfields]
                )
            except KeyError as exc:
                if custom_fields:
                    msg = f"{ADMIN_VIEW_FIELDS}: field {repr(exc.args[0])}"
                    raise Exception(msg) from None
                raise exc
            table.append([sanitize_for_live_update(v) for v in row])
        yield table


def export_wide(fp, session_code=None):
    rows = get_rows_for_wide_csv(session_code=session_code)
    _export_csv(fp, rows)


def export_app(app_name, fp, session_code=None):
    rows = get_rows_for_csv(app_name, session_code=session_code)
    _export_csv(fp, rows)


from sqlalchemy.orm import joinedload


def get_custom_export_functions(app_name):
    """Get all custom export functions from an app's models module.

    Returns a dict mapping function names to functions.
    Functions that start with 'custom_export' are included.
    """
    models_module = get_models_module(app_name)
    custom_exports = {}

    for attr_name in dir(models_module):
        if attr_name.startswith('custom_export'):
            attr = getattr(models_module, attr_name)
            if callable(attr):
                custom_exports[attr_name] = attr

    print('custom_exports:', app_name, custom_exports)
    return custom_exports


def custom_export_app(app_name, fp, session_code=None, function_name='custom_export'):

    models_module = get_models_module(app_name)
    Player = models_module.Player
    query = dbq(Player).order_by('id')

    if session_code:
        session = Session.objects_get(code=session_code)
        query = query.filter(Player.session_id == session.id)

    qs = list(
        query.options(
            joinedload(Player.participant, innerjoin=True),
            joinedload(Player.group, innerjoin=True),
            joinedload(Player.subsession, innerjoin=True),
            joinedload(Player.session, innerjoin=True),
        )
    )
    for player in qs:
        # need this to query null values
        player._is_frozen = False

    # Get the specific export function
    export_func = getattr(models_module, function_name, None)
    if not export_func:
        raise ValueError(
            f"Export function '{function_name}' not found in app '{app_name}'"
        )

    rows = export_func(qs)
    str_rows = []
    for row in rows:
        str_rows.append([sanitize_for_csv(ele) for ele in row])
    _export_csv(fp, str_rows)


def _export_csv(fp, rows):
    writer = csv.writer(fp)
    writer.writerows(rows)


def export_page_times(fp):
    write_page_completion_buffer()
    batches = values_flat(dbq(PageTimeBatch).order_by('id'), PageTimeBatch.text)
    fp.write(','.join(TimeSpentRow.__annotations__.keys()) + '\n')
    for batch in batches:
        fp.write(batch)


def export_chat(fp, session_code=None):
    from otree.models_concrete import ChatMessage

    column_names = [
        'session_code',
        'id_in_session',
        'participant_code',
        'channel',
        'nickname',
        'body',
        'timestamp',
    ]

    query = dbq(ChatMessage).join(Participant).order_by(ChatMessage.timestamp)

    if session_code:
        query = query.filter(Participant._session_code == session_code)

    rows = query.with_entities(
        Participant._session_code,
        Participant.id_in_session,
        Participant.code,
        ChatMessage.channel,
        ChatMessage.nickname,
        ChatMessage.body,
        ChatMessage.timestamp,
    )

    writer = csv.writer(fp)
    writer.writerows([column_names])
    writer.writerows(rows)


BOM = '\ufeff'
