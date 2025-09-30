"""
YouTube Channel Manager

Handles YouTube channel discovery, validation, and CRUD operations.
"""

import os
import re
import logging
from typing import Optional, Dict, List
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from sqlalchemy.exc import IntegrityError
from database import get_db_session
from models import Channel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# YouTube API configuration
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')

if not YOUTUBE_API_KEY:
    logger.warning("YOUTUBE_API_KEY not found in environment variables. Channel fetching will not work.")


def get_youtube_client():
    """
    Get YouTube API client.

    Returns:
        Resource: YouTube API client.

    Raises:
        ValueError: If YOUTUBE_API_KEY is not set.
    """
    if not YOUTUBE_API_KEY:
        raise ValueError("YOUTUBE_API_KEY environment variable is not set. Please add it to your .env file.")

    return build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)


def extract_channel_id_from_url(url: str) -> Optional[str]:
    """
    Extract channel ID from various YouTube URL formats.

    Supports:
    - https://www.youtube.com/channel/UC...
    - https://www.youtube.com/@username
    - https://www.youtube.com/c/channelname
    - https://www.youtube.com/user/username

    Args:
        url: YouTube channel URL.

    Returns:
        Channel ID if found, None otherwise.
    """
    # Pattern 1: Direct channel ID URL
    channel_id_pattern = r'youtube\.com/channel/([a-zA-Z0-9_-]+)'
    match = re.search(channel_id_pattern, url)
    if match:
        return match.group(1)

    # Pattern 2: Handle URL (need to resolve via API)
    handle_pattern = r'youtube\.com/@([a-zA-Z0-9_-]+)'
    match = re.search(handle_pattern, url)
    if match:
        handle = match.group(1)
        return resolve_handle_to_channel_id(handle)

    # Pattern 3: Custom URL (need to resolve via API)
    custom_pattern = r'youtube\.com/c/([a-zA-Z0-9_-]+)'
    match = re.search(custom_pattern, url)
    if match:
        custom_name = match.group(1)
        return resolve_custom_url_to_channel_id(custom_name)

    # Pattern 4: Username (legacy, need to resolve via API)
    user_pattern = r'youtube\.com/user/([a-zA-Z0-9_-]+)'
    match = re.search(user_pattern, url)
    if match:
        username = match.group(1)
        return resolve_username_to_channel_id(username)

    return None


def resolve_handle_to_channel_id(handle: str) -> Optional[str]:
    """
    Resolve YouTube handle (@username) to channel ID.

    Args:
        handle: YouTube handle (without @).

    Returns:
        Channel ID if found, None otherwise.
    """
    try:
        youtube = get_youtube_client()

        # Search for channel by handle
        request = youtube.search().list(
            part='snippet',
            q=f"@{handle}",
            type='channel',
            maxResults=1
        )
        response = request.execute()

        if response['items']:
            return response['items'][0]['snippet']['channelId']

    except Exception as e:
        logger.error(f"Failed to resolve handle {handle}: {e}")

    return None


def resolve_custom_url_to_channel_id(custom_name: str) -> Optional[str]:
    """
    Resolve custom URL to channel ID.

    Args:
        custom_name: Custom channel name.

    Returns:
        Channel ID if found, None otherwise.
    """
    try:
        youtube = get_youtube_client()

        # Search for channel by custom name
        request = youtube.search().list(
            part='snippet',
            q=custom_name,
            type='channel',
            maxResults=1
        )
        response = request.execute()

        if response['items']:
            return response['items'][0]['snippet']['channelId']

    except Exception as e:
        logger.error(f"Failed to resolve custom URL {custom_name}: {e}")

    return None


def resolve_username_to_channel_id(username: str) -> Optional[str]:
    """
    Resolve legacy username to channel ID.

    Args:
        username: YouTube username.

    Returns:
        Channel ID if found, None otherwise.
    """
    try:
        youtube = get_youtube_client()

        # Try channels API with forUsername parameter
        request = youtube.channels().list(
            part='id',
            forUsername=username
        )
        response = request.execute()

        if response['items']:
            return response['items'][0]['id']

    except Exception as e:
        logger.error(f"Failed to resolve username {username}: {e}")

    return None


def fetch_channel_metadata(channel_id: str) -> Optional[Dict]:
    """
    Fetch channel metadata from YouTube API.

    Args:
        channel_id: YouTube channel ID.

    Returns:
        Dictionary with channel information, or None if not found.
    """
    try:
        youtube = get_youtube_client()

        request = youtube.channels().list(
            part='snippet,statistics',
            id=channel_id
        )
        response = request.execute()

        if not response['items']:
            logger.error(f"Channel {channel_id} not found")
            return None

        channel_data = response['items'][0]
        snippet = channel_data['snippet']
        statistics = channel_data.get('statistics', {})

        return {
            'channel_id': channel_id,
            'channel_name': snippet['title'],
            'description': snippet.get('description', ''),
            'thumbnail_url': snippet['thumbnails']['high']['url'],
            'subscriber_count': statistics.get('subscriberCount', 0),
            'video_count': statistics.get('videoCount', 0),
            'custom_url': snippet.get('customUrl', '')
        }

    except HttpError as e:
        logger.error(f"YouTube API error fetching channel {channel_id}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error fetching channel metadata: {e}")
        return None


def add_channel(url: str) -> tuple[Optional[Channel], Optional[str]]:
    """
    Add a new YouTube channel to the database.

    Args:
        url: YouTube channel URL.

    Returns:
        Tuple of (Channel object, error message).
        If successful, returns (channel, None).
        If failed, returns (None, error_message).
    """
    # Extract channel ID from URL
    channel_id = extract_channel_id_from_url(url)
    if not channel_id:
        return None, "Could not extract channel ID from URL. Please provide a valid YouTube channel URL."

    # Fetch channel metadata
    metadata = fetch_channel_metadata(channel_id)
    if not metadata:
        return None, f"Channel not found or YouTube API error. Please verify the URL and try again."

    # Create channel object
    try:
        with get_db_session() as session:
            # Check if channel already exists
            existing_channel = session.query(Channel).filter_by(channel_id=channel_id).first()
            if existing_channel:
                return None, f"Channel '{metadata['channel_name']}' is already subscribed."

            # Create new channel
            new_channel = Channel(
                channel_id=channel_id,
                channel_name=metadata['channel_name'],
                channel_url=url,
                thumbnail_url=metadata['thumbnail_url']
            )
            session.add(new_channel)
            session.commit()

            logger.info(f"Added channel: {metadata['channel_name']} ({channel_id})")
            return new_channel, None

    except IntegrityError:
        return None, "Channel already exists in database."
    except Exception as e:
        logger.error(f"Database error adding channel: {e}")
        return None, f"Database error: {str(e)}"


def get_all_channels() -> List[Channel]:
    """
    Get all subscribed channels from database.

    Returns:
        List of Channel objects.
    """
    try:
        with get_db_session() as session:
            channels = session.query(Channel).order_by(Channel.channel_name).all()
            # Detach from session to avoid lazy loading issues
            session.expunge_all()
            return channels
    except Exception as e:
        logger.error(f"Error fetching channels: {e}")
        return []


def get_channel_by_id(channel_db_id: int) -> Optional[Channel]:
    """
    Get channel by database ID.

    Args:
        channel_db_id: Database ID of the channel.

    Returns:
        Channel object or None if not found.
    """
    try:
        with get_db_session() as session:
            channel = session.query(Channel).filter_by(id=channel_db_id).first()
            if channel:
                session.expunge(channel)
            return channel
    except Exception as e:
        logger.error(f"Error fetching channel {channel_db_id}: {e}")
        return None


def delete_channel(channel_db_id: int) -> tuple[bool, Optional[str]]:
    """
    Delete a channel from the database.
    This will also delete all associated videos (cascade delete).

    Args:
        channel_db_id: Database ID of the channel to delete.

    Returns:
        Tuple of (success, error_message).
    """
    try:
        with get_db_session() as session:
            channel = session.query(Channel).filter_by(id=channel_db_id).first()
            if not channel:
                return False, "Channel not found."

            channel_name = channel.channel_name
            session.delete(channel)
            session.commit()

            logger.info(f"Deleted channel: {channel_name} (ID: {channel_db_id})")
            return True, None

    except Exception as e:
        logger.error(f"Error deleting channel {channel_db_id}: {e}")
        return False, f"Database error: {str(e)}"


def get_channel_count() -> int:
    """
    Get total number of subscribed channels.

    Returns:
        Number of channels.
    """
    try:
        with get_db_session() as session:
            count = session.query(Channel).count()
            return count
    except Exception as e:
        logger.error(f"Error counting channels: {e}")
        return 0