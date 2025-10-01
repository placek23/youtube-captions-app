# Deployment Guide

## Vercel Deployment

### Prerequisites
- Vercel account
- GitHub repository connected to Vercel

### Environment Variables

Add these environment variables in your Vercel project settings (Settings → Environment Variables):

#### Application Configuration

| Variable | Required | Example Value | Description |
|----------|----------|---------------|-------------|
| `SECRET_KEY` | ✅ Yes | `7b42bca9...41393053` | Flask secret key for sessions (generate with `python -c "import secrets; print(secrets.token_hex(32))"`) |
| `ADMIN_USERNAME` | ✅ Yes | `admin_yt2024` | Admin username for login |
| `ADMIN_PASSWORD` | ✅ Yes | `SecureYT!Pass#2024$Admin` | Admin password (use a strong password!) |
| `GEMINI_API_KEY` | ✅ Yes | `AIzaSy...` | Google Gemini API key from https://makersuite.google.com/app/apikey |
| `YOUTUBE_API_KEY` | ✅ Yes | `AIzaSy...` | YouTube Data API v3 key from Google Cloud Console |
| `FLASK_ENV` | ⚠️ Recommended | `production` | Set to `production` for production deployments |

#### Database Configuration (Vercel Postgres)

These variables are **automatically set** when you connect a Vercel Postgres database:

| Variable | Auto-Set | Priority | Description |
|----------|----------|----------|-------------|
| `POSTGRES_PRISMA_URL` | ✅ Auto | **Highest** | pgBouncer connection pooling URL (recommended for serverless) |
| `DATABASE_URL` | ✅ Auto | Medium | Standard database connection URL |
| `POSTGRES_URL` | ✅ Auto | Lowest | Alternative connection URL |
| `POSTGRES_URL_NON_POOLING` | ✅ Auto | N/A | Direct connection URL (for migrations only) |

**Note**: The application automatically uses `POSTGRES_PRISMA_URL` if available (best for Vercel serverless), otherwise falls back to `DATABASE_URL` or `POSTGRES_URL`.

### Deployment Steps

1. **Connect Repository**
   - Go to https://vercel.com/new
   - Import your GitHub repository
   - Vercel will auto-detect Flask and configure build settings

2. **Connect Vercel Postgres Database**
   - In your Vercel project, go to Storage tab
   - Click "Create Database" → "Postgres"
   - Choose a database name and region (close to your main users)
   - Vercel will automatically set all `POSTGRES_*` environment variables

3. **Initialize Database**
   - After connecting the database, run migrations
   - Option A: Use Vercel CLI locally
     ```bash
     vercel env pull .env.local  # Download environment variables
     python migrate_db.py        # Run migrations
     ```
   - Option B: SSH into a serverless function (advanced)
   - The migration script creates all required tables and indexes

4. **Add Application Environment Variables**
   - Go to Project Settings → Environment Variables
   - Add the 6 required variables from the table above:
     - `SECRET_KEY`
     - `ADMIN_USERNAME`
     - `ADMIN_PASSWORD`
     - `GEMINI_API_KEY`
     - `YOUTUBE_API_KEY`
     - `FLASK_ENV` (set to `production`)
   - Apply to: Production, Preview, and Development

5. **Deploy**
   - Vercel will automatically deploy when you push to main branch
   - Or manually trigger deployment from Vercel dashboard
   - First deployment may take 2-3 minutes

6. **Test Deployment**
   - Visit your Vercel URL
   - Login with your credentials
   - Test the following features:
     - ✅ Single video caption extraction and summarization
     - ✅ Channel subscription (add a YouTube channel)
     - ✅ Video listing and filtering
     - ✅ Video detail view with detailed summaries
     - ✅ Manual video processing
     - ✅ Database persistence (refresh page, data should remain)

### Security Notes for Vercel

⚠️ **Important**: CSRF protection is automatically disabled on Vercel because serverless functions are stateless and cannot maintain sessions required for CSRF tokens.

**Security measures still active on Vercel:**
- ✅ Rate limiting (5 login attempts/minute, 10 caption requests/minute, 5 summarize requests/minute)
- ✅ Secure password hashing with Werkzeug
- ✅ Session-based authentication with Flask-Login
- ✅ Open redirect protection
- ✅ XSS protection with DOMPurify
- ✅ Security headers (CSP, HSTS, X-Frame-Options, etc.)
- ✅ Environment-based credential management

**Missing on Vercel:**
- ❌ CSRF protection (serverless limitation)

### Vercel Serverless Considerations

#### 10-Second Timeout Limitation
- Vercel serverless functions have a **10-second maximum execution time** on Hobby plan
- For long-running tasks (video processing, caption extraction), use manual triggers
- The app is designed with this limitation in mind:
  - Manual sync per channel
  - Manual processing per video or batch
  - Batch processing limits configurable in code

#### Cold Start Performance
- First request after inactivity may take 2-5 seconds (cold start)
- Database connections use retry logic to handle cold starts gracefully
- Connection pooling via `POSTGRES_PRISMA_URL` improves performance

#### Database Connection Optimization
- **NullPool** strategy: No persistent connections (closes after each request)
- **pgBouncer** mode: Automatic connection pooling via Vercel Postgres
- **Retry logic**: Automatic retry with exponential backoff for transient errors
- **Keepalive probes**: TCP keepalives prevent connection drops

### Testing Checklist

Use this checklist when deploying to Vercel:

- [ ] **Environment Variables Set**
  - [ ] `SECRET_KEY` configured
  - [ ] `ADMIN_USERNAME` and `ADMIN_PASSWORD` set
  - [ ] `GEMINI_API_KEY` configured
  - [ ] `YOUTUBE_API_KEY` configured
  - [ ] `FLASK_ENV=production`
  - [ ] Database variables auto-set by Vercel Postgres

- [ ] **Database Setup**
  - [ ] Vercel Postgres connected
  - [ ] Migrations run successfully (`migrate_db.py`)
  - [ ] Tables created (channels, videos)
  - [ ] Indexes created

- [ ] **Functionality Tests**
  - [ ] Login works
  - [ ] Single video processing works
  - [ ] Channel subscription works
  - [ ] Video fetching from YouTube API works
  - [ ] Caption extraction works
  - [ ] Summarization (short + detailed) works
  - [ ] Video listing pagination works
  - [ ] Channel filtering works
  - [ ] Video detail page displays correctly
  - [ ] Data persists after refresh

- [ ] **Performance Tests**
  - [ ] Cold start completes within 10 seconds
  - [ ] Database queries complete quickly
  - [ ] Static assets load correctly
  - [ ] No timeout errors on processing

- [ ] **API Quotas**
  - [ ] YouTube API quota sufficient for expected usage
  - [ ] Gemini API quota sufficient for expected usage

### Troubleshooting

**"Bad Request: The CSRF session token is missing"**
- This should be fixed with the latest code (commit b33475b)
- Vercel automatically sets `VERCEL=1` environment variable
- The app detects this and disables CSRF

**"ADMIN_USERNAME and ADMIN_PASSWORD environment variables must be set"**
- Make sure you've added all environment variables in Vercel settings
- Redeploy after adding environment variables

**"Login not working"**
- Check Vercel logs for errors
- Verify all environment variables are set correctly
- Make sure you're using the correct credentials

**"Database connection failed"**
- Verify Vercel Postgres is connected
- Check that `POSTGRES_PRISMA_URL` or `DATABASE_URL` is set
- Run migrations if not done already
- Check Vercel logs for specific error messages

**"Function execution timeout"**
- Processing taking too long (>10 seconds)
- Try processing fewer videos at once
- Check if YouTube API or Gemini API is slow
- Consider upgrading Vercel plan for longer timeouts

**"YouTube API quota exceeded"**
- YouTube Data API has daily quota limits
- Reduce number of videos fetched per request
- Spread out channel syncs throughout the day
- Monitor quota usage in Google Cloud Console

---

## Traditional Server Deployment (Non-Serverless)

For traditional deployments (not Vercel), CSRF protection remains enabled.

### Using Gunicorn

```bash
# Install dependencies
pip install -r requirements.txt gunicorn

# Set environment variables
export SECRET_KEY="your-secret-key"
export ADMIN_USERNAME="your-username"
export ADMIN_PASSWORD="your-password"
export GEMINI_API_KEY="your-api-key"
export FLASK_ENV="production"

# Run with Gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

### Security Features (Traditional Deployment)

All security features are active:
- ✅ CSRF protection
- ✅ Rate limiting
- ✅ Secure sessions
- ✅ Password hashing
- ✅ XSS protection
- ✅ Security headers
- ✅ Open redirect protection

---

## Environment Variable Generation

```bash
# Generate a secure SECRET_KEY
python -c "import secrets; print(secrets.token_hex(32))"

# Generate a random strong password
python -c "import secrets; import string; chars = string.ascii_letters + string.digits + string.punctuation; print(''.join(secrets.choice(chars) for _ in range(20)))"
```