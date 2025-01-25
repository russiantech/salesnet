import traceback
from flask import request
from flask_jwt_extended import jwt_required
from sqlalchemy import desc
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from web.apis.models.roles import Role
from web.apis.utils.decorators import access_required
from web.apis.utils.serializers import PageSerializer, error_response, success_response
from web.extensions import db
from web.apis import api_bp as role_bp

@role_bp.route('/roles', methods=['POST'])
@jwt_required()
@access_required('admin', 'dev')
def create_role():
    try:
        data = request.json
        new_role = Role(
            name=data.get('name'),
            description=data.get('description', '')
        )
        
        db.session.add(new_role)
        db.session.commit()
        return success_response("Role created successfully.", data=new_role.get_summary())
    
    except IntegrityError:
        db.session.rollback()
        return error_response("Failed to create role: Integrity error.")
    
    except SQLAlchemyError as e:
        db.session.rollback()
        return error_response(f"Database error: {str(e)}")
    
    except Exception as e:
        traceback.print_exc()
        return error_response(f"Unexpected error: {str(e)}")

@role_bp.route('/roles', methods=['GET'])
@role_bp.route('/roles/<int:role_id>', methods=['GET'])
@jwt_required()
@access_required('admin', 'dev')
def get_roles(role_id=None):
    try:
        if role_id:
            role = Role.query.get(role_id)
            if not role:
                return error_response("Role not found.")
            return success_response(f"Role <{role.name}> fetched successfully.", data=role.get_summary())

        # Pagination parameters: Default page = 1, page_size = 5
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 5, type=int)

        # Fetch roles ordered by creation date
        roles = Role.query.order_by(desc(Role.created_at)).paginate(page=page, per_page=page_size)

        # Serialize the paginated result using PageSerializer
        data = PageSerializer(pagination_obj=roles, resource_name="roles", include_user=True).get_data()

        # Check if data is iterable
        if isinstance(data, dict):  # Assuming get_data() returns a dict
            return success_response("Roles fetched successfully.", data=data)
        else:
            return error_response("Unexpected data format returned.")

    except Exception as e:
        traceback.print_exc()
        return error_response(f"Error fetching roles: {str(e)}")

@role_bp.route('/roles/<int:role_id>', methods=['PUT'])
@jwt_required()
@access_required('admin', 'dev')
def update_role(role_id):
    try:
        role = Role.query.get(role_id)
        if not role:
            return error_response("Role not found.")

        data = request.json
        role.name = data.get('name', role.name)
        role.description = data.get('description', role.description)

        db.session.commit()
        return success_response("Role updated successfully.", data=role.get_summary())

    except SQLAlchemyError as e:
        db.session.rollback()
        return error_response(f"Database error: {str(e)}")
    except Exception as e:
        return error_response(f"Unexpected error: {str(e)}")

@role_bp.route('/roles/<int:role_id>', methods=['DELETE'])
@jwt_required()
@access_required('admin', 'dev')
def delete_role(role_id):
    try:
        role = Role.query.get(role_id)
        if not role:
            return error_response("Role not found.")

        db.session.delete(role)
        db.session.commit()
        return success_response("Role deleted successfully.")

    except SQLAlchemyError as e:
        db.session.rollback()
        return error_response(f"Database error: {str(e)}")
    except Exception as e:
        return error_response(f"Unexpected error: {str(e)}")
