from datetime import datetime, timedelta, timezone
import traceback
from flask import request
from flask_jwt_extended import create_access_token, create_refresh_token, decode_token
from jwt import ExpiredSignatureError
from sqlalchemy import func, or_
from werkzeug.security import generate_password_hash, check_password_hash
from web.apis.utils.serializers import error_response
from web.extensions import db, jwt
from web.apis.models.roles import users_roles
# from web.apis.models.products import products_users
from web.apis.models.pages import users_pages
# from web.apis.models.chats import user_group

products_users = \
    db.Table(
        "products_users",
        db.Column("user_id", db.Integer, db.ForeignKey("users.id")),
        db.Column("product_id", db.Integer, db.ForeignKey("products.id"))
        )
    
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(300))
    avatar = db.Column(db.String(300))
    username = db.Column(db.String(64), index=True, unique=True, nullable=False)
    email = db.Column(db.String(120), index=True, unique=True, nullable=False)
    valid_email = db.Column(db.Boolean(), index=True, nullable=False, default=False)
    phone = db.Column(db.String(120), index=True, unique=True)
    password = db.Column(db.String(512), nullable=False)
    about_me = db.Column(db.String(300))
    is_guest = db.Column(db.Boolean, default=False)
    oauth_providers = db.Column(db.String(300)) # google, github, email etc.
    ip = db.Column(db.String(50), nullable=True)
    last_seen = db.Column(db.DateTime, nullable=True)
    online_status = db.Column(db.Boolean, default=False)
    is_deleted = db.Column(db.Boolean(), nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=func.now())
    updated_at = db.Column(db.DateTime, nullable=False, default=func.now(), onupdate=func.now())
    
    # comments = db.relationship('Comment', foreign_keys='Comment.user_id', back_populates='user', lazy='dynamic')
    comments = db.relationship(
        'Comment',
        foreign_keys='Comment.user_id',
        back_populates='user',
        lazy='dynamic', 
        cascade='all, delete-orphan',  # SQLAlchemy cascades
        passive_deletes=True           # Enable database-level ON DELETE CASCADE
    )
    roles = db.relationship('Role', secondary=users_roles, back_populates='users')
    
    chats = db.relationship('Chat', back_populates='users')
    groups = db.relationship('Group', secondary='user_group', back_populates='users')
    # chat_rooms = db.relationship('ChatRoom', secondary='user_chat_room', back_populates='users')
    
    favorites = db.relationship('Favorite', back_populates='users')
    baskets = db.relationship('Basket', back_populates='users')
    pages = db.relationship('Page', secondary=users_pages, lazy='dynamic', back_populates='users')
    products = db.relationship('Product', secondary=products_users, lazy='dynamic', back_populates='users')
    # transactions = db.relationship('Transaction', foreign_keys='Comment.user_id', back_populates='user', lazy='dynamic')
    transactions = db.relationship('Transaction', back_populates='user', lazy='dynamic')
    
    @staticmethod
    def get_user(username: str):
        """
        Static method to fetch a user from the database by username or user ID or user email.
        
        Args:
            username (str): The username or user ID or user email to search for.
        
        Returns:
            User: The user object if found, otherwise None.
        
        Raises:
            ValueError: If the username is empty.
        """
        if not username:
            raise ValueError("Username cannot be empty")
        
        # Attempt to fetch the user by either username or user ID or email
        user = db.session.query(User).filter(or_(User.username == username, User.id == username, User.email == username)).first()
        
        return user

    def set_password(self, password: str) -> None:
        """Hashes the password using bcrypt/scrypt and stores it."""
        if not password:
            raise ValueError("Password cannot be empty")
        self.password = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Checks the hashed password using bcrypt."""
        if self.password is None:
            # return False
            raise ValueError(f"Password not set for this user [{self.username}].")
        return check_password_hash(self.password, password)

    def is_admin(self):
        return 'admin' in [r.name for r in self.roles]

    def is_not_admin(self):
        return not self.is_admin()

    def __repr__(self):
        return '<User {}>'.format(self.username)

    def get_roles(self):
        return [ r.name for r in self.roles ]

    # def make_token(self, token_type: str = "verify_email") -> str:
    #     """
    #     Generate a JWT token for the specified token type (e.g., reset_password, verify_email).
    #     The token will expire in 1 hour.
    #     """
    #     try:
    #         # Prepare the additional claims (user summary data)
    #         additional_claims = self.get_summary(include_roles=True)
    #         additional_claims["token_type"] = token_type
    #         additional_claims["exp"] = datetime.now(timezone.utc) + timedelta(hours=1) # Token expires in 1 hour if necessary

    #         # Pass the user Email as the identity and user summary data as additional claims
    #         additional_claims['sub'] = str(self.email)  # Ensure 'sub' is a string

    #         # Create a token using flask_jwt_extended's create_access_token
    #         token = create_access_token(identity=str(self.email), additional_claims=additional_claims)
            
    #         return token

    #     except Exception:
    #         traceback.print_exc()
    #         return None  # Return None in case of any error

    from datetime import datetime, timedelta, timezone
    from flask_jwt_extended import create_access_token, create_refresh_token

    def make_token(self, token_type: str = "access") -> str:
        """
        Generate a JWT token for the specified token type (e.g., access or refresh).
        - The access token expires in 15 minutes.
        - The refresh token expires in 30 days.

        Args:
            token_type (str): The type of token to create ("access" or "refresh").
        
        Returns:
            str: The generated JWT token.
        """
        try:
            # Prepare the additional claims (user summary data)
            additional_claims = self.get_summary(include_roles=True)

            # Add the token type to the claims
            additional_claims["token_type"] = token_type

            # Set expiration based on token type
            if token_type == "access":
                expiration_time = timedelta(minutes=15)  # Access token expires in 15 minutes
            elif token_type == "refresh":
                expiration_time = timedelta(days=30)  # Refresh token expires in 30 days
            else:
                raise ValueError(f"Invalid token type: {token_type}")

            # Add expiration claim to additional claims
            additional_claims["exp"] = datetime.now(timezone.utc) + expiration_time

            # Use the user's email as the 'sub' claim (subject)
            additional_claims['sub'] = str(self.email)  # Ensure 'sub' is a string

            if token_type == "access":
                # Create the access token with the provided claims
                token = create_access_token(identity=str(self.email), additional_claims=additional_claims)
            elif token_type == "refresh":
                # Create the refresh token with a longer expiration time
                token = create_refresh_token(identity=str(self.email), additional_claims=additional_claims)
            
            return token

        except Exception as e:
            # Log the exception (optional)
            traceback.print_exc()
            return None  # Return None in case of any error

    @staticmethod
    def check_token(token: str) -> dict:
        """
            Verifies and decodes a JWT token using the Flask app's SECRET_KEY.
            Returns the decoded token if valid, or an error message if invalid or expired.
        """
        try:
            
            # Decode the token using the app's SECRET_KEY (from flask_jwt_extended)
            token = decode_token(token)
            print("decoded-token - ", token)
            return token

        except Exception:
            traceback.print_exc()
            return None

    def update_last_seen(self, user_id):
        user = self.query.get(user_id)
        if user:
            self.last_seen = func.now()
            db.session.commit()
        
    def get_summary(self, include_products=False, include_roles=False, include_pages=False):
        data = {
            'id': self.id,
            'name': self.name,
            'username': self.username,
            'email': self.email,
            'phone': self.phone,
            'about_me': self.about_me,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
        }
      
        if include_pages:
            data['pages'] = [ page.get_summary() for page in self.pages ]
            
        if include_roles:
            data['roles'] = self.get_roles()
            
        if include_products:
            # data['products'] = self.products.get_summary() // causees AttributeError: 'AppenderQuery' object has no attribute 'get_summary'
            data['products'] = [ product.get_summary() for product in self.products]
            # data['products'] = [
            #     {
            #         'id': product.id,
            #         'name': product.name,
            #     } for product in self.products
            # ]

        return data

from web.apis.utils.chats import connection_manager

# Register a callback function that takes whatever object is passed in as the
# identity when creating JWTs and converts it to a JSON serializable format.
@jwt.user_identity_loader
def user_identity_lookup(user):
    try:
        user = user.get('email', user['id'])
        return user.get('email', user)
    except Exception:
        return None

# Register a callback function that loads a user from your database whenever
# a protected route is accessed. This should return any python object on a
# successful lookup, or None if the lookup failed for any reason (for example
# if the user has been deleted from the database).
@jwt.user_lookup_loader
def user_lookup_callback(_jwt_header, jwt_data):
    identity = jwt_data["sub"]
    # return User.query.filter_by(or_(email=identity, id=identity)).one_or_none()
    return User.query.filter(
        or_(User.email == identity, User.id == identity)
    ).one_or_none()

# Callback function to check if a JWT exists in the database blocklist
from web.extensions import redis as r
@jwt.token_in_blocklist_loader
def check_if_token_revoked(jwt_header, jwt_payload: dict) -> bool:
    jti = jwt_payload["jti"]
    # token = db.session.query(TokenBlocklist.id).filter_by(jti=jti).scalar() // db-way-of-doing-it
    # return token is not None  // db-way-of-doing-it
    return r.sismember("blacklist", jti) #  // redis-way-of-doing-it

# 
# Custom error response for missing token
@jwt.unauthorized_loader
def unauthorized_callback(error):
    if 'socketio' in request.environ:
        # Handle WebSocket specific logic if needed
        connection_manager.notify('socket_response', data=error)
    return error_response(f'valid token required - {error}', status_code=401)

# Custom error response for expired token
@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    return error_response('token has expired', status_code=401)

# import requests
# from flask import request, jsonify, current_app, url_for

# Custom error response for expired token and refreshing. FOR NOW< LET FRONTEND HANDLE REQUESTING NEW ACCESS TOKENS/.
# @jwt.expired_token_loader
# def expired_token_callback(jwt_header, jwt_payload):
#     try:
#         # Retrieve the refresh token from the request (cookies or request body)
#         refresh_token = request.cookies.get('refresh_token_cookie') or request.json.get('refresh_token')

#         if not refresh_token:
#             return error_response('Refresh token is missing, please log in again.', 401)

#         # Prepare the payload for the refresh token request
#         refresh_token_data = {
#             'refresh_token': refresh_token
#         }

#         # Make an internal request to /users/refresh-token to get a new access token
#         refresh_token_url = url_for('user_api.refresh_token', _external=True)  # Ensure the correct external URL

#         # Make the request to the refresh token endpoint
#         response = requests.post(refresh_token_url, json=refresh_token_data)

#         if response.status_code == 200:
#             # Successfully refreshed, return the response directly to the client
#             return response.json(), 200

#         else:
#             # Handle failure case: refresh token is invalid, etc.
#             return error_response('Failed to refresh token, please log in again.', 401)

#     except Exception as e:
#         # In case of any errors during the process
#         return error_response(f"Error refreshing token: {str(e)}")


# Custom error response for fresh token requirement
@jwt.needs_fresh_token_loader
def fresh_token_required_response():
    return error_response('fresh token required', status_code=401)

@jwt.invalid_token_loader
def invalid_token_callback(error):
    return error_response('Invalid token. Signature verification failed.', status_code=401)