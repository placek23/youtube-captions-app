#!/usr/bin/env python
"""
Production-style server runner that disables all caching
"""
import os
import sys

# Disable bytecode generation
sys.dont_write_bytecode = True
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

# Import app
from app import app

if __name__ == '__main__':
    # Disable Jinja2 template caching
    app.jinja_env.auto_reload = True
    app.config['TEMPLATES_AUTO_RELOAD'] = True

    # Run without reloader and with minimal debug features
    print("=" * 60)
    print("Starting Flask server WITHOUT reloader or caching")
    print("Server URL: http://127.0.0.1:5001")
    print("=" * 60)

    app.run(
        host='0.0.0.0',
        port=5001,
        debug=True,
        use_reloader=False,
        threaded=True
    )