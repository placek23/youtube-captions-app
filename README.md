# YouTube Channel Subscription & AI Summary Manager

A full-stack Flask web application that manages YouTube channel subscriptions, automatically fetches videos, extracts captions, and generates AI-powered summaries using Google's Gemini API. Built with PostgreSQL for data persistence and optimized for serverless deployment on Vercel.

## Features

### 📺 Channel Management
- Subscribe to YouTube channels with a simple URL
- Automatically fetch channel metadata (name, thumbnail)
- Manual sync to fetch latest videos from subscribed channels
- Delete channels (automatically removes associated videos)

### 🎬 Video Collection
- Automatic fetching of latest videos from subscribed channels
- Paginated video grid with thumbnail previews
- Filter videos by channel
- Sort by publication date
- Duplicate prevention

### 🤖 AI-Powered Summarization
- **Dual Summaries**: Both short (50-100 words) and detailed summaries
- **Language Detection**: Automatic Polish/English caption detection
- **Language-Aware**: Summaries generated in the video's language
- **Gemini 2.5 Flash**: Advanced AI model for accurate summaries

### 🔒 Security & Authentication
- Secure login system with password hashing
- CSRF protection on all forms
- Rate limiting to prevent abuse
- Input validation and sanitization
- SQL injection prevention
- XSS protection with Content-Security-Policy headers

### ⚡ Performance
- Serverless-optimized database connections
- Connection pooling with retry logic
- Efficient pagination
- Batch processing capabilities

## Tech Stack

- **Backend**: Flask 2.3.3 with Flask-Login, Flask-WTF, Flask-Limiter
- **Database**: PostgreSQL (Vercel Neon) with SQLAlchemy 2.0+
- **APIs**:
  - Google Gemini API (2.5 Flash model)
  - YouTube Data API v3
- **Frontend**: Vanilla JavaScript, HTML5, CSS3
- **Markdown Rendering**: Marked.js
- **Deployment**: Vercel with @vercel/python

## Quick Start

### Prerequisites
- Python 3.8+
- PostgreSQL database (Vercel Postgres recommended)
- Google Gemini API key
- YouTube Data API v3 key

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd "Youtube Captions ver 2"
   ```

2. **Create virtual environment** (if not exists)
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   ```

   Edit `.env` and add your credentials:
   ```env
   # Required API Keys
   GEMINI_API_KEY=your_gemini_api_key_here
   YOUTUBE_API_KEY=your_youtube_api_key_here
   SECRET_KEY=your_secret_key_here

   # Database (one of the following)
   POSTGRES_PRISMA_URL=your_postgres_connection_string
   # OR
   DATABASE_URL=your_postgres_connection_string
   # OR
   POSTGRES_URL=your_postgres_connection_string
   ```

5. **Initialize database**
   ```bash
   python migrate_db.py
   ```

6. **Verify setup**
   ```bash
   python test_database.py
   python test_gemini_api.py
   python test_youtube_api.py
   ```

7. **Start the application**
   ```bash
   python app.py
   ```

8. **Access the application**
   Open browser to `http://127.0.0.1:5000`

   **Login credentials**:
   - Username: `admin_yt2024`
   - Password: `SecureYT!Pass#2024$Admin`

## Getting API Keys

### Google Gemini API Key
1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Click "Create API Key"
3. Copy the key to your `.env` file

### YouTube Data API v3 Key
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select existing)
3. Enable "YouTube Data API v3" in APIs & Services
4. Go to Credentials → Create Credentials → API Key
5. Copy the key to your `.env` file

### Vercel Postgres (for deployment)
1. Create a Vercel account
2. Create a new Vercel Postgres database
3. Connect it to your project
4. Environment variables are auto-added

## Usage

### 1. Subscribe to Channels
1. Navigate to **Channels** page
2. Paste a YouTube channel URL (e.g., `https://youtube.com/@channelname`)
3. Click "Add Channel"
4. Channel metadata is fetched automatically

### 2. Fetch Videos
1. Click "Sync" button on any channel
2. Latest videos are fetched from YouTube
3. Videos appear in the Videos page

### 3. Process Videos
Videos can be processed in two ways:

**Automatic Processing (for subscribed channels):**
- Videos are initially saved with `status=pending`
- Use "Process Pending Videos" button to batch process

**Manual Processing (single video):**
1. Go to **Process Single Video** page
2. Paste any YouTube URL
3. Click "Extract Captions"
4. Click "Generate Summary"
5. Click "Save to Database" (optional)

### 4. View Summaries
- Browse videos in the **Videos** page
- Click any video to see detailed summary
- Copy summaries to clipboard
- View original captions (expandable)

## Project Structure

```
.
├── app.py                      # Main Flask application
├── auth.py                     # Authentication system
├── database.py                 # Database connection & config
├── models.py                   # SQLAlchemy models
├── channel_manager.py          # YouTube channel operations
├── video_fetcher.py            # Video fetching from YouTube
├── caption_extractor.py        # Caption extraction logic
├── gemini_summarizer.py        # AI summarization
├── video_processor.py          # Processing pipeline
├── validators.py               # Input validation
├── startup_validator.py        # Environment validation
├── prompts.py                  # AI prompt templates
├── migrate_db.py               # Database migrations
├── test_*.py                   # Test scripts
├── templates/                  # HTML templates
│   ├── base.html
│   ├── channels.html
│   ├── videos.html
│   ├── video_detail.html
│   ├── process_single.html
│   └── login.html
├── static/
│   ├── js/                     # JavaScript files
│   └── css/                    # Stylesheets
├── requirements.txt            # Python dependencies
├── vercel.json                 # Vercel configuration
├── .env.example                # Environment template
└── README.md                   # This file
```

## Database Schema

### Channels Table
| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| channel_id | String (100) | YouTube channel ID (unique) |
| channel_name | String (255) | Channel display name |
| channel_url | String (500) | Full YouTube URL |
| thumbnail_url | String (500) | Channel thumbnail |
| created_at | DateTime | Creation timestamp |

### Videos Table
| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| channel_id | Integer | Foreign key to channels |
| video_id | String (20) | YouTube video ID (unique) |
| title | String (500) | Video title |
| thumbnail_url | String (500) | Video thumbnail |
| published_at | DateTime | YouTube publish date |
| caption_text | Text | Extracted captions |
| short_summary | Text | 50-100 word summary |
| detailed_summary | Text | Comprehensive summary |
| processing_status | String (20) | pending/processing/completed/failed |
| created_at | DateTime | Creation timestamp |
| updated_at | DateTime | Last update timestamp |

**Indexes**: channel_id, video_id, published_at, processing_status
**Relationships**: Channel → Videos (one-to-many, cascade delete)

## API Endpoints

### Channel Management
- `GET /api/channels` - List all channels
- `POST /api/channels` - Add channel (body: `{channel_url}`)
- `DELETE /api/channels/<id>` - Remove channel

### Video Management
- `GET /api/videos` - List videos (params: `page`, `per_page`, `channel_id`)
- `GET /api/videos/<id>` - Get video details

### Processing
- `POST /api/sync/channel/<id>` - Fetch new videos
- `POST /api/process/video/<id>` - Process single video
- `POST /api/process/pending` - Batch process pending videos

### Single Video Processing
- `POST /get_captions` - Extract captions
- `POST /summarize` - Generate summaries
- `POST /api/save_video` - Save to database

See [CLAUDE.md](./CLAUDE.md) for complete API documentation.

## Development

### Running Tests
```bash
# Database connection test
python test_database.py

# API endpoint tests (requires running server)
python test_api_comprehensive.py

# Individual API tests
python test_gemini_api.py
python test_youtube_api.py
```

### Database Migrations
```bash
# Run migrations
python migrate_db.py

# Verify tables
python test_database.py
```

### Environment Variables
All variables are loaded from `.env` file:

**Required:**
- `GEMINI_API_KEY` - Google Gemini API key
- `YOUTUBE_API_KEY` - YouTube Data API v3 key
- `SECRET_KEY` - Flask session secret
- Database URL (one of):
  - `POSTGRES_PRISMA_URL` (recommended for Vercel)
  - `DATABASE_URL`
  - `POSTGRES_URL`

**Optional:**
- `VERCEL` - Set to "1" on Vercel (auto-detected)

## Deployment to Vercel

1. **Push to GitHub**
   ```bash
   git add .
   git commit -m "Ready for deployment"
   git push origin main
   ```

2. **Import to Vercel**
   - Go to [vercel.com](https://vercel.com)
   - Click "Import Project"
   - Select your repository

3. **Add Vercel Postgres**
   - In project settings → Storage
   - Create Postgres database
   - Database env vars are auto-added

4. **Add other environment variables**
   - Project Settings → Environment Variables
   - Add `GEMINI_API_KEY`
   - Add `YOUTUBE_API_KEY`
   - Add `SECRET_KEY`

5. **Run database migration**
   - After first deployment
   - Use Vercel CLI or run `migrate_db.py` locally with production database URL

6. **Access your app**
   - App is live at `your-project.vercel.app`

See [DEPLOYMENT.md](./DEPLOYMENT.md) for detailed deployment instructions.

## Troubleshooting

### Database Connection Issues
- Verify database URL in `.env`
- Check that database exists and is accessible
- Run `python test_database.py` to diagnose
- For Vercel: Use `POSTGRES_PRISMA_URL` for better connection pooling

### API Quota Exceeded
- **YouTube API**: Default quota is 10,000 units/day
  - Each channel fetch costs ~3 units
  - Each video list costs ~1 unit
  - Request quota increase in Google Cloud Console if needed
- **Gemini API**: Check quota limits in Google AI Studio

### Processing Failures
- Check caption availability (not all videos have captions)
- Verify language support (Polish/English only)
- Check Gemini API key validity
- Review logs in terminal/Vercel dashboard

### Rate Limiting
- Default limits: 10 requests/minute per endpoint
- Adjust in `app.py` if needed for your use case

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see LICENSE file for details.

## Acknowledgments

- [Flask](https://flask.palletsprojects.com/) - Web framework
- [Google Gemini](https://ai.google.dev/) - AI summarization
- [YouTube Data API](https://developers.google.com/youtube/v3) - Video metadata
- [SQLAlchemy](https://www.sqlalchemy.org/) - Database ORM
- [Vercel](https://vercel.com) - Hosting platform

## Support

For issues, questions, or suggestions:
- Open an issue on GitHub
- Check [CLAUDE.md](./CLAUDE.md) for technical documentation
- Review [DEPLOYMENT.md](./DEPLOYMENT.md) for deployment help

---

**Status**: ✅ Production Ready (Phase 9 Complete)
**Version**: 2.0.0
**Last Updated**: 2025-10-01
