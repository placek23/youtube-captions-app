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
from models import Video, ProcessingStatus
from database import get_db_session
from sqlalchemy import desc

# Load environment variables from .env file
load_dotenv(override=True)

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
if not IS_SERVERLESS:
    csrf = CSRFProtect()
    csrf.init_app(app)

    # Make csrf_token available in all templates
    @app.context_processor
    def inject_csrf_token():
        from flask_wtf.csrf import generate_csrf
        return dict(csrf_token=generate_csrf)
else:
    # For serverless, provide a dummy csrf_token that always returns empty string
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
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        "script-src 'self' https://cdn.jsdelivr.net; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "img-src 'self' data:;"
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
    """Renders the main page."""
    return render_template('index.html', current_user=current_user)

@app.route('/get_captions', methods=['POST'])
@login_required
@limiter.limit("10 per minute")
def get_captions_route():
    """API endpoint to fetch captions for a given YouTube URL."""
    data = request.get_json()
    video_url = data.get('video_url')
    if not video_url:
        return jsonify({'error': 'Video URL is required.'}), 400

    try:
        # Extract video ID from URL
        parsed_url = urlparse(video_url)
        if 'youtube.com' in parsed_url.netloc or 'youtu.be' in parsed_url.netloc:
            if parsed_url.path == '/watch':
                video_id = parse_qs(parsed_url.query).get('v')
                if video_id:
                    video_id = video_id[0]
                else:
                    return jsonify({'error': 'Invalid YouTube URL: Missing video ID.'}), 400
            elif parsed_url.path.startswith('/'): # handles youtu.be/VIDEO_ID format
                video_id = parsed_url.path[1:]
            else:
                 return jsonify({'error': 'Invalid YouTube URL format.'}), 400
        else:
            return jsonify({'error': 'Not a valid YouTube URL.'}), 400

        if not video_id:
            return jsonify({'error': 'Could not extract video ID from URL.'}), 400

        captions = get_captions(video_id) # Pass video_id instead of full URL
        if not captions:
            return jsonify({'error': 'Could not retrieve captions for this video. It might be unavailable or private.'}), 404
        return jsonify({'captions': captions})
    except Exception as e:
        logger.error(f"Error getting captions: {e}")
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
    channel_url = data.get('url')

    if not channel_url:
        return jsonify({'error': 'Channel URL is required'}), 400

    try:
        channel, error = add_channel(channel_url)

        if error:
            return jsonify({'error': error}), 400

        return jsonify({
            'success': True,
            'channel': channel.to_dict(),
            'message': f'Successfully subscribed to {channel.channel_name}'
        }), 201

    except Exception as e:
        logger.error(f"Error adding channel: {e}")
        return jsonify({'error': 'Failed to add channel'}), 500


@app.route('/api/channels/<int:channel_id>', methods=['DELETE'])
@login_required
@limiter.limit("10 per minute")
def delete_channel_route(channel_id):
    """Delete a channel subscription."""
    try:
        success, error = delete_channel(channel_id)

        if not success:
            return jsonify({'error': error}), 404

        return jsonify({
            'success': True,
            'message': 'Channel deleted successfully'
        })

    except Exception as e:
        logger.error(f"Error deleting channel: {e}")
        return jsonify({'error': 'Failed to delete channel'}), 500


@app.route('/api/channels/<int:channel_id>/sync', methods=['POST'])
@login_required
@limiter.limit("5 per minute")
def sync_channel_route(channel_id):
    """Manually trigger video sync for a specific channel."""
    try:
        max_videos = request.get_json().get('max_videos', 50) if request.is_json else 50

        new_count, skipped_count, error = sync_channel_videos(channel_id, max_videos)

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


# ============================================================================
# Video Listing API Endpoints
# ============================================================================

@app.route('/api/videos', methods=['GET'])
@login_required
def get_videos():
    """Get paginated list of videos with optional channel filter."""
    try:
        # Get query parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        channel_id = request.args.get('channel_id', type=int)

        # Limit per_page to prevent abuse
        per_page = min(per_page, 50)
        page = max(page, 1)

        with get_db_session() as session:
            # Base query
            query = session.query(Video)

            # Filter by channel if specified
            if channel_id:
                query = query.filter(Video.channel_id == channel_id)

            # Order by published date (newest first)
            query = query.order_by(desc(Video.published_at))

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

            # Detach from session
            session.expunge(video)

        return jsonify({
            'video': video.to_dict(include_detailed=True)
        })

    except Exception as e:
        logger.error(f"Error fetching video detail: {e}")
        return jsonify({'error': 'Failed to fetch video'}), 500


# ============================================================================
# Video Processing API Endpoints
# ============================================================================

@app.route('/api/process/video/<int:video_id>', methods=['POST'])
@login_required
@limiter.limit("5 per minute")
def process_video_route(video_id):
    """Manually trigger processing for a specific video."""
    try:
        success, error = process_single_video(video_id)

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
        max_videos = min(max_videos, 20)  # Limit to prevent timeout

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
    host = os.environ.get('FLASK_HOST', '127.0.0.1')  # Default to localhost for security
    port = int(os.environ.get('FLASK_PORT', 5000))

    if debug_mode:
        logger.warning("Running in DEBUG mode. Do not use this in production!")

    app.run(debug=debug_mode, host=host, port=port)
