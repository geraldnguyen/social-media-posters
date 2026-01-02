"""
Common utilities for social media posting actions.
"""

import os
import sys
import logging
import json
from typing import Optional, Dict, Any
import requests
from pathlib import Path

from datetime import datetime, timezone, timedelta

# --- DRY RUN GUARD ---
def dry_run_guard(platform: str, content: str, media_files: list, request_body: dict):
    """
    If DRY_RUN env var is set to true, print info and exit instead of posting.
    """
    dry_run = os.getenv('DRY_RUN', '').lower() in ('1', 'true', 'yes')
    if dry_run:
        print("=" * 80)
        print(f"[DRY RUN MODE] Would post to {platform}")
        print("=" * 80)
        
        # Format and print request details
        print("\n📝 POST CONTENT:")
        print(f"   {content}")
        
        # Print text details
        if 'text_length' in request_body:
            print(f"\n📊 TEXT DETAILS:")
            print(f"   Length: {request_body['text_length']} characters")
        
        # Print link information
        if 'link' in request_body:
            print(f"\n🔗 LINK:")
            print(f"   {request_body['link']}")
            if 'link_note' in request_body:
                print(f"   Note: {request_body['link_note']}")
        
        # Print media files with details
        if media_files:
            print(f"\n🖼️  MEDIA FILES:")
            if isinstance(request_body.get('media_files'), list):
                for media_info in request_body['media_files']:
                    print(f"   [{media_info['index']}] {media_info['filename']}")
                    print(f"       Path: {media_info['path']}")
                    print(f"       Size: {media_info['size_kb']} KB ({media_info['size_bytes']} bytes)")
                    print(f"       Type: {media_info['extension']}")
            else:
                print(f"   {request_body.get('media_files', media_files)}")
        
        # Print embed information
        if 'embed_type' in request_body:
            print(f"\n🎨 EMBED:")
            print(f"   Type: {request_body['embed_type']}")
            if 'embed_details' in request_body:
                details = request_body['embed_details']
                for key, value in details.items():
                    print(f"   {key.replace('_', ' ').title()}: {value}")
        
        # Print raw request body for debugging
        print(f"\n🔧 RAW REQUEST DATA:")
        # Create a copy without redundant fields for cleaner output
        clean_request = {k: v for k, v in request_body.items() 
                        if k not in ['media_files', 'embed_details'] or not isinstance(v, (list, dict))}
        print(f"   {json.dumps(clean_request, indent=2)}")
        
        print("\n" + "=" * 80)
        print("[DRY RUN MODE] No actual post was created")
        print("=" * 80)
        
        # Also log for consistency
        logging.info(f"[DRY RUN] Would post to {platform}.")
        logging.info(f"[DRY RUN] Content: {content}")
        logging.info(f"[DRY RUN] Media files: {media_files}")
        
        sys.exit(0)

# Global cache for JSON config
_json_config_cache: Optional[Dict[str, Any]] = None
_json_config_loaded = False


def load_json_config() -> Optional[Dict[str, Any]]:
    """
    Load configuration from a JSON file if available.
    
    The JSON file path is determined by:
    1. INPUT_FILE environment variable
    2. input.json in the current directory (default)
    
    Returns:
        Dictionary containing the JSON config, or None if file doesn't exist or is invalid
    """
    global _json_config_cache, _json_config_loaded
    
    # Return cached config if already loaded
    if _json_config_loaded:
        return _json_config_cache
    
    _json_config_loaded = True
    
    # Determine the input file path
    input_file = os.getenv('INPUT_FILE', 'input.json')
    
    # Convert relative path to absolute path based on current working directory
    if not os.path.isabs(input_file):
        input_file = os.path.join(os.getcwd(), input_file)
    
    # Check if file exists
    if not os.path.exists(input_file):
        logging.debug(f"JSON config file not found: {input_file}")
        return None
    
    # Load and parse JSON file
    try:
        with open(input_file, 'r') as f:
            config = json.load(f)
        logging.info(f"Loaded configuration from JSON file: {input_file}")
        logging.debug(f"JSON config keys: {list(config.keys()) if isinstance(config, dict) else 'not a dict'}")
        _json_config_cache = config
        return config
    except json.JSONDecodeError as e:
        logging.error(f"Failed to parse JSON config file {input_file}: {e}")
        return None
    except Exception as e:
        logging.error(f"Error reading JSON config file {input_file}: {e}")
        return None


def setup_logging(level: str = "INFO") -> logging.Logger:
    """Setup logging configuration for social media actions."""
    log_level = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    return logging.getLogger(__name__)


def get_required_env_var(var_name: str) -> str:
    """
    Get a required environment variable or exit with error.
    
    Falls back to JSON config if environment variable is not set.
    """
    value = os.getenv(var_name)
    if not value:
        # Try to get from JSON config
        json_config = load_json_config()
        if json_config and isinstance(json_config, dict):
            value = json_config.get(var_name)
        
        if not value:
            logging.error(f"Required parameter {var_name} not found in environment or JSON config")
            sys.exit(1)
        else:
            logging.debug(f"Parameter {var_name} loaded from JSON config")
    return value




def get_optional_env_var(var_name: str, default: str = "") -> str:
    """
    Get an optional environment variable with default value.
    
    Falls back to JSON config if environment variable is not set.
    """
    value = os.getenv(var_name)
    if not value:
        # Try to get from JSON config
        json_config = load_json_config()
        if json_config and isinstance(json_config, dict):
            value = json_config.get(var_name)
        
        if value:
            logging.debug(f"Parameter {var_name} loaded from JSON config")
        else:
            value = default
    return value


def validate_post_content(content: str, max_length: Optional[int] = None) -> bool:
    """Validate post content length and format."""
    if not content or not content.strip():
        logging.error("Post content cannot be empty")
        return False
    
    logging.info(f"Validating post content of length {len(content)}: {content!r}")
    if max_length and len(content) > max_length:
        logging.error(f"Post content exceeds maximum length of {max_length} characters")
        return False
    
    return True


def handle_api_error(error: Exception, platform: str) -> None:
    """Handle API errors consistently across platforms."""
    logging.error(f"Error posting to {platform}: {str(error)}")
    sys.exit(1)


def log_success(platform: str, post_id: Optional[str] = None) -> None:
    """Log successful post creation."""
    if post_id:
        logging.info(f"Successfully posted to {platform}. Post ID: {post_id}")
    else:
        logging.info(f"Successfully posted to {platform}")


def download_file_if_url(file_path, max_download_size_mb=5):
    """
    If file_path is an http(s) URL and file size is less than max_download_size_mb, download it and return the local path.
    Otherwise, return the original file_path.
    """
    max_bytes = max_download_size_mb * 1024 * 1024
    local_path = file_path
    if file_path.startswith("http://") or file_path.startswith("https://"):
        try:
            resp = requests.get(file_path, stream=True, timeout=10)
            resp.raise_for_status()
            content_length = resp.headers.get('Content-Length')
            if content_length and int(content_length) > max_bytes:
                raise ValueError(f"File at {file_path} exceeds max size of {max_download_size_mb}MB")
            # Download to temp file
            suffix = Path(file_path).suffix or ".tmp"
            temp = Path("_downloaded_media_" + os.urandom(8).hex() + suffix)
            total = 0
            with open(temp, "wb") as f:
                for chunk in resp.iter_content(1024 * 64):
                    total += len(chunk)
                    if total > max_bytes:
                        f.close()
                        temp.unlink(missing_ok=True)
                        raise ValueError(f"File at {file_path} exceeds max size of {max_download_size_mb}MB while downloading")
                    f.write(chunk)
            local_path = str(temp)
        except Exception as e:
            logging.error(f"Failed to download media from {file_path}: {str(e)}")
            raise
    return local_path


def parse_media_files(media_input: str, max_download_size_mb: int = 5):
    """
    Parse media files input (comma-separated paths). For remote files, download if under max_download_size_mb.
    Returns a list of local file paths (downloaded or original).
    """
    if not media_input:
        return []

    media_files = [f.strip() for f in media_input.split(',') if f.strip()]
    local_files = []
    for file_path in media_files:
        local_path = download_file_if_url(file_path, max_download_size_mb)
        if not os.path.exists(local_path):
            logging.error(f"Media file not found: {file_path}")
            sys.exit(1)
        local_files.append(local_path)
    return local_files