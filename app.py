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

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'

# Initialize CSRF protection
csrf = CSRFProtect()
csrf.init_app(app)

# Make csrf_token available in all templates
@app.context_processor
def inject_csrf_token():
    from flask_wtf.csrf import generate_csrf
    return dict(csrf_token=generate_csrf)

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
            login_user(user)
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

if __name__ == '__main__':
    # Use environment variable to control debug mode
    debug_mode = os.environ.get('FLASK_ENV') != 'production'
    host = os.environ.get('FLASK_HOST', '127.0.0.1')  # Default to localhost for security
    port = int(os.environ.get('FLASK_PORT', 5000))

    if debug_mode:
        logger.warning("Running in DEBUG mode. Do not use this in production!")

    app.run(debug=debug_mode, host=host, port=port)
