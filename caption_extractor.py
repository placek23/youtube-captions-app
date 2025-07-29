import re
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound

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
    print(f"--- DEBUG: caption_extractor.py received video_id: '{video_id}' (type: {type(video_id)}) ---") # DEBUG LINE
    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
    except TranscriptsDisabled:
        return "Transcripts are disabled for this video."
    except Exception as e:
        return f"Could not retrieve transcript list: {e}"

    for lang_code in preferred_languages:
        try:
            transcript = transcript_list.find_transcript([lang_code])
            fetched_transcript = transcript.fetch()
            # Each item in fetched_transcript is a dict {'text': '...', 'start': ..., 'duration': ...}
            # Process each text item to replace internal newlines with spaces
            processed_texts = [item.text.replace('\n', ' ') for item in fetched_transcript]
            return ' '.join(processed_texts)
        except NoTranscriptFound:
            continue # Try next preferred language
        except Exception as e:
            return f"Error fetching {lang_code} transcript: {e}"
    
    return f"No transcripts found in the preferred languages: {', '.join(preferred_languages)}."

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
