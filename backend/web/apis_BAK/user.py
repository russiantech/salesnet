from datetime import datetime
from os import getenv
# oauth implimentations
import secrets, requests
from requests.exceptions import ConnectionError, Timeout, RequestException
from urllib.parse import urlencode

from flask import abort, current_app, session, jsonify, render_template, url_for, flash, redirect, request, Blueprint
from flask_login import login_user, current_user, logout_user, login_required

import sqlalchemy as sa, traceback
from jsonschema import validate, ValidationError

from web.models import (
    db, bcrypt, Transaction, User, Notification, AccountDetail
)

from web.extensions import csrf

from web.apis.utils.valid_schemas import (
    signin_schema, signup_schema, request_schema, update_user_schema, reset_password_schema, 
    reset_password_email_schema, validTokenSchema
)

from web.apis.utils.helpers import ( 
    error_response, success_response, user_ip, handle_verify_email, handle_reset_password
    )

from sqlalchemy.orm import joinedload

from web.apis.utils.uploader import uploader
from web.apis.utils.email import email as emailer
from web.apis.utils.decorators import admin_or_current_user, role_required
from web.apis.utils.oauth_providers import oauth2providers

user_bp = Blueprint('user', __name__)

def hash_txt(txt):
    return bcrypt.generate_password_hash(txt).decode('utf-8') # use .encode('utf-8') to decode this

@user_bp.route("/sign-in", methods=['POST'])
@csrf.exempt
def signin():
    try:

        if  current_user.is_authenticated:
            data = {"redirect": url_for('main.index')}
            return success_response("Already authenticated", data=data)

        """ if not current_user.is_anonymous:
            return jsonify({"success": False, "message": "Already authenticated", "redirect": url_for('main.index')}) """

        # Check if the request content type is application/json
        if request.content_type != 'application/json':
            return jsonify({"success": False, "error": "Content-Type must be application/json"})

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

        if user and bcrypt.check_password_hash(user.password, data['password']):
            user.online = True
            user.last_seen = datetime.utcnow()
            user.ip = user_ip()
            db.session.commit()
            login_user(user, remember=data.get('remember', False))
            data = {"redirect": url_for('main.index')}
            return success_response("Authentication Successful", data=data)
        else:
            return error_response("Invalid authentications")

    except Exception as e:
        return error_response(str(e))

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

@user_bp.route("/sign-up", methods=['POST'])
@csrf.exempt
def signup():
    
    if  current_user.is_authenticated:
        data = {"redirect": url_for('main.index')}
        return success_response("Already authenticated", data=data)

    if request.content_type != 'application/json':
        return error_response("Content-Type must be application/json")

    data = request.get_json()

    # Log received data for debugging purposes
    print(f"Received data: {data}")

    # Validate the data against the schema
    try:
        validate(instance=data, schema=signup_schema)
    except ValidationError as e:
        return error_response(e.message)

    # Ensure that no fields are empty
    if not all(data.get(key) for key in ('username', 'phone', 'email', 'password')):
        return error_response("Required field is empty")

    # Perform checks on the data
    if db.session.scalar(sa.select(User).where(User.username == data['username'])):
        return error_response("Please use a different username.")

    if db.session.scalar(sa.select(User).where(User.email == data['email'])):
        return error_response("Please use a different email address.")

    if db.session.scalar(sa.select(User).where(User.phone == data['phone'])):
        return error_response("Please use a different phone number.")

    try:
        # Create and save the new user
        user = User(
            username=data['username'],
            email=data['email'],
            phone=data['phone'],
            # password=bcrypt.generate_password_hash(data['password']),
            ip=user_ip()
        )
        user.set_password(data['password'])
        db.session.add(user)
        db.session.commit()

        # Send verification email
        emailer.verify_email(user)

        data = {"redirect": url_for('auth.signin')}
        return success_response("Registration Successful, you're now able to login")

    except Exception as e:
        print(traceback.print_exc())
        db.session.rollback()
        return error_response(str(e))

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

# Unified route to handle all token-related actions (reset password, email verification, etc.)
@user_bp.route("/process-token/<token>/<email>", methods=['GET', 'POST'])
@user_bp.route("/reset-password", methods=['GET', 'POST'])
def process_token(token: str, email: str):
    try:
        # If the user is already logged in, redirect them to the main page
        if current_user.is_authenticated:
            return redirect(url_for('main.index'))
        
        # Ensure token and email are provided
        if not token or not email:
            return error_response('Invalid request. Token or email missing.')

        # Validate incoming data against JSON schema (for schema defined in my utils )
        data = {
            'token': token,
            'email': email
        }

        try:
            validate(instance=data, schema=validTokenSchema)
        except ValidationError as e:
            return error_response(f"Validation error: {e.message}")

        # Find the user by email
        user = User.query.filter_by(email=email).first()
        if not user:
            return error_response('User not found')

        # Validate the token
        user = User.check_token(user, token)
        if not user:
            return error_response('Invalid or expired token')

        # Handle token types (email verification, password reset, etc.)
        if user.token_type == 'verify_email':
            return handle_verify_email(user)
        
        elif user.token_type == 'reset_password':
            return handle_reset_password(user)

        # If token type is unknown, return an error
        return error_response('Unexpected error with token type.')
    
    except Exception as e:
        return error_response(str(e))

# ===============================================================

@user_bp.route('/<string:username>/update_user', methods=['PUT'])
@csrf.exempt
@admin_or_current_user()
def update(username):
    try:
        
        if not current_user.is_admin and current_user.username != username:
            return jsonify({"success": False, "error": "Unauthorized"})

        if request.content_type == 'application/json':
            data = request.get_json()

        elif 'multipart/form-data' in request.content_type:
            data = request.form.to_dict()

        else:
            return jsonify({"success": False, "message": "Content-Type must be application/json or multipart/form-data"})

        if not data:
            return jsonify({"success": False, "message": "No data received"})
        
        # Validate the data against the schema
        try:
            validate(instance=data, schema=update_user_schema)

        except ValidationError as e:
            return jsonify({"success": False, "error": str(e)})
            #return jsonify({"success": False, "error": e.message})

        # Check for uniqueness of phone, email, and username
        if db.session.scalar(sa.select(User).where(User.phone == data.get('phone'), User.username != username)):
            # print(data.get('phone'), User.phone)
            return jsonify({"success": False, "error": "The phone number is already in use. Please use a different phone number."}), 200

        if db.session.scalar(sa.select(User).where(User.email == data.get('email'), User.username != username)):
            return jsonify({"success": False, "error": "The email address is already in use. Please use a different email address."}), 200

        if db.session.scalar(sa.select(User).where(User.username == data.get('username'), User.username != username)):
            return jsonify({"success": False, "error": "The username is already in use. Please use a different username."}), 200

        user = User.query.filter_by(username=username).first_or_404()

        # Update user attributes based on JSON data
        if 'password' in data:
            user.password = bcrypt.generate_password_hash(data['password'])

        if 'withdrawal_password' in data:
            user.withdrawal_password = bcrypt.generate_password_hash(data['withdrawal_password'])

        if 'image' in request.files:
            image_filename = uploader(request.files['image'], './static/img/avatars/', current_user.username)
            user.image = image_filename

        user.name = data.get('name', user.name)
        user.admin = data.get('admin', user.admin)
        user.name = data.get('name', user.name)
        user.email = data.get('email', user.email)
        user.phone = data.get('phone', user.phone)
        user.membership = data.get('membership', user.membership)
        user.balance = data.get('balance', user.balance)
        user.gender = data.get('gender', user.gender)
        user.about = data.get('about', user.about)
        user.verified = data.get('verified', user.verified)
        user.ip = user_ip()

        # Update account details
        # Ensure account_details is initialized
        if user.account_details is None:
            user.account_details = []

        # Update account details
        account_details_data = data.get('account_details', {})

        if user.account_details:
            # Update the existing account detail (assuming there's only one per user)
            account_detail = user.account_details[0]
            for field, value in account_details_data.items():
                if value is not None:
                    setattr(account_detail, field, value)
        else:
            # Insert new if none exists
            account_detail = AccountDetail(
                user_id=user.id,
                **account_details_data
            )
            user.account_details.append(account_detail)
            db.session.add(account_detail)

        db.session.commit()
        
       # Ensure account_details is initialized
        if user.account_details is None:
            user.account_details = []

        # Update account details
        if user.account_details:
            # Update the first existing account detail (assuming there's only one per user)
            account_details_data = {
                'user_id': data.get('user_id', current_user.id),
                'account_name': data.get('account_name'),
                'account_phone': data.get('account_phone'),
                'exchange': data.get('exchange'),
                'exchange_address': data.get('exchange_address'),
                'cash_app_email': data.get('cash_app_email'),
                'cash_app_username': data.get('cash_app_username'),
                'paypal_phone': data.get('paypal_phone'),
                'paypal_email': data.get('paypal_email')
            }

            account_detail = user.account_details[0]

            for field, value in account_details_data.items():
                if value is not None:
                    setattr(account_detail, field, value)
        else:
            # Insert new if none exists
            account_detail = AccountDetail(
                user_id=data.get('user_id', current_user.id),
                account_name=data.get('account_name'),
                account_phone=data.get('account_phone'),
                exchange=data.get('exchange'),
                exchange_address=data.get('exchange_address'),
                cash_app_email=data.get('cash_app_email'),
                cash_app_username=data.get('cash_app_username'),
                paypal_phone=data.get('paypal_phone'),
                paypal_email=data.get('paypal_email')
            )

            user.account_details.append(account_detail)
            db.session.add(account_detail)

        db.session.commit()
        
        
        return jsonify({"success": True, "message": "User updated successfully."}), 200

    except Exception as e:
        print(e)
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)})

@user_bp.route('/<string:username>/get_user_x', methods=['GET'])
@csrf.exempt
@admin_or_current_user()
def get_user_x(username):
    try:
        # Fetch the user by username and eagerly load account details
        user = db.session.query(User).options(joinedload(User.account_details)).filter_by(username=username).first_or_404()

        # Prepare user details dictionary
        user_details = {
            "username": user.username,
            "user_id": user.user_id,
            "name": user.name,
            "email": user.email,
            "phone": user.phone,
            "membership": user.membership,
            "balance": user.balance,
            "gender": user.gender,
            "about": user.about,
            "verified": user.verified,
            "ip": user.ip,
            "admin": user.admin,
            "image": user.image,
            "password": "+ + + + +",
            "withdrawal_password": "+ + + + +",
            "refcode": user.refcode,
            "uuid": user.user_id,
            "created": user.created.strftime('%Y-%m-%d %H:%M:%S') if user.created else None,
            "account_details": []
        }

        # Function to convert account details to dictionary
        def account_detail_to_dict(account_detail):
            return {
                "account_type": account_detail.account_type.name if account_detail.account_type else None,
                "exchange": account_detail.exchange,
                "exchange_address": account_detail.exchange_address,
                "bank_account": account_detail.bank_account,
                "short_code": account_detail.short_code,
                "link": account_detail.link,
                "account_name": account_detail.account_name,
                "account_phone": account_detail.account_phone,
                "cash_app_email": account_detail.cash_app_email,
                "cash_app_username": account_detail.cash_app_username,
                "paypal_phone": account_detail.paypal_phone,
                "paypal_email": account_detail.paypal_email,
                "deleted": account_detail.deleted,
                "created": account_detail.created.strftime('%Y-%m-%d %H:%M:%S') if account_detail.created else None,
                "updated": account_detail.updated.strftime('%Y-%m-%d %H:%M:%S') if account_detail.updated else None
            }

        # Update user details with account details
        if user.account_details:
            for detail in user.account_details:
                user_details["account_details"].append(account_detail_to_dict(detail))

        # Return the user details as a JSON response
        return jsonify({"success": True, "user": user_details}), 200

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@user_bp.route("/signout")
@login_required
def signout():
    logout_user()
    current_user.online = False
    db.session.commit()
    data={"redirect": url_for('showcase.showcase')}
    return success_response("Logout successful", data=data)

#this route-initializes auth
@user_bp.route('/authorize/<provider>')
def oauth2_authorize(provider):
    if not current_user.is_anonymous:
        return redirect(url_for('auth.update', username=current_user.username))

    provider_data = oauth2providers.get(provider)
    if provider_data is None:
        abort(404)

    # generate a random string for the state parameter
    session['oauth2_state'] = secrets.token_urlsafe(16)

    # create a query string with all the OAuth2 parameters
    qs = urlencode({
        'client_id': provider_data['client_id'],
        'redirect_uri': url_for('auth.oauth2_callback', provider=provider, _external=True),
        'response_type': 'code',
        'scope': ' '.join(provider_data['scopes']),
        'state': session['oauth2_state'],
    })

    data={"redirect": provider_data['authorize_url'] + '?' + qs}
    # redirect the user to the OAuth2 provider authorization URL
    return success_response("Redirecting", data=data)
    # return redirect(provider_data['authorize_url'] + '?' + qs)

@user_bp.route('/callback/<provider>')
def oauth2_callback(provider):
    if not current_user.is_anonymous:
        return redirect(url_for('main.index'))

    provider_data = oauth2providers.get(provider)
    if provider_data is None:
        abort(404)

    # if there was an authentication error, flash the error messages and exit
    if 'error' in request.args:
        for k, v in request.args.items():
            if k.startswith('error'):
                flash(f'{k}: {v}')
        return redirect(url_for('main.index'))

    # make sure that the state parameter matches the one we created in the
    # authorization request
    if request.args['state'] != session.get('oauth2_state'):
        abort(401)

    # make sure that the authorization code is present
    if 'code' not in request.args:
        abort(401)

    # exchange the authorization code for an access token
    response = requests.post(provider_data['token_url'], data={
        'client_id': provider_data['client_id'],
        'client_secret': provider_data['client_secret'],
        'code': request.args['code'],
        'grant_type': 'authorization_code',
        'redirect_uri': url_for('auth.oauth2_callback', provider=provider,
                                _external=True),
    }, headers={'Accept': 'application/json'})

    if response.status_code != 200:
        abort(401)
    oauth2_token = response.json().get('access_token')
    if not oauth2_token:
        abort(401)

    # use the access token to get the user's email address
    response = requests.get(provider_data['userinfo']['url'], headers={
        'Authorization': 'Bearer ' + oauth2_token,
        'Accept': 'application/json',
    })
    if response.status_code != 200:
        abort(401)
    email = provider_data['userinfo']['email'](response.json())

    # find or create the user in the database
    user = db.session.scalar(db.select(User).where(User.email == email))
    if user is None:
        user = User(email=email, username=email.split('@')[0], password=hash_txt(secrets.token_urlsafe(5)), src=provider)
        db.session.add(user)
        db.session.commit()

    # log the user in
    login_user(user)
    return redirect(url_for('main.index'))

@user_bp.route('/fetch_notifications', methods=['GET'])
@login_required
def fetch_notifications():
    notifications = Notification.query.filter_by(
        user_id=current_user.id, is_read=False, deleted=False
        ).order_by(Notification.created_at.desc()).all()
    notifications_list = [{
        'id': notification.id,
        'message': notification.message,
        'is_read': notification.is_read,
        'file_path': notification.file_path,
        'created_at': notification.created_at.strftime('%a, %b %d %I:%M %p')
    } for notification in notifications]

    return jsonify({"notifications": notifications_list}), 200

@user_bp.route('/mark_as_read/<int:notification_id>', methods=['PUT'])
@role_required('*')
@csrf.exempt
def mark_notification_as_read(notification_id):
    try:
        notification = Notification.query.get(notification_id)
        if notification:
            notification.is_read = True
            db.session.commit()
            return jsonify({'success': True}), 200
        else:
            return jsonify({'success': False, 'error': 'Notification not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@user_bp.route('/impersonate', methods=['POST'])
@login_required
# @role_required('admin') //this will cause issues/undefined. better do it under the route
@csrf.exempt
def impersonate():
    try:
        
        if not current_user.is_admin() and not "original_user_id" in session:
            return jsonify({'success': False, 'error': "Admin required"})
        
        data = request.get_json()
        
        action = data.get('action')
        user_id = data.get('user_id')
        
        if action == "impersonate":
            user = User.query.get(user_id)
            if user:
                session['original_user_id'] = current_user.id
                login_user(user)
                
                return jsonify({'success': True, 'message': f'You are now impersonating {user.username}'}), 200
            else:
                return jsonify({'success': False, 'error': "User not found"})

        elif action == "revert":
            original_user_id = session.pop('original_user_id', None)
            if original_user_id:
                original_user = User.query.get(original_user_id)
                if original_user:
                    login_user(original_user)
                    return jsonify({'success': True, 'message': f'You are now back as {original_user.username}'}), 200
                return jsonify({'success': False, 'error': "original user not found"})
            return jsonify({'success': False, 'error': "Failed to revert to original user, invalid user-id"})
        
        return jsonify({'success': False, 'error': "Invalid action"})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})