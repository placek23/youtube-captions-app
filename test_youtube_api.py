"""
Quick test script to verify YouTube API key is working.
"""

import os
from dotenv import load_dotenv
from channel_manager import get_youtube_client, fetch_channel_metadata

load_dotenv(override=True)

# Test a well-known YouTube channel
TEST_CHANNEL_ID = "UC_x5XG1OV2P6uZZ5FSM9Ttw"  # Google Developers channel

print("=" * 60)
print("YouTube API Test")
print("=" * 60)

# Check if API key is set
api_key = os.getenv('YOUTUBE_API_KEY')
if not api_key:
    print("[FAIL] YOUTUBE_API_KEY not found in .env file")
    exit(1)

print(f"[OK] API Key found: {api_key[:10]}...")

# Test API connection
try:
    print("\n1. Testing YouTube API client connection...")
    client = get_youtube_client()
    print("[OK] YouTube API client created successfully")

    print("\n2. Testing channel metadata fetch...")
    metadata = fetch_channel_metadata(TEST_CHANNEL_ID)

    if metadata:
        print("[OK] Channel metadata fetched successfully!")
        print(f"\nChannel Details:")
        print(f"  Name: {metadata['channel_name']}")
        print(f"  Subscriber Count: {metadata.get('subscriber_count', 'N/A')}")
        print(f"  Video Count: {metadata.get('video_count', 'N/A')}")
        print(f"  Channel ID: {metadata['channel_id']}")
        print("\n[SUCCESS] YouTube API is working correctly!")
    else:
        print("[FAIL] Failed to fetch channel metadata")
        exit(1)

except Exception as e:
    print(f"[ERROR] {e}")
    exit(1)

print("=" * 60)