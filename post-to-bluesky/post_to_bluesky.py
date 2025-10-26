#!/usr/bin/env python3
"""
Post content to Bluesky using the AT Protocol API.
"""

import os
from pathlib import Path

# Load environment variables from a local .env file if present (for local development)
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent / '.env'
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
except ImportError:
    pass  # python-dotenv is not installed; skip loading .env
import sys
import logging
import requests
import mimetypes
from datetime import datetime, timezone

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
    parse_media_files
)


BLUESKY_API_BASE_URL = "https://bsky.social/xrpc"


def create_session(identifier: str, password: str) -> dict:
    """Create an authenticated session with Bluesky."""
    url = f"{BLUESKY_API_BASE_URL}/com.atproto.server.createSession"
    
    payload = {
        "identifier": identifier,
        "password": password
    }
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        session_data = response.json()
        logging.info("Successfully authenticated with Bluesky")
        return session_data
    except requests.RequestException as exc:
        logging.error(f"Bluesky authentication failed: {exc}")
        raise
    except ValueError:
        logging.error(f"Bluesky authentication returned non-JSON response: {response.text}")
        raise


def upload_blob(access_token: str, file_path: str) -> dict:
    """Upload a media file (blob) to Bluesky."""
    url = f"{BLUESKY_API_BASE_URL}/com.atproto.repo.uploadBlob"
    
    headers = {
        "Authorization": f"Bearer {access_token}",
    }
    
    # Detect MIME type
    mime_type, _ = mimetypes.guess_type(file_path)
    if not mime_type:
        mime_type = "application/octet-stream"
    
    headers["Content-Type"] = mime_type
    
    try:
        with open(file_path, 'rb') as f:
            file_data = f.read()
        
        response = requests.post(url, headers=headers, data=file_data, timeout=60)
        response.raise_for_status()
        blob_data = response.json()
        logging.info(f"Successfully uploaded blob: {file_path}")
        return blob_data.get('blob')
    except requests.RequestException as exc:
        logging.error(f"Failed to upload blob {file_path}: {exc}")
        raise
    except ValueError:
        logging.error(f"Blob upload returned non-JSON response: {response.text}")
        raise


def create_post(access_token: str, did: str, text: str, media_blobs: list = None, link: str = None) -> dict:
    """Create a post on Bluesky."""
    url = f"{BLUESKY_API_BASE_URL}/com.atproto.repo.createRecord"
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    # Build the post record
    record = {
        "$type": "app.bsky.feed.post",
        "text": text,
        "createdAt": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
    }
    
    # Add embedded media if present
    if media_blobs:
        images = []
        for blob in media_blobs[:4]:  # Bluesky supports up to 4 images
            images.append({
                "alt": "",
                "image": blob
            })
        
        if images:
            record["embed"] = {
                "$type": "app.bsky.embed.images",
                "images": images
            }
    
    # Add link embed if present and no media
    elif link:
        # For now, we'll include the link in the text
        # Full link card embedding would require fetching link metadata
        pass
    
    payload = {
        "repo": did,
        "collection": "app.bsky.feed.post",
        "record": record
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        post_data = response.json()
        logging.info("Successfully created Bluesky post")
        return post_data
    except requests.RequestException as exc:
        logging.error(f"Failed to create Bluesky post: {exc}")
        if hasattr(exc.response, 'text'):
            logging.error(f"Response: {exc.response.text}")
        raise
    except ValueError:
        logging.error(f"Create post returned non-JSON response: {response.text}")
        raise


def post_to_bluesky():
    """Main function to post content to Bluesky."""
    # Setup logging
    log_level = get_optional_env_var("LOG_LEVEL", "INFO")
    logger = setup_logging(log_level)
    
    try:
        # Get required parameters
        identifier = get_required_env_var("BLUESKY_IDENTIFIER")
        password = get_required_env_var("BLUESKY_PASSWORD")
        content = get_required_env_var("POST_CONTENT")

        # Get optional parameters
        link = get_optional_env_var("POST_LINK", "")
        # Process templated content and link using the same JSON root
        content, link = process_templated_contents(content, link)

        # Validate content (Bluesky has a 300 character limit for posts)
        if not validate_post_content(content, max_length=300):
            sys.exit(1)
        
        media_input = get_optional_env_var("MEDIA_FILES", "")
        media_files = parse_media_files(media_input)
        
        # DRY RUN GUARD
        from social_media_utils import dry_run_guard
        dry_run_request = {
            'text': content,
            'identifier': identifier
        }
        if media_files:
            dry_run_request['media_files'] = ', '.join(media_files)
        if link:
            dry_run_request['link'] = link
        dry_run_guard("Bluesky", content, media_files, dry_run_request)
        
        # Authenticate
        session = create_session(identifier, password)
        access_token = session.get('accessJwt')
        did = session.get('did')
        
        if not access_token or not did:
            logging.error("Failed to get access token or DID from session")
            sys.exit(1)
        
        # Upload media files if present
        media_blobs = []
        if media_files:
            for media_file in media_files[:4]:  # Bluesky supports up to 4 images
                file_ext = Path(media_file).suffix.lower()
                
                # Only support images for now
                if file_ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
                    blob = upload_blob(access_token, media_file)
                    media_blobs.append(blob)
                else:
                    logger.warning(f"Unsupported media type for Bluesky: {file_ext}")
        
        # Create the post
        post_data = create_post(access_token, did, content, media_blobs, link)
        
        # Extract post URI and construct URL
        post_uri = post_data.get('uri', '')
        post_cid = post_data.get('cid', '')
        
        # Construct the Bluesky post URL
        # URI format: at://did:plc:xxx/app.bsky.feed.post/xxx
        if post_uri:
            parts = post_uri.split('/')
            if len(parts) >= 3:
                post_id = parts[-1]
                handle = session.get('handle', identifier)
                post_url = f"https://bsky.app/profile/{handle}/post/{post_id}"
            else:
                post_url = post_uri
        else:
            post_url = "(Post created but URL unavailable)"
        
        # Output for GitHub Actions
        if 'GITHUB_OUTPUT' in os.environ:
            with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
                f.write(f"post-uri={post_uri}\n")
                f.write(f"post-cid={post_cid}\n")
                f.write(f"post-url={post_url}\n")
        
        log_success("Bluesky", post_uri)
        logger.info(f"Post URL: {post_url}")
        
    except Exception as e:
        handle_api_error(e, "Bluesky")


if __name__ == "__main__":
    post_to_bluesky()
