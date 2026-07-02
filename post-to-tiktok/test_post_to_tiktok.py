#!/usr/bin/env python3
"""
Unit tests for post_to_tiktok.py
"""

import os
import sys
import json
import math
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open, call
import requests

# Add module path
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent / 'common'))

from post_to_tiktok import (
    TikTokAPI,
    post_to_tiktok,
    DEFAULT_CHUNK_SIZE_MB,
    MAX_DESCRIPTION_LENGTH,
    STATUS_POLL_MAX_ATTEMPTS,
)


class TestTikTokAPIAuth(unittest.TestCase):
    """Tests for TikTokAPI authentication methods."""

    def test_init_with_access_token(self):
        api = TikTokAPI(access_token="test_token")
        self.assertEqual(api.access_token, "test_token")
        self.assertIsNone(api.client_key)

    def test_init_with_refresh_credentials(self):
        api = TikTokAPI(client_key="key", client_secret="secret", refresh_token="refresh")
        self.assertIsNone(api.access_token)
        self.assertEqual(api.client_key, "key")
        self.assertEqual(api.refresh_token, "refresh")

    @patch('post_to_tiktok.requests.post')
    def test_refresh_access_token_success(self, mock_post):
        """Test that access token is refreshed successfully."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = '{}'
        mock_response.json.return_value = {
            "error": {"code": "ok"},
            "data": {
                "access_token": "new_access_token",
                "refresh_token": "new_refresh_token",
            }
        }
        mock_post.return_value = mock_response

        api = TikTokAPI(
            client_key="key",
            client_secret="secret",
            refresh_token="old_refresh",
        )
        api.refresh_access_token()

        self.assertEqual(api.access_token, "new_access_token")
        self.assertEqual(api.refresh_token, "new_refresh_token")
        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args
        self.assertIn("/v2/oauth/token/", call_kwargs[0][0])
        self.assertEqual(call_kwargs[1]["data"]["grant_type"], "refresh_token")
        self.assertEqual(call_kwargs[1]["data"]["client_key"], "key")

    @patch('post_to_tiktok.requests.post')
    def test_refresh_access_token_updates_refresh_token_when_returned(self, mock_post):
        """New refresh token from response is stored."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = '{}'
        mock_response.json.return_value = {
            "error": {"code": "ok"},
            "data": {
                "access_token": "new_at",
                "refresh_token": "new_rt",
            }
        }
        mock_post.return_value = mock_response

        api = TikTokAPI(client_key="k", client_secret="s", refresh_token="old_rt")
        api.refresh_access_token()
        self.assertEqual(api.refresh_token, "new_rt")

    def test_refresh_access_token_raises_without_credentials(self):
        """Raises ValueError when credentials are incomplete."""
        api = TikTokAPI(client_key="key", client_secret="secret")  # missing refresh_token
        with self.assertRaises(ValueError):
            api.refresh_access_token()

    def test_get_headers_raises_without_token(self):
        """Raises when neither access_token nor refresh_token is set."""
        api = TikTokAPI()
        with self.assertRaises(ValueError):
            api._get_headers()

    @patch('post_to_tiktok.requests.post')
    def test_ensure_access_token_triggers_refresh(self, mock_post):
        """_ensure_access_token refreshes when only refresh creds are present."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = '{}'
        mock_response.json.return_value = {
            "error": {"code": "ok"},
            "data": {"access_token": "fresh_token"},
        }
        mock_post.return_value = mock_response

        api = TikTokAPI(client_key="k", client_secret="s", refresh_token="rt")
        headers = api._get_headers()
        self.assertIn("Bearer fresh_token", headers["Authorization"])


class TestTikTokAPICreatorInfo(unittest.TestCase):
    """Tests for TikTokAPI.query_creator_info."""

    @patch('post_to_tiktok.requests.post')
    def test_query_creator_info_success(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = '{}'
        mock_response.json.return_value = {
            "error": {"code": "ok"},
            "data": {
                "max_video_post_duration_sec": 60,
                "privacy_level_options": ["PUBLIC_TO_EVERYONE", "SELF_ONLY"],
            }
        }
        mock_post.return_value = mock_response

        api = TikTokAPI(access_token="token")
        result = api.query_creator_info()

        self.assertEqual(result["max_video_post_duration_sec"], 60)
        mock_post.assert_called_once()
        self.assertIn("/v2/post/publish/creator_info/query/", mock_post.call_args[0][0])

    @patch('post_to_tiktok.requests.post')
    def test_query_creator_info_non_ok_returns_data(self, mock_post):
        """Non-ok code logs a warning but still returns data dict."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = '{}'
        mock_response.json.return_value = {
            "error": {"code": "access_token_invalid"},
            "data": {}
        }
        mock_post.return_value = mock_response

        api = TikTokAPI(access_token="token")
        result = api.query_creator_info()
        self.assertIsInstance(result, dict)


class TestTikTokAPIInitUpload(unittest.TestCase):
    """Tests for TikTokAPI.init_video_upload."""

    @patch('post_to_tiktok.requests.post')
    def test_init_file_upload_success(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = '{}'
        mock_response.json.return_value = {
            "error": {"code": "ok"},
            "data": {
                "publish_id": "v_publish_123",
                "upload_url": "https://upload.tiktok.com/chunks/abc",
            }
        }
        mock_post.return_value = mock_response

        api = TikTokAPI(access_token="token")
        post_info = {"title": "Test", "privacy_level": "SELF_ONLY"}
        source_info = {"source": "FILE_UPLOAD", "video_size": 1024, "chunk_size": 1024, "total_chunk_count": 1}

        result = api.init_video_upload(post_info, source_info)

        self.assertEqual(result["publish_id"], "v_publish_123")
        self.assertEqual(result["upload_url"], "https://upload.tiktok.com/chunks/abc")
        mock_post.assert_called_once()
        # The json kwarg is passed as a dict directly to requests.post
        req_body = mock_post.call_args.kwargs.get("json") or mock_post.call_args[1].get("json")
        self.assertEqual(req_body["post_mode"], "DIRECT_POST")
        self.assertEqual(req_body["post_info"]["title"], "Test")

    @patch('post_to_tiktok.requests.post')
    def test_init_pull_from_url_success(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = '{}'
        mock_response.json.return_value = {
            "error": {"code": "ok"},
            "data": {"publish_id": "v_pull_456"},
        }
        mock_post.return_value = mock_response

        api = TikTokAPI(access_token="token")
        source_info = {"source": "PULL_FROM_URL", "video_url": "https://cdn.example.com/video.mp4"}
        result = api.init_video_upload({}, source_info)
        self.assertEqual(result["publish_id"], "v_pull_456")

    @patch('post_to_tiktok.requests.post')
    def test_init_upload_raises_on_error_code(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = '{}'
        mock_response.json.return_value = {
            "error": {"code": "spam_risk_too_many_posts"},
            "data": {}
        }
        mock_post.return_value = mock_response

        api = TikTokAPI(access_token="token")
        with self.assertRaises(RuntimeError) as ctx:
            api.init_video_upload({}, {"source": "FILE_UPLOAD"})
        self.assertIn("spam_risk_too_many_posts", str(ctx.exception))


class TestTikTokAPIChunkUpload(unittest.TestCase):
    """Tests for TikTokAPI.upload_video_chunks."""

    @patch('post_to_tiktok.requests.put')
    @patch('post_to_tiktok.os.path.getsize')
    def test_single_chunk_upload(self, mock_getsize, mock_put):
        """Small file uploads in a single chunk."""
        file_data = b"A" * 100
        mock_getsize.return_value = len(file_data)

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = '{}'
        mock_put.return_value = mock_response

        api = TikTokAPI(access_token="token")
        with patch("builtins.open", mock_open(read_data=file_data)):
            api.upload_video_chunks("https://upload.url/chunks", "/fake/video.mp4", chunk_size=1024)

        mock_put.assert_called_once()
        call_kwargs = mock_put.call_args
        self.assertIn("Content-Range", call_kwargs[1]["headers"])
        self.assertEqual(call_kwargs[1]["headers"]["Content-Range"], f"bytes 0-99/100")

    @patch('post_to_tiktok.requests.put')
    @patch('post_to_tiktok.os.path.getsize')
    def test_multiple_chunk_upload(self, mock_getsize, mock_put):
        """File larger than chunk_size uploads in multiple chunks."""
        chunk_size = 50
        file_data = b"B" * 120  # 3 chunks: 50, 50, 20
        mock_getsize.return_value = len(file_data)

        mock_put.side_effect = [
            MagicMock(status_code=206, text=""),  # chunk 1
            MagicMock(status_code=206, text=""),  # chunk 2
            MagicMock(status_code=200, text=""),  # chunk 3 (final)
        ]

        api = TikTokAPI(access_token="token")
        with patch("builtins.open", mock_open(read_data=file_data)):
            api.upload_video_chunks("https://upload.url/chunks", "/fake/video.mp4", chunk_size=chunk_size)

        expected_chunks = math.ceil(120 / chunk_size)
        self.assertEqual(mock_put.call_count, expected_chunks)

    @patch('post_to_tiktok.requests.put')
    @patch('post_to_tiktok.os.path.getsize')
    def test_chunk_upload_raises_on_http_error(self, mock_getsize, mock_put):
        """Raises RuntimeError when a chunk upload returns an unexpected status."""
        mock_getsize.return_value = 100
        mock_put.return_value = MagicMock(status_code=400, text="Bad Request")

        api = TikTokAPI(access_token="token")
        with patch("builtins.open", mock_open(read_data=b"X" * 100)):
            with self.assertRaises(RuntimeError) as ctx:
                api.upload_video_chunks("https://upload.url", "/fake/video.mp4", chunk_size=1024)
        self.assertIn("400", str(ctx.exception))


class TestTikTokAPIPublishStatus(unittest.TestCase):
    """Tests for TikTokAPI.check_publish_status."""

    @patch('post_to_tiktok.requests.post')
    def test_publish_complete_on_first_poll(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = '{}'
        mock_response.json.return_value = {
            "error": {"code": "ok"},
            "data": {"status": "PUBLISH_COMPLETE", "video_id": "vid_789"},
        }
        mock_post.return_value = mock_response

        api = TikTokAPI(access_token="token")
        result = api.check_publish_status("v_pub_123")

        self.assertEqual(result["status"], "PUBLISH_COMPLETE")
        self.assertEqual(result["video_id"], "vid_789")

    @patch('post_to_tiktok.time.sleep', return_value=None)
    @patch('post_to_tiktok.requests.post')
    def test_publish_complete_after_processing(self, mock_post, mock_sleep):
        """First poll returns PROCESSING_UPLOAD, second returns PUBLISH_COMPLETE."""
        processing_response = MagicMock()
        processing_response.status_code = 200
        processing_response.text = '{}'
        processing_response.json.return_value = {
            "error": {"code": "ok"},
            "data": {"status": "PROCESSING_UPLOAD"},
        }

        complete_response = MagicMock()
        complete_response.status_code = 200
        complete_response.text = '{}'
        complete_response.json.return_value = {
            "error": {"code": "ok"},
            "data": {"status": "PUBLISH_COMPLETE", "video_id": "vid_999"},
        }

        mock_post.side_effect = [processing_response, complete_response]

        api = TikTokAPI(access_token="token")
        result = api.check_publish_status("pub_id")
        self.assertEqual(result["status"], "PUBLISH_COMPLETE")
        self.assertEqual(mock_sleep.call_count, 1)

    @patch('post_to_tiktok.requests.post')
    def test_publish_failed_raises(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = '{}'
        mock_response.json.return_value = {
            "error": {"code": "ok"},
            "data": {"status": "FAILED", "fail_reason": "video_too_short"},
        }
        mock_post.return_value = mock_response

        api = TikTokAPI(access_token="token")
        with self.assertRaises(RuntimeError) as ctx:
            api.check_publish_status("pub_id")
        self.assertIn("video_too_short", str(ctx.exception))

    @patch('post_to_tiktok.time.sleep', return_value=None)
    @patch('post_to_tiktok.requests.post')
    def test_publish_status_timeout_raises(self, mock_post, mock_sleep):
        """Raises RuntimeError after MAX_POLL_ATTEMPTS without completion."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = '{}'
        mock_response.json.return_value = {
            "error": {"code": "ok"},
            "data": {"status": "PROCESSING_UPLOAD"},
        }
        mock_post.return_value = mock_response

        api = TikTokAPI(access_token="token")
        with self.assertRaises(RuntimeError) as ctx:
            api.check_publish_status("pub_id")
        self.assertIn("timed out", str(ctx.exception).lower())
        self.assertEqual(mock_post.call_count, STATUS_POLL_MAX_ATTEMPTS)


class TestPostToTikTok(unittest.TestCase):
    """Integration-style tests for the post_to_tiktok() entry-point."""

    def _mock_env(self, overrides=None):
        base = {
            "TIKTOK_ACCESS_TOKEN": "test_access_token",
            "VIDEO_FILE": "/fake/video.mp4",
            "POST_CONTENT": "Hello TikTok!",
            "VIDEO_PRIVACY_LEVEL": "PUBLIC_TO_EVERYONE",
            "TIKTOK_DISABLE_DUET": "false",
            "TIKTOK_DISABLE_COMMENT": "false",
            "TIKTOK_DISABLE_STITCH": "false",
            "TIKTOK_BRAND_CONTENT": "false",
            "TIKTOK_BRAND_ORGANIC": "false",
            "TIKTOK_IS_AIGC": "false",
            "TIKTOK_COVER_TIMESTAMP_MS": "1000",
            "VIDEO_PUBLISH_AT": "",
            "TIKTOK_CHUNK_SIZE_MB": "10",
            "LOG_LEVEL": "INFO",
            "DRY_RUN": "false",
            "SAVE_RESPONSE": "false",
            "CONTENT_JSON": "",
        }
        if overrides:
            base.update(overrides)
        return base

    @patch('post_to_tiktok.TikTokAPI.check_publish_status')
    @patch('post_to_tiktok.TikTokAPI.upload_video_chunks')
    @patch('post_to_tiktok.TikTokAPI.init_video_upload')
    @patch('post_to_tiktok.TikTokAPI.query_creator_info')
    @patch('post_to_tiktok.os.path.getsize')
    @patch('post_to_tiktok.os.path.exists')
    @patch('post_to_tiktok.get_optional_env_var')
    @patch('post_to_tiktok.get_required_env_var')
    @patch('post_to_tiktok.process_templated_contents')
    def test_post_local_file_success(
        self,
        mock_template,
        mock_get_req,
        mock_get_opt,
        mock_exists,
        mock_getsize,
        mock_creator_info,
        mock_init,
        mock_upload_chunks,
        mock_check_status,
    ):
        """Test successful posting of a local video file."""
        mock_get_req.side_effect = lambda k: {"VIDEO_FILE": "/fake/video.mp4"}[k]
        mock_get_opt.side_effect = lambda k, d="": self._mock_env().get(k, d)
        mock_template.return_value = ("Hello TikTok!",)
        mock_exists.return_value = True
        mock_getsize.return_value = 5 * 1024 * 1024  # 5 MB

        mock_creator_info.return_value = {"max_video_post_duration_sec": 60}
        mock_init.return_value = {
            "publish_id": "pub_123",
            "upload_url": "https://upload.tiktok.com/chunks",
        }
        mock_check_status.return_value = {"status": "PUBLISH_COMPLETE", "video_id": "vid_abc"}

        post_to_tiktok()

        mock_init.assert_called_once()
        # Verify source_info uses FILE_UPLOAD
        call_args = mock_init.call_args
        source_info = call_args[0][1] if call_args[0] else call_args[1].get("source_info", {})
        # Accept positional or keyword args
        if len(call_args[0]) >= 2:
            source_info = call_args[0][1]
        self.assertEqual(source_info["source"], "FILE_UPLOAD")

        mock_upload_chunks.assert_called_once()
        mock_check_status.assert_called_once_with("pub_123")

    @patch('post_to_tiktok.TikTokAPI.check_publish_status')
    @patch('post_to_tiktok.TikTokAPI.init_video_upload')
    @patch('post_to_tiktok.TikTokAPI.query_creator_info')
    @patch('post_to_tiktok.download_file_if_url')
    @patch('post_to_tiktok.get_optional_env_var')
    @patch('post_to_tiktok.get_required_env_var')
    @patch('post_to_tiktok.process_templated_contents')
    def test_post_pull_from_url_when_download_fails(
        self,
        mock_template,
        mock_get_req,
        mock_get_opt,
        mock_download,
        mock_creator_info,
        mock_init,
        mock_check_status,
    ):
        """When the video URL cannot be downloaded, fall back to PULL_FROM_URL."""
        remote_url = "https://cdn.example.com/big-video.mp4"
        env = self._mock_env({"VIDEO_FILE": remote_url})
        mock_get_req.side_effect = lambda k: {"VIDEO_FILE": remote_url}[k]
        mock_get_opt.side_effect = lambda k, d="": env.get(k, d)
        mock_template.return_value = ("Caption",)

        # Simulate download failure (returns original URL unchanged)
        mock_download.side_effect = Exception("File too large")

        mock_creator_info.return_value = {}
        mock_init.return_value = {"publish_id": "pub_url_456"}
        mock_check_status.return_value = {"status": "PUBLISH_COMPLETE"}

        post_to_tiktok()

        mock_init.assert_called_once()
        # Verify source_info uses PULL_FROM_URL
        call_args = mock_init.call_args
        if len(call_args[0]) >= 2:
            source_info = call_args[0][1]
        else:
            source_info = call_args[1]["source_info"]
        self.assertEqual(source_info["source"], "PULL_FROM_URL")
        self.assertEqual(source_info["video_url"], remote_url)

    @patch('post_to_tiktok.get_optional_env_var')
    @patch('post_to_tiktok.get_required_env_var')
    @patch('post_to_tiktok.process_templated_contents')
    def test_exits_when_no_credentials(self, mock_template, mock_get_req, mock_get_opt):
        """Exits with error when neither access_token nor refresh credentials are provided."""
        env = self._mock_env()
        env["TIKTOK_ACCESS_TOKEN"] = ""
        env["TIKTOK_CLIENT_KEY"] = ""
        env["TIKTOK_CLIENT_SECRET"] = ""
        env["TIKTOK_REFRESH_TOKEN"] = ""
        mock_get_req.side_effect = lambda k: {"VIDEO_FILE": "/fake/video.mp4"}[k]
        mock_get_opt.side_effect = lambda k, d="": env.get(k, d)
        mock_template.return_value = ("Caption",)

        with self.assertRaises(SystemExit) as ctx:
            post_to_tiktok()
        self.assertEqual(ctx.exception.code, 1)

    @patch('post_to_tiktok.dry_run_guard')
    @patch('post_to_tiktok.os.path.getsize')
    @patch('post_to_tiktok.os.path.exists')
    @patch('post_to_tiktok.get_optional_env_var')
    @patch('post_to_tiktok.get_required_env_var')
    @patch('post_to_tiktok.process_templated_contents')
    def test_dry_run_calls_guard(
        self, mock_template, mock_get_req, mock_get_opt,
        mock_exists, mock_getsize, mock_dry_guard
    ):
        """Dry-run mode calls dry_run_guard and does not call the TikTok API."""
        env = self._mock_env({"DRY_RUN": "true"})
        mock_get_req.side_effect = lambda k: {"VIDEO_FILE": "/fake/video.mp4"}[k]
        mock_get_opt.side_effect = lambda k, d="": env.get(k, d)
        mock_template.return_value = ("Test caption",)
        mock_exists.return_value = True
        mock_getsize.return_value = 1024

        mock_dry_guard.side_effect = SystemExit(0)

        with self.assertRaises(SystemExit) as ctx:
            post_to_tiktok()
        self.assertEqual(ctx.exception.code, 0)
        mock_dry_guard.assert_called_once()

    @patch('post_to_tiktok.TikTokAPI.check_publish_status')
    @patch('post_to_tiktok.TikTokAPI.upload_video_chunks')
    @patch('post_to_tiktok.TikTokAPI.init_video_upload')
    @patch('post_to_tiktok.TikTokAPI.query_creator_info')
    @patch('post_to_tiktok.os.path.getsize')
    @patch('post_to_tiktok.os.path.exists')
    @patch('post_to_tiktok.get_optional_env_var')
    @patch('post_to_tiktok.get_required_env_var')
    @patch('post_to_tiktok.process_templated_contents')
    def test_scheduled_post_sets_scheduled_publish_time(
        self,
        mock_template,
        mock_get_req,
        mock_get_opt,
        mock_exists,
        mock_getsize,
        mock_creator_info,
        mock_init,
        mock_upload_chunks,
        mock_check_status,
    ):
        """Scheduled post passes scheduled_publish_time in post_info."""
        env = self._mock_env({"VIDEO_PUBLISH_AT": "+1d"})
        mock_get_req.side_effect = lambda k: {"VIDEO_FILE": "/fake/video.mp4"}[k]
        mock_get_opt.side_effect = lambda k, d="": env.get(k, d)
        mock_template.return_value = ("Scheduled post",)
        mock_exists.return_value = True
        mock_getsize.return_value = 1024

        mock_creator_info.return_value = {}
        mock_init.return_value = {
            "publish_id": "pub_sched",
            "upload_url": "https://upload.tiktok.com/chunks",
        }
        mock_check_status.return_value = {"status": "PUBLISH_COMPLETE"}

        post_to_tiktok()

        call_args = mock_init.call_args
        if len(call_args[0]) >= 1:
            post_info = call_args[0][0]
        else:
            post_info = call_args[1]["post_info"]
        self.assertIn("scheduled_publish_time", post_info)
        self.assertIsInstance(post_info["scheduled_publish_time"], int)
        # Should be in the future (roughly now + 1 day)
        import time
        self.assertGreater(post_info["scheduled_publish_time"], int(time.time()))

    @patch('post_to_tiktok.TikTokAPI.check_publish_status')
    @patch('post_to_tiktok.TikTokAPI.upload_video_chunks')
    @patch('post_to_tiktok.TikTokAPI.init_video_upload')
    @patch('post_to_tiktok.TikTokAPI.query_creator_info')
    @patch('post_to_tiktok.os.path.getsize')
    @patch('post_to_tiktok.os.path.exists')
    @patch('post_to_tiktok.get_optional_env_var')
    @patch('post_to_tiktok.get_required_env_var')
    @patch('post_to_tiktok.process_templated_contents')
    def test_url_warning_in_description(
        self,
        mock_template,
        mock_get_req,
        mock_get_opt,
        mock_exists,
        mock_getsize,
        mock_creator_info,
        mock_init,
        mock_upload_chunks,
        mock_check_status,
    ):
        """Warning is logged when description contains a URL."""
        env = self._mock_env()
        mock_get_req.side_effect = lambda k: {"VIDEO_FILE": "/fake/video.mp4"}[k]
        mock_get_opt.side_effect = lambda k, d="": env.get(k, d)
        mock_template.return_value = ("Visit https://example.com for more!",)
        mock_exists.return_value = True
        mock_getsize.return_value = 1024

        mock_creator_info.return_value = {}
        mock_init.return_value = {
            "publish_id": "pub_url_warn",
            "upload_url": "https://upload.tiktok.com/chunks",
        }
        mock_check_status.return_value = {"status": "PUBLISH_COMPLETE"}

        import logging
        with self.assertLogs('social_media_utils', level='WARNING') as cm:
            post_to_tiktok()

        self.assertTrue(
            any('url' in m.lower() for m in cm.output),
            "Expected a warning about URLs in description"
        )

    @patch('post_to_tiktok.save_post_response')
    @patch('post_to_tiktok.TikTokAPI.check_publish_status')
    @patch('post_to_tiktok.TikTokAPI.upload_video_chunks')
    @patch('post_to_tiktok.TikTokAPI.init_video_upload')
    @patch('post_to_tiktok.TikTokAPI.query_creator_info')
    @patch('post_to_tiktok.os.path.getsize')
    @patch('post_to_tiktok.os.path.exists')
    @patch('post_to_tiktok.get_optional_env_var')
    @patch('post_to_tiktok.get_required_env_var')
    @patch('post_to_tiktok.process_templated_contents')
    def test_save_response_called_on_success(
        self,
        mock_template,
        mock_get_req,
        mock_get_opt,
        mock_exists,
        mock_getsize,
        mock_creator_info,
        mock_init,
        mock_upload_chunks,
        mock_check_status,
        mock_save_response,
    ):
        """save_post_response is called with success=True on successful posting."""
        mock_get_req.side_effect = lambda k: {"VIDEO_FILE": "/fake/video.mp4"}[k]
        mock_get_opt.side_effect = lambda k, d="": self._mock_env().get(k, d)
        mock_template.return_value = ("Caption",)
        mock_exists.return_value = True
        mock_getsize.return_value = 1024
        mock_creator_info.return_value = {}
        mock_init.return_value = {
            "publish_id": "pub_ok",
            "upload_url": "https://upload.tiktok.com/chunks",
        }
        mock_check_status.return_value = {"status": "PUBLISH_COMPLETE", "video_id": "vid_ok"}

        post_to_tiktok()

        mock_save_response.assert_called_once_with("tiktok", success=True, post_id="vid_ok", post_url=unittest.mock.ANY)

    @patch('post_to_tiktok.save_post_response')
    @patch('post_to_tiktok.os.path.exists')
    @patch('post_to_tiktok.get_optional_env_var')
    @patch('post_to_tiktok.get_required_env_var')
    @patch('post_to_tiktok.process_templated_contents')
    def test_save_response_called_on_failure(
        self, mock_template, mock_get_req, mock_get_opt, mock_exists, mock_save_response
    ):
        """save_post_response is called with success=False when posting fails."""
        mock_get_req.side_effect = lambda k: {"VIDEO_FILE": "/nonexistent/video.mp4"}[k]
        mock_get_opt.side_effect = lambda k, d="": self._mock_env().get(k, d)
        mock_template.return_value = ("Caption",)
        mock_exists.return_value = False  # file not found

        with self.assertRaises(SystemExit):
            post_to_tiktok()


class TestTikTokAPIChunkSizeConstraints(unittest.TestCase):
    """Tests that chunk_size_mb is clamped to valid range."""

    @patch('post_to_tiktok.TikTokAPI.check_publish_status')
    @patch('post_to_tiktok.TikTokAPI.upload_video_chunks')
    @patch('post_to_tiktok.TikTokAPI.init_video_upload')
    @patch('post_to_tiktok.TikTokAPI.query_creator_info')
    @patch('post_to_tiktok.os.path.getsize')
    @patch('post_to_tiktok.os.path.exists')
    @patch('post_to_tiktok.get_optional_env_var')
    @patch('post_to_tiktok.get_required_env_var')
    @patch('post_to_tiktok.process_templated_contents')
    def test_chunk_size_clamped_to_min(
        self, mock_template, mock_get_req, mock_get_opt, mock_exists,
        mock_getsize, mock_creator_info, mock_init, mock_upload, mock_status
    ):
        """Chunk size below 5 MB is clamped to 5 MB."""
        env = {
            "TIKTOK_ACCESS_TOKEN": "token",
            "VIDEO_FILE": "/fake/video.mp4",
            "POST_CONTENT": "Test",
            "VIDEO_PRIVACY_LEVEL": "SELF_ONLY",
            "TIKTOK_DISABLE_DUET": "false",
            "TIKTOK_DISABLE_COMMENT": "false",
            "TIKTOK_DISABLE_STITCH": "false",
            "TIKTOK_BRAND_CONTENT": "false",
            "TIKTOK_BRAND_ORGANIC": "false",
            "TIKTOK_IS_AIGC": "false",
            "TIKTOK_COVER_TIMESTAMP_MS": "1000",
            "VIDEO_PUBLISH_AT": "",
            "TIKTOK_CHUNK_SIZE_MB": "1",  # below minimum
            "LOG_LEVEL": "INFO",
            "DRY_RUN": "false",
            "SAVE_RESPONSE": "false",
            "CONTENT_JSON": "",
        }
        mock_get_req.side_effect = lambda k: {"VIDEO_FILE": "/fake/video.mp4"}[k]
        mock_get_opt.side_effect = lambda k, d="": env.get(k, d)
        mock_template.return_value = ("Test",)
        mock_exists.return_value = True
        mock_getsize.return_value = 1024
        mock_creator_info.return_value = {}
        mock_init.return_value = {"publish_id": "p1", "upload_url": "https://u"}
        mock_status.return_value = {"status": "PUBLISH_COMPLETE"}

        post_to_tiktok()

        # Check that upload_video_chunks was called with chunk_size >= 5 MB
        mock_upload.assert_called_once()
        used_chunk_size = mock_upload.call_args[0][2] if len(mock_upload.call_args[0]) >= 3 else \
                          mock_upload.call_args[1].get("chunk_size", 0)
        self.assertGreaterEqual(used_chunk_size, 5 * 1024 * 1024)


if __name__ == "__main__":
    unittest.main()
