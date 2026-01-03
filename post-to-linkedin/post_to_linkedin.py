#!/usr/bin/env python3
"""
Post content to LinkedIn using the LinkedIn API.
"""

import os
import sys
from pathlib import Path

# Load environment variables from a local .env file if present (for local development)
try:
    from dotenv import load_dotenv
    env_path = Path.cwd() / '.env'
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
except ImportError:
    pass  # python-dotenv is not installed; skip loading .env
import logging
import requests
import json
import time

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
    dry_run_guard
)


# Module-level logger
logger = logging.getLogger(__name__)

class LinkedInAPI:
    """LinkedIn API client."""
    
    def __init__(self, access_token):
        self.access_token = access_token
        self.base_url = "https://api.linkedin.com/v2"
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0"
        }
    
    def upload_image(self, author_id, image_path):
        """Upload an image to LinkedIn and return the asset URN."""
        logger.info(f"Uploading image: {image_path}")
        
        # Step 1: Register the upload
        register_url = f"{self.base_url}/assets?action=registerUpload"
        register_data = {
            "registerUploadRequest": {
                "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
                "owner": author_id,
                "serviceRelationships": [
                    {
                        "relationshipType": "OWNER",
                        "identifier": "urn:li:userGeneratedContent"
                    }
                ]
            }
        }
        
        logger.debug(f"Registering upload: POST {register_url}")
        response = requests.post(register_url, headers=self.headers, json=register_data)
        logger.debug(f"Register response status: {response.status_code}")
        
        try:
            response.raise_for_status()
            register_result = response.json()
            logger.debug(f"Register result: {json.dumps(register_result, indent=2)}")
        except requests.HTTPError as http_err:
            logger.error(f"HTTP error registering upload: {http_err}")
            logger.error(f"Response content: {response.text}")
            raise
        except ValueError as json_err:
            logger.error(f"Invalid JSON response: {json_err}")
            logger.error(f"Response content: {response.text}")
            raise
        
        upload_url = register_result['value']['uploadMechanism']['com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest']['uploadUrl']
        asset_urn = register_result['value']['asset']
        
        # Step 2: Upload the image binary
        logger.debug(f"Uploading image binary to: {upload_url}")
        with open(image_path, 'rb') as image_file:
            upload_headers = {
                "Authorization": f"Bearer {self.access_token}"
            }
            upload_response = requests.put(upload_url, headers=upload_headers, data=image_file)
            logger.debug(f"Upload response status: {upload_response.status_code}")
            
            try:
                upload_response.raise_for_status()
                logger.info(f"Image uploaded successfully: {asset_urn}")
            except requests.HTTPError as http_err:
                logger.error(f"HTTP error uploading image: {http_err}")
                logger.error(f"Response content: {upload_response.text}")
                raise
        
        return asset_urn
    
    def create_post(self, author_id, content, media_assets=None, link_url=None):
        """Create a LinkedIn post."""
        url = f"{self.base_url}/ugcPosts"
        
        post_data = {
            "author": author_id,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {
                        "text": content
                    },
                    "shareMediaCategory": "NONE"
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
            }
        }
        
        # Add media if provided
        if media_assets:
            post_data["specificContent"]["com.linkedin.ugc.ShareContent"]["shareMediaCategory"] = "IMAGE"
            post_data["specificContent"]["com.linkedin.ugc.ShareContent"]["media"] = [
                {
                    "status": "READY",
                    "media": asset_urn
                }
                for asset_urn in media_assets
            ]
        
        # Add article link if provided (and no media)
        if link_url and not media_assets:
            post_data["specificContent"]["com.linkedin.ugc.ShareContent"]["shareMediaCategory"] = "ARTICLE"
            post_data["specificContent"]["com.linkedin.ugc.ShareContent"]["media"] = [
                {
                    "status": "READY",
                    "originalUrl": link_url
                }
            ]
        
        logger.info(f"Making API request to create post: POST {url}")
        logger.debug(f"Request data: {json.dumps(post_data, indent=2)}")
        
        response = requests.post(url, headers=self.headers, json=post_data)
        logger.info(f"API response status: {response.status_code}")
        
        try:
            response.raise_for_status()
            result = response.json()
            logger.info(f"Post created successfully")
            logger.debug(f"Response: {json.dumps(result, indent=2)}")
            return result.get("id")
        except requests.HTTPError as http_err:
            logger.error(f"HTTP error creating post: {http_err}")
            logger.error(f"Response content: {response.text}")
            raise
        except ValueError as json_err:
            logger.error(f"Invalid JSON response: {json_err}")
            logger.error(f"Response content: {response.text}")
            raise


def post_to_linkedin():
    """Main function to post content to LinkedIn."""
    # Setup logging
    log_level = get_optional_env_var("LOG_LEVEL", "INFO")
    logger = setup_logging(log_level)
    
    try:
        # Get required parameters
        access_token = get_required_env_var("LINKEDIN_ACCESS_TOKEN")
        author_id = get_required_env_var("LINKEDIN_AUTHOR_ID")
        content = get_required_env_var("POST_CONTENT")
        
        # Get optional parameters
        link = get_optional_env_var("POST_LINK", "")
        
        # Process templated content and link using the same JSON root
        content, link = process_templated_contents(content, link)
        
        # Validate content (LinkedIn has a 3000 character limit for posts)
        if not validate_post_content(content, max_length=3000):
            sys.exit(1)
        
        # Parse media files
        media_input = get_optional_env_var("MEDIA_FILES", "")
        media_files = parse_media_files(media_input)
        
        # Prepare dry run request data for detailed logging
        dry_run_request = {
            "text": content,
            "text_length": len(content)
        }
        
        if link:
            dry_run_request["link"] = link
            dry_run_request["link_note"] = "LinkedIn will automatically fetch link preview"
        
        if media_files:
            media_info = []
            for idx, file_path in enumerate(media_files, 1):
                file_size = os.path.getsize(file_path)
                media_info.append({
                    "index": idx,
                    "path": file_path,
                    "filename": os.path.basename(file_path),
                    "size_bytes": file_size,
                    "size_kb": round(file_size / 1024, 2),
                    "extension": Path(file_path).suffix
                })
            dry_run_request["media_files"] = media_info
        
        # DRY RUN GUARD
        dry_run_guard("LinkedIn", content, media_files, dry_run_request)
        
        # Create LinkedIn API client
        api = LinkedInAPI(access_token)
        
        # Upload media if provided
        media_assets = []
        if media_files:
            for media_file in media_files:
                file_ext = Path(media_file).suffix.lower()
                
                if file_ext in ['.jpg', '.jpeg', '.png', '.gif']:
                    # Upload image
                    asset_urn = api.upload_image(author_id, media_file)
                    media_assets.append(asset_urn)
                    logger.info(f"Uploaded media: {media_file} (URN: {asset_urn})")
                else:
                    logger.warning(f"Unsupported media type for LinkedIn: {file_ext}")
        
        # Create the post
        post_id = api.create_post(author_id, content, media_assets if media_assets else None, link if link else None)
        
        # LinkedIn post URLs are in the format: https://www.linkedin.com/feed/update/{post_id}
        post_url = f"https://www.linkedin.com/feed/update/{post_id}" if post_id else ""
        
        # Output for GitHub Actions
        if 'GITHUB_OUTPUT' in os.environ:
            with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
                f.write(f"post-id={post_id}\n")
                f.write(f"post-url={post_url}\n")
        
        log_success("LinkedIn", post_id)
        logger.info(f"Post URL: {post_url}")
        
    except Exception as e:
        handle_api_error(e, "LinkedIn")


if __name__ == "__main__":
    post_to_linkedin()
