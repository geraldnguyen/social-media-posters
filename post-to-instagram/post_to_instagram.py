#!/usr/bin/env python3
"""
Post content to Instagram using the Instagram Basic Display API.
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
from PIL import Image

# Add common module to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'common'))

from social_media_utils import (
    setup_logging,
    get_required_env_var,
    get_optional_env_var,
    validate_post_content,
    handle_api_error,
    log_success
)

from templating_utils import process_templated_contents


# Module-level logger
logger = logging.getLogger(__name__)

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
    
    def create_carousel_container(self, user_id, children_ids, caption):
        """Create a carousel container for multiple media items."""
        url = f"{self.base_url}/{user_id}/media"
        
        data = {
            "media_type": "CAROUSEL",
            "children": ",".join(children_ids),
            "caption": caption,
            "access_token": self.access_token
        }
        
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
        logger.error(f"Image validation failed: {str(e)}")
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
        logger.error("Media file must be a publicly accessible URL for Instagram posting: %s", file_path)
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
        
        # Get media files - support both single and multiple
        media_file = get_optional_env_var("MEDIA_FILE", "")
        media_files_input = get_optional_env_var("MEDIA_FILES", "")
        
        # Validate that exactly one media input is provided
        if not media_file and not media_files_input:
            logger.error("Either MEDIA_FILE or MEDIA_FILES must be provided")
            sys.exit(1)
        if media_file and media_files_input:
            logger.error("Cannot specify both MEDIA_FILE and MEDIA_FILES. Use one or the other.")
            sys.exit(1)
        
                
        # Process templated content (Instagram doesn't support links in posts)
        content, media_file, media_files_input = process_templated_contents(content, media_file, media_files_input)


        # Parse media files (Instagram requires URLs, so no downloading)
        if media_file:
            media_files = [media_file]
        else:
            # Simple parsing for Instagram - just split by comma and strip whitespace
            media_files = [f.strip() for f in media_files_input.split(',') if f.strip()]
        
        # Validate media files count
        if len(media_files) > 10:
            logger.error("Instagram carousel posts support maximum 10 media files")
            sys.exit(1)

        
        # Validate content
        if not validate_post_content(content, max_length=2200):  # Instagram caption limit
            sys.exit(1)
        
        # Create Instagram API client
        ig_api = InstagramAPI(get_required_env_var("IG_ACCESS_TOKEN"))
        
        # Determine media types and validate
        media_types = []
        for media_file in media_files:
            file_ext = Path(media_file).suffix.lower() if not media_file.startswith('http') else Path(media_file).suffix.lower()
            if file_ext in ['.mp4', '.mov', '.avi', '.wmv', '.mpg', '.mpeg', '.webm', '.flv', '.m4v', '.mkv', '.3gp', '.3g2', '.ogv']:
                media_types.append("VIDEO")
            else:
                media_types.append("IMAGE")
        
        # Validate media files are URLs (required for Instagram API)
        for media_file in media_files:
            if not media_file.startswith(('http://', 'https://')):
                logger.error(f"Instagram requires publicly accessible URLs. Invalid media file: {media_file}")
                sys.exit(1)
        
        logger.info(f"Using media URLs: {media_files}")
        
        # DRY RUN GUARD
        from social_media_utils import dry_run_guard
        dry_run_request = {
            'caption': content,
            'media_count': len(media_files),
            'media_types': media_types,
            'media_urls': media_files,  # media_files now contains the URLs directly
            'is_carousel': len(media_files) > 1
        }
        dry_run_guard("Instagram", content, media_files, dry_run_request)
        
        # Create media container(s)
        if len(media_files) == 1:
            # Single media post
            logger.info("Creating single media container...")
            creation_id = ig_api.create_media_container(
                user_id=user_id,
                image_url=media_files[0],
                caption=content,
                media_type=media_types[0]
            )
        else:
            # Carousel post - create individual containers first
            logger.info(f"Creating carousel with {len(media_files)} media items...")
            child_container_ids = []
            
            for i, (media_url, media_type) in enumerate(zip(media_files, media_types)):
                logger.info(f"Creating child container {i+1}/{len(media_files)}...")
                # Note: Individual containers in carousel don't have captions
                child_id = ig_api.create_media_container(
                    user_id=user_id,
                    image_url=media_url,
                    caption="",  # No caption for individual items in carousel
                    media_type=media_type
                )
                child_container_ids.append(child_id)
            
            # Create the carousel container
            logger.info("Creating carousel container...")
            creation_id = ig_api.create_carousel_container(
                user_id=user_id,
                children_ids=child_container_ids,
                caption=content
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