from datetime import datetime
from flask import abort, session, jsonify, render_template, url_for, flash, redirect, request, Blueprint
from flask_login import login_user, current_user, logout_user, login_required
from sqlalchemy import or_
#from utils.time_ago import timeAgo
from web.models import db, bcrypt
from web.models import Role, User

from web.apis.utils import email
from web.apis.utils.helpers import user_ip
from web.auth.forms import (SignupForm, SigninForm, UpdateMeForm, ForgotForm, ResetForm)
from web.utils.decorators import admin_or_current_user
from web.utils.providers import oauth2providers

from web.utils.db_session_management import db_session_management

#oauth implimentations
import secrets, requests
from urllib.parse import urlencode

auth = Blueprint('auth', __name__)

def hash_txt(txt):
    return bcrypt.generate_password_hash(txt).decode('utf-8') #use .encode('utf-8') to decode this

@auth.route("/signup", methods=['GET', 'POST'])
@db_session_management
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = SignupForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data, 
            email=form.email.data, 
            phone=form.phone.data, 
            password=hash_txt(form.password.data), 
            ip = user_ip()
            )
        db.session.add(user)
        db.session.commit()
        email.verify_email(user) if user else flash('Undefined User.', 'info')
        flash('Your Account Has Been Created! You Are Now Able To Log In', 'success')
        return redirect(url_for('auth.signin'))
    return render_template('auth/signup.html', title='Sign-up', form=form)

#this route-initializes auth
@auth.route('/authorize/<provider>')
@db_session_management
def oauth2_authorize(provider):
    if not current_user.is_anonymous:
        return redirect(url_for('main.index'))

    provider_data = oauth2providers.get(provider)
    if provider_data is None:
        abort(404)

    #return f"{provider_data}"

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

    # redirect the user to the OAuth2 provider authorization URL
    return redirect(provider_data['authorize_url'] + '?' + qs)

@auth.route('/callback/<provider>')
@db_session_management
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

@auth.route("/signin", methods=['GET', 'POST'])
@db_session_management
def signin():

    referrer = request.referrer
    if not current_user.is_anonymous:
        return redirect(url_for('main.index'))

    form = SigninForm()
    if form.validate_on_submit():
        user = User.query.filter( or_( User.email==form.signin.data, User.phone==form.signin.data, User.username==form.signin.data) ).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            user.online = True
            user.last_seen = datetime.utcnow()
            user.ip = user_ip()
            db.session.commit()
            login_user(user, remember=form.remember.data)
            #login_user(user)
            next_page = request.args.get('next')
            #return f"{current_user, form.remember.data}"
            return redirect(next_page or url_for('main.index'))
        else: 
            flash('Invalid Login Details. Try Again', 'danger')
            return redirect(referrer)
            #return f"Authentication failed. Reach out to admin regarding this"
    return render_template('auth/signin.html', title='Sign In', form=form)

@auth.route("/signout")
@login_required
@db_session_management
def signout():
    logout_user()
    current_user.online = False
    db.session.commit()
    return redirect(url_for('showcase.showcase'))

@auth.route("/<string:usrname>/update", methods=['GET', 'POST'])
@login_required
@admin_or_current_user()
@db_session_management
def update(usrname):
    usr = User.query.filter(User.username==usrname).first_or_404()
    form = UpdateMeForm()
    if usr.role:
        # Get the user's current role
        current_role = [ (r.id, r.type) for r in usr.role] or [('0', 'Not Granted')]
        other_roles = Role.query.filter( ~Role.id.in_(current_role[0]) if current_role[0] else None ).all() 

        choices = [ ( x[0], x[1]) for x in current_role] or [('0', 'nothing')] #if current_role else [ '', 'Nothing']
        choices.extend( (role.id, role.type) for role in other_roles) if current_user.is_admin() else None
        # Set choices for the form's role field
        form.role.choices = choices
    else:
        pass
    
    handles = usr.socials # Retrieve existing dictionary or create a new one

    if form.validate_on_submit():
        usr.name = form.name.data
        usr.username = form.username.data
        usr.email = form.email.data
        usr.phone = form.phone.data
        usr.gender = form.gender.data
        usr.acct_no = form.acct_no.data
        usr.bank = form.bank.data
        usr.city = form.city.data
        usr.about = form.about.data
        usr.password = hash_txt(form.password.data) if form.password.data else usr.password
        usr.cate = form.cate.data or 'user'
        new_role_ids = [form.role.data]  # Assuming the form data provides a list of role IDs
        new_roles = Role.query.filter(Role.id.in_(new_role_ids) ).all()
        usr.role = new_roles
            
        social_handles = \
            {'facebook': form.facebook.data, 'twitter' : form.twitter.data, 'instagram' :form.instagram.data, 'linkedin' :form.linkedin.data}
        #usr.socials = str(social_handles)
        usr.socials = social_handles

        db.session.commit()
        db.session.flush()
        flash('Your Account Has Been Updated!', 'success')
        return jsonify({ 
            'response': f'Success..!!, You"ve Updated This Account </b>..',
            'flash':'alert-success',
            'link': f''})
    
    elif request.method == 'GET':
        if handles:
            form.twitter.data = handles['twitter'] 
            form.facebook.data = handles['facebook'] 
            form.instagram.data = handles['instagram'] 
            form.linkedin.data = handles['linkedin'] 
        #form.socials.data = usr.socials
        form.photo.data = usr.photo or '0.svg'
        form.name.data = usr.name
        form.username.data = usr.username
        form.email.data = usr.email
        form.phone.data = usr.phone
        form.gender.data = usr.gender
        form.acct_no.data = usr.acct_no
        form.city.data = usr.city
        form.about.data = usr.about
        form.bank.data = usr.bank

    if request.method == "POST" and not form.validate_on_submit():
    #if not form.validate_on_submit():
        return jsonify({ 
            'response': f'invalid .. { form.errors}  </b>..',
            'flash':'alert-warning',
            'link': f''})
    context = {
                'form' : form,
                'user': usr,
                'brand': {'name':'IMS'},
            }
    return render_template('auth/update.html',  **context)

@auth.route("/forgot", methods=['GET', 'POST'])
@db_session_management
def forgot():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = ForgotForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        email.reset_email(user) if user else flash('Undefined User.', 'info')
        flash('An email has been sent with instructions to reset your password.', 'info')
        return redirect(url_for('auth.signin'))
    elif request.method == 'GET':
        form.email.data = request.args.get('e')
    return render_template('auth/forgot.html', form=form)

#->for unverified-users, notice use of 'POST' instead of 'post' before it works
@auth.route("/unverified", methods=['post', 'get'])
@login_required
@db_session_management
def unverified():
    if request.method == 'POST':
        email.verify_email(current_user)
        flash('Verication Emails Sent Again, Check You Mail Box', 'info')
    return render_template('auth/unverified.html')

#->for both verify/reset tokens
@auth.route("/confirm/<token>", methods=['GET', 'POST'])
@db_session_management
def confirm(token):
    #print(current_user.generate_token(type='verify'))
    if current_user.is_authenticated:
        #print(current_user.generate_token(type='verify')) #generate-token
        return redirect(url_for('main.index'))
    
    conf = User.verify_token(token) #verify

    if not conf:
        flash('That is an invalid or expired token', 'warning')
        return redirect(url_for('auth.signin'))
    
    user = conf[0] 
    type = conf[1]

    if not user :
        flash('Invalid/Expired Token', 'warning')
        return redirect(url_for('main.index'))
    
    if type == 'verify' and user.verified == True:
        flash(f'Weldone {user.username}, you have done this before now', 'success')
        return redirect(url_for('auth.signin', _external=True))

    if type == 'verify' and user.verified == False:
        user.verified = True
        db.session.commit()
        flash(f'Weldone {user.username}, Your Email Address is Confirmed, Continue Here', 'success')
        return redirect(url_for('auth.signin', _external=True))

    if type == 'reset':
        form = ResetForm() 
        if form.validate_on_submit():
            hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
            user.password = hashed_password
            db.session.commit()
            flash('Your password has been updated! Continue', 'success')
            return redirect(url_for('auth.signin'))
        return render_template('auth/reset.html', user=user, form=form)