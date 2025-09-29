#!/usr/bin/env python3
"""
Post content to a Facebook Page using the Facebook Graph API (v20.0) via direct HTTP requests.
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
import requests
import uuid

# Add common module to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'common'))

from social_media_utils import (
    setup_logging,
    get_required_env_var,
    get_optional_env_var,
    process_templated_content_if_needed,
    validate_post_content,
    handle_api_error,
    log_success,
    parse_media_files
)


GRAPH_API_VERSION = "v23.0"
GRAPH_API_BASE_URL = f"https://graph.facebook.com/{GRAPH_API_VERSION}"


def _graph_api_post(path: str, access_token: str, *, data=None, files=None, params=None, action: str):
    """Make a POST request to the Facebook Graph API and return the JSON payload."""
    params = dict(params or {})
    params['access_token'] = access_token

    url = f"{GRAPH_API_BASE_URL}/{path}"
    try:
        response = requests.post(url, params=params, data=data, files=files, timeout=60)
    except requests.RequestException as exc:
        logging.error(f"Facebook Graph API {action} request failed: {exc}")
        raise

    try:
        payload = response.json()
    except ValueError:
        logging.error(f"Facebook Graph API {action} returned non-JSON response: {response.text}")
        raise

    if not response.ok or 'error' in payload:
        error_info = payload.get('error', {}) if isinstance(payload, dict) else payload
        logging.error(
            f"Facebook Graph API {action} failed (status {response.status_code}): {error_info}"
        )
        raise RuntimeError(f"Facebook Graph API {action} failed")

    return payload


def upload_photo(page_id: str, photo_path: str, message: str, published: bool, access_token: str) -> str:
    """Upload a photo to Facebook Page."""
    data = {'published': str(published).lower()}
    if message:
        data['message'] = message

    try:
        with open(photo_path, 'rb') as photo_file:
            payload = _graph_api_post(
                f"{page_id}/photos",
                access_token,
                data=data,
                files={'source': photo_file},
                action="photo upload"
            )
    except Exception as exc:
        logging.error(f"Failed to upload photo {photo_path}: {exc}")
        raise

    return payload.get('post_id') or payload.get('id')


def upload_video(page_id: str, video_path: str, description: str, published: bool, access_token: str) -> str:
    """Upload a video to Facebook Page."""
    data = {'published': str(published).lower()}
    if description:
        data['description'] = description

    try:
        with open(video_path, 'rb') as video_file:
            payload = _graph_api_post(
                f"{page_id}/videos",
                access_token,
                data=data,
                files={'source': video_file},
                action="video upload"
            )
    except Exception as exc:
        logging.error(f"Failed to upload video {video_path}: {exc}")
        raise

    return payload.get('id')


def post_to_facebook():
    """Main function to post content to Facebook Page."""
    # Setup logging
    log_level = get_optional_env_var("LOG_LEVEL", "INFO")
    logger = setup_logging(log_level)
    
    try:
        # Get required parameters
        page_id = get_required_env_var("FB_PAGE_ID")
        access_token = get_required_env_var("FB_ACCESS_TOKEN")
        content = get_required_env_var("POST_CONTENT")
        # Process templated content if present (env, builtin, json sources)
        content = process_templated_content_if_needed(content)

        # Determine privacy mode
        privacy_mode = get_optional_env_var("POST_PRIVACY", "public").strip().lower()
        if privacy_mode not in {"public", "private"}:
            logging.error("POST_PRIVACY must be either 'public' or 'private'")
            sys.exit(1)
        published = privacy_mode == "public"

        # Validate content
        if not validate_post_content(content):
            sys.exit(1)
        
        # Get optional parameters
        link = get_optional_env_var("POST_LINK", "")
        # Process POST_CONTENT and POST_LINK in a single templating call so
        # they share the same API-driven JSON context (important for [RANDOM]).
        if link:
            delim = f"__FB_DELIM_{uuid.uuid4().hex}__"
            combined = f"{content}{delim}{link}"
            processed_combined = process_templated_content_if_needed(combined)
            if delim in processed_combined:
                content, link = processed_combined.split(delim, 1)
            else:
                # fallback, process individually
                content = process_templated_content_if_needed(content)
                link = process_templated_content_if_needed(link)
        else:
            # No link to process; just process content
            content = process_templated_content_if_needed(content)
        media_input = get_optional_env_var("MEDIA_FILES", "")
        media_files = parse_media_files(media_input)
        
        # Prepare post data
        post_data = {
            'message': content
        }

        if link:
            post_data['link'] = link
        if not published:
            post_data['published'] = 'false'

        # DRY RUN GUARD
        from social_media_utils import dry_run_guard
        dry_run_request = dict(post_data)
        if media_files:
            dry_run_request['media_files'] = ', '.join(media_files)
        dry_run_request['privacy'] = privacy_mode
        dry_run_guard("Facebook Page", content, media_files, dry_run_request)

        # Handle media files
        if media_files:
            if len(media_files) == 1:
                # Single media file
                media_file = media_files[0]
                file_ext = Path(media_file).suffix.lower()
                
                if file_ext in ['.jpg', '.jpeg', '.png', '.gif']:
                    # Upload photo
                    post_id = upload_photo(page_id, media_file, content, published, access_token)
                elif file_ext in ['.mp4', '.mov', '.avi']:
                    # Upload video
                    post_id = upload_video(page_id, media_file, content, published, access_token)
                else:
                    logger.warning(f"Unsupported media type: {file_ext}")
                    # Create text post with link if media type not supported
                    payload = _graph_api_post(
                        f"{page_id}/feed",
                        access_token,
                        data=post_data,
                        action="create feed post"
                    )
                    post_id = payload.get('id')
            else:
                # Multiple media files - create a text post and mention that media was uploaded separately
                logger.info("Multiple media files detected. Uploading separately and creating text post.")
                for media_file in media_files:
                    file_ext = Path(media_file).suffix.lower()
                    if file_ext in ['.jpg', '.jpeg', '.png', '.gif']:
                        upload_photo(page_id, media_file, "", published, access_token)
                    elif file_ext in ['.mp4', '.mov', '.avi']:
                        upload_video(page_id, media_file, "", published, access_token)
                
                # Create the main text post
                payload = _graph_api_post(
                    f"{page_id}/feed",
                    access_token,
                    data=post_data,
                    action="create feed post"
                )
                post_id = payload.get('id')
        else:
            # Create text post
            payload = _graph_api_post(
                f"{page_id}/feed",
                access_token,
                data=post_data,
                action="create feed post"
            )
            post_id = payload.get('id')
        
        post_url = f"https://www.facebook.com/{post_id}" if published else "(Unpublished post - no public URL)"
        
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