#!/usr/bin/env python3
"""
Post content to Instagram using Facebook Graph API with resumable upload.

This script uses the Instagram Graph API (via Facebook) to post content to Instagram,
with support for uploading local media files directly to Meta's servers using resumable upload for videos.
"""

import os
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
    download_file_if_url
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
    
    def upload_video_resumable(self, video_path, caption):
        """
        Upload a video using resumable upload (start/transfer/finish flow).
        
        Args:
            video_path: Path to local video file
            caption: Video caption
            
        Returns:
            container_id: Media container ID ready for publishing
        """
        video_size = os.path.getsize(video_path)
        logger.info(f"Uploading video {video_path} (size: {video_size} bytes) using resumable upload")
        
        # Step 1: Start upload session
        logger.info("Step 1: Starting upload session...")
        start_data = {
            'media_type': 'REELS',  # Use REELS for videos
            'caption': caption,
            'upload_phase': 'start',
            'file_size': str(video_size)
        }
        
        start_response = self._make_request('POST', f"{self.ig_user_id}/media", data=start_data)
        upload_session_id = start_response.get('upload_session_id')
        video_id = start_response.get('id')
        
        if not upload_session_id:
            raise RuntimeError(f"Failed to get upload_session_id from start phase: {start_response}")
        
        logger.info(f"Upload session started: session_id={upload_session_id}, video_id={video_id}")
        
        # Step 2: Transfer video data in chunks
        logger.info("Step 2: Transferring video data in chunks...")
        # Use 4MB chunks - recommended chunk size for video uploads
        chunk_size = 1024 * 1024 * 4  # 4MB chunks
        start_offset = 0
        
        try:
            with open(video_path, 'rb') as video_file:
                while start_offset < video_size:
                    # Read chunk
                    video_file.seek(start_offset)
                    chunk = video_file.read(chunk_size)
                    
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
                    transfer_response = self._make_request(
                        'POST',
                        f"{self.ig_user_id}/media",
                        data=transfer_data,
                        files={'video_file_chunk': chunk},
                        timeout=300  # 5 minutes for chunk upload
                    )
                    
                    logger.debug(f"Chunk upload response: {transfer_response}")
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
        
        finish_response = self._make_request(
            'POST',
            f"{self.ig_user_id}/media",
            data=finish_data
        )
        
        logger.info(f"Video upload completed successfully: {finish_response}")
        
        # Return the container ID (video_id from start phase)
        return video_id
    
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
        Check the status of a media container and wait until it's ready.
        
        Args:
            container_id: Media container ID
            max_wait: Maximum time to wait in seconds
            
        Returns:
            bool: True if container is ready, False otherwise
        """
        logger.info(f"Checking status of container {container_id}")
        
        start_time = time.time()
        while time.time() - start_time < max_wait:
            response = self._make_request(
                'GET',
                container_id,
                params={'fields': 'status_code,status'}
            )
            
            status_code = response.get('status_code')
            status = response.get('status')
            
            logger.debug(f"Container status: {status_code} - {status}")
            
            if status_code == 'FINISHED':
                logger.info("Container is ready for publishing")
                return True
            elif status_code == 'ERROR':
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


def upload_image_to_temp_hosting(image_path):
    """
    Upload image to a temporary hosting service to get a public URL.
    
    Note: For production use, you should upload to your own hosting service (S3, CDN, etc.).
    This function serves as a placeholder and requires the image to already be accessible via URL.
    
    Args:
        image_path: Path to local image file or URL
        
    Returns:
        str: Public URL to the image
    """
    if image_path.startswith(('http://', 'https://')):
        # Already a URL
        return image_path
    else:
        # For local files, we need a public URL
        # In production, upload to S3, Cloudinary, or similar service
        logger.error(f"Local image file requires public URL. Please upload {image_path} to a hosting service.")
        raise ValueError(
            f"Instagram requires publicly accessible URLs for images. "
            f"Please upload your image to a hosting service (S3, Cloudinary, etc.) and provide the URL, "
            f"or use the MEDIA_FILES environment variable with HTTP/HTTPS URLs."
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
        # Videos will be uploaded directly, images need to stay as URLs
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
            'upload_method': 'FB Resumable Upload (videos) / Public URL (images)'
        }
        dry_run_guard("Instagram (via Facebook)", content, media_files_raw, dry_run_request)
        
        # After dry run check, process media files for actual upload
        media_files = []
        for media_file in media_files_raw:
            # Download videos for resumable upload, keep image URLs as-is
            file_ext = Path(media_file).suffix.lower()
            if file_ext in ['.mp4', '.mov']:
                # Video - download if it's a URL
                if media_file.startswith(('http://', 'https://')):
                    # Download video for resumable upload
                    max_download_mb = int(get_optional_env_var("MAX_DOWNLOAD_SIZE_MB", "500"))
                    media_file = download_file_if_url(media_file, max_download_mb)
                if not os.path.exists(media_file):
                    logger.error(f"Video file not found: {media_file}")
                    sys.exit(1)
            else:
                # Image - must be a URL (Instagram Graph API requirement)
                if not media_file.startswith(('http://', 'https://')):
                    logger.error(f"Image file must be a publicly accessible URL: {media_file}")
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
                # Video - use resumable upload
                logger.info(f"Uploading video using resumable upload: {media_file}")
                
                # For single video, use the caption; for carousel, don't use caption on individual items
                item_caption = content if len(media_files) == 1 else ""
                
                container_id = ig_api.upload_video_resumable(media_file, item_caption)
                container_ids.append(container_id)
                
                # Wait for video processing
                logger.info("Waiting for video processing...")
                if not ig_api.check_container_status(container_id):
                    logger.error("Video processing failed or timed out")
                    sys.exit(1)
                
            else:
                # Image - need public URL
                logger.info(f"Processing image: {media_file}")
                
                # Get public URL (either from URL input or upload to hosting)
                image_url = upload_image_to_temp_hosting(media_file)
                
                # For single image, use the caption; for carousel, don't use caption on individual items
                item_caption = content if len(media_files) == 1 else ""
                
                container_id = ig_api.create_image_container(image_url, item_caption)
                container_ids.append(container_id)
                
                # Wait a moment for container creation
                time.sleep(1)
        
        # Create carousel if multiple media files
        if len(container_ids) > 1:
            logger.info("Creating carousel container...")
            final_container_id = ig_api.create_carousel_container(container_ids, content)
        else:
            final_container_id = container_ids[0]
        
        # Wait before publishing (Instagram recommendation)
        logger.info("Waiting before publishing...")
        time.sleep(2)
        
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
        
        log_success("Instagram (via Facebook)", media_id)
        logger.info(f"Post URL: {post_url}")
        
    except Exception as e:
        handle_api_error(e, "Instagram (via Facebook)")


if __name__ == "__main__":
    post_to_instagram_via_fb()
