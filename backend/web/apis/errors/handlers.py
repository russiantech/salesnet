from flask import Blueprint

from web.apis.utils.serializers import error_response

error_bp = Blueprint('errors', __name__)
# from web.extensions import bp as error_bp

@error_bp.app_errorhandler(422)
def error_422(error):
    """
    Handle 404 errors with a JSON response.
    """
    try:
        
        return error_response("unprocessible entity, ensure you send valid data & format to the server. confirm your jwt token is correct.", 422)
    except Exception as e:
        # Log the exception (e.g., using Flask's logger)
        error_bp.logger.error(f"Error handling 422: {str(e)}")
        return error_response("An error occurred while processing the 422 error", 422)
    
@error_bp.app_errorhandler(405)
def error_405(error):
    """
    Handle 405 errors with a JSON response.
    """
    try:
        
        return error_response("Method not allowed.", 405)
    except Exception as e:
        # Log the exception (e.g., using Flask's logger)
        error_bp.logger.error(f"Error handling 405: {str(e)}")
        return error_response("An error occurred while processing the 405 error", 405)
    
@error_bp.app_errorhandler(404)
def error_404(error):
    """
    Handle 404 errors with a JSON response.
    """
    try:
        
        return error_response("Resource not found", 404)
    except Exception as e:
        # Log the exception (e.g., using Flask's logger)
        error_bp.logger.error(f"Error handling 404: {str(e)}")
        return error_response("An error occurred while processing the 404 error", 404)

@error_bp.app_errorhandler(403)
def error_403(error):
    """
    Handle 403 errors with a JSON response.
    """
    try:
        return error_response("Access forbidden", 403)
    except Exception as e:
        # Log the exception
        error_bp.logger.error(f"Error handling 403: {str(e)}")
        return error_response("An error occurred while processing the 403 error", 403)

@error_bp.app_errorhandler(413)
def error_413(error):
    """
    Handle 413 errors with a JSON response.
    """
    try:
        return error_response("Request entity too large", 413)
    except Exception as e:
        # Log the exception
        error_bp.logger.error(f"Error handling 413: {str(e)}")
        return error_response("An error occurred while processing the 413 error", 413)
    
@error_bp.app_errorhandler(415)
def error_415(error):
    """
    Handle 415 errors with a JSON response.
    """
    try:
        return error_response("Unsupported media type", 415)
    except Exception as e:
        # Log the exception
        error_bp.logger.error(f"Error handling 415: {str(e)}")
        return error_response("An error occurred while processing the 415 error", 415)

@error_bp.app_errorhandler(409)
def error_409(error):
    """
    Handle 409 errors with a JSON response.
    """
    try:
        return error_response("Integrity/Duplicate Entires Deteccted", 409)
    except Exception as e:
        # Log the exception
        error_bp.logger.error(f"Error handling 409: {str(e)}")
        return error_response("An error occurred while processing the 409 error", 409)
    
@error_bp.app_errorhandler(429)
def error_429(error):
    """
    Handle 429 errors with a JSON response.
    """
    try:
        return error_response("Too many requests in just a few seconds, be calming down my gee.", 429)
    except Exception as e:
        # Log the exception
        error_bp.logger.error(f"Error handling 413: {str(e)}")
        return error_response("An error occurred while processing the 429 error", 429)
    
@error_bp.app_errorhandler(500)
def error_500(error):
    """
    Handle 500 errors with a JSON response.
    """
    try:
        return error_response("Internal server error", 500)
    except Exception as e:
        # Log the exception
        error_bp.logger.error(f"Error handling 500: {str(e)}")
        return error_response("An error occurred while processing the 500 error", 500)
    
from jwt.exceptions import ExpiredSignatureError
@error_bp.app_errorhandler(ExpiredSignatureError)
def handle_expired_jwt_token(error):
    """
    Handle handle_expired_jwt_token errors with a JSON response.
    """
    try:
        return error_response(f"Unexpected Error: {str(error)}", 401)
    except Exception as e:
        # Log the exception
        error_bp.logger.error(f"handle_expired_jwt_token: {str(e)}")
        return error_response("An error occurred while processing the expired_jwt_token", 500)
