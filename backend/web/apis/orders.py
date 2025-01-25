import traceback
from flask import request
from flask_jwt_extended import jwt_required, get_jwt, current_user
from jsonschema import ValidationError, validate
from sqlalchemy import desc
from web.apis.models.addresses import Address
from web.apis.utils.decorators import access_required
from web.extensions import db, fake
from web.apis.models.orders import Order, OrderItem
from web.apis.schemas.order import order_schema
from web.apis.utils.serializers import PageSerializer
from web.apis.models.products import Product
from web.apis.utils.serializers import success_response, error_response

from web.apis import api_bp as order_bp

@order_bp.route('/orders', methods=['GET'])
@jwt_required()
@access_required('dev', 'admin')
def orders():
    try:
        # Check permissions
        page_size = request.args.get('page_size', 5)
        page = request.args.get('page', 1)
        orders = Order.query.order_by(desc(Order.created_at)).paginate(page=page, per_page=page_size)
        data = PageSerializer(pagination_obj=orders, resource_name="orders", include_users=True).get_data()
        
        return success_response("Orders fetched successfully", data=data)
    
    except Exception as e:
        db.session.rollback()  # Rollback in case of error
        traceback.print_exc()
        return error_response(f"An error occurred: {str(e)}")

@order_bp.route('/orders/<int:user_id>/user', methods=['GET'])
@jwt_required()
def my_orders(user_id):
    try:
        # Check permissions
        if not current_user.is_admin() and user_id != current_user.id:
            return error_response("Permission denied.", status_code=403)
        
        page_size = request.args.get('page_size', 5)
        page = request.args.get('page', 1)
        
        orders = Order.query.filter_by(
            user_id=user_id).order_by(
            desc(Order.created_at)
            ).paginate(page=page, per_page=page_size)
        
        data = PageSerializer(pagination_obj=orders,  resource_name="orders", include_users=True).get_data()
        
        return success_response("Orders fetched successfully", data=data)
    
    except Exception as e:
        db.session.rollback()  # Rollback in case of error
        traceback.print_exc()
        return error_response(f"An error occurred: {str(e)}")

@order_bp.route('/orders/<order_id>', methods=['GET'])
@jwt_required()
@access_required('dev', 'admin')
def order_details(order_id):
    try:
        order = Order.query.get_or_404(order_id)
        user = current_user
        if order.user_id is user.id or user.is_admin():
            return success_response(f"Order <{order_id}> fetched successfully", data=order.get_summary(include_order_items=True))
        else:
            return error_response('Access denied, this does not belong to you', status_code=401)
    except Exception as e:
        db.session.rollback()  # Rollback in case of error
        traceback.print_exc()
        return error_response(f"An error occurred: {str(e)}", 500)

# @order_bp.route('/orders', methods=['POST'])
# @jwt_required(optional=True)
# def create_order():
#     try:
#         # Determine the content type and get data accordingly
#         if request.content_type == 'application/json':
#             data = request.get_json()
#         elif 'multipart/form-data' in request.content_type:
#             data = request.form.to_dict()
#         else:
#             return error_response("Content-Type must be application/json or multipart/form-data", 400)

#         # Validate the incoming data against the order schema
#         try:
#             validate(instance=data, schema=order_schema)
#         except ValidationError as e:
#             return error_response(f"Validation error: {e.message}", 400)

#         user = current_user
#         user_id = user.id if hasattr(user, 'id') else None
#         address_id = data.get('address_id') or request.args.get('address_id')

#         cart_items = data.get('cart_items', [])
#         address_id = data.get('address_id', None)
#         address = data.get('address', {})
    
#         if address_id is not None:
#             # Check if the address belongs to the user or if the user is an admin
#             address = Address.query.filter_by(id=address_id).first()
#             if address is None or (address.user_id is not None and address.user_id != user_id and not user.is_admin):
#                 return error_response('Permission Denied: Invalid address', 403)
#         else:
#             # Create a new address if none is provided
#             address = create_address(address, user)

#         # Create the order
#         order = Order(order_status=0, tracking_number=fake.uuid4(), address_id=address.id)

#         # Validate cart items
#         cart_items = data.get('cart_items')
#         product_ids = [ci['id'] for ci in cart_items]
#         products = db.session.query(Product).filter(Product.id.in_(product_ids)).all()

#         if len(products) != len(cart_items):
#             return error_response('Error: Some products are unavailable', 400)

#         # Add items to the order
#         for index, product in enumerate(products):
#             order.order_items.append(
#                 OrderItem(
#                     name=product.name,
#                     slug=product.slug,
#                     user_id=user_id,
#                     price=product.price,
#                     order_id=order.id, 
#                     product_id=product.id, 
#                     quantity=cart_items[index]['quantity'],
#                     order=order,
#                     user=user,
#                     product=product,
#                 )   
#             )

#         # Commit the order to the database
#         db.session.add(order)
#         db.session.commit()

#         return success_response('Order created successfully', data=order.get_summary(include_order_items=True))

#     except Exception as e:
#         db.session.rollback()  # Rollback in case of error
#         return error_response(f"An error occurred: {str(e)}", 500)

# def create_address(data, user):
#     first_name = data.get('first_name', None)
#     last_name = data.get('last_name', None)
#     zip_code = data.get('zip_code', None)
#     street_address = data.get('street_address', None)
#     country = data.get('country', None)
#     city = data.get('city', None)

#     if user is not None:
#         if first_name is None:
#             first_name = user.first_name

#         if last_name is None:
#             last_name = user.last_name

#     address = Address(
#         first_name=first_name,
#         last_name=last_name,
#         city=city,
#         country=country,
#         street_address=street_address,
#         zip_code=zip_code,
#     )
    
#     if user is not None:
#         address.user_id = user.id

#     db.session.add(address)
#     db.session.flush()  # Ensure the address ID is available

#     return address

@order_bp.route('/orders', methods=['POST'])
@jwt_required(optional=True)
def create_order():
    try:
        # Determine the content type and get data accordingly
        if request.content_type == 'application/json':
            data = request.get_json()
        elif 'multipart/form-data' in request.content_type:
            data = request.form.to_dict()
        else:
            return error_response("Content-Type must be application/json or multipart/form-data", 400)

        # Validate the incoming data against the order schema
        try:
            validate(instance=data, schema=order_schema)
        except ValidationError as e:
            return error_response(f"Validation error: {e.message}", 400)

        user = current_user
        user_id = user.id if hasattr(user, 'id') else None
        address_id = data.get('address_id')
        address_data = data.get('address', {})

        cart_items = data.get('cart_items', [])

        if address_id is not None:
            # Check if the address belongs to the user or if the user is an admin
            address = Address.query.filter_by(id=address_id).first()
            if address is None or (address.user_id is not None and address.user_id != user_id and not user.is_admin):
                return error_response('Permission Denied: Invalid address', 403)
        else:
            # Create a new address if none is provided
            address = create_address(address_data, user)

        # Create the order
        order = Order(order_status=0, tracking_number=fake.uuid4(), address_id=address.id)

        # Validate cart items
        product_ids = [ci['product_id'] for ci in cart_items]  # Updated key
        products = db.session.query(Product).filter(Product.id.in_(product_ids)).all()

        if len(products) != len(cart_items):
            return error_response('Error: Some products are unavailable', 400)

        # Add items to the order
        for index, product in enumerate(products):
            order.order_items.append(
                OrderItem(
                    name=product.name,
                    slug=product.slug,
                    user_id=user_id,
                    price=product.price,
                    order_id=order.id, 
                    product_id=product.id, 
                    quantity=cart_items[index]['quantity'],  # No change needed here
                    order=order,
                    user=user,
                    product=product,
                )   
            )

        # Commit the order to the database
        db.session.add(order)
        db.session.commit()

        return success_response('Order created successfully', data=order.get_summary(include_order_items=True))

    except Exception as e:
        db.session.rollback()  # Rollback in case of error
        return error_response(f"An error occurred: {str(e)}", 500)

def create_address(data, user):
    first_name = data.get('first_name', None)
    last_name = data.get('last_name', None)
    zip_code = data.get('zip_code', None)
    street_address = data.get('street_address', None)
    country = data.get('country', None)
    city = data.get('city', None)

    if user is not None:
        if first_name is None:
            first_name = user.first_name

        if last_name is None:
            last_name = user.last_name

    address = Address(
        first_name=first_name,
        last_name=last_name,
        city=city,
        country=country,
        street_address=street_address,
        zip_code=zip_code,
    )
    
    if user is not None:
        address.user_id = user.id

    db.session.add(address)
    db.session.flush()  # Ensure the address ID is available

    return address

@order_bp.route('/orders/<int:order_id>', methods=['PUT'])
@jwt_required(optional=True)
def update_order(order_id):
    try:
        # Determine content type and retrieve data accordingly
        if request.content_type == 'application/json':
            data = request.get_json()
        elif 'multipart/form-data' in request.content_type:
            data = request.form.to_dict()
        else:
            return error_response("Content-Type must be application/json or multipart/form-data", 400)

        # Validate incoming data against the order schema
        try:
            validate(instance=data, schema=order_schema)
        except ValidationError as e:
            return error_response(f"Validation error: {e.message}", 400)

        user = current_user
        order = Order.query.get_or_404(order_id)

        # Check if the user is authorized to update the order
        if order.user_id != user.id and not user.is_admin:
            return error_response('Permission Denied: You cannot update this order', 403)

        # Update order fields as necessary
        if 'order_status' in data:
            order.order_status = data['order_status']

        if 'address_id' in data:
            # Validate the address
            address = Address.query.filter_by(id=data['address_id']).first()
            if address is None or (address.user_id is not None and address.user_id != user.id and not user.is_admin):
                return error_response('Permission Denied: Invalid address', 403)
            
            order.address_id = data['address_id']

        if 'cart_items' in data:
            cart_items = data['cart_items']
            product_ids = [ci['id'] for ci in cart_items]
            products = db.session.query(Product).filter(Product.id.in_(product_ids)).all()

            # Check if all products are available
            if len(products) != len(cart_items):
                return error_response('Error: Some products are unavailable', 400)

            # Clear existing order items
            # order.order_items.clear() // This will only dis-associate the child relationship from parents, leaving null in those columns which can lead to inconsistencies
            for item in order.order_items:
                db.session.delete(item)  # Permanently remove from the database

            # Add new order items
            for index, product in enumerate(products):
                order_item = OrderItem(
                    name=product.name,
                    slug=product.slug,
                    user_id=user.id,
                    price=product.price,
                    order_id=order.id,  # Ensure this is not None
                    product_id=product.id,
                    quantity=cart_items[index]['quantity'],
                    order=order,
                    user=user,
                    product=product,
                )
                order.order_items.append(order_item)

        # Commit the changes to the database
        db.session.commit()
        return success_response('Order updated successfully', data=order.get_summary(include_order_items=True))

    except Exception as e:
        db.session.rollback()  # Rollback in case of error
        traceback.print_exc()
        return error_response(f"An error occurred: {str(e)}", 500)

@order_bp.route('/orders/<int:order_id>', methods=['DELETE'])
@jwt_required(optional=True)
def delete_order(order_id):
    try:
        user = current_user
        order = Order.query.get(order_id)

        if order is None:
            return error_response('Order not found', 404)

        # Check if the user is allowed to delete the order
        if order.user_id != user.id and not user.is_admin:
            return error_response('Permission Denied: You cannot delete this order', 403)
        
        if len(order.order_items) > 0:
            for item in order.order_items:
                db.session.delete(item)  # remove associated order items from the database
                    
        db.session.delete(order)
        db.session.commit()
        return success_response('Order deleted successfully')

    except Exception as e:
        db.session.rollback()  # Rollback in case of error
        return error_response(f"An error occurred: {str(e)}", 500)
