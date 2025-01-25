import traceback
from flask import Blueprint, request
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from web.models import Items, db
from web.apis.utils.helpers import success_response, error_response

# apportion_bp = Blueprint('apportion', __name__)
items_bp = Blueprint('items', __name__)

@items_bp.route('/items', methods=['POST'])
def create_item():
    try:
        data = request.json
        new_item = Items(
            name=data.get('name'),
            category=data.get('category', 'default_category'),
            quantity=data.get('quantity', 0),
            unit_price=data.get('unit_price', 0.0),
            description=data.get('description', ''),
        )
        
        db.session.add(new_item)
        db.session.commit()
        return success_response("Item created successfully.", data=new_item.to_dict())
    
    except IntegrityError:
        db.session.rollback()
        return error_response("Failed to create item: Integrity error.")
    
    except SQLAlchemyError as e:
        db.session.rollback()
        return error_response(f"Database error: {str(e)}")
    
    except Exception as e:
        return error_response(f"Unexpected error: {str(e)}")

@items_bp.route('/items', methods=['GET'])
@items_bp.route('/items/<int:item_id>', methods=['GET'])
def get_items(item_id=None):
    try:
        if item_id:
            item = Items.query.get(item_id)
            if not item:
                return error_response("Item not found.")
            return success_response("Item fetched successfully.", data=item.to_dict())

        # Pagination
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        dept = request.args.get('dept', None, type=str)
        query = Items.query
        if dept and dept is not None:
            query = query.filter_by(dept=dept)  # Filter by department if provided
            
        # Fetch paginated apportions, ordered by latest
        items_pagination = query.order_by(Items.created.desc()).paginate(page=page, per_page=per_page, error_out=False)
        items = [item.to_dict() for item in items_pagination.items]

        data = {
            "current_page": items_pagination.page,
            "items": items,
            "total_items": items_pagination.total,
            "total_pages": items_pagination.pages
        }
        return success_response("Items fetched successfully.", data=data)

    except Exception as e:
        return error_response(f"Error fetching items: {str(e)}")


@items_bp.route('/items/<int:item_id>', methods=['PUT'])
def update_item(item_id):
    try:
        item = Items.query.get(item_id)
        if not item:
            return error_response("Item not found.")

        data = request.json
        item.name = data.get('name', item.name)
        item.category = data.get('category', item.category)
        item.quantity = data.get('quantity', item.quantity)
        item.unit_price = data.get('unit_price', item.unit_price)
        item.description = data.get('description', item.description)

        db.session.commit()
        return success_response("Item updated successfully.")

    except SQLAlchemyError as e:
        db.session.rollback()
        return error_response(f"Database error: {str(e)}")
    except Exception as e:
        return error_response(f"Unexpected error: {str(e)}")


@items_bp.route('/items/<int:item_id>', methods=['DELETE'])
def delete_item(item_id):
    try:
        item = Items.query.get(item_id)
        if not item:
            return error_response("Item not found.")

        db.session.delete(item)
        db.session.commit()
        return success_response("Item deleted successfully.")

    except SQLAlchemyError as e:
        db.session.rollback()
        return error_response(f"Database error: {str(e)}")
    except Exception as e:
        return error_response(f"Unexpected error: {str(e)}")
