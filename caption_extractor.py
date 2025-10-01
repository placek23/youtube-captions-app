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
    """
    Fetches captions for a video ID, trying preferred languages.

    Returns:
        tuple: (captions_text, language_code) or (error_message, None) on failure
    """
    # Validate video_id format
    if not video_id or not isinstance(video_id, str) or len(video_id) != 11:
        return "Invalid YouTube video ID format.", None

    try:
        # Use the new API - direct fetch approach
        api = YouTubeTranscriptApi()
        transcript = api.fetch(video_id, preferred_languages)

        # Try to get language code from transcript object
        language_code = 'en'  # Default to English
        if hasattr(transcript, 'language_code'):
            language_code = transcript.language_code
        elif hasattr(transcript, 'lang'):
            language_code = transcript.lang
        # If we requested Polish first and got a response, assume it's Polish
        elif preferred_languages and preferred_languages[0] == 'pl':
            # Check if content looks like Polish (has Polish-specific characters)
            sample = ' '.join([s.text for s in transcript.snippets[:3]])
            if any(char in sample for char in 'ąćęłńóśźżĄĆĘŁŃÓŚŹŻ'):
                language_code = 'pl'

        # Process the transcript snippets
        processed_texts = [snippet.text.replace('\n', ' ') for snippet in transcript.snippets]
        result = ' '.join(processed_texts)

        return result, language_code

    except TranscriptsDisabled:
        return "Transcripts are disabled for this video.", None
    except NoTranscriptFound:
        # Try to get any available transcript as fallback
        try:
            transcript = api.fetch(video_id)  # Default to English
            language_code = 'en'
            if hasattr(transcript, 'language_code'):
                language_code = transcript.language_code
            elif hasattr(transcript, 'lang'):
                language_code = transcript.lang

            processed_texts = [snippet.text.replace('\n', ' ') for snippet in transcript.snippets]
            result = ' '.join(processed_texts)
            return result, language_code

        except Exception:
            return f"No transcripts found in the preferred languages: {', '.join(preferred_languages)}.", None

    except Exception as e:
        error_msg = str(e).lower()
        if "no element found" in error_msg or "xml" in error_msg or "parseerror" in error_msg:
            return "Video not found or captions are not available. Please check if the video exists and has captions enabled.", None
        return f"Could not retrieve transcript: {e}", None

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
