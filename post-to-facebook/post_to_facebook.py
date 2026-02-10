#!/usr/bin/env python3
"""
Post content to a Facebook Page using the Facebook Graph API (v20.0) via direct HTTP requests.
"""

import os
import json
from pathlib import Path
from datetime import datetime

# Load environment variables from a local .env file if present (for local development)
try:
    from dotenv import load_dotenv
    env_path = Path.cwd() / '.env'
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

from templating_utils import process_templated_contents
from social_media_utils import (
    setup_logging,
    get_required_env_var,
    get_optional_env_var,
    validate_post_content,
    handle_api_error,
    log_success,
    parse_media_files,
    parse_scheduled_time
)


GRAPH_API_VERSION = "v23.0"
GRAPH_API_BASE_URL = f"https://graph.facebook.com/{GRAPH_API_VERSION}"


# Module-level logger
logger = logging.getLogger(__name__)

def _graph_api_post(path: str, access_token: str, *, data=None, files=None, params=None, action: str, timeout: int = 60):
    """Make a POST request to the Facebook Graph API and return the JSON payload."""
    params = dict(params or {})
    params['access_token'] = access_token

    url = f"{GRAPH_API_BASE_URL}/{path}"
    try:
        response = requests.post(url, params=params, data=data, files=files, timeout=timeout)
    except requests.RequestException as exc:
        logger.error(f"Facebook Graph API {action} request failed: {exc}")
        raise

    try:
        payload = response.json()
    except ValueError:
        logger.error(f"Facebook Graph API {action} returned non-JSON response: {response.text}")
        raise

    if not response.ok or 'error' in payload:
        error_info = payload.get('error', {}) if isinstance(payload, dict) else payload
        logger.error(
            f"Facebook Graph API {action} failed (status {response.status_code}): {error_info}"
        )
        raise RuntimeError(f"Facebook Graph API {action} failed")

    return payload


def upload_photo(page_id: str, photo_path: str, message: str, published: bool, access_token: str, scheduled_publish_time: int = None) -> str:
    """Upload a photo to Facebook Page."""
    data = {'published': str(published).lower()}
    if message:
        data['message'] = message
    
    # Add scheduled publish time if provided
    if scheduled_publish_time:
        data['scheduled_publish_time'] = str(scheduled_publish_time)
        logger.info(f"Photo will be scheduled for: {scheduled_publish_time}")

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
        logger.error(f"Failed to upload photo {photo_path}: {exc}")
        raise

    return payload.get('post_id') or payload.get('id')


def upload_video(page_id: str, video_path: str, description: str, published: bool, access_token: str, scheduled_publish_time: int = None) -> str:
    """
    Upload a video to Facebook Page using resumable upload.
    
    Uses Facebook's resumable upload API for better reliability with large files:
    1. Start upload session
    2. Upload video in chunks
    3. Finish upload
    
    For small videos (<5MB), falls back to simple upload.
    """
    video_size = os.path.getsize(video_path)
    logger.info(f"Uploading video {video_path} (size: {video_size} bytes)")
    
    # Use resumable upload for videos larger than 5MB (configurable threshold)
    threshold_mb = int(get_optional_env_var("VIDEO_UPLOAD_THRESHOLD_MB", "5"))
    threshold_bytes = threshold_mb * 1024 * 1024
    
    if video_size < threshold_bytes:
        logger.info(f"Video is smaller than {threshold_mb}MB, using simple upload")
        return _upload_video_simple(page_id, video_path, description, published, access_token, scheduled_publish_time)
    else:
        logger.info(f"Video is larger than {threshold_mb}MB, using resumable upload")
        return _upload_video_resumable(page_id, video_path, description, published, access_token, scheduled_publish_time)


def _upload_video_simple(page_id: str, video_path: str, description: str, published: bool, access_token: str, scheduled_publish_time: int = None) -> str:
    """Upload a small video using simple POST request."""
    data = {'published': str(published).lower()}
    if description:
        data['description'] = description
    
    # Add scheduled publish time if provided
    if scheduled_publish_time:
        data['scheduled_publish_time'] = str(scheduled_publish_time)
        logger.info(f"Video will be scheduled for: {scheduled_publish_time}")

    try:
        with open(video_path, 'rb') as video_file:
            payload = _graph_api_post(
                f"{page_id}/videos",
                access_token,
                data=data,
                files={'source': video_file},
                action="video upload (simple)"
            )
    except Exception as exc:
        logger.error(f"Failed to upload video {video_path}: {exc}")
        raise

    return payload.get('id')


def _upload_video_resumable(page_id: str, video_path: str, description: str, published: bool, access_token: str, scheduled_publish_time: int = None) -> str:
    """
    Upload a large video using Facebook's resumable upload API.
    
    This approach uploads video in chunks to avoid timeout issues with large files.
    See: https://developers.facebook.com/docs/video-api/guides/publishing
    """
    video_size = os.path.getsize(video_path)
    
    # Step 1: Start upload session
    logger.info("Step 1: Starting upload session...")
    start_data = {
        'upload_phase': 'start',
        'file_size': str(video_size)
    }
    start_payload = _graph_api_post(
        f"{page_id}/videos",
        access_token,
        data=start_data,
        action="start upload session"
    )
    
    upload_session_id = start_payload.get('upload_session_id')
    video_id = start_payload.get('video_id')
    
    if not upload_session_id:
        raise RuntimeError("Failed to get upload_session_id from start phase")
    
    logger.info(f"Upload session started: session_id={upload_session_id}, video_id={video_id}")
    
    # Step 2: Transfer video data in chunks
    logger.info("Step 2: Transferring video data in chunks...")
    # Use 4MB chunks - this is Facebook's recommended chunk size for video uploads
    chunk_size = 1024 * 1024 * 4  # 4MB chunks
    start_offset = 0
    
    try:
        with open(video_path, 'rb') as video_file:
            while start_offset < video_size:
                # Read chunk
                video_file.seek(start_offset)
                chunk = video_file.read(chunk_size)
                
                # Defensive check - should not happen given while condition, but prevents infinite loop
                if not chunk:
                    break
                
                # Upload chunk
                chunk_end = min(start_offset + len(chunk), video_size)
                logger.info(f"Uploading chunk: bytes {start_offset}-{chunk_end-1}/{video_size}")
                
                transfer_data = {
                    'upload_phase': 'transfer',
                    'upload_session_id': upload_session_id,
                    'start_offset': str(start_offset)
                }
                
                # Use files parameter for binary data
                transfer_payload = _graph_api_post(
                    f"{page_id}/videos",
                    access_token,
                    data=transfer_data,
                    files={'video_file_chunk': chunk},
                    action="transfer video chunk",
                    timeout=300  # 5 minutes for chunk upload
                )
                
                logger.debug(f"Chunk upload response: {transfer_payload}")
                
                start_offset += len(chunk)
        
        logger.info("Video data transfer complete")
        
    except Exception as exc:
        logger.error(f"Failed to transfer video chunks: {exc}")
        raise
    
    # Step 3: Finish upload
    logger.info("Step 3: Finishing upload...")
    finish_data = {
        'upload_phase': 'finish',
        'upload_session_id': upload_session_id
    }
    
    if description:
        finish_data['description'] = description
    
    finish_data['published'] = str(published).lower()
    
    # Add scheduled publish time if provided
    if scheduled_publish_time:
        finish_data['scheduled_publish_time'] = str(scheduled_publish_time)
        logger.info(f"Video will be scheduled for: {scheduled_publish_time}")
    
    finish_payload = _graph_api_post(
        f"{page_id}/videos",
        access_token,
        data=finish_data,
        action="finish upload"
    )
    
    success = finish_payload.get('success', False)
    
    if not success:
        raise RuntimeError(f"Upload finish phase failed: {finish_payload}")
    
    logger.info(f"Video upload completed successfully: video_id={video_id}")
    
    return video_id


def post_comment(post_id: str, access_token: str, message: str) -> str:
    """Post a comment on a Facebook post.
    
    Args:
        post_id: The Facebook post ID to comment on
        access_token: Facebook Page access token
        message: The comment message text (can include links)
        
    Returns:
        The comment ID
        
    Note:
        - Comments only support text messages (including links in text)
        - Media files cannot be directly uploaded to comments
        - Comments cannot be scheduled
    """
    comment_data = {
        'message': message
    }
    
    payload = _graph_api_post(
        f"{post_id}/comments",
        access_token,
        data=comment_data,
        action="post comment"
    )
    
    return payload.get('id')


def post_to_facebook():
    """Main function to post content to Facebook Page or comment on a post."""
    # Setup logging
    log_level = get_optional_env_var("LOG_LEVEL", "INFO")
    logger = setup_logging(log_level)
    
    try:
        # Get required parameters
        access_token = get_required_env_var("FB_ACCESS_TOKEN")
        content = get_required_env_var("POST_CONTENT")
        
        # Check if we're posting a comment instead of a new post
        fb_post_id = get_optional_env_var("FB_POST_ID", "")
        
        if fb_post_id:
            # Comment mode - post as a comment on the specified post
            logger.info(f"Comment mode: posting comment on post {fb_post_id}")
            
            # Get optional parameters for comment
            link = get_optional_env_var("POST_LINK", "")
            media_input = get_optional_env_var("MEDIA_FILES", "")
            media_files = parse_media_files(media_input)
            
            # Process templated content and link using the same JSON root
            content, link = process_templated_contents(content, link)
            
            # Validate content
            if not validate_post_content(content):
                sys.exit(1)
            
            # Build the comment message
            comment_message = content
            
            # If link is provided, append it to the message
            if link:
                comment_message = f"{content}\n{link}"
                logger.info(f"Link will be included in comment text: {link}")
            
            # If media files are provided, include them as URLs in the message
            if media_files:
                logger.warning("Note: Media files cannot be directly uploaded to comments. URLs will be included in the comment text.")
                for media_file in media_files:
                    # If it's a URL, add it to the message
                    if media_file.startswith('http://') or media_file.startswith('https://'):
                        comment_message = f"{comment_message}\n{media_file}"
                    else:
                        logger.warning(f"Local file {media_file} cannot be included in a comment. Please provide a URL instead.")
            
            # DRY RUN GUARD
            from social_media_utils import dry_run_guard
            dry_run_request = {
                'post_id': fb_post_id,
                'message': comment_message
            }
            dry_run_guard("Facebook Comment", comment_message, [], dry_run_request)
            
            # Post the comment
            comment_id = post_comment(fb_post_id, access_token, comment_message)
            
            comment_url = f"https://www.facebook.com/{comment_id}"
            
            # Output for GitHub Actions
            if 'GITHUB_OUTPUT' in os.environ:
                with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
                    f.write(f"comment-id={comment_id}\n")
                    f.write(f"comment-url={comment_url}\n")
            
            log_success("Facebook Comment", comment_id)
            logger.info(f"Comment URL: {comment_url}")
            return
        
        # Normal post mode - create a new post
        page_id = get_required_env_var("FB_PAGE_ID")

        # Determine privacy mode
        privacy_mode = get_optional_env_var("POST_PRIVACY", "public").strip().lower()
        if privacy_mode not in {"public", "private"}:
            logger.error("POST_PRIVACY must be either 'public' or 'private'")
            sys.exit(1)
        published = privacy_mode == "public"

        # Get optional parameters
        link = get_optional_env_var("POST_LINK", "")
        # Process templated content and link using the same JSON root
        content, link = process_templated_contents(content, link)

        # Validate content
        if not validate_post_content(content):
            sys.exit(1)
        media_input = get_optional_env_var("MEDIA_FILES", "")
        media_files = parse_media_files(media_input)
        
        # Get scheduling parameters
        scheduled_time_str = get_optional_env_var("SCHEDULED_PUBLISH_TIME", "")
        scheduled_publish_time = None
        
        if scheduled_time_str:
            # Parse the scheduled time (supports ISO 8601 and offset format)
            scheduled_time_iso = parse_scheduled_time(scheduled_time_str)
            if scheduled_time_iso:
                # Facebook API requires Unix timestamp (seconds since epoch)
                dt = datetime.fromisoformat(scheduled_time_iso.replace('Z', '+00:00'))
                scheduled_publish_time = int(dt.timestamp())
                logger.info(f"Post will be scheduled for: {scheduled_time_iso} (Unix timestamp: {scheduled_publish_time})")
                
                # When scheduling, the post must be unpublished initially
                if published:
                    logger.info("Scheduling requires post to be initially unpublished. Setting published=False.")
                    published = False
        
        # Prepare post data
        post_data = {
            'message': content
        }

        if link:
            post_data['link'] = link
        if not published:
            post_data['published'] = 'false'
        
        # Add scheduled publish time to post data if provided
        if scheduled_publish_time:
            post_data['scheduled_publish_time'] = str(scheduled_publish_time)

        # DRY RUN GUARD
        from social_media_utils import dry_run_guard
        dry_run_request = dict(post_data)
        if media_files:
            dry_run_request['media_files'] = ', '.join(media_files)
        dry_run_request['privacy'] = 'scheduled' if scheduled_publish_time else privacy_mode
        if scheduled_publish_time:
            dry_run_request['scheduled_for'] = scheduled_time_str
        dry_run_guard("Facebook Page", content, media_files, dry_run_request)

        # Handle media files
        if media_files:
            if len(media_files) == 1:
                # Single media file
                media_file = media_files[0]
                file_ext = Path(media_file).suffix.lower()
                
                if file_ext in ['.jpg', '.jpeg', '.png', '.gif']:
                    # Upload photo
                    post_id = upload_photo(page_id, media_file, content, published, access_token, scheduled_publish_time)
                elif file_ext in ['.mp4', '.mov', '.avi']:
                    # Upload video
                    post_id = upload_video(page_id, media_file, content, published, access_token, scheduled_publish_time)
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
                # Multiple media files
                image_exts = {'.jpg', '.jpeg', '.png', '.gif'}
                video_exts = {'.mp4', '.mov', '.avi'}
                image_files = [m for m in media_files if Path(m).suffix.lower() in image_exts]
                video_files = [m for m in media_files if Path(m).suffix.lower() in video_exts]

                if image_files and not video_files:
                    # Multiple images: upload as unpublished and attach to a single feed post
                    logger.info("Multiple images detected. Uploading as attached media.")
                    attached_media = []
                    for media_file in image_files:
                        try:
                            with open(media_file, 'rb') as photo_file:
                                payload = _graph_api_post(
                                    f"{page_id}/photos",
                                    access_token,
                                    data={'published': 'false'},
                                    files={'source': photo_file},
                                    action="photo upload (unpublished)"
                                )
                            media_id = payload.get('id') or payload.get('post_id')
                            if not media_id:
                                raise RuntimeError(f"No media id returned for {media_file}")
                            attached_media.append({'media_fbid': media_id})
                        except Exception as exc:
                            logger.error(f"Failed to upload photo {media_file} for attached media: {exc}")
                            raise

                    # Create the main text post with attached media
                    post_data_with_media = dict(post_data)
                    post_data_with_media['attached_media'] = json.dumps(attached_media)
                    payload = _graph_api_post(
                        f"{page_id}/feed",
                        access_token,
                        data=post_data_with_media,
                        action="create feed post with attached media"
                    )
                    post_id = payload.get('id')
                else:
                    # Mixed media types or multiple videos are not supported for a single feed post
                    logger.error("Facebook does not support mixed media types (photos + videos) or multiple videos in a single feed post.")
                    sys.exit(1)
        else:
            # Create text post
            payload = _graph_api_post(
                f"{page_id}/feed",
                access_token,
                data=post_data,
                action="create feed post"
            )
            post_id = payload.get('id')
        
        post_url = f"https://www.facebook.com/{post_id}" if (published and not scheduled_publish_time) else "(Scheduled/Unpublished post - no public URL yet)"
        
        # Output for GitHub Actions
        if 'GITHUB_OUTPUT' in os.environ:
            with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
                f.write(f"post-id={post_id}\n")
                f.write(f"post-url={post_url}\n")
                if scheduled_publish_time:
                    f.write(f"scheduled-time={scheduled_time_str}\n")
        
        log_success("Facebook Page", post_id)
        logger.info(f"Post URL: {post_url}")
        if scheduled_publish_time:
            logger.info(f"Post scheduled for: {scheduled_time_str}")
        
    except Exception as e:
        handle_api_error(e, "Facebook Page")


if __name__ == "__main__":
    post_to_facebook()