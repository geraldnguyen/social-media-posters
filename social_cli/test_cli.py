#!/usr/bin/env python3
"""
Unit tests for the social CLI wrapper.
"""

import unittest
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
from click.testing import CliRunner

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from social_cli.cli import main, __version__


class TestCLI(unittest.TestCase):
    """Test the CLI commands."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
        # Clear environment variables that might interfere with tests
        self.env_backup = {}
        env_vars_to_clear = [
            'POST_CONTENT', 'DRY_RUN', 'LOG_LEVEL', 'INPUT_FILE',
            'X_API_KEY', 'X_API_SECRET', 'X_ACCESS_TOKEN', 'X_ACCESS_TOKEN_SECRET',
            'FB_PAGE_ID', 'FB_ACCESS_TOKEN', 'IG_USER_ID', 'IG_ACCESS_TOKEN',
            'LINKEDIN_ACCESS_TOKEN', 'LINKEDIN_AUTHOR_ID',
            'BLUESKY_IDENTIFIER', 'BLUESKY_PASSWORD',
            'THREADS_USER_ID', 'THREADS_ACCESS_TOKEN',
        ]
        for var in env_vars_to_clear:
            if var in os.environ:
                self.env_backup[var] = os.environ[var]
                del os.environ[var]
    
    def tearDown(self):
        """Restore environment variables."""
        for var, value in self.env_backup.items():
            os.environ[var] = value
    
    def test_version(self):
        """Test version command."""
        result = self.runner.invoke(main, ['--version'])
        self.assertEqual(result.exit_code, 0)
        self.assertIn(__version__, result.output)
    
    def test_help(self):
        """Test help command."""
        result = self.runner.invoke(main, ['--help'])
        self.assertEqual(result.exit_code, 0)
        self.assertIn('Social media posting CLI tool', result.output)
        self.assertIn('x', result.output)
        self.assertIn('facebook', result.output)
        self.assertIn('instagram', result.output)
        self.assertIn('threads', result.output)
        self.assertIn('linkedin', result.output)
        self.assertIn('youtube', result.output)
        self.assertIn('bluesky', result.output)
    
    def test_x_help(self):
        """Test X command help."""
        result = self.runner.invoke(main, ['x', '--help'])
        self.assertEqual(result.exit_code, 0)
        self.assertIn('Post to X', result.output)
        self.assertIn('--x-api-key', result.output)
        self.assertIn('--post-content', result.output)
        self.assertIn('--dry-run', result.output)
    
    def test_facebook_help(self):
        """Test Facebook command help."""
        result = self.runner.invoke(main, ['facebook', '--help'])
        self.assertEqual(result.exit_code, 0)
        self.assertIn('Post to Facebook', result.output)
        self.assertIn('--fb-page-id', result.output)
        self.assertIn('--fb-access-token', result.output)
    
    def test_instagram_help(self):
        """Test Instagram command help."""
        result = self.runner.invoke(main, ['instagram', '--help'])
        self.assertEqual(result.exit_code, 0)
        self.assertIn('Post to Instagram', result.output)
        self.assertIn('--ig-user-id', result.output)
        self.assertIn('--ig-access-token', result.output)
    
    def test_linkedin_help(self):
        """Test LinkedIn command help."""
        result = self.runner.invoke(main, ['linkedin', '--help'])
        self.assertEqual(result.exit_code, 0)
        self.assertIn('Post to LinkedIn', result.output)
        self.assertIn('--linkedin-access-token', result.output)
        self.assertIn('--linkedin-author-id', result.output)
    
    def test_youtube_help(self):
        """Test YouTube command help."""
        result = self.runner.invoke(main, ['youtube', '--help'])
        self.assertEqual(result.exit_code, 0)
        self.assertIn('Upload video to YouTube', result.output)
        self.assertIn('--video-file', result.output)
        self.assertIn('--video-title', result.output)
    
    def test_bluesky_help(self):
        """Test Bluesky command help."""
        result = self.runner.invoke(main, ['bluesky', '--help'])
        self.assertEqual(result.exit_code, 0)
        self.assertIn('Post to Bluesky', result.output)
        self.assertIn('--bluesky-identifier', result.output)
        self.assertIn('--bluesky-password', result.output)
    
    def test_threads_help(self):
        """Test Threads command help."""
        result = self.runner.invoke(main, ['threads', '--help'])
        self.assertEqual(result.exit_code, 0)
        self.assertIn('Post to Threads', result.output)
        self.assertIn('--threads-user-id', result.output)
        self.assertIn('--threads-access-token', result.output)
    
    @patch('post_to_x.post_to_x')
    def test_x_with_options(self, mock_post):
        """Test X command with options sets environment variables."""
        mock_post.return_value = None
        
        result = self.runner.invoke(main, [
            'x',
            '--post-content', 'Test content',
            '--dry-run',
            '--log-level', 'DEBUG',
            '--x-api-key', 'test_key',
            '--x-api-secret', 'test_secret',
            '--x-access-token', 'test_token',
            '--x-access-token-secret', 'test_token_secret'
        ])
        
        # Check environment variables were set
        self.assertEqual(os.environ.get('POST_CONTENT'), 'Test content')
        self.assertEqual(os.environ.get('DRY_RUN'), 'true')
        self.assertEqual(os.environ.get('LOG_LEVEL'), 'DEBUG')
        self.assertEqual(os.environ.get('X_API_KEY'), 'test_key')
        self.assertEqual(os.environ.get('X_API_SECRET'), 'test_secret')
        self.assertEqual(os.environ.get('X_ACCESS_TOKEN'), 'test_token')
        self.assertEqual(os.environ.get('X_ACCESS_TOKEN_SECRET'), 'test_token_secret')
        
        # Verify the post function was called
        mock_post.assert_called_once()
    
    @patch('post_to_facebook.post_to_facebook')
    def test_facebook_with_options(self, mock_post):
        """Test Facebook command with options sets environment variables."""
        mock_post.return_value = None
        
        result = self.runner.invoke(main, [
            'facebook',
            '--post-content', 'Test FB content',
            '--fb-page-id', '123456',
            '--fb-access-token', 'fb_token',
            '--post-link', 'https://example.com',
            '--post-privacy', 'public'
        ])
        
        # Check environment variables were set
        self.assertEqual(os.environ.get('POST_CONTENT'), 'Test FB content')
        self.assertEqual(os.environ.get('FB_PAGE_ID'), '123456')
        self.assertEqual(os.environ.get('FB_ACCESS_TOKEN'), 'fb_token')
        self.assertEqual(os.environ.get('POST_LINK'), 'https://example.com')
        self.assertEqual(os.environ.get('POST_PRIVACY'), 'public')
        
        # Verify the post function was called
        mock_post.assert_called_once()
    
    @patch('post_to_linkedin.post_to_linkedin')
    def test_linkedin_with_options(self, mock_post):
        """Test LinkedIn command with options sets environment variables."""
        mock_post.return_value = None
        
        result = self.runner.invoke(main, [
            'linkedin',
            '--post-content', 'Test LinkedIn content',
            '--linkedin-access-token', 'linkedin_token',
            '--linkedin-author-id', 'urn:li:person:123'
        ])
        
        # Check environment variables were set
        self.assertEqual(os.environ.get('POST_CONTENT'), 'Test LinkedIn content')
        self.assertEqual(os.environ.get('LINKEDIN_ACCESS_TOKEN'), 'linkedin_token')
        self.assertEqual(os.environ.get('LINKEDIN_AUTHOR_ID'), 'urn:li:person:123')
        
        # Verify the post function was called
        mock_post.assert_called_once()
    
    @patch('post_to_youtube.post_to_youtube')
    def test_youtube_with_options(self, mock_post):
        """Test YouTube command with options sets environment variables."""
        mock_post.return_value = None
        
        result = self.runner.invoke(main, [
            'youtube',
            '--video-file', 'test.mp4',
            '--video-title', 'Test Video',
            '--video-description', 'Test Description',
            '--video-privacy-status', 'private',
            '--youtube-oauth-client-id', 'client_id',
            '--youtube-oauth-client-secret', 'client_secret',
            '--youtube-oauth-refresh-token', 'refresh_token'
        ])
        
        # Check environment variables were set
        self.assertEqual(os.environ.get('VIDEO_FILE'), 'test.mp4')
        self.assertEqual(os.environ.get('VIDEO_TITLE'), 'Test Video')
        self.assertEqual(os.environ.get('VIDEO_DESCRIPTION'), 'Test Description')
        self.assertEqual(os.environ.get('VIDEO_PRIVACY_STATUS'), 'private')
        
        # Verify the post function was called
        mock_post.assert_called_once()
    
    def test_common_options_set_env_vars(self):
        """Test that common options properly set environment variables."""
        with patch('post_to_x.post_to_x'):
            result = self.runner.invoke(main, [
                'x',
                '--input-file', 'config.json',
                '--content-json', 'https://api.example.com/data.json',
                '--media-files', 'image1.jpg,image2.png',
                '--max-download-size-mb', '10'
            ])
            
            self.assertEqual(os.environ.get('INPUT_FILE'), 'config.json')
            self.assertEqual(os.environ.get('CONTENT_JSON'), 'https://api.example.com/data.json')
            self.assertEqual(os.environ.get('MEDIA_FILES'), 'image1.jpg,image2.png')
            self.assertEqual(os.environ.get('MAX_DOWNLOAD_SIZE_MB'), '10')
    
    def test_missing_credentials_error(self):
        """Test that missing credentials produce appropriate error."""
        # This test expects the post function to fail due to missing credentials
        result = self.runner.invoke(main, ['x', '--post-content', 'Test'])
        
        # The command should exit with non-zero code due to missing credentials
        self.assertNotEqual(result.exit_code, 0)


class TestCLIIntegration(unittest.TestCase):
    """Integration tests for CLI with actual scripts (mocked at API level)."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
    
    @patch('tweepy.Client')
    @patch('tweepy.API')
    def test_x_dry_run(self, mock_api, mock_client):
        """Test X command with dry-run mode."""
        result = self.runner.invoke(main, [
            'x',
            '--post-content', 'Test dry run',
            '--dry-run',
            '--x-api-key', 'test_key',
            '--x-api-secret', 'test_secret',
            '--x-access-token', 'test_token',
            '--x-access-token-secret', 'test_secret'
        ])
        
        # In dry-run mode, should exit with 0 and not call the API
        self.assertEqual(result.exit_code, 0)
        self.assertIn('[DRY RUN', result.output)
        mock_client.assert_not_called()


if __name__ == '__main__':
    unittest.main()
