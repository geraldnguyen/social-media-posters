import os
import unittest
from unittest.mock import patch, Mock
from templating_utils import process_templated_content_if_needed

class TestContentJsonRandom(unittest.TestCase):
    @patch('templating_utils.requests.get')
    @patch('random.randint', return_value=1)
    def test_content_json_with_random(self, mock_randint, mock_get):
        # Simulate JSON at the URL
        mock_json = {
            "stories": [
                {"description": "Desc1", "permalink": "https://link1"},
                {"description": "Desc2", "permalink": "https://link2"},
                {"description": "Desc3", "permalink": "https://link3"}
            ]
        }
        mock_get.return_value = Mock(status_code=200)
        mock_get.return_value.json.return_value = mock_json
        os.environ['CONTENT_JSON'] = "https://example.com/data.json | stories[RANDOM]"
        content = "API-driven: @{json.description}, @{json.permalink}"
        result = process_templated_content_if_needed(content)
        self.assertIn("Desc2", result)
        self.assertIn("https://link2", result)
        self.assertNotIn("@{json.description}", result)
        self.assertNotIn("@{json.permalink}", result)

    @patch('templating_utils.requests.get')
    @patch('random.randint', return_value=0)
    def test_content_json_with_random_first(self, mock_randint, mock_get):
        mock_json = {
            "stories": [
                {"description": "Desc1", "permalink": "https://link1"},
                {"description": "Desc2", "permalink": "https://link2"}
            ]
        }
        mock_get.return_value = Mock(status_code=200)
        mock_get.return_value.json.return_value = mock_json
        os.environ['CONTENT_JSON'] = "https://example.com/data.json | stories[RANDOM]"
        content = "@{json.description}"
        result = process_templated_content_if_needed(content)
        self.assertEqual(result, "Desc1")

    @patch('templating_utils.requests.get')
    @patch('random.randint', return_value=0)
    def test_content_json_with_random_empty(self, mock_randint, mock_get):
        mock_json = {"stories": []}
        mock_get.return_value = Mock(status_code=200)
        mock_get.return_value.json.return_value = mock_json
        os.environ['CONTENT_JSON'] = "https://example.com/data.json | stories[RANDOM]"
        content = "@{json.description}"
        result = process_templated_content_if_needed(content)
        self.assertEqual(result, "@{json.description}")

if __name__ == "__main__":
    unittest.main()
