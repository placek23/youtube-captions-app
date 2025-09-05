import os
from google import genai
from google.genai import types
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
        # Use the new Google Gen AI SDK
        client = genai.Client(api_key=api_key)
        
        print("Client configured. Attempting to generate content...")
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents="This is a test prompt.",
            config=types.GenerateContentConfig(
                temperature=0.7,
                max_output_tokens=100
            )
        )
        
        print("\n--- API Response ---")
        if response.text:
            print(response.text)
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