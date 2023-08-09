"""unit tests to validate the package functions
"""
import sys
import time
from patronigence import notion


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
    notion.load()
    database_id = notion.USER_DATA['databases'][DB_NAME]['id']
    pages = notion.get_pages(database_id, num_pages=PAGE_COUNT)
    response['result'] = len(pages) > 0
    if response['result']:
        response['message'] = f'fetched {len(pages)} notion pages from {DB_NAME} database'
    else:
        response['errors'] = f'failed to fetch notion pages from {DB_NAME} database'
    return response


TESTS = {
    1: {
        'label': 'notion_get_reviews',
        'function': test01_notion_get_reviews
    }
}


if __name__ == '__main__':
    if len(sys.argv) > 1:
        function_name = sys.argv[1]
        if function_name == 'run_test':
            run_test(sys.argv[2:])
