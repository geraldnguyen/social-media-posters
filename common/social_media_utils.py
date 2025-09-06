"""Common utilities for social media posting actions."""

import os
import sys
import logging
from typing import Optional, Dict, Any


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


def parse_media_files(media_input: str) -> list:
    """Parse media files input (comma-separated paths)."""
    if not media_input:
        return []
    
    media_files = [f.strip() for f in media_input.split(',') if f.strip()]
    
    # Validate files exist
    for file_path in media_files:
        if not os.path.exists(file_path):
            logging.error(f"Media file not found: {file_path}")
            sys.exit(1)
    
    return media_files