#!/usr/bin/env python3
"""
Post content to Threads using the Threads API.
"""

import os
import sys
import logging
import requests
import time
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


class ThreadsAPI:
    """Threads API client."""
    
    def __init__(self, access_token):
        self.access_token = access_token
        self.base_url = "https://graph.threads.net"
    
    def create_media_container(self, user_id, text, media_url=None, link_attachment=None):
        """Create a media container for Threads post."""
        url = f"{self.base_url}/{user_id}/threads"
        
        data = {
            "media_type": "TEXT",
            "text": text,
            "access_token": self.access_token
        }
        
        if media_url:
            if media_url.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                data["media_type"] = "IMAGE"
                data["image_url"] = media_url
            elif media_url.lower().endswith(('.mp4', '.mov')):
                data["media_type"] = "VIDEO"
                data["video_url"] = media_url
        
        if link_attachment:
            data["link_attachment"] = link_attachment
        
        response = requests.post(url, data=data)
        response.raise_for_status()
        return response.json()["id"]
    
    def publish_media(self, user_id, creation_id):
        """Publish the media container."""
        url = f"{self.base_url}/{user_id}/threads_publish"
        
        data = {
            "creation_id": creation_id,
            "access_token": self.access_token
        }
        
        response = requests.post(url, data=data)
        response.raise_for_status()
        return response.json()["id"]
    
    def get_thread_info(self, thread_id):
        """Get thread information."""
        url = f"{self.base_url}/{thread_id}"
        
        params = {
            "fields": "id,permalink",
            "access_token": self.access_token
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()


def post_to_threads():
    """Main function to post content to Threads."""
    # Setup logging
    log_level = get_optional_env_var("LOG_LEVEL", "INFO")
    logger = setup_logging(log_level)
    
    try:
        # Get required parameters
        user_id = get_required_env_var("THREADS_USER_ID")
        content = get_required_env_var("POST_CONTENT")
        
        # Validate content (Threads has a 500 character limit)
        if not validate_post_content(content, max_length=500):
            sys.exit(1)
        
        # Get optional parameters
        media_file = get_optional_env_var("MEDIA_FILE", "")
        link = get_optional_env_var("POST_LINK", "")
        
        # Create Threads API client
        threads_api = ThreadsAPI(get_required_env_var("THREADS_ACCESS_TOKEN"))
        
        # Validate media file is a URL if provided
        if media_file and not media_file.startswith(('http://', 'https://')):
            raise ValueError(
                "Media file must be a publicly accessible URL. "
                "Please upload your media to a hosting service and provide the URL."
            )
        
        logger.info("Creating thread container...")
        
        # Create media container
        creation_id = threads_api.create_media_container(
            user_id=user_id,
            text=content,
            media_url=media_file if media_file else None,
            link_attachment=link if link else None
        )
        
        logger.info(f"Thread container created with ID: {creation_id}")
        
        # Wait a moment before publishing (API recommendation)
        time.sleep(2)
        
        # Publish thread
        logger.info("Publishing thread...")
        thread_id = threads_api.publish_media(user_id, creation_id)
        
        # Get thread info for URL
        try:
            thread_info = threads_api.get_thread_info(thread_id)
            post_url = thread_info.get("permalink", f"https://www.threads.net/t/{thread_id}")
        except:
            # Fallback URL if we can't get permalink
            post_url = f"https://www.threads.net/t/{thread_id}"
        
        # Output for GitHub Actions
        if 'GITHUB_OUTPUT' in os.environ:
            with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
                f.write(f"post-id={thread_id}\n")
                f.write(f"post-url={post_url}\n")
        
        log_success("Threads", thread_id)
        logger.info(f"Post URL: {post_url}")
        
    except Exception as e:
        handle_api_error(e, "Threads")


if __name__ == "__main__":
    post_to_threads()