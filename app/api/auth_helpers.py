from functools import wraps
from flask import request
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from app.core.logger_config import logger


def get_current_user_id() -> int:
    """
    Get the current user ID from JWT token, or return system user (1) if not authenticated.
    This function verifies JWT optionally and returns the user ID or defaults to system user.
    """
    try:
        # Try to verify JWT token (optional=True means it won't raise if missing)
        verify_jwt_in_request(optional=True)
        user_id = get_jwt_identity()
        if user_id:
            return int(user_id)
    except Exception as e:
        logger.debug(f"JWT verification failed or no token provided: {e}")
    
    # Default to system user if not authenticated
    return 1


def jwt_required_optional(f):
    """
    Decorator that allows endpoints to work with or without JWT authentication.
    If JWT is present and valid, it's verified. Otherwise, the endpoint still works.
    Use get_current_user_id() inside the endpoint to get the user ID (or system user if not authenticated).
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Try to verify JWT, but don't fail if it's missing
        try:
            verify_jwt_in_request(optional=True)
        except Exception:
            pass  # Continue without JWT
        return f(*args, **kwargs)
    return decorated_function

