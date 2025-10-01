from app import app

# Vercel serverless function handler
def handler(event, context):
    return app(event, context)

# For Vercel's WSGI adapter
app = app
