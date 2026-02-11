"""Unit tests for value validation functionality."""

import unittest
import sys
from pathlib import Path

# Add common module to path
sys.path.insert(0, str(Path(__file__).parent))

from social_media_utils import is_value_empty_or_na


class TestIsValueEmptyOrNA(unittest.TestCase):
    """Test the is_value_empty_or_na function."""
    
    def test_none_value(self):
        """Test that None is considered empty."""
        self.assertTrue(is_value_empty_or_na(None))
    
    def test_empty_string(self):
        """Test that empty string is considered empty."""
        self.assertTrue(is_value_empty_or_na(""))
    
    def test_whitespace_only(self):
        """Test that whitespace-only strings are considered empty."""
        self.assertTrue(is_value_empty_or_na("   "))
        self.assertTrue(is_value_empty_or_na("\t"))
        self.assertTrue(is_value_empty_or_na("\n"))
        self.assertTrue(is_value_empty_or_na("  \t\n  "))
    
    def test_na_uppercase(self):
        """Test that N/A (uppercase) is considered empty."""
        self.assertTrue(is_value_empty_or_na("N/A"))
    
    def test_na_lowercase(self):
        """Test that n/a (lowercase) is considered empty."""
        self.assertTrue(is_value_empty_or_na("n/a"))
    
    def test_na_mixed_case(self):
        """Test that N/A with mixed case is considered empty."""
        self.assertTrue(is_value_empty_or_na("N/a"))
        self.assertTrue(is_value_empty_or_na("n/A"))
    
    def test_na_with_dots(self):
        """Test that n.a variations are considered empty."""
        self.assertTrue(is_value_empty_or_na("n.a"))
        self.assertTrue(is_value_empty_or_na("N.A"))
        self.assertTrue(is_value_empty_or_na("n.a."))
        self.assertTrue(is_value_empty_or_na("N.A."))
    
    def test_na_without_separator(self):
        """Test that 'na' without separator is considered empty."""
        self.assertTrue(is_value_empty_or_na("na"))
        self.assertTrue(is_value_empty_or_na("NA"))
        self.assertTrue(is_value_empty_or_na("Na"))
    
    def test_na_with_space(self):
        """Test that 'n a' with space is considered empty."""
        self.assertTrue(is_value_empty_or_na("n a"))
        self.assertTrue(is_value_empty_or_na("N A"))
    
    def test_not_applicable_full_text(self):
        """Test that 'not applicable' is considered empty."""
        self.assertTrue(is_value_empty_or_na("not applicable"))
        self.assertTrue(is_value_empty_or_na("Not Applicable"))
        self.assertTrue(is_value_empty_or_na("NOT APPLICABLE"))
        self.assertTrue(is_value_empty_or_na("Not applicable"))
    
    def test_not_applicable_without_space(self):
        """Test that 'notapplicable' without space is considered empty."""
        self.assertTrue(is_value_empty_or_na("notapplicable"))
        self.assertTrue(is_value_empty_or_na("NotApplicable"))
    
    def test_not_applicable_with_hyphen(self):
        """Test that 'not-applicable' with hyphen is considered empty."""
        self.assertTrue(is_value_empty_or_na("not-applicable"))
        self.assertTrue(is_value_empty_or_na("Not-Applicable"))
    
    def test_na_with_surrounding_whitespace(self):
        """Test that N/A variations with surrounding whitespace are considered empty."""
        self.assertTrue(is_value_empty_or_na("  n/a  "))
        self.assertTrue(is_value_empty_or_na("\tN/A\n"))
        self.assertTrue(is_value_empty_or_na("  not applicable  "))
    
    def test_valid_values_not_empty(self):
        """Test that valid non-N/A values are not considered empty."""
        self.assertFalse(is_value_empty_or_na("123456"))
        self.assertFalse(is_value_empty_or_na("video_id_abc123"))
        self.assertFalse(is_value_empty_or_na("post_12345"))
        self.assertFalse(is_value_empty_or_na("abc"))
        self.assertFalse(is_value_empty_or_na("This is a valid post"))
    
    def test_partial_na_not_empty(self):
        """Test that strings containing but not equal to N/A are not considered empty."""
        self.assertFalse(is_value_empty_or_na("This is n/a in the middle"))
        self.assertFalse(is_value_empty_or_na("n/a_video_123"))
        self.assertFalse(is_value_empty_or_na("post_n/a"))
        self.assertFalse(is_value_empty_or_na("banana"))
    
    def test_numbers_not_empty(self):
        """Test that numeric strings are not considered empty."""
        self.assertFalse(is_value_empty_or_na("0"))
        self.assertFalse(is_value_empty_or_na("1"))
        self.assertFalse(is_value_empty_or_na("123"))


if __name__ == '__main__':
    unittest.main()
