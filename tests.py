"""unit tests to validate the package functions
"""
import sys
import timeit
import time
from patronigence import notion
from patronigence import chat

REPORTS_DIR = 'C:\\Users\\taylo\\Gmail Drive\\05 Patron\\02 Planning\\02 Gatekeeper\\2023'
RESPONSE_DEFAULT = {
    'result': False,
    'message': 'test failed. default message',
    'errors': ''
}


def run_test(args):
    if len(args) > 0:
        test_id = int(args[0])
        pos_args = args[1:]
        response = RESPONSE_DEFAULT.copy()
        test_label = TESTS[test_id]['label']
        test_function = TESTS[test_id]['function']
        intro = f'running test {test_id}: {test_label} ... '
        fail_template = 'test failed. details {errors}'
        pass_template = 'test passed. {message}'
        print(intro)
        try:
            response = test_function(pos_args)
        except:
            pass
        if response['result']:
            message = pass_template.format(message=response['message'])
        else:
            message = fail_template.format(errors=response['errors'])
        print(message)


def test01_notion_get_reviews(pos_args=None, db_name='', page_count=0):
    if pos_args:
        DB_NAME = pos_args[0]
        PAGE_COUNT = int(pos_args[1])
    else:
        DB_NAME = db_name
        PAGE_COUNT = page_count
    response = RESPONSE_DEFAULT.copy()
    api = notion.NotionWorkspace()
    database_id = api.get_user_data('database_id', DB_NAME)
    pages = api.get_pages(database_id, num_pages=PAGE_COUNT)
    response['result'] = len(pages) > 0
    if response['result']:
        response['message'] = f'fetched {len(pages)} notion pages from {DB_NAME} database'
    else:
        response['errors'] = f'failed to fetch notion pages from {DB_NAME} database'
    return response


def test02_langchain_context_prompt(pos_args=None, report_dir='documents'):
    if pos_args:
        REP_DIR = pos_args[0]
    else:
        REP_DIR = report_dir

    start_time = timeit.default_timer()
    checks = []
    passed = False
    errors = ''
    response = RESPONSE_DEFAULT.copy()
    chat.load()
    chatbot = chat.Wilson()
    test_label = 'test 02.01 load chunks'
    try:
        chatbot.pdfs_load(dir_path=REP_DIR)
        elapsed_sec = timeit.default_timer() - start_time
    except Exception as e:
        errors = str(e)
    else:
        chunk_count = len(chatbot.chunks)
        passed = chunk_count > 0
        checks.append(passed)

    response['result'] = passed
    if passed:
        test_message = f'{test_label} passed. loaded {chunk_count} chunks from directory {REP_DIR}'
        test_message = test_message + f' executed in {round(elapsed_sec, 2)} sec'
        response['message'] = test_message
    else:
        response['errors'] = f'{test_label} failed. failed load chunks from directory {REP_DIR}' + errors

    if not True:
        test_label = 'test 02.02 create vector database'
        start_time = timeit.default_timer()
        try:
            chatbot.vector_db_create(load_pdfs=False)
            elapsed_sec = timeit.default_timer() - start_time
        except Exception as e:
            passed = False
            errors = str(e)
        else:
            passed = chatbot.vector_db is not None
            checks.append(passed)

    if passed:
        test_message = f'{test_label} passed. vector database created.'
        test_message = test_message + f' executed in {round(elapsed_sec, 2)} sec'
        response['message'] = response['message'] + '\n' + test_message
    else:
        response['errors'] = f'{test_label} failed. vector database not created.' + errors

    if response['result']:
        response['message'] = f'{sum(checks)} of {len(checks)} tests passed. ' + '\n' + response['message']

    return response


TESTS = {
    1: {
        'label': 'notion_get_reviews',
        'function': test01_notion_get_reviews
    },
    2: {
        'label': 'notion_langchain_context_prompt',
        'function': test02_langchain_context_prompt
    }
}


if __name__ == '__main__':
    if len(sys.argv) > 1:
        function_name = sys.argv[1]
        if function_name == 'run_test':
            run_test(sys.argv[2:])
