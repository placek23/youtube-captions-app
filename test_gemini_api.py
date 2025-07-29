import os
import google.generativeai as genai
from dotenv import load_dotenv

def run_test():
    print(f"GEMINI_API_KEY before load_dotenv: {os.environ.get('GEMINI_API_KEY')}")
    dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
    # Use override=True to ensure .env values take precedence
    loaded = load_dotenv(dotenv_path, override=True)
    print(f".env file found: {loaded}, loaded with override=True (Path: {dotenv_path})")
    api_key = os.environ.get("GEMINI_API_KEY")
    print(f"GEMINI_API_KEY after load_dotenv(override=True): {api_key}")

    if not api_key:
        print("ERROR: GEMINI_API_KEY not found in .env file or environment variables.")
        return

    print(f"Attempting to use API Key: {api_key[:10]}...{api_key[-4:]}") # Print partial key for verification

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name="gemini-2.5-flash-preview-05-20")
        
        print("Model configured. Attempting to generate content...")
        response = model.generate_content("This is a test prompt.")
        
        print("\n--- API Response ---")
        if response.parts:
            print("".join(part.text for part in response.parts))
        elif response.prompt_feedback and response.prompt_feedback.block_reason:
            print(f"Content generation failed due to: {response.prompt_feedback.block_reason_message}")
        else:
            print("No content generated or unknown issue.")
            print(f"Full response object: {response}")

    except Exception as e:
        print("\n--- ERROR DURING API TEST ---")
        print(f"An error occurred: {type(e).__name__} - {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_test()
