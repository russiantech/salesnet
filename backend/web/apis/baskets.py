from flask import request, jsonify, session
# from flask_jwt_extended import create_access_token, jwt_optional, get_jwt_identity
from flask_jwt_extended import jwt_required, get_jwt_identity

from web.apis.models.products import Product

from flask import Blueprint
basket_bp = Blueprint("basket_api", __name__)
        

@basket_bp.route('/basket/<string:action>', methods=['GET', 'POST'])
def basket(action):
    
    item_id = str(request.args.get('item', ''))
    qty = int(request.args.get('qty', 1))
    
    basket = session.get('basket', {})

    try:
        if action == 'save':
            if Product.exists(item_id):
                basket[item_id] = basket.get(item_id, 0) + qty
                session['basket'] = basket
                session.modified = True
                return jsonify(message="Success, You've Added To Your Shopping Basket"), 200
            return jsonify(message="Failed! This Item Is Not Found"), 404
        
        elif action == 'update':
            if item_id in basket:
                basket[item_id] = qty
                session['basket'] = basket
                session.modified = True
                return jsonify(message="Success, You've Updated Your Shopping Basket"), 200
            elif Product.exists(item_id):
                basket[item_id] = qty
                session['basket'] = basket
                session.modified = True
                return jsonify(message="Success, You've Added And Updated Your Shopping Basket"), 200
            return jsonify(message="Failed, Unable To Update Your Shopping Basket"), 404
        
        elif action == 'remove':
            if item_id in basket:
                del basket[item_id]
                session['basket'] = basket
                session.modified = True
                return jsonify(message="Success, You've Removed An Item From Your Cart"), 200
            return jsonify(message="Sorry, Unable To Remove The Item From Your Shopping Cart"), 404
        
        elif action == 'wipe':
            session.pop('basket', None)
            session.modified = True
            return jsonify(message="You've Emptied Your Shopping Basket"), 200
        
        elif action == 'fetch':
            if not basket:
                return jsonify(message="Empty shopping basket"), 200

            items = Product.query.filter(Product.id.in_(basket.keys())).all()
            sub_total = sum(item.price * int(basket[str(item.id)]) for item in items)
            item_count = len(items)
            basket_items = [
                {
                    'item': item.id,
                    'name': item.name,
                    'image': item.photos,
                    'qty': basket[str(item.id)],
                    'price': item.price,
                    'total_each': item.price * int(basket[str(item.id)]),
                    'attr': item.attributes[0],
                }
                for item in items
            ]
            return jsonify(basket=basket_items, sub_total=sub_total, item_count=item_count), 200
        
        else:
            return jsonify(message="Invalid action"), 400

    except Exception as e:
        return jsonify(message=str(e)), 500
