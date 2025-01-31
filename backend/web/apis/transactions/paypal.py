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

pay = Blueprint('pay', __name__)

@pay.route('/transactions/flutterwave', methods=['POST'])
# @csrf.exempt
@jwt_required(optional=True)
def initiate(order_id):
    try:
        if request.method == "POST":
            if request.content_type == 'application/json':
                data = request.get_json()
                
            elif 'multipart/form-data' in request.content_type:
                data = request.form.to_dict()
            else:
                return error_response("Content-Type must be application/json or multipart/form-data")
            
            if not data:
                return error_response("No data received to process transactions")
            
            try:
                validate(instance=data, schema=pay_schema)
            except ValidationError as e:
                return error_response(str(e.message))

            order = Order.query.filter(Order.id == order_id).first()
            
            if not order:
                return error_response(f"Order <{order_id}> not found!")
            
            amount = data.get('amount', order.amout)
            email = data.get('email', current_user.email if current_user else None)
            currency = data.get('currency', order.currency) or "USD"
            phone = data.get('phone', None)

            if not email:
                return error_response("A valid email address is required for receipt of transaction")

            if (not str(amount).isdigit() or int(amount) <= 0):
                return error_response("Kindly provide an amount > 0 to continue")
            
            headers = {
                "accept": "application/json",
                "Authorization": f"Bearer {current_app.config['FLUTTERWAVE_SK']}",
                "Content-Type": "application/json"
            }
            payment_url = "https://api.flutterwave.com/v3/payments"
            payload = {
                "tx_ref": generate_ref(prefix="TEC", num_digits=4, letters="???"),
                "amount": int(amount),
                "currency": currency,  # Ensure this matches the currency in the transaction plan
                "redirect_url": f"{request.referrer}",
                # "redirect_url": f"{request.url_root}api/transaction-callback",
                "customer": {
                    "email": email,
                    "phonenumber": current_user.phone if current_user.is_authenticated and current_user.phone else phone,
                    "name": current_user.name or current_user.username if current_user else email
                },
                
                "payment_options": "card, ussd, banktransfer, credit, mobilemoneyghana",
                "customizations": {
                    "title": f"{data.get('title',  plan.plan_title)}",
                    "logo": url_for('static', filename='images/logo_0.png', _external=True)
                }
            }

            try:

                payment_response = requests.post(payment_url, json=payload, headers=headers)
                payment_data = dict(payment_response.json()) if payment_response else {}
                payment_link = payment_data.get("data", {}).get("link")
                
                if not payment_link:
                    return error_response("Failed to retrieve transaction link")

                user = User.query.filter_by(email=email).first()
                if not user:
                    user_data = {
                        'username': email,
                        'email': email,
                        'phone': data.get('phone', None),
                    }
                    
                    new_user = User(**user_data)
                    new_user.set_password(secrets.token_urlsafe(5))
                    db.session.add(new_user)

                    try:
                        db.session.commit()
                        user_id = new_user.id
                    except IntegrityError:
                        db.session.rollback()
                        user = User.query.filter_by(email=email).first()
                        user_id = user.id
                else:
                    user_id = user.id

                payment_data = {
                    'currency_code': payload['currency'],
                    'tx_amount': payload['amount'],
                    'tx_ref': payload['tx_ref'],
                    'tx_status': 'pending',
                    'provider': 'flutterwave',
                    'tx_id': None,
                    'user_id': user_id,
                    # 'plan_id': plan.id,  # Link to the subscription plan
                    # 'is_subscription': True if subscription else False,  # Mark as a subscription
                    'tx_descr': f"Subscription for plan: {plan.plan_title}"
                }

                new_payment = Transaction(**payment_data)
                db.session.add(new_payment)
                db.session.commit()

                data = {"redirect": payment_link}
                return success_response("Continue to pay securely..", data=data)

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

        return error_response("Invalid request method", status_code=405)

    except Exception as e:
        print(traceback.print_exc())
        print(traceback.format_exc())
        
        return error_response(f"error: {str(e)}", status_code=500)

@pay.route('/callback', methods=['GET'])
@csrf.exempt
def callback():
    try:
        
        status = request.args.get('status')
        transaction_id = request.args.get('transaction_id')
        tx_ref = request.args.get('tx_ref')

        transaction = Transaction.query.filter(Transaction.tx_ref == tx_ref).first()

        if not transaction:
            return error_response('Transaction record not found', status_code=404)

        if status == 'successful':
            headers = {
                "accept": "application/json",
                "Authorization": f"Bearer {current_app.config['RAVE_SECRET_KEY']}",
                "Content-Type": "application/json"
            }

            verify_endpoint = f"https://api.flutterwave.com/v3/transactions/{transaction_id}/verify"
            # response = requests.get(verify_endpoint, headers=headers)
            # response = requests.request("POST", url, headers=headers, data=payload)
            response = requests.request("POST", verify_endpoint, headers=headers)
            # rresponse = requests.post(verify_endpoint, json=payload, headers=headers)
            response = requests.post(verify_endpoint, headers=headers)

            if response.status_code == 200:
                response_data = response.json().get('data', {})

                if (
                    response_data.get('status') == "successful"
                    and response_data.get('amount') >= transaction.tx_amount 
                    and response_data.get('currency') == transaction.currency
                ):
                    transaction.tx_status = response_data['status']
                    transaction.tx_id = response_data['id']
                    db.session.commit()
                    
                    return success_response('Transaction verified successfully', data=response_data)
                
                else:
                    return error_response(f'Transaction verification failed->{response_data}')
            else:
                return error_response('Failed to verify transaction')

        elif status == 'cancelled':
            transaction.tx_status = status
            db.session.commit()
            return error_response('Transaction was cancelled')

        else:
            return error_response('Invalid transaction status')

    except Exception as e:
        traceback.print_exc()
        return error_response(str(e))


# ===============
# app/controllers/payment_controller.py
from flask import Blueprint, request, jsonify
# from web.services.payment_service import PaymentService
from web.apis.utils.transactions import PaymentService

payment_bp = Blueprint('payment', __name__)
payment_service = PaymentService()

@payment_bp.route('/payment/stripe', methods=['POST'])
def stripe_payment():
    data = request.json
    amount = data['amount']
    currency = data['currency']
    source = data['source']
    
    charge = payment_service.process_stripe_payment(amount, currency, source)
    if 'error' in charge:
        return jsonify(charge), 400

    payment_service.save_transaction(data['user_id'], amount, currency, 'stripe', charge['id'])
    return jsonify({'status': 'success', 'charge': charge}), 200

# Similar routes for PayPal, Paystack, and Flutterwave
