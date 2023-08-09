import requests
import json


VERSION = '2022-06-28'
DATA_FILES = {
    'API_TOKEN': 'NOTION_API_TOKEN',
    'USER_DATA': 'notion_data.json'
}
API_TOKEN = ''
USER_DATA = {}
LOADED = False


headers = {
    'Authorization': 'Bearer {API_TOKEN}',
    'Content-Type': 'application/json',
    'Notion-Version': VERSION,
}


def load():
    global LOADED
    if not LOADED:
        load_api_token()
        load_headers()
        load_user_data()
        LOADED = True


def load_api_token():
    global API_TOKEN
    if not API_TOKEN:
        with open(DATA_FILES['API_TOKEN'], 'r') as f:
            API_TOKEN = f.read()
            f.close()


def load_headers():
    global headers
    if '{API_TOKEN}' in headers['Authorization']:
        headers['Authorization'] = headers['Authorization'].format(API_TOKEN=API_TOKEN)


def load_user_data():
    global USER_DATA
    if not USER_DATA:
        with open(DATA_FILES['USER_DATA'], 'r') as f:
            USER_DATA = json.load(f)
            f.close()


#--------PAGES------------------------------------------------------


def get_pages(database_id, num_pages=None):
    url = f'https://api.notion.com/v1/databases/{database_id}/query'

    get_all = num_pages is None
    page_size = 100 if get_all else num_pages

    payload = {'page_size': page_size}
    response = requests.post(url, json=payload, headers=headers)

    data = response.json()

    results = data['results']
    while data['has_more'] and get_all:
        payload = {'page_size': page_size, 'start_cursor': data['next_cursor']}
        url = f"https://api.notion.com/v1/databases/{database_id}/query"
        response = requests.post(url, json=payload, headers=headers)
        data = response.json()
        results.extend(data['results'])

    return results
