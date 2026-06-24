#!/usr/bin/env python3
"""
Upload videos to Dailymotion using the Dailymotion API.
"""

import os
import sys
import json
import logging
import requests
from pathlib import Path
from typing import Optional, Dict, Any, List

# Module-level logger
logger = logging.getLogger(__name__)

# Load environment variables from a local .env file if present (for local development)
try:
    from dotenv import load_dotenv
    env_path = Path.cwd() / '.env'
    
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
except ImportError:
    pass

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
    download_file_if_url,
    dry_run_guard,
    parse_scheduled_time,
    save_post_response,
)

class DailymotionAPI:
    """Dailymotion API client."""
    
    def __init__(self, client_id: str, client_secret: str, refresh_token: str, channel_id: Optional[str] = None):
        """Initialize Dailymotion API client with refresh token flow."""
        self.client_id = client_id
        self.client_secret = client_secret
        self.refresh_token = refresh_token
        self.channel_id = channel_id or "me"
        self.access_token = None
        self.api_base_url = "https://api.dailymotion.com"
        
    def authenticate(self):
        """Authenticate using refresh token grant type."""
        logger.info("Refreshing Dailymotion access token")
        url = f"{self.api_base_url}/oauth/token"
        data = {
            "grant_type": "refresh_token",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": self.refresh_token
        }
        
        try:
            response = requests.post(url, data=data, timeout=30)
            logger.debug(f"Dailymotion auth response: {response.status_code} - {response.text}")
            response.raise_for_status()
            auth_data = response.json()
            self.access_token = auth_data.get("access_token")
            # Update refresh token if a new one is provided
            if auth_data.get("refresh_token"):
                self.refresh_token = auth_data.get("refresh_token")
            logger.info("Successfully refreshed Dailymotion access token")
        except Exception as e:
            logger.error(f"Failed to refresh Dailymotion access token: {e}")
            raise

    def get_headers(self):
        """Get request headers with access token."""
        if not self.access_token:
            self.authenticate()
        return {"Authorization": f"Bearer {self.access_token}"}

    def get_upload_url(self) -> str:
        """Get an upload URL for the video file."""
        logger.info("Getting Dailymotion upload URL")
        url = f"{self.api_base_url}/file/upload"
        
        try:
            response = requests.get(url, headers=self.get_headers(), timeout=30)
            logger.debug(f"Dailymotion get_upload_url response: {response.status_code} - {response.text}")
            response.raise_for_status()
            return response.json().get("upload_url")
        except Exception as e:
            logger.error(f"Failed to get Dailymotion upload URL: {e}")
            raise

    def upload_file(self, upload_url: str, file_path: str) -> str:
        """Upload the video file to the provided upload URL."""
        logger.info(f"Uploading file to Dailymotion: {file_path}")
        
        try:
            with open(file_path, 'rb') as f:
                files = {'file': f}
                response = requests.post(upload_url, files=files, timeout=300) # Longer timeout for upload
                logger.debug(f"Dailymotion upload_file response: {response.status_code} - {response.text}")
                response.raise_for_status()
                return response.json().get("url")
        except Exception as e:
            logger.error(f"Failed to upload file to Dailymotion: {e}")
            raise

    def create_video(self, file_url: str, metadata: Dict[str, Any]) -> str:
        """Create a video object on Dailymotion."""
        logger.info(f"Creating video object on Dailymotion")
        
        # Standard API endpoint
        url = f"{self.api_base_url}/me/videos"
            
        logger.debug(f"Creating video at URL: {url}")
        
        data = {
            "url": file_url,
            "published": "true" if metadata.get("published", True) else "false"
        }
        
        # Add metadata fields
        for key, value in metadata.items():
            if key != "published":
                data[key] = value
        
        try:
            response = requests.post(url, headers=self.get_headers(), data=data, timeout=30)
            logger.debug(f"Dailymotion create_video response: {response.status_code} - {response.text}")
            response.raise_for_status()
            video_id = response.json().get("id")
            logger.info(f"Video created successfully. ID: {video_id}")
            return video_id
        except Exception as e:
            logger.error(f"Failed to create video on Dailymotion at {url}: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.debug(f"Error response body: {e.response.text}")
            raise

    def add_to_playlist(self, playlist_id: str, video_id: str) -> None:
        """Add a video to a playlist."""
        logger.info(f"Adding video {video_id} to playlist: {playlist_id}")
        url = f"{self.api_base_url}/playlist/{playlist_id}/videos/{video_id}"

        try:
            response = requests.post(url, headers=self.get_headers(), timeout=30)
            logger.debug(f"Dailymotion add_to_playlist response: {response.status_code} - {response.text}")
            response.raise_for_status()
            logger.info(f"Video successfully added to playlist {playlist_id}")
        except Exception as e:
            logger.error(f"Failed to add video to Dailymotion playlist: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.debug(f"Error response body: {e.response.text}")
            raise

    def update_video(self, video_id: str, metadata: Dict[str, Any]) -> None:
        """Update video metadata."""
        logger.info(f"Updating video metadata for ID: {video_id}")
        url = f"{self.api_base_url}/video/{video_id}"
        
        try:
            response = requests.post(url, headers=self.get_headers(), data=metadata, timeout=30)
            logger.debug(f"Dailymotion update_video response: {response.status_code} - {response.text}")
            response.raise_for_status()
            logger.info(f"Video updated successfully")
        except Exception as e:
            logger.error(f"Failed to update video on Dailymotion: {e}")
            raise

    def post_comment(self, video_id: str, message: str) -> Optional[str]:
        """Post a comment on a Dailymotion video.

        Args:
            video_id: Dailymotion video ID
            message: Comment text

        Returns:
            Comment ID if available
        """
        logger.info(f"Posting comment on Dailymotion video {video_id}")
        url = f"{self.api_base_url}/video/{video_id}/comments"
        data = {"message": message}
        try:
            response = requests.post(url, headers=self.get_headers(), data=data, timeout=30)
            logger.debug(f"Dailymotion post_comment response: {response.status_code} - {response.text}")
            response.raise_for_status()
            comment_id = response.json().get("id")
            logger.info(f"Comment posted successfully. ID: {comment_id}")
            return comment_id
        except Exception as e:
            logger.error(f"Failed to post comment on Dailymotion video {video_id}: {e}")
            raise

def post_to_dailymotion():
    """Main function to post content to Dailymotion."""
    # Setup logging
    log_level = get_optional_env_var("LOG_LEVEL", "INFO")
    logger_setup = setup_logging(log_level)
    logger_setup.info("Starting Dailymotion post process")
    
    try:
        # Get API credentials
        client_id = get_required_env_var("DAILYMOTION_CLIENT_ID")
        client_secret = get_required_env_var("DAILYMOTION_CLIENT_SECRET")
        refresh_token = get_required_env_var("DAILYMOTION_REFRESH_TOKEN")
        channel_id = get_optional_env_var("DAILYMOTION_CHANNEL_ID", "me")
        playlist_id = get_optional_env_var("DAILYMOTION_PLAYLIST_ID", "")
        
        # Get video details
        video_file = get_required_env_var("VIDEO_FILE")
        title = get_optional_env_var("VIDEO_TITLE", "")
        description = get_optional_env_var("VIDEO_DESCRIPTION", "")
        
        # Process templated content
        title, description = process_templated_contents(title, description)
        
        if not title:
            logger.error("VIDEO_TITLE is required for Dailymotion uploads")
            sys.exit(1)
            
        # Get more metadata
        channel = get_required_env_var("DAILYMOTION_CHANNEL") # Category
        is_created_for_kids = get_optional_env_var("VIDEO_MADE_FOR_KIDS", "false").lower() in ('true', '1', 'yes')
        tags_str = get_optional_env_var("VIDEO_TAGS", "")
        tags = [tag.strip() for tag in tags_str.split(',') if tag.strip()] if tags_str else []
        
        # Scheduling
        publish_at_str = get_optional_env_var("VIDEO_PUBLISH_AT", "")
        publish_at = None
        if publish_at_str:
            publish_at = parse_scheduled_time(publish_at_str)
            logger.info(f"Video will be scheduled for: {publish_at}")

        # Download video if it's a URL
        logger.info(f"Preparing video file: {video_file}")
        local_video_file = download_file_if_url(video_file, max_download_size_mb=500)
        
        if not os.path.exists(local_video_file):
            logger.error(f"Video file not found: {video_file}")
            sys.exit(1)
            
        # Metadata for Dailymotion
        metadata = {
            "title": title,
            "description": description,
            "channel": channel,
            "is_created_for_kids": "true" if is_created_for_kids else "false",
            "published": True
        }
        
        if tags:
            metadata["tags"] = ",".join(tags)
            
        if publish_at:
            # Dailymotion uses Unix timestamp for 'publish_date'
            from datetime import datetime
            dt = datetime.fromisoformat(publish_at.replace('Z', '+00:00'))
            metadata["published"] = False
            metadata["publish_date"] = int(dt.timestamp())

        # Prepare dry run data
        video_size = os.path.getsize(local_video_file)
        dry_run_request = {
            'action': 'upload_video',
            'video_file': local_video_file,
            'video_filename': os.path.basename(local_video_file),
            'video_size_bytes': video_size,
            'title': title,
            'description': description,
            'channel': channel,
            'is_created_for_kids': is_created_for_kids,
            'tags': tags,
            'published': metadata["published"],
            'channel_id': channel_id,
            'playlist_id': playlist_id
        }
        if publish_at:
            dry_run_request['publish_date'] = metadata["publish_date"]
            dry_run_request['scheduled_publish_at'] = publish_at

        # Get link-in-comment options before dry run guard
        link_in_comment = get_optional_env_var("LINK_IN_COMMENT", "")
        pin_link_comment = get_optional_env_var("PIN_LINK_COMMENT", "").lower() in ('1', 'true', 'yes')
        if link_in_comment:
            dry_run_request['link_in_comment'] = link_in_comment
            dry_run_request['pin_link_comment'] = pin_link_comment

        # DRY RUN GUARD
        dry_run_guard("Dailymotion", f"Video: {title}", [local_video_file], dry_run_request)
        
        # Create API client
        api = DailymotionAPI(client_id, client_secret, refresh_token, channel_id)
        
        # Step 1: Get upload URL
        upload_url = api.get_upload_url()
        
        # Step 2: Upload file
        file_url = api.upload_file(upload_url, local_video_file)
        
        # Step 3: Create video
        video_id = api.create_video(file_url, metadata)
        
        # Step 4: Add to playlist if requested
        if playlist_id:
            api.add_to_playlist(playlist_id, video_id)
        
        # Output for GitHub Actions
        video_url = f"https://www.dailymotion.com/video/{video_id}"
        if 'GITHUB_OUTPUT' in os.environ:
            with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
                f.write(f"video-id={video_id}\n")
                f.write(f"video-url={video_url}\n")
        
        save_post_response("dailymotion", success=True, post_id=video_id, post_url=video_url)
        log_success("Dailymotion", video_id)
        logger.info(f"Video URL: {video_url}")

        # Post link as a comment if LINK_IN_COMMENT is set
        if link_in_comment:
            logger.info(f"Posting link as comment on Dailymotion video {video_id}: {link_in_comment}")
            try:
                comment_id = api.post_comment(video_id, link_in_comment)
                logger.info(f"Link comment posted successfully. Comment ID: {comment_id}")
                if pin_link_comment:
                    logger.warning("Pinning comments is not supported by the Dailymotion API.")
            except Exception as comment_exc:
                logger.warning(f"Failed to post link as comment on Dailymotion: {comment_exc}")
        
    except Exception as e:
        save_post_response("dailymotion", success=False, error=str(e))
        handle_api_error(e, "Dailymotion")

if __name__ == "__main__":
    post_to_dailymotion()
