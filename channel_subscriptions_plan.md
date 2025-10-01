# YouTube Channel Subscription & Summary Management - Implementation Plan

**Feature Branch**: `feature/channel-subscriptions`
**Target Deployment**: Vercel with Neon Postgres
**Status**: Planning Complete - Ready for Implementation

---

## Phase 0: Git Branch & Environment Setup
- [x] Create new feature branch: `git checkout -b feature/channel-subscriptions`
- [x] Verify database credentials in `.env` file
  - [x] Confirm `POSTGRES_URL` or `DATABASE_URL` exists
  - [x] Verify additional Postgres variables (PRISMA_URL, etc.)
- [x] Create `.env.example` template file (no real credentials)
- [x] Verify `.env` is in `.gitignore`

---

## Phase 1: Database Setup & Schema Design
- [x] Install PostgreSQL dependencies
  - [x] Add `psycopg2-binary` to requirements.txt
  - [x] Add `SQLAlchemy` to requirements.txt
  - [x] Install dependencies: `./venv/Scripts/python.exe -m pip install -r requirements.txt`
- [x] Create `models.py` with SQLAlchemy models
  - [x] `Channel` model (id, channel_id, channel_name, channel_url, thumbnail_url, created_at)
  - [x] `Video` model (id, channel_id, video_id, title, thumbnail_url, published_at, caption_text, short_summary, detailed_summary, processing_status, created_at, updated_at)
  - [x] Define relationships (Channel → Videos: one-to-many)
  - [x] Add indexes (channel_id, video_id, published_at, processing_status)
  - [x] Add unique constraints (channel_id, video_id)
- [x] Create `database.py` for connection management
  - [x] Configure SQLAlchemy engine with Vercel Postgres URL
  - [x] Add connection pooling for serverless
  - [x] Create session factory
  - [x] Add connection test function
- [x] Create `migrate_db.py` database initialization script
  - [x] Create all tables
  - [x] Handle "already exists" gracefully
  - [x] Add verification function

---

## Phase 2: YouTube Channel Integration
- [x] Obtain YouTube Data API v3 credentials
  - [x] Create/enable API in Google Cloud Console
  - [x] Generate API key
  - [x] Add `YOUTUBE_API_KEY` to `.env`
  - [x] Add to `.env.example` as placeholder
- [x] Install YouTube API client
  - [x] Add `google-api-python-client` to requirements.txt
  - [x] Install: `./venv/Scripts/python.exe -m pip install google-api-python-client`
- [x] Create `channel_manager.py`
  - [x] Parse YouTube channel URLs (multiple formats)
  - [x] Extract channel ID from URL
  - [x] Fetch channel metadata via YouTube API
  - [x] Store channel in database (CRUD operations)
  - [x] Handle API quota limits
  - [x] Add error handling
- [x] Create `video_fetcher.py`
  - [x] Fetch latest videos from channel (configurable limit)
  - [x] Extract video metadata (title, thumbnail, published_at, video_id)
  - [x] Batch insert videos into database
  - [x] Skip duplicate videos (check video_id uniqueness)
  - [x] Handle pagination for large result sets
  - [x] Add error handling for API failures

---

## Phase 3: Background Processing System
- [x] Update `caption_extractor.py` for database integration
  - [x] Add function to process videos by status (in video_processor.py)
  - [x] Update processing_status: pending → processing → completed/failed
  - [x] Store extracted captions in database
  - [x] Handle extraction failures gracefully
  - [x] Add retry logic for failed extractions
- [x] Update `gemini_summarizer.py` for dual summaries
  - [x] Create `generate_short_summary()` function (50-100 words)
  - [x] Create `generate_detailed_summary()` function
  - [x] Add function to process both summaries in sequence (in video_processor.py)
  - [x] Update video record with both summaries
  - [x] Handle API timeouts and rate limits
  - [x] Add token usage tracking
- [x] Design processing strategy for Vercel
  - [x] Document 10-second timeout limitation
  - [x] Create video_processor.py with manual trigger functions
  - [x] Add batch processing with configurable limits
  - [x] Consider future webhook/queue implementation

---

## Phase 4: Backend API Endpoints
- [x] Add channel management endpoints to `app.py`
  - [x] `GET /api/channels` - List all subscribed channels
  - [x] `POST /api/channels` - Add new channel (validate + fetch metadata)
  - [x] `DELETE /api/channels/<id>` - Remove channel
  - [x] Protect all endpoints with `@login_required`
  - [x] Add input validation
  - [x] Add error handling and JSON responses
- [x] Add video listing endpoints to `app.py`
  - [x] `GET /api/videos` - Paginated video list
    - [x] Support `page` parameter (default: 1)
    - [x] Support `per_page` parameter (default: 20, max: 50)
    - [x] Support `channel_id` filter parameter
    - [x] Support `order_by` parameter (default: published_at DESC)
  - [x] Return pagination metadata (total_count, page, per_page)
  - [x] Protect with `@login_required`
- [x] Add video detail endpoint to `app.py`
  - [x] `GET /api/videos/<video_id>` - Full video details with detailed_summary
  - [x] Protect with `@login_required`
  - [x] Handle video not found (404)
- [x] Add manual processing endpoints to `app.py`
  - [x] `POST /api/sync/channel/<channel_id>` - Fetch new videos from channel
  - [x] `POST /api/process/video/<video_id>` - Process single video (captions + summaries)
  - [x] `POST /api/process/pending` - Batch process pending videos
  - [x] Protect with `@login_required`
  - [x] Add timeout safeguards
  - [x] Return processing status

---

## Phase 5: Frontend Development
- [x] Create base template (`templates/base.html`)
  - [x] Add navigation menu: Channels | Videos | Process Single Video | Logout
  - [x] Include common CSS and JS libraries
  - [x] Add responsive meta tags
- [x] Create channel management page
  - [x] Create `templates/channels.html`
    - [x] Add channel form (YouTube URL input)
    - [x] Display channel cards (grid layout)
    - [x] Add delete button per channel (with confirmation)
    - [x] Add manual sync button per channel
  - [x] Create `static/js/channels.js`
    - [x] Handle form submission (AJAX)
    - [x] Handle channel deletion
    - [x] Handle manual sync trigger
    - [x] Update UI dynamically
    - [x] Add loading states
    - [x] Display error messages
- [x] Create video list page (main landing page)
  - [x] Create `templates/videos.html`
    - [x] Grid/card layout (responsive)
    - [x] Display: thumbnail, title, channel, published date, short summary
    - [x] Add channel filter dropdown
    - [x] Add pagination controls (Previous, page numbers, Next)
    - [x] Make cards clickable → video detail page
  - [x] Create `static/js/videos.js`
    - [x] Fetch videos via API (paginated)
    - [x] Handle channel filtering
    - [x] Handle pagination navigation
    - [x] Update URL with query parameters (page, channel_id)
    - [x] Add loading states
    - [x] Handle empty states
  - [x] Create `static/css/videos.css`
    - [x] Style video cards
    - [x] Style pagination
    - [x] Responsive grid layout
- [x] Create video detail page
  - [x] Create `templates/video_detail.html`
    - [x] Display large thumbnail or embedded YouTube player
    - [x] Display full title, channel name, published date
    - [x] Display detailed summary (markdown rendered)
    - [x] Add copy-to-clipboard button
    - [x] Add "Back to Videos" link
    - [x] Optional: expandable original captions section
  - [x] Create `static/js/video_detail.js`
    - [x] Fetch video details via API
    - [x] Render markdown summary (using Marked.js)
    - [x] Handle copy-to-clipboard
    - [x] Handle video not found
- [x] Update navigation in all templates
  - [x] Update `templates/login.html` (if needed)
  - [x] Ensure consistent navigation across pages

---

## Phase 6: Update Existing Single-Video Feature
- [x] Rename `templates/index.html` to `templates/process_single.html`
- [x] Update route in `app.py` (keep `/` as redirect to `/videos`, add `/process` for single video)
- [x] Add "Save to Database" functionality
  - [x] Create `POST /api/save_video` endpoint
  - [x] Accept video_id, title, captions, summaries
  - [x] Create/link to channel if not exists
  - [x] Store in database
  - [x] Return saved video ID
- [x] Update `static/js/script.js` (or rename)
  - [x] Add "Save to Database" button (appears after processing)
  - [x] Handle save action (AJAX POST)
  - [x] Redirect to video detail page after save
  - [ ] Handle already-saved videos (check before processing) - Optional
- [x] Maintain backward compatibility
  - [x] Keep existing `/get_captions` endpoint
  - [x] Keep existing `/summarize` endpoint
  - [x] Add optional database integration
- [x] Additional improvements (beyond original plan)
  - [x] Fixed caption validation logic to avoid false failures for English videos
  - [x] Added language detection (Polish vs English)
  - [x] Implemented language-specific summaries (Polish summaries for Polish videos, English for English)

---

## Phase 7: Vercel-Specific Adaptations
- [ ] Optimize database connections for serverless
  - [ ] Use connection pooling with short-lived connections
  - [ ] Configure `POSTGRES_PRISMA_URL` if available (pgBouncer mode)
  - [ ] Handle cold starts gracefully
  - [ ] Add connection retry logic
- [ ] Update `vercel.json` configuration
  - [ ] Verify Flask app routing
  - [ ] Verify static file serving (`static/`)
  - [ ] Verify template directory configuration
  - [ ] Add any necessary rewrites
- [ ] Configure environment variables in Vercel
  - [ ] Add `GEMINI_API_KEY`
  - [ ] Add `YOUTUBE_API_KEY`
  - [ ] Add `SECRET_KEY`
  - [ ] Verify Postgres variables (auto-added by Vercel)
  - [ ] Set for both preview and production environments
- [ ] Test Vercel-specific considerations
  - [ ] Test 10-second timeout behavior
  - [ ] Test cold start performance
  - [ ] Test database connection pooling
  - [ ] Verify static asset serving

---

## Phase 8: Security & Quality Improvements
- [ ] Enhance authentication
  - [ ] Verify all new routes have `@login_required` decorator
  - [ ] Add CSRF protection (install Flask-WTF)
  - [ ] Add rate limiting (install Flask-Limiter)
  - [ ] Configure rate limits on expensive endpoints
- [ ] Add input validation
  - [ ] Validate YouTube URLs/channel IDs (regex patterns)
  - [ ] Validate pagination parameters (page, per_page)
  - [ ] Sanitize all user inputs (prevent XSS)
  - [ ] Use SQLAlchemy parameterized queries (prevent SQL injection)
  - [ ] Add maximum length limits for text fields
- [ ] Secure API keys
  - [ ] Verify `.env` in `.gitignore`
  - [ ] Ensure `.env.example` has no real credentials
  - [ ] Document API key setup in README
  - [ ] Add startup validation for required environment variables
- [ ] Implement database security
  - [ ] Use SSL connection for Vercel Postgres
  - [ ] Add unique constraints on `channel_id` and `video_id`
  - [ ] Add foreign key constraints with cascade rules
  - [ ] Add indexes for query performance
  - [ ] Test constraint violations
- [ ] Add comprehensive error handling
  - [ ] YouTube API quota exceeded → user-friendly message
  - [ ] Gemini API timeout → retry with exponential backoff
  - [ ] Database connection errors → graceful fallback
  - [ ] Invalid video IDs → 404 responses
  - [ ] Add logging (without sensitive data)
- [ ] Add security headers
  - [ ] Content Security Policy (CSP)
  - [ ] X-Frame-Options
  - [ ] X-Content-Type-Options
  - [ ] Add to Flask response headers

---

## Phase 9: Testing & Documentation
- [ ] Local testing
  - [ ] Test database connection to Vercel Postgres from local environment
  - [ ] Test channel add/delete operations
  - [ ] Test video fetching from YouTube API
  - [ ] Test caption extraction for stored videos
  - [ ] Test summary generation (short + detailed)
  - [ ] Test video pagination and filtering
  - [ ] Test authentication on all routes
  - [ ] Test rate limiting
  - [ ] Test error handling scenarios
- [ ] Update `requirements.txt`
  - [ ] Verify all new dependencies are listed
  - [ ] Test clean install in new virtual environment
- [ ] Update documentation
  - [ ] Update `CLAUDE.md` with new architecture
  - [ ] Document new models and database schema
  - [ ] Document new API endpoints
  - [ ] Document new environment variables
  - [ ] Add setup instructions for Vercel Postgres
  - [ ] Document YouTube API setup
  - [ ] Add troubleshooting section
- [ ] Create/update `README.md`
  - [ ] Add feature overview
  - [ ] Add setup instructions
  - [ ] Add deployment instructions
  - [ ] Add screenshots (optional)
- [ ] Create database migration documentation
  - [ ] Document how to run `migrate_db.py`
  - [ ] Document how to verify migrations
  - [ ] Document rollback strategy (if needed)

---

## Phase 10: Deployment to Vercel
- [ ] Prepare for deployment
  - [ ] Run final local tests
  - [ ] Verify all files are committed
  - [ ] Verify no sensitive data in commits
  - [ ] Update version number (if applicable)
- [ ] Commit and push feature branch
  - [ ] `git add .`
  - [ ] `git commit -m "Add YouTube channel subscription and summary management features"`
  - [ ] `git push origin feature/channel-subscriptions`
- [ ] Test Vercel preview deployment
  - [ ] Verify automatic preview deployment created
  - [ ] Check environment variables in Vercel dashboard
  - [ ] Run database migrations on preview environment
  - [ ] Test all features on preview URL
  - [ ] Check browser console for errors
  - [ ] Test mobile responsiveness
- [ ] Initialize production database
  - [ ] Run `migrate_db.py` against production Postgres
  - [ ] Verify tables created successfully
  - [ ] Check indexes and constraints
- [ ] Merge to main branch
  - [ ] Create pull request on GitHub/Git platform
  - [ ] Review changes
  - [ ] Merge to main
  - [ ] Verify production deployment
  - [ ] Test production URL
- [ ] Post-deployment verification
  - [ ] Test all features on production
  - [ ] Monitor logs for errors
  - [ ] Check database performance
  - [ ] Verify API quotas are sufficient

---

## Dependencies to Add
```
psycopg2-binary>=2.9.9
SQLAlchemy>=2.0.23
google-api-python-client>=2.108.0
Flask-WTF>=1.2.1
Flask-Limiter>=3.5.0
```

---

## Environment Variables Required
```
# Existing
GEMINI_API_KEY=your_gemini_api_key
SECRET_KEY=your_secret_key

# New - YouTube API
YOUTUBE_API_KEY=your_youtube_api_key

# New - Vercel Postgres (auto-added by Vercel)
POSTGRES_URL=your_postgres_connection_string
DATABASE_URL=your_database_url
POSTGRES_PRISMA_URL=your_prisma_url (optional)
POSTGRES_URL_NON_POOLING=your_non_pooling_url (optional)
```

---

## Progress Tracking
- **Phases Completed**: 6 / 10
- **Tasks Completed**: 120+ / 150+
- **Current Phase**: Phase 6 - Complete (with language detection enhancements)
- **Blockers**: None
- **Next Steps**: Phase 7 - Vercel-Specific Adaptations
- **Recent Achievements**:
  - ✅ Full channel subscription system with YouTube API integration
  - ✅ Video fetching and batch processing system
  - ✅ Complete frontend with channels, videos, and video detail pages
  - ✅ Single video processing with database save functionality
  - ✅ Language detection and language-specific summaries (Polish/English)

---

## Notes & Decisions
- **Database**: Using Vercel Postgres (Neon) - already provisioned and connected
- **Processing Strategy**: Manual triggers initially (due to Vercel 10-second timeout)
- **Frontend**: Vanilla JavaScript (consistent with existing implementation)
- **Authentication**: Existing Flask-Login system (no changes needed)
- **API Design**: RESTful JSON APIs for all new endpoints

---

**Last Updated**: 2025-09-30
**Plan Status**: Ready for Implementation