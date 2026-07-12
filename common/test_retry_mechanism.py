"""Unit tests for overall retry helpers."""

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import requests

# Add common module to path
sys.path.insert(0, str(Path(__file__).parent))

from social_media_utils import (
    _perform_request_with_retry,
    configure_requests_retry,
    parse_retry_spec,
    reset_requests_retry_for_tests,
)


class TestRetrySpecParsing(unittest.TestCase):
    """Validate RETRY format parsing."""

    def tearDown(self):
        os.environ.pop("RETRY", None)
        reset_requests_retry_for_tests()

    def test_parse_retry_spec_empty_returns_none(self):
        self.assertIsNone(parse_retry_spec(""))

    def test_parse_retry_spec_immediately(self):
        self.assertEqual(
            parse_retry_spec("3*immediately"),
            {
                "raw": "3*immediately",
                "retries": 3,
                "strategy": "immediately",
                "base_delay_seconds": 0,
            },
        )

    def test_parse_retry_spec_delay(self):
        self.assertEqual(
            parse_retry_spec("2*delay(5)"),
            {
                "raw": "2*delay(5)",
                "retries": 2,
                "strategy": "delay",
                "base_delay_seconds": 5,
            },
        )

    def test_parse_retry_spec_exp(self):
        self.assertEqual(
            parse_retry_spec("4*exp(3)"),
            {
                "raw": "4*exp(3)",
                "retries": 4,
                "strategy": "exp",
                "base_delay_seconds": 3,
            },
        )

    def test_parse_retry_spec_invalid_raises(self):
        with self.assertRaises(ValueError):
            parse_retry_spec("retry-later")

    def test_configure_requests_retry_reads_env(self):
        os.environ["RETRY"] = "1*delay(2)"

        retry_config = configure_requests_retry()

        self.assertEqual(retry_config["retries"], 1)
        self.assertEqual(retry_config["strategy"], "delay")
        self.assertEqual(retry_config["base_delay_seconds"], 2)


class TestRetryExecution(unittest.TestCase):
    """Validate retry execution behavior."""

    @patch("social_media_utils.time.sleep")
    def test_request_retries_on_retryable_status(self, mock_sleep):
        response_503 = MagicMock(spec=requests.Response)
        response_503.status_code = 503
        response_200 = MagicMock(spec=requests.Response)
        response_200.status_code = 200
        send_func = MagicMock(side_effect=[response_503, response_200])

        result = _perform_request_with_retry(
            send_func,
            "post",
            "https://example.com",
            {},
            parse_retry_spec("2*delay(4)"),
        )

        self.assertIs(result, response_200)
        self.assertEqual(send_func.call_count, 2)
        mock_sleep.assert_called_once_with(4)

    @patch("social_media_utils.time.sleep")
    def test_request_retries_on_connection_error(self, mock_sleep):
        response_200 = MagicMock(spec=requests.Response)
        response_200.status_code = 200
        send_func = MagicMock(
            side_effect=[requests.ConnectionError("boom"), response_200]
        )

        result = _perform_request_with_retry(
            send_func,
            "get",
            "https://example.com",
            {},
            parse_retry_spec("2*immediately"),
        )

        self.assertIs(result, response_200)
        self.assertEqual(send_func.call_count, 2)
        mock_sleep.assert_not_called()

    @patch("social_media_utils.time.sleep")
    def test_request_uses_exponential_backoff(self, mock_sleep):
        response_503_a = MagicMock(spec=requests.Response)
        response_503_a.status_code = 503
        response_503_b = MagicMock(spec=requests.Response)
        response_503_b.status_code = 503
        response_200 = MagicMock(spec=requests.Response)
        response_200.status_code = 200
        send_func = MagicMock(side_effect=[response_503_a, response_503_b, response_200])

        result = _perform_request_with_retry(
            send_func,
            "post",
            "https://example.com",
            {},
            parse_retry_spec("3*exp(2)"),
        )

        self.assertIs(result, response_200)
        self.assertEqual(send_func.call_count, 3)
        self.assertEqual(mock_sleep.call_args_list[0].args[0], 2)
        self.assertEqual(mock_sleep.call_args_list[1].args[0], 4)

    @patch("social_media_utils.time.sleep")
    def test_request_retries_on_known_transient_400_subcode(self, mock_sleep):
        response_400 = MagicMock(spec=requests.Response)
        response_400.status_code = 400
        response_400.json.return_value = {
            "error": {
                "message": "The requested resource does not exist",
                "error_subcode": 4279009,
                "is_transient": False,
            }
        }
        response_200 = MagicMock(spec=requests.Response)
        response_200.status_code = 200
        send_func = MagicMock(side_effect=[response_400, response_200])

        result = _perform_request_with_retry(
            send_func,
            "post",
            "https://graph.threads.net/user/threads_publish",
            {},
            parse_retry_spec("1*delay(5)"),
        )

        self.assertIs(result, response_200)
        self.assertEqual(send_func.call_count, 2)
        mock_sleep.assert_called_once_with(5)

    @patch("social_media_utils.time.sleep")
    def test_request_does_not_retry_non_retryable_status(self, mock_sleep):
        response_400 = MagicMock(spec=requests.Response)
        response_400.status_code = 400
        send_func = MagicMock(return_value=response_400)

        result = _perform_request_with_retry(
            send_func,
            "post",
            "https://example.com",
            {},
            parse_retry_spec("5*delay(3)"),
        )

        self.assertIs(result, response_400)
        self.assertEqual(send_func.call_count, 1)
        mock_sleep.assert_not_called()


if __name__ == "__main__":
    unittest.main()
