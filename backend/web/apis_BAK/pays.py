import traceback, requests, secrets
from flask_login import current_user
from flask import current_app, render_template, request, Blueprint, url_for
from web.models import Plan, db, User, Transaction
from web.extensions import csrf
from requests.exceptions import ConnectionError, Timeout, RequestException
from jsonschema import validate, ValidationError
from web.apis.utils.helpers import success_response, error_response, generate_random_id
from web.apis.utils.valid_schemas import pay_schema
from sqlalchemy.exc import IntegrityError

pay = Blueprint('pay', __name__)

@pay.route('/init-subscribe/<string:plan_type>', methods=['POST'])
@csrf.exempt
def subscribe_pay(plan_type):
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
            
            # Validate the data against the schema
            try:
                validate(instance=data, schema=pay_schema)
            except ValidationError as e:
                return error_response(str(e.message))

            # retrieve plan
            plan = Plan.query.filter(Plan.plan_type == plan_type).first()
            # plan = db.session.scalar(sa.select(Plan).where(Plan.plan_type == plan_type)).first()
            
            if not plan:
                return error_response("Plan not found!")
            
            # amount = data.get('amount', plan.plan_amount).strip()
            amount = data.get('amount', plan.plan_amount)
            email = data.get('email', current_user.email if current_user.is_authenticated else None)
            subscription = data.get('subscription', plan.plan_type)
            currency = data.get('currency', plan.plan_currency) or "USD"
            phone = data.get('phone', None)

            if not email:
                return error_response("A valid email address is required for receipt of transaction")

            # if (not amount.isdigit() or int(amount) <= 0):
            if (not str(amount).isdigit() or int(amount) <= 0):
                return error_response("Kindly provide an amount > 0 to continue")
            
            headers = {
                "accept": "application/json",
                "Authorization": f"Bearer {current_app.config['RAVE_LIVE_SECRET_KEY']}",
                "Content-Type": "application/json"
            }
            payment_url = "https://api.flutterwave.com/v3/payments"
            payload = {
                "tx_ref": f"Techa-{generate_random_id(k=5)}",
                "amount": int(amount),
                "currency": currency,  # Ensure this matches the currency in the transaction plan
                "redirect_url": f"{request.referrer}",
                # "redirect_url": f"{request.url_root}api/transaction-callback",
                "customer": {
                    "email": email,
                    "phonenumber": current_user.phone if current_user.is_authenticated and current_user.phone else phone,
                    "name": current_user.name or current_user.username if current_user.is_authenticated else email
                },
                
                "payment_options": "card, ussd, banktransfer, credit, mobilemoneyghana",
                "customizations": {
                    "title": f"{data.get('title',  plan.plan_title)}",
                    "logo": url_for('static', filename='images/logo_0.png', _external=True)
                }
            }

            try:
                if subscription:
                    # step 0: Get n initiate subscription
                    # plan_init_link = "https://api.flutterwave.com/v3/transaction-plans"
                    plan_init_link = "https://api.flutterwave.com/v3/payment-plans"
                    
                    # Step 1: Create the transaction plan with the same currency
                    plan_payload = {
                        "amount": payload['amount'],
                        "name": payload['customizations']["title"],
                        "interval": subscription,
                        "currency": payload['currency']  # Match the currency here as well
                    }
                    
                    plan_response = requests.post(plan_init_link, headers=headers, json=plan_payload)
                    plan_data = dict(plan_response.json().get('data', {}))
                    if plan_response.status_code != 200 or not plan_data.get('id'):
                        return error_response(f"Failed to create/initiate transaction plans - {plan_response.status_code}-{plan_data}")
    
                    # Step 2: Update the payload with the plan ID and initiate transaction
                    payload['payment_plan'] = plan_data['id']

                payment_response = requests.post(payment_url, json=payload, headers=headers)
                # payment_response = requests.request(method="POST", url=payment_url, headers=headers, data=payload)

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
                    'plan_id': plan.id,  # Link to the subscription plan
                    'is_subscription': True if subscription else False,  # Mark as a subscription
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

@pay.route('/transaction-callback', methods=['GET'])
@csrf.exempt
def transaction_callback():
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


@pay.route("/transaction-successful")
def success():
    support_amount = "30, 40, 50, 70, 80, 90, 100, 200, 300, 400, 500"
    support_interval = "daily, weekly, monthly, quarterly, yearly"
    context = {
        "title" :'Us . Intellect',
        "support_amount" : support_amount, 
        "support_interval" : support_interval, 
    }
    return render_template('incs/payment_successful.html', **context)
