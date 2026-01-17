import os
import unittest
from unittest.mock import patch, Mock
from templating_utils import process_templated_contents

class TestProcessTemplatedContents(unittest.TestCase):
    @patch('templating_utils.requests.get')
    @patch('random.randint', return_value=1)
    def test_multiple_contents_with_random(self, mock_randint, mock_get):
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
        content1 = "API-driven: @{json.description}"
        content2 = "Link: @{json.permalink}"
        result1, result2 = process_templated_contents(content1, content2)
        self.assertIn("Desc2", result1)
        self.assertIn("https://link2", result2)
        self.assertNotIn("@{json.description}", result1)
        self.assertNotIn("@{json.permalink}", result2)

    @patch('templating_utils.requests.get')
    def test_multiple_contents_no_json(self, mock_get):
        mock_get.return_value = Mock(status_code=200)
        mock_get.return_value.json.return_value = {"key": "value"}
        os.environ['CONTENT_JSON'] = "https://example.com/data.json"
        content1 = "Env: @{env.TEST_VAR}"
        content2 = "Builtin: @{builtin.CURR_DATE}"
        result1, result2 = process_templated_contents(content1, content2)
        self.assertEqual(result1, "Env: ")
        # Check that result2 contains a date in YYYY-MM-DD format
        self.assertRegex(result2, r"Builtin: \d{4}-\d{2}-\d{2}")

    @patch('templating_utils.requests.get')
    def test_single_content(self, mock_get):
        mock_get.return_value = Mock(status_code=200)
        mock_get.return_value.json.return_value = {"message": "Hello"}
        os.environ['CONTENT_JSON'] = "https://example.com/data.json"
        result = process_templated_contents("Message: @{json.message}")
        self.assertEqual(result, ("Message: Hello",))

    @patch('templating_utils.requests.get')
    @patch('random.randint', return_value=0)
    def test_random_consistency(self, mock_randint, mock_get):
        # Ensure that [RANDOM] picks the same index for multiple contents
        mock_json = {
            "items": [
                {"name": "First", "url": "http://first"},
                {"name": "Second", "url": "http://second"}
            ]
        }
        mock_get.return_value = Mock(status_code=200)
        mock_get.return_value.json.return_value = mock_json
        os.environ['CONTENT_JSON'] = "https://example.com/data.json | items[RANDOM]"
        content1 = "@{json.name}"
        content2 = "@{json.url}"
        result1, result2 = process_templated_contents(content1, content2)
        self.assertEqual(result1, "First")
        self.assertEqual(result2, "http://first")

if __name__ == "__main__":
    unittest.main()