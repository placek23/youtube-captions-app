"""
Input validation utilities for YouTube URL processing and parameter validation.

This module provides comprehensive validation for user inputs to prevent
injection attacks and ensure data integrity.
"""

import re
from urllib.parse import urlparse, parse_qs
from typing import Tuple, Optional


# YouTube URL patterns
YOUTUBE_WATCH_PATTERN = re.compile(
    r'^https?://(www\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})(&.*)?$'
)
YOUTUBE_SHORT_PATTERN = re.compile(
    r'^https?://youtu\.be/([a-zA-Z0-9_-]{11})(\?.*)?$'
)
YOUTUBE_CHANNEL_URL_PATTERN = re.compile(
    r'^https?://(www\.)?youtube\.com/(channel/|c/|@|user/)([a-zA-Z0-9_-]+)$'
)
YOUTUBE_VIDEO_ID_PATTERN = re.compile(r'^[a-zA-Z0-9_-]{11}$')
YOUTUBE_CHANNEL_ID_PATTERN = re.compile(r'^UC[a-zA-Z0-9_-]{22}$')

# Limits
MAX_VIDEOS_PER_REQUEST = 50
MAX_VIDEOS_BATCH_PROCESS = 20
MAX_PAGE_SIZE = 50
MAX_URL_LENGTH = 2048
MAX_TEXT_LENGTH = 1000000  # 1MB


def validate_youtube_video_url(url: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Validate YouTube video URL and extract video ID.

    Args:
        url: YouTube video URL to validate

    Returns:
        Tuple of (is_valid, video_id, error_message)

    Examples:
        >>> validate_youtube_video_url("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        (True, "dQw4w9WgXcQ", None)

        >>> validate_youtube_video_url("https://youtu.be/dQw4w9WgXcQ")
        (True, "dQw4w9WgXcQ", None)

        >>> validate_youtube_video_url("https://example.com/video")
        (False, None, "Not a valid YouTube URL")
    """
    if not url or not isinstance(url, str):
        return False, None, "URL is required"

    # Check URL length
    if len(url) > MAX_URL_LENGTH:
        return False, None, "URL is too long"

    # Strip whitespace
    url = url.strip()

    try:
        parsed_url = urlparse(url)

        # Validate scheme
        if parsed_url.scheme not in ('http', 'https'):
            return False, None, "Invalid URL scheme (must be http or https)"

        # Check for YouTube domain
        if 'youtube.com' in parsed_url.netloc:
            # Handle youtube.com/watch?v=VIDEO_ID format
            if parsed_url.path == '/watch':
                query_params = parse_qs(parsed_url.query)
                video_ids = query_params.get('v')
                if video_ids and len(video_ids) > 0:
                    video_id = video_ids[0]
                    if YOUTUBE_VIDEO_ID_PATTERN.match(video_id):
                        return True, video_id, None
                return False, None, "Invalid or missing video ID in URL"
            else:
                return False, None, "Invalid YouTube URL format (expected /watch?v=...)"

        elif 'youtu.be' in parsed_url.netloc:
            # Handle youtu.be/VIDEO_ID format
            video_id = parsed_url.path.lstrip('/')
            if video_id and YOUTUBE_VIDEO_ID_PATTERN.match(video_id):
                return True, video_id, None
            return False, None, "Invalid video ID in short URL"
        else:
            return False, None, "Not a valid YouTube URL"

    except Exception as e:
        return False, None, f"URL parsing error: {str(e)}"


def validate_youtube_channel_url(url: str) -> Tuple[bool, Optional[str]]:
    """
    Validate YouTube channel URL format.

    Args:
        url: YouTube channel URL to validate

    Returns:
        Tuple of (is_valid, error_message)

    Examples:
        >>> validate_youtube_channel_url("https://www.youtube.com/channel/UCxxx")
        (True, None)

        >>> validate_youtube_channel_url("https://example.com/channel")
        (False, "Not a valid YouTube channel URL")
    """
    if not url or not isinstance(url, str):
        return False, "Channel URL is required"

    # Check URL length
    if len(url) > MAX_URL_LENGTH:
        return False, "URL is too long"

    # Strip whitespace
    url = url.strip()

    try:
        parsed_url = urlparse(url)

        # Validate scheme
        if parsed_url.scheme not in ('http', 'https'):
            return False, "Invalid URL scheme (must be http or https)"

        # Check for YouTube domain
        if 'youtube.com' not in parsed_url.netloc:
            return False, "Not a valid YouTube channel URL"

        # Check path format (channel/, c/, @, user/)
        path = parsed_url.path
        if not any(path.startswith(prefix) for prefix in ['/channel/', '/c/', '/@', '/user/']):
            return False, "Invalid channel URL format (expected /channel/, /c/, /@, or /user/)"

        return True, None

    except Exception as e:
        return False, f"URL parsing error: {str(e)}"


def validate_video_id(video_id: str) -> Tuple[bool, Optional[str]]:
    """
    Validate YouTube video ID format.

    Args:
        video_id: Video ID to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not video_id or not isinstance(video_id, str):
        return False, "Video ID is required"

    video_id = video_id.strip()

    if not YOUTUBE_VIDEO_ID_PATTERN.match(video_id):
        return False, "Invalid video ID format (must be 11 characters: a-zA-Z0-9_-)"

    return True, None


def validate_channel_id(channel_id: str) -> Tuple[bool, Optional[str]]:
    """
    Validate YouTube channel ID format (UC + 22 chars).

    Args:
        channel_id: Channel ID to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not channel_id or not isinstance(channel_id, str):
        return False, "Channel ID is required"

    channel_id = channel_id.strip()

    if not YOUTUBE_CHANNEL_ID_PATTERN.match(channel_id):
        return False, "Invalid channel ID format (must start with UC and be 24 characters total)"

    return True, None


def validate_pagination_params(page: int, per_page: int) -> Tuple[bool, int, int, Optional[str]]:
    """
    Validate and sanitize pagination parameters.

    Args:
        page: Page number (1-indexed)
        per_page: Items per page

    Returns:
        Tuple of (is_valid, sanitized_page, sanitized_per_page, error_message)
    """
    try:
        # Convert to int if possible
        page = int(page) if page is not None else 1
        per_page = int(per_page) if per_page is not None else 20

        # Validate ranges
        if page < 1:
            page = 1

        if per_page < 1:
            per_page = 20
        elif per_page > MAX_PAGE_SIZE:
            per_page = MAX_PAGE_SIZE

        return True, page, per_page, None

    except (ValueError, TypeError) as e:
        return False, 1, 20, f"Invalid pagination parameters: {str(e)}"


def validate_max_videos(max_videos: int, max_allowed: int = MAX_VIDEOS_PER_REQUEST) -> Tuple[bool, int, Optional[str]]:
    """
    Validate and sanitize max_videos parameter.

    Args:
        max_videos: Requested maximum number of videos
        max_allowed: Maximum allowed value (default: MAX_VIDEOS_PER_REQUEST)

    Returns:
        Tuple of (is_valid, sanitized_max_videos, error_message)
    """
    try:
        max_videos = int(max_videos) if max_videos is not None else 10

        if max_videos < 1:
            max_videos = 10
        elif max_videos > max_allowed:
            max_videos = max_allowed

        return True, max_videos, None

    except (ValueError, TypeError) as e:
        return False, 10, f"Invalid max_videos parameter: {str(e)}"


def sanitize_text(text: str, max_length: int = MAX_TEXT_LENGTH) -> str:
    """
    Sanitize text input by limiting length and stripping dangerous characters.

    Args:
        text: Text to sanitize
        max_length: Maximum allowed length

    Returns:
        Sanitized text
    """
    if not text or not isinstance(text, str):
        return ""

    # Limit length
    text = text[:max_length]

    # Strip leading/trailing whitespace
    text = text.strip()

    return text


def validate_integer_id(id_value: any, field_name: str = "ID") -> Tuple[bool, Optional[int], Optional[str]]:
    """
    Validate integer ID parameter.

    Args:
        id_value: ID value to validate
        field_name: Name of the field for error messages

    Returns:
        Tuple of (is_valid, sanitized_id, error_message)
    """
    try:
        id_int = int(id_value)

        if id_int < 1:
            return False, None, f"{field_name} must be a positive integer"

        return True, id_int, None

    except (ValueError, TypeError):
        return False, None, f"Invalid {field_name} (must be a positive integer)"


# Export all validators
__all__ = [
    'validate_youtube_video_url',
    'validate_youtube_channel_url',
    'validate_video_id',
    'validate_channel_id',
    'validate_pagination_params',
    'validate_max_videos',
    'sanitize_text',
    'validate_integer_id',
    'MAX_VIDEOS_PER_REQUEST',
    'MAX_VIDEOS_BATCH_PROCESS',
    'MAX_PAGE_SIZE',
]
