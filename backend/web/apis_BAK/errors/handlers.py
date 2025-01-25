from web.apis.utils.helpers import error_response

# from flask import Blueprint
# errors_bp = Blueprint('errors', __name__)

from web.extensions import bp as errors_bp

@errors_bp.app_errorhandler(404)
def error_404(error):
    """
    Handle 404 errors with a JSON response.
    """
    try:
        return error_response("Resource not found ---------", 404)
    except Exception as e:
        # Log the exception (e.g., using Flask's logger)
        errors_bp.logger.error(f"Error handling 404: {str(e)}")
        return error_response("An error occurred while processing the 404 error", 500)

@errors_bp.app_errorhandler(403)
def error_403(error):
    """
    Handle 403 errors with a JSON response.
    """
    try:
        return error_response("Access forbidden", 403)
    except Exception as e:
        # Log the exception
        errors_bp.logger.error(f"Error handling 403: {str(e)}")
        return error_response("An error occurred while processing the 403 error", 500)

@errors_bp.app_errorhandler(500)
def error_500(error):
    """
    Handle 500 errors with a JSON response.
    """
    try:
        return error_response("Internal server error", 500)
    except Exception as e:
        # Log the exception
        errors_bp.logger.error(f"Error handling 500: {str(e)}")
        return error_response("An error occurred while processing the 500 error", 500)

@errors_bp.app_errorhandler(413)
def error_413(error):
    """
    Handle 413 errors with a JSON response.
    """
    try:
        return error_response("Request entity too large", 413)
    except Exception as e:
        # Log the exception
        errors_bp.logger.error(f"Error handling 413: {str(e)}")
        return error_response("An error occurred while processing the 413 error", 500)
