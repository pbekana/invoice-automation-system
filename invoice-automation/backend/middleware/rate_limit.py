"""
Rate Limiting Middleware - Prevent API abuse.

Provides:
- Per-endpoint rate limiting
- Per-user rate limiting
- IP-based rate limiting
- Configurable limits
"""

from functools import wraps
from flask import request, jsonify, g  # type: ignore
from flask_limiter import Limiter  # type: ignore
from flask_limiter.util import get_remote_address  # type: ignore
from logger_config import logger


def get_user_identifier():
    """Get user identifier for rate limiting (user ID or IP)."""
    # Try to get authenticated user ID
    user_id = getattr(g, 'user_id', None)
    if user_id:
        return f"user:{user_id}"
    
    # Fall back to IP address
    return f"ip:{get_remote_address()}"


# Rate limiter configuration
# NOTE: This will be initialized in app.py with Flask app instance
limiter = None


def init_rate_limiter(app):
    """Initialize rate limiter with Flask app."""
    global limiter
    
    # Check if Redis is available, otherwise use in-memory storage
    storage_uri = app.config.get('RATELIMIT_STORAGE_URL', 'memory://')
    
    limiter = Limiter(
        app=app,
        key_func=get_user_identifier,
        default_limits=["200 per hour", "50 per minute"],
        storage_uri=storage_uri,
        strategy="fixed-window"
    )
    
    logger.info(f"Rate limiter initialized with storage: {storage_uri}")
    return limiter

