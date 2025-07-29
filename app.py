import os
from flask import Flask, request, jsonify, render_template, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from dotenv import load_dotenv
from caption_extractor import get_captions
from urllib.parse import urlparse, parse_qs
from gemini_summarizer import summarize_text
from auth import get_user, authenticate_user

# Load environment variables from .env file
load_dotenv(override=True)

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-change-this-in-production')

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    return get_user(user_id)


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page and authentication."""
    print(f"DEBUG: Login route accessed. Method: {request.method}")
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        print(f"DEBUG: Login attempt for username: {username}")
        
        user = authenticate_user(username, password)
        if user:
            login_user(user)
            print(f"DEBUG: Login successful for user: {username}")
            next_page = request.args.get('next')
            print(f"DEBUG: Next page: {next_page}")
            return redirect(next_page) if next_page else redirect(url_for('index'))
        else:
            print(f"DEBUG: Login failed for username: {username}")
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
    print(f"DEBUG: Accessing index route. User authenticated: {current_user.is_authenticated if current_user else 'No current_user'}")
    return render_template('index.html', current_user=current_user)

@app.route('/get_captions', methods=['POST'])
@login_required
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
            # The get_captions function itself might return a more specific error from the API
            # For now, we keep a generic message or rely on the one from the API if it propagates
            return jsonify({'error': 'Could not retrieve captions for this video. It might be unavailable or private.'}), 404
        return jsonify({'captions': captions})
    except Exception as e:
        app.logger.error(f"Error getting captions: {e}")
        return jsonify({'error': 'An internal error occurred while fetching captions.'}), 500

@app.route('/summarize', methods=['POST'])
@login_required
def summarize_route():
    print("--- DEBUG: Entered /summarize route ---") # NEW TOP-LEVEL DEBUG LINE
    """API endpoint to summarize the provided caption text."""
    data = request.get_json()
    caption_text = data.get('caption_text')
    if not caption_text:
        return jsonify({'error': 'Caption text is required.'}), 400

    try:
        summary = summarize_text(caption_text)
        return jsonify({'summary': summary})
    except Exception as e:
        print(f"--- DEBUG: EXCEPTION IN /summarize ROUTE ---")
        print(f"--- Exception Type: {type(e)} ---")
        print(f"--- Exception Details: {str(e)} ---")
        import traceback
        traceback.print_exc() # This will print the full traceback
        app.logger.error(f"Error summarizing text: {e}")
        # Return the actual error message to the frontend for easier debugging
        return jsonify({'error': f'An internal error occurred: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
