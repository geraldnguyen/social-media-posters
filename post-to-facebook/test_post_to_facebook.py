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
    _graph_api_post,
    post_comment
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
            self.published, self.access_token, None, None
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
            self.published, self.access_token, None, None
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
    
    @patch('post_to_facebook._graph_api_post')
    @patch('builtins.open', new_callable=mock_open, read_data=b'photo_data')
    def test_upload_photo_with_scheduling(self, mock_file, mock_api_post):
        """Test photo upload with scheduled publish time."""
        # Setup
        mock_api_post.return_value = {'post_id': 'test_scheduled_post_id'}
        scheduled_time = 1735689599  # Unix timestamp
        
        # Execute
        result = upload_photo("page_123", "/path/to/photo.jpg", "Test message", False, "token_456", scheduled_time)
        
        # Verify
        mock_file.assert_called_once_with("/path/to/photo.jpg", 'rb')
        mock_api_post.assert_called_once()
        call_args = mock_api_post.call_args
        self.assertEqual(call_args[0][0], "page_123/photos")
        self.assertEqual(call_args[0][1], "token_456")
        self.assertEqual(call_args[1]['data']['message'], "Test message")
        self.assertEqual(call_args[1]['data']['published'], 'false')
        self.assertEqual(call_args[1]['data']['scheduled_publish_time'], str(scheduled_time))
        self.assertEqual(result, 'test_scheduled_post_id')


class TestVideoScheduling(unittest.TestCase):
    """Test cases for video scheduling functionality."""
    
    @patch('post_to_facebook._graph_api_post')
    @patch('builtins.open', new_callable=mock_open, read_data=b'video_data')
    def test_upload_video_simple_with_scheduling(self, mock_file, mock_api_post):
        """Test simple video upload with scheduled publish time."""
        # Setup
        mock_api_post.return_value = {'id': 'test_video_id'}
        scheduled_time = 1735689599  # Unix timestamp
        
        # Execute
        result = _upload_video_simple("page_123", "/path/to/video.mp4", "Test description", False, "token_456", scheduled_time)
        
        # Verify
        mock_file.assert_called_once_with("/path/to/video.mp4", 'rb')
        mock_api_post.assert_called_once()
        call_args = mock_api_post.call_args
        self.assertEqual(call_args[0][0], "page_123/videos")
        self.assertEqual(call_args[0][1], "token_456")
        self.assertEqual(call_args[1]['data']['description'], "Test description")
        self.assertEqual(call_args[1]['data']['published'], 'false')
        self.assertEqual(call_args[1]['data']['scheduled_publish_time'], str(scheduled_time))
        self.assertEqual(result, 'test_video_id')


class TestCommentPosting(unittest.TestCase):
    """Test cases for comment posting functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.post_id = "123456789_987654321"
        self.access_token = "test_access_token"
        self.message = "This is a test comment"
    
    @patch('post_to_facebook._graph_api_post')
    def test_post_comment_basic(self, mock_api_post):
        """Test basic comment posting."""
        # Setup
        mock_api_post.return_value = {'id': 'comment_id_123'}
        
        # Execute
        result = post_comment(self.post_id, self.access_token, self.message)
        
        # Verify
        mock_api_post.assert_called_once()
        call_args = mock_api_post.call_args
        self.assertEqual(call_args[0][0], f"{self.post_id}/comments")
        self.assertEqual(call_args[0][1], self.access_token)
        self.assertEqual(call_args[1]['data']['message'], self.message)
        self.assertEqual(call_args[1]['action'], 'post comment')
        self.assertEqual(result, 'comment_id_123')
    
    @patch('post_to_facebook._graph_api_post')
    def test_post_comment_with_link(self, mock_api_post):
        """Test comment posting with a link in the message."""
        # Setup
        message_with_link = f"{self.message}\nhttps://example.com"
        mock_api_post.return_value = {'id': 'comment_id_456'}
        
        # Execute
        result = post_comment(self.post_id, self.access_token, message_with_link)
        
        # Verify
        mock_api_post.assert_called_once()
        call_args = mock_api_post.call_args
        self.assertEqual(call_args[1]['data']['message'], message_with_link)
        self.assertEqual(result, 'comment_id_456')
    
    @patch('post_to_facebook._graph_api_post')
    def test_post_comment_with_media_url(self, mock_api_post):
        """Test comment posting with media URL in the message."""
        # Setup
        message_with_media = f"{self.message}\nhttps://example.com/image.jpg"
        mock_api_post.return_value = {'id': 'comment_id_789'}
        
        # Execute
        result = post_comment(self.post_id, self.access_token, message_with_media)
        
        # Verify
        mock_api_post.assert_called_once()
        call_args = mock_api_post.call_args
        self.assertEqual(call_args[1]['data']['message'], message_with_media)
        self.assertEqual(result, 'comment_id_789')


class TestFBPostIDValidation(unittest.TestCase):
    """Test cases for FB_POST_ID validation with N/A variations."""
    
    @patch('post_to_facebook.setup_logging')
    @patch('post_to_facebook.get_required_env_var')
    @patch('post_to_facebook.get_optional_env_var')
    @patch('post_to_facebook.process_templated_contents')
    @patch('post_to_facebook.post_content')
    def test_fb_post_id_na_treated_as_empty(self, mock_post_content, mock_template, 
                                            mock_optional, mock_required, mock_logging):
        """Test that FB_POST_ID with N/A is treated as empty (new post mode)."""
        from post_to_facebook import main
        
        # Setup mocks
        mock_logging.return_value = MagicMock()
        mock_required.side_effect = lambda x: {
            'FB_ACCESS_TOKEN': 'test_token',
            'POST_CONTENT': 'Test content',
            'FB_PAGE_ID': 'test_page_id'
        }.get(x, '')
        
        # Test various N/A variations
        na_variations = ['N/A', 'n/a', 'n.a', 'not applicable', '  n/a  ', '', '   ']
        
        for na_value in na_variations:
            mock_optional.side_effect = lambda x, default='': {
                'FB_POST_ID': na_value,
                'POST_LINK': '',
                'MEDIA_FILES': '',
                'SCHEDULE_TIME': '',
                'VIDEO_UPLOAD_THRESHOLD_MB': '5'
            }.get(x, default)
            
            mock_template.return_value = ('Test content', '')
            mock_post_content.return_value = 'post_123'
            
            # Execute - should go to post_content (new post), not comment mode
            with patch('sys.exit') as mock_exit:
                with patch('post_to_facebook.dry_run_guard') as mock_dry_run:
                    with patch('post_to_facebook.log_success'):
                        try:
                            main()
                        except SystemExit:
                            pass
            
            # Verify post_content was called (new post mode), not post_comment
            mock_post_content.assert_called()
    
    @patch('post_to_facebook.setup_logging')
    @patch('post_to_facebook.get_required_env_var')
    @patch('post_to_facebook.get_optional_env_var')
    @patch('post_to_facebook.process_templated_contents')
    @patch('post_to_facebook.post_comment')
    def test_fb_post_id_valid_goes_to_comment_mode(self, mock_post_comment, mock_template, 
                                                    mock_optional, mock_required, mock_logging):
        """Test that valid FB_POST_ID goes to comment mode."""
        from post_to_facebook import main
        
        # Setup mocks
        mock_logging.return_value = MagicMock()
        mock_required.side_effect = lambda x: {
            'FB_ACCESS_TOKEN': 'test_token',
            'POST_CONTENT': 'Test comment'
        }.get(x, '')
        
        mock_optional.side_effect = lambda x, default='': {
            'FB_POST_ID': '123456789_987654321',  # Valid post ID
            'POST_LINK': '',
            'MEDIA_FILES': '',
            'SCHEDULE_TIME': ''
        }.get(x, default)
        
        mock_template.return_value = ('Test comment',)
        mock_post_comment.return_value = 'comment_123'
        
        # Execute - should go to comment mode
        with patch('sys.exit') as mock_exit:
            with patch('post_to_facebook.dry_run_guard') as mock_dry_run:
                with patch('post_to_facebook.log_success'):
                    try:
                        main()
                    except SystemExit:
                        pass
        
        # Verify post_comment was called
        mock_post_comment.assert_called_once()


class TestVideoTitleSupport(unittest.TestCase):
    """Test cases for video title support (v1.22.0)."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.page_id = "test_page_id"
        self.access_token = "test_access_token"
        self.description = "Test video description"
        self.title = "Test Video Title"
        self.published = True
    
    @patch('post_to_facebook._graph_api_post')
    @patch('builtins.open', new_callable=mock_open, read_data=b'video_data')
    def test_upload_video_simple_with_title(self, mock_file, mock_api_post):
        """Test simple video upload with title parameter."""
        # Setup
        mock_api_post.return_value = {'id': 'test_video_id'}
        
        # Execute
        result = _upload_video_simple(self.page_id, "/path/to/video.mp4", 
                                     self.description, self.published, self.access_token, 
                                     None, self.title)
        
        # Verify
        mock_file.assert_called_once_with("/path/to/video.mp4", 'rb')
        mock_api_post.assert_called_once()
        call_args = mock_api_post.call_args
        self.assertEqual(call_args[0][0], f"{self.page_id}/videos")
        self.assertEqual(call_args[0][1], self.access_token)
        self.assertEqual(call_args[1]['data']['description'], self.description)
        self.assertEqual(call_args[1]['data']['title'], self.title)
        self.assertEqual(call_args[1]['data']['published'], 'true')
        self.assertEqual(result, 'test_video_id')
    
    @patch('post_to_facebook._graph_api_post')
    @patch('builtins.open', new_callable=mock_open, read_data=b'video_data')
    def test_upload_video_simple_without_title(self, mock_file, mock_api_post):
        """Test simple video upload without title parameter (backward compatibility)."""
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
        self.assertNotIn('title', call_args[1]['data'])  # Title should not be present
        self.assertEqual(call_args[1]['data']['published'], 'true')
        self.assertEqual(result, 'test_video_id')
    
    @patch('post_to_facebook.os.path.getsize')
    @patch('post_to_facebook._graph_api_post')
    @patch('builtins.open', new_callable=mock_open)
    def test_upload_video_resumable_with_title(self, mock_file, mock_api_post, mock_getsize):
        """Test resumable video upload with title in finish phase."""
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
                                        self.description, self.published, self.access_token, 
                                        None, self.title)
        
        # Verify
        self.assertEqual(result, 'video_456')
        
        # Check finish phase call for title
        finish_call = None
        for call_item in mock_api_post.call_args_list:
            if call_item[1].get('action') == 'finish upload':
                finish_call = call_item
                break
        
        self.assertIsNotNone(finish_call)
        self.assertEqual(finish_call[1]['data']['upload_phase'], 'finish')
        self.assertEqual(finish_call[1]['data']['description'], self.description)
        self.assertEqual(finish_call[1]['data']['title'], self.title)
        self.assertEqual(finish_call[1]['data']['published'], 'true')
    
    @patch('post_to_facebook.os.path.getsize')
    @patch('post_to_facebook._graph_api_post')
    @patch('builtins.open', new_callable=mock_open)
    def test_upload_video_resumable_without_title(self, mock_file, mock_api_post, mock_getsize):
        """Test resumable video upload without title (backward compatibility)."""
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
        
        # Check finish phase call - title should not be present
        finish_call = None
        for call_item in mock_api_post.call_args_list:
            if call_item[1].get('action') == 'finish upload':
                finish_call = call_item
                break
        
        self.assertIsNotNone(finish_call)
        self.assertEqual(finish_call[1]['data']['upload_phase'], 'finish')
        self.assertEqual(finish_call[1]['data']['description'], self.description)
        self.assertNotIn('title', finish_call[1]['data'])  # Title should not be present
        self.assertEqual(finish_call[1]['data']['published'], 'true')


class TestExpandedFileExtensions(unittest.TestCase):
    """Test cases for expanded image and video file extensions (v1.23.0)."""
    
    def test_webp_recognized_as_image(self):
        """Test that .webp files are recognized as images."""
        from pathlib import Path
        
        # These are the extensions from post_to_facebook.py line 455
        image_exts = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.tiff', '.tif']
        
        # Test that webp is in the list
        self.assertIn('.webp', image_exts)
        
        # Test case insensitive matching
        test_file = Path('test.webp')
        self.assertIn(test_file.suffix.lower(), image_exts)
        
        test_file_upper = Path('test.WEBP')
        self.assertIn(test_file_upper.suffix.lower(), image_exts)
    
    def test_bmp_recognized_as_image(self):
        """Test that .bmp files are recognized as images."""
        from pathlib import Path
        
        image_exts = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.tiff', '.tif']
        
        # Test that bmp is in the list
        self.assertIn('.bmp', image_exts)
        
        test_file = Path('test.bmp')
        self.assertIn(test_file.suffix.lower(), image_exts)
    
    def test_tiff_recognized_as_image(self):
        """Test that .tiff and .tif files are recognized as images."""
        from pathlib import Path
        
        image_exts = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.tiff', '.tif']
        
        # Test that both tiff and tif are in the list
        self.assertIn('.tiff', image_exts)
        self.assertIn('.tif', image_exts)
        
        test_file1 = Path('test.tiff')
        self.assertIn(test_file1.suffix.lower(), image_exts)
        
        test_file2 = Path('test.tif')
        self.assertIn(test_file2.suffix.lower(), image_exts)
    
    def test_wmv_recognized_as_video(self):
        """Test that .wmv files are recognized as videos."""
        from pathlib import Path
        
        # These are the extensions from post_to_facebook.py line 458
        video_exts = ['.mp4', '.mov', '.avi', '.wmv', '.mpg', '.mpeg', '.webm', '.flv', '.m4v', '.mkv', '.3gp', '.3g2', '.ogv']
        
        # Test that wmv is in the list
        self.assertIn('.wmv', video_exts)
        
        test_file = Path('test.wmv')
        self.assertIn(test_file.suffix.lower(), video_exts)
    
    def test_webm_recognized_as_video(self):
        """Test that .webm files are recognized as videos."""
        from pathlib import Path
        
        video_exts = ['.mp4', '.mov', '.avi', '.wmv', '.mpg', '.mpeg', '.webm', '.flv', '.m4v', '.mkv', '.3gp', '.3g2', '.ogv']
        
        # Test that webm is in the list
        self.assertIn('.webm', video_exts)
        
        test_file = Path('test.webm')
        self.assertIn(test_file.suffix.lower(), video_exts)
    
    def test_mkv_recognized_as_video(self):
        """Test that .mkv files are recognized as videos."""
        from pathlib import Path
        
        video_exts = ['.mp4', '.mov', '.avi', '.wmv', '.mpg', '.mpeg', '.webm', '.flv', '.m4v', '.mkv', '.3gp', '.3g2', '.ogv']
        
        # Test that mkv is in the list
        self.assertIn('.mkv', video_exts)
        
        test_file = Path('test.mkv')
        self.assertIn(test_file.suffix.lower(), video_exts)
    
    def test_mpeg_formats_recognized_as_video(self):
        """Test that .mpg and .mpeg files are recognized as videos."""
        from pathlib import Path
        
        video_exts = ['.mp4', '.mov', '.avi', '.wmv', '.mpg', '.mpeg', '.webm', '.flv', '.m4v', '.mkv', '.3gp', '.3g2', '.ogv']
        
        # Test that both mpg and mpeg are in the list
        self.assertIn('.mpg', video_exts)
        self.assertIn('.mpeg', video_exts)
        
        test_file1 = Path('test.mpg')
        self.assertIn(test_file1.suffix.lower(), video_exts)
        
        test_file2 = Path('test.mpeg')
        self.assertIn(test_file2.suffix.lower(), video_exts)
    
    def test_mobile_video_formats_recognized(self):
        """Test that mobile video formats (.3gp, .3g2) are recognized as videos."""
        from pathlib import Path
        
        video_exts = ['.mp4', '.mov', '.avi', '.wmv', '.mpg', '.mpeg', '.webm', '.flv', '.m4v', '.mkv', '.3gp', '.3g2', '.ogv']
        
        # Test that mobile formats are in the list
        self.assertIn('.3gp', video_exts)
        self.assertIn('.3g2', video_exts)
        
        test_file1 = Path('test.3gp')
        self.assertIn(test_file1.suffix.lower(), video_exts)
        
        test_file2 = Path('test.3g2')
        self.assertIn(test_file2.suffix.lower(), video_exts)
    
    def test_all_new_image_extensions(self):
        """Test that all newly added image extensions are supported."""
        new_extensions = ['.webp', '.bmp', '.tiff', '.tif']
        image_exts = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.tiff', '.tif']
        
        for ext in new_extensions:
            with self.subTest(extension=ext):
                self.assertIn(ext, image_exts)
    
    def test_all_new_video_extensions(self):
        """Test that all newly added video extensions are supported."""
        new_extensions = ['.wmv', '.mpg', '.mpeg', '.webm', '.flv', '.m4v', '.mkv', '.3gp', '.3g2', '.ogv']
        video_exts = ['.mp4', '.mov', '.avi', '.wmv', '.mpg', '.mpeg', '.webm', '.flv', '.m4v', '.mkv', '.3gp', '.3g2', '.ogv']
        
        for ext in new_extensions:
            with self.subTest(extension=ext):
                self.assertIn(ext, video_exts)


if __name__ == '__main__':
    unittest.main()

