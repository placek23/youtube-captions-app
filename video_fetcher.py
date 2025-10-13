"""
YouTube Video Fetcher

Fetches videos from subscribed YouTube channels and stores them in the database.
"""

import os
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from sqlalchemy.exc import IntegrityError
from database import get_db_session
from models import Channel, Video, ProcessingStatus

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# YouTube API configuration
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')

# Default number of videos to fetch per channel
DEFAULT_MAX_RESULTS = 50


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


def fetch_channel_videos(channel_id: str, max_results: int = DEFAULT_MAX_RESULTS) -> List[Dict]:
    """
    Fetch latest videos from a YouTube channel (from last 3 days only).

    Args:
        channel_id: YouTube channel ID.
        max_results: Maximum number of videos to fetch (default: 50).

    Returns:
        List of video dictionaries with metadata.
    """
    videos = []

    try:
        youtube = get_youtube_client()

        # Calculate 3 days ago threshold (timezone-aware)
        from datetime import timezone
        three_days_ago = datetime.now(timezone.utc) - timedelta(days=3)

        # Get uploads playlist ID
        channel_request = youtube.channels().list(
            part='contentDetails',
            id=channel_id
        )
        channel_response = channel_request.execute()

        if not channel_response['items']:
            logger.warning(f"Channel {channel_id} not found")
            return []

        uploads_playlist_id = channel_response['items'][0]['contentDetails']['relatedPlaylists']['uploads']

        # Fetch videos from uploads playlist
        next_page_token = None
        fetched_count = 0
        should_continue = True

        while should_continue and fetched_count < max_results:
            playlist_request = youtube.playlistItems().list(
                part='snippet,contentDetails',
                playlistId=uploads_playlist_id,
                maxResults=min(50, max_results - fetched_count),  # API max is 50 per request
                pageToken=next_page_token
            )
            playlist_response = playlist_request.execute()

            for item in playlist_response['items']:
                snippet = item['snippet']
                video_id = item['contentDetails']['videoId']

                # Parse published date
                published_at = None
                try:
                    published_at = datetime.fromisoformat(snippet['publishedAt'].replace('Z', '+00:00'))
                except Exception as e:
                    logger.warning(f"Failed to parse date for video {video_id}: {e}")
                    continue

                # Filter: Only include videos from last 3 days
                if published_at and published_at < three_days_ago:
                    # Videos are ordered by date (newest first), so we can stop here
                    logger.info(f"Reached videos older than 3 days, stopping fetch")
                    should_continue = False
                    break

                video_data = {
                    'video_id': video_id,
                    'title': snippet['title'],
                    'thumbnail_url': snippet['thumbnails']['high']['url'] if 'high' in snippet['thumbnails'] else snippet['thumbnails']['default']['url'],
                    'published_at': published_at,
                    'description': snippet.get('description', '')
                }
                videos.append(video_data)
                fetched_count += 1

            # Check if there are more pages
            next_page_token = playlist_response.get('nextPageToken')
            if not next_page_token or fetched_count >= max_results:
                break

        logger.info(f"Fetched {len(videos)} videos from channel {channel_id} (last 3 days)")
        return videos

    except HttpError as e:
        logger.error(f"YouTube API error fetching videos for channel {channel_id}: {e}")
        return []
    except Exception as e:
        logger.error(f"Error fetching videos for channel {channel_id}: {e}")
        return []


def store_videos_in_database(channel_db_id: int, videos: List[Dict]) -> tuple[int, int]:
    """
    Store fetched videos in the database.

    Args:
        channel_db_id: Database ID of the channel.
        videos: List of video dictionaries.

    Returns:
        Tuple of (new_videos_count, skipped_videos_count).
    """
    new_count = 0
    skipped_count = 0

    try:
        with get_db_session() as session:
            # Verify channel exists
            channel = session.query(Channel).filter_by(id=channel_db_id).first()
            if not channel:
                logger.error(f"Channel {channel_db_id} not found in database")
                return 0, 0

            for video_data in videos:
                try:
                    # Check if video already exists
                    existing_video = session.query(Video).filter_by(video_id=video_data['video_id']).first()
                    if existing_video:
                        skipped_count += 1
                        continue

                    # Create new video record
                    new_video = Video(
                        channel_id=channel_db_id,
                        video_id=video_data['video_id'],
                        title=video_data['title'],
                        thumbnail_url=video_data['thumbnail_url'],
                        published_at=video_data['published_at'],
                        processing_status=ProcessingStatus.PENDING
                    )
                    session.add(new_video)
                    new_count += 1

                except IntegrityError:
                    # Duplicate video (race condition)
                    session.rollback()
                    skipped_count += 1
                except Exception as e:
                    logger.error(f"Error storing video {video_data['video_id']}: {e}")
                    session.rollback()

            session.commit()
            logger.info(f"Stored {new_count} new videos, skipped {skipped_count} existing videos")
            return new_count, skipped_count

    except Exception as e:
        logger.error(f"Database error storing videos: {e}")
        return 0, 0


def sync_channel_videos(channel_db_id: int, max_results: int = DEFAULT_MAX_RESULTS) -> tuple[int, int, Optional[str]]:
    """
    Sync videos for a specific channel (fetch from YouTube and store in database).

    Args:
        channel_db_id: Database ID of the channel.
        max_results: Maximum number of videos to fetch.

    Returns:
        Tuple of (new_videos_count, skipped_videos_count, error_message).
        If successful, error_message is None.
    """
    try:
        with get_db_session() as session:
            # Get channel
            channel = session.query(Channel).filter_by(id=channel_db_id).first()
            if not channel:
                return 0, 0, "Channel not found"

            channel_id = channel.channel_id
            channel_name = channel.channel_name

        logger.info(f"Syncing videos for channel: {channel_name} ({channel_id})")

        # Fetch videos from YouTube
        videos = fetch_channel_videos(channel_id, max_results)

        if not videos:
            # No videos found is a valid state (channel may not have posted recently)
            logger.info(f"Sync complete for {channel_name}: 0 videos found")
            return 0, 0, None

        # Store videos in database
        new_count, skipped_count = store_videos_in_database(channel_db_id, videos)

        logger.info(f"Sync complete for {channel_name}: {new_count} new, {skipped_count} skipped")
        return new_count, skipped_count, None

    except Exception as e:
        logger.error(f"Error syncing channel {channel_db_id}: {e}")
        return 0, 0, str(e)


def sync_all_channels(max_results_per_channel: int = DEFAULT_MAX_RESULTS) -> Dict[str, any]:
    """
    Sync videos for all subscribed channels.

    Args:
        max_results_per_channel: Maximum number of videos to fetch per channel.

    Returns:
        Dictionary with sync statistics.
    """
    stats = {
        'total_channels': 0,
        'successful_channels': 0,
        'failed_channels': 0,
        'total_new_videos': 0,
        'total_skipped_videos': 0,
        'errors': []
    }

    try:
        with get_db_session() as session:
            channels = session.query(Channel).all()
            stats['total_channels'] = len(channels)

            for channel in channels:
                new_count, skipped_count, error = sync_channel_videos(channel.id, max_results_per_channel)

                if error:
                    stats['failed_channels'] += 1
                    stats['errors'].append({
                        'channel_name': channel.channel_name,
                        'error': error
                    })
                else:
                    stats['successful_channels'] += 1
                    stats['total_new_videos'] += new_count
                    stats['total_skipped_videos'] += skipped_count

        logger.info(f"Sync all channels complete: {stats}")
        return stats

    except Exception as e:
        logger.error(f"Error syncing all channels: {e}")
        stats['errors'].append({'error': str(e)})
        return stats


def get_video_count_by_channel(channel_db_id: int) -> int:
    """
    Get number of videos for a specific channel.

    Args:
        channel_db_id: Database ID of the channel.

    Returns:
        Number of videos.
    """
    try:
        with get_db_session() as session:
            count = session.query(Video).filter_by(channel_id=channel_db_id).count()
            return count
    except Exception as e:
        logger.error(f"Error counting videos for channel {channel_db_id}: {e}")
        return 0


def get_pending_videos_count() -> int:
    """
    Get number of videos pending processing.

    Returns:
        Number of pending videos.
    """
    try:
        with get_db_session() as session:
            count = session.query(Video).filter_by(processing_status=ProcessingStatus.PENDING).count()
            return count
    except Exception as e:
        logger.error(f"Error counting pending videos: {e}")
        return 0