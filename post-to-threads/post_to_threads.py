#!/usr/bin/env python3
"""
Post content to Threads using the Threads API.
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
import time
from pathlib import Path
from urllib.parse import urlparse

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
    dry_run_guard
)


# Module-level logger
logger = logging.getLogger(__name__)

def validate_link_url(link):
    """Validate that a link is a properly formatted URL.
    
    Args:
        link: URL string to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not link or not isinstance(link, str):
        return False
    
    link = link.strip()
    if not link:
        return False
    
    try:
        result = urlparse(link)
        # Basic validation: must have scheme and netloc
        return all([result.scheme in ('http', 'https'), result.netloc])
    except Exception as e:
        logger.warning(f"Error validating link URL: {e}")
        return False

def check_link_accessibility(link, timeout=5):
    """Pre-check if a link is accessible before publishing.
    
    Args:
        link: URL to check
        timeout: Request timeout in seconds
        
    Returns:
        True if accessible, False otherwise
    """
    if not validate_link_url(link):
        logger.error(f"Invalid link format: {link}")
        return False
    
    try:
        logger.debug(f"Pre-checking link accessibility: {link}")
        response = requests.head(link, timeout=timeout, allow_redirects=True)
        is_accessible = response.status_code < 400
        if is_accessible:
            logger.info(f"Link accessibility check passed (status {response.status_code}): {link}")
        else:
            logger.warning(f"Link accessibility check failed (status {response.status_code}): {link}")
        return is_accessible
    except requests.Timeout:
        logger.warning(f"Link accessibility check timed out after {timeout}s: {link}")
        return False
    except requests.RequestException as e:
        logger.warning(f"Link accessibility check failed: {link} - {e}")
        return False

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
            if media_url.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.tiff', '.tif')):
                data["media_type"] = "IMAGE"
                data["image_url"] = media_url
            elif media_url.lower().endswith(('.mp4', '.mov', '.avi', '.wmv', '.mpg', '.mpeg', '.webm', '.flv', '.m4v', '.mkv', '.3gp', '.3g2', '.ogv')):
                data["media_type"] = "VIDEO"
                data["video_url"] = media_url
        
        if link_attachment:
            # Threads API expects link_attachment as a JSON object, not a string
            data["link_attachment"] = {"url": link_attachment}
        
        logger.info(f"Making API request to create media container: POST {url}")
        logger.debug(f"Request data: media_type={data.get('media_type')}, text_length={len(text)}, has_media={bool(media_url)}, has_link={bool(link_attachment)}")
        response = requests.post(url, data=data)
        logger.info(f"API response status: {response.status_code}")
        
        try:
            response.raise_for_status()
            result = response.json()
            logger.info(f"Media container created successfully: {result.get('id')}")
            return result["id"]
        except requests.HTTPError as http_err:
            logger.error(f"HTTP error creating media container: {http_err}")
            logger.error(f"Response content: {response.text}")
            raise
        except ValueError as json_err:
            logger.error(f"Invalid JSON response: {json_err}")
            logger.error(f"Response content: {response.text}")
            raise
    
    def publish_media(self, user_id, creation_id, max_retries=3, base_delay=2):
        """Publish the media container with retry logic for transient failures.
        
        Args:
            user_id: Threads user ID
            creation_id: Creation ID to publish
            max_retries: Maximum number of retry attempts
            base_delay: Base delay in seconds for exponential backoff
        """
        url = f"{self.base_url}/{user_id}/threads_publish"
        
        data = {
            "creation_id": creation_id,
            "access_token": self.access_token
        }
        
        for attempt in range(max_retries):
            try:
                logger.info(f"Making API request to publish media (attempt {attempt + 1}/{max_retries}): POST {url}")
                logger.info(f"Publishing creation_id: {creation_id}")
                response = requests.post(url, data=data)
                logger.info(f"API response status: {response.status_code}")
                
                response.raise_for_status()
                result = response.json()
                logger.info(f"Media published successfully: {result.get('id')}")
                return result["id"]
                
            except requests.HTTPError as http_err:
                try:
                    error_data = response.json()
                    is_transient = error_data.get('error', {}).get('is_transient', False)
                    error_msg = error_data.get('error', {}).get('error_user_msg', str(http_err))
                except (ValueError, KeyError):
                    is_transient = False
                    error_msg = str(http_err)
                
                logger.error(f"HTTP error publishing media: {http_err}")
                logger.error(f"Error message: {error_msg}")
                logger.error(f"Response content: {response.text}")
                
                # Retry on transient errors or on certain status codes
                if attempt < max_retries - 1 and (is_transient or response.status_code in [429, 500, 502, 503, 504]):
                    delay = base_delay * (2 ** attempt)  # Exponential backoff
                    logger.warning(f"Transient error detected. Retrying in {delay} seconds...")
                    time.sleep(delay)
                    continue
                else:
                    # Non-transient error or final attempt
                    raise
                    
            except ValueError as json_err:
                logger.error(f"Invalid JSON response: {json_err}")
                logger.error(f"Response content: {response.text}")
                raise
    
    def get_thread_info(self, thread_id):
        """Get thread information."""
        url = f"{self.base_url}/{thread_id}"
        
        params = {
            "fields": "id,permalink",
            "access_token": self.access_token
        }
        
        logger.info(f"Making API request to get thread info: GET {url}")
        logger.info(f"Retrieving info for thread_id: {thread_id}")
        response = requests.get(url, params=params)
        logger.info(f"API response status: {response.status_code}")
        
        try:
            response.raise_for_status()
            result = response.json()
            logger.info(f"Thread info retrieved successfully: has_permalink={bool(result.get('permalink'))}")
            return result
        except requests.HTTPError as http_err:
            logger.error(f"HTTP error getting thread info: {http_err}")
            logger.error(f"Response content: {response.text}")
            raise
        except ValueError as json_err:
            logger.error(f"Invalid JSON response: {json_err}")
            logger.error(f"Response content: {response.text}")
            raise


def post_to_threads():
    """Main function to post content to Threads."""
    # Setup logging
    log_level = get_optional_env_var("LOG_LEVEL", "INFO")
    logger = setup_logging(log_level)
    
    try:
        # Get required parameters
        user_id = get_required_env_var("THREADS_USER_ID")
        content = get_required_env_var("POST_CONTENT")
        logger.info(f"Retrieved required parameters: user_id={user_id}, content_length={len(content)}")
        
        # Get optional parameters
        media_file = get_optional_env_var("MEDIA_FILE", "")
        link = get_optional_env_var("POST_LINK", "")
        logger.info(f"Retrieved optional parameters: media_file={'present' if media_file else 'none'}, link={'present' if link else 'none'}")
        
        # Process templated content and link using the same JSON root
        original_content = content
        original_link = link
        content, link = process_templated_contents(content, link)
        if content != original_content or link != original_link:
            logger.info("Template processing applied changes to content or link")
        else:
            logger.info("No template processing changes applied")
        
        # Validate content (Threads has a 500 character limit) - moved after template processing
        if not validate_post_content(content, max_length=500):
            logger.error(f"Content validation failed for content: {content[:100]}{'...' if len(content) > 100 else ''}")
            sys.exit(1)
        logger.info("Content validation passed")
        
        # Create Threads API client
        logger.info("Initializing Threads API client")
        threads_api = ThreadsAPI(get_required_env_var("THREADS_ACCESS_TOKEN"))
        
        # Validate media file is a URL if provided
        if media_file and not media_file.startswith(('http://', 'https://')):
            logger.error(f"Invalid media file URL: {media_file}")
            raise ValueError(
                "Media file must be a publicly accessible URL. "
                "Please upload your media to a hosting service and provide the URL."
            )
        if media_file:
            logger.info(f"Media file URL validated: {media_file}")
        
        # Validate link if provided
        if link:
            if not validate_link_url(link):
                logger.error(f"Invalid link format: {link}")
                raise ValueError(
                    f"Link must be a valid URL starting with http:// or https://. "
                    f"Provided link: {link}"
                )
            logger.info(f"Link format validation passed: {link}")
            
            # Pre-check link accessibility
            logger.info("Performing pre-check on link accessibility...")
            if not check_link_accessibility(link):
                logger.warning(
                    f"Link accessibility check failed. The link may be temporarily unavailable. "
                    f"Proceeding anyway as Threads API may handle this. Link: {link}"
                )
            else:
                logger.info("Link accessibility check successful")
        
        # DRY RUN GUARD
        media_files = [media_file] if media_file else []
        dry_run_request = {
            'text': content,
            'media_url': media_file,
            'link': link
        }
        logger.info("Checking dry run guard...")
        dry_run_guard("Threads", content, media_files, dry_run_request)
        
        logger.info("Creating thread container...")
        media_type = "TEXT"
        if media_file:
            if media_file.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.tiff', '.tif')):
                media_type = "IMAGE"
            elif media_file.lower().endswith(('.mp4', '.mov', '.avi', '.wmv', '.mpg', '.mpeg', '.webm', '.flv', '.m4v', '.mkv', '.3gp', '.3g2', '.ogv')):
                media_type = "VIDEO"
        logger.info(f"Creating media container with type: {media_type}, has_link: {bool(link)}")
        
        # Create media container
        creation_id = threads_api.create_media_container(
            user_id=user_id,
            text=content,
            media_url=media_file if media_file else None,
            link_attachment=link if link else None
        )
        
        logger.info(f"Thread container created with ID: {creation_id}")
        
        # Wait a moment before publishing (API recommendation)
        logger.info("Waiting 2 seconds before publishing (API recommendation)")
        time.sleep(2)
        
        # Publish thread
        logger.info("Publishing thread...")
        thread_id = threads_api.publish_media(user_id, creation_id)
        logger.info(f"Thread published successfully with ID: {thread_id}")
        
        # Get thread info for URL
        logger.info("Retrieving thread information for permalink...")
        try:
            thread_info = threads_api.get_thread_info(thread_id)
            post_url = thread_info.get("permalink", f"https://www.threads.net/t/{thread_id}")
            logger.info(f"Retrieved thread permalink: {post_url}")
        except Exception as url_exc:
            logger.warning(f"Failed to get thread permalink: {url_exc}")
            # Fallback URL if we can't get permalink
            post_url = f"https://www.threads.net/t/{thread_id}"
            logger.info(f"Using fallback URL: {post_url}")
        
        # Output for GitHub Actions
        if 'GITHUB_OUTPUT' in os.environ:
            with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
                f.write(f"post-id={thread_id}\n")
                f.write(f"post-url={post_url}\n")
        
        log_success("Threads", thread_id)
        logger.info(f"Post URL: {post_url}")
        
    except Exception as e:
        logger.error(f"Error occurred during Threads posting: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        import traceback
        logger.debug(f"Full traceback: {traceback.format_exc()}")
        handle_api_error(e, "Threads")


if __name__ == "__main__":
    post_to_threads()