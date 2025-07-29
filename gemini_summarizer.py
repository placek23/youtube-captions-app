import os
import google.generativeai as genai
from prompts import GEMINI_PROMPT

# Flag to ensure genai is configured only once
_genai_configured = False

def _ensure_genai_configured():
    """Configures the Gemini API client if not already configured."""
    global _genai_configured
    if not _genai_configured:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            # This error will be caught by the calling function in app.py
            raise ValueError("GEMINI_API_KEY environment variable not set or is empty. Please check your .env file.")
        genai.configure(api_key=api_key)
        _genai_configured = True

def summarize_text(text_to_summarize: str) -> str:
    """
    Sends text to the Gemini 1.5 Flash model for summarization.
    Uses the 'gemini-1.5-flash-latest' model.
    """
    _ensure_genai_configured() # Configure on first call

    try:
        model = genai.GenerativeModel(model_name="gemini-2.5-flash-preview-05-20")
        
        full_prompt = GEMINI_PROMPT.format(caption_text=text_to_summarize)
        
        generation_config = genai.types.GenerationConfig(
            response_mime_type="text/plain"
        )

        response_stream = model.generate_content(
            full_prompt,
            stream=True,
            generation_config=generation_config
        )
        
        summary_text = ""
        for chunk in response_stream:
            if hasattr(chunk, 'prompt_feedback') and chunk.prompt_feedback and chunk.prompt_feedback.block_reason:
                raise Exception(f"Summarization failed during stream due to: {chunk.prompt_feedback.block_reason_message}")
            if chunk.parts:
                 summary_text += "".join(part.text for part in chunk.parts if hasattr(part, 'text'))

        if not summary_text:
            # Consider more robust post-stream checks if available in SDK
            return "No summary could be generated. The response stream was empty or processing stopped."
            
        return summary_text

    except ValueError as ve: 
        print(f"Configuration Error in Gemini Summarizer: {ve}")
        raise ve
    except Exception as e:
        if "Gemini API Error:" not in str(e) and "Summarization failed" not in str(e):
            print(f"An unexpected error occurred during summarization with Gemini: {e}")
            raise Exception(f"Gemini API Error: {e}")
        else:
            raise
