import os
import unittest
from unittest.mock import patch, Mock
from templating_utils import process_templated_contents as process_templated_content_if_needed

class TestTemplatingUtilsCaseOperations(unittest.TestCase):
    
    def setUp(self):
        os.environ.pop('CONTENT_JSON', None)
        self.json_url = 'https://example.com/data.json'
        os.environ['CONTENT_JSON'] = self.json_url

    def tearDown(self):
        os.environ.pop('CONTENT_JSON', None)

    @patch('templating_utils.requests.get')
    def test_each_case_title(self, mock_get):
        mock_get.return_value = Mock(status_code=200)
        mock_get.return_value.json.return_value = {
            "words": ["hello world", "foo bar", "test case"]
        }
        content = "@{json.words | each:case_title() | join(', ')}"
        result, = process_templated_content_if_needed(content)
        self.assertEqual(result, "Hello World, Foo Bar, Test Case")

    @patch('templating_utils.requests.get')
    def test_each_case_sentence(self, mock_get):
        mock_get.return_value = Mock(status_code=200)
        mock_get.return_value.json.return_value = {
            "words": ["hello world", "foo bar", "test case"]
        }
        content = "@{json.words | each:case_sentence() | join(', ')}"
        result, = process_templated_content_if_needed(content)
        self.assertEqual(result, "Hello world, Foo bar, Test case")

    @patch('templating_utils.requests.get')
    def test_each_case_upper(self, mock_get):
        mock_get.return_value = Mock(status_code=200)
        mock_get.return_value.json.return_value = {
            "words": ["hello world", "Foo Bar", "Test Case"]
        }
        content = "@{json.words | each:case_upper() | join(', ')}"
        result, = process_templated_content_if_needed(content)
        self.assertEqual(result, "HELLO WORLD, FOO BAR, TEST CASE")

    @patch('templating_utils.requests.get')
    def test_each_case_lower(self, mock_get):
        mock_get.return_value = Mock(status_code=200)
        mock_get.return_value.json.return_value = {
            "words": ["HELLO WORLD", "Foo Bar", "Test Case"]
        }
        content = "@{json.words | each:case_lower() | join(', ')}"
        result, = process_templated_content_if_needed(content)
        self.assertEqual(result, "hello world, foo bar, test case")

    @patch('templating_utils.requests.get')
    def test_each_case_pascal(self, mock_get):
        mock_get.return_value = Mock(status_code=200)
        mock_get.return_value.json.return_value = {
            "words": ["hello world", "foo bar baz", "test-case_item"]
        }
        content = "@{json.words | each:case_pascal() | join(', ')}"
        result, = process_templated_content_if_needed(content)
        self.assertEqual(result, "HelloWorld, FooBarBaz, TestCaseItem")

    @patch('templating_utils.requests.get')
    def test_each_case_kebab(self, mock_get):
        mock_get.return_value = Mock(status_code=200)
        mock_get.return_value.json.return_value = {
            "words": ["hello world", "FooBar", "test_case_item"]
        }
        content = "@{json.words | each:case_kebab() | join(', ')}"
        result, = process_templated_content_if_needed(content)
        self.assertEqual(result, "hello-world, foo-bar, test-case-item")

    @patch('templating_utils.requests.get')
    def test_each_case_snake(self, mock_get):
        mock_get.return_value = Mock(status_code=200)
        mock_get.return_value.json.return_value = {
            "words": ["hello world", "FooBar", "test-case-item"]
        }
        content = "@{json.words | each:case_snake() | join(', ')}"
        result, = process_templated_content_if_needed(content)
        self.assertEqual(result, "hello_world, foo_bar, test_case_item")

    @patch('templating_utils.requests.get')
    def test_case_operations_on_non_list_warns(self, mock_get):
        mock_get.return_value = Mock(status_code=200)
        mock_get.return_value.json.return_value = {
            "text": "hello world"
        }
        content = "@{json.text | each:case_title()}"
        result, = process_templated_content_if_needed(content)
        # Should return original string since it's not a list
        self.assertEqual(result, "hello world")

    @patch('templating_utils.requests.get')
    def test_chained_case_operations(self, mock_get):
        mock_get.return_value = Mock(status_code=200)
        mock_get.return_value.json.return_value = {
            "items": ["hello world", "foo bar"]
        }
        content = "@{json.items | each:case_upper() | each:prefix('#') | join(' ')}"
        result, = process_templated_content_if_needed(content)
        self.assertEqual(result, "#HELLO WORLD #FOO BAR")

if __name__ == '__main__':
    unittest.main()
