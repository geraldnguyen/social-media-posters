import os
import unittest
from unittest.mock import patch, Mock
from templating_utils import process_templated_contents

class TestTemplatingUtilsRandomAttrOperations(unittest.TestCase):

    def setUp(self):
        os.environ.pop('CONTENT_JSON', None)
        self.json_url = 'https://example.com/data.json'
        os.environ['CONTENT_JSON'] = self.json_url

    def tearDown(self):
        os.environ.pop('CONTENT_JSON', None)

    @patch('templating_utils.requests.get')
    @patch('random.randint', return_value=1)
    def test_random_basic(self, mock_randint, mock_get):
        mock_get.return_value = Mock(status_code=200)
        mock_get.return_value.json.return_value = {
            "items": ["first", "second", "third"]
        }
        content = "@{json.items | random()}"
        result, = process_templated_contents(content)
        self.assertEqual(result, "second")

    @patch('templating_utils.requests.get')
    def test_random_empty_list(self, mock_get):
        mock_get.return_value = Mock(status_code=200)
        mock_get.return_value.json.return_value = {
            "items": []
        }
        content = "@{json.items | random()}"
        with self.assertRaises(ValueError) as cm:
            process_templated_contents(content)
        self.assertIn("random() operation requires non-empty list", str(cm.exception))

    @patch('templating_utils.requests.get')
    def test_random_not_list(self, mock_get):
        mock_get.return_value = Mock(status_code=200)
        mock_get.return_value.json.return_value = {
            "item": "not a list"
        }
        content = "@{json.item | random()}"
        with self.assertRaises(ValueError) as cm:
            process_templated_contents(content)
        self.assertIn("random() operation requires list input", str(cm.exception))

    @patch('templating_utils.requests.get')
    def test_attr_basic(self, mock_get):
        mock_get.return_value = Mock(status_code=200)
        mock_get.return_value.json.return_value = {
            "object": {"name": "John", "age": 30}
        }
        content = "@{json.object | attr(name)}"
        result, = process_templated_contents(content)
        self.assertEqual(result, "John")

    @patch('templating_utils.requests.get')
    def test_attr_nested(self, mock_get):
        mock_get.return_value = Mock(status_code=200)
        mock_get.return_value.json.return_value = {
            "user": {"profile": {"firstName": "Jane", "lastName": "Doe"}}
        }
        content = "@{json.user | attr(profile) | attr(firstName)}"
        result, = process_templated_contents(content)
        self.assertEqual(result, "Jane")

    @patch('templating_utils.requests.get')
    def test_attr_missing_attribute(self, mock_get):
        mock_get.return_value = Mock(status_code=200)
        mock_get.return_value.json.return_value = {
            "object": {"name": "John"}
        }
        content = "@{json.object | attr(missing)}"
        with self.assertRaises(ValueError) as cm:
            process_templated_contents(content)
        self.assertIn("attr() attribute 'missing' not found in object", str(cm.exception))

    @patch('templating_utils.requests.get')
    def test_attr_not_dict(self, mock_get):
        mock_get.return_value = Mock(status_code=200)
        mock_get.return_value.json.return_value = {
            "item": "not a dict"
        }
        content = "@{json.item | attr(name)}"
        with self.assertRaises(ValueError) as cm:
            process_templated_contents(content)
        self.assertIn("attr() operation requires dict input", str(cm.exception))

    @patch('templating_utils.requests.get')
    def test_attr_no_argument(self, mock_get):
        mock_get.return_value = Mock(status_code=200)
        mock_get.return_value.json.return_value = {
            "object": {"name": "John"}
        }
        content = "@{json.object | attr()}"
        with self.assertRaises(ValueError) as cm:
            process_templated_contents(content)
        self.assertIn("attr() requires at least 1 argument (attribute name)", str(cm.exception))

    @patch('templating_utils.requests.get')
    @patch('random.randint', return_value=0)
    def test_random_with_attr(self, mock_randint, mock_get):
        mock_get.return_value = Mock(status_code=200)
        mock_get.return_value.json.return_value = {
            "users": [
                {"name": "Alice", "role": "admin"},
                {"name": "Bob", "role": "user"}
            ]
        }
        content = "@{json.users | random() | attr(name)}"
        result, = process_templated_contents(content)
        self.assertEqual(result, "Alice")

if __name__ == '__main__':
    unittest.main()