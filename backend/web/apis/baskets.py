from flask import request, session
from flask_jwt_extended import current_user, jwt_required
from web.apis.models.products import Product
from web.apis.models.users import User
from web.apis.utils.serializers import PageSerializer, error_response, success_response
from web.extensions import db
from web.apis.models.baskets import Basket, BasketItem
from web.apis import api_bp as basket_bp

@basket_bp.route('/basket', methods=['GET'])
@jwt_required(optional=True)
def get_basket():
    # Get user_id from query parameters or default to current_user.id if authenticated
    user_id = request.args.get('user_id') or (current_user.id if current_user else None)
    try:
        if user_id:
            # Authenticated user: retrieve from database
            basket = Basket.query.filter_by(user_id=user_id).first()
            # print(basket.basket_items)
            if basket:
                serializer = PageSerializer(items=basket.basket_items, resource_name='basket_items')
                return success_response('Basket fetched successfully', serializer.get_data(), 200)
            return success_response('Basket is empty', {'basket_items': []}, 200)
        else:
            # Non-authenticated user: retrieve from session
            basket = session.get('basket', [])
            return success_response('Basket fetched successfully', {'basket_items': basket}, 200)
    except Exception as e:
        return error_response(f"Error retrieving basket: {str(e)}", status_code=500)

@basket_bp.route('/basket', methods=['POST'])
@jwt_required(optional=True)
def add_to_basket():
    # Get user_id from query parameters or default to current_user.id if authenticated
    user_id = request.args.get('user_id') or (current_user.id if current_user else None)
    product_id = request.json.get('product_id')
    quantity = request.json.get('quantity', 1)

    try:
        
        product = Product.get_product(product_id)
        if not product:
            return error_response(f"Product <{product_id}> not found.", status_code=404)
        
        if user_id:
            # Authenticated user
            user = User.get_user(user_id)
            if not user:
                return error_response(f"User <{user_id}> not found.", status_code=404)
            
            basket = Basket.query.filter_by(user_id=user.id).first()
            
            if not basket:
                basket = Basket(user_id=user.id)
                db.session.add(basket)
                db.session.commit()

            # Check if item already exists in basket
            basket_item = BasketItem.query.filter_by(basket_id=basket.id, product_id=product_id).first()
            if basket_item:
                basket_item.quantity += quantity
            else:
                basket_item = BasketItem(basket_id=basket.id, product_id=product_id, quantity=quantity)
                db.session.add(basket_item)

            db.session.commit()
            return success_response('Item added to basket successfully', status_code=201)
        else:
            # Non-authenticated user
            if 'basket' not in session:
                session['basket'] = []

            # Check if item already exists in session basket
            existing_item = next((item for item in session['basket'] if item['product_id'] == product_id), None)
            if existing_item:
                existing_item['quantity'] += quantity
            else:
                session['basket'].append({'product_id': product_id, 'quantity': quantity})

            return success_response('Item added to session basket successfully', status_code=201)
    except Exception as e:
        return error_response(f"Error adding item to basket: {str(e)}", status_code=500)

@basket_bp.route('/basket/<int:product_id>', methods=['DELETE'])
@jwt_required(optional=True)
def remove_from_basket(product_id):
    # Get user_id from query parameters or default to current_user.id if authenticated
    user_id = request.args.get('user_id') or (current_user.id if current_user else None)
    try:
        if user_id:
            # Authenticated user
            basket = Basket.query.filter_by(user_id=user_id).first()
            if basket:
                basket_item = BasketItem.query.filter_by(basket_id=basket.id, product_id=product_id).first()
                if basket_item:
                    db.session.delete(basket_item)
                    db.session.commit()
                    return success_response('Item removed from basket successfully', status_code=200)
                return error_response(f'Item <{product_id}> not found in basket', status_code=404)
            return error_response('Basket not found', status_code=404)
        else:
            # Non-authenticated user
            if 'basket' in session:
                session['basket'] = [item for item in session['basket'] if item['product_id'] != product_id]
                return success_response('Item removed from session basket successfully', status_code=200)
            return error_response('No items in basket', status_code=404)
    except Exception as e:
        return error_response(f"Error removing item from basket: {str(e)}", status_code=500)