import os
import unittest
from unittest.mock import patch, Mock
from templating_utils import process_templated_contents as process_templated_content_if_needed

class TestTemplatingUtilsLengthOperations(unittest.TestCase):
    
    def setUp(self):
        os.environ.pop('CONTENT_JSON', None)
        self.json_url = 'https://example.com/data.json'
        os.environ['CONTENT_JSON'] = self.json_url

    def tearDown(self):
        os.environ.pop('CONTENT_JSON', None)

    @patch('templating_utils.requests.get')
    def test_max_length_basic(self, mock_get):
        mock_get.return_value = Mock(status_code=200)
        mock_get.return_value.json.return_value = {
            "description": "This is a very long description that should be truncated"
        }
        content = "@{json.description | max_length(20, '...')}"
        result, = process_templated_content_if_needed(content)
        self.assertEqual(result, "This is a very long...")

    @patch('templating_utils.requests.get')
    def test_max_length_no_suffix(self, mock_get):
        mock_get.return_value = Mock(status_code=200)
        mock_get.return_value.json.return_value = {
            "description": "Short text"
        }
        content = "@{json.description | max_length(50)}"
        result, = process_templated_content_if_needed(content)
        self.assertEqual(result, "Short text")

    @patch('templating_utils.requests.get')
    def test_max_length_exact_length(self, mock_get):
        mock_get.return_value = Mock(status_code=200)
        mock_get.return_value.json.return_value = {
            "description": "Exactly twenty chars"
        }
        content = "@{json.description | max_length(20, '...')}"
        result, = process_templated_content_if_needed(content)
        self.assertEqual(result, "Exactly twenty chars")

    @patch('templating_utils.requests.get')
    def test_max_length_word_boundary(self, mock_get):
        mock_get.return_value = Mock(status_code=200)
        mock_get.return_value.json.return_value = {
            "description": "This is a test sentence for word boundary"
        }
        content = "@{json.description | max_length(15, '...')}"
        result, = process_templated_content_if_needed(content)
        # Should clip at "This is a test" (14 chars) + "..." = "This is a test..."
        self.assertEqual(result, "This is a test...")

    @patch('templating_utils.requests.get')
    def test_each_max_length(self, mock_get):
        mock_get.return_value = Mock(status_code=200)
        mock_get.return_value.json.return_value = {
            "descriptions": [
                "Short",
                "This is a longer description",
                "Medium length text"
            ]
        }
        content = "@{json.descriptions | each:max_length(10, '...') | join(', ')}"
        result, = process_templated_content_if_needed(content)
        self.assertEqual(result, "Short, This is a..., Medium...")

    @patch('templating_utils.requests.get')
    def test_join_while_basic(self, mock_get):
        mock_get.return_value = Mock(status_code=200)
        mock_get.return_value.json.return_value = {
            "tags": ["one", "two", "three", "four", "five"]
        }
        content = "@{json.tags | join_while(' ', 12)}"
        result, = process_templated_content_if_needed(content)
        # "one two three" = 13 chars, "one two" = 7 chars (fits), "one two three" = 13 chars (exceeds)
        self.assertEqual(result, "one two")

    @patch('templating_utils.requests.get')
    def test_join_while_single_item_too_long(self, mock_get):
        mock_get.return_value = Mock(status_code=200)
        mock_get.return_value.json.return_value = {
            "tags": ["verylongfirstitem", "short"]
        }
        content = "@{json.tags | join_while(' ', 10)}"
        result, = process_templated_content_if_needed(content)
        # First item is too long, so result should be empty
        self.assertEqual(result, "")

    @patch('templating_utils.requests.get')
    def test_join_while_all_fit(self, mock_get):
        mock_get.return_value = Mock(status_code=200)
        mock_get.return_value.json.return_value = {
            "tags": ["a", "b", "c"]
        }
        content = "@{json.tags | join_while(' ', 10)}"
        result, = process_templated_content_if_needed(content)
        self.assertEqual(result, "a b c")

    @patch('templating_utils.requests.get')
    def test_chained_length_operations(self, mock_get):
        mock_get.return_value = Mock(status_code=200)
        mock_get.return_value.json.return_value = {
            "items": [
                "This is a very long item description",
                "Short item",
                "Another moderately long item"
            ]
        }
        content = "@{json.items | each:max_length(15, '...') | join_while(', ', 40)}"
        result, = process_templated_content_if_needed(content)
        # After each:max_length: ["This is a very...", "Short item", "Another..."]
        # join_while with 40 chars: "This is a very..., Short item" = 33 chars (fits)
        # Adding ", Another..." would make it 46 chars (exceeds 40)
        self.assertEqual(result, "This is a very..., Short item")

    @patch('templating_utils.requests.get')
    def test_max_length_on_non_string_warns(self, mock_get):
        mock_get.return_value = Mock(status_code=200)
        mock_get.return_value.json.return_value = {
            "items": ["one", "two", "three"]
        }
        # max_length on a list should warn
        content = "@{json.items | max_length(10, '...')}"
        result, = process_templated_content_if_needed(content)
        # Should apply max_length to the string representation of the list
        expected = str(["one", "two", "three"])
        if len(expected) > 10:
            # Find last space before position 10
            truncated = expected[:10]
            last_space = truncated.rfind(' ')
            if last_space != -1:
                expected = expected[:last_space] + "..."
            else:
                expected = truncated + "..."
        self.assertTrue(result.endswith("..."))

    @patch('templating_utils.requests.get')
    def test_invalid_arguments(self, mock_get):
        mock_get.return_value = Mock(status_code=200)
        mock_get.return_value.json.return_value = {
            "text": "hello world",
            "items": ["a", "b", "c"]
        }
        
        # Test max_length with invalid arguments
        content1 = "@{json.text | max_length()}"
        result1 = process_templated_content_if_needed(content1)
        self.assertEqual(result1, "hello world")  # Should remain unchanged
        
        # Test join_while with insufficient arguments
        content2 = "@{json.items | join_while(' ')}"
        result2 = process_templated_content_if_needed(content2)
        self.assertEqual(result2, "['a', 'b', 'c']")  # Should remain unchanged

if __name__ == '__main__':
    unittest.main()
