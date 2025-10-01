#!/usr/bin/env python3
"""
Cleanup script to remove old videos and orphaned videos from the database.
"""

import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from models import Video, Channel, ProcessingStatus
from database import get_db_session

# Load environment variables
load_dotenv()

def cleanup_old_videos(days=3):
    """Delete videos older than specified number of days."""
    cutoff_date = datetime.now() - timedelta(days=days)

    print(f"\n=== Deleting videos older than {days} days (before {cutoff_date.strftime('%Y-%m-%d')}) ===")

    with get_db_session() as session:
        # Find old videos
        old_videos = session.query(Video).filter(
            Video.published_at < cutoff_date
        ).all()

        print(f"Found {len(old_videos)} old videos to delete")

        if old_videos:
            for video in old_videos:
                print(f"  - Deleting: {video.title} (published: {video.published_at.strftime('%Y-%m-%d')})")
                session.delete(video)

            session.commit()
            print(f"[OK] Deleted {len(old_videos)} old videos")
        else:
            print("No old videos to delete")

    return len(old_videos)

def cleanup_orphaned_videos():
    """Delete videos whose channels no longer exist."""
    print("\n=== Deleting orphaned videos (channels deleted) ===")

    with get_db_session() as session:
        # Get all valid channel IDs
        valid_channel_ids = [c.id for c in session.query(Channel.id).all()]

        # Find videos with invalid channel_id
        orphaned_videos = session.query(Video).filter(
            ~Video.channel_id.in_(valid_channel_ids) if valid_channel_ids else Video.channel_id.isnot(None)
        ).all()

        print(f"Found {len(orphaned_videos)} orphaned videos to delete")

        if orphaned_videos:
            for video in orphaned_videos:
                print(f"  - Deleting: {video.title} (channel_id: {video.channel_id})")
                session.delete(video)

            session.commit()
            print(f"[OK] Deleted {len(orphaned_videos)} orphaned videos")
        else:
            print("No orphaned videos to delete")

    return len(orphaned_videos)

def show_stats():
    """Show current database statistics."""
    print("\n=== Current Database Stats ===")

    with get_db_session() as session:
        video_count = session.query(Video).count()
        channel_count = session.query(Channel).count()

        # Count videos by status
        pending_count = session.query(Video).filter(Video.processing_status == ProcessingStatus.PENDING).count()
        completed_count = session.query(Video).filter(Video.processing_status == ProcessingStatus.COMPLETED).count()
        failed_count = session.query(Video).filter(Video.processing_status == ProcessingStatus.FAILED).count()

        print(f"Total channels: {channel_count}")
        print(f"Total videos: {video_count}")
        print(f"  - Pending: {pending_count}")
        print(f"  - Completed: {completed_count}")
        print(f"  - Failed: {failed_count}")

if __name__ == '__main__':
    print("=" * 60)
    print("VIDEO CLEANUP UTILITY")
    print("=" * 60)

    # Show stats before cleanup
    show_stats()

    # Confirm deletion
    print("\n" + "=" * 60)
    response = input("\nProceed with cleanup? (yes/no): ").strip().lower()

    if response not in ['yes', 'y']:
        print("Cleanup cancelled.")
        exit(0)

    # Perform cleanup
    old_deleted = cleanup_old_videos(days=3)
    orphaned_deleted = cleanup_orphaned_videos()

    # Show stats after cleanup
    show_stats()

    print("\n" + "=" * 60)
    print(f"CLEANUP COMPLETE")
    print(f"Total deleted: {old_deleted + orphaned_deleted} videos")
    print("=" * 60)
