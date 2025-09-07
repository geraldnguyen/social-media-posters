import os
import unittest
from unittest.mock import patch, Mock
from templating_utils import process_templated_content_if_needed

class TestContentJsonWithExtraction(unittest.TestCase):
    @patch('templating_utils.requests.get')
    def test_content_json_with_extraction(self, mock_get):
        # Simulate JSON at the URL
        mock_json = {
            "stories": [
                {"description": "Desc1", "permalink": "https://link1"},
                {"description": "Desc2", "permalink": "https://link2"}
            ]
        }
        mock_get.return_value = Mock(status_code=200)
        mock_get.return_value.json.return_value = mock_json
        # Set CONTENT_JSON to URL | path
        os.environ['CONTENT_JSON'] = "https://example.com/data.json | stories[0]"
        # POST_CONTENT uses fields from the sub-JSON
        content = "API-driven: @{json.description}, @{json.permalink}"
        result = process_templated_content_if_needed(content)
        self.assertIn("Desc1", result)
        self.assertIn("https://link1", result)
        self.assertNotIn("@{json.description}", result)
        self.assertNotIn("@{json.permalink}", result)

    @patch('templating_utils.requests.get')
    def test_content_json_with_extraction_missing_key(self, mock_get):
        mock_json = {"stories": [{"foo": 123}]}
        mock_get.return_value = Mock(status_code=200)
        mock_get.return_value.json.return_value = mock_json
        os.environ['CONTENT_JSON'] = "https://example.com/data.json | stories[0]"
        content = "@{json.description}"
        result = process_templated_content_if_needed(content)
        self.assertEqual(result, "@{json.description}")

if __name__ == "__main__":
    unittest.main()
