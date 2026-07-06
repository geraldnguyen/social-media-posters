#!/usr/bin/env python3
"""
Post videos to TikTok using the TikTok Content Posting API v2.

Supports:
- Instant publishing (DIRECT_POST mode)
- Scheduled publishing (DIRECT_POST with scheduled_publish_time)
- Local file upload (FILE_UPLOAD source)
- Remote URL upload (PULL_FROM_URL source)
- Configurable privacy, duet/stitch/comment settings
- AI-generated content labelling (is_aigc)
- Dry-run mode
- Save post response to JSON file
- Templated content via CONTENT_JSON
"""

import os
import sys
import json
import math
import time
import logging
import requests
from pathlib import Path
from typing import Optional, Dict, Any

# Module-level logger
logger = logging.getLogger(__name__)

# Load environment variables from a local .env file if present (for local development)
try:
    from dotenv import load_dotenv
    env_path = Path.cwd() / '.env'
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
except ImportError:
    pass  # python-dotenv not installed; skip loading .env

# Add common module to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'common'))

from templating_utils import process_templated_contents
from social_media_utils import (
    setup_logging,
    get_required_env_var,
    get_optional_env_var,
    handle_api_error,
    log_success,
    download_file_if_url,
    dry_run_guard,
    parse_scheduled_time,
    save_post_response,
)

# TikTok API constants
TIKTOK_API_BASE = "https://open.tiktokapis.com"
DEFAULT_CHUNK_SIZE_MB = 10           # 10 MB per chunk
MAX_CHUNK_SIZE_MB = 64               # TikTok maximum chunk size
MIN_CHUNK_SIZE_MB = 5                # TikTok minimum chunk size
MAX_VIDEO_SIZE_MB = 4096             # 4 GB practical upper limit
MAX_DESCRIPTION_LENGTH = 2200        # TikTok caption character limit
STATUS_POLL_MAX_ATTEMPTS = 30        # Maximum status polling attempts
STATUS_POLL_INTERVAL_SECS = 5        # Seconds between each status poll

# Valid TikTok privacy levels
VALID_PRIVACY_LEVELS = [
    "PUBLIC_TO_EVERYONE",
    "MUTUAL_FOLLOW_FRIENDS",
    "FOLLOWER_OF_CREATOR",
    "SELF_ONLY",
]


class TikTokAPI:
    """Client for the TikTok Content Posting API v2."""

    def __init__(
        self,
        access_token: Optional[str] = None,
        client_key: Optional[str] = None,
        client_secret: Optional[str] = None,
        refresh_token: Optional[str] = None,
    ):
        self.access_token = access_token
        self.client_key = client_key
        self.client_secret = client_secret
        self.refresh_token = refresh_token

    # ------------------------------------------------------------------
    # Authentication
    # ------------------------------------------------------------------

    def refresh_access_token(self) -> None:
        """Obtain a new access token using the refresh token grant."""
        if not all([self.client_key, self.client_secret, self.refresh_token]):
            raise ValueError(
                "TIKTOK_CLIENT_KEY, TIKTOK_CLIENT_SECRET, and TIKTOK_REFRESH_TOKEN are "
                "all required to refresh the TikTok access token."
            )
        logger.info("Refreshing TikTok access token")
        url = f"{TIKTOK_API_BASE}/v2/oauth/token/"
        payload = {
            "client_key": self.client_key,
            "client_secret": self.client_secret,
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token,
        }
        response = requests.post(url, data=payload, timeout=30)
        logger.debug(f"Token refresh response: {response.status_code} — {response.text}")
        response.raise_for_status()

        resp_json = response.json()
        error_info = resp_json.get("error")
        if error_info and error_info.get("code") not in ("ok", None, ""):
            raise RuntimeError(f"TikTok token refresh error: {resp_json}")

        token_data = resp_json.get("data", resp_json)
        self.access_token = token_data.get("access_token")
        if not self.access_token:
            raise RuntimeError(f"TikTok token refresh did not return access_token: {resp_json}")

        # Keep refresh token fresh when a new one is issued
        new_refresh = token_data.get("refresh_token")
        if new_refresh:
            self.refresh_token = new_refresh
            logger.debug("Stored updated refresh token")

        logger.info("Successfully refreshed TikTok access token")

    def _ensure_access_token(self) -> None:
        """Make sure we have a valid access token, refreshing if necessary."""
        if not self.access_token:
            if self.refresh_token:
                self.refresh_access_token()
            else:
                raise ValueError(
                    "No TikTok access token available. "
                    "Set TIKTOK_ACCESS_TOKEN, or supply TIKTOK_REFRESH_TOKEN + "
                    "TIKTOK_CLIENT_KEY + TIKTOK_CLIENT_SECRET."
                )

    def _get_headers(self) -> Dict[str, str]:
        """Build HTTP headers with the current bearer token."""
        self._ensure_access_token()
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json; charset=UTF-8",
        }

    # ------------------------------------------------------------------
    # API methods
    # ------------------------------------------------------------------

    def query_creator_info(self) -> Dict[str, Any]:
        """
        Query the authenticated creator's posting configuration.

        Returns allowed video durations, privacy levels, and other metadata.
        This call is informational; failure is non-fatal.
        """
        logger.info("Querying TikTok creator info")
        url = f"{TIKTOK_API_BASE}/v2/post/publish/creator_info/query/"
        response = requests.post(url, headers=self._get_headers(), json={}, timeout=30)
        logger.debug(f"creator_info response: {response.status_code} — {response.text}")
        response.raise_for_status()

        data = response.json()
        error_info = data.get("error", {})
        if error_info.get("code") not in ("ok", None, ""):
            logger.warning(f"TikTok creator_info returned non-ok: {data}")

        creator_data = data.get("data", {})
        max_duration = creator_data.get("max_video_post_duration_sec")
        privacy_opts = creator_data.get("privacy_level_options", [])
        logger.info(
            f"TikTok creator info — "
            f"max_video_duration={max_duration}s, "
            f"privacy_levels={privacy_opts}"
        )
        return creator_data

    def init_video_upload(
        self,
        post_info: Dict[str, Any],
        source_info: Dict[str, Any],
        post_mode: str = "DIRECT_POST",
    ) -> Dict[str, Any]:
        """
        Initialise a video upload job and return the publish_id (and upload_url
        for FILE_UPLOAD source).
        """
        logger.info(f"Initialising TikTok video upload — mode={post_mode}, source={source_info.get('source')}")
        url = f"{TIKTOK_API_BASE}/v2/post/publish/video/init/"
        body = {
            "post_info": post_info,
            "source_info": source_info,
            "post_mode": post_mode,
        }
        logger.debug(f"Init request body:\n{json.dumps(body, indent=2)}")
        response = requests.post(url, headers=self._get_headers(), json=body, timeout=30)
        logger.debug(f"Init response: {response.status_code} — {response.text}")
        response.raise_for_status()

        data = response.json()
        error_info = data.get("error", {})
        if error_info.get("code") not in ("ok", None, ""):
            raise RuntimeError(f"TikTok video init failed: {data}")

        result = data.get("data", {})
        logger.info(f"Video init successful — publish_id={result.get('publish_id')}")
        return result

    def upload_video_chunks(
        self, upload_url: str, file_path: str, chunk_size: int
    ) -> None:
        """
        Upload a local video file in chunks to *upload_url*.

        TikTok expects each chunk via an HTTP PUT with a Content-Range header.
        The final chunk receives a 200 response; intermediate chunks receive 206.
        """
        file_size = os.path.getsize(file_path)
        total_chunks = math.ceil(file_size / chunk_size)
        logger.info(
            f"Uploading '{Path(file_path).name}' to TikTok — "
            f"{file_size:,} bytes, {total_chunks} chunk(s) of {chunk_size:,} bytes each"
        )

        with open(file_path, "rb") as fh:
            for chunk_idx in range(total_chunks):
                start = chunk_idx * chunk_size
                chunk_data = fh.read(chunk_size)
                end = start + len(chunk_data) - 1

                logger.debug(
                    f"Uploading chunk {chunk_idx + 1}/{total_chunks} "
                    f"(bytes {start}–{end}/{file_size})"
                )
                headers = {
                    "Content-Range": f"bytes {start}-{end}/{file_size}",
                    "Content-Type": "video/mp4",
                    "Content-Length": str(len(chunk_data)),
                }
                response = requests.put(
                    upload_url, headers=headers, data=chunk_data, timeout=300
                )
                logger.debug(
                    f"Chunk {chunk_idx + 1} upload response: "
                    f"{response.status_code} — {response.text}"
                )
                if response.status_code not in (200, 206):
                    raise RuntimeError(
                        f"TikTok chunk {chunk_idx + 1} upload failed: "
                        f"HTTP {response.status_code} — {response.text}"
                    )
                logger.info(f"Chunk {chunk_idx + 1}/{total_chunks} uploaded")

        logger.info("All video chunks uploaded successfully")

    def check_publish_status(self, publish_id: str) -> Dict[str, Any]:
        """
        Poll the TikTok publish status endpoint until the video is published,
        fails, or the polling limit is reached.

        Returns the final status payload on success.
        Raises RuntimeError on failure or timeout.
        """
        logger.info(f"Polling TikTok publish status for publish_id={publish_id}")
        url = f"{TIKTOK_API_BASE}/v2/post/publish/status/fetch/"
        body = {"publish_id": publish_id}

        for attempt in range(1, STATUS_POLL_MAX_ATTEMPTS + 1):
            logger.debug(f"Status poll attempt {attempt}/{STATUS_POLL_MAX_ATTEMPTS}")
            response = requests.post(url, headers=self._get_headers(), json=body, timeout=30)
            logger.debug(f"Status response: {response.status_code} — {response.text}")
            response.raise_for_status()

            data = response.json()
            error_info = data.get("error", {})
            if error_info.get("code") not in ("ok", None, ""):
                raise RuntimeError(f"TikTok status fetch error: {data}")

            status_data = data.get("data", {})
            status = status_data.get("status", "")
            logger.info(f"TikTok publish status: {status}")

            if status == "PUBLISH_COMPLETE":
                logger.info("TikTok video published successfully")
                return status_data

            if status in ("FAILED", "PUBLISH_FAILED"):
                fail_reason = status_data.get("fail_reason", "unknown reason")
                raise RuntimeError(f"TikTok publish failed: {fail_reason}")

            # Still in progress
            if status in (
                "PROCESSING_UPLOAD",
                "PROCESSING_DOWNLOAD",
                "SEND_TO_USER_INBOX",
                "IN_PROGRESS",
            ):
                logger.info(
                    f"Publish in progress ({status}). "
                    f"Waiting {STATUS_POLL_INTERVAL_SECS}s before next check..."
                )
            else:
                logger.warning(
                    f"Unexpected publish status '{status}'. "
                    f"Waiting {STATUS_POLL_INTERVAL_SECS}s before next check..."
                )

            time.sleep(STATUS_POLL_INTERVAL_SECS)

        raise RuntimeError(
            f"TikTok publish timed out after {STATUS_POLL_MAX_ATTEMPTS} polling attempts "
            f"(publish_id={publish_id}). The video may still process — check your TikTok account."
        )


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def post_to_tiktok() -> None:
    """Load configuration and post a video to TikTok."""
    log_level = get_optional_env_var("LOG_LEVEL", "INFO")
    logger = setup_logging(log_level)
    logger.info("Starting TikTok post process")

    try:
        # -----------------------------------------------------------------------
        # Credentials
        # -----------------------------------------------------------------------
        access_token = get_optional_env_var("TIKTOK_ACCESS_TOKEN", "")
        client_key = get_optional_env_var("TIKTOK_CLIENT_KEY", "")
        client_secret = get_optional_env_var("TIKTOK_CLIENT_SECRET", "")
        refresh_token = get_optional_env_var("TIKTOK_REFRESH_TOKEN", "")

        if not access_token and not (client_key and client_secret and refresh_token):
            logger.error(
                "TikTok credentials missing. "
                "Provide TIKTOK_ACCESS_TOKEN, or provide all three of "
                "TIKTOK_CLIENT_KEY + TIKTOK_CLIENT_SECRET + TIKTOK_REFRESH_TOKEN."
            )
            sys.exit(1)

        logger.debug(
            f"Credentials — access_token={'set' if access_token else 'not set'}, "
            f"refresh_token={'set' if refresh_token else 'not set'}"
        )

        # -----------------------------------------------------------------------
        # Video file
        # -----------------------------------------------------------------------
        video_file = get_required_env_var("VIDEO_FILE")
        logger.info(f"Video file (raw): {video_file}")

        # -----------------------------------------------------------------------
        # Metadata
        # -----------------------------------------------------------------------
        description = get_optional_env_var("POST_CONTENT", "")
        privacy_level = get_optional_env_var("VIDEO_PRIVACY_LEVEL", "PUBLIC_TO_EVERYONE")
        disable_duet = get_optional_env_var("TIKTOK_DISABLE_DUET", "false").lower() in ("true", "1", "yes")
        disable_comment = get_optional_env_var("TIKTOK_DISABLE_COMMENT", "false").lower() in ("true", "1", "yes")
        disable_stitch = get_optional_env_var("TIKTOK_DISABLE_STITCH", "false").lower() in ("true", "1", "yes")
        brand_content = get_optional_env_var("TIKTOK_BRAND_CONTENT", "false").lower() in ("true", "1", "yes")
        brand_organic = get_optional_env_var("TIKTOK_BRAND_ORGANIC", "false").lower() in ("true", "1", "yes")
        is_aigc = get_optional_env_var("TIKTOK_IS_AIGC", "false").lower() in ("true", "1", "yes")
        cover_timestamp_ms = int(get_optional_env_var("TIKTOK_COVER_TIMESTAMP_MS", "1000"))

        chunk_size_mb = int(get_optional_env_var("TIKTOK_CHUNK_SIZE_MB", str(DEFAULT_CHUNK_SIZE_MB)))
        chunk_size_mb = max(MIN_CHUNK_SIZE_MB, min(chunk_size_mb, MAX_CHUNK_SIZE_MB))
        chunk_size = chunk_size_mb * 1024 * 1024
        logger.debug(f"Chunk size: {chunk_size_mb} MB ({chunk_size:,} bytes)")

        # -----------------------------------------------------------------------
        # Scheduling
        # -----------------------------------------------------------------------
        publish_at_str = get_optional_env_var("VIDEO_PUBLISH_AT", "")
        scheduled_publish_time: Optional[int] = None
        if publish_at_str:
            scheduled_iso = parse_scheduled_time(publish_at_str)
            if scheduled_iso:
                from datetime import datetime, timezone
                dt = datetime.fromisoformat(scheduled_iso.replace("Z", "+00:00"))
                scheduled_publish_time = int(dt.timestamp())
                logger.info(
                    f"Video scheduled for: {scheduled_iso} (Unix timestamp: {scheduled_publish_time})"
                )

        # -----------------------------------------------------------------------
        # Template processing
        # -----------------------------------------------------------------------
        (description,) = process_templated_contents(description)
        logger.debug(f"Processed description: {description!r}")

        # -----------------------------------------------------------------------
        # Validation
        # -----------------------------------------------------------------------
        if privacy_level not in VALID_PRIVACY_LEVELS:
            logger.warning(
                f"Privacy level '{privacy_level}' is not in the known list "
                f"{VALID_PRIVACY_LEVELS}. The API call may fail."
            )

        if description and len(description) > MAX_DESCRIPTION_LENGTH:
            logger.warning(
                f"Description length ({len(description)} chars) exceeds TikTok's "
                f"limit of {MAX_DESCRIPTION_LENGTH} characters. It will be truncated by TikTok."
            )

        if description and ("http://" in description or "https://" in description):
            logger.warning(
                "TikTok does not allow clickable URLs in video descriptions. "
                "Including URLs may cause the video to be rejected or shadowbanned. "
                "Consider using LINK_IN_COMMENT instead."
            )

        # -----------------------------------------------------------------------
        # Prepare local video file
        # -----------------------------------------------------------------------
        is_remote_source = video_file.startswith("http://") or video_file.startswith("https://")

        if is_remote_source:
            # Attempt to download the file (up to MAX_VIDEO_SIZE_MB)
            logger.info(f"Attempting to download video from URL: {video_file}")
            try:
                local_video_file = download_file_if_url(video_file, max_download_size_mb=MAX_VIDEO_SIZE_MB)
                logger.info(f"Downloaded video to: {local_video_file}")
            except Exception as download_err:
                # Download failed (e.g. too large) — fall back to PULL_FROM_URL
                logger.warning(
                    f"Could not download video from URL ({download_err}). "
                    f"Will use PULL_FROM_URL source instead."
                )
                local_video_file = video_file
        else:
            local_video_file = video_file

        # Decide upload source
        use_pull_from_url = (is_remote_source and local_video_file == video_file)

        if not use_pull_from_url:
            if not os.path.exists(local_video_file):
                logger.error(f"Video file not found: {local_video_file}")
                sys.exit(1)
            video_size = os.path.getsize(local_video_file)
            video_ext = Path(local_video_file).suffix.lower()
            logger.info(f"Local video: {local_video_file} ({video_size:,} bytes, ext={video_ext})")

            supported_formats = [".mp4", ".mov", ".webm", ".mpeg"]
            if video_ext not in supported_formats:
                logger.warning(
                    f"Video extension '{video_ext}' may not be supported by TikTok. "
                    f"Supported: {supported_formats}"
                )
        else:
            video_size = 0
            logger.info(f"Using PULL_FROM_URL source. TikTok will download from: {video_file}")

        # -----------------------------------------------------------------------
        # Build API request structures
        # -----------------------------------------------------------------------
        post_info: Dict[str, Any] = {
            "title": description,
            "privacy_level": privacy_level,
            "disable_duet": disable_duet,
            "disable_comment": disable_comment,
            "disable_stitch": disable_stitch,
            "video_cover_timestamp_ms": cover_timestamp_ms,
            "brand_content_toggle": brand_content,
            "brand_organic_toggle": brand_organic,
        }
        if is_aigc:
            post_info["is_aigc"] = True
        if scheduled_publish_time:
            post_info["scheduled_publish_time"] = scheduled_publish_time

        if use_pull_from_url:
            source_info: Dict[str, Any] = {
                "source": "PULL_FROM_URL",
                "video_url": video_file,
            }
        else:
            # TikTok requires chunk_size <= video_size; cap it when the file is
            # smaller than the configured chunk size (common for short clips).
            effective_chunk_size = min(chunk_size, video_size)
            if effective_chunk_size != chunk_size:
                logger.debug(
                    f"Adjusted chunk_size from {chunk_size:,} to {effective_chunk_size:,} bytes "
                    f"because the video ({video_size:,} bytes) is smaller than the configured chunk size."
                )
            total_chunk_count = math.ceil(video_size / effective_chunk_size)
            source_info = {
                "source": "FILE_UPLOAD",
                "video_size": video_size,
                "chunk_size": effective_chunk_size,
                "total_chunk_count": total_chunk_count,
            }

        post_mode = "DIRECT_POST"

        # -----------------------------------------------------------------------
        # Dry-run guard
        # -----------------------------------------------------------------------
        dry_run_request: Dict[str, Any] = {
            "post_mode": post_mode,
            "source": source_info["source"],
            "video_file": local_video_file,
            "description": description,
            "description_length": len(description) if description else 0,
            "privacy_level": privacy_level,
            "disable_duet": disable_duet,
            "disable_comment": disable_comment,
            "disable_stitch": disable_stitch,
            "brand_content": brand_content,
            "brand_organic": brand_organic,
            "is_aigc": is_aigc,
            "cover_timestamp_ms": cover_timestamp_ms,
        }
        if scheduled_publish_time:
            dry_run_request["scheduled_publish_time"] = scheduled_publish_time
        if not use_pull_from_url:
            dry_run_request["video_size_bytes"] = video_size
            dry_run_request["total_chunk_count"] = source_info.get("total_chunk_count")
            dry_run_request["effective_chunk_size_bytes"] = source_info.get("chunk_size")
            dry_run_request["chunk_size_mb"] = chunk_size_mb

        dry_run_guard("TikTok", description or "(no description)", [local_video_file], dry_run_request)

        # -----------------------------------------------------------------------
        # Post to TikTok
        # -----------------------------------------------------------------------
        api = TikTokAPI(
            access_token=access_token or None,
            client_key=client_key or None,
            client_secret=client_secret or None,
            refresh_token=refresh_token or None,
        )

        # Query creator info (informational, non-fatal)
        try:
            creator_info = api.query_creator_info()
            max_duration = creator_info.get("max_video_post_duration_sec")
            if max_duration:
                logger.info(f"Your TikTok account allows videos up to {max_duration} seconds")
        except Exception as creator_err:
            logger.warning(f"Could not query TikTok creator info (non-fatal): {creator_err}")

        # Initialise upload
        init_result = api.init_video_upload(post_info, source_info, post_mode)
        publish_id: str = init_result.get("publish_id", "")
        upload_url: Optional[str] = init_result.get("upload_url")

        if not publish_id:
            raise RuntimeError(f"TikTok video init did not return a publish_id: {init_result}")

        if source_info["source"] == "FILE_UPLOAD":
            if not upload_url:
                raise RuntimeError(
                    "TikTok video init did not return an upload_url for FILE_UPLOAD source."
                )
            # Upload video in chunks using the same effective chunk size that was
            # declared to the TikTok init endpoint.
            api.upload_video_chunks(upload_url, local_video_file, source_info["chunk_size"])
            logger.info("All chunks uploaded. Waiting for TikTok to process the video...")
        else:
            logger.info("PULL_FROM_URL source — TikTok is downloading the video. Waiting for processing...")

        # Poll for completion
        status_data = api.check_publish_status(publish_id)
        video_id: Optional[str] = status_data.get("video_id") or publish_id
        video_url: Optional[str] = (
            f"https://www.tiktok.com/@me/video/{video_id}" if status_data.get("video_id") else None
        )

        # -----------------------------------------------------------------------
        # Output
        # -----------------------------------------------------------------------
        if "GITHUB_OUTPUT" in os.environ:
            with open(os.environ["GITHUB_OUTPUT"], "a") as fh:
                fh.write(f"video-id={video_id}\n")
                if video_url:
                    fh.write(f"video-url={video_url}\n")

        save_post_response("tiktok", success=True, post_id=video_id, post_url=video_url)
        log_success("TikTok", video_id)
        if video_url:
            logger.info(f"TikTok video URL: {video_url}")

    except Exception as exc:
        save_post_response("tiktok", success=False, error=str(exc))
        handle_api_error(exc, "TikTok")


if __name__ == "__main__":
    post_to_tiktok()
