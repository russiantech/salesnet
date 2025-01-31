from flask import Flask, request, jsonify, redirect, url_for
import requests
import os
from dotenv import load_dotenv

load_dotenv()

from web.apis.transactions import transact_bp
# Use environment variables for Paystack API keys
PAYSTACK_SECRET_KEY = os.getenv("PAYSTACK_SECRET_KEY")
PAYSTACK_PUBLIC_KEY = os.getenv("PAYSTACK_PUBLIC_KEY")

# Paystack API URLs
PAYSTACK_URL = "https://api.paystack.co"
VERIFY_PAYMENT_URL = f"{PAYSTACK_URL}/transaction/verify"

@transact_bp.route('/initiate_payment', methods=['POST'])
def init_paystack():
    """Initiates payment request to Paystack"""
    data = request.json
    amount = data.get('amount')  # amount should be in kobo (Naira cents)
    email = data.get('email')

    headers = {
        'Authorization': str("Bearer " + PAYSTACK_SECRET_KEY),
        'Content-Type': 'application/json',
    }

    payload = {
        "email": email,
        "amount": amount * 100,  # Paystack API expects amount in kobo (100 kobo = 1 Naira)
        "currency": "NGN",  # Set currency if required
        "callback_url": url_for('payment_callback', _external=True),
    }

    response = requests.post(f"{PAYSTACK_URL}/transaction/initialize", json=payload, headers=headers)

    if response.status_code == 200:
        data = response.json()
        if data['status']:
            # Redirect to Paystack payment page
            return jsonify({
                'status': 'success',
                'payment_url': data['data']['authorization_url']
            })
        else:
            return jsonify({'status': 'error', 'message': 'Failed to initialize payment'}), 400
    else:
        return jsonify({'status': 'error', 'message': 'Paystack API request failed'}), 500


@transact_bp.route('/payment_callback', methods=['GET'])
def payment_callback():
    """Handles Paystack payment callback"""
    transaction_reference = request.args.get('reference')
    headers = {
        'Authorization': f'Bearer {PAYSTACK_SECRET_KEY}',
    }
    
    response = requests.get(f"{VERIFY_PAYMENT_URL}/{transaction_reference}", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        if data['status'] and data['data']['status'] == 'success':
            # Update the database (order status) and finalize payment
            return jsonify({
                'status': 'success',
                'message': 'Payment was successful'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Payment failed'
            }), 400
    else:
        return jsonify({
            'status': 'error',
            'message': 'Unable to verify payment'
        }), 500
