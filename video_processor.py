"""
Video Processor

Processes videos from database: extracts captions and generates summaries.
"""

import logging
from typing import Optional, List, Dict
from database import get_db_session
from models import Video, ProcessingStatus
from caption_extractor import get_captions
from gemini_summarizer import generate_short_summary, generate_detailed_summary

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def process_single_video(video_db_id: int) -> tuple[bool, Optional[str]]:
    """
    Process a single video: extract captions and generate summaries.

    Args:
        video_db_id: Database ID of the video to process.

    Returns:
        Tuple of (success, error_message).
    """
    try:
        with get_db_session() as session:
            # Get video
            video = session.query(Video).filter_by(id=video_db_id).first()
            if not video:
                return False, "Video not found"

            # Update status to processing
            video.processing_status = ProcessingStatus.PROCESSING
            session.commit()

            video_id = video.video_id
            video_title = video.title

        logger.info(f"Processing video: {video_title} ({video_id})")

        # Step 1: Extract captions
        logger.info(f"  Step 1/3: Extracting captions for {video_id}")
        captions, language_code = get_captions(video_id, preferred_languages=['pl', 'en'])

        # Check if caption extraction failed - look for specific error message patterns
        error_patterns = [
            "Invalid YouTube video ID",
            "Transcripts are disabled",
            "No transcripts found",
            "Video not found or captions are not available",
            "Could not retrieve transcript:"
        ]

        is_error = not captions or language_code is None or any(captions.startswith(pattern) for pattern in error_patterns)

        if is_error:
            logger.warning(f"  Caption extraction failed for {video_id}: {captions[:100] if captions else 'Empty response'}")
            with get_db_session() as session:
                video = session.query(Video).filter_by(id=video_db_id).first()
                video.processing_status = ProcessingStatus.FAILED
                video.caption_text = f"Caption extraction failed: {captions}"
                session.commit()
            return False, f"Caption extraction failed: {captions}"

        logger.info(f"  Extracted {len(captions)} characters of captions (language: {language_code})")

        # Step 2: Generate short summary
        logger.info(f"  Step 2/3: Generating short summary for {video_id}")
        try:
            short_summary = generate_short_summary(captions, language_code)
            logger.info(f"  Generated short summary ({len(short_summary)} chars)")
        except Exception as e:
            logger.error(f"  Short summary generation failed: {e}")
            short_summary = f"Summary generation failed: {str(e)}"

        # Step 3: Generate detailed summary
        logger.info(f"  Step 3/3: Generating detailed summary for {video_id}")
        try:
            detailed_summary = generate_detailed_summary(captions, language_code)
            logger.info(f"  Generated detailed summary ({len(detailed_summary)} chars)")
        except Exception as e:
            logger.error(f"  Detailed summary generation failed: {e}")
            detailed_summary = f"Summary generation failed: {str(e)}"

        # Update database with results
        with get_db_session() as session:
            video = session.query(Video).filter_by(id=video_db_id).first()
            video.caption_text = captions
            video.short_summary = short_summary
            video.detailed_summary = detailed_summary
            video.processing_status = ProcessingStatus.COMPLETED
            session.commit()

        logger.info(f"✓ Successfully processed video: {video_title}")
        return True, None

    except Exception as e:
        logger.error(f"Error processing video {video_db_id}: {e}")

        # Update status to failed
        try:
            with get_db_session() as session:
                video = session.query(Video).filter_by(id=video_db_id).first()
                if video:
                    video.processing_status = ProcessingStatus.FAILED
                    session.commit()
        except:
            pass

        return False, str(e)


def process_pending_videos(max_videos: int = 10) -> Dict[str, any]:
    """
    Process pending videos in batch (limited by max_videos).

    Args:
        max_videos: Maximum number of videos to process in this batch.

    Returns:
        Dictionary with processing statistics.
    """
    stats = {
        'total_processed': 0,
        'successful': 0,
        'failed': 0,
        'errors': []
    }

    try:
        # Get pending videos
        with get_db_session() as session:
            pending_videos = (
                session.query(Video)
                .filter_by(processing_status=ProcessingStatus.PENDING)
                .order_by(Video.created_at)
                .limit(max_videos)
                .all()
            )

            if not pending_videos:
                logger.info("No pending videos to process")
                return stats

            # Detach from session
            session.expunge_all()

        logger.info(f"Processing {len(pending_videos)} pending videos")

        for video in pending_videos:
            stats['total_processed'] += 1
            success, error = process_single_video(video.id)

            if success:
                stats['successful'] += 1
            else:
                stats['failed'] += 1
                stats['errors'].append({
                    'video_id': video.video_id,
                    'title': video.title,
                    'error': error
                })

        logger.info(f"Batch processing complete: {stats}")
        return stats

    except Exception as e:
        logger.error(f"Error in batch processing: {e}")
        stats['errors'].append({'error': str(e)})
        return stats


def reprocess_failed_videos(max_videos: int = 5) -> Dict[str, any]:
    """
    Retry processing for failed videos.

    Args:
        max_videos: Maximum number of failed videos to retry.

    Returns:
        Dictionary with processing statistics.
    """
    stats = {
        'total_processed': 0,
        'successful': 0,
        'failed': 0,
        'errors': []
    }

    try:
        # Get failed videos
        with get_db_session() as session:
            failed_videos = (
                session.query(Video)
                .filter_by(processing_status=ProcessingStatus.FAILED)
                .order_by(Video.created_at)
                .limit(max_videos)
                .all()
            )

            if not failed_videos:
                logger.info("No failed videos to reprocess")
                return stats

            # Detach from session
            session.expunge_all()

        logger.info(f"Reprocessing {len(failed_videos)} failed videos")

        for video in failed_videos:
            # Reset to pending before reprocessing
            with get_db_session() as session:
                video_obj = session.query(Video).filter_by(id=video.id).first()
                video_obj.processing_status = ProcessingStatus.PENDING
                session.commit()

            stats['total_processed'] += 1
            success, error = process_single_video(video.id)

            if success:
                stats['successful'] += 1
            else:
                stats['failed'] += 1
                stats['errors'].append({
                    'video_id': video.video_id,
                    'title': video.title,
                    'error': error
                })

        logger.info(f"Reprocessing complete: {stats}")
        return stats

    except Exception as e:
        logger.error(f"Error in reprocessing: {e}")
        stats['errors'].append({'error': str(e)})
        return stats


def get_processing_stats() -> Dict[str, int]:
    """
    Get video processing statistics.

    Returns:
        Dictionary with counts by status.
    """
    try:
        with get_db_session() as session:
            total = session.query(Video).count()
            pending = session.query(Video).filter_by(processing_status=ProcessingStatus.PENDING).count()
            processing = session.query(Video).filter_by(processing_status=ProcessingStatus.PROCESSING).count()
            completed = session.query(Video).filter_by(processing_status=ProcessingStatus.COMPLETED).count()
            failed = session.query(Video).filter_by(processing_status=ProcessingStatus.FAILED).count()

            return {
                'total': total,
                'pending': pending,
                'processing': processing,
                'completed': completed,
                'failed': failed
            }
    except Exception as e:
        logger.error(f"Error getting processing stats: {e}")
        return {
            'total': 0,
            'pending': 0,
            'processing': 0,
            'completed': 0,
            'failed': 0
        }