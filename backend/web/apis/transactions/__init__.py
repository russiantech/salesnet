

from flask import Blueprint
transact_bp = Blueprint('transactions', __name__)

from web.apis.utils.serializers import success_response, error_response
from web.apis.models.transactions import Transaction
from web.extensions import db
from sqlalchemy.exc import SQLAlchemyError

def save_transaction(
    user_id, order_id, 
    product_id, amount, 
    currency, payment_method, 
    refference, 
    status="pending", 
    description=None
    ):
    try:
        # Create the transaction
        transaction = Transaction(
            user_id=user_id,
            order_id=order_id,
            product_id=product_id,
            amount=amount,
            currency=currency,
            payment_method=payment_method,
            status = status,
            refference=refference,
            description=description  # Optional description
        )
        db.session.add(transaction)
        db.session.commit()
        return success_response("Transaction saved successfully", data=transaction.get_summary()) # Return the created transaction for confirmation
    except SQLAlchemyError as e:
        db.session.rollback()  # Rollback the session in case of error
        print(f"Error saving transaction: {e}")  # Log the error (consider using a logging framework)
        return None  # Return None or raise an exception as needed
        # return error_response(f"error: {str(e)}", status_code=500)


from . import flutterwave
from . import paystack

__all__ = [
    "flutterwave",
    "paystack"
]
