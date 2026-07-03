"""Authentication middleware for protecting routes."""
from functools import wraps
from flask import request, jsonify, g  # type: ignore
from typing import List, Optional, Callable

from logger_config import logger


def get_token_from_header() -> Optional[str]:
    """Extract JWT token from Authorization header."""
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return None
    
    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != 'bearer':
        return None
    
    return parts[1]


def require_auth(f: Callable) -> Callable:
    """Decorator to require authentication for a route."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from services.auth_service import auth_service  # type: ignore
        
        token = get_token_from_header()
        if not token:
            logger.warning(f"Unauthorized access attempt to {request.path}")
            return jsonify({"error": "Authentication required"}), 401
        
        # Verify token
        valid, payload, error = auth_service.verify_token(token)
        if not valid:
            logger.warning(f"Invalid token for {request.path}: {error}")
            return jsonify({"error": error or "Invalid token"}), 401
        
        # Get user
        user = auth_service.get_user_by_id(payload["user_id"])
        if not user or not user.is_active():
            logger.warning(f"Inactive user attempt: {payload.get('email')}")
            return jsonify({"error": "User not found or inactive"}), 401
        
        # Store user in request context
        g.current_user = user
        g.token_payload = payload
        
        return f(*args, **kwargs)
    
    return decorated_function


def require_roles(roles: List[str]) -> Callable:
    """Decorator to require specific roles for a route."""
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        @require_auth
        def decorated_function(*args, **kwargs):
            user = g.current_user
            
            if not user.has_any_role(roles):
                logger.warning(
                    f"Authorization failed for {user.email} on {request.path}. "
                    f"Required roles: {roles}, User roles: {user.roles}"
                )
                return jsonify({
                    "error": "Insufficient permissions",
                    "required_roles": roles
                }), 403
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator


def optional_auth(f: Callable) -> Callable:
    """Decorator for routes that work with or without authentication."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from services.auth_service import auth_service  # type: ignore
        
        token = get_token_from_header()
        if token:
            valid, payload, _ = auth_service.verify_token(token)
            if valid:
                user = auth_service.get_user_by_id(payload["user_id"])
                if user and user.is_active():
                    g.current_user = user
                    g.token_payload = payload
        
        # Set to None if not authenticated
        if not hasattr(g, 'current_user'):
            g.current_user = None
        
        return f(*args, **kwargs)
    
    return decorated_function


def get_current_user():
    """Helper to get current authenticated user from request context."""
    return getattr(g, 'current_user', None)


def get_current_user_id() -> Optional[str]:
    """Helper to get current user ID."""
    user = get_current_user()
    return str(user._id) if user else None
