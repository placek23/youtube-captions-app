import os
from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv
from caption_extractor import get_captions
from urllib.parse import urlparse, parse_qs
from gemini_summarizer import summarize_text

# Load environment variables from .env file
load_dotenv(override=True)

app = Flask(__name__)

@app.route('/')
def index():
    """Renders the main page."""
    return render_template('index.html')

@app.route('/get_captions', methods=['POST'])
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

# For Vercel deployment
app.debug = False

if __name__ == '__main__':
    app.run(debug=True)
