import os
from google import genai
from google.genai import types
from prompts import GEMINI_PROMPT, GEMINI_DETAILED_PROMPT, GEMINI_SHORT_PROMPT

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

        # Try different ways to extract the response
        summary_text = None

        # Method 1: Direct .text attribute
        if hasattr(response, 'text') and response.text:
            summary_text = response.text

        # Method 2: Check candidates
        elif hasattr(response, 'candidates') and response.candidates:
            candidate = response.candidates[0]

            if hasattr(candidate, 'content') and candidate.content:
                content = candidate.content

                if hasattr(content, 'parts') and content.parts:
                    for part in content.parts:
                        if hasattr(part, 'text') and part.text:
                            summary_text = part.text
                            break

        # Method 3: Check for error conditions
        if hasattr(response, 'prompt_feedback') and response.prompt_feedback:
            feedback = response.prompt_feedback
            if hasattr(feedback, 'block_reason') and feedback.block_reason:
                return f"Content was blocked by Gemini: {feedback.block_reason}"

        if summary_text:
            return summary_text
        else:
            return "No summary could be generated. The response was empty."

    except ValueError as ve:
        raise ve
    except Exception as e:
        if "Gemini API Error:" not in str(e) and "Summarization failed" not in str(e):
            raise Exception(f"Gemini API Error: {e}")
        else:
            raise


def generate_short_summary(text_to_summarize: str, language_code: str = 'en') -> str:
    """
    Generates a short summary (50-100 words) for video list display.
    Uses Gemini 2.5 Flash model with reduced token limit.

    Args:
        text_to_summarize: Caption text to summarize.
        language_code: Language code ('pl' for Polish, 'en' for English, etc.)

    Returns:
        Short summary text.
    """
    client = _get_genai_client()

    # Map language codes to full language names
    language_map = {
        'pl': 'Polish',
        'en': 'English',
        'es': 'Spanish',
        'fr': 'French',
        'de': 'German'
    }
    language_name = language_map.get(language_code, 'English')

    try:
        # Add language instruction to prompt
        language_instruction = f"\n\nIMPORTANT: Write the summary in {language_name}."
        full_prompt = GEMINI_SHORT_PROMPT.format(caption_text=text_to_summarize) + language_instruction

        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=full_prompt,
            config=types.GenerateContentConfig(
                temperature=0.7,
                max_output_tokens=500,  # Limited for short summary
                response_mime_type="text/plain"
            )
        )

        # Extract response using same methods as summarize_text
        summary_text = None

        if hasattr(response, 'text') and response.text:
            summary_text = response.text
        elif hasattr(response, 'candidates') and response.candidates:
            candidate = response.candidates[0]
            if hasattr(candidate, 'content') and candidate.content:
                content = candidate.content
                if hasattr(content, 'parts') and content.parts:
                    for part in content.parts:
                        if hasattr(part, 'text') and part.text:
                            summary_text = part.text
                            break

        if hasattr(response, 'prompt_feedback') and response.prompt_feedback:
            feedback = response.prompt_feedback
            if hasattr(feedback, 'block_reason') and feedback.block_reason:
                return f"Content was blocked by Gemini: {feedback.block_reason}"

        if summary_text:
            return summary_text.strip()
        else:
            return "No summary could be generated."

    except ValueError as ve:
        raise ve
    except Exception as e:
        if "Gemini API Error:" not in str(e):
            raise Exception(f"Gemini API Error: {e}")
        else:
            raise


def generate_detailed_summary(text_to_summarize: str, language_code: str = 'en') -> str:
    """
    Generates a detailed summary for video detail display.
    Uses Gemini 2.5 Flash model with high token limit.

    Args:
        text_to_summarize: Caption text to summarize.
        language_code: Language code ('pl' for Polish, 'en' for English, etc.)

    Returns:
        Detailed summary text with markdown formatting.
    """
    client = _get_genai_client()

    # Map language codes to full language names
    language_map = {
        'pl': 'Polish',
        'en': 'English',
        'es': 'Spanish',
        'fr': 'French',
        'de': 'German'
    }
    language_name = language_map.get(language_code, 'English')

    try:
        # Add language instruction to prompt
        language_instruction = f"\n\nIMPORTANT: Write the entire summary in {language_name}."
        full_prompt = GEMINI_DETAILED_PROMPT.format(caption_text=text_to_summarize) + language_instruction

        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=full_prompt,
            config=types.GenerateContentConfig(
                temperature=0.7,
                max_output_tokens=20000,  # Extended for comprehensive summaries
                response_mime_type="text/plain"
            )
        )

        # Extract response using same methods as summarize_text
        summary_text = None

        if hasattr(response, 'text') and response.text:
            summary_text = response.text
        elif hasattr(response, 'candidates') and response.candidates:
            candidate = response.candidates[0]
            if hasattr(candidate, 'content') and candidate.content:
                content = candidate.content
                if hasattr(content, 'parts') and content.parts:
                    for part in content.parts:
                        if hasattr(part, 'text') and part.text:
                            summary_text = part.text
                            break

        if hasattr(response, 'prompt_feedback') and response.prompt_feedback:
            feedback = response.prompt_feedback
            if hasattr(feedback, 'block_reason') and feedback.block_reason:
                return f"Content was blocked by Gemini: {feedback.block_reason}"

        if summary_text:
            return summary_text
        else:
            return "No summary could be generated."

    except ValueError as ve:
        raise ve
    except Exception as e:
        if "Gemini API Error:" not in str(e):
            raise Exception(f"Gemini API Error: {e}")
        else:
            raise