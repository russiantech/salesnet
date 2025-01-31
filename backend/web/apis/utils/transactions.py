# app/services/payment_service.py
from flask import current_app
import stripe
import requests
from web.apis.models.transactions import Transaction
from web.extensions import db

class PaymentService:
    def __init__(self):
        stripe.api_key = current_app.config['STRIPE_SECRET_KEY']

    def process_stripe_payment(self, amount, currency, source):
        try:
            charge = stripe.Charge.create(
                amount=amount,
                currency=currency,
                source=source,
                description='Payment for order'
            )
            return charge
        except stripe.error.StripeError as e:
            # Handle Stripe errors
            return {'error': str(e)}

    def process_paypal_payment(self, amount, currency):
        # Implement PayPal payment processing
        pass

    def process_paystack_payment(self, amount, currency):
        # Implement Paystack payment processing
        pass

    def process_flutterwave_payment(self, amount, currency):
        # Implement Flutterwave payment processing
        pass

    def save_transaction(self, user_id, amount, currency, payment_method, transaction_id):
        transaction = Transaction(
            user_id=user_id,
            amount=amount,
            currency=currency,
            payment_method=payment_method,
            transaction_id=transaction_id
        )
        db.session.add(transaction)
        db.session.commit()
