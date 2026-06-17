#!/usr/bin/env python3
"""
Unit tests for the post_to_mastodon module.
"""

import sys
import os
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
import requests

# Add parent and common module to path
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent / 'common'))

from post_to_mastodon import (
    upload_media_to_mastodon,
    post_to_mastodon
)


class TestMastodonPosting(unittest.TestCase):
    """Test cases for post_to_mastodon.py"""

    @patch('post_to_mastodon.requests.post')
    @patch('post_to_mastodon.open', new_callable=mock_open, read_data=b"fake_media_data")
    def test_upload_media_v2_success(self, mock_file, mock_post):
        """Test successful media upload using API v2."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": "123456"}
        mock_post.return_value = mock_response

        media_id = upload_media_to_mastodon("https://mastodon.social", "fake_token", "photo.png")

        self.assertEqual(media_id, "123456")
        mock_post.assert_called_once_with(
            "https://mastodon.social/api/v2/media",
            headers={"Authorization": "Bearer fake_token"},
            files={"file": ("photo.png", mock_file.return_value)},
            timeout=30
        )

    @patch('post_to_mastodon.requests.post')
    @patch('post_to_mastodon.open', new_callable=mock_open, read_data=b"fake_media_data")
    def test_upload_media_v2_not_found_v1_fallback(self, mock_file, mock_post):
        """Test API v2 media upload 404 falling back to v1."""
        # First call (v2) returns 404, second call (v1) returns 200
        mock_resp_v2 = MagicMock()
        mock_resp_v2.status_code = 404
        
        mock_resp_v1 = MagicMock()
        mock_resp_v1.status_code = 200
        mock_resp_v1.json.return_value = {"id": "789012"}
        
        mock_post.side_effect = [mock_resp_v2, mock_resp_v1]

        media_id = upload_media_to_mastodon("https://mastodon.social", "fake_token", "photo.png")

        self.assertEqual(media_id, "789012")
        self.assertEqual(mock_post.call_count, 2)
        mock_post.assert_any_call(
            "https://mastodon.social/api/v2/media",
            headers={"Authorization": "Bearer fake_token"},
            files={"file": ("photo.png", mock_file.return_value)},
            timeout=30
        )
        mock_post.assert_any_call(
            "https://mastodon.social/api/v1/media",
            headers={"Authorization": "Bearer fake_token"},
            files={"file": ("photo.png", mock_file.return_value)},
            timeout=30
        )

    @patch('post_to_mastodon.requests.post')
    @patch('post_to_mastodon.get_required_env_var')
    @patch('post_to_mastodon.get_optional_env_var')
    @patch('post_to_mastodon.parse_media_files')
    @patch('post_to_mastodon.process_templated_contents')
    @patch('post_to_mastodon.validate_post_content')
    def test_post_to_mastodon_immediate_success(self, mock_validate, mock_template, mock_parse_media, mock_get_opt, mock_get_req, mock_post):
        """Test posting text content immediately."""
        mock_get_req.side_effect = lambda key: {
            "MASTODON_SERVER": "mastodon.social",
            "MASTODON_ACCESS_TOKEN": "fake_token",
            "POST_CONTENT": "Hello from unit test!"
        }[key]
        
        mock_get_opt.side_effect = lambda key, default="": {
            "LOG_LEVEL": "INFO",
            "POST_LINK": "https://tellstory.net",
            "MEDIA_FILES": "",
            "MAX_DOWNLOAD_SIZE_MB": "5",
            "SCHEDULED_PUBLISH_TIME": "",
            "DRY_RUN": "false"
        }.get(key, default)

        mock_template.return_value = ("Hello from unit test!", "https://tellstory.net")
        mock_validate.return_value = True
        mock_parse_media.return_value = []

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "11111",
            "url": "https://mastodon.social/@test_user/11111"
        }
        mock_post.return_value = mock_response

        # Execute
        with patch.dict(os.environ, {}, clear=True):
            post_to_mastodon()

        # Check that server URL was normalized and link was appended to content
        mock_post.assert_called_once_with(
            "https://mastodon.social/api/v1/statuses",
            json={"status": "Hello from unit test!\n\nhttps://tellstory.net"},
            headers={
                "Authorization": "Bearer fake_token",
                "Content-Type": "application/json"
            },
            timeout=30
        )

    @patch('post_to_mastodon.requests.post')
    @patch('post_to_mastodon.upload_media_to_mastodon')
    @patch('post_to_mastodon.get_required_env_var')
    @patch('post_to_mastodon.get_optional_env_var')
    @patch('post_to_mastodon.parse_media_files')
    @patch('post_to_mastodon.process_templated_contents')
    @patch('post_to_mastodon.validate_post_content')
    def test_post_to_mastodon_with_media_and_scheduling(self, mock_validate, mock_template, mock_parse_media, mock_get_opt, mock_get_req, mock_upload, mock_post):
        """Test posting with media attachment and scheduled publishing."""
        mock_get_req.side_effect = lambda key: {
            "MASTODON_SERVER": "me.dm",
            "MASTODON_ACCESS_TOKEN": "fake_token",
            "POST_CONTENT": "Dynamic content"
        }[key]
        
        mock_get_opt.side_effect = lambda key, default="": {
            "LOG_LEVEL": "DEBUG",
            "POST_LINK": "",
            "MEDIA_FILES": "image.jpg",
            "MAX_DOWNLOAD_SIZE_MB": "5",
            "SCHEDULED_PUBLISH_TIME": "+1d",
            "DRY_RUN": "false"
        }.get(key, default)

        mock_template.return_value = ("Dynamic content", "")
        mock_validate.return_value = True
        mock_parse_media.return_value = ["image.jpg"]
        mock_upload.return_value = "media_999"

        # Mock scheduling calculation (returns static ISO format string)
        with patch('post_to_mastodon.parse_scheduled_time', return_value="2026-06-18T12:00:00Z"):
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "id": "22222",
                "scheduled_at": "2026-06-18T12:00:00Z"
            }
            mock_post.return_value = mock_response

            # Execute
            post_to_mastodon()

        mock_upload.assert_called_once_with("https://me.dm", "fake_token", "image.jpg")
        mock_post.assert_called_once_with(
            "https://me.dm/api/v1/statuses",
            json={
                "status": "Dynamic content",
                "media_ids": ["media_999"],
                "scheduled_at": "2026-06-18T12:00:00Z"
            },
            headers={
                "Authorization": "Bearer fake_token",
                "Content-Type": "application/json"
            },
            timeout=30
        )


if __name__ == "__main__":
    unittest.main()
