"""
Common utilities for social media posting actions.
"""

import os
import sys
import logging
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
        logging.info(f"[DRY RUN] Would post to {platform}.")
        logging.info(f"[DRY RUN] Content: {content}")
        logging.info(f"[DRY RUN] Media files: {media_files}")
        logging.info(f"[DRY RUN] Request body: {request_body}")
        print(f"[DRY RUN] Would post to {platform}.")
        print(f"[DRY RUN] Content: {content}")
        print(f"[DRY RUN] Media files: {media_files}")
        print(f"[DRY RUN] Request body: {request_body}")
        sys.exit(0)

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
    """Get a required environment variable or exit with error."""
    value = os.getenv(var_name)
    if not value:
        logging.error(f"Required environment variable {var_name} not found")
        sys.exit(1)
    return value




def get_optional_env_var(var_name: str, default: str = "") -> str:
    """Get an optional environment variable with default value."""
    return os.getenv(var_name, default)


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