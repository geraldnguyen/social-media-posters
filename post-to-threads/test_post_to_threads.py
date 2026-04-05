#!/usr/bin/env python3
"""
Unit tests for post_to_threads module, specifically link validation and retry logic.
"""

import sys
import os
from pathlib import Path
import unittest
from unittest.mock import patch, MagicMock
import requests

# Add parent and common module to path
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent / 'common'))

from post_to_threads import validate_link_url, check_link_accessibility, ThreadsAPI


class TestValidateLinkUrl(unittest.TestCase):
    """Test cases for validate_link_url function."""
    
    def test_valid_https_url(self):
        """Test that valid HTTPS URL is accepted."""
        self.assertTrue(validate_link_url("https://tellstory.net/stories/spiritual/david-and-jonathan/"))
    
    def test_valid_http_url(self):
        """Test that valid HTTP URL is accepted."""
        self.assertTrue(validate_link_url("http://example.com"))
    
    def test_url_with_query_params(self):
        """Test URL with query parameters."""
        self.assertTrue(validate_link_url("https://example.com/path?key=value&foo=bar"))
    
    def test_url_with_fragment(self):
        """Test URL with fragment identifier."""
        self.assertTrue(validate_link_url("https://example.com/path#section"))
    
    def test_invalid_url_no_scheme(self):
        """Test that URL without http/https scheme is rejected."""
        self.assertFalse(validate_link_url("example.com/path"))
    
    def test_invalid_url_wrong_scheme(self):
        """Test that URL with wrong scheme is rejected."""
        self.assertFalse(validate_link_url("ftp://example.com"))
    
    def test_none_input(self):
        """Test that None input is rejected."""
        self.assertFalse(validate_link_url(None))
    
    def test_empty_string(self):
        """Test that empty string is rejected."""
        self.assertFalse(validate_link_url(""))
    
    def test_whitespace_only(self):
        """Test that whitespace-only string is rejected."""
        self.assertFalse(validate_link_url("   "))
    
    def test_non_string_input(self):
        """Test that non-string input is rejected."""
        self.assertFalse(validate_link_url(123))
        self.assertFalse(validate_link_url({"url": "https://example.com"}))
    
    def test_url_with_whitespace(self):
        """Test URL with leading/trailing whitespace."""
        self.assertTrue(validate_link_url("  https://example.com  "))
    
    def test_invalid_scheme_only(self):
        """Test that scheme without netloc is rejected."""
        self.assertFalse(validate_link_url("https://"))


class TestCheckLinkAccessibility(unittest.TestCase):
    """Test cases for check_link_accessibility function."""
    
    @patch('post_to_threads.requests.head')
    def test_accessible_link_200(self, mock_head):
        """Test that link with 200 status is considered accessible."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_head.return_value = mock_response
        
        result = check_link_accessibility("https://example.com")
        self.assertTrue(result)
        mock_head.assert_called_once()
    
    @patch('post_to_threads.requests.head')
    def test_accessible_link_301_redirect(self, mock_head):
        """Test that link with 301 redirect is considered accessible."""
        mock_response = MagicMock()
        mock_response.status_code = 301
        mock_head.return_value = mock_response
        
        result = check_link_accessibility("https://example.com")
        self.assertTrue(result)
    
    @patch('post_to_threads.requests.head')
    def test_inaccessible_link_404(self, mock_head):
        """Test that link with 404 status is not accessible."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_head.return_value = mock_response
        
        result = check_link_accessibility("https://example.com")
        self.assertFalse(result)
    
    @patch('post_to_threads.requests.head')
    def test_inaccessible_link_500(self, mock_head):
        """Test that link with 500 status is not accessible."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_head.return_value = mock_response
        
        result = check_link_accessibility("https://example.com")
        self.assertFalse(result)
    
    @patch('post_to_threads.requests.head')
    def test_timeout_during_check(self, mock_head):
        """Test that timeout during accessibility check returns False."""
        mock_head.side_effect = requests.Timeout("Connection timed out")
        
        result = check_link_accessibility("https://example.com")
        self.assertFalse(result)
    
    @patch('post_to_threads.requests.head')
    def test_connection_error_during_check(self, mock_head):
        """Test that connection error during check returns False."""
        mock_head.side_effect = requests.ConnectionError("Connection failed")
        
        result = check_link_accessibility("https://example.com")
        self.assertFalse(result)
    
    def test_invalid_url_format(self):
        """Test that invalid URL format returns False."""
        result = check_link_accessibility("not a valid url")
        self.assertFalse(result)
    
    @patch('post_to_threads.requests.head')
    def test_custom_timeout(self, mock_head):
        """Test that custom timeout is applied."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_head.return_value = mock_response
        
        check_link_accessibility("https://example.com", timeout=10)
        
        # Verify timeout was passed to requests.head
        call_kwargs = mock_head.call_args.kwargs
        self.assertEqual(call_kwargs.get('timeout'), 10)


class TestThreadsAPICreateMediaContainer(unittest.TestCase):
    """Test cases for ThreadsAPI.create_media_container method."""
    
    @patch('post_to_threads.requests.post')
    def test_create_container_with_text_and_link(self, mock_post):
        """Test creating media container with text and link attachment."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": "12345"}
        mock_post.return_value = mock_response
        
        api = ThreadsAPI("test_token")
        result = api.create_media_container(
            user_id="user123",
            text="Test post",
            link_attachment="https://example.com"
        )
        
        self.assertEqual(result, "12345")
        
        # Verify that link_attachment was sent as JSON object
        call_args = mock_post.call_args
        data = call_args.kwargs.get('data') if call_args.kwargs else call_args[0][1]
        
        # Note: requests library will convert dict to form data, but we sent it as dict
        # Check that it's a dict (before requests converts it)
        self.assertIsInstance(data, dict)
    
    @patch('post_to_threads.requests.post')
    def test_create_container_with_image(self, mock_post):
        """Test creating media container with image URL."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": "12345"}
        mock_post.return_value = mock_response
        
        api = ThreadsAPI("test_token")
        result = api.create_media_container(
            user_id="user123",
            text="Test post",
            media_url="https://example.com/image.jpg"
        )
        
        self.assertEqual(result, "12345")
        
        # Verify media_type was set to IMAGE
        call_args = mock_post.call_args
        data = call_args.kwargs.get('data') if call_args.kwargs else call_args[0][1]
        self.assertEqual(data.get('media_type'), 'IMAGE')


class TestThreadsAPIPublishMediaRetry(unittest.TestCase):
    """Test cases for ThreadsAPI.publish_media retry logic."""
    
    @patch('post_to_threads.requests.post')
    @patch('post_to_threads.time.sleep')
    def test_publish_success_first_attempt(self, mock_sleep, mock_post):
        """Test publish succeeds on first attempt."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": "thread123"}
        mock_post.return_value = mock_response
        
        api = ThreadsAPI("test_token")
        result = api.publish_media(user_id="user123", creation_id="create456")
        
        self.assertEqual(result, "thread123")
        self.assertEqual(mock_post.call_count, 1)
        mock_sleep.assert_not_called()
    
    @patch('post_to_threads.requests.post')
    @patch('post_to_threads.time.sleep')
    def test_publish_retries_on_transient_error(self, mock_sleep, mock_post):
        """Test publish retries on transient error (is_transient=true)."""
        # First call: transient error
        # Second call: success
        mock_response_error = MagicMock()
        mock_response_error.status_code = 400
        mock_response_error.json.return_value = {
            "error": {
                "message": "Fatal",
                "is_transient": True,
                "error_user_msg": "Temporary issue"
            }
        }
        mock_response_error.raise_for_status.side_effect = requests.HTTPError("400 Error")
        
        mock_response_success = MagicMock()
        mock_response_success.status_code = 200
        mock_response_success.json.return_value = {"id": "thread123"}
        
        mock_post.side_effect = [mock_response_error, mock_response_success]
        
        api = ThreadsAPI("test_token")
        result = api.publish_media(user_id="user123", creation_id="create456")
        
        self.assertEqual(result, "thread123")
        self.assertEqual(mock_post.call_count, 2)
        self.assertEqual(mock_sleep.call_count, 1)
        # Verify exponential backoff: 2 * (2^0) = 2
        mock_sleep.assert_called_with(2)
    
    @patch('post_to_threads.requests.post')
    @patch('post_to_threads.time.sleep')
    def test_publish_retries_on_server_error_503(self, mock_sleep, mock_post):
        """Test publish retries on server error (503)."""
        mock_response_error = MagicMock()
        mock_response_error.status_code = 503
        mock_response_error.json.return_value = {
            "error": {"is_transient": False}
        }
        mock_response_error.raise_for_status.side_effect = requests.HTTPError("503 Error")
        
        mock_response_success = MagicMock()
        mock_response_success.status_code = 200
        mock_response_success.json.return_value = {"id": "thread123"}
        
        mock_post.side_effect = [mock_response_error, mock_response_success]
        
        api = ThreadsAPI("test_token")
        result = api.publish_media(user_id="user123", creation_id="create456")
        
        self.assertEqual(result, "thread123")
        self.assertEqual(mock_post.call_count, 2)
    
    @patch('post_to_threads.requests.post')
    @patch('post_to_threads.time.sleep')
    def test_publish_fails_on_non_transient_error(self, mock_sleep, mock_post):
        """Test publish fails immediately on non-transient error."""
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {
            "error": {
                "message": "Invalid Link Attachment",
                "is_transient": False,
                "error_user_msg": "The post has an invalid link."
            }
        }
        mock_response.text = '{"error": {"is_transient": false}}'
        mock_response.raise_for_status.side_effect = requests.HTTPError("400 Error")
        mock_post.return_value = mock_response
        
        api = ThreadsAPI("test_token")
        
        with self.assertRaises(requests.HTTPError):
            api.publish_media(user_id="user123", creation_id="create456")
        
        self.assertEqual(mock_post.call_count, 1)
        mock_sleep.assert_not_called()
    
    @patch('post_to_threads.requests.post')
    @patch('post_to_threads.time.sleep')
    def test_publish_max_retries_exhausted(self, mock_sleep, mock_post):
        """Test publish fails after exhausting max retries."""
        mock_response = MagicMock()
        mock_response.status_code = 503
        mock_response.json.return_value = {
            "error": {"is_transient": False}
        }
        mock_response.text = 'error'
        mock_response.raise_for_status.side_effect = requests.HTTPError("503 Error")
        mock_post.return_value = mock_response
        
        api = ThreadsAPI("test_token")
        
        with self.assertRaises(requests.HTTPError):
            api.publish_media(user_id="user123", creation_id="create456", max_retries=3)
        
        # Should retry 3 times (attempts 0, 1, 2)
        self.assertEqual(mock_post.call_count, 3)
        # Should sleep 2 times (between attempts)
        self.assertEqual(mock_sleep.call_count, 2)


if __name__ == '__main__':
    unittest.main()
