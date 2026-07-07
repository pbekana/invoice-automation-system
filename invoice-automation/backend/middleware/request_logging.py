"""
Request Logging Middleware - Log all API requests.

Provides:
- Request/response logging
- Performance monitoring
- Error tracking
- IP address capture
"""

import time
from flask import request, g  # type: ignore
from functools import wraps
from logger_config import logger
from typing import Callable


def log_request():
    """Log request start time."""
    g.start_time = time.time()
    g.request_id = request.headers.get('X-Request-ID', str(time.time()))


def log_response(response):
    """Log response with timing information."""
    try:
        duration = time.time() - g.get('start_time', time.time())
        
        # Get user info if authenticated
        user_id = 'anonymous'
        if hasattr(g, 'current_user') and g.current_user:
            user_id = str(g.current_user._id)
        
        # Get client IP
        client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        
        # Log request details
        log_data = {
            'request_id': g.get('request_id'),
            'method': request.method,
            'path': request.path,
            'status': response.status_code,
            'duration_ms': round(duration * 1000, 2),
            'user_id': user_id,
            'ip': client_ip,
            'user_agent': request.headers.get('User-Agent', '')[:100]
        }
        
        # Log at appropriate level
        if response.status_code >= 500:
            logger.error(f"Request completed with error: {log_data}")
        elif response.status_code >= 400:
            logger.warning(f"Request completed with client error: {log_data}")
        else:
            logger.info(f"Request completed: {request.method} {request.path} - {response.status_code} ({log_data['duration_ms']}ms)")
        
        # Add timing header
        response.headers['X-Response-Time'] = f"{log_data['duration_ms']}ms"
        response.headers['X-Request-ID'] = log_data['request_id']
        
    except Exception as e:
        logger.error(f"Error logging response: {e}")
    
    return response


def track_api_call(action: str):
    """
    Decorator to track specific API calls in detail.
    
    Usage:
        @track_api_call("invoice_upload")
        def upload_invoice():
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            error = None
            result = None
            
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                error = e
                raise
            finally:
                duration = time.time() - start_time
                
                # Log to database for analytics
                try:
                    from db import db_manager
                    db_manager.db.api_calls.insert_one({
                        'action': action,
                        'method': request.method,
                        'path': request.path,
                        'user_id': g.get('user_id'),
                        'ip': request.headers.get('X-Forwarded-For', request.remote_addr),
                        'duration_ms': round(duration * 1000, 2),
                        'success': error is None,
                        'error': str(error) if error else None,
                        'timestamp': time.time()
                    })
                except Exception as log_error:
                    logger.error(f"Failed to log API call: {log_error}")
        
        return wrapper
    return decorator
