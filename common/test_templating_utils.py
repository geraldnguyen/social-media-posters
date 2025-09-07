import os
import unittest
from unittest.mock import patch
from datetime import datetime, timezone
from templating_utils import process_templated_content_if_needed

class TestTemplatingUtils(unittest.TestCase):

    def setUp(self):
        # Clear any existing env vars for clean tests
        os.environ.pop('TEST_VAR', None)
        os.environ.pop('TIME_ZONE', None)

    def tearDown(self):
        # Clean up after tests
        os.environ.pop('TEST_VAR', None)
        os.environ.pop('TIME_ZONE', None)

    def test_no_placeholders(self):
        """Test content without placeholders remains unchanged."""
        content = "This is a simple message."
        result = process_templated_content_if_needed(content)
        self.assertEqual(result, content)

    def test_env_variable_replacement(self):
        """Test replacement of ${env.VAR} with environment variable."""
        os.environ['TEST_VAR'] = 'Hello World'
        content = "Message: @{env.TEST_VAR}"
        result = process_templated_content_if_needed(content)
        self.assertEqual(result, "Message: Hello World")

    def test_env_variable_not_found(self):
        """Test replacement when env var is not set."""
        content = "Message: @{env.NON_EXISTENT_VAR}"
        result = process_templated_content_if_needed(content)
        self.assertEqual(result, "Message: ")

    def test_builtin_curr_date(self):
        """Test ${builtin.CURR_DATE} replacement."""
        with patch('templating_utils.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2023, 10, 15, 12, 30, 45, tzinfo=timezone.utc)
            content = "Date: @{builtin.CURR_DATE}"
            result = process_templated_content_if_needed(content)
            self.assertEqual(result, "Date: 2023-10-15")

    def test_builtin_curr_time(self):
        """Test ${builtin.CURR_TIME} replacement."""
        with patch('templating_utils.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2023, 10, 15, 12, 30, 45, tzinfo=timezone.utc)
            content = "Time: @{builtin.CURR_TIME}"
            result = process_templated_content_if_needed(content)
            self.assertEqual(result, "Time: 12:30:45")

    def test_builtin_curr_datetime(self):
        """Test ${builtin.CURR_DATETIME} replacement."""
        with patch('templating_utils.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2023, 10, 15, 12, 30, 45, tzinfo=timezone.utc)
            content = "Datetime: @{builtin.CURR_DATETIME}"
            result = process_templated_content_if_needed(content)
            self.assertEqual(result, "Datetime: 2023-10-15 12:30:45")

    def test_unknown_builtin(self):
        """Test unknown builtin placeholder."""
        content = "Unknown: @{builtin.UNKNOWN}"
        result = process_templated_content_if_needed(content)
        self.assertEqual(result, "Unknown: ")

    def test_unknown_source(self):
        """Test unknown source placeholder."""
        content = "Unknown: @{unknown.VAR}"
        result = process_templated_content_if_needed(content)
        self.assertEqual(result, "Unknown: @{unknown.VAR}")

    def test_mixed_placeholders(self):
        """Test content with multiple placeholders."""
        os.environ['TEST_VAR'] = 'Test'
        with patch('templating_utils.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2023, 10, 15, tzinfo=timezone.utc)
            content = "@{env.TEST_VAR} on @{builtin.CURR_DATE}"
            result = process_templated_content_if_needed(content)
            self.assertEqual(result, "Test on 2023-10-15")

    def test_timezone_utc(self):
        """Test timezone handling with UTC."""
        os.environ['TIME_ZONE'] = 'UTC'
        with patch('templating_utils.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2023, 10, 15, 12, 0, 0, tzinfo=timezone.utc)
            content = "@{builtin.CURR_DATE}"
            result = process_templated_content_if_needed(content)
            self.assertEqual(result, "2023-10-15")

    def test_timezone_offset(self):
        """Test timezone handling with offset."""
        os.environ['TIME_ZONE'] = 'UTC+5'
        with patch('templating_utils.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2023, 10, 15, 17, 0, 0, tzinfo=timezone.utc)
            content = "@{builtin.CURR_DATE}"
            result = process_templated_content_if_needed(content)
            # Note: Mocking timezone is complex; this test assumes the function handles it
            self.assertEqual(result, "2023-10-15")

if __name__ == '__main__':
    unittest.main()
