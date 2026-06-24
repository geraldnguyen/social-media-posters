#!/usr/bin/env python3
"""
Post content to Mastodon using the Mastodon REST API.
"""

import os
import sys
import logging
import requests
from pathlib import Path

# Load environment variables from a local .env file if present (for local development)
try:
    from dotenv import load_dotenv
    env_path = Path.cwd() / '.env'
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
except ImportError:
    pass  # python-dotenv is not installed; skip loading .env

# Add common module to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'common'))

from templating_utils import process_templated_contents
from social_media_utils import (
    setup_logging,
    get_required_env_var,
    get_optional_env_var,
    validate_post_content,
    handle_api_error,
    log_success,
    parse_media_files,
    parse_scheduled_time,
    dry_run_guard,
    save_post_response,
)

# Module-level logger
logger = logging.getLogger(__name__)


def upload_media_to_mastodon(server: str, access_token: str, file_path: str) -> str:
    """Upload media file to Mastodon API v2 and return media ID."""
    url = f"{server}/api/v2/media"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    file_name = Path(file_path).name
    logger.info(f"Uploading media file {file_path} to Mastodon via API v2...")
    
    # We will upload the media file using multipart/form-data
    with open(file_path, "rb") as f:
        files = {"file": (file_name, f)}
        response = requests.post(url, headers=headers, files=files, timeout=30)
        
    # If API v2 is not found/supported, fallback to v1
    if response.status_code == 404:
        logger.warning("Mastodon API v2 media upload returned 404. Falling back to API v1...")
        url_v1 = f"{server}/api/v1/media"
        with open(file_path, "rb") as f:
            files = {"file": (file_name, f)}
            response = requests.post(url_v1, headers=headers, files=files, timeout=30)
            
    response.raise_for_status()
    data = response.json()
    media_id = data.get("id")
    if not media_id:
        raise ValueError(f"Could not retrieve media ID from Mastodon response: {data}")
        
    logger.info(f"Successfully uploaded media {file_name}. ID: {media_id}")
    return media_id


def post_to_mastodon():
    """Main function to post content to Mastodon."""
    # Setup logging
    log_level = get_optional_env_var("LOG_LEVEL", "INFO")
    logger = setup_logging(log_level)
    
    media_files = []
    try:
        # Get required parameters
        server = get_required_env_var("MASTODON_SERVER").strip()
        access_token = get_required_env_var("MASTODON_ACCESS_TOKEN").strip()
        content = get_required_env_var("POST_CONTENT")

        # Get optional parameters
        link = get_optional_env_var("POST_LINK", "")
        
        # Normalize server address
        if not server.startswith("http://") and not server.startswith("https://"):
            server = f"https://{server}"
        server = server.rstrip("/")
        
        # Process templated content and link using the same JSON root
        content, link = process_templated_contents(content, link)

        # Get link-in-comment options (needed before link is appended to content)
        # LINK_IN_COMMENT is a boolean flag; when set, POST_LINK is posted as a reply
        link_in_comment = get_optional_env_var("LINK_IN_COMMENT", "").lower() in ('1', 'true', 'yes')
        pin_link_comment = get_optional_env_var("PIN_LINK_COMMENT", "").lower() in ('1', 'true', 'yes')

        # If there's a link and not posting it as a comment, append it to the content for Mastodon
        if link and not link_in_comment:
            content = f"{content}\n\n{link}" if content else link

        # Validate content (Mastodon default character limit is 500 characters)
        if not validate_post_content(content, max_length=500):
            sys.exit(1)
            
        # Parse media files
        media_input = get_optional_env_var("MEDIA_FILES", "")
        max_size_mb = int(get_optional_env_var("MAX_DOWNLOAD_SIZE_MB", "5"))
        media_files = parse_media_files(media_input, max_size_mb)
        
        # Process scheduling
        scheduled_time_str = get_optional_env_var("SCHEDULED_PUBLISH_TIME", "")
        scheduled_at = None
        if scheduled_time_str:
            scheduled_at = parse_scheduled_time(scheduled_time_str)
            logger.info(f"Post will be scheduled for: {scheduled_at}")

        # DRY RUN GUARD
        dry_run_request = {
            'text': content,
            'text_length': len(content),
            'server': server,
            'scheduled_at': scheduled_at,
        }
        
        if media_files:
            dry_run_request['media_files_count'] = len(media_files)
            dry_run_request['media_files'] = []
            for idx, media_file in enumerate(media_files, 1):
                file_path = Path(media_file)
                file_size = file_path.stat().st_size if file_path.exists() else 0
                dry_run_request['media_files'].append({
                    'index': idx,
                    'path': str(media_file),
                    'filename': file_path.name,
                    'extension': file_path.suffix,
                    'size_bytes': file_size,
                    'size_kb': round(file_size / 1024, 2) if file_size > 0 else 0
                })

        if link_in_comment and link:
            dry_run_request['link_in_comment'] = link  # actual URL
            dry_run_request['pin_link_comment'] = pin_link_comment

        dry_run_guard("Mastodon", content, media_files, dry_run_request)
        
        # Upload media files if provided
        media_ids = []
        for media_file in media_files:
            media_id = upload_media_to_mastodon(server, access_token, media_file)
            media_ids.append(media_id)

        # Create status payload
        # According to Mastodon API documentation, we can send statuses as JSON or URL-encoded form data.
        # JSON is preferred.
        url = f"{server}/api/v1/statuses"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "status": content
        }
        if media_ids:
            payload["media_ids"] = media_ids
        if scheduled_at:
            payload["scheduled_at"] = scheduled_at

        logger.info(f"Creating status post on Mastodon...")
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        post_id = data.get("id")
        
        # Format post URL
        if scheduled_at:
            # If scheduled, the API returns a ScheduledStatus object with ID
            logger.info(f"Successfully scheduled Mastodon post. Scheduled ID: {post_id} at {data.get('scheduled_at')}")
            post_url = f"{server}/api/v1/scheduled_statuses/{post_id}"
        else:
            post_url = data.get("url", f"{server}/statuses/{post_id}")
            logger.info(f"Successfully posted to Mastodon. Post ID: {post_id}")
            
        # Output for GitHub Actions
        if 'GITHUB_OUTPUT' in os.environ:
            with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
                f.write(f"post-id={post_id}\n")
                f.write(f"post-url={post_url}\n")

        save_post_response("mastodon", success=True, post_id=post_id, post_url=post_url)
                
        log_success("Mastodon", post_id)
        logger.info(f"Post URL: {post_url}")

        # Post POST_LINK as a reply if LINK_IN_COMMENT flag is set (only for non-scheduled)
        if link_in_comment and link and not scheduled_at:
            logger.info(f"Posting link as reply on Mastodon post {post_id}: {link}")
            try:
                reply_payload = {
                    "status": link,
                    "in_reply_to_id": post_id
                }
                reply_response = requests.post(url, json=reply_payload, headers=headers, timeout=30)
                reply_response.raise_for_status()
                comment_id = reply_response.json().get("id")
                logger.info(f"Link reply posted successfully. Comment ID: {comment_id}")
                if pin_link_comment:
                    logger.warning("Pinning replies is not supported by the Mastodon API.")
            except Exception as comment_exc:
                logger.warning(f"Failed to post link as reply on Mastodon: {comment_exc}")
        elif link_in_comment and not link:
            logger.warning("LINK_IN_COMMENT is set but no POST_LINK was provided; skipping comment.")
        elif link_in_comment and link and scheduled_at:
            logger.info("LINK_IN_COMMENT is set but post is scheduled; comment will not be posted now.")
        
    except Exception as e:
        save_post_response("mastodon", success=False, error=str(e))
        handle_api_error(e, "Mastodon")
    finally:
        # Cleanup downloaded media files
        if media_files:
            for media_file in media_files:
                file_path = Path(media_file)
                if file_path.exists() and file_path.name.startswith("_downloaded_media_"):
                    try:
                        file_path.unlink()
                        logger.debug(f"Cleaned up temporary downloaded media file: {media_file}")
                    except Exception as e:
                        logger.warning(f"Failed to clean up temporary file {media_file}: {e}")


if __name__ == "__main__":
    post_to_mastodon()
