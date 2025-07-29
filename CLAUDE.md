# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview
This is a Flask web application that extracts YouTube video captions and generates AI-powered summaries using Google's Gemini API. The app supports both Polish and English captions with automatic language detection and includes a complete authentication system for secure access.

## Architecture
- **Flask Backend** (`app.py`): Main server with authentication, home page, caption extraction, and summarization endpoints
- **Authentication System** (`auth.py`): Flask-Login based user authentication with password hashing
- **Caption Extraction** (`caption_extractor.py`): Uses youtube-transcript-api to fetch captions with fallback language support (Polish → English)
- **AI Summarization** (`gemini_summarizer.py`): Integrates with Gemini 2.5 Flash model for detailed content analysis
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
- Supports multiple YouTube URL formats (youtube.com/watch, youtu.be)
- Language preference order: Polish (`pl`) → English (`en`)
- Processes transcript text by replacing internal newlines with spaces
- Handles API errors gracefully with specific error messages

### AI Summarization
- Uses Gemini 2.5 Flash Preview model (`gemini-2.5-flash-preview-05-20`)
- Streaming response processing for better performance
- Structured prompt template in `prompts.py` for consistent output format
- Error handling for API configuration and response issues

### Frontend Architecture
- Single-page application with progressive disclosure (summary button appears after caption extraction)
- Markdown rendering using Marked.js CDN
- Copy-to-clipboard functionality for captions
- Loading states and error handling for async operations

## Development Notes
- Debug logging is enabled in several places (search for "DEBUG" comments)
- The app uses Flask's built-in development server (not suitable for production)
- No database required - stateless processing with in-memory user store
- Static files served from `static/` directory (CSS, JS)
- HTML templates in `templates/` directory (`index.html`, `login.html`)
- Vercel deployment configured with `@vercel/python` builder
- Mixed Windows/WSL2 environment requires direct Python executable calls

## Route Protection
All main application routes require authentication:
- `/` - Main application interface (redirects to login if not authenticated)
- `/get_captions` - Caption extraction API endpoint
- `/summarize` - AI summarization API endpoint
- `/logout` - User logout
- `/login` - Authentication endpoint (accessible without login)