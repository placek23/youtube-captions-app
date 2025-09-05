import os
from google import genai
from google.genai import types
from prompts import GEMINI_PROMPT

# Flag to ensure genai client is configured only once
_genai_client = None

def _get_genai_client():
    """Gets or creates the Gemini API client."""
    global _genai_client
    if _genai_client is None:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set or is empty. Please check your .env file.")
        _genai_client = genai.Client(api_key=api_key)
    return _genai_client

def summarize_text(text_to_summarize: str) -> str:
    """
    Sends text to the Gemini 2.5 Flash model for summarization.
    Uses the new 'google-genai' library and 'gemini-2.5-flash' model.
    """
    client = _get_genai_client()

    try:
        full_prompt = GEMINI_PROMPT.format(caption_text=text_to_summarize)
        print(f"--- DEBUG: Sending prompt of length {len(full_prompt)} characters to Gemini 2.5 Flash ---")
        
        # Use the new Google Gen AI SDK with proper configuration
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=full_prompt,
            config=types.GenerateContentConfig(
                temperature=0.7,
                max_output_tokens=20000,  # Extended to 20K tokens for comprehensive summaries
                response_mime_type="text/plain"
            )
        )
        
        print(f"--- DEBUG: Received response from Gemini ---")
        print(f"--- DEBUG: Response type: {type(response)} ---")
        print(f"--- DEBUG: Response attributes: {[attr for attr in dir(response) if not attr.startswith('_')]} ---")
        
        # Try different ways to extract the response
        summary_text = None
        
        # Method 1: Direct .text attribute
        if hasattr(response, 'text') and response.text:
            summary_text = response.text
            print(f"--- DEBUG: Got text via response.text, length: {len(summary_text)} ---")
        
        # Method 2: Check candidates
        elif hasattr(response, 'candidates') and response.candidates:
            print(f"--- DEBUG: Found {len(response.candidates)} candidates ---")
            candidate = response.candidates[0]
            print(f"--- DEBUG: First candidate type: {type(candidate)} ---")
            print(f"--- DEBUG: Candidate attributes: {[attr for attr in dir(candidate) if not attr.startswith('_')]} ---")
            
            # Check finish reason
            if hasattr(candidate, 'finish_reason') and candidate.finish_reason:
                print(f"--- DEBUG: Finish reason: {candidate.finish_reason} ---")
                if str(candidate.finish_reason) == 'MAX_TOKENS':
                    print("--- DEBUG: Response was truncated due to MAX_TOKENS ---")
            
            if hasattr(candidate, 'content') and candidate.content:
                content = candidate.content
                print(f"--- DEBUG: Content type: {type(content)} ---")
                print(f"--- DEBUG: Content attributes: {[attr for attr in dir(content) if not attr.startswith('_')]} ---")
                
                if hasattr(content, 'parts') and content.parts:
                    print(f"--- DEBUG: Found {len(content.parts)} parts ---")
                    for i, part in enumerate(content.parts):
                        print(f"--- DEBUG: Part {i} type: {type(part)} ---")
                        print(f"--- DEBUG: Part {i} attributes: {[attr for attr in dir(part) if not attr.startswith('_')]} ---")
                        if hasattr(part, 'text') and part.text:
                            summary_text = part.text
                            print(f"--- DEBUG: Got text from part {i}, length: {len(summary_text)} ---")
                            break
                else:
                    print(f"--- DEBUG: No parts found in content ---")
        
        # Method 3: Check for error conditions
        if hasattr(response, 'prompt_feedback') and response.prompt_feedback:
            feedback = response.prompt_feedback
            print(f"--- DEBUG: Prompt feedback: {feedback} ---")
            if hasattr(feedback, 'block_reason') and feedback.block_reason:
                return f"Content was blocked by Gemini: {feedback.block_reason}"
        
        if summary_text:
            print(f"--- DEBUG: Successfully extracted summary, final length: {len(summary_text)} ---")
            return summary_text
        else:
            print(f"--- DEBUG: Could not extract text from response ---")
            print(f"--- DEBUG: Full response object: {response} ---")
            return "No summary could be generated. The response was empty."

    except ValueError as ve: 
        print(f"Configuration Error in Gemini Summarizer: {ve}")
        raise ve
    except Exception as e:
        if "Gemini API Error:" not in str(e) and "Summarization failed" not in str(e):
            print(f"An unexpected error occurred during summarization with Gemini: {e}")
            raise Exception(f"Gemini API Error: {e}")
        else:
            raise