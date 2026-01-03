"""Unit tests for JSON value conversion to string format."""

import os
import sys
import json
import tempfile
import unittest
from pathlib import Path

# Add common module to path
sys.path.insert(0, str(Path(__file__).parent))

from social_media_utils import (
    _convert_json_value_to_string,
    get_required_env_var,
    get_optional_env_var
)
import social_media_utils


class TestJSONValueConversion(unittest.TestCase):
    """Test JSON value conversion to string format."""
    
    def setUp(self):
        """Reset cache and environment before each test."""
        # Reset the global cache
        social_media_utils._json_config_cache = None
        social_media_utils._json_config_loaded = False
        
        # Clean up environment variables
        for key in ['INPUT_FILE', 'TEST_STRING', 'TEST_LIST', 'TEST_BOOL', 
                   'TEST_NUMBER', 'TEST_NULL', 'TEST_DICT']:
            os.environ.pop(key, None)
    
    def tearDown(self):
        """Clean up after each test."""
        # Reset the global cache
        social_media_utils._json_config_cache = None
        social_media_utils._json_config_loaded = False
        
        # Clean up environment variables
        for key in ['INPUT_FILE', 'TEST_STRING', 'TEST_LIST', 'TEST_BOOL',
                   'TEST_NUMBER', 'TEST_NULL', 'TEST_DICT', 'VIDEO_TAGS',
                   'VIDEO_MADE_FOR_KIDS', 'VIDEO_CONTAINS_SYNTHETIC_MEDIA',
                   'VIDEO_CATEGORY_ID', 'VIDEO_PRIVACY_STATUS', 'VIDEO_EMBEDDABLE']:
            os.environ.pop(key, None)
    
    def test_convert_string_value(self):
        """Test conversion of string value."""
        result = _convert_json_value_to_string("hello world")
        self.assertEqual(result, "hello world")
    
    def test_convert_list_value(self):
        """Test conversion of list to comma-separated string."""
        result = _convert_json_value_to_string(["tag1", "tag2", "tag3"])
        self.assertEqual(result, "tag1,tag2,tag3")
    
    def test_convert_mixed_list_value(self):
        """Test conversion of list with mixed types."""
        result = _convert_json_value_to_string(["classic", 123, "frog"])
        self.assertEqual(result, "classic,123,frog")
    
    def test_convert_bool_true(self):
        """Test conversion of boolean true."""
        result = _convert_json_value_to_string(True)
        self.assertEqual(result, "true")
    
    def test_convert_bool_false(self):
        """Test conversion of boolean false."""
        result = _convert_json_value_to_string(False)
        self.assertEqual(result, "false")
    
    def test_convert_integer(self):
        """Test conversion of integer."""
        result = _convert_json_value_to_string(24)
        self.assertEqual(result, "24")
    
    def test_convert_float(self):
        """Test conversion of float."""
        result = _convert_json_value_to_string(3.14)
        self.assertEqual(result, "3.14")
    
    def test_convert_null(self):
        """Test conversion of None/null."""
        result = _convert_json_value_to_string(None)
        self.assertEqual(result, "")
    
    def test_convert_dict(self):
        """Test conversion of dictionary to JSON string."""
        result = _convert_json_value_to_string({"key": "value"})
        self.assertEqual(result, '{"key": "value"}')
    
    def test_convert_empty_list(self):
        """Test conversion of empty list."""
        result = _convert_json_value_to_string([])
        self.assertEqual(result, "")
    
    def test_get_required_env_var_with_list_from_json(self):
        """Test getting list value from JSON config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            os.chdir(tmpdir)
            
            # Create input.json with list value
            config_data = {
                "VIDEO_TAGS": ["classic", "moral", "frog"]
            }
            with open("input.json", "w") as f:
                json.dump(config_data, f)
            
            value = get_required_env_var("VIDEO_TAGS")
            self.assertEqual(value, "classic,moral,frog")
    
    def test_get_required_env_var_with_bool_from_json(self):
        """Test getting boolean value from JSON config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            os.chdir(tmpdir)
            
            # Create input.json with boolean value
            config_data = {
                "VIDEO_MADE_FOR_KIDS": False
            }
            with open("input.json", "w") as f:
                json.dump(config_data, f)
            
            value = get_required_env_var("VIDEO_MADE_FOR_KIDS")
            self.assertEqual(value, "false")
    
    def test_get_optional_env_var_with_number_from_json(self):
        """Test getting number value from JSON config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            os.chdir(tmpdir)
            
            # Create input.json with number value
            config_data = {
                "VIDEO_CATEGORY_ID": 24
            }
            with open("input.json", "w") as f:
                json.dump(config_data, f)
            
            value = get_optional_env_var("VIDEO_CATEGORY_ID", "22")
            self.assertEqual(value, "24")
    
    def test_get_optional_env_var_with_bool_true_from_json(self):
        """Test getting boolean true value from JSON config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            os.chdir(tmpdir)
            
            # Create input.json with boolean value
            config_data = {
                "VIDEO_CONTAINS_SYNTHETIC_MEDIA": True
            }
            with open("input.json", "w") as f:
                json.dump(config_data, f)
            
            value = get_optional_env_var("VIDEO_CONTAINS_SYNTHETIC_MEDIA", "")
            self.assertEqual(value, "true")
    
    def test_complex_youtube_config(self):
        """Test with a complex YouTube configuration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            os.chdir(tmpdir)
            
            # Create input.json with various value types
            config_data = {
                "VIDEO_TAGS": ["classic", "moral", "frog", "ox"],
                "VIDEO_MADE_FOR_KIDS": False,
                "VIDEO_CONTAINS_SYNTHETIC_MEDIA": True,
                "VIDEO_CATEGORY_ID": 24,
                "VIDEO_PRIVACY_STATUS": "public",
                "VIDEO_EMBEDDABLE": True
            }
            with open("input.json", "w") as f:
                json.dump(config_data, f)
            
            # Test each value
            tags = get_optional_env_var("VIDEO_TAGS", "")
            self.assertEqual(tags, "classic,moral,frog,ox")
            
            made_for_kids = get_optional_env_var("VIDEO_MADE_FOR_KIDS", "false")
            self.assertEqual(made_for_kids, "false")
            
            synthetic = get_optional_env_var("VIDEO_CONTAINS_SYNTHETIC_MEDIA", "")
            self.assertEqual(synthetic, "true")
            
            category = get_optional_env_var("VIDEO_CATEGORY_ID", "22")
            self.assertEqual(category, "24")
            
            privacy = get_optional_env_var("VIDEO_PRIVACY_STATUS", "public")
            self.assertEqual(privacy, "public")
            
            embeddable = get_optional_env_var("VIDEO_EMBEDDABLE", "true")
            self.assertEqual(embeddable, "true")
    
    def test_env_var_overrides_json_list(self):
        """Test that environment variable overrides JSON list value."""
        with tempfile.TemporaryDirectory() as tmpdir:
            os.chdir(tmpdir)
            
            # Create input.json with list value
            config_data = {
                "VIDEO_TAGS": ["json", "tags"]
            }
            with open("input.json", "w") as f:
                json.dump(config_data, f)
            
            # Set environment variable
            os.environ['VIDEO_TAGS'] = "env,tags"
            
            value = get_optional_env_var("VIDEO_TAGS", "")
            self.assertEqual(value, "env,tags")


if __name__ == '__main__':
    unittest.main()
