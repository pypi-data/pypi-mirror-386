from contextlib import nullcontext
import asyncio
import datetime
import io
import logging
import traceback
import urllib.parse
from starlette.endpoints import WebSocketEndpoint
from starlette.websockets import WebSocket
from starlette.datastructures import FormData
import otree.bots.browser
import otree.channels.utils as channel_utils
import otree.session
from otree import settings
from otree.channels.utils import get_chat_group, channel_layer
from otree.common import (
    get_models_module,
    GlobalState,
    signer_unsign,
    participants_with_updated_presence_icons,
)
from otree.currency import json_dumps
from otree.database import NoResultFound
from otree.database import session_scope, db
from otree.database import dbq
from otree.export import export_wide, export_app, custom_export_app, BOM
from otree.live import (
    live_payload_function,
    live_method_is_async,
    get_participant_scoped_lock,
)
from otree.models import Participant, Session
from otree.models_concrete import (
    CompletedGroupWaitPage,
    CompletedSubsessionWaitPage,
    CompletedGBATWaitPage,
    ChatMessage,
)
from otree.room import ROOM_DICT, LabelRoom, NoLabelRoom
from otree.session import SESSION_CONFIGS_DICT
from otree.views.admin import CreateSessionForm
from otree.common import AUTH_COOKIE_NAME, AUTH_COOKIE_VALUE
from otree.middleware import lock2
from otree.trials import trial_payload_function

# lock2 = asyncio.Lock()

logger = logging.getLogger(__name__)

SESSION_READY_PAYLOAD = {'status': 'session_ready'}


class InvalidWebSocketParams(Exception):
    '''exception to raise when websocket params are invalid'''


class _OTreeAsyncJsonWebsocketConsumer(WebSocketEndpoint):
    """
    This is not public API, might change at any time.
    """

    encoding = 'json'
    websocket: WebSocket
    groups: list
    _requires_login = False
    lock = lock2

    def clean_kwargs(self, **kwargs):
        '''
        subclasses should override if the route accesses query params.
        otherwise, this just passes the route kwargs as is (usually there is just one).
        The output of this method is passed to self.group_name(), self.post_connect,
        and self.pre_disconnect, so within each class, all 3 of those methods must
        accept the same args (or at least take a **kwargs wildcard, if the args aren't used)
        '''
        return kwargs

    def group_name(self, **kwargs):
        raise NotImplementedError()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cleaned_kwargs = self.clean_kwargs(**self.scope['path_params'])
        group_name = self.group_name(**self.cleaned_kwargs)
        self.groups = [group_name] if group_name else []

    def _is_unauthorized(self):
        return

    async def on_connect(self, websocket: WebSocket) -> None:
        # patch the instance
        websocket.send = channel_utils.wrap_websocket_send(websocket.send)
        # need to accept no matter what, so we can at least send
        # an error message
        await websocket.accept()

        if (
            self._requires_login
            and not websocket.session.get(AUTH_COOKIE_NAME) == AUTH_COOKIE_VALUE
        ):
            msg = 'rejected un-authenticated access to websocket path {}'.format(
                self.scope['path']
            )
            logger.error(msg)
            await websocket.close(code=1008)
            return

        self.websocket = websocket
        async with self.lock:
            with session_scope():
                await self.post_connect(**self.cleaned_kwargs)
        for group in self.groups:
            channel_layer.add(group, websocket)

    async def post_connect(self, **kwargs):
        pass

    async def on_disconnect(self, websocket: WebSocket, close_code: int):
        async with self.lock:
            with session_scope():
                await self.pre_disconnect(**self.cleaned_kwargs)
        for group in self.groups:
            channel_layer.discard(group, websocket)

    async def pre_disconnect(self, **kwargs):
        pass

    async def on_receive(self, websocket: WebSocket, data):
        async with self.lock:
            with session_scope():
                await self.post_receive_json(data, **self.cleaned_kwargs)

    async def post_receive_json(self, content, **kwargs):
        pass

    async def send_json(self, data):
        await self.websocket.send_json(data)


class BaseWaitPage(_OTreeAsyncJsonWebsocketConsumer):
    kwarg_names: list
    participant_id: int

    def clean_kwargs(self):
        d = parse_querystring(self.scope['query_string'])
        kwargs = {}
        for k in self.kwarg_names:
            kwargs[k] = int(d[k])
        return kwargs

    async def pre_disconnect(self, participant_id, **kwargs):
        self.mark_waitpage_connected_or_not(
            is_connected=False, session_pk=kwargs['session_pk']
        )

    async def post_receive_json(self, content, **kwargs):
        if 'tab_hidden' in content:
            self.mark_waitpage_tab_hidden_or_not(
                tab_hidden=content['tab_hidden'], session_pk=kwargs['session_pk']
            )

    def mark_waitpage_connected_or_not(self, is_connected, session_pk):
        Participant.objects_filter(id=self.participant_id).update(
            {Participant._waitpage_is_connected: is_connected}
        )
        participants_with_updated_presence_icons[session_pk].add(self.participant_id)

    def mark_waitpage_tab_hidden_or_not(self, tab_hidden, session_pk):
        Participant.objects_filter(id=self.participant_id).update(
            {Participant._waitpage_tab_hidden: tab_hidden}
        )
        participants_with_updated_presence_icons[session_pk].add(self.participant_id)


class WSSubsessionWaitPage(BaseWaitPage):
    kwarg_names = ('session_pk', 'page_index', 'participant_id')

    def group_name(self, session_pk, page_index, participant_id):
        return channel_utils.subsession_wait_page_name(session_pk, page_index)

    def completion_exists(self, **kwargs):
        return CompletedSubsessionWaitPage.objects_exists(**kwargs)

    async def post_connect(self, session_pk, page_index, participant_id):
        self.participant_id = participant_id
        if self.completion_exists(page_index=page_index, session_id=session_pk):
            await self.websocket.send_json({'status': 'ready'})
        self.mark_waitpage_connected_or_not(session_pk=session_pk, is_connected=True)


class WSGroupWaitPage(BaseWaitPage):

    kwarg_names = WSSubsessionWaitPage.kwarg_names + ('group_id',)

    def group_name(self, session_pk, page_index, group_id, participant_id):
        return channel_utils.group_wait_page_name(session_pk, page_index, group_id)

    def completion_exists(self, **kwargs):
        return CompletedGroupWaitPage.objects_exists(**kwargs)

    async def post_connect(self, session_pk, page_index, group_id, participant_id):
        self.participant_id = participant_id
        if self.completion_exists(
            page_index=page_index, group_id=group_id, session_id=session_pk
        ):
            await self.websocket.send_json({'status': 'ready'})
        self.mark_waitpage_connected_or_not(session_pk=session_pk, is_connected=True)


class WSGroupByArrivalTime(BaseWaitPage):

    app_name: str
    player_id: int

    def clean_kwargs(self):
        d = parse_querystring(self.scope['query_string'])
        return {
            'app_name': d['app_name'],
            'session_pk': int(d['session_pk']),
            'participant_id': int(d['participant_id']),
            'page_index': int(d['page_index']),
            'player_id': int(d['player_id']),
        }

    def group_name(self, app_name, player_id, page_index, session_pk, participant_id):
        gn = channel_utils.gbat_group_name(session_pk, page_index)
        return gn

    def is_ready(self, *, app_name, player_id, page_index, session_pk):
        models_module = get_models_module(app_name)
        Player = models_module.Player
        Group = models_module.Group

        [group_id_in_subsession] = (
            dbq(Player)
            .join(Group)
            .filter(Player.id == player_id)
            .with_entities(Group.id_in_subsession)
            .one()
        )

        return CompletedGBATWaitPage.objects_exists(
            page_index=page_index,
            id_in_subsession=group_id_in_subsession,
            session_id=session_pk,
        )

    def mark_gbat_is_connected(self, is_connected):
        Participant.objects_filter(id=self.participant_id).update(
            {Participant._waitpage_is_connected: is_connected}
        )

    async def post_connect(
        self, app_name, player_id, page_index, session_pk, participant_id
    ):
        self.app_name = app_name
        self.player_id = player_id
        self.participant_id = participant_id
        try:
            is_ready = self.is_ready(
                app_name=app_name,
                player_id=player_id,
                page_index=page_index,
                session_pk=session_pk,
            )
        except NoResultFound:
            # if session was deleted
            pass
        else:
            if is_ready:
                await self.websocket.send_json({'status': 'ready'})
        # note-to-self
        # previously we were just marking connected=True in the dispatch() method
        # of the view, and connected=False with WS disconnect.
        # but the flaw is that WS disconnect seems to fire AFTER dispatch
        # so add some redundancy here because i'm pretty sure connect() must run
        # after disconnect() of the previous page load.
        self.mark_waitpage_connected_or_not(session_pk=session_pk, is_connected=True)


class LiveConsumer(_OTreeAsyncJsonWebsocketConsumer):
    def group_name(self, session_code, page_index, participant_code, **kwargs):
        return channel_utils.live_group(session_code, page_index, participant_code)

    def clean_kwargs(self):
        return parse_querystring(self.scope['query_string'])

    async def on_receive(self, websocket: WebSocket, data):
        cleaned_kwargs = self.clean_kwargs()
        participant_code = cleaned_kwargs['participant_code']
        if live_method_is_async(participant_code):
            async with get_participant_scoped_lock(participant_code):
                # Create isolated session for this async task.
                # With contextvars, each async task gets its own context automatically.
                with session_scope():
                    await self.post_receive_json(data, **cleaned_kwargs)
        else:
            async with lock2:
                with session_scope():
                    await self.post_receive_json(data, **cleaned_kwargs)

    def browser_bot_exists(self, participant_code):
        # for browser bots, block liveSend calls that get triggered on page load.
        # instead, everything must happen through call_live_method in a controlled way.
        return Participant.objects_exists(code=participant_code, is_browser_bot=True)

    async def post_receive_json(self, content, participant_code, page_name, **kwargs):
        if self.browser_bot_exists(participant_code):
            return
        try:
            await live_payload_function(
                participant_code=participant_code, page_name=page_name, payload=content
            )
        except Exception as e:
            [group] = self.groups
            # f'Error in live_method. See server logs for details.'
            payload = {
                'otree_success': False,
                'live_method_payload': None,
            }
            await channel_utils.group_send(group=group, data=payload)
            # or should we do logger.exception? maybe that will stop the extra
            # websockets.exceptions.ConnectionClosedError: sent 1000 (OK); no close frame received
            logger.exception(repr(e))

    @classmethod
    async def encode_json(cls, content):
        return json_dumps(content)


class DetectAutoAdvance(_OTreeAsyncJsonWebsocketConsumer):
    def clean_kwargs(self):
        d = parse_querystring(self.scope['query_string'])
        return {
            'participant_code': d['participant_code'],
            'page_index': int(d['page_index']),
        }

    def group_name(self, page_index, participant_code):
        return channel_utils.auto_advance_group(participant_code)

    def page_should_be_on(self, participant_code):
        try:
            [res] = (
                Participant.objects_filter(code=participant_code)
                .with_entities('_index_in_pages')
                .one()
            )
            return res
        except NoResultFound:
            return

    async def post_connect(self, page_index, participant_code):

        # note-to-self
        # in case message was sent before this web socket connects
        page_should_be_on = self.page_should_be_on(participant_code)
        if page_should_be_on is None:
            await self.send_json({'error': 'Participant not found in database.'})
        elif page_should_be_on > page_index:
            await self.send_json({'auto_advanced': True})


class BaseCreateSession(_OTreeAsyncJsonWebsocketConsumer):
    lock = nullcontext()

    def group_name(self, **kwargs):
        return None

    async def send_response_to_browser(self, event: dict):
        raise NotImplemented

    async def send_progress_message(self, message: str):
        raise NotImplemented

    async def create_session_then_send_start_link(
        self, use_browser_bots, **session_kwargs
    ):
        loop = asyncio.get_event_loop()

        def progress_message_fxn(msg):
            # Schedule from sync thread - need thread-safe version
            asyncio.run_coroutine_threadsafe(
                self.send_progress_message(msg),
                loop
            )

        def create_session_in_thread():
            # Worker thread needs its own DB session since it runs in a different context
            with session_scope():
                session = otree.session.create_session_traceback_wrapper(
                    progress_message_fxn=progress_message_fxn, **session_kwargs
                )
                # Return necessary data since the session object will be detached once we exit
                return {
                    'id': session.id,
                    'code': session.code,
                    'is_demo': session.is_demo,
                    'is_mturk': session.is_mturk,
                }

        try:
            # Run blocking session creation in thread pool to avoid blocking the event loop.
            # This allows progress messages to be sent in real-time and other requests to be handled.
            session_data = await loop.run_in_executor(None, create_session_in_thread)

            if use_browser_bots:
                otree.bots.browser.initialize_session(
                    session_pk=session_data['id'], case_number=None
                )
            # the "elif" is because if it uses browser bots, then exogenous data is mocked
            # as part of run_bots.
            # 2020-07-07: this queries the DB, shouldn't i use database_sync_to_async?
            # i don't get any error
            elif session_data['is_demo']:
                # Re-fetch the session in the main thread's context
                from otree.models import Session
                session = Session.objects_get(id=session_data['id'])
                session.mock_exogenous_data()
        except Exception as e:
            if isinstance(e, otree.session.CreateSessionError):
                e = e.__cause__
            traceback_str = ''.join(
                traceback.format_exception(type(e), e, e.__traceback__)
            )
            await self.send_response_to_browser(
                dict(error=f'Failed to create session: {e}', traceback=traceback_str)
            )

            # i used to do "raise" here.
            # if I raise, then in non-demo sessions, the traceback is not displayed
            # as it should be.
            # Instead, there is an error
            # "Server error occurred, check Sentry or the logs"
            # I guess the websocket gets cut off? that's also why my test_traceback test was failing.
            # why did I use raise in the first place?
            # was it just so the traceback would go to the console or Sentry?
            # if we show it in the browser, there's no need to show it anywhere else, right?
            # maybe it was just a fallback in case the TB was truncated?
            # or because the traceback should not be shown outside of DEBUG mode
        else:
            from otree.asgi import reverse

            session_home_view = (
                'MTurkCreateHIT' if session_data['is_mturk'] else 'SessionStartLinks'
            )

            await self.send_response_to_browser(
                {'session_url': reverse(session_home_view, code=session_data['code'])}
            )


class WSCreateDemoSession(BaseCreateSession):
    async def send_response_to_browser(self, event: dict):
        await self.send_json(event)

    async def send_progress_message(self, message: str):
        print("send_json", message)
        await self.send_json({'progress': message})

    async def post_receive_json(self, form_data: dict):
        session_config_name = form_data['session_config']
        config = SESSION_CONFIGS_DICT.get(session_config_name)
        if not config:
            msg = f'Session config "{session_config_name}" does not exist.'
            await self.send_json({'validation_errors': msg})
            return

        num_participants = config['num_demo_participants']
        use_browser_bots = config.get('use_browser_bots', False)

        await self.create_session_then_send_start_link(
            session_config_name=session_config_name,
            use_browser_bots=use_browser_bots,
            num_participants=num_participants,
            is_demo=True,
        )


class WSCreateSession(BaseCreateSession):
    def group_name(self, **kwargs):
        return 'create_session'

    async def send_progress_message(self, message: str):
        print("send_json", message)

        [group] = self.groups
        await channel_utils.group_send(group=group, data={'progress': message})

    async def post_receive_json(self, form_data: dict):
        # when i passed in data= as a dict, InputRequired failed.
        # i guess it looks in formdata to see if an input was made.
        form = CreateSessionForm(formdata=FormData(form_data))
        if not form.validate():
            await self.send_json({'validation_errors': form.errors})
            return

        session_config_name = form.session_config.data
        is_mturk = form.is_mturk.data

        config = SESSION_CONFIGS_DICT[session_config_name]

        num_participants = form.num_participants.data
        if is_mturk:
            num_participants *= settings.MTURK_NUM_PARTICIPANTS_MULTIPLE

        modified_session_config_fields = {}

        for field in config.editable_fields():
            html_field_name = config.html_field_name(field)
            old_value = config[field]

            # note-to-self
            # to allow concise unit tests, we can simply omit any fields we don't
            # want to change. this allows us to write more concise
            # unit tests.
            # EXCEPT for boolean fields -- omitting
            # it means we turn it off.
            # ideally we could interpret omitted boolean fields as unchanged
            # and False as unchecked, but HTML & serializeArray omits
            # unchecked checkboxes from form data.

            if isinstance(old_value, bool):
                new_value = bool(form_data.get(html_field_name))
                if old_value != new_value:
                    modified_session_config_fields[field] = new_value
            else:
                new_value_raw = form_data.get(html_field_name, '')
                if new_value_raw != '':
                    # don't use isinstance because that will catch bool also
                    if type(old_value) is int:
                        # in case someone enters 1.0 instead of 1
                        new_value = int(float(new_value_raw))
                    else:
                        new_value = type(old_value)(new_value_raw)
                    if old_value != new_value:
                        modified_session_config_fields[field] = new_value

        use_browser_bots = modified_session_config_fields.get(
            'use_browser_bots', config.get('use_browser_bots', False)
        )

        # if room_name is missing, it will be empty string
        room_name = form.room_name.data or None

        await self.create_session_then_send_start_link(
            session_config_name=session_config_name,
            num_participants=num_participants,
            is_demo=False,
            is_mturk=is_mturk,
            modified_session_config_fields=modified_session_config_fields,
            use_browser_bots=use_browser_bots,
            room_name=room_name,
        )

        if room_name:
            await channel_utils.group_send(
                group=channel_utils.room_participants_group_name(room_name),
                data=SESSION_READY_PAYLOAD,
            )

    async def send_response_to_browser(self, event: dict):
        '''
        Send to a group instead of the channel only,
        because if the websocket disconnects during creation of a large session,
        (due to temporary network error, etc, or Heroku H15, 55 seconds without ping)
        the user could be stuck on "please wait" forever.
        the downside is that if two admins create sessions around the same time,
        your page could automatically redirect to the other admin's session.
        '''
        [group] = self.groups
        await channel_utils.group_send(group=group, data=event)


class WSSessionMonitor(_OTreeAsyncJsonWebsocketConsumer):
    def group_name(self, code):
        return channel_utils.session_monitor_group_name(code)

    def get_initial_data(self, code):
        participants = Participant.objects_filter(_session_code=code, visited=True)
        return otree.export.get_rows_for_monitor(participants)

    async def post_connect(self, code):
        initial_data = self.get_initial_data(code=code)
        await self.send_json(dict(rows=initial_data))


class WSRoomAdmin(_OTreeAsyncJsonWebsocketConsumer):
    def group_name(self, room_name):
        return channel_utils.room_admin_group_name(room_name)

    async def post_connect(self, room_name):
        room = ROOM_DICT[room_name]

        msg = dict(status='init')
        if room.has_participant_labels:
            room: LabelRoom
            msg['present_labels'] = list(dict.fromkeys(sorted(room.present_list)))
        else:
            room: NoLabelRoom
            msg['present_count'] = room.present_count
        await self.send_json(msg)


class WSRoomParticipant(_OTreeAsyncJsonWebsocketConsumer):
    def clean_kwargs(self):
        d = parse_querystring(self.scope['query_string'])
        d.setdefault('participant_label', '')
        return d

    def group_name(self, room_name, participant_label, tab_unique_id):
        return channel_utils.room_participants_group_name(room_name)

    async def post_connect(self, room_name, participant_label, tab_unique_id):
        if not room_name in ROOM_DICT:
            return
        room = ROOM_DICT[room_name]
        # add it even if there is a session, because in pre_disconnect we do
        # presence_remove, so we need to be consistent.
        room.presence_add(participant_label)
        if room.has_session():
            await self.send_json(SESSION_READY_PAYLOAD)
        else:
            await channel_utils.group_send(
                group=channel_utils.room_admin_group_name(room_name),
                data={'status': 'add_participant', 'participant': participant_label},
            )

    async def pre_disconnect(self, room_name, participant_label, tab_unique_id):
        room = ROOM_DICT[room_name]
        event = {'status': 'remove_participant', 'participant': participant_label}
        room.presence_remove(participant_label)

        admin_group = channel_utils.room_admin_group_name(room_name)

        await channel_utils.group_send(group=admin_group, data=event)


class WSBrowserBotsLauncher(_OTreeAsyncJsonWebsocketConsumer):

    # OK to be unrestricted because this websocket doesn't create the session,
    # or do anything sensitive.

    def group_name(self, session_code):
        return channel_utils.browser_bots_launcher_group(session_code)


class WSBrowserBot(_OTreeAsyncJsonWebsocketConsumer):
    def group_name(self):
        return 'browser_bot_wait'

    async def post_connect(self):
        if GlobalState.browser_bots_launcher_session_code:
            await self.send_json(SESSION_READY_PAYLOAD)


class WSChat(_OTreeAsyncJsonWebsocketConsumer):
    def clean_kwargs(self):
        d = parse_querystring(self.scope['query_string'])
        return {
            'channel': signer_unsign(d['channel']),
            'participant_id': int(signer_unsign(d['participant_id'])),
        }

    def group_name(self, channel, participant_id):
        return get_chat_group(channel)

    def _get_history(self, channel):
        fields = ['nickname', 'body', 'participant_id']
        rows = list(
            ChatMessage.objects_filter(channel=channel)
            .order_by('timestamp')
            .values(*fields)
        )
        return [dict(zip(fields, row)) for row in rows]

    async def post_connect(self, channel, participant_id):

        history = self._get_history(channel=channel)

        # Convert ValuesQuerySet to list
        # but is it ok to send a list (not a dict) as json?
        await self.send_json(history)

    async def post_receive_json(self, content, channel, participant_id):

        # note-to-self
        # in the Channels docs, the example has a separate msg_consumer
        # channel, so this can be done asynchronously.
        # but i think the perf is probably good enough.
        # moving into here for simplicity, especially for testing.
        nickname_signed = content['nickname_signed']
        nickname = signer_unsign(nickname_signed)
        body = content['body']

        chat_message = dict(nickname=nickname, body=body, participant_id=participant_id)

        [group] = self.groups
        await channel_utils.group_send(group=group, data=[chat_message])

        self._create_message(
            participant_id=participant_id, channel=channel, body=body, nickname=nickname
        )

    def _create_message(self, **kwargs):
        ChatMessage.objects_create(**kwargs)


class WSDeleteSessions(_OTreeAsyncJsonWebsocketConsumer):
    async def post_receive_json(self, content):
        Session.objects_filter(Session.code.in_(content)).delete(
            synchronize_session=False
        )
        await self.send_json('ok')

    def group_name(self, **kwargs):
        return None


class WSExportData(_OTreeAsyncJsonWebsocketConsumer):
    '''
    I load tested this locally with sqlite and:
    - large files up to 22MB (by putting long text in LongStringFields)
    - thousands of participants/rounds, 111000 rows and 20 cols in excel file.
    '''

    async def post_receive_json(self, content: dict):
        '''
        if an app name is given, export the app.
        otherwise, export all the data (wide).
        don't need time_spent or chat yet, they are quick enough
        '''

        app_name = content.get('app_name')
        is_custom = content.get('is_custom')
        function_name = content.get('function_name', 'custom_export')

        iso_date = datetime.date.today().isoformat()
        try:
            with io.StringIO() as fp:
                # Excel requires BOM; otherwise non-english characters are garbled
                if content.get('for_excel'):
                    fp.write(BOM)
                if app_name:
                    if is_custom:
                        fxn = custom_export_app
                        # Generate filename based on export_name
                        file_name_prefix = f'{app_name}_{function_name}'
                        fxn(app_name, fp, function_name=function_name)
                    else:
                        fxn = export_app
                        file_name_prefix = app_name
                        fxn(app_name, fp)
                else:
                    export_wide(fp)
                    file_name_prefix = 'all_apps_wide'
                data = fp.getvalue()
        except Exception:
            content.update(
                error="Error exporting data. Check the server logs for details."
            )
            await self.send_json(content)
            raise
        else:
            file_name = f'{file_name_prefix}_{iso_date}.csv'
            content.update(file_name=file_name, data=data, mime_type='text/csv')
            # note, this doesn't go through channel layer currently
            await self.send_json(content)

    def group_name(self, **kwargs):
        return None


def parse_querystring(query_string) -> dict:
    '''it seems parse_qs omits keys with empty values'''
    return {k: v[0] for k, v in urllib.parse.parse_qs(query_string.decode()).items()}


class LifespanApp:
    '''
    temporary shim for https://github.com/django/channels/issues/1216
    needed so that hypercorn doesn't display an error.
    this uses ASGI 2.0 format, not the newer 3.0 single callable
    '''

    def __init__(self, scope):
        self.scope = scope

    async def __call__(self, receive, send):
        if self.scope['type'] == 'lifespan':
            while True:
                message = await receive()
                if message['type'] == 'lifespan.startup':
                    await send({'type': 'lifespan.startup.complete'})
                elif message['type'] == 'lifespan.shutdown':
                    await send({'type': 'lifespan.shutdown.complete'})
                    return


class TrialConsumer(_OTreeAsyncJsonWebsocketConsumer):
    def group_name(self, participant_code, page_index, **kwargs):
        return channel_utils.trial_group(participant_code, page_index)

    def clean_kwargs(self):
        return parse_querystring(self.scope['query_string'])

    def browser_bot_exists(self, participant_code):
        # for browser bots, block liveSend calls that get triggered on page load.
        # instead, everything must happen through call_live_method in a controlled way.
        return Participant.objects_exists(code=participant_code, is_browser_bot=True)

    async def post_receive_json(self, content, participant_code, page_name, **kwargs):
        if self.browser_bot_exists(participant_code):
            return
        await trial_payload_function(
            participant_code=participant_code, page_name=page_name, msg=content
        )

    @classmethod
    async def encode_json(cls, content):
        return json_dumps(content)
