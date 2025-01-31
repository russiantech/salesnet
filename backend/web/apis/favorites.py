import traceback
from flask import request, session
from flask_jwt_extended import current_user, jwt_required
from web.apis.models.products import Product
from web.apis.models.users import User
from web.apis.utils.serializers import PageSerializer, error_response, success_response
from web.extensions import db
from web.apis.models.favorites import Favorite
from web.apis import api_bp as basket_bp

@basket_bp.route('/favorite', methods=['GET'])
@jwt_required(optional=True)
def get_favorite():
    """Retrieve favorite items for a user, either from the database (authenticated users) or session (non-authenticated users)."""
    user_id = request.args.get('user_id') or (current_user.id if current_user else None)
    try:
        if user_id:
            # Authenticated user: retrieve favorites from the database
            user = User.get_user(user_id)
            if not user:
                return error_response(f"User <{user_id}> not found.", status_code=404)

            # favorites = Favorite.query.filter_by(user_id=user_id).all()
            page = request.args.get('page', 1, type=int)  # Default to page 1
            per_size = request.args.get('page_size', 10, type=int)  # Default to 10 items per page
            favorites = Favorite.query.filter_by(user_id=user_id).paginate(page=page, per_page=per_size, error_out=False)

            # data = PageSerializer(items=favorites.items, resource_name='favorites').get_data()
            
            if favorites:
                # data = PageSerializer(pagination_obj=favorites, resource_name='favorites').get_data()
                data = PageSerializer(items=favorites.items, resource_name='favorites').get_data()
                return success_response('Favorite products fetched successfully.', data=data, status_code=200)

            return success_response('No favorite products found.', {'favorites': []}, status_code=200)
        else:
            # Non-authenticated user: retrieve favorites from the session
            favorite = session.get('favorite', [])
            return success_response('Favorite products fetched successfully (guest).', {'favorites': favorite}, status_code=200)
    except Exception as e:
        traceback.print_exc()
        return error_response(f"Error retrieving favorite products: {str(e)}", status_code=500)

@basket_bp.route('/favorite', methods=['POST'])
@jwt_required(optional=True)
def add_favorite():
    """Add a product to the user's favorites. Supports both authenticated and non-authenticated users."""
    user_id = request.args.get('user_id', request.json.get('user_id')) or (current_user.id if current_user else None)
    product_id = request.json.get('product_id')

    if not product_id:
        return error_response("Product ID is required.", status_code=400)

    try:
        product = Product.get_product(product_id)
        if not product:
            return error_response(f"Product <{product_id}> not found.", status_code=404)

        if user_id:
            # Authenticated user: store in the database
            user = User.get_user(user_id)
            if not user:
                return error_response(f"User <{user_id}> not found.", status_code=404)

            favorite = Favorite.query.filter_by(user_id=user_id, product_id=product_id).first()
            if not favorite:
                favorite = Favorite(user_id=user_id, product_id=product_id)
                db.session.add(favorite)
                db.session.commit()
            
            return success_response('Product added to favorites successfully.', status_code=201)
        else:
            # Non-authenticated user: store in session
            favorite = session.get('favorite', [])
            if product_id not in favorite:
                favorite.append(product_id)
                session['favorite'] = favorite

            return success_response('Product added to favorites successfully (guest).', status_code=201)
    except Exception as e:
        return error_response(f"Error adding product to favorites: {str(e)}", status_code=500)

@basket_bp.route('/favorite/<int:product_id>', methods=['DELETE'])
@jwt_required(optional=True)
def remove_favorite(product_id):
    """Remove a product from the user's favorites."""
    user_id = request.args.get('user_id') or (current_user.id if current_user else None)

    try:
        if user_id:
            # Authenticated user: remove from the database
            user = User.get_user(user_id)
            if not user:
                return error_response(f"User <{user_id}> not found.", status_code=404)

            favorite = Favorite.query.filter_by(user_id=user_id, product_id=product_id).first()
            if favorite:
                db.session.delete(favorite)
                db.session.commit()
                return success_response('Product removed from favorites successfully.', status_code=200)

            return error_response(f"Product <{product_id}> not found in your <{user.username}> favorites.", status_code=404)
        else:
            # Non-authenticated user: remove from session
            favorite = session.get('favorite', [])
            if product_id in favorite:
                favorite.remove(product_id)
                session['favorite'] = favorite
                return success_response('Product removed from favorites successfully (guest).', status_code=200)

            return error_response(f"Product <{product_id}> not found in favorites (guest).", status_code=404)
    except Exception as e:
        return error_response(f"Error removing product from favorites: {str(e)}", status_code=500)