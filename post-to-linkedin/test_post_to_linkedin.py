#!/usr/bin/env python3
"""
Unit tests for post_to_linkedin.py
"""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path

# Add the current directory and common module to path
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent / 'common'))

# Import the module to test
from post_to_linkedin import LinkedInAPI, post_to_linkedin


class TestLinkedInAPI(unittest.TestCase):
    """Test cases for LinkedInAPI class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.access_token = "test_access_token"
        self.api = LinkedInAPI(self.access_token)
        self.author_id = "urn:li:person:12345"
    
    def test_init(self):
        """Test LinkedInAPI initialization."""
        self.assertEqual(self.api.access_token, self.access_token)
        self.assertEqual(self.api.base_url, "https://api.linkedin.com/v2")
        self.assertIn("Authorization", self.api.headers)
        self.assertEqual(self.api.headers["Authorization"], f"Bearer {self.access_token}")
    
    @patch('post_to_linkedin.requests.post')
    @patch('post_to_linkedin.requests.put')
    @patch('builtins.open', new_callable=mock_open, read_data=b'fake_image_data')
    @patch('os.path.exists')
    def test_upload_image(self, mock_exists, mock_file, mock_put, mock_post):
        """Test image upload functionality."""
        # Mock responses
        mock_exists.return_value = True
        
        # Mock register upload response
        register_response = MagicMock()
        register_response.status_code = 200
        register_response.raise_for_status = MagicMock()
        register_response.json.return_value = {
            'value': {
                'uploadMechanism': {
                    'com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest': {
                        'uploadUrl': 'https://upload.url/image'
                    }
                },
                'asset': 'urn:li:digitalmediaAsset:12345'
            }
        }
        
        # Mock upload response
        upload_response = MagicMock()
        upload_response.status_code = 201
        upload_response.raise_for_status = MagicMock()
        
        mock_post.return_value = register_response
        mock_put.return_value = upload_response
        
        # Test upload
        image_path = "/tmp/test_image.jpg"
        asset_urn = self.api.upload_image(self.author_id, image_path)
        
        # Verify the asset URN is returned
        self.assertEqual(asset_urn, 'urn:li:digitalmediaAsset:12345')
        
        # Verify register upload was called
        self.assertTrue(mock_post.called)
        
        # Verify image binary was uploaded
        self.assertTrue(mock_put.called)
    
    @patch('post_to_linkedin.requests.post')
    def test_create_post_text_only(self, mock_post):
        """Test creating a text-only post."""
        # Mock response
        response = MagicMock()
        response.status_code = 201
        response.raise_for_status = MagicMock()
        response.json.return_value = {'id': 'urn:li:share:67890'}
        mock_post.return_value = response
        
        # Create post
        content = "This is a test post"
        post_id = self.api.create_post(self.author_id, content)
        
        # Verify
        self.assertEqual(post_id, 'urn:li:share:67890')
        self.assertTrue(mock_post.called)
        
        # Check the request payload
        call_args = mock_post.call_args
        post_data = call_args[1]['json']
        self.assertEqual(post_data['author'], self.author_id)
        self.assertEqual(post_data['specificContent']['com.linkedin.ugc.ShareContent']['shareCommentary']['text'], content)
        self.assertEqual(post_data['specificContent']['com.linkedin.ugc.ShareContent']['shareMediaCategory'], 'NONE')
    
    @patch('post_to_linkedin.requests.post')
    def test_create_post_with_media(self, mock_post):
        """Test creating a post with media."""
        # Mock response
        response = MagicMock()
        response.status_code = 201
        response.raise_for_status = MagicMock()
        response.json.return_value = {'id': 'urn:li:share:67890'}
        mock_post.return_value = response
        
        # Create post with media
        content = "Post with image"
        media_assets = ['urn:li:digitalmediaAsset:12345']
        post_id = self.api.create_post(self.author_id, content, media_assets=media_assets)
        
        # Verify
        self.assertEqual(post_id, 'urn:li:share:67890')
        
        # Check the request payload
        call_args = mock_post.call_args
        post_data = call_args[1]['json']
        self.assertEqual(post_data['specificContent']['com.linkedin.ugc.ShareContent']['shareMediaCategory'], 'IMAGE')
        self.assertEqual(len(post_data['specificContent']['com.linkedin.ugc.ShareContent']['media']), 1)
    
    @patch('post_to_linkedin.requests.post')
    def test_create_post_with_link(self, mock_post):
        """Test creating a post with a link."""
        # Mock response
        response = MagicMock()
        response.status_code = 201
        response.raise_for_status = MagicMock()
        response.json.return_value = {'id': 'urn:li:share:67890'}
        mock_post.return_value = response
        
        # Create post with link
        content = "Check out this article"
        link_url = "https://example.com/article"
        post_id = self.api.create_post(self.author_id, content, link_url=link_url)
        
        # Verify
        self.assertEqual(post_id, 'urn:li:share:67890')
        
        # Check the request payload
        call_args = mock_post.call_args
        post_data = call_args[1]['json']
        self.assertEqual(post_data['specificContent']['com.linkedin.ugc.ShareContent']['shareMediaCategory'], 'ARTICLE')
        self.assertEqual(post_data['specificContent']['com.linkedin.ugc.ShareContent']['media'][0]['originalUrl'], link_url)


class TestPostToLinkedIn(unittest.TestCase):
    """Test cases for the main post_to_linkedin function."""
    
    def setUp(self):
        """Set up test environment."""
        # Set required environment variables
        os.environ['LINKEDIN_ACCESS_TOKEN'] = 'test_token'
        os.environ['LINKEDIN_AUTHOR_ID'] = 'urn:li:person:12345'
        os.environ['POST_CONTENT'] = 'Test post'
        os.environ['LOG_LEVEL'] = 'ERROR'  # Suppress logs during tests
        
        # Clear optional variables
        os.environ.pop('MEDIA_FILES', None)
        os.environ.pop('POST_LINK', None)
        os.environ.pop('CONTENT_JSON', None)
        os.environ.pop('DRY_RUN', None)
        os.environ.pop('GITHUB_OUTPUT', None)
    
    def tearDown(self):
        """Clean up test environment."""
        for var in ['LINKEDIN_ACCESS_TOKEN', 'LINKEDIN_AUTHOR_ID', 'POST_CONTENT', 
                    'LOG_LEVEL', 'MEDIA_FILES', 'POST_LINK', 'CONTENT_JSON', 'DRY_RUN']:
            os.environ.pop(var, None)
    
    @patch('post_to_linkedin.LinkedInAPI')
    def test_post_to_linkedin_success(self, mock_linkedin_api):
        """Test successful LinkedIn post."""
        # Mock the API
        mock_api_instance = MagicMock()
        mock_api_instance.create_post.return_value = 'urn:li:share:12345'
        mock_linkedin_api.return_value = mock_api_instance
        
        # Call the function
        with patch('sys.exit') as mock_exit:
            post_to_linkedin()
            # Should not call sys.exit on success
            mock_exit.assert_not_called()
        
        # Verify API was called
        mock_api_instance.create_post.assert_called_once()
    
    @patch('post_to_linkedin.LinkedInAPI')
    @patch('os.path.getsize')
    @patch('os.path.exists')
    def test_post_to_linkedin_with_media(self, mock_exists, mock_getsize, mock_linkedin_api):
        """Test LinkedIn post with media."""
        os.environ['MEDIA_FILES'] = '/tmp/test.jpg'
        mock_exists.return_value = True
        mock_getsize.return_value = 1024
        
        # Mock the API
        mock_api_instance = MagicMock()
        mock_api_instance.upload_image.return_value = 'urn:li:digitalmediaAsset:12345'
        mock_api_instance.create_post.return_value = 'urn:li:share:12345'
        mock_linkedin_api.return_value = mock_api_instance
        
        # Call the function
        with patch('sys.exit') as mock_exit:
            post_to_linkedin()
            mock_exit.assert_not_called()
        
        # Verify media was uploaded
        mock_api_instance.upload_image.assert_called_once()
        mock_api_instance.create_post.assert_called_once()
    
    @patch('post_to_linkedin.dry_run_guard')
    def test_dry_run_mode(self, mock_dry_run_guard):
        """Test dry-run mode."""
        os.environ['DRY_RUN'] = 'true'
        
        # Mock dry_run_guard to simulate exit
        mock_dry_run_guard.side_effect = SystemExit(0)
        
        # Call the function
        with self.assertRaises(SystemExit):
            post_to_linkedin()
        
        # Verify dry_run_guard was called
        mock_dry_run_guard.assert_called_once()


if __name__ == '__main__':
    unittest.main()
