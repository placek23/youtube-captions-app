# Deployment Guide

## Vercel Deployment

### Prerequisites
- Vercel account
- GitHub repository connected to Vercel

### Environment Variables

Add these environment variables in your Vercel project settings (Settings → Environment Variables):

| Variable | Required | Example Value | Description |
|----------|----------|---------------|-------------|
| `SECRET_KEY` | ✅ Yes | `7b42bca9...41393053` | Flask secret key for sessions (generate with `python -c "import secrets; print(secrets.token_hex(32))"`) |
| `ADMIN_USERNAME` | ✅ Yes | `admin_yt2024` | Admin username for login |
| `ADMIN_PASSWORD` | ✅ Yes | `SecureYT!Pass#2024$Admin` | Admin password (use a strong password!) |
| `GEMINI_API_KEY` | ✅ Yes | `AIzaSy...` | Google Gemini API key from https://makersuite.google.com/app/apikey |
| `FLASK_ENV` | ⚠️ Recommended | `production` | Set to `production` for production deployments |

### Deployment Steps

1. **Connect Repository**
   - Go to https://vercel.com/new
   - Import your GitHub repository
   - Vercel will auto-detect Flask and configure build settings

2. **Add Environment Variables**
   - Go to Project Settings → Environment Variables
   - Add all 5 required variables listed above
   - Apply to: Production, Preview, and Development

3. **Deploy**
   - Vercel will automatically deploy when you push to main branch
   - Or manually trigger deployment from Vercel dashboard

4. **Test**
   - Visit your Vercel URL
   - Login with your credentials
   - Test caption extraction and summarization

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

### Troubleshooting

**"Bad Request: The CSRF session token is missing"**
- This should be fixed with the latest code (commit b33475b)
- Vercel automatically sets `VERCEL=1` environment variable
- The app detects this and disables CSRF

**"ADMIN_USERNAME and ADMIN_PASSWORD environment variables must be set"**
- Make sure you've added all environment variables in Vercel settings
- Redeploy after adding environment variables

**Login not working**
- Check Vercel logs for errors
- Verify all environment variables are set correctly
- Make sure you're using the correct credentials

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