from io import StringIO
import datetime
from starlette.responses import Response
from . import cbv
from starlette.endpoints import HTTPEndpoint

import otree.common
import otree.models
from otree import export
from otree.export import BOM, get_installed_apps_with_data
from otree.models import Participant
from otree.models_concrete import ChatMessage
from otree.database import dbq
from . import cbv


def get_csv_http_response(buffer: StringIO, filename_prefix) -> Response:
    buffer.seek(0)
    response = Response(buffer.read())
    date = datetime.date.today().isoformat()
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = (
        f'attachment; filename="{filename_prefix}-{date}.csv"'
    )
    return response


class ExportMixin:
    """Shared logic for all export views"""

    def file_name_stem(self):
        raise NotImplementedError

    def write_to_buf(self, buf, session_code, query_params):
        raise NotImplementedError

    def process_export(self, request):
        query_params = request.query_params
        session_code = query_params.get('session_code')
        buf = StringIO()
        if query_params.get('format') == 'csv_bom':
            buf.write(BOM)
        self.write_to_buf(buf, session_code, query_params)
        return get_csv_http_response(buf, self.file_name_stem())


class BaseExport(ExportMixin, HTTPEndpoint):
    """REST API export with REST key authentication"""

    def get(self, request):
        error_response = cbv.validate_rest_key(request)
        if error_response:
            return error_response
        return self.process_export(request)


class LoginProtectedExport(ExportMixin, cbv.AdminView):
    """Login-protected export for non-API endpoints"""

    def get(self, request, **kwargs):
        return self.process_export(request)


class ExportWide(BaseExport):
    '''used by data page'''

    url_pattern = '/api/export_wide'

    def file_name_stem(self):
        return 'all_apps_wide'

    def write_to_buf(self, buf, session_code, query_params):
        export.export_wide(buf, session_code=session_code)


class ExportPageTimes(BaseExport):

    url_pattern = '/api/export_page_times'

    def file_name_stem(self):
        return 'PageTimes'

    def write_to_buf(self, buf, session_code, query_params):
        export.export_page_times(buf)


class ExportChat(BaseExport):

    url_pattern = '/api/export_chat'

    def file_name_stem(self):
        return 'ChatMessages'

    def write_to_buf(self, buf, session_code, query_params):
        export.export_chat(buf, session_code=session_code)


class ExportApp(BaseExport):

    url_pattern = '/api/export_app'

    def file_name_stem(self):
        return self.app_name

    def write_to_buf(self, buf, session_code, query_params):
        app_name = query_params.get('app')
        self.app_name = app_name
        if not app_name:
            raise ValueError("app parameter is required")
        export.export_app(app_name, buf, session_code=session_code)


class ExportAppCustom(BaseExport):

    url_pattern = '/api/export_app_custom'

    app_name: str
    function_name: str

    def file_name_stem(self):
        return f'{self.app_name}_{self.function_name}'

    def write_to_buf(self, buf, session_code, query_params):
        app_name = query_params.get('app')
        function_name = query_params.get('function_name', 'custom_export')
        self.app_name = app_name
        self.function_name = function_name
        if not app_name:
            raise ValueError("app parameter is required")
        export.custom_export_app(
            app_name, buf, session_code=session_code, function_name=function_name
        )


class ExportPageTimesLogin(LoginProtectedExport):
    """Login-protected version of page times export"""

    url_pattern = '/ExportPageTimes'

    def file_name_stem(self):
        return 'PageTimes'

    def write_to_buf(self, buf, session_code, query_params):
        export.export_page_times(buf)


class ExportChatLogin(LoginProtectedExport):
    """Login-protected version of chat export"""

    url_pattern = '/ExportChat'

    def file_name_stem(self):
        return 'ChatMessages'

    def write_to_buf(self, buf, session_code, query_params):
        export.export_chat(buf, session_code=session_code)


class ExportIndex(cbv.AdminView):
    url_pattern = '/ExportIndex'

    def vars_for_template(self):
        from otree.asgi import reverse

        # can't use settings.OTREE_APPS, because maybe the app
        # was removed from SESSION_CONFIGS.
        app_names_with_data = get_installed_apps_with_data()

        # Find all custom export functions
        custom_export_list = []
        for app_name in app_names_with_data:
            custom_exports = export.get_custom_export_functions(app_name)
            for export_function_name in sorted(custom_exports.keys()):
                custom_export_list.append((app_name, export_function_name))

        # Base URLs
        wide_url = reverse('ExportWide')
        export_url = reverse('ExportApp')
        custom_export_url = reverse('ExportAppCustom')
        page_times_url = reverse('ExportPageTimes')
        chat_url = reverse('ExportChat')

        # Wide export table
        wide_table = [
            dict(
                name='All apps (wide format)',
                csv_url=wide_url,
                excel_url=wide_url + '?format=csv_bom',
                example_session_url=wide_url + '?session_code={SESSION_CODE}',
            )
        ]

        # Per-app export table
        app_table = [
            dict(
                name=app_name,
                csv_url=export_url + '?app=' + app_name,
                excel_url=export_url + '?format=csv_bom&app=' + app_name,
                example_session_url=export_url
                + '?app='
                + app_name
                + '&session_code={SESSION_CODE}',
                app_name=app_name,
            )
            for app_name in app_names_with_data
        ]

        # Custom export table
        custom_export_table = []
        for app_name, export_function_name in custom_export_list:
            custom_export_table.append(
                dict(
                    name=f'{app_name} ({export_function_name})',
                    csv_url=custom_export_url
                    + f'?app={app_name}&function_name={export_function_name}',
                    excel_url=custom_export_url
                    + f'?format=csv_bom&app={app_name}&function_name={export_function_name}',
                    example_session_url=custom_export_url
                    + f'?app={app_name}&function_name={export_function_name}'
                    + '&session_code={SESSION_CODE}',
                    app_name=app_name,
                    function_name=export_function_name,
                )
            )

        # Other exports (using login-protected endpoints)
        page_times_login_url = reverse('ExportPageTimesLogin')
        chat_login_url = reverse('ExportChatLogin')

        other_exports = [
            dict(
                name='Page times',
                csv_url=page_times_login_url,
                excel_url=page_times_login_url + '?format=csv_bom',
                api_csv_url=page_times_url,
                api_excel_url=page_times_url + '?format=csv_bom',
                example_session_url=None,
            ),
        ]

        chat_messages_exist = bool(dbq(ChatMessage).first())
        if chat_messages_exist:
            other_exports.append(
                dict(
                    name='Chat logs',
                    csv_url=chat_login_url,
                    excel_url=chat_login_url + '?format=csv_bom',
                    api_csv_url=chat_url,
                    api_excel_url=chat_url + '?format=csv_bom',
                    example_session_url=chat_url + '?session_code={SESSION_CODE}',
                )
            )

        return dict(
            db_is_empty=not bool(dbq(Participant).first()),
            wide_table=wide_table,
            app_table=app_table,
            custom_export_table=custom_export_table,
            other_exports=other_exports,
        )
