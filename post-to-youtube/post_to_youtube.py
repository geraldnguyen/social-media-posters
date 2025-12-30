#!/usr/bin/env python3
"""
Upload videos and posts to YouTube using the YouTube Data API v3.
"""

import os
import sys
from pathlib import Path

# Load environment variables from a local .env file if present (for local development)
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent / '.env'
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
except ImportError:
    pass  # python-dotenv is not installed; skip loading .env

import logging
import json
import io
from datetime import datetime
from typing import Optional, Dict, Any

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
    dry_run_guard
)

# Google API imports
from google.oauth2 import service_account
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload, MediaIoBaseUpload
import requests


class YouTubeAPI:
    """YouTube Data API v3 client."""
    
    def __init__(self, credentials_json: Optional[str] = None, api_key: Optional[str] = None,
                 oauth_client_id: Optional[str] = None, oauth_client_secret: Optional[str] = None,
                 oauth_refresh_token: Optional[str] = None, oauth_scopes: Optional[list] = None):
        """
        Initialize YouTube API client.
        
        Args:
            credentials_json: Path to service account credentials JSON file or JSON string
            api_key: YouTube Data API key (alternative to service account)
            oauth_client_id: OAuth 2.0 Client ID (for refresh token authentication)
            oauth_client_secret: OAuth 2.0 Client Secret (for refresh token authentication)
            oauth_refresh_token: OAuth 2.0 Refresh Token (for refresh token authentication)
            oauth_scopes: OAuth 2.0 scopes (defaults to ['https://www.googleapis.com/auth/youtube'])
        """
        self.youtube = None
        
        # Default OAuth scopes if not provided
        if oauth_scopes is None:
            oauth_scopes = ['https://www.googleapis.com/auth/youtube']
        
        # Option 1: OAuth Refresh Token authentication (preferred for user-based access)
        if oauth_refresh_token and oauth_client_id and oauth_client_secret:
            logging.info("Authenticating with OAuth refresh token")
            logging.info(f"Using OAuth scopes: {oauth_scopes}")
            credentials = Credentials(
                token=None,  # Will be obtained from refresh token
                refresh_token=oauth_refresh_token,
                token_uri='https://oauth2.googleapis.com/token',
                client_id=oauth_client_id,
                client_secret=oauth_client_secret,
                scopes=oauth_scopes
            )
            
            # Refresh the token to get a valid access token
            try:
                credentials.refresh(Request())
                self.youtube = build('youtube', 'v3', credentials=credentials)
                logging.info("Successfully authenticated with OAuth refresh token")
            except Exception as e:
                logging.error(f"Failed to refresh OAuth token: {e}")
                raise ValueError(f"Failed to authenticate with OAuth refresh token: {e}")
        
        # Option 2: Service Account authentication
        elif credentials_json:
            logging.info(f"Using OAuth scopes: {oauth_scopes}")
            # Try to parse as JSON string first
            try:
                creds_data = json.loads(credentials_json)
                credentials = service_account.Credentials.from_service_account_info(
                    creds_data,
                    scopes=oauth_scopes
                )
                self.youtube = build('youtube', 'v3', credentials=credentials)
                logging.info("Initialized YouTube API with service account credentials")
            except json.JSONDecodeError:
                # Treat as file path
                if os.path.exists(credentials_json):
                    credentials = service_account.Credentials.from_service_account_file(
                        credentials_json,
                        scopes=oauth_scopes
                    )
                    self.youtube = build('youtube', 'v3', credentials=credentials)
                    logging.info("Initialized YouTube API with service account credentials from file")
                else:
                    raise ValueError("credentials_json is not valid JSON or file path")
        elif api_key:
            # Use API key (limited functionality)
            self.youtube = build('youtube', 'v3', developerKey=api_key)
            logging.info("Initialized YouTube API with API key (limited functionality)")
        else:
            raise ValueError(
                "Authentication required. Provide one of:\n"
                "  - OAuth refresh token (oauth_refresh_token + oauth_client_id + oauth_client_secret)\n"
                "  - Service account credentials (credentials_json)\n"
                "  - API key (api_key, limited functionality)"
            )
    
    def upload_video(self,
                    video_file: str,
                    title: str,
                    description: str = "",
                    tags: Optional[list] = None,
                    category_id: str = "22",
                    privacy_status: str = "public",
                    publish_at: Optional[str] = None,
                    made_for_kids: bool = False,
                    embeddable: bool = True,
                    license_type: str = "youtube",
                    public_stats_viewable: bool = True,
                    contains_synthetic_media: Optional[bool] = None) -> Dict[str, Any]:
        """
        Upload a video to YouTube.
        
        Args:
            video_file: Path to video file
            title: Video title
            description: Video description
            tags: List of video tags
            category_id: Video category ID
            privacy_status: Privacy status (public, private, unlisted)
            publish_at: Scheduled publish time (ISO 8601 format)
            made_for_kids: Whether video is made for kids
            embeddable: Whether video is embeddable
            license_type: Video license (youtube or creativeCommon)
            public_stats_viewable: Whether stats are publicly viewable
            contains_synthetic_media: Whether video contains synthetic/altered media (AI-generated, deepfakes, etc.)
            
        Returns:
            Dict with video information including ID and URL
        """
        logging.info(f"Uploading video: {video_file}")
        
        # Build the request body
        body = {
            'snippet': {
                'title': title,
                'description': description,
                'categoryId': category_id
            },
            'status': {
                'privacyStatus': privacy_status,
                'selfDeclaredMadeForKids': made_for_kids,
                'embeddable': embeddable,
                'license': license_type,
                'publicStatsViewable': public_stats_viewable
            }
        }
        
        # Add containsSyntheticMedia if specified
        if contains_synthetic_media is not None:
            body['status']['containsSyntheticMedia'] = contains_synthetic_media
            logging.info(f"Set containsSyntheticMedia to {contains_synthetic_media}")
        
        # Add tags if provided
        if tags:
            body['snippet']['tags'] = tags
        
        # Add scheduled publish time if provided
        if publish_at:
            # Validate that privacy_status is 'private' for scheduling
            if privacy_status != 'private':
                logging.warning("Scheduled publishing requires privacy_status to be 'private'. Setting to 'private'.")
                body['status']['privacyStatus'] = 'private'
            body['status']['publishAt'] = publish_at
            logging.info(f"Video scheduled to publish at: {publish_at}")
        
        logging.debug(f"Request body: {json.dumps(body, indent=2)}")
        
        # Prepare media upload
        media = MediaFileUpload(video_file, chunksize=-1, resumable=True)
        
        # Execute the upload
        try:
            request = self.youtube.videos().insert(
                part='snippet,status',
                body=body,
                media_body=media
            )
            
            logging.info("Starting video upload...")
            response = None
            while response is None:
                status, response = request.next_chunk()
                if status:
                    progress = int(status.progress() * 100)
                    logging.info(f"Upload progress: {progress}%")
            
            video_id = response['id']
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            
            logging.info(f"Video uploaded successfully. ID: {video_id}")
            logging.info(f"Video URL: {video_url}")
            
            return {
                'id': video_id,
                'url': video_url,
                'title': title,
                'privacy_status': body['status']['privacyStatus']
            }
            
        except HttpError as e:
            logging.error(f"An HTTP error {e.resp.status} occurred:")
            logging.error(f"Error details: {e.content}")
            raise
    
    def upload_thumbnail(self, video_id: str, thumbnail_file: str) -> None:
        """
        Upload a custom thumbnail for a video.
        
        Args:
            video_id: Video ID
            thumbnail_file: Path to thumbnail image file
        """
        logging.info(f"Uploading thumbnail for video {video_id}: {thumbnail_file}")
        
        try:
            media = MediaFileUpload(thumbnail_file)
            request = self.youtube.thumbnails().set(
                videoId=video_id,
                media_body=media
            )
            response = request.execute()
            logging.info(f"Thumbnail uploaded successfully")
            logging.debug(f"Response: {json.dumps(response, indent=2)}")
        except HttpError as e:
            logging.error(f"An HTTP error {e.resp.status} occurred while uploading thumbnail:")
            logging.error(f"Error details: {e.content}")
            raise
    
    def add_video_to_playlist(self, video_id: str, playlist_id: str) -> None:
        """
        Add a video to a playlist.
        
        Args:
            video_id: Video ID
            playlist_id: Playlist ID
        """
        logging.info(f"Adding video {video_id} to playlist {playlist_id}")
        
        try:
            request = self.youtube.playlistItems().insert(
                part='snippet',
                body={
                    'snippet': {
                        'playlistId': playlist_id,
                        'resourceId': {
                            'kind': 'youtube#video',
                            'videoId': video_id
                        }
                    }
                }
            )
            response = request.execute()
            logging.info(f"Video added to playlist successfully")
            logging.debug(f"Response: {json.dumps(response, indent=2)}")
        except HttpError as e:
            logging.error(f"An HTTP error {e.resp.status} occurred while adding to playlist:")
            logging.error(f"Error details: {e.content}")
            raise


def post_to_youtube():
    """Main function to post content to YouTube."""
    # Setup logging
    log_level = get_optional_env_var("LOG_LEVEL", "INFO")
    logger = setup_logging(log_level)
    
    try:
        # Get API credentials - multiple options supported
        credentials_json = get_optional_env_var("YOUTUBE_API_KEY", "")
        oauth_client_id = get_optional_env_var("YOUTUBE_OAUTH_CLIENT_ID", "")
        oauth_client_secret = get_optional_env_var("YOUTUBE_OAUTH_CLIENT_SECRET", "")
        oauth_refresh_token = get_optional_env_var("YOUTUBE_OAUTH_REFRESH_TOKEN", "")
        
        # Get OAuth scopes (optional, defaults to youtube scope)
        oauth_scopes_str = get_optional_env_var("YOUTUBE_OAUTH_SCOPES", "")
        oauth_scopes = None
        if oauth_scopes_str:
            oauth_scopes = [scope.strip() for scope in oauth_scopes_str.split(',') if scope.strip()]
            logging.info(f"Using custom OAuth scopes: {oauth_scopes}")
        
        # Determine what we're doing - video upload or community post
        video_file = get_optional_env_var("VIDEO_FILE", "")
        content = get_optional_env_var("POST_CONTENT", "")
        
        if not video_file and not content:
            logging.error("Either VIDEO_FILE or POST_CONTENT must be provided")
            sys.exit(1)
        
        # Process templated content
        title = get_optional_env_var("VIDEO_TITLE", "")
        description = get_optional_env_var("VIDEO_DESCRIPTION", "")
        
        # Process all templated strings using the same JSON root
        title, description, content = process_templated_contents(title, description, content)
        
        if video_file:
            # VIDEO UPLOAD MODE
            if not title:
                logging.error("VIDEO_TITLE is required for video uploads")
                sys.exit(1)
            
            # Download video if it's a URL
            logging.info(f"Preparing video file: {video_file}")
            local_video_file = download_file_if_url(video_file, max_download_size_mb=500)  # Allow larger downloads for videos
            
            if not os.path.exists(local_video_file):
                logging.error(f"Video file not found: {video_file}")
                sys.exit(1)
            
            # Get video metadata
            tags_str = get_optional_env_var("VIDEO_TAGS", "")
            tags = [tag.strip() for tag in tags_str.split(',') if tag.strip()] if tags_str else []
            
            category_id = get_optional_env_var("VIDEO_CATEGORY_ID", "22")
            privacy_status = get_optional_env_var("VIDEO_PRIVACY_STATUS", "public")
            publish_at = get_optional_env_var("VIDEO_PUBLISH_AT", "")
            
            # Get video settings
            made_for_kids = get_optional_env_var("VIDEO_MADE_FOR_KIDS", "false").lower() in ('true', '1', 'yes')
            embeddable = get_optional_env_var("VIDEO_EMBEDDABLE", "true").lower() in ('true', '1', 'yes')
            license_type = get_optional_env_var("VIDEO_LICENSE", "youtube")
            public_stats_viewable = get_optional_env_var("VIDEO_PUBLIC_STATS_VIEWABLE", "true").lower() in ('true', '1', 'yes')
            
            # Get contains_synthetic_media setting (optional)
            contains_synthetic_media_str = get_optional_env_var("VIDEO_CONTAINS_SYNTHETIC_MEDIA", "")
            contains_synthetic_media = None
            if contains_synthetic_media_str:
                contains_synthetic_media = contains_synthetic_media_str.lower() in ('true', '1', 'yes')
            
            # Get optional parameters
            thumbnail_file = get_optional_env_var("VIDEO_THUMBNAIL", "")
            playlist_id = get_optional_env_var("PLAYLIST_ID", "")
            
            # Download thumbnail if provided (do this once to reuse later)
            thumbnail_local = None
            if thumbnail_file:
                thumbnail_local = download_file_if_url(thumbnail_file, max_download_size_mb=2)
            
            # Prepare dry run data
            video_size = os.path.getsize(local_video_file)
            dry_run_request = {
                'action': 'upload_video',
                'video_file': local_video_file,
                'video_filename': os.path.basename(local_video_file),
                'video_size_bytes': video_size,
                'video_size_mb': round(video_size / (1024 * 1024), 2),
                'title': title,
                'title_length': len(title),
                'description': description,
                'description_length': len(description),
                'tags': tags,
                'category_id': category_id,
                'privacy_status': privacy_status,
                'made_for_kids': made_for_kids,
                'embeddable': embeddable,
                'license': license_type,
                'public_stats_viewable': public_stats_viewable
            }
            
            if publish_at:
                dry_run_request['scheduled_publish_at'] = publish_at
            
            if thumbnail_local and os.path.exists(thumbnail_local):
                thumbnail_size = os.path.getsize(thumbnail_local)
                dry_run_request['thumbnail_file'] = thumbnail_local
                dry_run_request['thumbnail_size_kb'] = round(thumbnail_size / 1024, 2)
            
            if playlist_id:
                dry_run_request['playlist_id'] = playlist_id
            
            # DRY RUN GUARD
            dry_run_guard("YouTube", f"Video: {title}", [local_video_file], dry_run_request)
            
            # Create YouTube API client with appropriate authentication
            api = YouTubeAPI(
                credentials_json=credentials_json or None,
                oauth_client_id=oauth_client_id or None,
                oauth_client_secret=oauth_client_secret or None,
                oauth_refresh_token=oauth_refresh_token or None,
                oauth_scopes=oauth_scopes
            )
            
            # Upload the video
            result = api.upload_video(
                video_file=local_video_file,
                title=title,
                description=description,
                tags=tags,
                category_id=category_id,
                privacy_status=privacy_status,
                publish_at=publish_at if publish_at else None,
                made_for_kids=made_for_kids,
                embeddable=embeddable,
                license_type=license_type,
                public_stats_viewable=public_stats_viewable,
                contains_synthetic_media=contains_synthetic_media
            )
            
            video_id = result['id']
            video_url = result['url']
            
            # Upload thumbnail if provided (reuse already downloaded file)
            if thumbnail_local and os.path.exists(thumbnail_local):
                try:
                    api.upload_thumbnail(video_id, thumbnail_local)
                except Exception as e:
                    logging.warning(f"Failed to upload thumbnail: {e}")
            
            # Add to playlist if provided
            if playlist_id:
                try:
                    api.add_video_to_playlist(video_id, playlist_id)
                except Exception as e:
                    logging.warning(f"Failed to add video to playlist: {e}")
            
            # Output for GitHub Actions
            if 'GITHUB_OUTPUT' in os.environ:
                with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
                    f.write(f"video-id={video_id}\n")
                    f.write(f"video-url={video_url}\n")
            
            log_success("YouTube", video_id)
            logger.info(f"Video URL: {video_url}")
            
        else:
            # COMMUNITY POST MODE (Note: Community posts via API are limited)
            logging.warning("Community posts are not fully supported via YouTube Data API v3")
            logging.warning("Please use the YouTube Studio interface for community posts")
            sys.exit(1)
        
    except Exception as e:
        handle_api_error(e, "YouTube")


if __name__ == "__main__":
    post_to_youtube()
