#!/usr/bin/env python3
"""
Post content to Instagram using Facebook Graph API with resumable upload.

This script uses the Instagram Graph API (via Facebook) to post content to Instagram,
with support for uploading local media files directly to Meta's servers using resumable upload for videos.
"""

import os
from datetime import datetime, timezone
from pathlib import Path

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
import time
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
    parse_scheduled_time
)

from templating_utils import process_templated_contents


# Module-level logger
logger = logging.getLogger(__name__)

GRAPH_API_VERSION = "v23.0"
GRAPH_API_BASE_URL = f"https://graph.facebook.com/{GRAPH_API_VERSION}"


class InstagramFBAPI:
    """Instagram Graph API client using Facebook infrastructure."""
    
    def __init__(self, access_token, ig_user_id):
        self.access_token = access_token
        self.ig_user_id = ig_user_id
        self.base_url = GRAPH_API_BASE_URL
    
    def _make_request(self, method, endpoint, **kwargs):
        """Make a request to the Graph API."""
        url = f"{self.base_url}/{endpoint}"
        
        # Add access token to params
        if 'params' not in kwargs:
            kwargs['params'] = {}
        kwargs['params']['access_token'] = self.access_token
        
        try:
            if method == 'GET':
                response = requests.get(url, **kwargs)
            elif method == 'POST':
                response = requests.post(url, **kwargs)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_detail = e.response.json()
                    logger.error(f"Error details: {error_detail}")
                except:
                    logger.error(f"Response text: {e.response.text}")
            raise

    def _create_resumable_video_container(self, caption, is_carousel_item):
        """Start a resumable upload session and return container id + upload URL."""
        data = {
            'upload_type': 'resumable',
            'media_type': 'VIDEO' if is_carousel_item else 'REELS',
        }

        # Captions go on the container unless it's a carousel item
        if caption and not is_carousel_item:
            data['caption'] = caption

        if is_carousel_item:
            data['is_carousel_item'] = True

        response = self._make_request('POST', f"{self.ig_user_id}/media", data=data)

        container_id = response.get('id')
        upload_url = response.get('upload_url') or response.get('uri')

        if not container_id:
            raise RuntimeError(f"Failed to create resumable upload container: {response}")

        # Fallback to documented rupload endpoint if API does not return a URL key
        if not upload_url:
            upload_url = f"https://rupload.facebook.com/ig-api-upload/{GRAPH_API_VERSION}/{container_id}"

        logger.info(
            "Resumable upload session created: container_id=%s upload_url=%s", container_id, upload_url
        )
        return container_id, upload_url
    
    def create_video_container_with_url(self, video_url, caption):
        """
        Create a video media container using a publicly accessible URL.
        
        Instagram Graph API requires videos to be hosted at publicly accessible URLs.
        The video is downloaded by Instagram's servers from the provided URL.
        
        Args:
            video_url: Public URL to video file
            caption: Video caption
            
        Returns:
            container_id: Media container ID ready for publishing
        """
        logger.info(f"Creating video container with URL: {video_url}")
        
        data = {
            'media_type': 'REELS',
            'video_url': video_url,
            'caption': caption
        }
        
        response = self._make_request('POST', f"{self.ig_user_id}/media", data=data)
        container_id = response.get('id')
        
        logger.info(f"Video container created: {container_id}")
        return container_id
    
    def upload_video_resumable(self, video_path, caption):
        """
        Upload a video using the documented resumable upload flow.

        Supports both local files and publicly hosted videos (via `file_url`).
        """
        is_carousel_item = False  # Backward compatibility when callers omit this flag
        return self.upload_video_resumable_with_carousel_flag(video_path, caption, is_carousel_item)

    def upload_video_resumable_with_carousel_flag(self, video_source, caption, is_carousel_item=False):
        """Resumable upload that explicitly supports carousel items."""
        logger.info(
            "Starting resumable upload for %s (carousel_item=%s)", video_source, is_carousel_item
        )

        container_id, upload_url = self._create_resumable_video_container(caption, is_carousel_item)

        headers = {
            'Authorization': f'OAuth {self.access_token}'
        }

        try:
            if str(video_source).startswith(('http://', 'https://')):
                # Hosted file upload using file_url header
                headers['file_url'] = video_source
                logger.info("Uploading hosted video via file_url header to %s", upload_url)
                response = requests.post(upload_url, headers=headers, timeout=600)
            else:
                if not os.path.exists(video_source):
                    raise FileNotFoundError(f"Video file not found: {video_source}")

                file_size = os.path.getsize(video_source)
                headers.update({
                    'offset': '0',
                    'file_size': str(file_size),
                    'Content-Type': 'application/octet-stream'
                })

                logger.info("Uploading %s bytes to %s", file_size, upload_url)
                with open(video_source, 'rb') as video_file:
                    response = requests.post(
                        upload_url,
                        headers=headers,
                        data=video_file.read(),
                        timeout=600
                    )

            response.raise_for_status()

            try:
                upload_result = response.json()
                logger.info("Resumable upload response: %s", upload_result)
            except ValueError:
                logger.info("Resumable upload completed (status: %s)", response.status_code)

        except requests.exceptions.RequestException as e:
            logger.error(f"Video upload failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_detail = e.response.json()
                    logger.error(f"Error details: {error_detail}")
                except:
                    logger.error(f"Response text: {e.response.text}")
            raise

        return container_id
    
    def create_image_container(self, image_url, caption):
        """
        Create an image media container.
        
        Args:
            image_url: Public URL to image
            caption: Image caption
            
        Returns:
            container_id: Media container ID ready for publishing
        """
        logger.info(f"Creating image container with URL: {image_url}")
        
        data = {
            'image_url': image_url,
            'caption': caption
        }
        
        response = self._make_request('POST', f"{self.ig_user_id}/media", data=data)
        container_id = response.get('id')
        
        logger.info(f"Image container created: {container_id}")
        return container_id
    
    def create_carousel_container(self, children_ids, caption):
        """
        Create a carousel container for multiple media items.
        
        Args:
            children_ids: List of media container IDs
            caption: Carousel caption
            
        Returns:
            container_id: Carousel container ID ready for publishing
        """
        logger.info(f"Creating carousel container with {len(children_ids)} items")
        
        data = {
            'media_type': 'CAROUSEL',
            'children': ','.join(children_ids),
            'caption': caption
        }
        
        response = self._make_request('POST', f"{self.ig_user_id}/media", data=data)
        container_id = response.get('id')
        
        logger.info(f"Carousel container created: {container_id}")
        return container_id
    
    def check_container_status(self, container_id, max_wait=300):
        """
        Poll the container until the upload + processing phases finish.
        """
        logger.info(f"Checking status of container {container_id}")

        start_time = time.time()
        while time.time() - start_time < max_wait:
            response = self._make_request(
                'GET',
                container_id,
                params={'fields': 'status,status_code,video_status'}
            )

            status_code = response.get('status_code')
            status = response.get('status')
            video_status = response.get('video_status', {}) or {}
            uploading_phase = video_status.get('uploading_phase', {})
            processing_phase = video_status.get('processing_phase', {})

            logger.debug(
                "Container status_code=%s status=%s uploading=%s processing=%s",
                status_code,
                status,
                uploading_phase,
                processing_phase
            )

            if status_code in ('FINISHED', 'PUBLISHED'):
                logger.info("Container is ready for publishing")
                return True
            if status_code == 'ERROR':
                logger.error(f"Container processing failed: {status}")
                return False

            # Wait before checking again
            time.sleep(2)

        logger.warning(f"Container status check timed out after {max_wait} seconds")
        return False
    
    def publish_media(self, container_id):
        """
        Publish a media container.
        
        Args:
            container_id: Media container ID
            
        Returns:
            media_id: Published media ID
        """
        logger.info(f"Publishing container {container_id}")
        
        data = {
            'creation_id': container_id
        }
        
        response = self._make_request('POST', f"{self.ig_user_id}/media_publish", data=data)
        media_id = response.get('id')
        
        logger.info(f"Media published successfully: {media_id}")
        return media_id
    
    def get_media_info(self, media_id):
        """
        Get media information.
        
        Args:
            media_id: Published media ID
            
        Returns:
            dict: Media information including permalink
        """
        response = self._make_request(
            'GET',
            media_id,
            params={'fields': 'id,permalink'}
        )
        
        return response


def upload_image_to_temp_hosting(image_url):
    """
    Validate that the image is a publicly accessible URL.
    
    Instagram Graph API requires all media to be hosted at publicly accessible URLs.
    
    Args:
        image_url: URL to image or path
        
    Returns:
        str: The validated URL
        
    Raises:
        ValueError: If the input is not a valid URL
    """
    if image_url.startswith(('http://', 'https://')):
        # Already a URL
        return image_url
    else:
        # For local files, we need a public URL
        logger.error(f"Local image file requires public URL. Please upload {image_url} to a hosting service.")
        raise ValueError(
            f"Instagram requires publicly accessible URLs for all media. "
            f"Please upload your media to a hosting service (S3, Cloudinary, etc.) and provide the URL."
        )


def post_to_instagram_via_fb():
    """Main function to post content to Instagram via Facebook Graph API."""
    # Setup logging
    log_level = get_optional_env_var("LOG_LEVEL", "INFO")
    logger = setup_logging(log_level)
    
    try:
        # Get required parameters
        ig_user_id = get_required_env_var("IG_USER_ID")
        fb_access_token = get_required_env_var("FB_ACCESS_TOKEN")
        content = get_required_env_var("POST_CONTENT")
        
        # Get media files
        media_input = get_optional_env_var("MEDIA_FILES", "")
        
        if not media_input:
            logger.error("MEDIA_FILES is required for Instagram posting")
            sys.exit(1)
        
        # Process templated content
        content, media_input = process_templated_contents(content, media_input)
        
        # Parse media files - for Instagram via FB, we handle URLs differently
        # Videos use resumable upload (local file or hosted URL), images need to stay as URLs
        if not media_input:
            logger.error("At least one media file is required for Instagram posting")
            sys.exit(1)
        
        media_files_raw = [f.strip() for f in media_input.split(',') if f.strip()]
        
        # Validate media files count
        if len(media_files_raw) > 10:
            logger.error("Instagram carousel posts support maximum 10 media files")
            sys.exit(1)
        
        # Validate content
        if not validate_post_content(content, max_length=2200):  # Instagram caption limit
            sys.exit(1)

        # Scheduling (local wait-until publish)
        scheduled_time_str = get_optional_env_var("SCHEDULED_PUBLISH_TIME", "")
        scheduled_publish_time = None
        scheduled_time_iso = None

        if scheduled_time_str:
            scheduled_time_iso = parse_scheduled_time(scheduled_time_str)
            if scheduled_time_iso:
                dt = datetime.fromisoformat(scheduled_time_iso.replace('Z', '+00:00'))
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                else:
                    dt = dt.astimezone(timezone.utc)
                scheduled_publish_time = int(dt.timestamp())
                logger.info(
                    "Post will be scheduled for: %s (Unix timestamp: %s)",
                    scheduled_time_iso,
                    scheduled_publish_time
                )
        
        # DRY RUN GUARD - Check before processing media files
        from social_media_utils import dry_run_guard
        media_details = []
        for i, media_file in enumerate(media_files_raw):
            file_ext = Path(media_file).suffix.lower()
            media_type = "VIDEO" if file_ext in ['.mp4', '.mov'] else "IMAGE"
            file_size = os.path.getsize(media_file) if os.path.exists(media_file) else 'N/A'
            media_details.append({
                'index': i + 1,
                'path': media_file,
                'filename': Path(media_file).name,
                'extension': file_ext,
                'size_bytes': file_size,
                'size_kb': round(file_size / 1024, 2) if file_size != 'N/A' else 'N/A',
                'type': media_type
            })
        
        dry_run_request = {
            'caption': content,
            'media_count': len(media_files_raw),
            'media_files': media_details,
            'is_carousel': len(media_files_raw) > 1,
            'upload_method': 'Resumable upload via rupload (videos) / Public URL (images)'
        }
        if scheduled_publish_time:
            dry_run_request['scheduled_for'] = scheduled_time_str
        dry_run_guard("Instagram (via Facebook)", content, media_files_raw, dry_run_request)
        
        # After dry run check, process media files for actual upload
        media_files = []
        for media_file in media_files_raw:
            file_ext = Path(media_file).suffix.lower()
            # Videos can be local files or URLs; images must be URLs
            if file_ext in ['.mp4', '.mov']:
                if not media_file.startswith(('http://', 'https://')):
                    if not os.path.exists(media_file):
                        logger.error(f"Video file not found: {media_file}")
                        sys.exit(1)
            else:
                # Image - must be URL
                if not media_file.startswith(('http://', 'https://')):
                    logger.error(
                        f"Images require publicly accessible URLs. "
                        f"Invalid media file: {media_file}\n"
                        f"Please upload your image to a hosting service (S3, Cloudinary, etc.) first."
                    )
                    sys.exit(1)
            media_files.append(media_file)
        
        # Create Instagram API client
        ig_api = InstagramFBAPI(fb_access_token, ig_user_id)
        
        # Process media files
        container_ids = []
        
        for i, media_file in enumerate(media_files):
            logger.info(f"Processing media file {i+1}/{len(media_files)}: {media_file}")
            
            file_ext = Path(media_file).suffix.lower()
            
            if file_ext in ['.mp4', '.mov']:
                # Video - always use resumable upload (local or hosted via file_url header)
                item_caption = content if len(media_files) == 1 else ""
                is_carousel_item = len(media_files) > 1

                logger.info("Uploading video via resumable flow: %s", media_file)
                container_id = ig_api.upload_video_resumable_with_carousel_flag(
                    media_file,
                    item_caption,
                    is_carousel_item=is_carousel_item
                )

                container_ids.append(container_id)

                # Wait for video processing
                logger.info("Waiting for video processing...")
                if not ig_api.check_container_status(container_id):
                    logger.error("Video processing failed or timed out")
                    sys.exit(1)

            else:
                # Image - create container with URL
                logger.info(f"Creating image container with URL: {media_file}")
                
                # For single image, use the caption; for carousel, don't use caption on individual items
                item_caption = content if len(media_files) == 1 else ""
                
                container_id = ig_api.create_image_container(media_file, item_caption)
                container_ids.append(container_id)
                
                # Wait a moment for container creation
                time.sleep(1)
        
        # Create carousel if multiple media files
        if len(container_ids) > 1:
            logger.info("Creating carousel container...")
            final_container_id = ig_api.create_carousel_container(container_ids, content)
        else:
            final_container_id = container_ids[0]
        
        # Wait before publishing (Instagram recommendation + optional scheduling)
        logger.info("Waiting before publishing...")
        time.sleep(2)

        if scheduled_publish_time:
            now_ts = int(time.time())
            wait_seconds = scheduled_publish_time - now_ts
            if wait_seconds > 0:
                logger.info(
                    "Scheduling enabled. Waiting %s seconds until %s before publishing...",
                    wait_seconds,
                    scheduled_time_iso
                )
                time.sleep(wait_seconds)
            else:
                logger.info(
                    "Scheduled time %s already passed (diff=%ss). Publishing now...",
                    scheduled_time_iso,
                    wait_seconds
                )
        
        # Publish media
        logger.info("Publishing media...")
        media_id = ig_api.publish_media(final_container_id)
        
        # Get media info for URL
        try:
            media_info = ig_api.get_media_info(media_id)
            post_url = media_info.get("permalink", f"https://www.instagram.com/p/{media_id}/")
        except:
            post_url = f"https://www.instagram.com/p/{media_id}/"
        
        # Output for GitHub Actions
        if 'GITHUB_OUTPUT' in os.environ:
            with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
                f.write(f"post-id={media_id}\n")
                f.write(f"post-url={post_url}\n")
                if scheduled_publish_time:
                    f.write(f"scheduled-time={scheduled_time_str}\n")
        
        log_success("Instagram (via Facebook)", media_id)
        logger.info(f"Post URL: {post_url}")
        if scheduled_publish_time:
            logger.info(f"Post scheduled for: {scheduled_time_str}")
        
    except Exception as e:
        handle_api_error(e, "Instagram (via Facebook)")


if __name__ == "__main__":
    post_to_instagram_via_fb()
