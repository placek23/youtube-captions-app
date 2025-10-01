# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview
This is a full-stack Flask web application that provides YouTube channel subscription management with automated video processing, caption extraction, and AI-powered summarization. The app includes a PostgreSQL database for data persistence, complete authentication system, and is optimized for serverless deployment on Vercel.

### Key Features
- **Channel Subscriptions**: Subscribe to YouTube channels and automatically fetch latest videos
- **Video Management**: Browse, filter, and paginate through collected videos with thumbnails
- **AI Summarization**: Generate both short (50-100 words) and detailed summaries using Gemini 2.5 Flash
- **Caption Extraction**: Automatic caption extraction with Polish/English language detection
- **Single Video Processing**: Quick processing of individual YouTube videos with database save option
- **Security**: CSRF protection, rate limiting, input validation, and secure authentication

## Architecture

### Backend Components
- **Flask Backend** (`app.py`): Main server with 20+ routes including authentication, channel management, video listing, and processing endpoints
- **Authentication System** (`auth.py`): Flask-Login based user authentication with password hashing
- **Database Layer**:
  - `database.py`: SQLAlchemy engine with serverless-optimized connection pooling and retry logic
  - `models.py`: Channel and Video models with relationships, indexes, and constraints
- **YouTube Integration**:
  - `channel_manager.py`: Channel URL parsing, metadata fetching, and CRUD operations
  - `video_fetcher.py`: Batch video fetching with pagination and duplicate prevention
  - `caption_extractor.py`: Multi-language caption extraction (Polish/English)
- **AI Processing**:
  - `gemini_summarizer.py`: Dual summary generation (short + detailed) with language-aware prompts
  - `video_processor.py`: Orchestrates caption extraction and summarization pipeline
  - `prompts.py`: Language-specific prompt templates
- **Security & Validation**:
  - `validators.py`: Comprehensive input validation for URLs, IDs, and parameters
  - `startup_validator.py`: Environment variable validation on application startup
- **Utilities**:
  - `migrate_db.py`: Database initialization and migration script
  - `test_database.py`: Database connection and schema verification
  - `test_api_comprehensive.py`: API endpoint testing suite

### Frontend Components
- **Templates**:
  - `base.html`: Base template with navigation and security headers
  - `channels.html`: Channel subscription management interface
  - `videos.html`: Paginated video grid with filtering
  - `video_detail.html`: Individual video view with detailed summary
  - `process_single.html`: Single video processing interface
  - `login.html`: Authentication page
- **Static Assets**:
  - `static/js/`: JavaScript for each page (channels, videos, video_detail, script)
  - `static/css/`: Stylesheets for videos and other pages
  - Uses Marked.js CDN for markdown rendering

### Database Schema
- **PostgreSQL (Neon)** via Vercel Postgres
- **Channels Table**: id, channel_id (unique), channel_name, channel_url, thumbnail_url, created_at
- **Videos Table**: id, channel_id (FK), video_id (unique), title, thumbnail_url, published_at, caption_text, short_summary, detailed_summary, processing_status, created_at, updated_at
- **Indexes**: channel_id, video_id, published_at, processing_status
- **Relationships**: Channel → Videos (one-to-many with cascade delete)

## Common Development Commands

### First-Time Setup
```bash
# 1. Install dependencies
./venv/Scripts/python.exe -m pip install -r requirements.txt

# 2. Create .env file with required variables (see Environment Variables section below)
cp .env.example .env
# Edit .env and add your API keys

# 3. Initialize database (creates tables)
./venv/Scripts/python.exe migrate_db.py

# 4. Verify database connection
./venv/Scripts/python.exe test_database.py

# 5. Start the application
./venv/Scripts/python.exe app.py
```

### Running the Application
```bash
# Standard run (development mode)
./venv/Scripts/python.exe app.py

# Using the run_server.py wrapper (recommended for Windows/WSL2)
./venv/Scripts/python.exe run_server.py
```
The app runs on Flask's development server at `http://127.0.0.1:5000`.

### Database Operations
```bash
# Initialize/migrate database (creates all tables)
./venv/Scripts/python.exe migrate_db.py

# Test database connection and verify schema
./venv/Scripts/python.exe test_database.py

# Check database contents (use psql or database GUI)
# Connection string is in POSTGRES_URL environment variable
```

### Testing
```bash
# Test database connection
./venv/Scripts/python.exe test_database.py

# Test Gemini API
./venv/Scripts/python.exe test_gemini_api.py

# Test YouTube API
./venv/Scripts/python.exe test_youtube_api.py

# Comprehensive API endpoint tests (requires server running)
./venv/Scripts/python.exe test_api_comprehensive.py
```

### Development Dependencies
```bash
# Install/update all dependencies
./venv/Scripts/python.exe -m pip install -r requirements.txt

# Install individual packages
./venv/Scripts/python.exe -m pip install package-name
```

## Key Implementation Details

### Environment Variables
All environment variables are loaded from `.env` file (use `.env.example` as template).

**Required Variables:**
- `GEMINI_API_KEY`: Google Gemini API key for AI summarization
- `YOUTUBE_API_KEY`: YouTube Data API v3 key for channel/video fetching
- `SECRET_KEY`: Flask session secret (use strong random string for production)
- **Database URL** (one of the following, priority order):
  1. `POSTGRES_PRISMA_URL`: Recommended for Vercel (pgBouncer connection pooling)
  2. `DATABASE_URL`: Standard PostgreSQL connection string
  3. `POSTGRES_URL`: Alternative PostgreSQL connection string

**Optional Variables:**
- `POSTGRES_URL_NON_POOLING`: Direct database connection (non-pooled)
- `VERCEL`: Set to "1" on Vercel (auto-detected, triggers serverless optimizations)

**Getting API Keys:**
1. **Gemini API**: Visit https://makersuite.google.com/app/apikey
2. **YouTube API**:
   - Go to https://console.cloud.google.com/
   - Create/select project
   - Enable "YouTube Data API v3"
   - Create credentials → API key
3. **Vercel Postgres**: Automatically added when you connect Vercel Postgres to your project

### Environment Setup
- Virtual environment is located in `venv/` directory (Windows-style venv on WSL2)
- Uses `python-dotenv` for environment variable loading with override enabled
- `startup_validator.py` validates all required environment variables on startup
- `.env` file must be created (never commit it - use `.env.example` as template)

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

## API Endpoints

### Authentication Routes
- `GET /login` - Login page (public)
- `POST /login` - Authenticate user
- `GET /logout` - Logout current user

### Page Routes (Protected)
- `GET /` - Redirect to `/videos` (main landing page)
- `GET /videos` - Video grid page with pagination and filtering
- `GET /channels` - Channel management page
- `GET /process` - Single video processing page
- `GET /video/<int:video_id>` - Individual video detail page

### Channel API (Protected, JSON)
- `GET /api/channels` - List all subscribed channels
- `POST /api/channels` - Add new channel subscription
  - Body: `{"channel_url": "https://youtube.com/..."}`
  - Validates URL, fetches metadata, stores in database
- `DELETE /api/channels/<int:channel_id>` - Remove channel (cascades to videos)

### Video API (Protected, JSON)
- `GET /api/videos` - Paginated video list
  - Query params: `page` (default: 1), `per_page` (default: 20, max: 50), `channel_id` (filter), `order_by` (default: published_at DESC)
  - Returns: `{videos: [], page, per_page, total_count, total_pages}`
- `GET /api/videos/<int:video_id>` - Single video details with detailed summary

### Processing API (Protected, JSON)
- `POST /api/sync/channel/<int:channel_id>` - Fetch new videos from YouTube for channel
  - Fetches up to 10 latest videos
  - Skips duplicates
  - Returns count of new videos added
- `POST /api/process/video/<int:video_id>` - Process single video (extract captions + generate summaries)
  - Status: pending → processing → completed/failed
  - Updates video record with captions and summaries
- `POST /api/process/pending` - Batch process pending videos
  - Query param: `limit` (default: 5, max: 10)
  - Processes videos with status="pending"
  - Returns processing results

### Single Video Processing (Protected, JSON)
- `POST /get_captions` - Extract captions from YouTube URL
  - Body: `{"video_url": "https://youtube.com/..."}`
  - Returns: `{captions: "...", video_id: "...", title: "...", language: "pl/en"}`
- `POST /summarize` - Generate summaries from captions
  - Body: `{captions: "...", language: "pl/en"}`
  - Returns: `{short_summary: "...", detailed_summary: "...", language: "..."}`
- `POST /api/save_video` - Save processed video to database
  - Body: `{video_id, title, captions, short_summary, detailed_summary, language}`
  - Creates/links channel if not exists
  - Returns: `{video_id: <db_id>, message: "..."}`

### Security Features
- **Authentication**: All routes except `/login` require `@login_required`
- **CSRF Protection**: Flask-WTF CSRF tokens on all POST/DELETE requests
- **Rate Limiting**: Flask-Limiter on all endpoints (configurable per route)
- **Input Validation**: `validators.py` sanitizes and validates all inputs
- **SQL Injection Prevention**: SQLAlchemy parameterized queries
- **XSS Prevention**: Input sanitization and Content-Security-Policy headers