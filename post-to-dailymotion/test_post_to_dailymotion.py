#!/usr/bin/env python3
"""
Unit tests for post_to_dailymotion.py
"""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path
import json

# Add the current directory and common module to path
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent / 'common'))

# Import the module to test
from post_to_dailymotion import DailymotionAPI, post_to_dailymotion

class TestDailymotionAPI(unittest.TestCase):
    """Test cases for DailymotionAPI class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.client_id = "test_client_id"
        self.client_secret = "test_client_secret"
        self.api = DailymotionAPI(self.client_id, self.client_secret)

    @patch('requests.post')
    def test_authenticate(self, mock_post):
        """Test Dailymotion authentication."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"access_token": "test_access_token"}
        mock_response.raise_for_status.return_value = None
        mock_response.status_code = 200
        mock_response.text = '{"access_token": "test_access_token"}'
        mock_post.return_value = mock_response
        
        self.api.authenticate()
        
        self.assertEqual(self.api.access_token, "test_access_token")
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertEqual(args[0], "https://partner.api.dailymotion.com/oauth/v1/token")
        self.assertEqual(kwargs['data']['client_id'], self.client_id)
        self.assertEqual(kwargs['data']['grant_type'], "client_credentials")

    @patch('requests.get')
    def test_get_upload_url(self, mock_get):
        """Test getting upload URL."""
        self.api.access_token = "test_token"
        mock_response = MagicMock()
        mock_response.json.return_value = {"upload_url": "https://upload.dailymotion.com/test"}
        mock_response.raise_for_status.return_value = None
        mock_response.status_code = 200
        mock_response.text = '{"upload_url": "https://upload.dailymotion.com/test"}'
        mock_get.return_value = mock_response
        
        upload_url = self.api.get_upload_url()
        
        self.assertEqual(upload_url, "https://upload.dailymotion.com/test")
        mock_get.assert_called_once()
        headers = mock_get.call_args[1]['headers']
        self.assertEqual(headers['Authorization'], "Bearer test_token")

    @patch('requests.post')
    def test_upload_file(self, mock_post):
        """Test file upload."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"url": "https://file.dailymotion.com/test.mp4"}
        mock_response.raise_for_status.return_value = None
        mock_response.status_code = 200
        mock_response.text = '{"url": "https://file.dailymotion.com/test.mp4"}'
        mock_post.return_value = mock_response
        
        # Mock open
        with patch('builtins.open', mock_open(read_data=b"test data")):
            file_url = self.api.upload_file("https://upload.url", "test.mp4")
            
        self.assertEqual(file_url, "https://file.dailymotion.com/test.mp4")
        mock_post.assert_called_once()

    @patch('requests.post')
    def test_create_video_me(self, mock_post):
        """Test video creation with 'me' channel."""
        self.api.access_token = "test_token"
        self.api.channel_id = "me"
        mock_response = MagicMock()
        mock_response.json.return_value = {"id": "x12345"}
        mock_response.raise_for_status.return_value = None
        mock_response.status_code = 200
        mock_response.text = '{"id": "x12345"}'
        mock_post.return_value = mock_response
        
        metadata = {
            "title": "Test Video",
            "published": True
        }
        
        video_id = self.api.create_video("https://file.url", metadata)
        
        self.assertEqual(video_id, "x12345")
        args, kwargs = mock_post.call_args
        self.assertEqual(args[0], "https://partner.api.dailymotion.com/rest/user/me/videos")

    @patch('requests.post')
    def test_create_video_specific_channel(self, mock_post):
        """Test video creation with specific channel ID."""
        self.api.access_token = "test_token"
        self.api.channel_id = "test_channel"
        mock_response = MagicMock()
        mock_response.json.return_value = {"id": "x12345"}
        mock_response.raise_for_status.return_value = None
        mock_response.status_code = 200
        mock_response.text = '{"id": "x12345"}'
        mock_post.return_value = mock_response
        
        metadata = {
            "title": "Test Video",
            "published": True
        }
        
        video_id = self.api.create_video("https://file.url", metadata)
        
        self.assertEqual(video_id, "x12345")
        args, kwargs = mock_post.call_args
        self.assertEqual(args[0], "https://partner.api.dailymotion.com/rest/user/test_channel/videos")

class TestPostToDailymotion(unittest.TestCase):
    """Test cases for post_to_dailymotion function."""
    
    @patch('post_to_dailymotion.get_required_env_var')
    @patch('post_to_dailymotion.get_optional_env_var')
    @patch('post_to_dailymotion.download_file_if_url')
    @patch('post_to_dailymotion.dry_run_guard')
    @patch('post_to_dailymotion.DailymotionAPI')
    @patch('os.path.exists')
    @patch('os.path.getsize')
    def test_post_to_dailymotion_success(self, mock_getsize, mock_exists, mock_api_class, 
                                        mock_dry_run, mock_download, mock_get_optional, mock_get_required):
        """Test successful Dailymotion posting."""
        # Setup mocks
        mock_get_required.side_effect = lambda var: {
            "DAILYMOTION_CLIENT_ID": "id",
            "DAILYMOTION_CLIENT_SECRET": "secret",
            "VIDEO_FILE": "video.mp4",
            "DAILYMOTION_CHANNEL": "news"
        }[var]
        
        mock_get_optional.side_effect = lambda var, default="": {
            "LOG_LEVEL": "INFO",
            "VIDEO_TITLE": "Test Title",
            "VIDEO_DESCRIPTION": "Test Desc",
            "VIDEO_MADE_FOR_KIDS": "false",
            "VIDEO_TAGS": "tag1,tag2",
            "VIDEO_PUBLISH_AT": "",
            "DRY_RUN": "false"
        }.get(var, default)
        
        mock_download.return_value = "video.mp4"
        mock_exists.return_value = True
        mock_getsize.return_value = 1000
        
        mock_api = MagicMock()
        mock_api_class.return_value = mock_api
        mock_api.get_upload_url.return_value = "https://upload.url"
        mock_api.upload_file.return_value = "https://file.url"
        mock_api.create_video.return_value = "x12345"
        
        # Call the function
        with patch('social_media_utils.load_json_config', return_value={}):
            post_to_dailymotion()
        
        # Verify calls
        mock_api.get_upload_url.assert_called_once()
        mock_api.upload_file.assert_called_once_with("https://upload.url", "video.mp4")
        mock_api.create_video.assert_called_once()
        
        metadata = mock_api.create_video.call_args[0][1]
        self.assertEqual(metadata['title'], "Test Title")
        self.assertEqual(metadata['channel'], "news")
        self.assertEqual(metadata['tags'], "tag1,tag2")

if __name__ == '__main__':
    unittest.main()
