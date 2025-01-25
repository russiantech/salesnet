
# oauth implimentations
import secrets, requests, sqlalchemy as sa, traceback
from requests.exceptions import ConnectionError, Timeout, RequestException
from urllib.parse import urlencode
from datetime import datetime, timedelta, timezone

# from flask_login import login_user, current_user, logout_user, login_required

# from flask_jwt_extended import jwt_optional, get_jwt_claims // deprecated
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, get_jwt, current_user  # Instead of get_jwt_claims
from jsonschema import validate, ValidationError
from flask import (
    abort, current_app, session, jsonify, render_template, 
    url_for, flash, redirect, request
)

from web.extensions import db, csrf, bcrypt, limiter
from web.apis.utils.helpers import user_ip
from web.apis.models.roles import Role
from web.apis.models.users import User
from web.apis.utils.serializers import (
    PageSerializer, error_response, success_response
)

from web.apis.schemas.user import (
    signin_schema, signup_schema, request_schema, reset_password_email_schema, 
    validTokenSchema, reset_password_schema, update_user_schema
)

from web.apis.utils import email as emailer
from web.apis.utils.oauth_providers import oauth2providers

from web.apis import api_bp as user_bp

# @jwt_optional # deprecated
@jwt_required(optional=True)
def partially_protected():
    # If no JWT is sent in with the request, get_jwt_identity()
    # will return None
    current_user = get_jwt_identity()
    if current_user:
        return jsonify(logged_in_as=current_user), 200
    else:
        return jsonify(loggeed_in_as='anonymous user'), 200


@user_bp.route("/sign-up", methods=['POST'])
@csrf.exempt
@jwt_required(optional=True)
def signup():

    # Check if the user is already authenticated (using JWT token)
    user_identity = get_jwt_identity()  # Attempt to get the current user's identity from the JWT token
    if user_identity:
        return error_response("You are already authenticated. No need to sign up.", data={"redirect": url_for('main.index')})
    
    # Log received data for debugging purposes
    if request.content_type != 'application/json':
        return error_response("Content-Type must be application/json")

    data = request.get_json()
    # print(f"Received data: {data}")

    # Validate the data against the schema
    try:
        validate(instance=data, schema=signup_schema)
    except ValidationError as e:
        return error_response(e.message)

    # Ensure that no fields are empty
    if not all(data.get(key) for key in ('username', 'phone', 'email', 'password')):
        return error_response("Missing required fields ('username', 'phone', 'email', 'password')")

    # Perform checks on the data
    if db.session.scalar(sa.select(User).where(User.username == data['username'])):
        return error_response("Please use a different username.")

    if db.session.scalar(sa.select(User).where(User.email == data['email'])):
        return error_response("Please use a different email address.")

    if db.session.scalar(sa.select(User).where(User.phone == data['phone'])):
        return error_response("Please use a different phone number.")

    role = db.session.query(Role).filter_by(name='user').first()
    
    try:
        # Create and save the new user
        user = User(
            username=data['username'],
            email=data['email'],
            phone=data['phone'],
            roles=[role],
            ip=user_ip()  # Capture the user's IP
        )
        user.set_password(data['password'])  # Use bcrypt or your hashing method
        db.session.add(user)
        db.session.commit()

        # Send verification email
        emailer.verify_email(user)

        # Prepare response data
        # serializer = PageSerializer(items=user, resource_name="user")
        
        # Pass a list containing the user object
        serializer = PageSerializer(items=[user], resource_name="user")
        response_data = serializer.get_data()
        response_data.update({"redirect": url_for('apis.signin')})

        return success_response("sign up successful.", data=response_data)

    except Exception as e:
        # Rollback on error and log
        db.session.rollback()
        print(traceback.print_exc())
        return error_response(str(e))


@user_bp.route("/sign-in", methods=['POST'])
@csrf.exempt
@jwt_required(optional=True)
def signin():
    try:
        # Check if the user is already authenticated (using JWT token)
        user_identity = get_jwt_identity()  # Attempt to get the current user's identity from the JWT token
        if user_identity:
            return success_response("Already authenticated", data={"redirect": url_for('main.index')})

        # Check if the request content type is application/json
        if request.content_type != 'application/json' or not request.json:
            return error_response("Content-Type must be application/json & json payload expected.")

        # Parse JSON data from the request
        data = request.get_json()

        # Ensure that no fields are empty
        if not all(data.get(key) for key in ('username', 'password')):
            return error_response("All fields are required and must not be empty.")

        # Validate the data against the schema
        try:
            validate(instance=data, schema=signin_schema)
        except ValidationError as e:
            return error_response(e.message)

        # Authentication logic
        user = User.query.filter(
            sa.or_(
                User.email == data['username'],
                User.phone == data['username'],
                User.username == data['username']
            )
        ).first()

        # If user exists and password matches
        if user and user.check_password(data['password']):
            
            # user.online = True
            # user.last_seen = func.now()
            # user.ip = user_ip()
            # db.session.commit()

            # Create the JWT token for the authenticated user
            # access_token = create_access_token(identity=user) # saves too many informations about the user in the token, it's more professional though
            # access_token = create_access_token(identity=user.get_summary(include_roles=False)) # > saves only a few info from the get_summary() to the token
            # return success_response("sign-in successful", data={"token":access_token})
            
            # 
            # Prepare the additional claims (user summary data)
            # additional_claims = user.get_summary(include_roles=True)
            # additional_claims["exp"] = datetime.now(timezone.utc) + timedelta(hours=1) # Token expires in 1 hour if necessary

            # # Pass the user Email as the identity and user summary data as additional claims
            # # token = create_access_token(identity=self.email, additional_claims=additional_claims)
            # additional_claims['sub'] = str(user.email)  # Ensure 'sub' is a string

            # Create a token using flask_jwt_extended's create_access_token
            access_token = user.make_token(token_type=None)
    
            # Return success response with user data and token
            data = {
                "redirect": url_for('showcase.index'),
                'token': access_token
            }
            
            return success_response("sign in successful", data=data)
        
        # If authentication failed
        else:
            return error_response("Invalid username or password.")
        
    except Exception as e:
        # Log the exception for debugging
        traceback.print_exc()
        print(f"Error signing in: {e}")
        return error_response(f'Error signing in: {e}', status_code=400)

@user_bp.route("/reset-password", methods=['POST'])
def reset_password():
    try:
        # Redirect authenticated users to the main page
        if current_user.is_authenticated:
            data = {'redirect': url_for('main.index')}
            return success_response('You are already logged in.', data=data)

        # Parse and validate the JSON request payload
        data = request.get_json()
        if not data:
            return error_response('Invalid request: No JSON data provided.', status_code=400)

        try:
            validate(instance=data, schema=reset_password_email_schema)
        except ValidationError as ve:
            return error_response(f'Validation error: {ve.message}', status_code=400)

        # Extract email after validation
        email = data['email']

        # Handle the password reset logic
        user = User.query.filter_by(email=email).first()
        if user:
            emailer.reset_email(user)
            data = {'redirect': url_for('main.index')}
            return success_response('An email has been sent with instructions to reset your password.', data=data)
        else:
            return error_response('No user found with the provided email.', status_code=404)

    except Exception as e:
        # Log the exception for debugging
        print(f"Error in reset_password: {e}")
        return error_response('An internal server error occurred. Please try again later.', status_code=500)

# Requests form route
@user_bp.route('/requests', methods=['POST'])
@csrf.exempt
def make_request():
    try:
        
        data = request.get_json()
        
        name = data.get('name')
        email = data.get('email')
        phone = data.get('phone')
        details = data.get('details')
        concern = data.get('concern')
        budget = int(data.get('budget', 0))

        # Validate email and request content
        if not email or not phone or not details:
            return error_response('Email, Phone & Details  Are Required')

        # return success_response("testing", data=data)
    
        # Validate the data against the schema
        try:
            validate(instance=data, schema=request_schema)
        except ValidationError as e:
            return error_response(e.message)
        
        # Prepare email content for support
        subject = "[Incoming Requests ] from {}".format(email)
        text_body = f"From: {email} (Phone: {phone})\n\nDetails:\n{details}"
        
        context = {
            "name":name,
            "email":email, 
            "phone":phone, 
            "budget":budget, 
            "concern":concern,
            "details":details,
        }
        
        html_body = render_template('email/requests.html', **context)

        # Send email to support team
        emailer.send_email(
            subject=subject,
            # sender=email, // can be omitted if 'DEFAULT_MAIL_SENDER' is configured
            recipients=[current_app.config['MAIL_USERNAME'], "chrisjsmez@gmail.com"],  # The contact email for receiving messages
            text_body=text_body,
            html_body=html_body
        )

        return success_response(f'Your Request has been submitted successfully. Thank you!')
    
    except ConnectionError:
            # print(traceback.print_exc())
            print(traceback.format_exc())
            return error_response("No internet connection. pls check your network and try again.")

    except Timeout:
        # print(traceback.print_exc())
        print(traceback.format_exc())
        return error_response("The request timed out. Please try again later.")

    except RequestException as e:
        print(traceback.print_exc())
        # print(traceback.format_exc())
        return error_response(f"error: {str(e)}")
    
    except Exception as e:
        traceback.format_exc()
        return error_response(str(e))

# ============================HELPERS=============
# Helper function to handle email verification
def handle_verify_email(user):
    try:
        if user.valid_email:
            return success_response(f'Your email address, {user.username}, is already verified.')
        user.valid_email = True
        db.session.commit()
        return success_response(f'Email address confirmed for {user.username}.')
    except Exception as e:
        
        return error_response(f"{e}")

# Helper function to handle password reset
# from flask_expects_json import expects_json
# @expects_json(reset_password_schema)
def handle_reset_password(user):
    try:
        data = request.get_json()
        
        try:
            validate(instance=data, schema=reset_password_schema)
        except ValidationError as e:
            return error_response(f"Validation error: {e.message}")
        
        new_password = data["password"]
        
        user.set_password(new_password)
        db.session.commit()
        
        return success_response(f'Your password has been updated for {user.username}. successfully.')
    
    except ValueError as e:
        return error_response(f"{str(e)}")
    except Exception as e:
        return error_response(f"{str(e)}")
    
# Unified route to handle all token-related actions (reset password, email verification, etc.)
@user_bp.route("/process-token/<token>", methods=['GET', 'POST'])
@user_bp.route("/reset-password", methods=['GET', 'POST'])
@limiter.exempt
@jwt_required(optional=True)
def process_token(token: str = None):
    try:
        # Ensure token and email are provided
        if not token:
            return error_response('Invalid request. Token or email missing.')

        # Validate incoming data against JSON schema
        data = { 'token': token }

        try:
            validate(instance=data, schema=validTokenSchema)
        except ValidationError as e:
            return error_response(f"Token-validation error: {e.message}")

        print("token-data -", data)
        # Validate the token
        valid_token =  User.check_token(data['token'])
        print(valid_token)
        
        if not valid_token:
            return error_response('Invalid or expired token.')

        # Find the user by email
        user = User.query.filter_by(email=valid_token['email']).first()
        
        if not user:
            return error_response(f'User not found with this email address: {valid_token['email']}')
        
        # Handle token types (email verification, password reset, etc.)
        token_type = valid_token["token_type"]
        
        if token_type == 'verify_email':
            return handle_verify_email(user)
        
        elif token_type == 'reset_password':
            return handle_reset_password(user)

        # If token type is unknown, return an error
        return error_response('Unexpected error with token type.')

    except Exception as e:
        traceback.print_exc()
        return error_response(f'An error occurred: {str(e)}')
    

@user_bp.route("/signout")
@jwt_required
def signout():
    # logout_user()
    current_user.online = False
    db.session.commit()
    data={"redirect": url_for('showcase.showcase')}
    return success_response("Logout successful", data=data)

# ==========OAUTH authentications================

# Route to initialize OAuth
@user_bp.route('/authorize/<provider>')
@jwt_required(optional=True)
def oauth2_authorize(provider):
    
    try:
        # Check if the user is already authenticated
        if get_jwt_identity() is not None:
            return success_response(f"already signed-in as {get_jwt_identity()['username']}")

        provider_data = oauth2providers.get(provider)
        if provider_data is None:
            abort(404)

        # Generate a random string for the state parameter
        session['oauth2_state'] = secrets.token_urlsafe(16)

        # Create a query string with all the OAuth2 parameters
        qs = urlencode({
            'client_id': provider_data['client_id'],
            'redirect_uri': url_for('apis.oauth2_callback', provider=provider, _external=True),
            'response_type': 'code',
            'scope': ' '.join(provider_data['scopes']),
            'state': session['oauth2_state'],
        })

        data = {"redirect": provider_data['authorize_url'] + '?' + qs}
        
        return success_response(f"redirecting for {provider} sign in", data=data)
    
    except Exception as e:
        traceback.print_exc()
        return error_response(f"An error occurred: {str(e)}")

# Route to handle the OAuth2 callback
@user_bp.route('/callback/<provider>')
@jwt_required(optional=True)
def oauth2_callback(provider):
    try:
        
        # Check if the user is already authenticated
        if get_jwt_identity() is not None:
            return success_response("already authenticated", data={"redirect": url_for("showcase.index")})

        provider_data = oauth2providers.get(provider)
        if provider_data is None:
            abort(404)

        # Handle authentication errors
        if 'error' in request.args:
            for k, v in request.args.items():
                if k.startswith('error'):
                    # flash(f'{k}: {v}')
                    return error_response(f"error during authentications - {v}")
            return error_response(f"authentication errors occured - {request.args.get('error')}")

        # Validate the state parameter
        if request.args['state'] != session.get('oauth2_state'):
            abort(401)

        # Validate the presence of the authorization code
        if 'code' not in request.args:
            abort(401)

        # Exchange the authorization code for an access token
        response = requests.post(provider_data['token_url'], data={
            'client_id': provider_data['client_id'],
            'client_secret': provider_data['client_secret'],
            'code': request.args['code'],
            'grant_type': 'authorization_code',
            'redirect_uri': url_for('apis.oauth2_callback', provider=provider, _external=True),
        }, headers={'Accept': 'application/json'})

        if response.status_code != 200:
            abort(401)

        oauth2_token = response.json().get('access_token')
        if not oauth2_token:
            abort(401)

        # Use the access token to get the user's email address
        response = requests.get(provider_data['userinfo']['url'], headers={
            'Authorization': 'Bearer ' + oauth2_token,
            'Accept': 'application/json',
        })
        
        if response.status_code != 200:
            abort(401)

        email = provider_data['userinfo']['email'](response.json())

        # Find or create the user in the database
        user = db.session.scalar(db.select(User).where(User.email == email))
        if user is None:
            # user = User(email=email, username=email.split('@')[0], password=hash_txt(secrets.token_urlsafe(5)), src=provider)
            user = User(email=email, username=email.split('@')[0], src=provider)
            user.set_password(secrets.token_urlsafe(5))
            db.session.add(user)
            db.session.commit()

        # Create a JWT token for the user
        # access_token = create_access_token(identity={'username': user.username, 'email': user.email})
        # access_token = create_access_token(identity=user.get_summary())
        # return success_response("sign-in successful", data={"token":access_token})
        
        access_token = create_access_token(identity=user.get_summary(include_roles=True))
        # Return success response with user data and token
        data = {
            "redirect": url_for('showcase.index'),
            'token': access_token
        }
        
        return success_response("sign in successful", data=data)

    except Exception as e:
        traceback.print_exc()
        return error_response(f"An error occurred: {str(e)}")
    
from sqlalchemy import desc, func

@user_bp.route('/users', methods=['GET'])
@user_bp.route('/users/<int:user_id>', methods=['GET'])
# @jwt_required() 
def get_users(user_id=None):
    try:
        # Fetch specific user record by ID
        if user_id is not None:
            user = User.query.get(user_id)
            if not user:
                return error_response("User not found.", status_code=404)
            # return success_response("User fetched successfully.", data=PageSerializer(items=[user], resource_name="user"))
            data=PageSerializer(items=[user], resource_name="user").get_data()
            return success_response("User fetched successfully.", data=data)

        # Pagination parameters
        page = request.args.get('page', 1, type=int)  # Ensure page is an integer
        page_size = request.args.get('page_size', 5, type=int)  # Fixed to 'page_size'

        # Fetch users with pagination
        paginated_users = User.query.order_by(desc(User.created_at)).paginate(page=page, per_page=page_size)
        # paginated_users = User.query.order_by(desc(User.created_at)).offset((page - 1) * page_size).limit(page_size).all()

        response_data = PageSerializer(pagination_obj=paginated_users, resource_name="users")
        # response_data = PageSerializer(items=paginated_users, resource_name="users") // user items param in PageSerializer() when returning a list of item(s)
        data = response_data.get_data()
        
        return success_response("Users fetched successfully", data=data)

    except Exception as e:
        traceback.print_exc()
        return error_response(f"An error occurred: {str(e)}")

@user_bp.route('/users/<int:user_id>', methods=['PUT'])
@jwt_required()
@limiter.exempt
def update_user(user_id):
    try:
        
        user = User.query.get_or_404(user_id)

        data = request.json
        
        # Validate the incoming data against the JSON schema
        try:
            validate(instance=data, schema=update_user_schema)
        except ValidationError as e:
            return error_response(f"Validation error: {e.message}")
        
        user.name = data.get('name', user.name)
        user.username = data.get('username', user.username)
        user.phone = data.get('phone', user.phone)
        user.email = data.get('email', user.email)
        user.about_me = data.get('about_me', user.about_me)
        user.password = user.set_password(data.get('password')) or user.password
        user.avatar = data.get('avatar', user.avatar)
        user.updated_at = func.now()
        
        db.session.commit()
        return success_response("User updated successfully.", data=PageSerializer(items=[user], resource_name="user"))
    except Exception as e:
        return error_response(f"An error occurred: {str(e)}")

@user_bp.route('/users/<int:id>', methods=['DELETE'])
def delete_user(id):
    try:
        user = User.query.get_or_404(id)
        # user.deleted = True
        db.session.delete(user)
        db.session.commit()
        return success_response("User deleted successfully.", status_code=204)
    except Exception as e:
        return error_response(f"An error occurred: {str(e)}")