# Security Features - YouTube Captions Application

This document outlines the comprehensive security features implemented in the YouTube Channel Subscription and Summary Management system.

## Overview

Phase 8 has hardened the application with production-ready security features including input validation, startup validation, rate limiting, and comprehensive error handling.

---

## Security Modules

### 1. Input Validation (`validators.py`)

Comprehensive validation for all user inputs:

#### YouTube URL Validation
- Validates YouTube video URLs (youtube.com/watch, youtu.be formats)
- Validates YouTube channel URLs (channel/, c/, @, user/ formats)
- Extracts and validates video IDs (11-character format)
- Validates channel IDs (UC prefix + 22 characters)
- URL length limits (max 2048 characters)
- Prevents malformed URL injection

#### Parameter Validation
- Pagination parameters (page, per_page) with bounds checking
- Integer ID validation with positive value enforcement
- Max videos parameter with configurable limits
- Text sanitization with length limits (max 1MB)

#### Security Limits
```python
MAX_VIDEOS_PER_REQUEST = 50
MAX_VIDEOS_BATCH_PROCESS = 20
MAX_PAGE_SIZE = 50
MAX_URL_LENGTH = 2048
MAX_TEXT_LENGTH = 1000000  # 1MB
```

### 2. Startup Validation (`startup_validator.py`)

Validates environment configuration before application starts:

#### Environment Variable Checks
- **SECRET_KEY**: Minimum 24 characters, no common insecure values
- **GEMINI_API_KEY**: Minimum 30 characters, no placeholder values
- **YOUTUBE_API_KEY**: Minimum 30 characters, no placeholder values
- **Database URL**: Priority detection (POSTGRES_PRISMA_URL > DATABASE_URL > POSTGRES_URL)

#### Validation Output
```
============================================================
Starting environment validation...
============================================================
✓ SECRET_KEY: Valid
✓ Database URL: Using POSTGRES_PRISMA_URL
✓ GEMINI_API_KEY: Valid
✓ YOUTUBE_API_KEY: Valid
============================================================
✓ All required environment variables are valid
============================================================
```

#### Error Handling
- Clear error messages for missing/invalid configuration
- Application refuses to start if critical configuration is missing
- No sensitive data in error messages

---

## Endpoint Security

### Authentication
- All routes protected with `@login_required` decorator
- Secure session cookies with HttpOnly, SameSite=Lax
- 2-hour session lifetime
- Password hashing with Werkzeug

### Rate Limiting
Rate limits configured for all endpoints:

```python
# Login endpoint
@limiter.limit("5 per minute")

# Caption extraction
@limiter.limit("10 per minute")

# AI summarization
@limiter.limit("5 per minute")

# Channel management
@limiter.limit("10 per minute")  # Add/Delete

# Video sync
@limiter.limit("5 per minute")

# Batch processing
@limiter.limit("3 per minute")

# Global limits
"200 per day", "50 per hour"
```

### Input Validation Integration

All endpoints now validate inputs before processing:

#### GET /api/videos
- Validates pagination parameters (page, per_page)
- Validates channel_id if provided
- Sanitizes order_by parameter

#### POST /api/channels
- Validates YouTube channel URL format
- Checks for malformed URLs
- Prevents injection attacks

#### DELETE /api/channels/<id>
- Validates integer ID
- Ensures positive values

#### POST /get_captions
- Validates YouTube video URL
- Extracts and validates video ID
- Prevents malformed URL processing

#### POST /api/sync/channel/<id>
- Validates channel ID
- Validates max_videos parameter
- Enforces limits (max 50 videos per request)

#### POST /api/process/pending
- Validates max_videos parameter
- Enforces batch limit (max 20 videos)
- Prevents timeout from excessive processing

---

## Security Headers

Comprehensive HTTP security headers on all responses:

```python
X-Content-Type-Options: nosniff
X-Frame-Options: SAMEORIGIN  # Allow YouTube embeds
X-XSS-Protection: 1; mode=block
Strict-Transport-Security: max-age=31536000; includeSubDomains

Content-Security-Policy:
  - default-src 'self'
  - script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net
  - style-src 'self' 'unsafe-inline' https://fonts.googleapis.com
  - font-src 'self' https://fonts.gstatic.com
  - img-src 'self' data: https://img.youtube.com https://i.ytimg.com
            https://yt3.ggpht.com https://via.placeholder.com
  - frame-src https://www.youtube.com https://youtube.com
  - media-src 'self' https://www.youtube.com
```

### CSP Policy Explanation
- `default-src 'self'`: Only load resources from same origin by default
- `script-src`: Allow scripts from CDN (Marked.js) and inline scripts for dynamic content
- `style-src`: Allow styles from Google Fonts and inline styles
- `img-src`: Allow YouTube thumbnails and placeholder images
- `frame-src`: Allow YouTube video embeds
- `media-src`: Allow YouTube media content

---

## Database Security

### Connection Security
- SSL connections for Vercel Postgres (pgBouncer mode)
- TCP keepalives for connection stability
- Connection retry logic with exponential backoff (3 retries)
- 10-second connection timeout

### Schema Constraints
```python
# Unique constraints
channel_id: unique=True, nullable=False
video_id: unique=True, nullable=False

# Foreign key constraints with CASCADE
Video.channel_id → Channel.id (ondelete='CASCADE')

# Indexes for performance
channel_id: indexed
video_id: indexed
published_at: indexed
processing_status: indexed
(channel_id, published_at): composite index
(processing_status, created_at): composite index
```

### SQL Injection Prevention
- All queries use SQLAlchemy ORM (parameterized queries)
- No raw SQL string concatenation
- Input validation before database operations

---

## Error Handling

### Comprehensive Logging
```python
# All errors logged with context
logger.error(f"Error adding channel {channel_url}: {e}", exc_info=True)
logger.warning(f"Invalid YouTube URL: {video_url} - {error}")
logger.info(f"Successfully added channel: {channel.channel_name}")
```

### User-Friendly Error Messages
- Generic error messages to users (no stack traces)
- Detailed logging for debugging (with exc_info)
- HTTP status codes reflect error type:
  - 400: Bad Request (validation errors)
  - 404: Not Found (missing resources)
  - 409: Conflict (duplicate entries)
  - 500: Internal Server Error (unexpected errors)

### API Error Response Format
```json
{
  "error": "Invalid YouTube URL format (expected /watch?v=...)"
}
```

---

## Open Redirect Protection

Safe redirect checking for login flow:

```python
def is_safe_url(target):
    """Check if the target URL is safe for redirects."""
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc
```

---

## CSRF Protection

CSRF protection available via Flask-WTF:
- Imported and configured in app.py
- Currently disabled for serverless compatibility
- Can be enabled by uncommenting csrf initialization

---

## Environment File Security

### .gitignore Protection
```
# Verified .env is in .gitignore
.env
```

### .env.example Template
Safe template with placeholders (no real credentials):
```
SECRET_KEY=your_secret_key_here_min_24_chars_random_string
GEMINI_API_KEY=your_gemini_api_key_here
YOUTUBE_API_KEY=your_youtube_api_key_here
```

---

## Serverless Security Considerations

### Vercel Environment
- Detects Vercel environment: `IS_VERCEL = os.environ.get('VERCEL') == '1'`
- Uses NullPool for database connections (no connection pooling)
- Relies on pgBouncer (POSTGRES_PRISMA_URL) for pooling
- Optimized for cold starts with retry logic

### Production Configuration
```python
# Secure cookies in production
app.config['SESSION_COOKIE_SECURE'] = os.environ.get('FLASK_ENV') == 'production'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
```

---

## Security Testing Checklist

Before deployment, verify:

- [ ] All environment variables validated on startup
- [ ] Rate limits tested (login, API endpoints)
- [ ] Invalid input rejected with appropriate errors
- [ ] SQL injection attempts blocked
- [ ] XSS attempts blocked by CSP
- [ ] CSRF tokens work (if enabled)
- [ ] Security headers present in responses
- [ ] Database constraints enforced
- [ ] Error messages don't leak sensitive data
- [ ] HTTPS enforced in production (SESSION_COOKIE_SECURE)
- [ ] Login rate limiting prevents brute force
- [ ] Session timeout works (2 hours)

---

## Security Best Practices

### API Keys
- Never commit API keys to git
- Use environment variables for all secrets
- Rotate keys regularly
- Use different keys for dev/staging/production

### Passwords
- User passwords hashed with Werkzeug
- No plaintext password storage
- Strong password policy enforced (see auth.py)

### Database
- Use connection pooling (pgBouncer)
- Enable SSL for database connections
- Regular backups (Vercel Postgres handles this)
- Monitor for unusual query patterns

### Deployment
- Set `FLASK_ENV=production` in production
- Enable `SESSION_COOKIE_SECURE` for HTTPS
- Use Vercel's environment variable encryption
- Monitor logs for security events

---

## Future Security Enhancements

Optional improvements for Phase 9:

1. **Two-Factor Authentication (2FA)**
   - Add TOTP support
   - Email verification

2. **API Key Rotation**
   - Automated key rotation
   - Key expiration tracking

3. **Audit Logging**
   - Track all administrative actions
   - Failed login attempts
   - Data modifications

4. **Content Security Policy (CSP) Reporting**
   - Add CSP report-uri
   - Monitor CSP violations

5. **Dependency Scanning**
   - Regular dependency updates
   - Vulnerability scanning (Snyk, Dependabot)

---

## Contact

For security concerns or to report vulnerabilities, please contact the development team.

**Last Updated**: 2025-10-01
**Security Review**: Phase 8 Complete
