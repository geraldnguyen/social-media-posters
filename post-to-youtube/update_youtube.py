#!/usr/bin/env python3
"""
Update YouTube video metadata using the YouTube Data API v3.
"""

import os
import sys
from pathlib import Path

# Module-level logger
import logging
logger = logging.getLogger(__name__)

# Load environment variables from a local .env file if present (for local development)
try:
    from dotenv import load_dotenv
    env_path = Path.cwd() / '.env'
    
    if env_path.exists():
        logging.warning(f"Loading environment variables from {env_path}")
        load_dotenv(dotenv_path=env_path)
except ImportError:
    pass  # python-dotenv is not installed; skip loading .env


import json
from typing import Optional, Dict, Any

# Add common module to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'common'))

from templating_utils import process_templated_contents
from social_media_utils import (
    setup_logging,
    get_required_env_var,
    get_optional_env_var,
    handle_api_error,
    log_success,
    dry_run_guard,
    is_value_empty_or_na
)

# Google API imports
from google.oauth2 import service_account
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


class YouTubeUpdateAPI:
    """YouTube Data API v3 client for updating video metadata."""
    
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
        
        # Log the scopes being used
        logger.info(f"Using OAuth scopes: {oauth_scopes}")
        
        # Option 1: OAuth Refresh Token authentication (preferred for user-based access)
        if oauth_refresh_token and oauth_client_id and oauth_client_secret:
            logger.info("Authenticating with OAuth refresh token")
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
                logger.info("Successfully authenticated with OAuth refresh token")
            except Exception as e:
                logger.error(f"Failed to refresh OAuth token: {e}")
                raise ValueError(f"Failed to authenticate with OAuth refresh token: {e}")
        
        # Option 2: Service Account authentication
        elif credentials_json:
            # Try to parse as JSON string first
            try:
                creds_data = json.loads(credentials_json)
                credentials = service_account.Credentials.from_service_account_info(
                    creds_data,
                    scopes=oauth_scopes
                )
                self.youtube = build('youtube', 'v3', credentials=credentials)
                logger.info("Initialized YouTube API with service account credentials")
            except json.JSONDecodeError:
                # Treat as file path
                if os.path.exists(credentials_json):
                    credentials = service_account.Credentials.from_service_account_file(
                        credentials_json,
                        scopes=oauth_scopes
                    )
                    self.youtube = build('youtube', 'v3', credentials=credentials)
                    logger.info("Initialized YouTube API with service account credentials from file")
                else:
                    raise ValueError("credentials_json is not valid JSON or file path")
        elif api_key:
            # Use API key (limited functionality)
            self.youtube = build('youtube', 'v3', developerKey=api_key)
            logger.info("Initialized YouTube API with API key (limited functionality)")
        else:
            raise ValueError(
                "Authentication required. Provide one of:\n"
                "  - OAuth refresh token (oauth_refresh_token + oauth_client_id + oauth_client_secret)\n"
                "  - Service account credentials (credentials_json)\n"
                "  - API key (api_key, limited functionality)"
            )
    
    def get_video(self, video_id: str) -> Dict[str, Any]:
        """
        Get video details.
        
        Args:
            video_id: Video ID
            
        Returns:
            Dict with video information
        """
        logger.info(f"Fetching video details for: {video_id}")
        
        try:
            request = self.youtube.videos().list(
                part='snippet,status',
                id=video_id
            )
            response = request.execute()
            
            if not response.get('items'):
                raise ValueError(f"Video not found: {video_id}")
            
            return response['items'][0]
            
        except HttpError as e:
            logger.error(f"An HTTP error {e.resp.status} occurred:")
            logger.error(f"Error details: {e.content}")
            raise
    
    def update_video(self,
                    video_id: str,
                    title: Optional[str] = None,
                    description: Optional[str] = None,
                    tags: Optional[list] = None,
                    category_id: Optional[str] = None,
                    privacy_status: Optional[str] = None,
                    embeddable: Optional[bool] = None,
                    license_type: Optional[str] = None,
                    public_stats_viewable: Optional[bool] = None,
                    made_for_kids: Optional[bool] = None,
                    contains_synthetic_media: Optional[bool] = None) -> Dict[str, Any]:
        """
        Update video metadata.
        
        Args:
            video_id: Video ID to update
            title: New video title (optional)
            description: New video description (optional)
            tags: New list of video tags (optional)
            category_id: New video category ID (optional)
            privacy_status: New privacy status (public, private, unlisted) (optional)
            embeddable: New embeddable setting (optional)
            license_type: New video license (youtube or creativeCommon) (optional)
            public_stats_viewable: New public stats viewable setting (optional)
            made_for_kids: New made for kids setting (optional)
            contains_synthetic_media: New synthetic media flag (optional)
            
        Returns:
            Dict with updated video information
        """
        logger.info(f"Updating video: {video_id}")
        
        # First, get the current video details
        current_video = self.get_video(video_id)
        
        # Build the update request body by merging with current values
        body = {
            'id': video_id,
            'snippet': current_video['snippet'].copy(),
            'status': current_video['status'].copy()
        }
        
        # Update snippet fields if provided
        if title is not None:
            body['snippet']['title'] = title
            logger.info(f"Updating title to: {title}")
        
        if description is not None:
            body['snippet']['description'] = description
            logger.info(f"Updating description (length: {len(description)})")
        
        if tags is not None:
            body['snippet']['tags'] = tags
            logger.info(f"Updating tags to: {tags}")
        
        if category_id is not None:
            body['snippet']['categoryId'] = category_id
            logger.info(f"Updating category ID to: {category_id}")
        
        # Update status fields if provided
        if privacy_status is not None:
            body['status']['privacyStatus'] = privacy_status
            logger.info(f"Updating privacy status to: {privacy_status}")
        
        if embeddable is not None:
            body['status']['embeddable'] = embeddable
            logger.info(f"Updating embeddable to: {embeddable}")
        
        if license_type is not None:
            body['status']['license'] = license_type
            logger.info(f"Updating license to: {license_type}")
        
        if public_stats_viewable is not None:
            body['status']['publicStatsViewable'] = public_stats_viewable
            logger.info(f"Updating publicStatsViewable to: {public_stats_viewable}")
        
        if made_for_kids is not None:
            body['status']['selfDeclaredMadeForKids'] = made_for_kids
            logger.info(f"Updating selfDeclaredMadeForKids to: {made_for_kids}")
        
        if contains_synthetic_media is not None:
            body['status']['containsSyntheticMedia'] = contains_synthetic_media
            logger.info(f"Updating containsSyntheticMedia to: {contains_synthetic_media}")
        
        logger.debug(f"Request body: {json.dumps(body, indent=2)}")
        
        # Execute the update
        try:
            request = self.youtube.videos().update(
                part='snippet,status',
                body=body
            )
            
            logger.info("Executing video update...")
            response = request.execute()
            
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            
            logger.info(f"Video updated successfully. ID: {video_id}")
            logger.info(f"Video URL: {video_url}")
            
            return {
                'id': video_id,
                'url': video_url,
                'title': response['snippet']['title'],
                'privacy_status': response['status']['privacyStatus']
            }
            
        except HttpError as e:
            logger.error(f"An HTTP error {e.resp.status} occurred:")
            logger.error(f"Error details: {e.content}")
            raise


def update_youtube():
    """Main function to update YouTube video metadata."""
    # Setup logging
    log_level = get_optional_env_var("LOG_LEVEL", "INFO")
    logger = setup_logging(log_level)
    logger.info("Starting YouTube video update process")
    
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
            logger.info(f"Using custom OAuth scopes: {oauth_scopes}")
        
        # Get video ID (required)
        video_id = get_required_env_var("VIDEO_ID")
        
        # Validate that VIDEO_ID is not empty or N/A variation
        if is_value_empty_or_na(video_id):
            logger.error("VIDEO_ID cannot be empty, N/A, or similar variations")
            sys.exit(1)
        
        # Get optional update fields
        title = get_optional_env_var("VIDEO_TITLE", "")
        description = get_optional_env_var("VIDEO_DESCRIPTION", "")
        tags_str = get_optional_env_var("VIDEO_TAGS", "")
        category_id = get_optional_env_var("VIDEO_CATEGORY_ID", "")
        privacy_status = get_optional_env_var("VIDEO_PRIVACY_STATUS", "")
        
        # Get boolean settings
        embeddable_str = get_optional_env_var("VIDEO_EMBEDDABLE", "")
        license_type = get_optional_env_var("VIDEO_LICENSE", "")
        public_stats_viewable_str = get_optional_env_var("VIDEO_PUBLIC_STATS_VIEWABLE", "")
        made_for_kids_str = get_optional_env_var("VIDEO_MADE_FOR_KIDS", "")
        contains_synthetic_media_str = get_optional_env_var("VIDEO_CONTAINS_SYNTHETIC_MEDIA", "")
        
        # Process templated content
        title, description = process_templated_contents(title, description)
        
        # Parse tags if provided
        tags = None
        if tags_str:
            tags = [tag.strip() for tag in tags_str.split(',') if tag.strip()]
        
        # Parse boolean fields
        embeddable = None
        if embeddable_str:
            embeddable = embeddable_str.lower() in ('true', '1', 'yes')
        
        public_stats_viewable = None
        if public_stats_viewable_str:
            public_stats_viewable = public_stats_viewable_str.lower() in ('true', '1', 'yes')
        
        made_for_kids = None
        if made_for_kids_str:
            made_for_kids = made_for_kids_str.lower() in ('true', '1', 'yes')
        
        contains_synthetic_media = None
        if contains_synthetic_media_str:
            contains_synthetic_media = contains_synthetic_media_str.lower() in ('true', '1', 'yes')
        
        # Validate at least one field is being updated
        if not any([title, description, tags, category_id, privacy_status, 
                   embeddable is not None, license_type, public_stats_viewable is not None,
                   made_for_kids is not None, contains_synthetic_media is not None]):
            logger.error("At least one field must be provided for update")
            sys.exit(1)
        
        # Prepare dry run data
        dry_run_request = {
            'action': 'update_video',
            'video_id': video_id
        }
        
        if title:
            dry_run_request['new_title'] = title
            dry_run_request['new_title_length'] = len(title)
        if description:
            dry_run_request['new_description'] = description
            dry_run_request['new_description_length'] = len(description)
        if tags:
            dry_run_request['new_tags'] = tags
        if category_id:
            dry_run_request['new_category_id'] = category_id
        if privacy_status:
            dry_run_request['new_privacy_status'] = privacy_status
        if embeddable is not None:
            dry_run_request['new_embeddable'] = embeddable
        if license_type:
            dry_run_request['new_license'] = license_type
        if public_stats_viewable is not None:
            dry_run_request['new_public_stats_viewable'] = public_stats_viewable
        if made_for_kids is not None:
            dry_run_request['new_made_for_kids'] = made_for_kids
        if contains_synthetic_media is not None:
            dry_run_request['new_contains_synthetic_media'] = contains_synthetic_media
        
        # DRY RUN GUARD
        dry_run_guard("YouTube Update", f"Video ID: {video_id}", [], dry_run_request)
        
        # Create YouTube API client with appropriate authentication
        api = YouTubeUpdateAPI(
            credentials_json=credentials_json or None,
            oauth_client_id=oauth_client_id or None,
            oauth_client_secret=oauth_client_secret or None,
            oauth_refresh_token=oauth_refresh_token or None,
            oauth_scopes=oauth_scopes
        )
        
        # Update the video
        result = api.update_video(
            video_id=video_id,
            title=title if title else None,
            description=description if description else None,
            tags=tags,
            category_id=category_id if category_id else None,
            privacy_status=privacy_status if privacy_status else None,
            embeddable=embeddable,
            license_type=license_type if license_type else None,
            public_stats_viewable=public_stats_viewable,
            made_for_kids=made_for_kids,
            contains_synthetic_media=contains_synthetic_media
        )
        
        video_url = result['url']
        
        # Output for GitHub Actions
        if 'GITHUB_OUTPUT' in os.environ:
            with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
                f.write(f"video-id={video_id}\n")
                f.write(f"video-url={video_url}\n")
        
        log_success("YouTube Update", video_id)
        logger.info(f"Video URL: {video_url}")
        
    except Exception as e:
        handle_api_error(e, "YouTube Update")


if __name__ == "__main__":
    update_youtube()
