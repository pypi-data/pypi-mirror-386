from starlette.endpoints import HTTPEndpoint
from starlette.responses import HTMLResponse, Response, RedirectResponse, JSONResponse
from starlette.requests import Request
from starlette.responses import Response, RedirectResponse

import otree.bots.browser as browser_bots
import otree.channels.utils as channel_utils
import otree.common
import otree.constants
import otree.models
import otree.views.admin
import otree.views.cbv
import otree.views.mturk
from otree.common import (
    make_hash,
    BotError,
    GlobalState,
)
from otree.database import NoResultFound, db, dbq
from otree.i18n import core_gettext as _
from otree.models import Participant, Session
from otree.models_concrete import ParticipantVarsFromREST
from otree.mturk_client import TurkClient
from otree.room import ROOM_DICT
from otree.templating import render
from otree.views.abstract import GenericWaitPageMixin


def no_participants_left_http_response():
    '''
    this function exists because i'm not sure if Http response objects can be reused
    better to return 404 so browser bot client & tests can recognize it
    '''
    # Translators: for example this is shown if you create a session for 10
    # participants. The 11th person to click will get this message
    # It means there is no space for you.
    return Response(_("Session is full."), status_code=404)


class OutOfRangeNotification(HTTPEndpoint):
    url_pattern = '/OutOfRangeNotification/{code}'

    def get(self, request):
        code = request.path_params['code']
        participant = db.get_or_404(Participant, code=code)
        if participant.is_browser_bot:
            session = participant.session
            has_next_submission = browser_bots.enqueue_next_post_data(
                participant_code=participant.code
            )

            if has_next_submission:
                msg = (
                    'Finished the last page, '
                    'but the bot is still trying '
                    'to submit more pages.'
                )
                raise BotError(msg)

            browser_bots.send_completion_message(
                session_code=session.code, participant_code=code
            )

        return render('otree/OutOfRangeNotification.html', {})


class GBATInactive(HTTPEndpoint):
    url_pattern = '/GBATInactive'

    def get(self, request):
        return render('otree/GBATInactive.html', {})


class InitializeParticipant(HTTPEndpoint):

    url_pattern = '/InitializeParticipant/{code}'

    def get(self, request: Request):
        """anything essential should be done in"""
        code = request.path_params['code']
        pp = db.get_or_404(Participant, code=code)
        query_params = request.query_params
        label = query_params.get(otree.constants.participant_label)
        pp.initialize(label)

        first_url = pp._url_i_should_be_on()
        return RedirectResponse(first_url)


class MTurkStart(HTTPEndpoint):

    url_pattern = r"/MTurkStart/{code}"

    def get(self, request: Request):
        code = request.path_params['code']
        session = self.session = db.get_or_404(Session, code=code)
        GET = request.query_params
        try:
            assignment_id = GET['assignmentId']
            worker_id = GET['workerId']
        except KeyError:
            return Response(
                'URL is missing assignmentId or workerId parameter', status_code=404
            )
        qual_id = session.config['mturk_hit_settings'].get('grant_qualification_id')
        use_sandbox = session.mturk_use_sandbox
        if qual_id and not use_sandbox:
            # this is necessary because MTurk's qualification requirements
            # don't prevent 100% of duplicate participation. See:
            # https://groups.google.com/forum/#!topic/otree/B66HhbFE9ck

            previous_participation = (
                dbq(Participant)
                .join(Session)
                .filter(
                    Participant.session != session,
                    Session.mturk_qual_id == qual_id,
                    Participant.mturk_worker_id == worker_id,
                )
                .scalar()
                is not None
            )
            if previous_participation:
                return Response('You have already accepted a related HIT')

            # if using sandbox, there is no point in granting quals.
            # https://groups.google.com/forum/#!topic/otree/aAmqTUF-b60

            # don't pass request arg, because we don't want to show a message.
            # using the fully qualified name because that seems to make mock.patch work

            # seems OK to assign this multiple times
            TurkClient.assign_qualification(
                dict(
                    QualificationTypeId=qual_id,
                    WorkerId=worker_id,
                    # Mturk complains if I omit IntegerValue
                    IntegerValue=1,
                ),
                use_sandbox=use_sandbox,
            )

        try:
            # just check if this worker already game, but
            # don't filter for assignment, because maybe they already started
            # and returned the previous assignment
            # in this case, we should assign back to the same participant
            # so that we don't get duplicates in the DB, and so people
            # can't snoop and try the HIT first, then re-try to get a bigger bonus
            pp = self.session.pp_set.filter_by(mturk_worker_id=worker_id).one()
        except NoResultFound:
            pp = self.session.pp_set.filter_by(visited=False).order_by('id').first()
            if not pp:
                return no_participants_left_http_response()

            # 2014-10-17: needs to be here even if it's also set in
            # the next view to prevent race conditions
            # this needs to be inside the lock
            pp.visited = True
            pp.mturk_worker_id = worker_id
        # reassign assignment_id, even if they are returning, because maybe they accepted
        # and then returned, then re-accepted with a different assignment ID
        # if it's their second time
        pp.mturk_assignment_id = assignment_id
        return _redirect_to_start_url(pp)


def _redirect_to_start_url(participant):
    start_url = participant._start_url()
    return RedirectResponse(start_url, status_code=302)


def get_participant_by_label(session, label):
    q = session.pp_set
    if label:
        try:
            return q.filter_by(label=label).one()
        except NoResultFound:
            pass
    return q.filter_by(visited=False).order_by('id').first()


def get_participant_by_cookies(session, cookies):
    cookie_name = 'session_{}_participant'.format(session.code)
    code = cookies.get(cookie_name)
    # this could return None
    if code:
        return Participant.objects_filter(code=code).first()
    participant = session.pp_set.filter_by(visited=False).order_by('id').first()
    if participant:
        cookies[cookie_name] = participant.code
        return participant


def mark_visited_and_record_label(participant, label):
    if not participant:
        return

    # needs to be here even if it's also set in
    # the next view to prevent race conditions
    participant.visited = True
    if label:
        participant.set_label(label)

    return participant


def participant_or_none_if_exceeded(session, *, label, cookies=None):
    '''pass request.session as an arg if you want to get/set a cookie'''
    if cookies is None:
        participant = get_participant_by_label(session, label)
    else:
        participant = get_participant_by_cookies(session, cookies)
    if not participant:
        return

    return mark_visited_and_record_label(participant, label)


class SessionWideLink(HTTPEndpoint):
    """
    Better to have just 1 endpoint.
    In demo mode, we don't use cookies.
    With a real session, we do use cookies.
    We never need to have both.
    And don't have to think about what if the participant changes the URL.
    """

    url_pattern = '/join/{anonymous_code}'

    use_cookies: bool

    def get_participant(self, request, label):
        raise NotImplementedError

    def get(self, request: Request):
        anonymous_code = request.path_params['anonymous_code']
        session = db.get_or_404(Session, _anonymous_code=anonymous_code)
        label = request.query_params.get('participant_label')

        # is this priority right? maybe cookies should override label?
        # but maybe a participant first clicks the wrong link,
        # they shouldn't be stuck and forbidden from participating.

        if label:
            participant = get_participant_by_label(session, label)
        elif not session.is_demo:
            participant = get_participant_by_cookies(session, request.session)
        else:
            participant = get_participant_by_label(session, None)

        if not participant:
            return no_participants_left_http_response()
        mark_visited_and_record_label(participant, label)

        return _redirect_to_start_url(participant)


def validate_room_visitor(room, query_params: dict) -> dict:
    errors = {}
    if room.has_participant_labels:
        label = query_params.get('participant_label', '')
        if not label:
            errors['participant_label'] = 'Please enter a participant label'
        elif label not in room.get_participant_labels():
            errors['participant_label'] = 'This participant label was not found'
        elif room.use_secure_urls:
            hash = query_params.get('hash')
            if not hash or hash != make_hash(label):
                errors['hash'] = (
                    'Invalid hash parameter. use_secure_urls is True, '
                    'so you must use the participant-specific URL.'
                )
    # later, validate custom params here.
    return errors


class AssignVisitorToRoom(GenericWaitPageMixin, HTTPEndpoint):

    url_pattern = '/room/{room_name}'

    def get(self, request: Request):
        room_name = request.path_params['room_name']
        try:
            room = ROOM_DICT[room_name]
        except KeyError:
            return Response('Invalid room specified in url', status_code=404)

        if not request.query_params.get('welcome_page_ok'):
            return render(
                room.welcome_page or "otree/RoomWelcomePage.html",
                dict(has_participant_label_file=room.has_participant_labels),
            )

        errors = validate_room_visitor(room, request.query_params)

        if errors:
            return HTMLResponse(f"<pre>{errors}</pre>", status_code=404)

        # labels are still allowed even if the room has no participant_labels_file
        label = request.query_params.get('participant_label', '')

        session = room.get_session()

        if session is None:
            self.tab_unique_id = otree.common.random_chars_join_code()
            self._socket_url = channel_utils.room_participant_path(
                room_name=room_name,
                participant_label=label,
                # random chars in case the participant has multiple tabs open
                tab_unique_id=self.tab_unique_id,
            )
            return render(
                "otree/WaitPageRoom.html",
                dict(
                    view=self,
                    title_text=_('Please wait'),
                    body_text=_('Waiting for your session to begin'),
                ),
            )

        if label:
            participant = get_participant_by_label(session, label)
        else:
            participant = get_participant_by_cookies(session, request.session)

        if not participant:
            return no_participants_left_http_response()

        mark_visited_and_record_label(participant, label)
        if label:  # whether the room has participant labels or not
            passed_vars = ParticipantVarsFromREST.objects_filter(
                room_name=room_name, participant_label=label
            ).first()
            if passed_vars:
                participant.vars.update(passed_vars.vars)
                db.delete(passed_vars)

        return _redirect_to_start_url(participant)

    def socket_url(self):
        return self._socket_url

    async def post(self, request: Request):
        room_name = request.path_params['room_name']
        try:
            room = ROOM_DICT[room_name]
        except KeyError:
            return Response('Invalid room specified in url', status_code=404)

        # Parse JSON data from the request
        try:
            json_data = await request.json()
        except:
            return Response('Invalid JSON data', status_code=400)

        # Merge query params with JSON data for validation
        query_params = dict(request.query_params)
        query_params.update(json_data)

        # Validate the data
        errors = validate_room_visitor(room, query_params)
        if errors:
            return JSONResponse({'errors': errors})

        # If validation passes, return success
        return JSONResponse({'status': 'ok'})


class BrowserBotStartLink(GenericWaitPageMixin, HTTPEndpoint):
    '''should i move this to another module?
    because the rest of these views are accessible without password login.
    '''

    # remote CLI browser bots won't work if this takes an admin_secret_code param because
    # SECRET_KEY might be different on the server.
    url_pattern = '/browser_bot_start'

    def get(self, request):

        session_code = GlobalState.browser_bots_launcher_session_code
        if session_code:
            try:
                session = Session.objects_get(code=session_code)
            except NoResultFound:
                # maybe it's an old session
                pass
            else:
                participant = (
                    session.pp_set.filter_by(visited=False).order_by('id').first()
                )
                if not participant:
                    return no_participants_left_http_response()

                # 2014-10-17: needs to be here even if it's also set in
                # the next view to prevent race conditions
                participant.visited = True
                return _redirect_to_start_url(participant)
        ctx = dict(
            view=self,
            title_text='Please wait',
            body_text='Waiting for browser bots session to begin',
        )
        return render("otree/WaitPageBase.html", ctx)

    def socket_url(self):
        return '/browser_bot_wait/'
