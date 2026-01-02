"""Unit tests for JSON config loading functionality."""

import os
import sys
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

# Add common module to path
sys.path.insert(0, str(Path(__file__).parent))

from social_media_utils import (
    load_json_config,
    get_required_env_var,
    get_optional_env_var,
    _json_config_cache,
    _json_config_loaded
)
import social_media_utils


class TestJSONConfigLoading(unittest.TestCase):
    """Test JSON config file loading functionality."""
    
    def setUp(self):
        """Reset cache and environment before each test."""
        # Reset the global cache
        social_media_utils._json_config_cache = None
        social_media_utils._json_config_loaded = False
        
        # Clean up environment variables
        for key in ['INPUT_FILE', 'TEST_VAR', 'TEST_REQUIRED', 'TEST_OPTIONAL']:
            os.environ.pop(key, None)
    
    def tearDown(self):
        """Clean up after each test."""
        # Reset the global cache
        social_media_utils._json_config_cache = None
        social_media_utils._json_config_loaded = False
        
        # Clean up environment variables
        for key in ['INPUT_FILE', 'TEST_VAR', 'TEST_REQUIRED', 'TEST_OPTIONAL']:
            os.environ.pop(key, None)
    
    def test_load_json_config_file_not_exists(self):
        """Test loading when JSON config file doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            os.chdir(tmpdir)
            config = load_json_config()
            self.assertIsNone(config)
    
    def test_load_json_config_default_file(self):
        """Test loading from default input.json file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            os.chdir(tmpdir)
            
            # Create input.json
            config_data = {"TEST_VAR": "test_value", "ANOTHER_VAR": "another_value"}
            with open("input.json", "w") as f:
                json.dump(config_data, f)
            
            config = load_json_config()
            self.assertIsNotNone(config)
            self.assertEqual(config["TEST_VAR"], "test_value")
            self.assertEqual(config["ANOTHER_VAR"], "another_value")
    
    def test_load_json_config_custom_file(self):
        """Test loading from custom JSON file specified via INPUT_FILE."""
        with tempfile.TemporaryDirectory() as tmpdir:
            os.chdir(tmpdir)
            
            # Create custom config file
            config_data = {"CUSTOM_VAR": "custom_value"}
            custom_file = os.path.join(tmpdir, "custom_config.json")
            with open(custom_file, "w") as f:
                json.dump(config_data, f)
            
            os.environ['INPUT_FILE'] = custom_file
            config = load_json_config()
            self.assertIsNotNone(config)
            self.assertEqual(config["CUSTOM_VAR"], "custom_value")
    
    def test_load_json_config_relative_path(self):
        """Test loading from relative path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            os.chdir(tmpdir)
            
            # Create config file
            config_data = {"RELATIVE_VAR": "relative_value"}
            with open("config.json", "w") as f:
                json.dump(config_data, f)
            
            os.environ['INPUT_FILE'] = "config.json"
            config = load_json_config()
            self.assertIsNotNone(config)
            self.assertEqual(config["RELATIVE_VAR"], "relative_value")
    
    def test_load_json_config_invalid_json(self):
        """Test loading when JSON file is invalid."""
        with tempfile.TemporaryDirectory() as tmpdir:
            os.chdir(tmpdir)
            
            # Create invalid JSON file
            with open("input.json", "w") as f:
                f.write("{ invalid json }")
            
            config = load_json_config()
            self.assertIsNone(config)
    
    def test_load_json_config_caching(self):
        """Test that config is cached after first load."""
        with tempfile.TemporaryDirectory() as tmpdir:
            os.chdir(tmpdir)
            
            # Create input.json
            config_data = {"CACHED_VAR": "cached_value"}
            with open("input.json", "w") as f:
                json.dump(config_data, f)
            
            # Load first time
            config1 = load_json_config()
            self.assertIsNotNone(config1)
            
            # Modify the file
            config_data = {"CACHED_VAR": "modified_value"}
            with open("input.json", "w") as f:
                json.dump(config_data, f)
            
            # Load second time - should return cached value
            config2 = load_json_config()
            self.assertEqual(config1, config2)
            self.assertEqual(config2["CACHED_VAR"], "cached_value")
    
    def test_get_required_env_var_from_env(self):
        """Test getting required var from environment."""
        os.environ['TEST_REQUIRED'] = 'env_value'
        value = get_required_env_var('TEST_REQUIRED')
        self.assertEqual(value, 'env_value')
    
    def test_get_required_env_var_from_json(self):
        """Test getting required var from JSON config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            os.chdir(tmpdir)
            
            # Create input.json
            config_data = {"TEST_REQUIRED": "json_value"}
            with open("input.json", "w") as f:
                json.dump(config_data, f)
            
            value = get_required_env_var('TEST_REQUIRED')
            self.assertEqual(value, 'json_value')
    
    def test_get_required_env_var_env_takes_precedence(self):
        """Test that environment variable takes precedence over JSON config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            os.chdir(tmpdir)
            
            # Create input.json
            config_data = {"TEST_REQUIRED": "json_value"}
            with open("input.json", "w") as f:
                json.dump(config_data, f)
            
            os.environ['TEST_REQUIRED'] = 'env_value'
            value = get_required_env_var('TEST_REQUIRED')
            self.assertEqual(value, 'env_value')
    
    def test_get_required_env_var_not_found(self):
        """Test that missing required var exits with error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            os.chdir(tmpdir)
            
            with self.assertRaises(SystemExit) as cm:
                get_required_env_var('MISSING_VAR')
            self.assertEqual(cm.exception.code, 1)
    
    def test_get_optional_env_var_from_env(self):
        """Test getting optional var from environment."""
        os.environ['TEST_OPTIONAL'] = 'env_value'
        value = get_optional_env_var('TEST_OPTIONAL', 'default_value')
        self.assertEqual(value, 'env_value')
    
    def test_get_optional_env_var_from_json(self):
        """Test getting optional var from JSON config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            os.chdir(tmpdir)
            
            # Create input.json
            config_data = {"TEST_OPTIONAL": "json_value"}
            with open("input.json", "w") as f:
                json.dump(config_data, f)
            
            value = get_optional_env_var('TEST_OPTIONAL', 'default_value')
            self.assertEqual(value, 'json_value')
    
    def test_get_optional_env_var_default(self):
        """Test getting optional var with default when not found."""
        with tempfile.TemporaryDirectory() as tmpdir:
            os.chdir(tmpdir)
            
            value = get_optional_env_var('MISSING_VAR', 'default_value')
            self.assertEqual(value, 'default_value')
    
    def test_get_optional_env_var_env_takes_precedence(self):
        """Test that environment variable takes precedence over JSON config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            os.chdir(tmpdir)
            
            # Create input.json
            config_data = {"TEST_OPTIONAL": "json_value"}
            with open("input.json", "w") as f:
                json.dump(config_data, f)
            
            os.environ['TEST_OPTIONAL'] = 'env_value'
            value = get_optional_env_var('TEST_OPTIONAL', 'default_value')
            self.assertEqual(value, 'env_value')


if __name__ == '__main__':
    unittest.main()
