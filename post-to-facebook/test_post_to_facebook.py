#!/usr/bin/env python3
"""
Unit tests for post_to_facebook.py
"""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock, mock_open, call
from pathlib import Path
import tempfile

# Add the current directory and common module to path
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent / 'common'))

# Import the module to test
from post_to_facebook import (
    upload_video,
    _upload_video_simple,
    _upload_video_resumable,
    upload_photo,
    _graph_api_post
)


class TestVideoUpload(unittest.TestCase):
    """Test cases for video upload functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.page_id = "test_page_id"
        self.access_token = "test_access_token"
        self.description = "Test video description"
        self.published = True
        
    @patch('post_to_facebook.os.path.getsize')
    @patch('post_to_facebook._upload_video_simple')
    @patch('post_to_facebook.get_optional_env_var')
    def test_upload_video_small_file_uses_simple_upload(self, mock_get_env, mock_simple, mock_getsize):
        """Test that small videos use simple upload method."""
        # Setup
        mock_getsize.return_value = 4 * 1024 * 1024  # 4MB
        mock_get_env.return_value = "5"  # 5MB threshold
        mock_simple.return_value = "test_video_id"
        
        # Execute
        result = upload_video(self.page_id, "/path/to/video.mp4", self.description, 
                            self.published, self.access_token)
        
        # Verify
        mock_simple.assert_called_once_with(
            self.page_id, "/path/to/video.mp4", self.description, 
            self.published, self.access_token
        )
        self.assertEqual(result, "test_video_id")
    
    @patch('post_to_facebook.os.path.getsize')
    @patch('post_to_facebook._upload_video_resumable')
    @patch('post_to_facebook.get_optional_env_var')
    def test_upload_video_large_file_uses_resumable_upload(self, mock_get_env, mock_resumable, mock_getsize):
        """Test that large videos use resumable upload method."""
        # Setup
        mock_getsize.return_value = 10 * 1024 * 1024  # 10MB
        mock_get_env.return_value = "5"  # 5MB threshold
        mock_resumable.return_value = "test_video_id"
        
        # Execute
        result = upload_video(self.page_id, "/path/to/large_video.mp4", self.description, 
                            self.published, self.access_token)
        
        # Verify
        mock_resumable.assert_called_once_with(
            self.page_id, "/path/to/large_video.mp4", self.description, 
            self.published, self.access_token
        )
        self.assertEqual(result, "test_video_id")
    
    @patch('post_to_facebook._graph_api_post')
    @patch('builtins.open', new_callable=mock_open, read_data=b'video_data')
    def test_upload_video_simple(self, mock_file, mock_api_post):
        """Test simple video upload method."""
        # Setup
        mock_api_post.return_value = {'id': 'test_video_id'}
        
        # Execute
        result = _upload_video_simple(self.page_id, "/path/to/video.mp4", 
                                     self.description, self.published, self.access_token)
        
        # Verify
        mock_file.assert_called_once_with("/path/to/video.mp4", 'rb')
        mock_api_post.assert_called_once()
        call_args = mock_api_post.call_args
        self.assertEqual(call_args[0][0], f"{self.page_id}/videos")
        self.assertEqual(call_args[0][1], self.access_token)
        self.assertEqual(call_args[1]['data']['description'], self.description)
        self.assertEqual(call_args[1]['data']['published'], 'true')
        self.assertEqual(result, 'test_video_id')
    
    @patch('post_to_facebook.os.path.getsize')
    @patch('post_to_facebook._graph_api_post')
    @patch('builtins.open', new_callable=mock_open)
    def test_upload_video_resumable_start_phase(self, mock_file, mock_api_post, mock_getsize):
        """Test resumable upload start phase."""
        # Setup
        video_size = 10 * 1024 * 1024  # 10MB
        mock_getsize.return_value = video_size
        
        # Mock API responses
        def api_post_side_effect(*args, **kwargs):
            action = kwargs.get('action', '')
            if action == 'start upload session':
                return {'upload_session_id': 'session_123', 'video_id': 'video_456'}
            elif action == 'transfer video chunk':
                return {'success': True}
            elif action == 'finish upload':
                return {'success': True}
            return {}
        
        mock_api_post.side_effect = api_post_side_effect
        
        # Mock file reading
        chunk_size = 4 * 1024 * 1024  # 4MB
        chunks = [b'x' * chunk_size, b'x' * chunk_size, b'x' * (video_size - 2 * chunk_size)]
        mock_file.return_value.read.side_effect = chunks + [b'']
        
        # Execute
        result = _upload_video_resumable(self.page_id, "/path/to/large_video.mp4", 
                                        self.description, self.published, self.access_token)
        
        # Verify
        self.assertEqual(result, 'video_456')
        
        # Check start phase call
        start_call = None
        for call_item in mock_api_post.call_args_list:
            if call_item[1].get('action') == 'start upload session':
                start_call = call_item
                break
        
        self.assertIsNotNone(start_call)
        self.assertEqual(start_call[1]['data']['upload_phase'], 'start')
        self.assertEqual(start_call[1]['data']['file_size'], str(video_size))
    
    @patch('post_to_facebook.os.path.getsize')
    @patch('post_to_facebook._graph_api_post')
    @patch('builtins.open', new_callable=mock_open)
    def test_upload_video_resumable_transfer_chunks(self, mock_file, mock_api_post, mock_getsize):
        """Test resumable upload transfer phase with multiple chunks."""
        # Setup
        video_size = 10 * 1024 * 1024  # 10MB
        mock_getsize.return_value = video_size
        
        # Mock API responses
        def api_post_side_effect(*args, **kwargs):
            action = kwargs.get('action', '')
            if action == 'start upload session':
                return {'upload_session_id': 'session_123', 'video_id': 'video_456'}
            elif action == 'transfer video chunk':
                return {'success': True}
            elif action == 'finish upload':
                return {'success': True}
            return {}
        
        mock_api_post.side_effect = api_post_side_effect
        
        # Mock file reading - 3 chunks
        chunk_size = 4 * 1024 * 1024  # 4MB
        chunks = [b'x' * chunk_size, b'x' * chunk_size, b'x' * (video_size - 2 * chunk_size)]
        mock_file.return_value.read.side_effect = chunks + [b'']
        
        # Execute
        result = _upload_video_resumable(self.page_id, "/path/to/large_video.mp4", 
                                        self.description, self.published, self.access_token)
        
        # Verify
        self.assertEqual(result, 'video_456')
        
        # Count transfer calls
        transfer_calls = [c for c in mock_api_post.call_args_list 
                         if c[1].get('action') == 'transfer video chunk']
        self.assertEqual(len(transfer_calls), 3)  # Should have 3 chunk uploads
        
        # Verify offsets are correct
        expected_offsets = [0, chunk_size, 2 * chunk_size]
        for i, call_item in enumerate(transfer_calls):
            self.assertEqual(call_item[1]['data']['start_offset'], str(expected_offsets[i]))
            self.assertEqual(call_item[1]['data']['upload_phase'], 'transfer')
            self.assertEqual(call_item[1]['data']['upload_session_id'], 'session_123')
    
    @patch('post_to_facebook.os.path.getsize')
    @patch('post_to_facebook._graph_api_post')
    @patch('builtins.open', new_callable=mock_open)
    def test_upload_video_resumable_finish_phase(self, mock_file, mock_api_post, mock_getsize):
        """Test resumable upload finish phase."""
        # Setup
        video_size = 5 * 1024 * 1024  # 5MB
        mock_getsize.return_value = video_size
        
        # Mock API responses
        def api_post_side_effect(*args, **kwargs):
            action = kwargs.get('action', '')
            if action == 'start upload session':
                return {'upload_session_id': 'session_123', 'video_id': 'video_456'}
            elif action == 'transfer video chunk':
                return {'success': True}
            elif action == 'finish upload':
                return {'success': True}
            return {}
        
        mock_api_post.side_effect = api_post_side_effect
        
        # Mock file reading - 2 chunks
        chunk_size = 4 * 1024 * 1024  # 4MB
        chunks = [b'x' * chunk_size, b'x' * (video_size - chunk_size)]
        mock_file.return_value.read.side_effect = chunks + [b'']
        
        # Execute
        result = _upload_video_resumable(self.page_id, "/path/to/large_video.mp4", 
                                        self.description, self.published, self.access_token)
        
        # Verify
        self.assertEqual(result, 'video_456')
        
        # Check finish phase call
        finish_call = None
        for call_item in mock_api_post.call_args_list:
            if call_item[1].get('action') == 'finish upload':
                finish_call = call_item
                break
        
        self.assertIsNotNone(finish_call)
        self.assertEqual(finish_call[1]['data']['upload_phase'], 'finish')
        self.assertEqual(finish_call[1]['data']['upload_session_id'], 'session_123')
        self.assertEqual(finish_call[1]['data']['description'], self.description)
        self.assertEqual(finish_call[1]['data']['published'], 'true')
    
    @patch('post_to_facebook.os.path.getsize')
    @patch('post_to_facebook._graph_api_post')
    @patch('builtins.open', new_callable=mock_open)
    def test_upload_video_resumable_missing_session_id(self, mock_file, mock_api_post, mock_getsize):
        """Test resumable upload handles missing upload_session_id error."""
        # Setup
        mock_getsize.return_value = 10 * 1024 * 1024
        mock_api_post.return_value = {}  # No upload_session_id
        
        # Execute and verify
        with self.assertRaises(RuntimeError) as context:
            _upload_video_resumable(self.page_id, "/path/to/large_video.mp4", 
                                   self.description, self.published, self.access_token)
        
        self.assertIn("Failed to get upload_session_id", str(context.exception))
    
    @patch('post_to_facebook.os.path.getsize')
    @patch('post_to_facebook._graph_api_post')
    @patch('builtins.open', new_callable=mock_open)
    def test_upload_video_resumable_finish_failure(self, mock_file, mock_api_post, mock_getsize):
        """Test resumable upload handles finish phase failure."""
        # Setup
        video_size = 5 * 1024 * 1024
        mock_getsize.return_value = video_size
        
        # Mock API responses
        def api_post_side_effect(*args, **kwargs):
            action = kwargs.get('action', '')
            if action == 'start upload session':
                return {'upload_session_id': 'session_123', 'video_id': 'video_456'}
            elif action == 'transfer video chunk':
                return {'success': True}
            elif action == 'finish upload':
                return {'success': False}  # Finish fails
            return {}
        
        mock_api_post.side_effect = api_post_side_effect
        
        # Mock file reading
        chunk_size = 4 * 1024 * 1024
        chunks = [b'x' * chunk_size, b'x' * (video_size - chunk_size)]
        mock_file.return_value.read.side_effect = chunks + [b'']
        
        # Execute and verify
        with self.assertRaises(RuntimeError) as context:
            _upload_video_resumable(self.page_id, "/path/to/large_video.mp4", 
                                   self.description, self.published, self.access_token)
        
        self.assertIn("Upload finish phase failed", str(context.exception))


class TestPhotoUpload(unittest.TestCase):
    """Test cases for photo upload functionality."""
    
    @patch('post_to_facebook._graph_api_post')
    @patch('builtins.open', new_callable=mock_open, read_data=b'photo_data')
    def test_upload_photo(self, mock_file, mock_api_post):
        """Test photo upload."""
        # Setup
        mock_api_post.return_value = {'post_id': 'test_post_id'}
        
        # Execute
        result = upload_photo("page_123", "/path/to/photo.jpg", "Test message", True, "token_456")
        
        # Verify
        mock_file.assert_called_once_with("/path/to/photo.jpg", 'rb')
        mock_api_post.assert_called_once()
        call_args = mock_api_post.call_args
        self.assertEqual(call_args[0][0], "page_123/photos")
        self.assertEqual(call_args[0][1], "token_456")
        self.assertEqual(call_args[1]['data']['message'], "Test message")
        self.assertEqual(call_args[1]['data']['published'], 'true')
        self.assertEqual(result, 'test_post_id')


if __name__ == '__main__':
    unittest.main()
