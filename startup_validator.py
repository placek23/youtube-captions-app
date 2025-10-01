"""
Startup validation utilities for environment variables and configuration.

This module ensures all required environment variables are present and valid
before the application starts, providing clear error messages for missing
or invalid configuration.
"""

import os
import sys
import logging
from typing import List, Tuple, Optional

logger = logging.getLogger(__name__)


class StartupValidationError(Exception):
    """Exception raised when startup validation fails."""
    pass


def validate_env_var(
    var_name: str,
    required: bool = True,
    min_length: int = 0,
    description: str = ""
) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Validate a single environment variable.

    Args:
        var_name: Name of the environment variable
        required: Whether the variable is required
        min_length: Minimum length for the value
        description: Human-readable description of the variable

    Returns:
        Tuple of (is_valid, value, error_message)
    """
    value = os.environ.get(var_name)

    if not value:
        if required:
            return False, None, f"{var_name} is required but not set"
        return True, None, None

    value = value.strip()

    if min_length > 0 and len(value) < min_length:
        return False, value, f"{var_name} is too short (minimum {min_length} characters)"

    return True, value, None


def validate_api_key(key_name: str, min_length: int = 20) -> Tuple[bool, Optional[str]]:
    """
    Validate an API key environment variable.

    Args:
        key_name: Name of the API key environment variable
        min_length: Minimum expected length for the API key

    Returns:
        Tuple of (is_valid, error_message)
    """
    is_valid, value, error = validate_env_var(key_name, required=True, min_length=min_length)

    if not is_valid:
        return False, error

    # Check for placeholder values
    placeholder_values = ['your_', 'placeholder', 'example', 'test_key', 'xxx']
    if value and any(placeholder in value.lower() for placeholder in placeholder_values):
        return False, f"{key_name} appears to contain a placeholder value. Please set a real API key."

    return True, None


def validate_database_url() -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Validate database connection URL.

    Checks for POSTGRES_PRISMA_URL, DATABASE_URL, or POSTGRES_URL
    in priority order.

    Returns:
        Tuple of (is_valid, url_name_used, error_message)
    """
    url_vars = ['POSTGRES_PRISMA_URL', 'DATABASE_URL', 'POSTGRES_URL']

    for var_name in url_vars:
        url = os.environ.get(var_name)
        if url:
            # Basic validation
            url = url.strip()
            if len(url) < 10:
                return False, var_name, f"{var_name} is too short to be a valid database URL"

            # Check for postgres/postgresql protocol
            if not (url.startswith('postgres://') or url.startswith('postgresql://')):
                return False, var_name, f"{var_name} must start with postgres:// or postgresql://"

            return True, var_name, None

    return False, None, (
        "No database URL found. Please set one of the following:\n"
        "  - POSTGRES_PRISMA_URL (recommended for Vercel)\n"
        "  - DATABASE_URL\n"
        "  - POSTGRES_URL"
    )


def validate_secret_key() -> Tuple[bool, Optional[str]]:
    """
    Validate Flask SECRET_KEY.

    Returns:
        Tuple of (is_valid, error_message)
    """
    secret_key = os.environ.get('SECRET_KEY')

    if not secret_key:
        return False, "SECRET_KEY is required for Flask session management"

    secret_key = secret_key.strip()

    # Check minimum length
    if len(secret_key) < 24:
        return False, "SECRET_KEY should be at least 24 characters for security"

    # Check for common insecure values
    insecure_values = ['dev', 'test', 'secret', 'password', '12345', 'changeme']
    if secret_key.lower() in insecure_values:
        return False, "SECRET_KEY appears to be insecure. Please use a strong random value."

    return True, None


def run_startup_validation(strict: bool = True) -> bool:
    """
    Run comprehensive startup validation for all required configuration.

    Args:
        strict: If True, raises StartupValidationError on any failure.
                If False, logs warnings but continues.

    Returns:
        bool: True if all validations passed, False otherwise.

    Raises:
        StartupValidationError: If strict=True and validation fails.
    """
    errors = []
    warnings = []

    logger.info("=" * 60)
    logger.info("Starting environment validation...")
    logger.info("=" * 60)

    # Validate SECRET_KEY
    is_valid, error = validate_secret_key()
    if not is_valid:
        errors.append(f"✗ SECRET_KEY: {error}")
    else:
        logger.info("✓ SECRET_KEY: Valid")

    # Validate database URL
    is_valid, url_name, error = validate_database_url()
    if not is_valid:
        errors.append(f"✗ Database URL: {error}")
    else:
        logger.info(f"✓ Database URL: Using {url_name}")

    # Validate GEMINI_API_KEY
    is_valid, error = validate_api_key('GEMINI_API_KEY', min_length=30)
    if not is_valid:
        errors.append(f"✗ GEMINI_API_KEY: {error}")
    else:
        logger.info("✓ GEMINI_API_KEY: Valid")

    # Validate YOUTUBE_API_KEY
    is_valid, error = validate_api_key('YOUTUBE_API_KEY', min_length=30)
    if not is_valid:
        errors.append(f"✗ YOUTUBE_API_KEY: {error}")
    else:
        logger.info("✓ YOUTUBE_API_KEY: Valid")

    # Optional: Check FLASK_ENV
    flask_env = os.environ.get('FLASK_ENV', 'development')
    if flask_env == 'production':
        logger.info("✓ FLASK_ENV: production")
    else:
        warnings.append(f"⚠ FLASK_ENV: {flask_env} (development mode)")

    # Optional: Check for Vercel environment
    if os.environ.get('VERCEL') == '1':
        logger.info("✓ Running in Vercel serverless environment")

    logger.info("=" * 60)

    # Report results
    if errors:
        logger.error(f"Environment validation failed with {len(errors)} error(s):")
        for error in errors:
            logger.error(f"  {error}")

        if strict:
            logger.error("\nPlease fix the above errors and restart the application.")
            raise StartupValidationError(
                f"Environment validation failed:\n" + "\n".join(errors)
            )
        return False

    if warnings:
        logger.warning(f"Environment validation completed with {len(warnings)} warning(s):")
        for warning in warnings:
            logger.warning(f"  {warning}")

    logger.info("✓ All required environment variables are valid")
    logger.info("=" * 60)
    return True


def generate_env_example() -> str:
    """
    Generate a template .env.example file content.

    Returns:
        str: Content for .env.example file
    """
    return """# Flask Configuration
SECRET_KEY=your_secret_key_here_min_24_chars_random_string

# Google Gemini API (for AI summarization)
# Get your API key from: https://makersuite.google.com/app/apikey
GEMINI_API_KEY=your_gemini_api_key_here

# YouTube Data API v3 (for channel/video metadata)
# Get your API key from: https://console.cloud.google.com/apis/credentials
YOUTUBE_API_KEY=your_youtube_api_key_here

# Database Configuration (Vercel Postgres)
# These are automatically set by Vercel when you connect a Postgres database
# For local development, get these from your Vercel project settings
POSTGRES_URL=postgresql://user:password@host:5432/database
DATABASE_URL=postgresql://user:password@host:5432/database
POSTGRES_PRISMA_URL=postgresql://user:password@host:5432/database?pgbouncer=true

# Optional: Flask Environment
FLASK_ENV=development  # Set to 'production' for production deployment
FLASK_HOST=0.0.0.0
FLASK_PORT=5000

# Optional: Vercel Environment (automatically set by Vercel)
# VERCEL=1
"""


# Export main functions
__all__ = [
    'run_startup_validation',
    'validate_api_key',
    'validate_database_url',
    'validate_secret_key',
    'generate_env_example',
    'StartupValidationError',
]
