from functools import wraps
from flask_jwt_extended import current_user, jwt_required
from web.apis.utils.serializers import error_response

def confirm_email(func):
    """Check if email has been confirmed"""
    @wraps(func)
    @jwt_required()  # Ensure JWT is required for this route
    def wrapper_function(*args, **kwargs):
        if not current_user.verified:
            return error_response("You're yet to verify your account!", status_code=403)  # Forbidden
        return func(*args, **kwargs)
    return wrapper_function


def access_required_former(*required_roles, strict=False):
    """Decorator to check user roles or allow admin/current_user access.
    
    Parameters:
        *required_roles: Roles required to access the route.
        strict (bool): If True, only the specified roles have access (no fallback).
    """
    def decorator(view_func):
        @wraps(view_func)
        @jwt_required()  # Ensure JWT is required for this route
        def wrapper(*args, **kwargs):
            requested_username = kwargs.get('username')

            # Strict access check
            if strict:
                user_has_role = any(role_x in [role_y.name for role_y in current_user.roles] for role_x in required_roles)
                if user_has_role:
                    return view_func(*args, **kwargs)
                else:
                    return error_response("Access forbidden: insufficient permissions.", status_code=403)  # Forbidden

            # Non-strict access check (admin or current user)
            if current_user.is_admin or (requested_username and current_user.username == requested_username):
                return view_func(*args, **kwargs)

            # Check for required roles
            user_has_role = any(role_x in [role_y.name for role_y in current_user.roles] for role_x in required_roles)
            allow_all = any('*' in role for role in required_roles)

            if user_has_role or allow_all:
                return view_func(*args, **kwargs)
            else:
                return error_response("Access forbidden: insufficient permissions.", status_code=403)  # Forbidden

        return wrapper
    return decorator

def access_required(*required_roles, strict=False):
    """Decorator to check user roles or allow account owner access.
    
    Parameters:
        *required_roles: Roles required to access the route.
        strict (bool): If True, only the specified roles have access (no fallback).
    """
    """ 
    a. If user has role/permission grant access. This will also allow admin access without a different checks.
    b. If user owns the account grant access.
    c. If `*` in required_roles, allow access to all.
    """
    def decorator(view_func):
        @wraps(view_func)
        @jwt_required()  # Ensure JWT is required for this route
        def wrapper(*args, **kwargs):
            # Extract the requested user identifier (can be id, email, or username)
            requested_user_id = kwargs.get('user_id')  # This is the user identifier from the URL or route parameters

            # Check if user has any of the required roles
            user_has_role = any(role in [role_y.name for role_y in current_user.roles] for role in required_roles)
            allow_all = any(role == '*' for role in required_roles)

            # Grant access if user has a required role or if `*` is present
            if user_has_role or allow_all:
                return view_func(*args, **kwargs)

            # Grant access if the user owns the account (by id, email, or username)
            if requested_user_id:
                if (str(current_user.id) == requested_user_id or
                    current_user.email == requested_user_id or
                    current_user.username == requested_user_id):
                    return view_func(*args, **kwargs)

            # If none of the conditions are met, deny access
            return error_response("Access forbidden: insufficient permissions.", status_code=403)  # Forbidden

        return wrapper
    return decorator

# access_required() combines these 2 below:
def role_required(*required_roles):
    def decorator(view_func):
        @wraps(view_func)
        @jwt_required()  # Ensure JWT is required for this route
        def wrapper(*args, **kwargs):
            user_has_role = any(role_x in [role_y.name for role_y in current_user.roles] for role_x in required_roles)
            allow_all = any('*' in role for role in required_roles)

            if user_has_role or allow_all:
                return view_func(*args, **kwargs)
            else:
                return error_response("Access forbidden: insufficient permissions.", status_code=403)  # Forbidden

        return wrapper
    return decorator

def admin_or_current_user():
    def decorator(view_func):
        """Allow only admin/current_user access to this route"""
        @wraps(view_func)
        @jwt_required()  # Ensure JWT is required for this route
        def wrapper(*args, **kwargs):
            requested_username = kwargs.get('username')
            if current_user.is_admin or current_user.username == requested_username:
                return view_func(*args, **kwargs)
            else:
                return error_response("Access forbidden: insufficient permissions.", status_code=403)  # Forbidden

        return wrapper
    return decorator

# 

from functools import wraps
from flask_jwt_extended import decode_token, get_jwt_identity
from flask import request
from jwt import ExpiredSignatureError, InvalidTokenError
from flask_jwt_extended.config import config
from flask_jwt_extended.utils import get_unverified_jwt_headers
from flask_jwt_extended.exceptions import NoAuthorizationError

def jwt_required_ws():
    """
    Custom decorator to handle JWT authentication for WebSocket endpoints.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            token = None

            # Try to get the token from the configured locations
            try:
                if 'headers' in config.token_location:
                    auth_header = request.headers.get('Authorization', None)
                    if auth_header and auth_header.startswith('Bearer '):
                        token = auth_header.split(' ')[1]

                if not token and 'cookies' in config.token_location:
                    token = request.cookies.get(config.access_cookie_name, None)

                if not token and 'query_string' in config.token_location:
                    query_string_params = request.args
                    token = query_string_params.get(config.query_string_name, None)

                if not token and 'json' in config.token_location:
                    json_data = request.json
                    token = json_data.get(config.json_key_name, None)

                # If no token is found, raise an exception
                if not token:
                    raise NoAuthorizationError("Missing JWT token")

                # Decode the token
                decoded_token = decode_token(token)
                request.current_user = decoded_token['sub']  # Attach the user identity to the request

            except ExpiredSignatureError:
                return {"success": False, "error": "Your session has expired. Please log in again."}
            except InvalidTokenError:
                return {"success": False, "error": "Invalid token. Please log in again."}
            except Exception as e:
                return {"success": False, "error": str(e)}

            # Call the actual function
            return func(*args, **kwargs)
        return wrapper
    return decorator
