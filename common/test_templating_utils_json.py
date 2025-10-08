import os
import unittest
from unittest.mock import patch, Mock
from datetime import datetime, timezone
from templating_utils import process_templated_contents as process_templated_content_if_needed

class TestTemplatingUtilsJson(unittest.TestCase):
    def setUp(self):
        os.environ.pop('CONTENT_JSON', None)
        self.json_url = 'https://example.com/data.json'
        os.environ['CONTENT_JSON'] = self.json_url

    def tearDown(self):
        os.environ.pop('CONTENT_JSON', None)

    @patch('templating_utils.requests.get')
    def test_json_path_dot_and_bracket(self, mock_get):
        # Simulate JSON response
        mock_get.return_value = Mock(status_code=200)
        mock_get.return_value.json.return_value = {
            "stories": [
                {"description": "Desc1", "permalink": "url1"},
                {"description": "Desc2", "permalink": "url2"}
            ]
        }
        content = "API-driven: @{json.stories[0].description}, @{json.stories[0].permalink}"
        result, = process_templated_content_if_needed(content)
        self.assertIn("Desc1", result)
        self.assertIn("url1", result)
        self.assertNotIn("@{json.stories[0].description}", result)
        self.assertNotIn("@{json.stories[0].permalink}", result)

    @patch('templating_utils.requests.get')
    def test_json_path_missing(self, mock_get):
        mock_get.return_value = Mock(status_code=200)
        mock_get.return_value.json.return_value = {"foo": 123}
        content = "@{json.bar}"  # bar does not exist
        result, = process_templated_content_if_needed(content)
        self.assertEqual(result, "@{json.bar}")

    @patch('templating_utils.requests.get')
    def test_json_path_array_index_out_of_range(self, mock_get):
        mock_get.return_value = Mock(status_code=200)
        mock_get.return_value.json.return_value = {"arr": [1,2,3]}
        content = "@{json.arr[5]}"
        result, = process_templated_content_if_needed(content)
        self.assertEqual(result, "@{json.arr[5]}")

    @patch('templating_utils.requests.get')
    def test_json_path_non_string(self, mock_get):
        mock_get.return_value = Mock(status_code=200)
        mock_get.return_value.json.return_value = {"num": 42}
        content = "@{json.num}"
        result, = process_templated_content_if_needed(content)
        self.assertEqual(result, "42")

    @patch('templating_utils.requests.get')
    def test_json_pipeline_each_prefix_and_join(self, mock_get):
        mock_get.return_value = Mock(status_code=200)
        mock_get.return_value.json.return_value = {
            "genres": ["Mythology", "Tragedy", "Supernatural"]
        }
        content = "@{json.genres | each:prefix('#') | join(' ')}"
        result, = process_templated_content_if_needed(content)
        self.assertEqual(result, "#Mythology #Tragedy #Supernatural")

    @patch('templating_utils.requests.get')
    def test_json_join_warns_on_non_list(self, mock_get):
        mock_get.return_value = Mock(status_code=200)
        mock_get.return_value.json.return_value = {
            "description": "Simple"
        }
        content = "@{json.description | join(', ')}"
        result, = process_templated_content_if_needed(content)
        self.assertEqual(result, "Simple")

    @patch('templating_utils.requests.get')
    def test_json_fetch_fail(self, mock_get):
        mock_get.side_effect = Exception("fail")
        content = "@{json.foo}"
        result, = process_templated_content_if_needed(content)
        self.assertEqual(result, "@{json.foo}")

if __name__ == '__main__':
    unittest.main()
