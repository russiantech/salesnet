# Helper function to handle email verification
import traceback
from jsonschema import ValidationError, validate
from web.apis.utils.serializers import success_response, error_response
from web.extensions import db
from web.apis.schemas.user import validTokenSchema

def handle_verify_email(user):
    try:
        if user.valid_email:
            return success_response(f'Your email address, {user.username}, is already verified.')
        user.valid_email = True
        db.session.commit()
        return success_response(f'Email address verified for {user.username}.')
    except Exception as e:
        
        return error_response(f"{e}")

# Helper function to handle password reset
# from flask_expects_json import expects_json
# @expects_json(reset_password_schema)
def handle_reset_password(user, data):
    try:
       
        try:
            validate(instance=data, schema=validTokenSchema)
        except ValidationError as e:
            return error_response(f"Validation error: {e.message}")
        
        new_password = data["password"]
        
        if not new_password:
            return error_response(f"Missing password in the reset password request")
        
        user.set_password(new_password)
        db.session.commit()
        
        return success_response(f'Your password has been updated for {user.username}. successfully.')
    
    except ValueError as e:
        traceback.print_exc()
        return error_response(f"{str(e)}")
    except Exception as e:
        traceback.print_exc()
        return error_response(f"{str(e)}")
  