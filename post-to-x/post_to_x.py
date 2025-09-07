#!/usr/bin/env python3
"""
Post content to X (formerly Twitter) using the X API v2.
"""

import os
from pathlib import Path

# Load environment variables from a local .env file if present (for local development)
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent / '.env'
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
except ImportError:
    pass  # python-dotenv is not installed; skip loading .env
import sys
import logging
import tweepy
from pathlib import Path

# Add common module to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'common'))

from social_media_utils import (
    setup_logging,
    get_required_env_var,
    get_optional_env_var,
    validate_post_content,
    handle_api_error,
    log_success,
    parse_media_files
)


def create_x_client():
    """Create and return an authenticated X API client."""
    api_key = get_required_env_var("X_API_KEY")
    api_secret = get_required_env_var("X_API_SECRET")
    access_token = get_required_env_var("X_ACCESS_TOKEN")
    access_token_secret = get_required_env_var("X_ACCESS_TOKEN_SECRET")
    
    # Create client with OAuth 1.0a User Context
    client = tweepy.Client(
        consumer_key=api_key,
        consumer_secret=api_secret,
        access_token=access_token,
        access_token_secret=access_token_secret,
        wait_on_rate_limit=True
    )
    
    return client


def upload_media(client, media_files):
    """Upload media files and return media IDs."""
    if not media_files:
        return []
    
    # For media upload, we need the API v1.1 client
    api_key = get_required_env_var("X_API_KEY")
    api_secret = get_required_env_var("X_API_SECRET")
    access_token = get_required_env_var("X_ACCESS_TOKEN")
    access_token_secret = get_required_env_var("X_ACCESS_TOKEN_SECRET")
    
    auth = tweepy.OAuth1UserHandler(
        api_key, api_secret, access_token, access_token_secret
    )
    api = tweepy.API(auth)
    
    media_ids = []
    for file_path in media_files:
        try:
            media = api.media_upload(filename=file_path)
            media_ids.append(media.media_id)
            logging.info(f"Uploaded media: {file_path} (ID: {media.media_id})")
        except Exception as e:
            logging.error(f"Failed to upload media {file_path}: {str(e)}")
            raise
    
    return media_ids


def post_to_x():
    """Main function to post content to X."""
    # Setup logging
    log_level = get_optional_env_var("LOG_LEVEL", "INFO")
    logger = setup_logging(log_level)
    
    try:
        # Get post content
        content = get_required_env_var("POST_CONTENT")
        
        # Validate content (X has a 280 character limit)
        if not validate_post_content(content, max_length=280):
            sys.exit(1)
        
        # Parse media files
        media_input = get_optional_env_var("MEDIA_FILES", "")
        media_files = parse_media_files(media_input)
        
        # Create X client
        client = create_x_client()
        
        # Upload media if provided
        media_ids = upload_media(client, media_files) if media_files else None
        
        # Create the post
        response = client.create_tweet(
            text=content,
            media_ids=media_ids
        )
        
        post_id = response.data['id'] # type: ignore
        post_url = f"https://twitter.com/i/web/status/{post_id}"
        
        # Output for GitHub Actions
        if 'GITHUB_OUTPUT' in os.environ:
            with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
                f.write(f"post-id={post_id}\n")
                f.write(f"post-url={post_url}\n")
        
        log_success("X", post_id)
        logger.info(f"Post URL: {post_url}")
        
    except Exception as e:
        handle_api_error(e, "X")


if __name__ == "__main__":
    post_to_x()