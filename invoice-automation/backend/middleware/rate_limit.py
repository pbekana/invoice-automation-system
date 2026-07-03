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


# Common rate limit decorators
def rate_limit_strict(func):
    """Strict rate limit: 10 requests per minute."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        if limiter:
            limiter.limit("10 per minute")(func)(*args, **kwargs)
        return func(*args, **kwargs)
    return wrapper


def rate_limit_moderate(func):
    """Moderate rate limit: 30 requests per minute."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        if limiter:
            limiter.limit("30 per minute")(func)(*args, **kwargs)
        return func(*args, **kwargs)
    return wrapper


def rate_limit_relaxed(func):
    """Relaxed rate limit: 100 requests per minute."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        if limiter:
            limiter.limit("100 per minute")(func)(*args, **kwargs)
        return func(*args, **kwargs)
    return wrapper
