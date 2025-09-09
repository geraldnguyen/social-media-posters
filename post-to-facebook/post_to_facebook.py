#!/usr/bin/env python3
"""
Post content to a Facebook Page using the Facebook Graph API.
"""

import os
from pathlib import Path

# Load environment variables from a local .env file if present (for local development)
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent / '.env'
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
except ImportError:
    pass  # python-dotenv is not installed; skip loading .env
import sys
import logging
import facebook
import requests
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


def create_facebook_client():
    """Create and return an authenticated Facebook Graph API client."""
    access_token = get_required_env_var("FB_ACCESS_TOKEN")
    return facebook.GraphAPI(access_token=access_token, version="3.1")


def upload_photo(graph, page_id, photo_path, message=""):
    """Upload a photo to Facebook Page."""
    try:
        with open(photo_path, 'rb') as photo_file:
            response = graph.put_photo(
                image=photo_file,
                message=message,
                album_path=f"{page_id}/photos"
            )
        return response.get('id')
    except Exception as e:
        logging.error(f"Failed to upload photo {photo_path}: {str(e)}")
        raise


def upload_video(graph, page_id, video_path, description=""):
    """Upload a video to Facebook Page."""
    try:
        with open(video_path, 'rb') as video_file:
            response = graph.put_video(
                video=video_file,
                description=description,
                album_path=f"{page_id}/videos"
            )
        return response.get('id')
    except Exception as e:
        logging.error(f"Failed to upload video {video_path}: {str(e)}")
        raise


def post_to_facebook():
    """Main function to post content to Facebook Page."""
    # Setup logging
    log_level = get_optional_env_var("LOG_LEVEL", "INFO")
    logger = setup_logging(log_level)
    
    try:
        # Get required parameters
        page_id = get_required_env_var("FB_PAGE_ID")
        content = get_required_env_var("POST_CONTENT")
        
        # Validate content
        if not validate_post_content(content):
            sys.exit(1)
        
        # Get optional parameters
        link = get_optional_env_var("POST_LINK", "")
        media_input = get_optional_env_var("MEDIA_FILES", "")
        media_files = parse_media_files(media_input)
        
        # Create Facebook client
        graph = create_facebook_client()

        # Prepare post data
        post_data = {
            'message': content
        }

        if link:
            post_data['link'] = link

        # DRY RUN GUARD
        from social_media_utils import dry_run_guard
        dry_run_guard("Facebook Page", content, media_files, post_data)

        # Handle media files
        if media_files:
            if len(media_files) == 1:
                # Single media file
                media_file = media_files[0]
                file_ext = Path(media_file).suffix.lower()
                
                if file_ext in ['.jpg', '.jpeg', '.png', '.gif']:
                    # Upload photo
                    media_id = upload_photo(graph, page_id, media_file, content)
                    # For photo posts, we don't need to create a separate post
                    post_id = media_id
                elif file_ext in ['.mp4', '.mov', '.avi']:
                    # Upload video
                    media_id = upload_video(graph, page_id, media_file, content)
                    post_id = media_id
                else:
                    logger.warning(f"Unsupported media type: {file_ext}")
                    # Create text post with link if media type not supported
                    response = graph.put_object(page_id, "feed", **post_data)
                    post_id = response['id']
            else:
                # Multiple media files - create a text post and mention that media was uploaded separately
                logger.info("Multiple media files detected. Uploading separately and creating text post.")
                for media_file in media_files:
                    file_ext = Path(media_file).suffix.lower()
                    if file_ext in ['.jpg', '.jpeg', '.png', '.gif']:
                        upload_photo(graph, page_id, media_file)
                    elif file_ext in ['.mp4', '.mov', '.avi']:
                        upload_video(graph, page_id, media_file)
                
                # Create the main text post
                response = graph.put_object(page_id, "feed", **post_data)
                post_id = response['id']
        else:
            # Create text post
            response = graph.put_object(page_id, "feed", **post_data)
            post_id = response['id']
        
        post_url = f"https://www.facebook.com/{post_id}"
        
        # Output for GitHub Actions
        if 'GITHUB_OUTPUT' in os.environ:
            with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
                f.write(f"post-id={post_id}\n")
                f.write(f"post-url={post_url}\n")
        
        log_success("Facebook Page", post_id)
        logger.info(f"Post URL: {post_url}")
        
    except Exception as e:
        handle_api_error(e, "Facebook Page")


if __name__ == "__main__":
    post_to_facebook()