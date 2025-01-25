
class SequentialGenerator:
    def __init__(self, start=1):
        self.counter = start

    def next(self):
        current_value = self.counter
        self.counter += 1
        return current_value

# Create an instance of the SequentialGenerator
generator = SequentialGenerator(start=10)
# version=generator.next()

# Making slug
from slugify import slugify

def slugifie(title, id=0):
    combined = f"{title}-{id}"
    return slugify(combined.lower())

import random
import string

def generate_random_id(k=8):
    """Generate a random alphanumeric ID."""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=k)).lower()

def make_slug(text):
    """
    Generate a slug from the given text with a random ID. 
    usage:
    text = "This is a long text with some characters."
    slug = make_slug(text)
    print(slug)  # Output example: 'This-is-a-long-text-q7ZwF9Xv'
    """
    # Generate a random ID
    id = generate_random_id()

    # Extract the first 50 characters of the text
    text_prefix = text[:50]
    
    # Remove any non-alphanumeric characters and replace spaces with hyphens
    cleaned_text = ''.join(c if c.isalnum() else '-' for c in text_prefix.strip()).strip('-')
    
    # Combine the cleaned text and the ID to create the slug
    slug = f"{cleaned_text}-{id}"
    
    return slug.lower()
 
from flask import request
def user_ip():
    if request.environ.get('HTTP_X_FORWARDED_FOR') is None:
        ip =  request.environ['REMOTE_ADDR']
    else:
        ip = request.environ['HTTP_X_FORWARDED_FOR'] # if behind a proxy
    return ip


def strtobool_custom(value):
    value = value.lower()
    if value in ('y', 'yes', 'true', 't', '1'):
        return True
    elif value in ('n', 'no', 'false', 'f', '0'):
        return False
    else:
        raise ValueError(f"Invalid boolean string: {value}")

def validate_file_upload(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ['png', 'jpeg', 'jpg']
           

from flask_jwt_extended import decode_token
from jwt import ExpiredSignatureError, InvalidTokenError
from web.apis.utils.serializers import error_response
def extract_and_verify_jwt_ws(data, connection_manager, event_name):
    """
    Extract and verify a JWT token from WebSocket request data.

    Parameters:
        data (dict): The WebSocket request payload containing the token.
        connection_manager (object): WebSocket connection manager for sending responses.
        event_name (str): The event name to respond to in case of errors.

    Returns:
        str: The current user's identifier (e.g., "sub") if authentication is successful.
        None: If authentication fails, a response is sent via `connection_manager`.

    Example Usage:
        current_user = extract_and_verify_jwt(data, connection_manager, 'save_chat_response')
        if not current_user:
            # Authentication failed, response already sent
            return
    """
    # Extract the token
    token = data.get('jwt') or request.args.get('jwt')
    if not token:
        error, _ = error_response(f"Missing token. Please provide a valid token. {request.headers}")
        connection_manager.notify(event_name, data=error)
        return None

    # Verify the token
    try:
        decoded_token = decode_token(token)
        current_user = decoded_token.get("sub")
    except ExpiredSignatureError:
        error, _ = error_response("Your session has expired. Please log in again.")
        connection_manager.notify(event_name, data=error)
        return None
    except InvalidTokenError:
        error, _ = error_response(f"Invalid token. Please log in again. {request.args.get('jwt')}")
        connection_manager.notify(event_name, data=error)
        return None

    # Validate the user identity
    if not current_user:
        error, _ = error_response("Kindly sign in to enjoy a seamless chat experience.")
        connection_manager.notify(event_name, data=error)
        return None

    return current_user

