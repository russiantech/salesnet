from flask_jwt_extended import current_user, jwt_required
import traceback, requests, secrets
from flask import current_app, request, Blueprint, url_for
from web.apis.utils.serializers import error_response, success_response
from web.apis.models.transactions import Transaction
from sqlalchemy.exc import IntegrityError
from requests.exceptions import ConnectionError, Timeout, RequestException
from jsonschema import validate, ValidationError
from web.apis.schemas.transactions import pay_schema
from web.extensions import db, csrf
from web.apis.models.users import User
from web.apis.models.orders import Order
from web.apis.utils.helpers import generate_ref

# app/webhooks/stripe_webhook.py
from flask import Blueprint, request
import stripe

stripe_webhook_bp = Blueprint('stripe_webhook', __name__)

@stripe_webhook_bp.route('/webhook/stripe', methods=['POST'])
def stripe_webhook():
    payload = request.get_data(as_text=True)
    sig_header = request.headers.get('Stripe-Signature')
    
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, current_app.config['STRIPE_WEBHOOK_SECRET'])
    except ValueError as e:
        return jsonify({'error': 'Invalid payload'}), 400
    except stripe.error.SignatureVerificationError as e:
        return jsonify({'error': 'Invalid signature'}), 400

    # Handle the event
    if event['type'] == 'charge.succeeded':
        charge = event['data']['object']
        # Update transaction status in the database

    return jsonify({'status': 'success'}), 200
