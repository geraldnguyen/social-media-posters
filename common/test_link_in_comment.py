"""Unit tests for link-in-comment feature (v1.33.0)."""

import io
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add common module to path
sys.path.insert(0, str(Path(__file__).parent))

import social_media_utils
from social_media_utils import dry_run_guard, get_optional_env_var


class TestDryRunGuardLinkInComment(unittest.TestCase):
    """Validate that dry_run_guard displays link-in-comment and pin info."""

    def setUp(self):
        social_media_utils._json_config_cache = None
        social_media_utils._json_config_loaded = False
        for key in ["DRY_RUN", "SAVE_RESPONSE", "LINK_IN_COMMENT", "PIN_LINK_COMMENT", "INPUT_FILE"]:
            os.environ.pop(key, None)

    def tearDown(self):
        for key in ["DRY_RUN", "SAVE_RESPONSE", "LINK_IN_COMMENT", "PIN_LINK_COMMENT", "INPUT_FILE"]:
            os.environ.pop(key, None)
        social_media_utils._json_config_cache = None
        social_media_utils._json_config_loaded = False

    def _capture_dry_run(self, request_body):
        """Run dry_run_guard with DRY_RUN=true and capture stdout."""
        os.environ["DRY_RUN"] = "true"
        captured = io.StringIO()
        with patch("sys.stdout", captured):
            with self.assertRaises(SystemExit) as cm:
                dry_run_guard("Test", "Some content", [], request_body)
        self.assertEqual(cm.exception.code, 0)
        return captured.getvalue()

    def test_link_in_comment_shown_in_dry_run(self):
        """When link_in_comment is in request_body, it appears in dry-run output."""
        output = self._capture_dry_run({
            "text": "hello",
            "link_in_comment": "https://example.com/link",
        })
        self.assertIn("LINK IN COMMENT", output)
        self.assertIn("https://example.com/link", output)

    def test_pin_link_comment_shown_when_true(self):
        """When pin_link_comment is True, the pin message appears in dry-run output."""
        output = self._capture_dry_run({
            "text": "hello",
            "link_in_comment": "https://example.com/link",
            "pin_link_comment": True,
        })
        self.assertIn("Pin: Requested", output)

    def test_pin_link_comment_not_shown_when_false(self):
        """When pin_link_comment is False, the pin message does not appear."""
        output = self._capture_dry_run({
            "text": "hello",
            "link_in_comment": "https://example.com/link",
            "pin_link_comment": False,
        })
        self.assertIn("LINK IN COMMENT", output)
        self.assertNotIn("Pin: Requested", output)

    def test_link_in_comment_not_shown_when_absent(self):
        """When link_in_comment is not in request_body, the section is absent."""
        output = self._capture_dry_run({"text": "hello"})
        self.assertNotIn("LINK IN COMMENT", output)

    def test_link_in_comment_not_shown_when_empty(self):
        """When link_in_comment is an empty string, the section is absent."""
        output = self._capture_dry_run({"text": "hello", "link_in_comment": ""})
        self.assertNotIn("LINK IN COMMENT", output)


class TestLinkInCommentEnvVar(unittest.TestCase):
    """Validate LINK_IN_COMMENT and PIN_LINK_COMMENT environment variable reading."""

    def setUp(self):
        social_media_utils._json_config_cache = None
        social_media_utils._json_config_loaded = False
        for key in ["LINK_IN_COMMENT", "PIN_LINK_COMMENT", "INPUT_FILE"]:
            os.environ.pop(key, None)

    def tearDown(self):
        for key in ["LINK_IN_COMMENT", "PIN_LINK_COMMENT", "INPUT_FILE"]:
            os.environ.pop(key, None)
        social_media_utils._json_config_cache = None
        social_media_utils._json_config_loaded = False

    def test_link_in_comment_defaults_to_empty(self):
        """LINK_IN_COMMENT returns empty string when not set."""
        value = get_optional_env_var("LINK_IN_COMMENT", "")
        self.assertEqual(value, "")

    def test_link_in_comment_reads_env_var(self):
        """LINK_IN_COMMENT returns the set value."""
        os.environ["LINK_IN_COMMENT"] = "https://example.com/my-post"
        value = get_optional_env_var("LINK_IN_COMMENT", "")
        self.assertEqual(value, "https://example.com/my-post")

    def test_pin_link_comment_defaults_to_falsy(self):
        """PIN_LINK_COMMENT is not set by default, evaluates to empty string."""
        value = get_optional_env_var("PIN_LINK_COMMENT", "")
        self.assertFalse(value.lower() in ('1', 'true', 'yes'))

    def test_pin_link_comment_truthy_values(self):
        """PIN_LINK_COMMENT is truthy when set to '1', 'true', or 'yes'."""
        for truthy in ('1', 'true', 'yes', 'True', 'TRUE', 'YES'):
            os.environ["PIN_LINK_COMMENT"] = truthy
            value = get_optional_env_var("PIN_LINK_COMMENT", "")
            self.assertTrue(value.lower() in ('1', 'true', 'yes'),
                            f"Expected '{truthy}' to be truthy")

    def test_pin_link_comment_falsy_values(self):
        """PIN_LINK_COMMENT is falsy when set to '0', 'false', or 'no'."""
        for falsy in ('0', 'false', 'no', 'False', 'FALSE'):
            os.environ["PIN_LINK_COMMENT"] = falsy
            value = get_optional_env_var("PIN_LINK_COMMENT", "")
            self.assertFalse(value.lower() in ('1', 'true', 'yes'),
                             f"Expected '{falsy}' to be falsy")


class TestThreadsAPIReplyToId(unittest.TestCase):
    """Validate that ThreadsAPI.create_media_container supports reply_to_id."""

    def setUp(self):
        # Import from post-to-threads folder
        threads_path = str(Path(__file__).parent.parent / 'post-to-threads')
        if threads_path not in sys.path:
            sys.path.insert(0, threads_path)

    def test_create_media_container_accepts_reply_to_id(self):
        """create_media_container should include reply_to_id in request data."""
        from post_to_threads import ThreadsAPI

        api = ThreadsAPI(access_token="fake_token")
        captured_data = {}

        def mock_post(url, data):
            captured_data.update(data)
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"id": "reply_container_123"}
            mock_response.raise_for_status = MagicMock()
            return mock_response

        with patch("requests.post", side_effect=mock_post):
            container_id = api.create_media_container(
                user_id="user123",
                text="https://example.com",
                reply_to_id="original_thread_456"
            )

        self.assertEqual(container_id, "reply_container_123")
        self.assertIn("reply_to_id", captured_data)
        self.assertEqual(captured_data["reply_to_id"], "original_thread_456")

    def test_create_media_container_without_reply_to_id(self):
        """create_media_container without reply_to_id should not include it in data."""
        from post_to_threads import ThreadsAPI

        api = ThreadsAPI(access_token="fake_token")
        captured_data = {}

        def mock_post(url, data):
            captured_data.update(data)
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"id": "container_789"}
            mock_response.raise_for_status = MagicMock()
            return mock_response

        with patch("requests.post", side_effect=mock_post):
            api.create_media_container(
                user_id="user123",
                text="Hello world"
            )

        self.assertNotIn("reply_to_id", captured_data)


class TestLinkedInAPIPostComment(unittest.TestCase):
    """Validate LinkedInAPI.post_comment method."""

    def setUp(self):
        linkedin_path = str(Path(__file__).parent.parent / 'post-to-linkedin')
        if linkedin_path not in sys.path:
            sys.path.insert(0, linkedin_path)

    def test_post_comment_sends_correct_request(self):
        """post_comment should POST to the correct URL with author and message."""
        from post_to_linkedin import LinkedInAPI

        api = LinkedInAPI(access_token="fake_token")
        captured_kwargs = {}

        def mock_post(url, **kwargs):
            captured_kwargs['url'] = url
            captured_kwargs.update(kwargs)
            mock_response = MagicMock()
            mock_response.status_code = 201
            mock_response.headers = {"X-RestLi-Id": "urn:li:comment:123"}
            mock_response.raise_for_status = MagicMock()
            return mock_response

        with patch("requests.post", side_effect=mock_post):
            comment_id = api.post_comment(
                author_id="urn:li:person:abc123",
                post_urn="urn:li:ugcPost:xyz456",
                comment_text="https://example.com/link"
            )

        self.assertEqual(comment_id, "urn:li:comment:123")
        self.assertIn("socialActions/urn:li:ugcPost:xyz456/comments", captured_kwargs['url'])
        body = captured_kwargs.get('json', {})
        self.assertEqual(body.get('actor'), "urn:li:person:abc123")
        self.assertEqual(body.get('message', {}).get('text'), "https://example.com/link")


class TestDailymotionAPIPostComment(unittest.TestCase):
    """Validate DailymotionAPI.post_comment method."""

    def setUp(self):
        dm_path = str(Path(__file__).parent.parent / 'post-to-dailymotion')
        if dm_path not in sys.path:
            sys.path.insert(0, dm_path)

    def test_post_comment_sends_correct_request(self):
        """post_comment should POST to /video/{video_id}/comments with message."""
        from post_to_dailymotion import DailymotionAPI

        api = DailymotionAPI(
            client_id="cid",
            client_secret="csecret",
            refresh_token="rtoken"
        )
        api.access_token = "fake_access_token"  # Skip authentication
        captured_kwargs = {}

        def mock_post(url, **kwargs):
            captured_kwargs['url'] = url
            captured_kwargs.update(kwargs)
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"id": "comment_abc"}
            mock_response.raise_for_status = MagicMock()
            return mock_response

        with patch("requests.post", side_effect=mock_post):
            comment_id = api.post_comment("video123", "https://example.com/link")

        self.assertEqual(comment_id, "comment_abc")
        self.assertIn("video/video123/comments", captured_kwargs['url'])
        self.assertEqual(captured_kwargs.get('data', {}).get('message'), "https://example.com/link")


if __name__ == "__main__":
    unittest.main()
