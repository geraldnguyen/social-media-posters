#!/usr/bin/env python3
"""
Unit tests for scheduling utilities in social_media_utils.py
"""

import unittest
import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta
from unittest.mock import patch

# Add common module to path
sys.path.insert(0, str(Path(__file__).parent))

from social_media_utils import parse_scheduled_time, _parse_offset_time


class TestParseScheduledTime(unittest.TestCase):
    """Test cases for parse_scheduled_time function."""
    
    def test_parse_none(self):
        """Test parsing None returns None."""
        result = parse_scheduled_time(None)
        self.assertIsNone(result)
    
    def test_parse_empty_string(self):
        """Test parsing empty string returns None."""
        result = parse_scheduled_time("")
        self.assertIsNone(result)
    
    def test_parse_whitespace(self):
        """Test parsing whitespace returns None."""
        result = parse_scheduled_time("   ")
        self.assertIsNone(result)
    
    def test_parse_iso8601_with_z(self):
        """Test parsing ISO 8601 datetime with Z timezone."""
        result = parse_scheduled_time("2024-12-31T23:59:59Z")
        self.assertEqual(result, "2024-12-31T23:59:59Z")
    
    def test_parse_iso8601_with_offset(self):
        """Test parsing ISO 8601 datetime with timezone offset."""
        result = parse_scheduled_time("2024-12-31T23:59:59+00:00")
        self.assertEqual(result, "2024-12-31T23:59:59Z")
    
    def test_parse_iso8601_with_different_offset(self):
        """Test parsing ISO 8601 datetime with non-UTC timezone."""
        # 2024-12-31T23:59:59+05:00 should convert to 2024-12-31T18:59:59Z
        result = parse_scheduled_time("2024-12-31T23:59:59+05:00")
        self.assertEqual(result, "2024-12-31T18:59:59Z")
    
    def test_parse_iso8601_without_timezone(self):
        """Test parsing ISO 8601 datetime without timezone (assumes UTC)."""
        result = parse_scheduled_time("2024-12-31T23:59:59")
        self.assertEqual(result, "2024-12-31T23:59:59Z")
    
    def test_parse_offset_days(self):
        """Test parsing offset format with days."""
        # Mock the current time to get predictable results
        mock_now = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        with patch('social_media_utils.datetime') as mock_datetime:
            mock_datetime.now.return_value = mock_now
            mock_datetime.strftime = datetime.strftime
            # Need to mock the timedelta as well
            with patch('social_media_utils.timedelta', side_effect=timedelta):
                result = parse_scheduled_time("+1d")
                expected = (mock_now + timedelta(days=1)).strftime('%Y-%m-%dT%H:%M:%SZ')
                self.assertEqual(result, expected)
    
    def test_parse_offset_hours(self):
        """Test parsing offset format with hours."""
        mock_now = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        with patch('social_media_utils.datetime') as mock_datetime:
            mock_datetime.now.return_value = mock_now
            mock_datetime.strftime = datetime.strftime
            with patch('social_media_utils.timedelta', side_effect=timedelta):
                result = parse_scheduled_time("+2h")
                expected = (mock_now + timedelta(hours=2)).strftime('%Y-%m-%dT%H:%M:%SZ')
                self.assertEqual(result, expected)
    
    def test_parse_offset_minutes(self):
        """Test parsing offset format with minutes."""
        mock_now = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        with patch('social_media_utils.datetime') as mock_datetime:
            mock_datetime.now.return_value = mock_now
            mock_datetime.strftime = datetime.strftime
            with patch('social_media_utils.timedelta', side_effect=timedelta):
                result = parse_scheduled_time("+30m")
                expected = (mock_now + timedelta(minutes=30)).strftime('%Y-%m-%dT%H:%M:%SZ')
                self.assertEqual(result, expected)
    
    def test_parse_invalid_offset_no_unit(self):
        """Test parsing invalid offset format without time unit."""
        with self.assertRaises(ValueError) as cm:
            parse_scheduled_time("+10")
        self.assertIn("Invalid offset format", str(cm.exception))
    
    def test_parse_invalid_offset_bad_unit(self):
        """Test parsing invalid offset format with invalid time unit."""
        with self.assertRaises(ValueError) as cm:
            parse_scheduled_time("+10s")
        self.assertIn("Invalid offset format", str(cm.exception))
    
    def test_parse_invalid_offset_negative(self):
        """Test parsing invalid offset format with negative value."""
        with self.assertRaises(ValueError) as cm:
            parse_scheduled_time("-1d")
        self.assertIn("Invalid scheduled time format", str(cm.exception))
    
    def test_parse_invalid_datetime(self):
        """Test parsing invalid datetime string."""
        with self.assertRaises(ValueError) as cm:
            parse_scheduled_time("not-a-date")
        self.assertIn("Invalid scheduled time format", str(cm.exception))


class TestParseOffsetTime(unittest.TestCase):
    """Test cases for _parse_offset_time function."""
    
    def test_parse_offset_1_day(self):
        """Test parsing +1d offset."""
        mock_now = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        with patch('social_media_utils.datetime') as mock_datetime:
            mock_datetime.now.return_value = mock_now
            mock_datetime.strftime = datetime.strftime
            with patch('social_media_utils.timedelta', side_effect=timedelta):
                result = _parse_offset_time("+1d")
                self.assertEqual(result, "2024-01-02T12:00:00Z")
    
    def test_parse_offset_7_days(self):
        """Test parsing +7d offset."""
        mock_now = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        with patch('social_media_utils.datetime') as mock_datetime:
            mock_datetime.now.return_value = mock_now
            mock_datetime.strftime = datetime.strftime
            with patch('social_media_utils.timedelta', side_effect=timedelta):
                result = _parse_offset_time("+7d")
                self.assertEqual(result, "2024-01-08T12:00:00Z")
    
    def test_parse_offset_24_hours(self):
        """Test parsing +24h offset."""
        mock_now = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        with patch('social_media_utils.datetime') as mock_datetime:
            mock_datetime.now.return_value = mock_now
            mock_datetime.strftime = datetime.strftime
            with patch('social_media_utils.timedelta', side_effect=timedelta):
                result = _parse_offset_time("+24h")
                self.assertEqual(result, "2024-01-02T12:00:00Z")
    
    def test_parse_offset_90_minutes(self):
        """Test parsing +90m offset."""
        mock_now = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        with patch('social_media_utils.datetime') as mock_datetime:
            mock_datetime.now.return_value = mock_now
            mock_datetime.strftime = datetime.strftime
            with patch('social_media_utils.timedelta', side_effect=timedelta):
                result = _parse_offset_time("+90m")
                self.assertEqual(result, "2024-01-01T13:30:00Z")
    
    def test_parse_offset_invalid_format(self):
        """Test parsing invalid offset format."""
        with self.assertRaises(ValueError) as cm:
            _parse_offset_time("+1x")
        self.assertIn("Invalid offset format", str(cm.exception))
    
    def test_parse_offset_no_plus(self):
        """Test parsing offset without plus sign."""
        with self.assertRaises(ValueError) as cm:
            _parse_offset_time("1d")
        self.assertIn("Invalid offset format", str(cm.exception))
    
    def test_parse_offset_zero(self):
        """Test parsing +0d offset (edge case)."""
        mock_now = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        with patch('social_media_utils.datetime') as mock_datetime:
            mock_datetime.now.return_value = mock_now
            mock_datetime.strftime = datetime.strftime
            with patch('social_media_utils.timedelta', side_effect=timedelta):
                result = _parse_offset_time("+0d")
                self.assertEqual(result, "2024-01-01T12:00:00Z")


if __name__ == '__main__':
    unittest.main()
