"""Unit tests for shared remote media parsing helpers."""

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent))

from social_media_utils import parse_media_files


class TestParseMediaFiles(unittest.TestCase):
    """Test remote media parsing behavior."""

    @patch('social_media_utils.os.path.exists')
    @patch('social_media_utils.download_file_if_url')
    def test_preserves_remote_video_url_when_requested(self, mock_download, mock_exists):
        remote_video = 'https://cdn.example.com/video.mp4'

        result = parse_media_files(remote_video, preserve_remote_video_urls=True)

        self.assertEqual(result, [remote_video])
        mock_download.assert_not_called()
        mock_exists.assert_not_called()

    @patch('social_media_utils.os.path.exists', return_value=True)
    @patch('social_media_utils.download_file_if_url', return_value='_downloaded_media_image.jpg')
    def test_still_downloads_remote_image_when_video_passthrough_enabled(self, mock_download, mock_exists):
        remote_image = 'https://cdn.example.com/image.jpg'

        result = parse_media_files(remote_image, preserve_remote_video_urls=True)

        self.assertEqual(result, ['_downloaded_media_image.jpg'])
        mock_download.assert_called_once_with(remote_image, 5)
        mock_exists.assert_called_once_with('_downloaded_media_image.jpg')


if __name__ == '__main__':
    unittest.main()