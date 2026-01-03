#!/usr/bin/env python3
"""
Post content to Bluesky using the AT Protocol Python SDK.
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
from atproto import Client, models
import requests
from bs4 import BeautifulSoup

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


# Module-level logger
logger = logging.getLogger(__name__)

def fetch_link_metadata(url: str) -> dict:
    """Fetch metadata (title, description, image) from a URL for a link card."""
    try:
        response = requests.get(url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'lxml')
        
        title = soup.find('meta', property='og:title') or soup.find('title')
        description = soup.find('meta', property='og:description') or soup.find('meta', attrs={'name': 'description'})
        image_url_tag = soup.find('meta', property='og:image')
        
        return {
            'url': url,
            'title': title.get('content', title.text) if title else '',
            'description': description.get('content', '') if description else '',
            'image_url': image_url_tag.get('content') if image_url_tag else None
        }
    except requests.RequestException as e:
        logger.warning(f"Could not fetch metadata from link {url}: {e}")
        return None


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
            'text_length': len(content),
            'identifier': identifier,
        }
        
        # Add detailed media information
        if media_files:
            dry_run_request['media_files_count'] = len(media_files)
            dry_run_request['media_files'] = []
            for idx, media_file in enumerate(media_files, 1):
                file_path = Path(media_file)
                file_size = file_path.stat().st_size if file_path.exists() else 0
                dry_run_request['media_files'].append({
                    'index': idx,
                    'path': str(media_file),
                    'filename': file_path.name,
                    'extension': file_path.suffix,
                    'size_bytes': file_size,
                    'size_kb': round(file_size / 1024, 2) if file_size > 0 else 0
                })
            
            # Determine embed type
            image_exts = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
            image_count = sum(1 for f in media_files if Path(f).suffix.lower() in image_exts)
            if image_count > 0:
                dry_run_request['embed_type'] = 'images'
                dry_run_request['embed_details'] = {
                    'type': 'app.bsky.embed.images',
                    'image_count': min(image_count, 4),
                    'note': f'{image_count} image(s) will be embedded (max 4 supported)'
                }
        
        # Add link information
        if link:
            dry_run_request['link'] = link
            dry_run_request['embed_type'] = 'external'
            dry_run_request['embed_details'] = {
                'type': 'app.bsky.embed.external',
                'note': 'Will attempt to fetch metadata to create a link card'
            }
        
        dry_run_guard("Bluesky", content, media_files, dry_run_request)
        
        # Authenticate using the AT Protocol SDK
        client = Client()
        try:
            client.login(identifier, password)
            logger.info("Successfully authenticated with Bluesky")
        except Exception as exc:
            logger.error(f"Bluesky authentication failed: {exc}")
            raise
        
        # Prepare images for embedding
        images = []
        if media_files:
            for media_file in media_files[:4]:  # Bluesky supports up to 4 images
                file_ext = Path(media_file).suffix.lower()
                
                # Only support images for now
                if file_ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
                    try:
                        with open(media_file, 'rb') as f:
                            img_data = f.read()
                        
                        # Upload the image and get the blob reference
                        upload_result = client.upload_blob(img_data)
                        images.append(models.AppBskyEmbedImages.Image(alt="", image=upload_result.blob))
                        logger.info(f"Successfully uploaded image: {media_file}")
                    except Exception as exc:
                        logger.error(f"Failed to upload image {media_file}: {exc}")
                        raise
                else:
                    logger.warning(f"Unsupported media type for Bluesky: {file_ext}")
        
        # Create the post with or without images/link card
        embed = None
        if images:
            embed = models.AppBskyEmbedImages.Main(images=images)
        elif link:
            # Attempt to create a link card embed
            metadata = fetch_link_metadata(link)
            if metadata:
                thumb_blob = None
                # If there's an image, download and upload it
                if metadata['image_url']:
                    try:
                        img_response = requests.get(metadata['image_url'], timeout=10)
                        img_response.raise_for_status()
                        
                        # Upload the thumbnail image
                        upload_result = client.upload_blob(img_response.content)
                        thumb_blob = upload_result.blob
                        logger.info(f"Successfully uploaded link card thumbnail from {metadata['image_url']}")
                    except Exception as exc:
                        logger.warning(f"Could not upload link card thumbnail: {exc}")

                external = models.AppBskyEmbedExternal.External(
                    uri=metadata['url'],
                    title=metadata['title'],
                    description=metadata['description'],
                    thumb=thumb_blob
                )
                embed = models.AppBskyEmbedExternal.Main(external=external)
        
        try:
            response = client.send_post(text=content, embed=embed)
            logger.info("Successfully created Bluesky post")
        except Exception as exc:
            logger.error(f"Failed to create Bluesky post: {exc}")
            raise
        
        # Extract post URI and construct URL
        post_uri = response.uri
        post_cid = response.cid
        
        # Construct the Bluesky post URL
        # URI format: at://did:plc:xxx/app.bsky.feed.post/xxx
        if post_uri:
            parts = post_uri.split('/')
            if len(parts) >= 3:
                post_id = parts[-1]
                # Get handle from the client session
                handle = client.me.handle if hasattr(client.me, 'handle') else identifier
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
