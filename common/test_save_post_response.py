"""Unit tests for response file persistence helpers."""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

# Add common module to path
sys.path.insert(0, str(Path(__file__).parent))

import social_media_utils
from social_media_utils import save_post_response


class TestSavePostResponse(unittest.TestCase):
    """Validate save_post_response behavior."""

    def setUp(self):
        """Create an isolated temp directory and clean env state."""
        self._old_cwd = os.getcwd()
        self._tmpdir = tempfile.TemporaryDirectory()
        os.chdir(self._tmpdir.name)

        social_media_utils._json_config_cache = None
        social_media_utils._json_config_loaded = False

        for key in ["SAVE_RESPONSE", "INPUT_FILE"]:
            os.environ.pop(key, None)

    def tearDown(self):
        """Restore working directory and clean test state."""
        os.chdir(self._old_cwd)
        self._tmpdir.cleanup()

        social_media_utils._json_config_cache = None
        social_media_utils._json_config_loaded = False

        for key in ["SAVE_RESPONSE", "INPUT_FILE"]:
            os.environ.pop(key, None)

    def test_save_post_response_enabled_writes_json_file(self):
        """When enabled, response payload is written to <social>-response.json."""
        os.environ["SAVE_RESPONSE"] = "true"

        output_file = save_post_response(
            "x",
            success=True,
            post_id="12345",
            post_url="https://x.com/i/web/status/12345",
        )

        self.assertEqual(output_file, "x-response.json")
        self.assertTrue(os.path.exists(output_file))

        with open(output_file, "r", encoding="utf-8") as f:
            payload = json.load(f)

        self.assertEqual(
            payload,
            {
                "success": True,
                "error": None,
                "post_id": "12345",
                "post_url": "https://x.com/i/web/status/12345",
            },
        )

    def test_save_post_response_disabled_does_not_write_file(self):
        """When disabled, no file is written."""
        output_file = save_post_response(
            "facebook",
            success=True,
            post_id="abc",
            post_url="https://facebook.com/abc",
        )

        self.assertIsNone(output_file)
        self.assertFalse(os.path.exists("facebook-response.json"))

    def test_save_post_response_failure_payload(self):
        """Failure payload includes error text and null identifiers."""
        os.environ["SAVE_RESPONSE"] = "1"

        output_file = save_post_response(
            "threads",
            success=False,
            error="The post you're trying to publish has an invalid link attachment.",
        )

        self.assertEqual(output_file, "threads-response.json")
        with open(output_file, "r", encoding="utf-8") as f:
            payload = json.load(f)

        self.assertEqual(payload["success"], False)
        self.assertEqual(
            payload["error"],
            "The post you're trying to publish has an invalid link attachment.",
        )
        self.assertIsNone(payload["post_id"])
        self.assertIsNone(payload["post_url"])

    def test_save_post_response_normalizes_social_key(self):
        """Social names are normalized to lowercase hyphenated file names."""
        os.environ["SAVE_RESPONSE"] = "yes"

        output_file = save_post_response("Instagram (via Facebook)", success=True)

        self.assertEqual(output_file, "instagram-via-facebook-response.json")
        self.assertTrue(os.path.exists(output_file))


if __name__ == "__main__":
    unittest.main()
