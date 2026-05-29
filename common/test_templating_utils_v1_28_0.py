import os
import unittest
from unittest.mock import patch, Mock

from templating_utils import process_templated_contents


class TestTemplatingUtilsV1_28_0(unittest.TestCase):
    def setUp(self):
        os.environ.pop('CONTENT_JSON', None)
        os.environ['CONTENT_JSON'] = 'https://example.com/data.json'

    def tearDown(self):
        os.environ.pop('CONTENT_JSON', None)

    @patch('templating_utils.requests.get')
    def test_double_pipe_truthy_short_circuit(self, mock_get):
        mock_get.return_value = Mock(status_code=200)
        mock_get.return_value.json.return_value = {
            "youtube_link": "https://youtube.com/watch?v=123",
            "permalink": "https://example.com/article"
        }
        content = "@{json.youtube_link || json.permalink}"
        result, = process_templated_contents(content)
        self.assertEqual(result, "https://youtube.com/watch?v=123")

    @patch('templating_utils.requests.get')
    def test_double_pipe_falsy_uses_value_expression(self, mock_get):
        mock_get.return_value = Mock(status_code=200)
        mock_get.return_value.json.return_value = {
            "youtube_link": "",
            "permalink": "https://example.com/article"
        }
        content = "@{json.youtube_link || json.permalink}"
        result, = process_templated_contents(content)
        self.assertEqual(result, "https://example.com/article")

    @patch('templating_utils.requests.get')
    def test_double_pipe_falsy_uses_literal(self, mock_get):
        mock_get.return_value = Mock(status_code=200)
        mock_get.return_value.json.return_value = {
            "youtube_link": ""
        }
        content = "@{json.youtube_link || 'default-link'}"
        result, = process_templated_contents(content)
        self.assertEqual(result, "default-link")

    @patch('templating_utils.requests.get')
    def test_double_pipe_rhs_function_expression(self, mock_get):
        mock_get.return_value = Mock(status_code=200)
        mock_get.return_value.json.return_value = {
            "youtube_link": "",
            "permalink": "https://example.com/article"
        }
        content = "@{json.youtube_link || or json.permalink}"
        result, = process_templated_contents(content)
        self.assertEqual(result, "https://example.com/article")

    @patch('templating_utils.requests.get')
    def test_double_pipe_truthy_skips_rhs_pipeline(self, mock_get):
        mock_get.return_value = Mock(status_code=200)
        mock_get.return_value.json.return_value = {
            "title": "Full Title",
            "fallback": "fallback title"
        }
        content = "@{json.title || json.fallback | max_length(4, '...')}"
        result, = process_templated_contents(content)
        self.assertEqual(result, "Full Title")

    @patch('templating_utils.requests.get')
    def test_double_pipe_chained(self, mock_get):
        mock_get.return_value = Mock(status_code=200)
        mock_get.return_value.json.return_value = {
            "primary": "",
            "secondary": "second-value"
        }
        content = "@{json.primary || json.secondary || 'default'}"
        result, = process_templated_contents(content)
        self.assertEqual(result, "second-value")


if __name__ == '__main__':
    unittest.main()
