from flask_jwt_extended import current_user, jwt_required
import traceback, requests, secrets
from flask import current_app, request, url_for
from web.apis.utils.serializers import error_response, success_response
from web.apis.models.transactions import Transaction
from requests.exceptions import ConnectionError, Timeout, RequestException
from jsonschema import validate, ValidationError
from web.apis.schemas.transactions import pay_schema
from web.extensions import db, csrf
from web.apis.models.users import User
from web.apis.models.orders import Order
from web.apis.utils.helpers import generate_ref
from web.apis.transactions import save_transaction, transact_bp

@transact_bp.route('/transactions/flutterwave', methods=['POST'])
@csrf.exempt
@jwt_required(optional=True)
def initiate_flutterwave():
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

            # order = Order.query.filter(Order.id == data['order_id']).first()
            order = Order.get_order(data['order_id'])
            
            if not order:
                return error_response(f"Order <{data['order_id']}> not found!")
            # print(order.calculate_total_amount())
            amount = data.get('amount', order.calculate_total_amount())
            order_id = data.get('order_id', order.id)
            email = data.get('email', current_user.email if current_user else None)
            currency = data.get('currency', "USD")
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
            
            payment_url = str("https://api.flutterwave.com/v3/payments")
            refference = str(generate_ref(prefix="TEC", num_digits=4, letters="???"))
            redirect_url = str(request.url_root+"api/transactions/callback/flutterwave")
            # redirect_url = f"{request.url_root}api/transaction/callback/flutterwave"
            payload = {
                "tx_ref": refference,
                "amount": int(amount),
                "currency": currency,  # Ensure this matches the currency in the transaction plan
                "redirect_url": redirect_url,
                "customer": {
                    "email": email,
                    "phonenumber": current_user.phone if current_user and current_user.phone else phone,
                    "name": current_user.name or current_user.username if current_user else email
                },
                
                "payment_options": "card, ussd, banktransfer, credit, mobilemoneyghana",
                "customizations": {
                    "title": f"{data.get('name',  f'<Order-id:{order_id}')}",
                    "logo": url_for('static', filename='images/logo_0.png', _external=True)
                }
            }

            try:
                payment_response = requests.post(payment_url, json=payload, headers=headers)
                payment_data = dict(payment_response.json()) if payment_response else {}
                payment_link = payment_data.get("data", {}).get("link")
                if not payment_link:
                    print("Response Content:", payment_response.content.decode('utf-8'))
                    return error_response(f"Failed to retrieve transaction link > {payment_response.content.decode('utf-8')} ")

                user = User.get_user(email)
                if not user:
                    user = User(
                        username=email.split('@')[0],
                        email=email,
                        phone=phone,
                        is_guest=True
                        )
                    user.set_password(secrets.token_urlsafe(5))
                    db.session.add(user)
                    db.session.commit()

                # Save transaction using the new function
                save_t = save_transaction(
                    user_id=user.id,
                    order_id=order.id,
                    product_id=None,  # Assuming no product here, adjust if necessary
                    amount=amount,
                    currency=currency,
                    payment_method='flutterwave',
                    refference=payload['tx_ref'],
                    status='pending',
                    description=f"Payment for order <Order_id:{order_id}"
                )
                
                if not save_t:
                    return error_response("Could not save transactions.")
                
                return success_response("Continue to pay securely..", data={"redirect": payment_link})

            except ConnectionError:
                return error_response("No internet connection. pls check your network and try again.")

            except Timeout:
                return error_response("The request timed out. Please try again later.")

            except RequestException as e:
                return error_response(f"error: {str(e)}")

        return error_response("Invalid request method", status_code=405)

    except Exception as e:
        print(traceback.print_exc())
        return error_response(f"error: {str(e)}", status_code=500)

@transact_bp.route('/transactions/callback/flutterwave', methods=['GET'])
# @csrf.exempt
@jwt_required(optional=True)
def callback():
    try:
        status = request.args.get('status')
        transaction_id = request.args.get('transaction_id')
        refference = request.args.get('tx_ref')
        transaction = Transaction.get_transaction(refference)
        if not transaction:
            return error_response('Transaction record not found', status_code=404)

        if status == 'successful':
            headers = {
                "accept": "application/json",
                "Authorization": f"Bearer {current_app.config['RAVE_SECRET_KEY']}",
                "Content-Type": "application/json"
            }

            verify_endpoint = f"https://api.flutterwave.com/v3/transactions/{transaction_id}/verify"
            response = requests.get(verify_endpoint, headers=headers)

            if response.status_code == 200:
                response_data = response.json().get('data', {})
                if (
                    response_data.get('status') == "successful"
                    and response_data.get('amount') >= transaction.amount 
                    and response_data.get('currency') == transaction.currency
                ):
                    transaction.status = response_data['status']
                    db.session.commit()
                    return success_response('Transaction verified successfully', data=response_data)
                else:
                    return error_response(f'Transaction verification failed->{response_data}')
            else:
                return error_response('Failed to verify transaction')

        elif status == 'cancelled':
            transaction.status = status
            db.session.commit()
            return error_response('Transaction was cancelled')
        else:
            return error_response('Invalid transaction status')

    except Exception as e:
        traceback.print_exc()
        return error_response(str(e))
