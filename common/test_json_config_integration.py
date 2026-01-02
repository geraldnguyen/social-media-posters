"""Integration tests for JSON config with post-to-x script."""

import os
import sys
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add common module to path
sys.path.insert(0, str(Path(__file__).parent))

import social_media_utils


class TestJSONConfigIntegration(unittest.TestCase):
    """Integration tests for JSON config loading with post scripts."""
    
    def setUp(self):
        """Reset cache and environment before each test."""
        # Reset the global cache
        social_media_utils._json_config_cache = None
        social_media_utils._json_config_loaded = False
        
        # Clean up environment variables
        env_vars = ['INPUT_FILE', 'POST_CONTENT', 'X_API_KEY', 'X_API_SECRET', 
                   'X_ACCESS_TOKEN', 'X_ACCESS_TOKEN_SECRET', 'LOG_LEVEL',
                   'MEDIA_FILES', 'DRY_RUN', 'CONTENT_JSON']
        for key in env_vars:
            os.environ.pop(key, None)
    
    def tearDown(self):
        """Clean up after each test."""
        # Reset the global cache
        social_media_utils._json_config_cache = None
        social_media_utils._json_config_loaded = False
        
        # Clean up environment variables
        env_vars = ['INPUT_FILE', 'POST_CONTENT', 'X_API_KEY', 'X_API_SECRET',
                   'X_ACCESS_TOKEN', 'X_ACCESS_TOKEN_SECRET', 'LOG_LEVEL',
                   'MEDIA_FILES', 'DRY_RUN', 'CONTENT_JSON']
        for key in env_vars:
            os.environ.pop(key, None)
    
    def test_load_config_from_json_for_x(self):
        """Test loading X (Twitter) config from JSON file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            os.chdir(tmpdir)
            
            # Create input.json with X credentials
            config_data = {
                "X_API_KEY": "test_api_key",
                "X_API_SECRET": "test_api_secret",
                "X_ACCESS_TOKEN": "test_access_token",
                "X_ACCESS_TOKEN_SECRET": "test_access_token_secret",
                "POST_CONTENT": "Test post from JSON config",
                "LOG_LEVEL": "DEBUG"
            }
            with open("input.json", "w") as f:
                json.dump(config_data, f)
            
            # Load config using the utility functions
            from social_media_utils import get_required_env_var, get_optional_env_var
            
            api_key = get_required_env_var("X_API_KEY")
            api_secret = get_required_env_var("X_API_SECRET")
            access_token = get_required_env_var("X_ACCESS_TOKEN")
            access_token_secret = get_required_env_var("X_ACCESS_TOKEN_SECRET")
            content = get_required_env_var("POST_CONTENT")
            log_level = get_optional_env_var("LOG_LEVEL", "INFO")
            
            self.assertEqual(api_key, "test_api_key")
            self.assertEqual(api_secret, "test_api_secret")
            self.assertEqual(access_token, "test_access_token")
            self.assertEqual(access_token_secret, "test_access_token_secret")
            self.assertEqual(content, "Test post from JSON config")
            self.assertEqual(log_level, "DEBUG")
    
    def test_load_config_from_custom_json_file(self):
        """Test loading config from custom JSON file path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            os.chdir(tmpdir)
            
            # Create custom config file
            config_data = {
                "POST_CONTENT": "Custom config content"
            }
            custom_file = os.path.join(tmpdir, "my_config.json")
            with open(custom_file, "w") as f:
                json.dump(config_data, f)
            
            os.environ['INPUT_FILE'] = custom_file
            
            from social_media_utils import get_required_env_var
            content = get_required_env_var("POST_CONTENT")
            
            self.assertEqual(content, "Custom config content")
    
    def test_env_var_overrides_json_config(self):
        """Test that environment variable takes precedence over JSON config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            os.chdir(tmpdir)
            
            # Create input.json
            config_data = {
                "POST_CONTENT": "Content from JSON"
            }
            with open("input.json", "w") as f:
                json.dump(config_data, f)
            
            # Set environment variable
            os.environ['POST_CONTENT'] = "Content from ENV"
            
            from social_media_utils import get_required_env_var
            content = get_required_env_var("POST_CONTENT")
            
            self.assertEqual(content, "Content from ENV")
    
    def test_load_facebook_config_from_json(self):
        """Test loading Facebook config from JSON file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            os.chdir(tmpdir)
            
            # Create input.json with Facebook credentials
            config_data = {
                "FB_PAGE_ID": "123456789",
                "FB_ACCESS_TOKEN": "test_fb_token",
                "POST_CONTENT": "Test Facebook post",
                "POST_LINK": "https://example.com",
                "POST_PRIVACY": "public"
            }
            with open("input.json", "w") as f:
                json.dump(config_data, f)
            
            from social_media_utils import get_required_env_var, get_optional_env_var
            
            page_id = get_required_env_var("FB_PAGE_ID")
            access_token = get_required_env_var("FB_ACCESS_TOKEN")
            content = get_required_env_var("POST_CONTENT")
            link = get_optional_env_var("POST_LINK", "")
            privacy = get_optional_env_var("POST_PRIVACY", "public")
            
            self.assertEqual(page_id, "123456789")
            self.assertEqual(access_token, "test_fb_token")
            self.assertEqual(content, "Test Facebook post")
            self.assertEqual(link, "https://example.com")
            self.assertEqual(privacy, "public")
    
    def test_load_youtube_config_from_json(self):
        """Test loading YouTube config from JSON file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            os.chdir(tmpdir)
            
            # Create input.json with YouTube credentials
            config_data = {
                "YOUTUBE_OAUTH_CLIENT_ID": "test_client_id",
                "YOUTUBE_OAUTH_CLIENT_SECRET": "test_client_secret",
                "YOUTUBE_OAUTH_REFRESH_TOKEN": "test_refresh_token",
                "VIDEO_TITLE": "Test Video",
                "VIDEO_DESCRIPTION": "Test Description",
                "VIDEO_FILE": "/path/to/video.mp4",
                "VIDEO_PRIVACY_STATUS": "private"
            }
            with open("input.json", "w") as f:
                json.dump(config_data, f)
            
            from social_media_utils import get_optional_env_var
            
            client_id = get_optional_env_var("YOUTUBE_OAUTH_CLIENT_ID", "")
            client_secret = get_optional_env_var("YOUTUBE_OAUTH_CLIENT_SECRET", "")
            refresh_token = get_optional_env_var("YOUTUBE_OAUTH_REFRESH_TOKEN", "")
            title = get_optional_env_var("VIDEO_TITLE", "")
            description = get_optional_env_var("VIDEO_DESCRIPTION", "")
            video_file = get_optional_env_var("VIDEO_FILE", "")
            privacy = get_optional_env_var("VIDEO_PRIVACY_STATUS", "public")
            
            self.assertEqual(client_id, "test_client_id")
            self.assertEqual(client_secret, "test_client_secret")
            self.assertEqual(refresh_token, "test_refresh_token")
            self.assertEqual(title, "Test Video")
            self.assertEqual(description, "Test Description")
            self.assertEqual(video_file, "/path/to/video.mp4")
            self.assertEqual(privacy, "private")
    
    def test_mixed_env_and_json_config(self):
        """Test loading some params from env and others from JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            os.chdir(tmpdir)
            
            # Create input.json with some credentials
            config_data = {
                "X_API_SECRET": "json_api_secret",
                "X_ACCESS_TOKEN_SECRET": "json_access_token_secret"
            }
            with open("input.json", "w") as f:
                json.dump(config_data, f)
            
            # Set some credentials in environment
            os.environ['X_API_KEY'] = "env_api_key"
            os.environ['X_ACCESS_TOKEN'] = "env_access_token"
            
            from social_media_utils import get_required_env_var
            
            api_key = get_required_env_var("X_API_KEY")
            api_secret = get_required_env_var("X_API_SECRET")
            access_token = get_required_env_var("X_ACCESS_TOKEN")
            access_token_secret = get_required_env_var("X_ACCESS_TOKEN_SECRET")
            
            # From env
            self.assertEqual(api_key, "env_api_key")
            self.assertEqual(access_token, "env_access_token")
            # From JSON
            self.assertEqual(api_secret, "json_api_secret")
            self.assertEqual(access_token_secret, "json_access_token_secret")


if __name__ == '__main__':
    unittest.main()
