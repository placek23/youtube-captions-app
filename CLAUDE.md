# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview
This is a Flask web application that extracts YouTube video captions and generates AI-powered summaries using Google's Gemini API. The app supports both Polish and English captions with automatic language detection and includes a complete authentication system for secure access.

## Architecture
- **Flask Backend** (`app.py`): Main server with authentication, home page, caption extraction, and summarization endpoints
- **Authentication System** (`auth.py`): Flask-Login based user authentication with password hashing
- **Caption Extraction** (`caption_extractor.py`): Uses youtube-transcript-api v1.2.2 to fetch captions with fallback language support (Polish → English)
- **AI Summarization** (`gemini_summarizer.py`): Integrates with Gemini 2.5 Flash model using the new Google Gen AI SDK for detailed content analysis
- **Prompt Engineering** (`prompts.py`): Structured templates for consistent AI output formatting
- **Frontend**: Vanilla JavaScript with Marked.js for markdown rendering
- **Environment Configuration**: Requires `.env` file with `GEMINI_API_KEY`

## Common Development Commands

### Running the Application
```bash
# On WSL2/Linux systems, activate virtual environment first
./venv/Scripts/python.exe app.py
# Or if you can activate the venv:
# . venv/Scripts/activate  (Windows venv on WSL2)
# python app.py
```
The app runs in debug mode by default on Flask's development server at `http://127.0.0.1:5000`.

### Installing Dependencies
```bash
# Install dependencies using virtual environment Python directly
./venv/Scripts/python.exe -m pip install -r requirements.txt
# Or if venv is activated:
# pip install -r requirements.txt
```

**Note**: The project now uses `google-genai` (new SDK) instead of the deprecated `google-generativeai` library.

### Testing Gemini API Connection
```bash
python test_gemini_api.py
```

### Running Individual Components
```bash
# Test caption extraction standalone
python caption_extractor.py

# Direct summarization test (requires manual setup)
python gemini_summarizer.py
```

## Key Implementation Details

### Environment Setup
- Virtual environment is located in `venv/` directory (Windows-style venv on WSL2)
- Requires `GEMINI_API_KEY` environment variable in `.env` file
- Optional `SECRET_KEY` environment variable for Flask sessions (has fallback)
- Uses `python-dotenv` for environment variable loading with override enabled

### Authentication System
- **User Management**: In-memory user store with single admin user
- **Credentials**: Username: `admin_yt2024`, Password: `SecureYT!Pass#2024$Admin`
- **Security**: Werkzeug password hashing, Flask-Login session management
- **Access Control**: All main routes protected with `@login_required` decorator
- **Session Flow**: Login required → Main page → Logout available

### Caption Processing
- Uses updated youtube-transcript-api v1.2.2 with new API methods (`YouTubeTranscriptApi().fetch()`)
- Supports multiple YouTube URL formats (youtube.com/watch, youtu.be)
- Language preference order: Polish (`pl`) → English (`en`)
- Enhanced error handling for XML parsing issues and video availability
- Processes transcript text by replacing internal newlines with spaces
- Improved debugging output for troubleshooting caption extraction issues

### AI Summarization
- **Library**: Uses new `google-genai` SDK (replacing deprecated `google-generativeai`)
- **Model**: Gemini 2.5 Flash (`gemini-2.5-flash`) for advanced content analysis
- **Configuration**: 20,000 max output tokens for comprehensive summaries
- **API Pattern**: Uses `client.models.generate_content()` with proper response extraction
- **Response Handling**: Enhanced debugging and multiple extraction methods for robustness
- **Error Handling**: Comprehensive error handling for API configuration, token limits, and response issues
- **Structured Prompts**: Uses templates in `prompts.py` for consistent output formatting

### Frontend Architecture
- Single-page application with progressive disclosure (summary button appears after caption extraction)
- Markdown rendering using Marked.js CDN
- Copy-to-clipboard functionality for captions
- Loading states and error handling for async operations

## Development Notes
- **Debugging**: Extensive debug logging enabled throughout (search for "DEBUG" comments)
- **Server**: Uses Flask's built-in development server (not suitable for production)
- **Database**: No database required - stateless processing with in-memory user store
- **Static Files**: Served from `static/` directory (CSS, JS)
- **Templates**: HTML templates in `templates/` directory (`index.html`, `login.html`)
- **Deployment**: Vercel deployment configured with `@vercel/python` builder
- **Environment**: Mixed Windows/WSL2 environment requires direct Python executable calls
- **Library Updates**: Migrated from deprecated libraries to current versions:
  - `google-generativeai` → `google-genai`
  - `youtube-transcript-api` v0.6.1 → v1.2.2

## Route Protection
All main application routes require authentication:
- `/` - Main application interface (redirects to login if not authenticated)
- `/get_captions` - Caption extraction API endpoint
- `/summarize` - AI summarization API endpoint
- `/logout` - User logout
- `/login` - Authentication endpoint (accessible without login)