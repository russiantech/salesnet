import traceback
from flask import request
from flask_jwt_extended import current_user, jwt_required
from sqlalchemy import desc
from web.extensions import db
from web.apis import api_bp as address_bp
from web.apis.models.addresses import Address
from web.apis.utils.serializers import PageSerializer, success_response, error_response
from web.apis.schemas.address import address_schema  
from jsonschema import validate, ValidationError

@address_bp.route('/addresses/<user_id>/user', methods=['GET'])
@jwt_required()
def user_addresses(user_id=None):
    """get addresses for the authenticated user with pagination."""
    try:
        
        page_size = request.args.get('page_size', 5, type=int)
        page = request.args.get('page', 1, type=int)
        user_id = user_id or current_user.id

        addresses = Address.query.filter_by(user_id=user_id).order_by(desc(Address.created_at)) \
            .paginate(page=page, per_page=page_size)

        data = PageSerializer(pagination_obj=addresses, resource_name="addresses", include_user=False).get_data()
        # data = PageSerializer(items=[addresses], resource_name="addresses", include_user=False).get_data()
        return success_response("Addresses fetched successfully", data=data)

    except Exception as e:
        return error_response(f"Unexpected error: {str(e)}", status_code=500)
    
@address_bp.route('/addresses', methods=['GET'])
@address_bp.route('/addresses/<address_id>', methods=['GET'])
@jwt_required()
def list_addresses(address_id=None):
    """List all/one addresses for the authenticated user with pagination."""
    try:
        if address_id is not None:
            address = Address.query.get_or_404(int(address_id))
            if not address:
                return error_response("Address not found.", status_code=404)
            
            # data=PageSerializer(items=[address], resource_name="address").get_data()
            data = address.get_summary(include_user=True)
            return success_response("Address fetched successfully.", data=data)
        
        page_size = request.args.get('page_size', 5, type=int)
        page = request.args.get('page', 1, type=int)
        
        addresses = Address.query.order_by(desc(Address.created_at)).paginate(page=page, per_page=page_size)

        data = PageSerializer(pagination_obj=addresses, resource_name="addresses", include_user=False).get_data()
        # data = PageSerializer(items=[addresses], resource_name="addresses", include_user=False).get_data()
        return success_response("Addresses fetched successfully", data=data)

    except Exception as e:
        traceback.print_exc()
        return error_response(f"Unexpected error: {str(e)}", status_code=500)

@address_bp.route('/addresses', methods=['POST'])
@jwt_required()
def create_address():
    """Create a new address for the authenticated user."""
    try:
        # Parse incoming request data
        data = request.json
        validate(instance=data, schema=address_schema)  # Validate the data using JSON schema

        # Extract values and set user_id
        user_id = current_user.id
        address = Address(
            first_name=data['first_name'],
            last_name=data['last_name'],
            zip_code=data['zip_code'],
            phone_number=data['phone_number'],
            street_address=data['address'],
            city=data['city'],
            country=data['country'],
            user_id=user_id,
            user=current_user
        )

        db.session.add(address)
        db.session.commit()
        return success_response("Address created successfully.", data=address.get_summary(), status_code=201)

    except ValidationError as e:
        return error_response(f"Validation error: {e.message}", status_code=400)
    except Exception as e:
        return error_response(f"Unexpected error: {str(e)}", status_code=500)

@address_bp.route('/addresses/<int:address_id>', methods=['PUT'])
@jwt_required()
def update_address(address_id):
    """Update an existing address for the authenticated user."""
    try:
        
        # Fetch the address and ensure the user is authorized to edit it
        address = Address.query.get_or_404(address_id)

        if not address:
            return error_response("Address not found", status_code=404)

        # Ensure the user is either the owner of the address or has admin/dev role
        if not (
            current_user.id == address.user_id or
            any(role.name in ["admin", "dev"] for role in current_user.roles)
        ):
            return error_response(f"{address.user_id, current_user.id}, Access forbidden: insufficient permissions.", status_code=403)  # Forbidden
        
        # Parse incoming request data
        data = request.json
        validate(instance=data, schema=address_schema)  # Validate using JSON schema

        # Update address fields
        address.first_name = data.get('first_name', address.first_name)
        address.last_name = data.get('last_name', address.last_name)
        address.zip_code = data.get('zip_code', address.zip_code)
        address.phone_number = data.get('phone_number', address.phone_number)
        address.street_address = data.get('address', address.street_address)
        address.city = data.get('city', address.city)
        address.country = data.get('country', address.country)
        db.session.commit()

        return success_response("Address updated successfully.", data=address.get_summary())

    except ValidationError as e:
        return error_response(f"Validation error: {e.message}", status_code=400)
    except Exception as e:
        return error_response(f"Unexpected error: {str(e)}", status_code=500)

@address_bp.route('/addresses/<int:address_id>', methods=['DELETE'])
@jwt_required()
def delete_address(address_id):
    """Delete an existing address for the authenticated user."""
    try:
        # Fetch the address and ensure the user is authorized to delete it
        address = Address.query.get_or_404(address_id)
                # Ensure the user is either the owner of the address or has admin/dev role
        if not (
            current_user.id == address.user_id or
            any(role.name in ["admin", "dev"] for role in current_user.roles)
        ):
            return error_response(f"Access forbidden: insufficient permissions.", status_code=403)  # Forbidden
        
        # Check permissions - only the address owner or an admin can delete
        if not current_user.is_admin() and address.user_id != current_user.id:
            return error_response("Permission denied.", status_code=403)

        db.session.delete(address)
        db.session.commit()
        # return success_response("Address deleted successfully.", status_code=204)
        return success_response("Address deleted successfully.")

    except Exception as e:
        return error_response(f"Unexpected error: {str(e)}")
        # return error_response(f"Unexpected error: {str(e)}", status_code=500)