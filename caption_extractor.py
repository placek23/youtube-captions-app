import re
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
import xml.etree.ElementTree as ET

def extract_video_id(url):
    """Extracts YouTube video ID from various URL formats."""
    patterns = [
        r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
        r'youtu\.be\/([0-9A-Za-z_-]{11})',
        r'youtube\.com\/embed\/([0-9A-Za-z_-]{11})'
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def get_captions(video_id, preferred_languages=['pl', 'en']):
    """Fetches captions for a video ID, trying preferred languages."""
    # Validate video_id format
    if not video_id or not isinstance(video_id, str) or len(video_id) != 11:
        return "Invalid YouTube video ID format."

    try:
        # Use the new API - direct fetch approach
        api = YouTubeTranscriptApi()
        transcript = api.fetch(video_id, preferred_languages)

        # Process the transcript snippets
        processed_texts = [snippet.text.replace('\n', ' ') for snippet in transcript.snippets]
        result = ' '.join(processed_texts)

        return result

    except TranscriptsDisabled:
        return "Transcripts are disabled for this video."
    except NoTranscriptFound:
        # Try to get any available transcript as fallback
        try:
            transcript = api.fetch(video_id)  # Default to English
            processed_texts = [snippet.text.replace('\n', ' ') for snippet in transcript.snippets]
            result = ' '.join(processed_texts)
            return result

        except Exception:
            return f"No transcripts found in the preferred languages: {', '.join(preferred_languages)}."

    except Exception as e:
        error_msg = str(e).lower()
        if "no element found" in error_msg or "xml" in error_msg or "parseerror" in error_msg:
            return "Video not found or captions are not available. Please check if the video exists and has captions enabled."
        return f"Could not retrieve transcript: {e}"

if __name__ == "__main__":
    video_url = input("Enter the YouTube video URL: ")
    video_id = extract_video_id(video_url)

    if not video_id:
        print("Invalid YouTube URL or could not extract video ID.")
    else:
        print(f"\nExtracting captions for video ID: {video_id}\n")
        captions = get_captions(video_id)
        print("--- Captions ---")
        print(captions)
        print("------------------")

    # To deactivate the virtual environment when you're done (optional):
    # deactivate
