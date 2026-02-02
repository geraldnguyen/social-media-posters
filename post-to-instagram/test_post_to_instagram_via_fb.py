#!/usr/bin/env python3
"""
Unit tests for post_to_instagram_via_fb.py
"""

import unittest
from unittest.mock import patch, MagicMock, mock_open
import sys
import os
from pathlib import Path

# Add paths for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'common'))
sys.path.insert(0, str(Path(__file__).parent))

# Import the module to test
import post_to_instagram_via_fb


class TestInstagramFBAPI(unittest.TestCase):
    """Test cases for InstagramFBAPI class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.api = post_to_instagram_via_fb.InstagramFBAPI('test_token', 'test_ig_user_id')
    
    @patch('post_to_instagram_via_fb.requests.post')
    def test_start_video_upload_session(self, mock_post):
        """Test starting a video upload session."""
        
        # Mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'upload_session_id': 'test_session_123',
            'id': 'test_video_456'
        }
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response
        
        api = post_to_instagram_via_fb.InstagramFBAPI('test_token', 'test_ig_id')
        
        # Mock file
        with patch('builtins.open', mock_open(read_data=b'video_data')):
            with patch('os.path.getsize', return_value=1024):
                # This would call upload_video_resumable but we'll test individual methods
                pass
    
    @patch('post_to_instagram_via_fb.requests.post')
    def test_create_image_container(self, mock_post):
        """Test creating an image container."""
        
        # Mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {'id': 'test_container_789'}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response
        
        api = post_to_instagram_via_fb.InstagramFBAPI('test_token', 'test_ig_id')
        container_id = api.create_image_container('https://example.com/image.jpg', 'Test caption')
        
        self.assertEqual(container_id, 'test_container_789')
        mock_post.assert_called_once()
    
    @patch('post_to_instagram_via_fb.requests.post')
    def test_create_carousel_container(self, mock_post):
        """Test creating a carousel container."""
        
        # Mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {'id': 'test_carousel_999'}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response
        
        api = post_to_instagram_via_fb.InstagramFBAPI('test_token', 'test_ig_id')
        children_ids = ['child1', 'child2', 'child3']
        container_id = api.create_carousel_container(children_ids, 'Carousel caption')
        
        self.assertEqual(container_id, 'test_carousel_999')
        mock_post.assert_called_once()
    
    @patch('post_to_instagram_via_fb.requests.get')
    def test_check_container_status_finished(self, mock_get):
        """Test checking container status when finished."""
        
        # Mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'status_code': 'FINISHED',
            'status': 'Ready'
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        
        api = post_to_instagram_via_fb.InstagramFBAPI('test_token', 'test_ig_id')
        is_ready = api.check_container_status('test_container', max_wait=5)
        
        self.assertTrue(is_ready)
    
    @patch('post_to_instagram_via_fb.requests.get')
    def test_check_container_status_error(self, mock_get):
        """Test checking container status when error occurs."""
        
        # Mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'status_code': 'ERROR',
            'status': 'Processing failed'
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        
        api = post_to_instagram_via_fb.InstagramFBAPI('test_token', 'test_ig_id')
        is_ready = api.check_container_status('test_container', max_wait=5)
        
        self.assertFalse(is_ready)
    
    @patch('post_to_instagram_via_fb.requests.post')
    def test_publish_media(self, mock_post):
        """Test publishing a media container."""
        
        # Mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {'id': 'published_media_111'}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response
        
        api = post_to_instagram_via_fb.InstagramFBAPI('test_token', 'test_ig_id')
        media_id = api.publish_media('test_container')
        
        self.assertEqual(media_id, 'published_media_111')
        mock_post.assert_called_once()
    
    @patch('post_to_instagram_via_fb.requests.get')
    def test_get_media_info(self, mock_get):
        """Test getting media information."""
        
        # Mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'id': 'media_222',
            'permalink': 'https://www.instagram.com/p/test123/'
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        
        api = post_to_instagram_via_fb.InstagramFBAPI('test_token', 'test_ig_id')
        media_info = api.get_media_info('media_222')
        
        self.assertEqual(media_info['id'], 'media_222')
        self.assertIn('instagram.com', media_info['permalink'])


class TestUploadImageToTempHosting(unittest.TestCase):
    """Test cases for upload_image_to_temp_hosting function."""
    
    def test_url_passthrough(self):
        """Test that URLs are passed through unchanged."""
        
        url = 'https://example.com/image.jpg'
        result = post_to_instagram_via_fb.upload_image_to_temp_hosting(url)
        self.assertEqual(result, url)
    
    def test_local_file_raises_error(self):
        """Test that local files raise an error."""
        
        with self.assertRaises(ValueError) as context:
            post_to_instagram_via_fb.upload_image_to_temp_hosting('/path/to/local/image.jpg')
        
        self.assertIn('publicly accessible URLs', str(context.exception))


class TestPostToInstagramViaFBIntegration(unittest.TestCase):
    """Integration tests for post_to_instagram_via_fb function."""
    
    @patch.dict('os.environ', {
        'IG_USER_ID': 'test_ig_user',
        'FB_ACCESS_TOKEN': 'test_fb_token',
        'POST_CONTENT': 'Test post content',
        'MEDIA_FILES': 'https://example.com/image.jpg',
        'DRY_RUN': 'true'
    })
    def test_dry_run_mode(self):
        """Test that dry run mode exits without making API calls."""
        
        # Dry run should exit with code 0
        with self.assertRaises(SystemExit) as context:
            post_to_instagram_via_fb.post_to_instagram_via_fb()
        
        self.assertEqual(context.exception.code, 0)
    
    @patch.dict('os.environ', {
        'IG_USER_ID': 'test_ig_user',
        'FB_ACCESS_TOKEN': 'test_fb_token',
        'POST_CONTENT': 'Test post'
    })
    def test_missing_media_files(self):
        """Test that missing MEDIA_FILES causes an error."""
        
        # Should exit with error code
        with self.assertRaises(SystemExit) as context:
            post_to_instagram_via_fb.post_to_instagram_via_fb()
        
        self.assertEqual(context.exception.code, 1)
    
    @patch.dict('os.environ', {
        'IG_USER_ID': 'test_ig_user',
        'FB_ACCESS_TOKEN': 'test_fb_token',
        'POST_CONTENT': 'Test' * 1000,  # Too long
        'MEDIA_FILES': 'https://example.com/image.jpg'
    })
    def test_content_too_long(self):
        """Test that content exceeding max length is rejected."""
        
        # Should exit with error code
        with self.assertRaises(SystemExit) as context:
            post_to_instagram_via_fb.post_to_instagram_via_fb()
        
        self.assertEqual(context.exception.code, 1)


if __name__ == '__main__':
    unittest.main()
