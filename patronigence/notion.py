import requests
import json


VERSION_DATE = '2022-06-28'
VERSION = 'v1'
DATA_FILES = {
    'API_TOKEN': 'NOTION_API_TOKEN',
    'USER_DATA': 'notion_data.json'
}
API_TOKEN = ''
USER_DATA = {}
EXCEPTIONS = {
    'api_response': 'ERROR. problem encountered when processing api request.'
}
URL_ROUTES = {
    'databases': 'databases/',
    'pages': 'pages/'
}
LOADED = False


headers = {
    'Authorization': 'Bearer {API_TOKEN}',
    'Content-Type': 'application/json',
    'Notion-Version': VERSION_DATE,
}


class NotionWorkspace(object):
    URL_DOMAIN = ''
    _API_TOKEN = ''
    _USER_DATA = {}
    _headers = headers.copy()
    exceptions_printout = False
    errors = ''

    def __init__(self,
                 api_token_file=DATA_FILES['API_TOKEN'],
                 user_data_file=DATA_FILES['USER_DATA']):
        self._set_api_token(api_token_file)
        self._set_user_data(user_data_file)
        self._set_headers()
        self._set_url_domain()

    def _set_api_token(self, api_token_file):
        if not self._API_TOKEN:
            with open(api_token_file, 'r') as f:
                self._API_TOKEN = f.read()
                f.close()

    def _set_user_data(self, user_data_file):
        if not self._USER_DATA:
            with open(user_data_file, 'r') as f:
                self._USER_DATA = json.load(f)
                f.close()

    def _set_headers(self):
        if '{API_TOKEN}' in self._headers['Authorization']:
            self._headers['Authorization'] = self._headers[
                'Authorization'].format(API_TOKEN=self._API_TOKEN)

    def _set_url_domain(self):
        self.URL_DOMAIN = 'https://api.notion.com/v1/'

    def get_url_endpoint(self, route_id):
        url_endpoint = self.URL_DOMAIN + URL_ROUTES[route_id]
        return url_endpoint

    def api_request(self, url, method='post', payload={}, suppress=False):
        response = {}

        def requests_function(method):
            if method == 'get':
                return requests.get
            elif method == 'post':
                return requests.post
            else:
                return None

        try:
            if payload:
                response = requests_function(method)(url, json=payload, headers=self._headers)
            else:
                response = requests_function(method)(url, headers=self._headers)
        except Exception as e:
            self._exception_handle(
                exception_type='api_response', exception=e, suppress=suppress)

        return response

    def get_pages(self, database_id, num_pages=None):
        url = self.get_url_endpoint('databases') + f'{database_id}/query'
        data = {
            'has_more': True
        }
        get_all = num_pages is None
        results = []
        first_query = True
        page_size = num_pages if num_pages is not None else 100

        while first_query or (data['has_more'] and get_all):
            if first_query:
                payload = {'page_size': page_size}
            else:
                payload = {'page_size': page_size, 'start_cursor': data['next_cursor']}
            response = self.api_request(url, 'post', payload=payload)
            data = response.json()
            results.extend(data['results'])
            first_query = False

        return results

    def get_user_data(self, attribute, key):
        attr_value = None
        if attribute == 'database_id':
            attr_value = self._get_database_attribute('id', key)
        return attr_value

    def _get_database_attribute(self, attribute, database_label):
        attr_value = None
        attributes = self._USER_DATA['databases'][database_label] if database_label in self._USER_DATA['databases'] else {}
        if attributes:
            attr_value = attributes[attribute] if attribute in attributes else None
        return attr_value

    def _exception_handle(self, exception_type='', message='',
                          exception=None, suppress=False):
        exception_message = message
        if exception_type in EXCEPTIONS:
            exception_message = EXCEPTIONS[exception_type] + message
        if exception:
            exception_message = exception_message + str(exception)

        self.errors = exception_message
        if self.exceptions_printout:
            print(exception_message)

        if exception and (not suppress):
            raise ValueError(exception_message) from exception
