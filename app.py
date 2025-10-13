import os
import logging
from datetime import timedelta
from flask import Flask, request, jsonify, render_template, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from dotenv import load_dotenv
from caption_extractor import get_captions
from urllib.parse import urlparse, parse_qs, urljoin
from gemini_summarizer import summarize_text
from auth import get_user, authenticate_user
from channel_manager import add_channel, get_all_channels, get_channel_by_id, delete_channel, get_channel_count
from video_fetcher import sync_channel_videos, get_pending_videos_count
from video_processor import process_single_video, process_pending_videos, get_processing_stats
from models import Video, Channel, ProcessingStatus
from database import get_db_session
from sqlalchemy import desc
from validators import (
    validate_youtube_video_url,
    validate_youtube_channel_url,
    validate_pagination_params,
    validate_max_videos,
    sanitize_text,
    validate_integer_id,
    MAX_VIDEOS_BATCH_PROCESS
)
from startup_validator import run_startup_validation

# Load environment variables from .env file
load_dotenv(override=True)

# Run startup validation to ensure all required environment variables are present
try:
    run_startup_validation(strict=True)
except Exception as e:
    logging.error(f"Startup validation failed: {e}")
    raise

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Enforce SECRET_KEY requirement
secret_key = os.environ.get('SECRET_KEY')
if not secret_key:
    raise ValueError(
        "SECRET_KEY environment variable must be set. "
        "Please add it to your .env file with a strong random value."
    )
app.secret_key = secret_key

# Configure secure session cookies
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SECURE'] = os.environ.get('FLASK_ENV') == 'production'  # Enable for HTTPS
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=2)

# Detect if running on Vercel (serverless)
IS_SERVERLESS = os.environ.get('VERCEL') == '1' or os.environ.get('FLASK_ENV') == 'serverless'

# CSRF Configuration
if not IS_SERVERLESS:
    # Enable CSRF protection for traditional deployments
    app.config['WTF_CSRF_TIME_LIMIT'] = None
    app.config['WTF_CSRF_SSL_STRICT'] = False
    app.config['WTF_CSRF_CHECK_DEFAULT'] = True

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'

# Initialize CSRF protection (conditionally)
# Disabled for now - all routes are protected with @login_required
# if not IS_SERVERLESS:
#     csrf = CSRFProtect()
#     csrf.init_app(app)
#
#     # Make csrf_token available in all templates
#     @app.context_processor
#     def inject_csrf_token():
#         from flask_wtf.csrf import generate_csrf
#         return dict(csrf_token=generate_csrf)
# else:
csrf = None
# Provide a dummy csrf_token that always returns empty string
@app.context_processor
def inject_csrf_token():
    return dict(csrf_token=lambda: '')

# Initialize rate limiter
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

# Security headers middleware
@app.after_request
def set_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'  # Allow YouTube embeds
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "img-src 'self' data: https://img.youtube.com https://i.ytimg.com https://yt3.ggpht.com https://via.placeholder.com; "
        "frame-src https://www.youtube.com https://youtube.com; "  # Allow YouTube embeds
        "media-src 'self' https://www.youtube.com;"
    )
    return response

def is_safe_url(target):
    """Check if the target URL is safe for redirects."""
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc

@login_manager.user_loader
def load_user(user_id):
    return get_user(user_id)


@app.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def login():
    """Login page and authentication."""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = authenticate_user(username, password)
        if user:
            login_user(user, remember=True)  # Use remember=True for serverless compatibility
            logger.info(f"Successful login for user: {username}")

            # Safely handle redirect with open redirect protection
            next_page = request.args.get('next')
            if next_page and is_safe_url(next_page):
                return redirect(next_page)
            return redirect(url_for('index'))
        else:
            logger.warning(f"Failed login attempt for username: {username}")
            flash('Invalid username or password')

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    """Logout the current user."""
    logout_user()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    """Redirect to videos page (main landing page)."""
    return redirect(url_for('videos_page'))

@app.route('/videos')
@login_required
def videos_page():
    """Renders the videos list page."""
    return render_template('videos.html', current_user=current_user)

@app.route('/channels')
@login_required
def channels_page():
    """Renders the channel management page."""
    return render_template('channels.html', current_user=current_user)

@app.route('/video/<video_id>')
@login_required
def video_detail_page(video_id):
    """Renders the video detail page."""
    return render_template('video_detail.html', current_user=current_user, video_id=video_id)

@app.route('/process')
@login_required
def process_single_page():
    """Renders the single video processing page."""
    return render_template('process_single.html', current_user=current_user)

@app.route('/date-summary')
@login_required
def date_summary_page():
    """Renders the date range summary page."""
    return render_template('date_summary.html', current_user=current_user)

@app.route('/get_captions', methods=['POST'])
@login_required
@limiter.limit("10 per minute")
def get_captions_route():
    """API endpoint to fetch captions for a given YouTube URL."""
    data = request.get_json()
    video_url = data.get('video_url')

    if not video_url:
        return jsonify({'error': 'Video URL is required.'}), 400

    # Validate YouTube URL and extract video ID
    is_valid, video_id, error = validate_youtube_video_url(video_url)
    if not is_valid:
        logger.warning(f"Invalid YouTube URL: {video_url} - {error}")
        return jsonify({'error': error}), 400

    try:
        captions = get_captions(video_id)
        if not captions:
            return jsonify({'error': 'Could not retrieve captions for this video. It might be unavailable or private.'}), 404
        return jsonify({'captions': captions})
    except Exception as e:
        logger.error(f"Error getting captions for video {video_id}: {e}", exc_info=True)
        return jsonify({'error': 'An internal error occurred while fetching captions.'}), 500

@app.route('/summarize', methods=['POST'])
@login_required
@limiter.limit("5 per minute")
def summarize_route():
    """API endpoint to summarize the provided caption text."""
    data = request.get_json()
    caption_text = data.get('caption_text')
    if not caption_text:
        return jsonify({'error': 'Caption text is required.'}), 400

    try:
        summary = summarize_text(caption_text)
        return jsonify({'summary': summary})
    except Exception as e:
        logger.error(f"Error summarizing text: {e}", exc_info=True)
        return jsonify({'error': 'An error occurred while generating the summary. Please try again.'}), 500


@app.route('/api/summarize/date-range', methods=['POST'])
@login_required
@limiter.limit("5 per minute")
def summarize_date_range_route():
    """API endpoint to generate a comprehensive summary from multiple videos in a date range."""
    try:
        data = request.get_json()
        videos = data.get('videos')

        if not videos or not isinstance(videos, list) or len(videos) == 0:
            return jsonify({'error': 'Videos array is required and must not be empty'}), 400

        # Extract date range from videos
        dates = [v.get('published_at') for v in videos if v.get('published_at')]
        if not dates:
            return jsonify({'error': 'Videos must have published_at dates'}), 400

        start_date = min(dates)
        end_date = max(dates)

        # Detect language from videos (use majority language)
        from collections import Counter

        # Try to detect language from summaries or default to Polish
        detected_langs = []
        for video in videos:
            # Simple heuristic: if summary contains Polish characters, assume Polish
            summary_text = video.get('short_summary', '') + video.get('detailed_summary', '')
            if any(char in summary_text for char in 'ąćęłńóśźżĄĆĘŁŃÓŚŹŻ'):
                detected_langs.append('pl')
            else:
                detected_langs.append('en')

        # Use most common language, default to Polish
        if detected_langs:
            language_code = Counter(detected_langs).most_common(1)[0][0]
        else:
            language_code = 'pl'

        # Import the new function
        from gemini_summarizer import generate_date_range_summary

        # Generate the comprehensive summary
        summary = generate_date_range_summary(
            videos_data=videos,
            start_date=start_date,
            end_date=end_date,
            language_code=language_code
        )

        logger.info(f"Generated date range summary for {len(videos)} videos from {start_date} to {end_date}")

        return jsonify({
            'summary': summary,
            'video_count': len(videos),
            'start_date': start_date,
            'end_date': end_date,
            'language': language_code
        })

    except Exception as e:
        logger.error(f"Error generating date range summary: {e}", exc_info=True)
        return jsonify({'error': 'An error occurred while generating the summary. Please try again.'}), 500


# ============================================================================
# Channel Management API Endpoints
# ============================================================================

@app.route('/api/channels', methods=['GET'])
@login_required
def get_channels():
    """Get all subscribed channels."""
    try:
        channels = get_all_channels()
        return jsonify({
            'channels': [channel.to_dict() for channel in channels],
            'total': len(channels)
        })
    except Exception as e:
        logger.error(f"Error fetching channels: {e}")
        return jsonify({'error': 'Failed to fetch channels'}), 500


@app.route('/api/channels', methods=['POST'])
@login_required
@limiter.limit("10 per minute")
def add_channel_route():
    """Add a new YouTube channel subscription."""
    data = request.get_json()
    channel_url = data.get('channel_url') or data.get('url')  # Support both parameter names

    if not channel_url:
        return jsonify({'error': 'Channel URL is required'}), 400

    # Validate channel URL format
    is_valid, error = validate_youtube_channel_url(channel_url)
    if not is_valid:
        logger.warning(f"Invalid channel URL: {channel_url} - {error}")
        return jsonify({'error': error}), 400

    try:
        channel, error = add_channel(channel_url)

        if error:
            logger.warning(f"Failed to add channel {channel_url}: {error}")
            return jsonify({'error': error}), 400

        logger.info(f"Successfully added channel: {channel.channel_name} ({channel.channel_id})")
        return jsonify({
            'success': True,
            'channel': channel.to_dict(),
            'message': f'Successfully subscribed to {channel.channel_name}'
        }), 201

    except Exception as e:
        logger.error(f"Error adding channel {channel_url}: {e}", exc_info=True)
        return jsonify({'error': 'Failed to add channel. Please try again later.'}), 500


@app.route('/api/channels/<int:channel_id>', methods=['DELETE'])
@login_required
@limiter.limit("10 per minute")
def delete_channel_route(channel_id):
    """Delete a channel subscription."""
    # Validate channel ID
    is_valid, sanitized_id, error = validate_integer_id(channel_id, "Channel ID")
    if not is_valid:
        return jsonify({'error': error}), 400

    try:
        success, error = delete_channel(sanitized_id)

        if not success:
            logger.warning(f"Failed to delete channel {sanitized_id}: {error}")
            return jsonify({'error': error}), 404

        logger.info(f"Successfully deleted channel ID: {sanitized_id}")
        return jsonify({
            'success': True,
            'message': 'Channel deleted successfully'
        })

    except Exception as e:
        logger.error(f"Error deleting channel {sanitized_id}: {e}", exc_info=True)
        return jsonify({'error': 'Failed to delete channel. Please try again later.'}), 500


@app.route('/api/sync/channel/<int:channel_id>', methods=['POST'])
@login_required
@limiter.limit("5 per minute")
def sync_channel_route(channel_id):
    """Manually trigger video sync for a specific channel."""
    # Validate channel ID
    is_valid, sanitized_id, error = validate_integer_id(channel_id, "Channel ID")
    if not is_valid:
        return jsonify({'error': error}), 400

    try:
        max_videos = request.get_json().get('max_videos', 50) if request.is_json else 50

        # Validate max_videos
        is_valid, max_videos, error = validate_max_videos(max_videos, max_allowed=50)
        if not is_valid:
            return jsonify({'error': error}), 400

        new_count, skipped_count, error = sync_channel_videos(sanitized_id, max_videos)

        if error:
            return jsonify({'error': error}), 400

        return jsonify({
            'success': True,
            'new_videos': new_count,
            'skipped_videos': skipped_count,
            'message': f'Synced {new_count} new videos'
        })

    except Exception as e:
        logger.error(f"Error syncing channel: {e}")
        return jsonify({'error': 'Failed to sync channel'}), 500


@app.route('/api/sync/channels/bulk', methods=['POST'])
@login_required
@limiter.limit("3 per minute")
def bulk_sync_channels_route():
    """Sync multiple channels at once."""
    try:
        data = request.get_json()
        if not data or 'channel_ids' not in data:
            return jsonify({'error': 'channel_ids array is required'}), 400

        channel_ids = data['channel_ids']

        if not isinstance(channel_ids, list):
            return jsonify({'error': 'channel_ids must be an array'}), 400

        if len(channel_ids) == 0:
            return jsonify({'error': 'At least one channel ID is required'}), 400

        if len(channel_ids) > 20:
            return jsonify({'error': 'Maximum 20 channels can be synced at once'}), 400

        max_videos_per_channel = data.get('max_videos', 50)

        # Validate max_videos
        is_valid, max_videos_per_channel, error = validate_max_videos(max_videos_per_channel, max_allowed=50)
        if not is_valid:
            return jsonify({'error': error}), 400

        results = []
        total_new_videos = 0
        total_skipped_videos = 0
        failed_channels = []

        # Sync each channel
        for channel_id in channel_ids:
            # Validate each channel ID
            is_valid, sanitized_id, error = validate_integer_id(channel_id, "Channel ID")
            if not is_valid:
                failed_channels.append({'channel_id': channel_id, 'error': error})
                continue

            try:
                new_count, skipped_count, error = sync_channel_videos(sanitized_id, max_videos_per_channel)

                if error:
                    failed_channels.append({'channel_id': sanitized_id, 'error': error})
                else:
                    total_new_videos += new_count
                    total_skipped_videos += skipped_count
                    results.append({
                        'channel_id': sanitized_id,
                        'new_videos': new_count,
                        'skipped_videos': skipped_count
                    })
            except Exception as e:
                logger.error(f"Error syncing channel {sanitized_id}: {e}")
                failed_channels.append({'channel_id': sanitized_id, 'error': str(e)})

        response = {
            'success': True,
            'synced_channels': len(results),
            'total_new_videos': total_new_videos,
            'total_skipped_videos': total_skipped_videos,
            'message': f'Synced {len(results)} channels, found {total_new_videos} new videos'
        }

        if failed_channels:
            response['failed_channels'] = failed_channels
            response['message'] += f'. {len(failed_channels)} channels failed.'

        return jsonify(response)

    except Exception as e:
        logger.error(f"Error in bulk sync: {e}")
        return jsonify({'error': 'Failed to sync channels'}), 500


# ============================================================================
# Video Listing API Endpoints
# ============================================================================

@app.route('/api/videos', methods=['GET'])
@login_required
def get_videos():
    """Get paginated list of videos with optional channel filter and sorting."""
    try:
        # Get query parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        channel_id = request.args.get('channel_id', type=int)
        order_by = request.args.get('order_by', 'published_at_desc', type=str)

        # Validate and sanitize pagination parameters
        is_valid, page, per_page, error = validate_pagination_params(page, per_page)
        if not is_valid:
            return jsonify({'error': error}), 400

        # Validate channel_id if provided
        if channel_id is not None:
            is_valid, channel_id, error = validate_integer_id(channel_id, "Channel ID")
            if not is_valid:
                return jsonify({'error': error}), 400

        with get_db_session() as session:
            # Base query with eager loading of channel relationship
            from sqlalchemy.orm import joinedload
            from datetime import datetime, timedelta
            query = session.query(Video).options(joinedload(Video.channel))

            # Filter to videos from last 3 days
            three_days_ago = datetime.utcnow() - timedelta(days=3)
            query = query.filter(Video.published_at >= three_days_ago)

            # Filter by channel if specified
            if channel_id:
                query = query.filter(Video.channel_id == channel_id)

            # Apply sorting
            if order_by == 'published_at_asc':
                query = query.order_by(Video.published_at.asc())
            elif order_by == 'published_at_desc':
                query = query.order_by(Video.published_at.desc())
            elif order_by == 'title_asc':
                query = query.order_by(Video.title.asc())
            elif order_by == 'title_desc':
                query = query.order_by(Video.title.desc())
            else:
                # Default to newest first
                query = query.order_by(Video.published_at.desc())

            # Get total count
            total_count = query.count()

            # Apply pagination
            offset = (page - 1) * per_page
            videos = query.offset(offset).limit(per_page).all()

            # Detach from session
            session.expunge_all()

        # Calculate pagination info
        total_pages = (total_count + per_page - 1) // per_page

        return jsonify({
            'videos': [video.to_dict(include_detailed=False) for video in videos],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total_count': total_count,
                'total_pages': total_pages,
                'has_next': page < total_pages,
                'has_prev': page > 1
            }
        })

    except Exception as e:
        logger.error(f"Error fetching videos: {e}")
        return jsonify({'error': 'Failed to fetch videos'}), 500


@app.route('/api/videos/<video_id>', methods=['GET'])
@login_required
def get_video_detail(video_id):
    """Get detailed information for a specific video."""
    try:
        with get_db_session() as session:
            video = session.query(Video).filter(Video.video_id == video_id).first()

            if not video:
                return jsonify({'error': 'Video not found'}), 404

            # Convert to dict BEFORE expunging to allow relationship access
            video_data = video.to_dict(include_detailed=True)

        # Return video data directly (not nested)
        return jsonify(video_data)

    except Exception as e:
        logger.error(f"Error fetching video detail: {e}")
        return jsonify({'error': 'Failed to fetch video'}), 500


@app.route('/api/videos/date-range', methods=['POST'])
@login_required
@limiter.limit("10 per minute")
def get_videos_by_date_range():
    """Get all completed videos within a specific date range."""
    try:
        data = request.get_json()
        start_date = data.get('start_date')
        end_date = data.get('end_date')

        if not start_date or not end_date:
            return jsonify({'error': 'Both start_date and end_date are required'}), 400

        # Validate date format (YYYY-MM-DD)
        from datetime import datetime
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d').date()
            end = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400

        if start > end:
            return jsonify({'error': 'Start date must be before or equal to end date'}), 400

        with get_db_session() as session:
            # Query videos within date range with completed processing status
            videos = session.query(Video).filter(
                Video.published_at >= start,
                Video.published_at <= end,
                Video.processing_status == ProcessingStatus.COMPLETED
            ).order_by(desc(Video.published_at)).all()

            # Convert to dict before session closes
            videos_data = []
            for video in videos:
                video_dict = video.to_dict(include_detailed=False)
                # Add channel name if available
                if video.channel:
                    video_dict['channel_name'] = video.channel.channel_name
                videos_data.append(video_dict)

        logger.info(f"Fetched {len(videos_data)} videos from {start_date} to {end_date}")

        return jsonify({
            'videos': videos_data,
            'count': len(videos_data),
            'start_date': start_date,
            'end_date': end_date
        })

    except Exception as e:
        logger.error(f"Error fetching videos by date range: {e}")
        return jsonify({'error': 'Failed to fetch videos'}), 500


@app.route('/api/save_video', methods=['POST'])
@login_required
@limiter.limit("10 per minute")
def save_video_route():
    """Save a processed video to the database."""
    try:
        data = request.get_json()

        # Validate required fields
        required_fields = ['video_id', 'title', 'video_url']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Missing required field: {field}'}), 400

        video_id = data.get('video_id')
        title = data.get('title')
        video_url = data.get('video_url')
        caption_text = data.get('caption_text', '')
        short_summary = data.get('short_summary', '')
        detailed_summary = data.get('detailed_summary', '')

        with get_db_session() as session:
            # Check if video already exists
            existing_video = session.query(Video).filter(Video.video_id == video_id).first()
            if existing_video:
                return jsonify({
                    'error': 'Video already exists in database',
                    'video_id': video_id
                }), 409

            # Extract channel URL from video URL
            # For YouTube videos, the channel URL format is: https://www.youtube.com/channel/{channel_id}
            # We'll use the YouTube API to get channel info
            from googleapiclient.discovery import build
            youtube_api_key = os.environ.get('YOUTUBE_API_KEY')
            if not youtube_api_key:
                return jsonify({'error': 'YouTube API key not configured'}), 500

            try:
                youtube = build('youtube', 'v3', developerKey=youtube_api_key)

                # Get video details to extract channel info
                video_response = youtube.videos().list(
                    part='snippet',
                    id=video_id
                ).execute()

                if not video_response.get('items'):
                    return jsonify({'error': 'Video not found on YouTube'}), 404

                video_snippet = video_response['items'][0]['snippet']
                channel_id = video_snippet['channelId']
                channel_title = video_snippet['channelTitle']
                thumbnail_url = video_snippet.get('thumbnails', {}).get('high', {}).get('url', '')
                published_at_str = video_snippet.get('publishedAt')

                # Parse published_at
                from datetime import datetime
                published_at = None
                if published_at_str:
                    try:
                        published_at = datetime.fromisoformat(published_at_str.replace('Z', '+00:00'))
                    except:
                        pass

            except Exception as e:
                logger.error(f"Error fetching video metadata from YouTube API: {e}")
                return jsonify({'error': 'Failed to fetch video metadata from YouTube'}), 500

            # Check if channel exists in database
            channel = session.query(Channel).filter(Channel.channel_id == channel_id).first()

            if not channel:
                # Create new channel
                channel_url = f"https://www.youtube.com/channel/{channel_id}"

                try:
                    # Get channel thumbnail
                    channel_response = youtube.channels().list(
                        part='snippet',
                        id=channel_id
                    ).execute()

                    channel_thumbnail = ''
                    if channel_response.get('items'):
                        channel_thumbnail = channel_response['items'][0].get('snippet', {}).get('thumbnails', {}).get('high', {}).get('url', '')

                    channel = Channel(
                        channel_id=channel_id,
                        channel_name=channel_title,
                        channel_url=channel_url,
                        thumbnail_url=channel_thumbnail
                    )
                    session.add(channel)
                    session.flush()  # Get the channel.id
                    logger.info(f"Created new channel: {channel_title} ({channel_id})")

                except Exception as e:
                    logger.error(f"Error creating channel: {e}")
                    return jsonify({'error': 'Failed to create channel'}), 500

            # Create new video
            new_video = Video(
                channel_id=channel.id,
                video_id=video_id,
                title=title,
                thumbnail_url=thumbnail_url,
                published_at=published_at,
                caption_text=caption_text,
                short_summary=short_summary,
                detailed_summary=detailed_summary,
                processing_status=ProcessingStatus.COMPLETED if (caption_text and short_summary) else ProcessingStatus.PENDING
            )

            session.add(new_video)
            session.commit()

            logger.info(f"Saved video to database: {title} ({video_id})")

            return jsonify({
                'success': True,
                'video_id': video_id,
                'message': 'Video saved successfully'
            }), 201

    except Exception as e:
        logger.error(f"Error saving video: {e}")
        return jsonify({'error': 'Failed to save video'}), 500


# ============================================================================
# Video Processing API Endpoints
# ============================================================================

@app.route('/api/process/video/<video_id>', methods=['POST'])
@login_required
@limiter.limit("5 per minute")
def process_video_route(video_id):
    """Manually trigger processing for a specific video (by video_id string)."""
    try:
        # Find video by video_id (YouTube ID string, not database integer ID)
        with get_db_session() as session:
            video = session.query(Video).filter(Video.video_id == video_id).first()

            if not video:
                return jsonify({'error': 'Video not found'}), 404

            db_id = video.id
            session.expunge(video)

        success, error = process_single_video(db_id)

        if not success:
            return jsonify({'error': error}), 400

        return jsonify({
            'success': True,
            'message': 'Video processed successfully'
        })

    except Exception as e:
        logger.error(f"Error processing video: {e}")
        return jsonify({'error': 'Failed to process video'}), 500


@app.route('/api/process/pending', methods=['POST'])
@login_required
@limiter.limit("3 per minute")
def process_pending_route():
    """Process pending videos in batch."""
    try:
        max_videos = request.get_json().get('max_videos', 10) if request.is_json else 10

        # Validate max_videos (limit to MAX_VIDEOS_BATCH_PROCESS to prevent timeout)
        is_valid, max_videos, error = validate_max_videos(max_videos, max_allowed=MAX_VIDEOS_BATCH_PROCESS)
        if not is_valid:
            return jsonify({'error': error}), 400

        stats = process_pending_videos(max_videos)

        return jsonify({
            'success': True,
            'stats': stats
        })

    except Exception as e:
        logger.error(f"Error processing pending videos: {e}")
        return jsonify({'error': 'Failed to process videos'}), 500


@app.route('/api/stats', methods=['GET'])
@login_required
def get_stats():
    """Get processing and channel statistics."""
    try:
        processing_stats = get_processing_stats()
        channel_count = get_channel_count()
        pending_count = get_pending_videos_count()

        return jsonify({
            'channels': {
                'total': channel_count
            },
            'videos': processing_stats,
            'pending_processing': pending_count
        })

    except Exception as e:
        logger.error(f"Error fetching stats: {e}")
        return jsonify({'error': 'Failed to fetch statistics'}), 500


if __name__ == '__main__':
    # Use environment variable to control debug mode
    debug_mode = os.environ.get('FLASK_ENV') != 'production'
    host = os.environ.get('FLASK_HOST', '0.0.0.0')  # Listen on all interfaces
    port = int(os.environ.get('FLASK_PORT', 5000))

    if debug_mode:
        logger.warning("Running in DEBUG mode. Do not use this in production!")

    # Disable Flask reloader to avoid bytecode cache issues
    app.run(debug=debug_mode, host=host, port=port, use_reloader=False)
