"""
Common utilities for social media posting actions.
"""

import os
import sys
import logging
import json
import re
from typing import Optional, Dict, Any
import requests
from pathlib import Path

from datetime import datetime, timezone, timedelta

# Module-level logger
logger = logging.getLogger(__name__)

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
        logger.debug(f"JSON config file not found: {input_file}")
        return None
    
    # Load and parse JSON file
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        logger.info(f"Loaded configuration from JSON file: {input_file}")
        logger.debug(f"JSON config keys: {list(config.keys()) if isinstance(config, dict) else 'not a dict'}")
        _json_config_cache = config
        return config
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON config file {input_file}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error reading JSON config file {input_file}: {e}")
        return None


def setup_logging(level: str = "INFO") -> logging.Logger:
    """Setup logging configuration for social media actions."""
    log_level = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True,  # overwrite any existing logging configuration
    )
    logger = logging.getLogger(__name__)
    logger.setLevel(log_level)
    return logger


def _convert_json_value_to_string(value: Any) -> str:
    """
    Convert a JSON value to a string format compatible with environment variables.
    
    Args:
        value: Value from JSON config (can be list, bool, int, float, str, None, or dict)
    
    Returns:
        String representation suitable for environment variable usage
    """
    if value is None:
        return ""
    elif isinstance(value, bool):
        # Convert boolean to lowercase string (true/false)
        return str(value).lower()
    elif isinstance(value, list):
        # Join list elements with commas, converting each element to string
        return ",".join(str(item) for item in value)
    elif isinstance(value, dict):
        # Convert dict to JSON string for complex structures
        return json.dumps(value)
    else:
        # For numbers and strings, convert to string
        return str(value)


def get_required_env_var(var_name: str) -> str:
    """
    Get a required environment variable or exit with error.
    
    Falls back to JSON config if environment variable is not set.
    JSON values are automatically converted to strings to match environment variable behavior.
    """
    value = os.getenv(var_name)
    if not value:
        # Try to get from JSON config
        json_config = load_json_config()
        if json_config and isinstance(json_config, dict):
            json_value = json_config.get(var_name)
            if json_value is not None:
                value = _convert_json_value_to_string(json_value)
                logger.debug(f"Parameter {var_name} loaded from JSON config and converted to string")
        
        if not value:
            logger.error(f"Required parameter {var_name} not found in environment or JSON config")
            sys.exit(1)
    return value




def get_optional_env_var(var_name: str, default: str = "") -> str:
    """
    Get an optional environment variable with default value.
    
    Falls back to JSON config if environment variable is not set.
    JSON values are automatically converted to strings to match environment variable behavior.
    """
    value = os.getenv(var_name)
    if not value:
        # Try to get from JSON config
        json_config = load_json_config()
        if json_config and isinstance(json_config, dict):
            json_value = json_config.get(var_name)
            if json_value is not None:
                value = _convert_json_value_to_string(json_value)
                logger.debug(f"Parameter {var_name} loaded from JSON config and converted to string")
        
        if not value:
            value = default
    return value


# --- DRY RUN GUARD ---
def dry_run_guard(platform: str, content: str, media_files: list, request_body: dict):
    """
    If DRY_RUN env var is set to true, print info and exit instead of posting.
    """
    dry_run = get_optional_env_var('DRY_RUN', '').lower() in ('1', 'true', 'yes')
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
        logger.info(f"[DRY RUN] Would post to {platform}.")
        logger.info(f"[DRY RUN] Content: {content}")
        logger.info(f"[DRY RUN] Media files: {media_files}")
        
        sys.exit(0)


def validate_post_content(content: str, max_length: Optional[int] = None) -> bool:
    """Validate post content length and format."""
    if not content or not content.strip():
        logger.error("Post content cannot be empty")
        return False
    
    logger.info(f"Validating post content of length {len(content)}: {content!r}")
    if max_length and len(content) > max_length:
        logger.error(f"Post content exceeds maximum length of {max_length} characters")
        return False
    
    return True


def is_value_empty_or_na(value: str) -> bool:
    """
    Check if a value is empty, None, or represents "N/A" or its variations.
    
    This function treats the following as empty:
    - None
    - Empty string
    - Whitespace-only strings
    - "N/A" (case-insensitive)
    - "n.a" (case-insensitive)
    - "n/a" (case-insensitive)
    - "not applicable" (case-insensitive)
    - "na" (case-insensitive)
    - "n a" (case-insensitive)
    
    Args:
        value: The string value to check
        
    Returns:
        True if the value is empty or represents N/A, False otherwise
    """
    if not value or not value.strip():
        return True
    
    # Normalize the value for comparison: lowercase and remove extra spaces
    normalized = value.strip().lower()
    
    # List of N/A variations to check
    na_variations = [
        'n/a',
        'n.a',
        'n.a.',
        'na',
        'n a',
        'not applicable',
        'notapplicable',
        'not-applicable'
    ]
    
    return normalized in na_variations


def handle_api_error(error: Exception, platform: str) -> None:
    """Handle API errors consistently across platforms."""
    logger.error(f"Error posting to {platform}: {str(error)}")
    sys.exit(1)


def log_success(platform: str, post_id: Optional[str] = None) -> None:
    """Log successful post creation."""
    if post_id:
        logger.info(f"Successfully posted to {platform}. Post ID: {post_id}")
    else:
        logger.info(f"Successfully posted to {platform}")


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
            logger.error(f"Failed to download media from {file_path}: {str(e)}")
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
            logger.error(f"Media file not found: {file_path}")
            sys.exit(1)
        local_files.append(local_path)
    return local_files


def parse_scheduled_time(scheduled_time: str) -> Optional[str]:
    """
    Parse scheduled time in either ISO 8601 format or offset format.
    
    Supported formats:
    1. ISO 8601 datetime string (e.g., '2024-12-31T23:59:59Z' or '2024-12-31T23:59:59+00:00')
    2. Offset format: '+<offset><time-unit>' where:
       - '+' means present time PLUS the offset period
       - <offset> is a positive integer
       - <time-unit> can be 'd' (days), 'h' (hours), 'm' (minutes)
       Examples: '+1d' (1 day from now), '+2h' (2 hours from now), '+30m' (30 minutes from now)
    
    Args:
        scheduled_time: Time string in one of the supported formats
    
    Returns:
        ISO 8601 formatted datetime string in UTC, or None if input is empty/None
    
    Raises:
        ValueError: If the format is invalid
    """
    if not scheduled_time:
        return None
    
    scheduled_time = scheduled_time.strip()
    
    # After stripping, check if empty
    if not scheduled_time:
        return None
    
    # Check if it's an offset format
    if scheduled_time.startswith('+'):
        return _parse_offset_time(scheduled_time)
    
    # Otherwise, treat as ISO 8601 datetime
    try:
        # Parse the datetime string
        # Try with timezone first
        try:
            dt = datetime.fromisoformat(scheduled_time.replace('Z', '+00:00'))
        except ValueError:
            # Try without timezone (assume UTC)
            dt = datetime.fromisoformat(scheduled_time)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
        
        # Convert to UTC if needed
        if dt.tzinfo != timezone.utc:
            dt = dt.astimezone(timezone.utc)
        
        # Return in ISO 8601 format
        return dt.strftime('%Y-%m-%dT%H:%M:%SZ')
    
    except ValueError as e:
        logger.error(f"Invalid datetime format '{scheduled_time}': {e}")
        raise ValueError(
            f"Invalid scheduled time format. Expected ISO 8601 datetime "
            f"(e.g., '2024-12-31T23:59:59Z') or offset format "
            f"(e.g., '+1d', '+2h', '+30m'). Got: '{scheduled_time}'"
        )


def _parse_offset_time(offset_str: str) -> str:
    """
    Parse offset time format and return ISO 8601 datetime string.
    
    Args:
        offset_str: Offset string in format '+<offset><time-unit>'
                   Example: '+1d', '+2h', '+30m'
    
    Returns:
        ISO 8601 formatted datetime string in UTC
    
    Raises:
        ValueError: If the offset format is invalid
    """
    # Parse the offset string: +<number><unit>
    match = re.match(r'^\+(\d+)([dhm])$', offset_str)
    if not match:
        raise ValueError(
            f"Invalid offset format '{offset_str}'. "
            f"Expected format: '+<offset><time-unit>' where offset is a positive integer "
            f"and time-unit is 'd' (days), 'h' (hours), or 'm' (minutes). "
            f"Examples: '+1d', '+2h', '+30m'"
        )
    
    offset_value = int(match.group(1))
    time_unit = match.group(2)
    
    # Calculate the target datetime
    now = datetime.now(timezone.utc)
    
    if time_unit == 'd':
        target_dt = now + timedelta(days=offset_value)
    elif time_unit == 'h':
        target_dt = now + timedelta(hours=offset_value)
    elif time_unit == 'm':
        target_dt = now + timedelta(minutes=offset_value)
    else:
        raise ValueError(f"Invalid time unit '{time_unit}'. Must be 'd', 'h', or 'm'.")
    
    # Return in ISO 8601 format
    return target_dt.strftime('%Y-%m-%dT%H:%M:%SZ')