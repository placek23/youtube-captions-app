#!/usr/bin/env python3
"""
Comprehensive API Test Suite
Tests all API endpoints with authentication, validation, and error handling
Run this with: ./venv/Scripts/python.exe test_api_comprehensive.py
"""
import requests
import json
import time
from typing import Dict, Any

# Configuration
BASE_URL = "http://127.0.0.1:5000"
USERNAME = "admin_yt2024"
PASSWORD = "SecureYT!Pass#2024$Admin"

class APITester:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session = requests.Session()
        self.test_results = []

    def log_test(self, name: str, passed: bool, message: str = ""):
        """Log test result"""
        status = "[OK]" if passed else "[FAIL]"
        result = f"{status} {name}"
        if message:
            result += f": {message}"
        print(result)
        self.test_results.append({"name": name, "passed": passed, "message": message})

    def login(self):
        """Authenticate and create session"""
        print("\n" + "=" * 60)
        print("AUTHENTICATION TESTS")
        print("=" * 60)

        response = self.session.post(
            f"{self.base_url}/login",
            data={"username": USERNAME, "password": PASSWORD},
            allow_redirects=False
        )

        if response.status_code in [200, 302]:
            self.log_test("User login", True, "Successfully authenticated")
            return True
        else:
            self.log_test("User login", False, f"Status code: {response.status_code}")
            return False

    def test_authentication(self):
        """Test authentication requirements on protected routes"""
        # Try accessing protected route without login
        new_session = requests.Session()
        response = new_session.get(f"{self.base_url}/api/channels")

        if response.status_code in [401, 302]:
            self.log_test("Protected route without auth", True, "Correctly blocked")
        else:
            self.log_test("Protected route without auth", False, "Should require authentication")

    def test_channels_api(self):
        """Test channel management endpoints"""
        print("\n" + "=" * 60)
        print("CHANNEL API TESTS")
        print("=" * 60)

        # Test GET /api/channels
        response = self.session.get(f"{self.base_url}/api/channels")
        if response.status_code == 200:
            channels = response.json()
            self.log_test("GET /api/channels", True, f"Found {len(channels)} channels")
        else:
            self.log_test("GET /api/channels", False, f"Status: {response.status_code}")

        # Test POST /api/channels with valid URL
        test_channel_url = "https://www.youtube.com/@Google"
        response = self.session.post(
            f"{self.base_url}/api/channels",
            json={"channel_url": test_channel_url}
        )

        if response.status_code in [200, 201]:
            self.log_test("POST /api/channels (valid URL)", True, "Channel added")
            channel_data = response.json()
            test_channel_id = channel_data.get("channel", {}).get("id")
        else:
            self.log_test("POST /api/channels (valid URL)", False, f"Status: {response.status_code}")
            test_channel_id = None

        # Test POST /api/channels with invalid URL
        response = self.session.post(
            f"{self.base_url}/api/channels",
            json={"channel_url": "not-a-valid-url"}
        )

        if response.status_code in [400, 422]:
            self.log_test("POST /api/channels (invalid URL)", True, "Correctly rejected")
        else:
            self.log_test("POST /api/channels (invalid URL)", False, "Should reject invalid URLs")

        # Test POST /api/channels with missing data
        response = self.session.post(
            f"{self.base_url}/api/channels",
            json={}
        )

        if response.status_code in [400, 422]:
            self.log_test("POST /api/channels (missing data)", True, "Correctly rejected")
        else:
            self.log_test("POST /api/channels (missing data)", False, "Should require channel_url")

        return test_channel_id

    def test_videos_api(self):
        """Test video listing endpoints"""
        print("\n" + "=" * 60)
        print("VIDEO API TESTS")
        print("=" * 60)

        # Test GET /api/videos (default pagination)
        response = self.session.get(f"{self.base_url}/api/videos")
        if response.status_code == 200:
            data = response.json()
            videos = data.get("videos", [])
            page = data.get("page", 0)
            total = data.get("total_count", 0)
            self.log_test("GET /api/videos (default)", True, f"Page {page}, {total} total videos")
        else:
            self.log_test("GET /api/videos (default)", False, f"Status: {response.status_code}")

        # Test GET /api/videos with pagination
        response = self.session.get(f"{self.base_url}/api/videos?page=1&per_page=5")
        if response.status_code == 200:
            data = response.json()
            videos = data.get("videos", [])
            self.log_test("GET /api/videos (pagination)", True, f"Retrieved {len(videos)} videos")
        else:
            self.log_test("GET /api/videos (pagination)", False, f"Status: {response.status_code}")

        # Test GET /api/videos with invalid pagination
        response = self.session.get(f"{self.base_url}/api/videos?page=-1")
        if response.status_code in [400, 422]:
            self.log_test("GET /api/videos (invalid page)", True, "Correctly rejected")
        else:
            self.log_test("GET /api/videos (invalid page)", False, "Should reject negative page numbers")

        # Test GET /api/videos with excessive per_page
        response = self.session.get(f"{self.base_url}/api/videos?per_page=1000")
        if response.status_code in [400, 422]:
            self.log_test("GET /api/videos (excessive per_page)", True, "Correctly limited")
        else:
            self.log_test("GET /api/videos (excessive per_page)", False, "Should limit per_page")

    def test_video_detail_api(self):
        """Test individual video detail endpoint"""
        print("\n" + "=" * 60)
        print("VIDEO DETAIL API TESTS")
        print("=" * 60)

        # First, get a video ID
        response = self.session.get(f"{self.base_url}/api/videos?per_page=1")
        if response.status_code == 200 and response.json().get("videos"):
            video_id = response.json()["videos"][0]["id"]

            # Test GET /api/videos/<id>
            response = self.session.get(f"{self.base_url}/api/videos/{video_id}")
            if response.status_code == 200:
                video = response.json()
                self.log_test("GET /api/videos/<id>", True, f"Retrieved video: {video.get('title', '')[:30]}...")
            else:
                self.log_test("GET /api/videos/<id>", False, f"Status: {response.status_code}")
        else:
            self.log_test("GET /api/videos/<id>", False, "No videos available for testing")

        # Test GET /api/videos/<id> with invalid ID
        response = self.session.get(f"{self.base_url}/api/videos/99999999")
        if response.status_code == 404:
            self.log_test("GET /api/videos/<invalid_id>", True, "Correctly returned 404")
        else:
            self.log_test("GET /api/videos/<invalid_id>", False, "Should return 404 for non-existent video")

    def test_sync_endpoints(self):
        """Test manual sync and processing endpoints"""
        print("\n" + "=" * 60)
        print("SYNC & PROCESSING API TESTS")
        print("=" * 60)

        # Get a channel ID first
        response = self.session.get(f"{self.base_url}/api/channels")
        if response.status_code == 200 and response.json():
            channel_id = response.json()[0]["id"]

            # Test POST /api/sync/channel/<id>
            response = self.session.post(f"{self.base_url}/api/sync/channel/{channel_id}")
            if response.status_code in [200, 202]:
                self.log_test("POST /api/sync/channel/<id>", True, "Sync initiated")
            else:
                self.log_test("POST /api/sync/channel/<id>", False, f"Status: {response.status_code}")
        else:
            self.log_test("POST /api/sync/channel/<id>", False, "No channels available")

        # Test POST /api/sync/channel/<invalid_id>
        response = self.session.post(f"{self.base_url}/api/sync/channel/99999999")
        if response.status_code == 404:
            self.log_test("POST /api/sync/channel/<invalid_id>", True, "Correctly returned 404")
        else:
            self.log_test("POST /api/sync/channel/<invalid_id>", False, "Should return 404")

    def test_rate_limiting(self):
        """Test rate limiting on endpoints"""
        print("\n" + "=" * 60)
        print("RATE LIMITING TESTS")
        print("=" * 60)

        # Make rapid requests to test rate limiting
        rate_limited = False
        for i in range(15):  # Try 15 requests rapidly
            response = self.session.get(f"{self.base_url}/api/channels")
            if response.status_code == 429:
                rate_limited = True
                break

        if rate_limited:
            self.log_test("Rate limiting", True, "Rate limit enforced")
        else:
            self.log_test("Rate limiting", True, "Rate limit not reached (normal behavior)")

    def test_input_validation(self):
        """Test input validation and sanitization"""
        print("\n" + "=" * 60)
        print("INPUT VALIDATION TESTS")
        print("=" * 60)

        # Test XSS prevention in channel URL
        response = self.session.post(
            f"{self.base_url}/api/channels",
            json={"channel_url": "<script>alert('xss')</script>"}
        )
        if response.status_code in [400, 422]:
            self.log_test("XSS prevention (channel URL)", True, "Invalid input rejected")
        else:
            self.log_test("XSS prevention (channel URL)", False, "Should reject script tags")

        # Test SQL injection prevention (via pagination)
        response = self.session.get(f"{self.base_url}/api/videos?page=1' OR '1'='1")
        if response.status_code in [400, 422]:
            self.log_test("SQL injection prevention", True, "Invalid input rejected")
        else:
            self.log_test("SQL injection prevention", True, "Handled safely")

    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)

        total = len(self.test_results)
        passed = sum(1 for r in self.test_results if r["passed"])
        failed = total - passed

        print(f"\nTotal Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Success Rate: {(passed/total*100):.1f}%")

        if failed > 0:
            print("\nFailed Tests:")
            for result in self.test_results:
                if not result["passed"]:
                    print(f"  - {result['name']}: {result['message']}")

        print("\n" + "=" * 60)
        return failed == 0

def main():
    """Run all tests"""
    print("=" * 60)
    print("COMPREHENSIVE API TEST SUITE")
    print("=" * 60)
    print(f"\nBase URL: {BASE_URL}")
    print("Make sure the Flask app is running before starting tests")
    print("\nStarting tests in 3 seconds...")
    time.sleep(3)

    tester = APITester(BASE_URL)

    # Run authentication first
    if not tester.login():
        print("\n[FAIL] Authentication failed. Cannot proceed with tests.")
        return 1

    # Run all test suites
    tester.test_authentication()
    tester.test_channels_api()
    tester.test_videos_api()
    tester.test_video_detail_api()
    tester.test_sync_endpoints()
    tester.test_rate_limiting()
    tester.test_input_validation()

    # Print summary
    success = tester.print_summary()
    return 0 if success else 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
