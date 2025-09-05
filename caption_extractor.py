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
    print(f"--- DEBUG: caption_extractor.py received video_id: '{video_id}' (type: {type(video_id)}) ---")
    
    # Validate video_id format
    if not video_id or not isinstance(video_id, str) or len(video_id) != 11:
        return "Invalid YouTube video ID format."
    
    try:
        # Use the new API - direct fetch approach
        api = YouTubeTranscriptApi()
        print(f"--- DEBUG: Attempting to fetch transcript for video_id: {video_id} ---")
        
        transcript = api.fetch(video_id, preferred_languages)
        print(f"--- DEBUG: Successfully fetched transcript ---")
        print(f"--- DEBUG: Language: {transcript.language} ({transcript.language_code}) ---")
        print(f"--- DEBUG: Number of snippets: {len(transcript.snippets)} ---")
        
        # Process the transcript snippets
        processed_texts = [snippet.text.replace('\n', ' ') for snippet in transcript.snippets]
        result = ' '.join(processed_texts)
        print(f"--- DEBUG: Processed transcript, total length: {len(result)} characters ---")
        
        return result
        
    except TranscriptsDisabled:
        print(f"--- DEBUG: Transcripts are disabled for video {video_id} ---")
        return "Transcripts are disabled for this video."
    except NoTranscriptFound:
        print(f"--- DEBUG: No transcript found in preferred languages: {preferred_languages} ---")
        
        # Try to get any available transcript as fallback
        try:
            print(f"--- DEBUG: Trying fallback with any available language ---")
            transcript = api.fetch(video_id)  # Default to English
            print(f"--- DEBUG: Fallback successful - Language: {transcript.language} ({transcript.language_code}) ---")
            
            processed_texts = [snippet.text.replace('\n', ' ') for snippet in transcript.snippets]
            result = ' '.join(processed_texts)
            return result
            
        except Exception as fallback_error:
            print(f"--- DEBUG: Fallback failed: {type(fallback_error).__name__}: {str(fallback_error)} ---")
            return f"No transcripts found in the preferred languages: {', '.join(preferred_languages)}."
            
    except Exception as e:
        print(f"--- DEBUG: Exception when fetching transcript: {type(e).__name__}: {str(e)} ---")
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
