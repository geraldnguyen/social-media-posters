#!/usr/bin/env python3
"""
Post content to Instagram using the Instagram Basic Display API.
"""

import os
import sys
import logging
import requests
import time
from pathlib import Path
from PIL import Image

# Add common module to path
import sys
# NOTE: This script assumes you are running from the project root (social-media-posters)
# and that 'common' is a package (contains __init__.py).
from common.social_media_utils import (
    setup_logging,
    get_required_env_var,
    get_optional_env_var,
    validate_post_content,
    handle_api_error,
    log_success
)

from social_media_utils import (
    setup_logging,
    get_required_env_var,
    get_optional_env_var,
    validate_post_content,
    handle_api_error,
    log_success
)


class InstagramAPI:
    """Instagram Graph API client."""
    
    def __init__(self, access_token):
        self.access_token = access_token
        self.base_url = "https://graph.instagram.com"
    
    def create_media_container(self, user_id, image_url, caption, media_type="IMAGE"):
        """Create a media container for Instagram post."""
        url = f"{self.base_url}/{user_id}/media"
        
        data = {
            "image_url": image_url,
            "caption": caption,
            "media_type": media_type,
            "access_token": self.access_token
        }
        
        if media_type == "VIDEO":
            data["video_url"] = image_url
            del data["image_url"]
        
        response = requests.post(url, data=data)
        response.raise_for_status()
        return response.json()["id"]
    
    def publish_media(self, user_id, creation_id):
        """Publish the media container."""
        url = f"{self.base_url}/{user_id}/media_publish"
        
        data = {
            "creation_id": creation_id,
            "access_token": self.access_token
        }
        
        response = requests.post(url, data=data)
        response.raise_for_status()
        return response.json()["id"]
    
    def get_media_info(self, media_id):
        """Get media information."""
        url = f"{self.base_url}/{media_id}"
        
        params = {
            "fields": "id,permalink",
            "access_token": self.access_token
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()


def validate_image(file_path):
    """Validate image file for Instagram requirements."""
    try:
        with Image.open(file_path) as img:
            width, height = img.size
            
            # Instagram image requirements
            if width < 320 or height < 320:
                raise ValueError("Image must be at least 320x320 pixels")
            
            aspect_ratio = width / height
            if aspect_ratio < 0.8 or aspect_ratio > 1.91:
                raise ValueError("Image aspect ratio must be between 0.8 and 1.91")
            
            return True
    except Exception as e:
        logging.error(f"Image validation failed: {str(e)}")
        return False


def upload_media_to_hosting(file_path):
    """
    Upload media to a hosting service.
    Note: This is a placeholder. In real implementation, you would upload to
    a service like AWS S3, Cloudinary, or similar to get a public URL.
    For this example, we'll assume the file is already hosted.
    """
    # In a real implementation, you would:
    # 1. Upload the file to a hosting service
    # 2. Return the public URL
    
    # For now, we'll assume the file_path is already a URL or return an error
    if file_path.startswith(('http://', 'https://')):
        return file_path
    else:
        raise ValueError(
            "Media file must be a publicly accessible URL. "
            "Please upload your media to a hosting service and provide the URL."
        )


def post_to_instagram():
    """Main function to post content to Instagram."""
    # Setup logging
    log_level = get_optional_env_var("LOG_LEVEL", "INFO")
    logger = setup_logging(log_level)
    
    try:
        # Get required parameters
        user_id = get_required_env_var("IG_USER_ID")
        content = get_required_env_var("POST_CONTENT")
        media_file = get_required_env_var("MEDIA_FILE")
        
        # Validate content
        if not validate_post_content(content, max_length=2200):  # Instagram caption limit
            sys.exit(1)
        
        # Create Instagram API client
        ig_api = InstagramAPI(get_required_env_var("IG_ACCESS_TOKEN"))
        
        # Determine media type
        file_ext = Path(media_file).suffix.lower() if not media_file.startswith('http') else Path(media_file).suffix.lower()
        media_type = "VIDEO" if file_ext in ['.mp4', '.mov'] else "IMAGE"
        
        # Validate image if it's an image file and local
        if media_type == "IMAGE" and not media_file.startswith('http'):
            if not validate_image(media_file):
                sys.exit(1)
        
        # Get media URL (upload to hosting service if needed)
        media_url = upload_media_to_hosting(media_file)
        logger.info(f"Using media URL: {media_url}")
        
        # Create media container
        logger.info("Creating media container...")
        creation_id = ig_api.create_media_container(
            user_id=user_id,
            image_url=media_url,
            caption=content,
            media_type=media_type
        )
        
        logger.info(f"Media container created with ID: {creation_id}")
        
        # Wait a moment before publishing (Instagram recommendation)
        time.sleep(2)
        
        # Publish media
        logger.info("Publishing media...")
        media_id = ig_api.publish_media(user_id, creation_id)
        
        # Get media info for URL
        media_info = ig_api.get_media_info(media_id)
        post_url = media_info.get("permalink", f"https://www.instagram.com/p/{media_id}/")
        
        # Output for GitHub Actions
        if 'GITHUB_OUTPUT' in os.environ:
            with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
                f.write(f"post-id={media_id}\n")
                f.write(f"post-url={post_url}\n")
        
        log_success("Instagram", media_id)
        logger.info(f"Post URL: {post_url}")
        
    except Exception as e:
        handle_api_error(e, "Instagram")


if __name__ == "__main__":
    post_to_instagram()