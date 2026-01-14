#!/usr/bin/env python3
"""
Unit tests for update_youtube.py
"""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock, mock_open, call
from pathlib import Path
import json

# Add the current directory and common module to path
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent / 'common'))

# Import the module to test
from update_youtube import YouTubeUpdateAPI, update_youtube


class TestYouTubeUpdateAPI(unittest.TestCase):
    """Test cases for YouTubeUpdateAPI class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_creds = {
            "type": "service_account",
            "project_id": "test-project",
            "private_key_id": "test-key-id",
            "private_key": "-----BEGIN PRIVATE KEY-----\ntest\n-----END PRIVATE KEY-----\n",
            "client_email": "test@test-project.iam.gserviceaccount.com",
            "client_id": "123456789",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token"
        }
        
        self.mock_video_response = {
            'id': 'test_video_id',
            'snippet': {
                'title': 'Original Title',
                'description': 'Original Description',
                'tags': ['original', 'tags'],
                'categoryId': '22'
            },
            'status': {
                'privacyStatus': 'public',
                'embeddable': True,
                'license': 'youtube',
                'publicStatsViewable': True,
                'selfDeclaredMadeForKids': False
            }
        }
    
    @patch('update_youtube.build')
    @patch('update_youtube.service_account.Credentials.from_service_account_info')
    def test_init_with_service_account_json(self, mock_creds, mock_build):
        """Test YouTubeUpdateAPI initialization with service account JSON."""
        mock_credentials = MagicMock()
        mock_creds.return_value = mock_credentials
        mock_youtube = MagicMock()
        mock_build.return_value = mock_youtube
        
        api = YouTubeUpdateAPI(credentials_json=json.dumps(self.test_creds))
        
        # Verify credentials were created
        mock_creds.assert_called_once()
        
        # Verify YouTube API was built
        mock_build.assert_called_once_with('youtube', 'v3', credentials=mock_credentials)
        self.assertEqual(api.youtube, mock_youtube)
    
    @patch('update_youtube.build')
    @patch('update_youtube.Credentials')
    @patch('update_youtube.Request')
    def test_init_with_oauth_refresh_token(self, mock_request, mock_credentials_class, mock_build):
        """Test YouTubeUpdateAPI initialization with OAuth refresh token."""
        # Mock the Credentials object
        mock_credentials = MagicMock()
        mock_credentials_class.return_value = mock_credentials
        
        # Mock the build function
        mock_youtube = MagicMock()
        mock_build.return_value = mock_youtube
        
        # Create API with OAuth refresh token
        api = YouTubeUpdateAPI(
            oauth_client_id="test_client_id",
            oauth_client_secret="test_client_secret",
            oauth_refresh_token="test_refresh_token"
        )
        
        # Verify Credentials was created with correct parameters
        mock_credentials_class.assert_called_once_with(
            token=None,
            refresh_token="test_refresh_token",
            token_uri='https://oauth2.googleapis.com/token',
            client_id="test_client_id",
            client_secret="test_client_secret",
            scopes=['https://www.googleapis.com/auth/youtube']
        )
        
        # Verify refresh was called
        mock_credentials.refresh.assert_called_once()
        
        # Verify YouTube API was built
        mock_build.assert_called_once_with('youtube', 'v3', credentials=mock_credentials)
        self.assertEqual(api.youtube, mock_youtube)
    
    @patch('update_youtube.build')
    def test_init_with_api_key(self, mock_build):
        """Test YouTubeUpdateAPI initialization with API key."""
        mock_youtube = MagicMock()
        mock_build.return_value = mock_youtube
        
        api = YouTubeUpdateAPI(api_key="test_api_key")
        
        # Verify YouTube API was built with API key
        mock_build.assert_called_once_with('youtube', 'v3', developerKey="test_api_key")
        self.assertEqual(api.youtube, mock_youtube)
    
    def test_init_with_no_credentials(self):
        """Test YouTubeUpdateAPI initialization fails without credentials."""
        with self.assertRaises(ValueError):
            YouTubeUpdateAPI()
    
    @patch('update_youtube.build')
    @patch('update_youtube.service_account.Credentials.from_service_account_info')
    def test_get_video(self, mock_creds, mock_build):
        """Test get_video functionality."""
        # Mock credentials and build
        mock_credentials = MagicMock()
        mock_creds.return_value = mock_credentials
        
        # Mock YouTube API
        mock_youtube = MagicMock()
        mock_build.return_value = mock_youtube
        
        # Mock the get video response
        mock_youtube.videos().list().execute.return_value = {
            'items': [self.mock_video_response]
        }
        
        # Create API and get video
        api = YouTubeUpdateAPI(credentials_json=json.dumps(self.test_creds))
        result = api.get_video('test_video_id')
        
        # Verify result
        self.assertEqual(result['id'], 'test_video_id')
        self.assertEqual(result['snippet']['title'], 'Original Title')
        
        # Verify API was called correctly - check that list was called with the right params
        call_args_list = mock_youtube.videos().list.call_args_list
        # Find the call with the right parameters
        found = any(
            call[1].get('part') == 'snippet,status' and call[1].get('id') == 'test_video_id'
            for call in call_args_list
        )
        self.assertTrue(found, "videos().list should be called with correct parameters")
    
    @patch('update_youtube.build')
    @patch('update_youtube.service_account.Credentials.from_service_account_info')
    def test_get_video_not_found(self, mock_creds, mock_build):
        """Test get_video with non-existent video."""
        # Mock credentials and build
        mock_credentials = MagicMock()
        mock_creds.return_value = mock_credentials
        
        # Mock YouTube API
        mock_youtube = MagicMock()
        mock_build.return_value = mock_youtube
        
        # Mock empty response (video not found)
        mock_youtube.videos().list().execute.return_value = {'items': []}
        
        # Create API and try to get video
        api = YouTubeUpdateAPI(credentials_json=json.dumps(self.test_creds))
        
        with self.assertRaises(ValueError) as context:
            api.get_video('nonexistent_video_id')
        
        self.assertIn("Video not found", str(context.exception))
    
    @patch('update_youtube.build')
    @patch('update_youtube.service_account.Credentials.from_service_account_info')
    def test_update_video_title(self, mock_creds, mock_build):
        """Test updating video title."""
        # Mock credentials and build
        mock_credentials = MagicMock()
        mock_creds.return_value = mock_credentials
        
        # Mock YouTube API
        mock_youtube = MagicMock()
        mock_build.return_value = mock_youtube
        
        # Mock the get video response
        mock_youtube.videos().list().execute.return_value = {
            'items': [self.mock_video_response.copy()]
        }
        
        # Mock the update response
        updated_video = self.mock_video_response.copy()
        updated_video['snippet'] = updated_video['snippet'].copy()
        updated_video['snippet']['title'] = 'New Title'
        mock_youtube.videos().update().execute.return_value = updated_video
        
        # Create API and update video
        api = YouTubeUpdateAPI(credentials_json=json.dumps(self.test_creds))
        result = api.update_video('test_video_id', title='New Title')
        
        # Verify result
        self.assertEqual(result['id'], 'test_video_id')
        self.assertEqual(result['title'], 'New Title')
        
        # Verify update was called - check call_args_list for the right parameters
        call_args_list = mock_youtube.videos().update.call_args_list
        found = False
        for call in call_args_list:
            if 'body' in call[1]:
                body = call[1]['body']
                if body.get('snippet', {}).get('title') == 'New Title' and body.get('id') == 'test_video_id':
                    found = True
                    break
        self.assertTrue(found, "videos().update should be called with correct body")
    
    @patch('update_youtube.build')
    @patch('update_youtube.service_account.Credentials.from_service_account_info')
    def test_update_video_description(self, mock_creds, mock_build):
        """Test updating video description."""
        # Mock credentials and build
        mock_credentials = MagicMock()
        mock_creds.return_value = mock_credentials
        
        # Mock YouTube API
        mock_youtube = MagicMock()
        mock_build.return_value = mock_youtube
        
        # Mock the get video response
        mock_youtube.videos().list().execute.return_value = {
            'items': [self.mock_video_response.copy()]
        }
        
        # Mock the update response
        updated_video = self.mock_video_response.copy()
        updated_video['snippet'] = updated_video['snippet'].copy()
        updated_video['snippet']['description'] = 'New Description'
        mock_youtube.videos().update().execute.return_value = updated_video
        
        # Create API and update video
        api = YouTubeUpdateAPI(credentials_json=json.dumps(self.test_creds))
        result = api.update_video('test_video_id', description='New Description')
        
        # Verify result
        self.assertEqual(result['id'], 'test_video_id')
        
        # Verify update was called with correct description
        call_args = mock_youtube.videos().update.call_args
        body = call_args[1]['body']
        self.assertEqual(body['snippet']['description'], 'New Description')
    
    @patch('update_youtube.build')
    @patch('update_youtube.service_account.Credentials.from_service_account_info')
    def test_update_video_tags(self, mock_creds, mock_build):
        """Test updating video tags."""
        # Mock credentials and build
        mock_credentials = MagicMock()
        mock_creds.return_value = mock_credentials
        
        # Mock YouTube API
        mock_youtube = MagicMock()
        mock_build.return_value = mock_youtube
        
        # Mock the get video response
        mock_youtube.videos().list().execute.return_value = {
            'items': [self.mock_video_response.copy()]
        }
        
        # Mock the update response
        updated_video = self.mock_video_response.copy()
        updated_video['snippet'] = updated_video['snippet'].copy()
        updated_video['snippet']['tags'] = ['new', 'tags', 'here']
        mock_youtube.videos().update().execute.return_value = updated_video
        
        # Create API and update video
        api = YouTubeUpdateAPI(credentials_json=json.dumps(self.test_creds))
        new_tags = ['new', 'tags', 'here']
        result = api.update_video('test_video_id', tags=new_tags)
        
        # Verify update was called with correct tags
        call_args = mock_youtube.videos().update.call_args
        body = call_args[1]['body']
        self.assertEqual(body['snippet']['tags'], new_tags)
    
    @patch('update_youtube.build')
    @patch('update_youtube.service_account.Credentials.from_service_account_info')
    def test_update_video_multiple_fields(self, mock_creds, mock_build):
        """Test updating multiple video fields at once."""
        # Mock credentials and build
        mock_credentials = MagicMock()
        mock_creds.return_value = mock_credentials
        
        # Mock YouTube API
        mock_youtube = MagicMock()
        mock_build.return_value = mock_youtube
        
        # Mock the get video response
        mock_youtube.videos().list().execute.return_value = {
            'items': [self.mock_video_response.copy()]
        }
        
        # Mock the update response
        updated_video = self.mock_video_response.copy()
        updated_video['snippet'] = updated_video['snippet'].copy()
        updated_video['status'] = updated_video['status'].copy()
        updated_video['snippet']['title'] = 'Updated Title'
        updated_video['snippet']['description'] = 'Updated Description'
        updated_video['snippet']['tags'] = ['updated', 'tags']
        updated_video['status']['privacyStatus'] = 'private'
        mock_youtube.videos().update().execute.return_value = updated_video
        
        # Create API and update video
        api = YouTubeUpdateAPI(credentials_json=json.dumps(self.test_creds))
        result = api.update_video(
            'test_video_id',
            title='Updated Title',
            description='Updated Description',
            tags=['updated', 'tags'],
            privacy_status='private'
        )
        
        # Verify update was called with all fields
        call_args = mock_youtube.videos().update.call_args
        body = call_args[1]['body']
        self.assertEqual(body['snippet']['title'], 'Updated Title')
        self.assertEqual(body['snippet']['description'], 'Updated Description')
        self.assertEqual(body['snippet']['tags'], ['updated', 'tags'])
        self.assertEqual(body['status']['privacyStatus'], 'private')
    
    @patch('update_youtube.build')
    @patch('update_youtube.service_account.Credentials.from_service_account_info')
    def test_update_video_privacy_status(self, mock_creds, mock_build):
        """Test updating video privacy status."""
        # Mock credentials and build
        mock_credentials = MagicMock()
        mock_creds.return_value = mock_credentials
        
        # Mock YouTube API
        mock_youtube = MagicMock()
        mock_build.return_value = mock_youtube
        
        # Mock the get video response
        mock_youtube.videos().list().execute.return_value = {
            'items': [self.mock_video_response.copy()]
        }
        
        # Mock the update response
        updated_video = self.mock_video_response.copy()
        updated_video['status'] = updated_video['status'].copy()
        updated_video['status']['privacyStatus'] = 'unlisted'
        mock_youtube.videos().update().execute.return_value = updated_video
        
        # Create API and update video
        api = YouTubeUpdateAPI(credentials_json=json.dumps(self.test_creds))
        result = api.update_video('test_video_id', privacy_status='unlisted')
        
        # Verify update was called with correct privacy status
        call_args = mock_youtube.videos().update.call_args
        body = call_args[1]['body']
        self.assertEqual(body['status']['privacyStatus'], 'unlisted')
    
    @patch('update_youtube.build')
    @patch('update_youtube.service_account.Credentials.from_service_account_info')
    def test_update_video_synthetic_media_flag(self, mock_creds, mock_build):
        """Test updating video with containsSyntheticMedia flag."""
        # Mock credentials and build
        mock_credentials = MagicMock()
        mock_creds.return_value = mock_credentials
        
        # Mock YouTube API
        mock_youtube = MagicMock()
        mock_build.return_value = mock_youtube
        
        # Mock the get video response
        mock_youtube.videos().list().execute.return_value = {
            'items': [self.mock_video_response.copy()]
        }
        
        # Mock the update response
        updated_video = self.mock_video_response.copy()
        updated_video['status'] = updated_video['status'].copy()
        updated_video['status']['containsSyntheticMedia'] = True
        mock_youtube.videos().update().execute.return_value = updated_video
        
        # Create API and update video
        api = YouTubeUpdateAPI(credentials_json=json.dumps(self.test_creds))
        result = api.update_video('test_video_id', contains_synthetic_media=True)
        
        # Verify update was called with containsSyntheticMedia
        call_args = mock_youtube.videos().update.call_args
        body = call_args[1]['body']
        self.assertEqual(body['status']['containsSyntheticMedia'], True)


class TestUpdateYouTube(unittest.TestCase):
    """Test cases for update_youtube function."""
    
    @patch('update_youtube.YouTubeUpdateAPI')
    @patch('update_youtube.process_templated_contents')
    def test_update_youtube_basic(self, mock_template, mock_api_class):
        """Test basic video update through update_youtube."""
        # Setup environment
        os.environ['YOUTUBE_API_KEY'] = json.dumps({"test": "credentials"})
        os.environ['VIDEO_ID'] = 'test_video_id'
        os.environ['VIDEO_TITLE'] = 'Updated Title'
        os.environ['LOG_LEVEL'] = 'ERROR'  # Suppress logs during test
        
        # Mock templating
        mock_template.return_value = ('Updated Title', '')
        
        # Mock API
        mock_api = MagicMock()
        mock_api_class.return_value = mock_api
        mock_api.update_video.return_value = {
            'id': 'test_video_id',
            'url': 'https://www.youtube.com/watch?v=test_video_id',
            'title': 'Updated Title',
            'privacy_status': 'public'
        }
        
        # Mock GitHub output
        with patch.dict(os.environ, {'GITHUB_OUTPUT': '/tmp/output'}):
            with patch('builtins.open', mock_open()):
                # Call function
                update_youtube()
        
        # Verify API was called
        mock_api.update_video.assert_called_once()
        call_args = mock_api.update_video.call_args
        self.assertEqual(call_args[1]['video_id'], 'test_video_id')
        self.assertEqual(call_args[1]['title'], 'Updated Title')
        
        # Clean up
        for key in ['YOUTUBE_API_KEY', 'VIDEO_ID', 'VIDEO_TITLE']:
            if key in os.environ:
                del os.environ[key]
    
    @patch('update_youtube.sys.exit')
    def test_update_youtube_no_video_id(self, mock_exit):
        """Test that function exits when video ID is not provided."""
        os.environ['YOUTUBE_API_KEY'] = 'test_key'
        os.environ['LOG_LEVEL'] = 'ERROR'
        
        # Remove VIDEO_ID if it exists
        if 'VIDEO_ID' in os.environ:
            del os.environ['VIDEO_ID']
        
        # Call function - should exit with error
        update_youtube()
        
        # Verify exit was called
        mock_exit.assert_called()
        
        # Clean up
        if 'YOUTUBE_API_KEY' in os.environ:
            del os.environ['YOUTUBE_API_KEY']
    
    @patch('update_youtube.sys.exit')
    @patch('update_youtube.process_templated_contents')
    def test_update_youtube_no_fields(self, mock_template, mock_exit):
        """Test that function exits when no update fields are provided."""
        os.environ['YOUTUBE_API_KEY'] = 'test_key'
        os.environ['VIDEO_ID'] = 'test_video_id'
        os.environ['LOG_LEVEL'] = 'ERROR'
        
        # Mock templating returns empty values
        mock_template.return_value = ('', '')
        
        # Call function - should exit with error
        update_youtube()
        
        # Verify exit was called
        mock_exit.assert_called()
        
        # Clean up
        for key in ['YOUTUBE_API_KEY', 'VIDEO_ID']:
            if key in os.environ:
                del os.environ[key]
    
    @patch('update_youtube.YouTubeUpdateAPI')
    @patch('update_youtube.process_templated_contents')
    def test_update_youtube_multiple_fields(self, mock_template, mock_api_class):
        """Test updating multiple fields."""
        # Setup environment
        os.environ['YOUTUBE_API_KEY'] = json.dumps({"test": "credentials"})
        os.environ['VIDEO_ID'] = 'test_video_id'
        os.environ['VIDEO_TITLE'] = 'Updated Title'
        os.environ['VIDEO_DESCRIPTION'] = 'Updated Description'
        os.environ['VIDEO_TAGS'] = 'tag1, tag2, tag3'
        os.environ['VIDEO_PRIVACY_STATUS'] = 'private'
        os.environ['LOG_LEVEL'] = 'ERROR'
        
        # Mock templating
        mock_template.return_value = ('Updated Title', 'Updated Description')
        
        # Mock API
        mock_api = MagicMock()
        mock_api_class.return_value = mock_api
        mock_api.update_video.return_value = {
            'id': 'test_video_id',
            'url': 'https://www.youtube.com/watch?v=test_video_id',
            'title': 'Updated Title',
            'privacy_status': 'private'
        }
        
        # Mock GitHub output
        with patch.dict(os.environ, {'GITHUB_OUTPUT': '/tmp/output'}):
            with patch('builtins.open', mock_open()):
                # Call function
                update_youtube()
        
        # Verify API was called with all fields
        call_args = mock_api.update_video.call_args
        self.assertEqual(call_args[1]['video_id'], 'test_video_id')
        self.assertEqual(call_args[1]['title'], 'Updated Title')
        self.assertEqual(call_args[1]['description'], 'Updated Description')
        self.assertEqual(call_args[1]['tags'], ['tag1', 'tag2', 'tag3'])
        self.assertEqual(call_args[1]['privacy_status'], 'private')
        
        # Clean up
        for key in ['YOUTUBE_API_KEY', 'VIDEO_ID', 'VIDEO_TITLE', 'VIDEO_DESCRIPTION', 
                   'VIDEO_TAGS', 'VIDEO_PRIVACY_STATUS']:
            if key in os.environ:
                del os.environ[key]


if __name__ == '__main__':
    unittest.main()
