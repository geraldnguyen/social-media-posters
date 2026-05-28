import os
import unittest
from unittest.mock import Mock, patch

from templating_utils import process_templated_contents


class TestTemplatingUtilsTLNWShortener(unittest.TestCase):
    def setUp(self):
        os.environ['CONTENT_JSON'] = 'https://example.com/data.json'
        os.environ.pop('TLNW_CLIENT_ID', None)
        os.environ.pop('TLNW_CLIENT_SECRET', None)

    def tearDown(self):
        os.environ.pop('CONTENT_JSON', None)
        os.environ.pop('TLNW_CLIENT_ID', None)
        os.environ.pop('TLNW_CLIENT_SECRET', None)

    @patch('templating_utils.requests.post')
    @patch('templating_utils.requests.get')
    def test_tlnw_shorten_url_success(self, mock_get, mock_post):
        mock_get.return_value = Mock(status_code=200)
        mock_get.return_value.json.return_value = {"permalink": "https://example.com/very/long/url"}
        mock_post.return_value = Mock(status_code=200)
        mock_post.return_value.json.return_value = {"short": "https://go.tlnw.uk/EsMoIJef"}

        os.environ['TLNW_CLIENT_ID'] = 'test-client-id'
        os.environ['TLNW_CLIENT_SECRET'] = 'test-client-secret'

        content = "@{json.permalink | tlnw:shorten_url}"
        result, = process_templated_contents(content)

        self.assertEqual(result, "https://go.tlnw.uk/EsMoIJef")
        mock_post.assert_called_once_with(
            'https://go.tlnw.uk/shorten',
            headers={
                'x-client-id': 'test-client-id',
                'x-client-secret': 'test-client-secret',
            },
            json={'url': 'https://example.com/very/long/url'},
            timeout=10,
        )

    @patch('templating_utils.requests.post')
    @patch('templating_utils.requests.get')
    def test_tlnw_shorten_url_success_with_parentheses(self, mock_get, mock_post):
        mock_get.return_value = Mock(status_code=200)
        mock_get.return_value.json.return_value = {"permalink": "https://example.com/very/long/url"}
        mock_post.return_value = Mock(status_code=200)
        mock_post.return_value.json.return_value = {"short": "https://go.tlnw.uk/AbCdEf"}

        os.environ['TLNW_CLIENT_ID'] = 'test-client-id'
        os.environ['TLNW_CLIENT_SECRET'] = 'test-client-secret'

        content = "@{json.permalink | tlnw:shorten_url()}"
        result, = process_templated_contents(content)

        self.assertEqual(result, "https://go.tlnw.uk/AbCdEf")

    @patch('templating_utils.requests.get')
    def test_tlnw_shorten_url_missing_credentials(self, mock_get):
        mock_get.return_value = Mock(status_code=200)
        mock_get.return_value.json.return_value = {"permalink": "https://example.com/very/long/url"}

        with self.assertRaises(ValueError) as cm:
            process_templated_contents("@{json.permalink | tlnw:shorten_url}")

        self.assertIn("requires TLNW_CLIENT_ID and TLNW_CLIENT_SECRET", str(cm.exception))

    @patch('templating_utils.requests.post')
    @patch('templating_utils.requests.get')
    def test_tlnw_shorten_url_missing_short_in_response(self, mock_get, mock_post):
        mock_get.return_value = Mock(status_code=200)
        mock_get.return_value.json.return_value = {"permalink": "https://example.com/very/long/url"}
        mock_post.return_value = Mock(status_code=200)
        mock_post.return_value.json.return_value = {"created_at": "2026-05-28T03:05:25.827Z"}

        os.environ['TLNW_CLIENT_ID'] = 'test-client-id'
        os.environ['TLNW_CLIENT_SECRET'] = 'test-client-secret'

        with self.assertRaises(ValueError) as cm:
            process_templated_contents("@{json.permalink | tlnw:shorten_url}")

        self.assertIn("did not include a valid 'short' URL", str(cm.exception))


if __name__ == '__main__':
    unittest.main()
