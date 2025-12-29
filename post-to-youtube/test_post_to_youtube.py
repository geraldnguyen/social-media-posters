#!/usr/bin/env python3
"""
Unit tests for post_to_youtube.py
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
from post_to_youtube import YouTubeAPI, post_to_youtube


class TestYouTubeAPI(unittest.TestCase):
    """Test cases for YouTubeAPI class."""
    
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
    
    @patch('post_to_youtube.build')
    @patch('post_to_youtube.service_account.Credentials.from_service_account_info')
    def test_init_with_service_account_json(self, mock_creds, mock_build):
        """Test YouTubeAPI initialization with service account JSON."""
        mock_credentials = MagicMock()
        mock_creds.return_value = mock_credentials
        mock_youtube = MagicMock()
        mock_build.return_value = mock_youtube
        
        api = YouTubeAPI(credentials_json=json.dumps(self.test_creds))
        
        # Verify credentials were created
        mock_creds.assert_called_once()
        
        # Verify YouTube API was built
        mock_build.assert_called_once_with('youtube', 'v3', credentials=mock_credentials)
        self.assertEqual(api.youtube, mock_youtube)
    
    @patch('post_to_youtube.build')
    @patch('post_to_youtube.Credentials')
    @patch('post_to_youtube.Request')
    def test_init_with_oauth_refresh_token(self, mock_request, mock_credentials_class, mock_build):
        """Test YouTubeAPI initialization with OAuth refresh token."""
        # Mock the Credentials object
        mock_credentials = MagicMock()
        mock_credentials_class.return_value = mock_credentials
        
        # Mock the build function
        mock_youtube = MagicMock()
        mock_build.return_value = mock_youtube
        
        # Create API with OAuth refresh token
        api = YouTubeAPI(
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
            scopes=['https://www.googleapis.com/auth/youtube.upload',
                    'https://www.googleapis.com/auth/youtube.force-ssl']
        )
        
        # Verify refresh was called
        mock_credentials.refresh.assert_called_once()
        
        # Verify YouTube API was built
        mock_build.assert_called_once_with('youtube', 'v3', credentials=mock_credentials)
        self.assertEqual(api.youtube, mock_youtube)
    
    @patch('post_to_youtube.build')
    def test_init_with_api_key(self, mock_build):
        """Test YouTubeAPI initialization with API key."""
        mock_youtube = MagicMock()
        mock_build.return_value = mock_youtube
        
        api = YouTubeAPI(api_key="test_api_key")
        
        # Verify YouTube API was built with API key
        mock_build.assert_called_once_with('youtube', 'v3', developerKey="test_api_key")
        self.assertEqual(api.youtube, mock_youtube)
    
    def test_init_with_no_credentials(self):
        """Test YouTubeAPI initialization fails without credentials."""
        with self.assertRaises(ValueError):
            YouTubeAPI()
    
    @patch('post_to_youtube.MediaFileUpload')
    @patch('post_to_youtube.build')
    @patch('post_to_youtube.service_account.Credentials.from_service_account_info')
    def test_upload_video_basic(self, mock_creds, mock_build, mock_media_upload):
        """Test basic video upload functionality."""
        # Mock credentials and build
        mock_credentials = MagicMock()
        mock_creds.return_value = mock_credentials
        
        # Mock YouTube API
        mock_youtube = MagicMock()
        mock_build.return_value = mock_youtube
        
        # Mock the upload response
        mock_request = MagicMock()
        mock_request.next_chunk.return_value = (None, {'id': 'test_video_id'})
        
        mock_youtube.videos().insert.return_value = mock_request
        
        # Mock MediaFileUpload
        mock_media = MagicMock()
        mock_media_upload.return_value = mock_media
        
        # Create API and upload
        api = YouTubeAPI(credentials_json=json.dumps(self.test_creds))
        
        result = api.upload_video(
            video_file='/tmp/test_video.mp4',
            title='Test Video',
            description='Test Description'
        )
        
        # Verify result
        self.assertEqual(result['id'], 'test_video_id')
        self.assertEqual(result['url'], 'https://www.youtube.com/watch?v=test_video_id')
        self.assertEqual(result['title'], 'Test Video')
        
        # Verify API was called correctly
        mock_youtube.videos().insert.assert_called_once()
    
    @patch('post_to_youtube.MediaFileUpload')
    @patch('post_to_youtube.build')
    @patch('post_to_youtube.service_account.Credentials.from_service_account_info')
    def test_upload_video_with_scheduling(self, mock_creds, mock_build, mock_media_upload):
        """Test video upload with scheduled publishing."""
        # Mock credentials and build
        mock_credentials = MagicMock()
        mock_creds.return_value = mock_credentials
        
        # Mock YouTube API
        mock_youtube = MagicMock()
        mock_build.return_value = mock_youtube
        
        # Mock the upload response
        mock_request = MagicMock()
        mock_request.next_chunk.return_value = (None, {'id': 'scheduled_video_id'})
        
        mock_youtube.videos().insert.return_value = mock_request
        
        # Mock MediaFileUpload
        mock_media = MagicMock()
        mock_media_upload.return_value = mock_media
        
        # Create API and upload with scheduling
        api = YouTubeAPI(credentials_json=json.dumps(self.test_creds))
        
        result = api.upload_video(
            video_file='/tmp/test_video.mp4',
            title='Scheduled Video',
            description='Will be published later',
            privacy_status='private',
            publish_at='2025-12-31T12:00:00Z'
        )
        
        # Verify result
        self.assertEqual(result['id'], 'scheduled_video_id')
        
        # Verify the insert call included publishAt
        call_args = mock_youtube.videos().insert.call_args
        body = call_args[1]['body']
        self.assertEqual(body['status']['publishAt'], '2025-12-31T12:00:00Z')
        self.assertEqual(body['status']['privacyStatus'], 'private')
    
    @patch('post_to_youtube.MediaFileUpload')
    @patch('post_to_youtube.build')
    @patch('post_to_youtube.service_account.Credentials.from_service_account_info')
    def test_upload_video_with_tags(self, mock_creds, mock_build, mock_media_upload):
        """Test video upload with tags."""
        # Mock credentials and build
        mock_credentials = MagicMock()
        mock_creds.return_value = mock_credentials
        
        # Mock YouTube API
        mock_youtube = MagicMock()
        mock_build.return_value = mock_youtube
        
        # Mock the upload response
        mock_request = MagicMock()
        mock_request.next_chunk.return_value = (None, {'id': 'tagged_video_id'})
        
        mock_youtube.videos().insert.return_value = mock_request
        
        # Mock MediaFileUpload
        mock_media = MagicMock()
        mock_media_upload.return_value = mock_media
        
        # Create API and upload with tags
        api = YouTubeAPI(credentials_json=json.dumps(self.test_creds))
        
        tags = ['test', 'tutorial', 'demo']
        result = api.upload_video(
            video_file='/tmp/test_video.mp4',
            title='Tagged Video',
            description='Video with tags',
            tags=tags
        )
        
        # Verify tags were included
        call_args = mock_youtube.videos().insert.call_args
        body = call_args[1]['body']
        self.assertEqual(body['snippet']['tags'], tags)
    
    @patch('post_to_youtube.MediaFileUpload')
    @patch('post_to_youtube.build')
    @patch('post_to_youtube.service_account.Credentials.from_service_account_info')
    def test_upload_thumbnail(self, mock_creds, mock_build, mock_media_upload):
        """Test thumbnail upload functionality."""
        # Mock credentials and build
        mock_credentials = MagicMock()
        mock_creds.return_value = mock_credentials
        
        # Mock YouTube API
        mock_youtube = MagicMock()
        mock_build.return_value = mock_youtube
        
        # Mock the thumbnail upload response
        mock_youtube.thumbnails().set().execute.return_value = {'items': [{'default': {}}]}
        
        # Mock MediaFileUpload
        mock_media = MagicMock()
        mock_media_upload.return_value = mock_media
        
        # Create API and upload thumbnail
        api = YouTubeAPI(credentials_json=json.dumps(self.test_creds))
        
        # Should not raise an exception
        api.upload_thumbnail('test_video_id', '/tmp/thumbnail.jpg')
        
        # Verify API was called with correct parameters
        self.assertTrue(mock_youtube.thumbnails().set.called)
    
    @patch('post_to_youtube.build')
    @patch('post_to_youtube.service_account.Credentials.from_service_account_info')
    def test_add_video_to_playlist(self, mock_creds, mock_build):
        """Test adding video to playlist."""
        # Mock credentials and build
        mock_credentials = MagicMock()
        mock_creds.return_value = mock_credentials
        
        # Mock YouTube API
        mock_youtube = MagicMock()
        mock_build.return_value = mock_youtube
        
        # Mock the playlist add response
        mock_youtube.playlistItems().insert().execute.return_value = {'id': 'playlist_item_id'}
        
        # Create API and add to playlist
        api = YouTubeAPI(credentials_json=json.dumps(self.test_creds))
        
        # Should not raise an exception
        api.add_video_to_playlist('test_video_id', 'test_playlist_id')
        
        # Verify API was called with correct parameters
        self.assertTrue(mock_youtube.playlistItems().insert.called)
        # Get the call with keyword arguments
        calls = mock_youtube.playlistItems().insert.call_args_list
        # Find the call with body parameter
        body_call = [c for c in calls if 'body' in c[1]]
        self.assertTrue(len(body_call) > 0)
        body = body_call[0][1]['body']
        self.assertEqual(body['snippet']['playlistId'], 'test_playlist_id')
        self.assertEqual(body['snippet']['resourceId']['videoId'], 'test_video_id')


class TestPostToYouTube(unittest.TestCase):
    """Test cases for post_to_youtube function."""
    
    @patch('post_to_youtube.os.path.exists')
    @patch('post_to_youtube.os.path.getsize')
    @patch('post_to_youtube.YouTubeAPI')
    @patch('post_to_youtube.download_file_if_url')
    @patch('post_to_youtube.process_templated_contents')
    def test_post_to_youtube_basic_video(self, mock_template, mock_download, mock_api_class, mock_getsize, mock_exists):
        """Test basic video upload through post_to_youtube."""
        # Setup environment
        os.environ['YOUTUBE_API_KEY'] = json.dumps({"test": "credentials"})
        os.environ['VIDEO_FILE'] = '/tmp/test.mp4'
        os.environ['VIDEO_TITLE'] = 'Test Video'
        os.environ['VIDEO_DESCRIPTION'] = 'Test Description'
        os.environ['LOG_LEVEL'] = 'ERROR'  # Suppress logs during test
        
        # Mock templating
        mock_template.return_value = ('Test Video', 'Test Description', '')
        
        # Mock file operations
        mock_download.return_value = '/tmp/test.mp4'
        mock_exists.return_value = True
        mock_getsize.return_value = 1024000
        
        # Mock API
        mock_api = MagicMock()
        mock_api_class.return_value = mock_api
        mock_api.upload_video.return_value = {
            'id': 'test_video_id',
            'url': 'https://www.youtube.com/watch?v=test_video_id',
            'title': 'Test Video',
            'privacy_status': 'public'
        }
        
        # Mock GitHub output
        with patch.dict(os.environ, {'GITHUB_OUTPUT': '/tmp/output'}):
            with patch('builtins.open', mock_open()):
                # Call function
                post_to_youtube()
        
        # Verify API was called
        mock_api.upload_video.assert_called_once()
        
        # Clean up
        for key in ['YOUTUBE_API_KEY', 'VIDEO_FILE', 'VIDEO_TITLE', 'VIDEO_DESCRIPTION']:
            if key in os.environ:
                del os.environ[key]
    
    @patch('post_to_youtube.sys.exit')
    def test_post_to_youtube_no_video_or_content(self, mock_exit):
        """Test that function exits when neither video nor content is provided."""
        os.environ['YOUTUBE_API_KEY'] = 'test_key'
        os.environ['LOG_LEVEL'] = 'ERROR'
        
        # Call function - should exit with error
        post_to_youtube()
        
        # Verify exit was called
        mock_exit.assert_called()
        
        # Clean up
        if 'YOUTUBE_API_KEY' in os.environ:
            del os.environ['YOUTUBE_API_KEY']
    
    @patch('post_to_youtube.sys.exit')
    @patch('post_to_youtube.process_templated_contents')
    def test_post_to_youtube_no_title(self, mock_template, mock_exit):
        """Test that function exits when video file is provided but title is missing."""
        os.environ['YOUTUBE_API_KEY'] = 'test_key'
        os.environ['VIDEO_FILE'] = '/tmp/test.mp4'
        os.environ['LOG_LEVEL'] = 'ERROR'
        
        # Mock templating returns empty title
        mock_template.return_value = ('', '', '')
        
        # Call function - should exit with error
        post_to_youtube()
        
        # Verify exit was called
        mock_exit.assert_called()
        
        # Clean up
        for key in ['YOUTUBE_API_KEY', 'VIDEO_FILE']:
            if key in os.environ:
                del os.environ[key]


if __name__ == '__main__':
    unittest.main()
