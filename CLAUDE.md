# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview
This is a Flask web application that extracts YouTube video captions and generates AI-powered summaries using Google's Gemini API. The app supports both Polish and English captions with automatic language detection.

## Architecture
- **Flask Backend** (`app.py`): Main server with three endpoints - home page, caption extraction, and summarization
- **Caption Extraction** (`caption_extractor.py`): Uses youtube-transcript-api to fetch captions with fallback language support (Polish → English)
- **AI Summarization** (`gemini_summarizer.py`): Integrates with Gemini 2.5 Flash model for detailed content analysis
- **Frontend**: Vanilla JavaScript with Marked.js for markdown rendering
- **Environment Configuration**: Requires `.env` file with `GEMINI_API_KEY`

## Common Development Commands

### Running the Application
```bash
python app.py
```
The app runs in debug mode by default on Flask's development server.

### Installing Dependencies
```bash
pip install -r requirements.txt
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
- Virtual environment is located in `venv/` directory
- Requires `GEMINI_API_KEY` environment variable in `.env` file
- Uses `python-dotenv` for environment variable loading with override enabled

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
- No database required - stateless processing only
- Static files served from `static/` directory (CSS, JS)
- HTML templates in `templates/` directory