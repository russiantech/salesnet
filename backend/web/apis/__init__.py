""" import os

from flask import jsonify, send_from_directory

# from web.apis.ecommerce_api.factory import app

@app.route("/routes")
def site_map():
    links = []
    # for rule in app.url_map.iter_rules():
    for rule in app.url_map._rules:
        # Filter out rules we can't navigate to in a browser
        # and rules that require parameters
        links.append({'url': rule.rule, 'view': rule.endpoint})
    return jsonify(links), 200


# @app.route('/api/images/<path:path>')
def send_js(path):
    basedir = os.path.join(os.path.realpath(os.getcwd()), 'static', 'bellerin.png')
    if os.path.exists(basedir):
        return app.send_static_file(basedir)
    return send_from_directory('images', path)
 """
 
# import web.apis.user
# import sys
# sys.stdout.write('[+] Registering routes for user\n')

from flask import Blueprint, make_response
from web.apis.utils.serializers import error_response, success_response
api_bp = Blueprint('apis', __name__)

# from datetime import datetime, timezone
# from flask import g
# from flask_jwt_extended import current_user, jwt_required, get_jwt
# @api_bp.before_request
# @jwt_required(optional=True)
# def refresh_token_if_needed():
#     jwt_data = get_jwt()
#     exp = jwt_data.get('exp')  # Use get to avoid KeyError

#     if exp is None:
#         # Handle the case where 'exp' is missing
#         return error_response("Token does not contain expiration time.", 401)

#     current_time = datetime.now(timezone.utc).timestamp()

#     # Check if the token is about to expire in the next 5 minutes
#     if exp - current_time < 300:  # 5 minutes
#         access_token = current_user.make_token(token_type='access', fresh=True)
#         refresh_token = current_user.make_token(token_type='refresh')

#         # Create response object
#         response = make_response(
#             success_response(
#                 "Re-authentication successful", 
#                 data={"access_token": access_token}
#             )
#         )

#         # Set cookies for web clients
#         response.set_cookie('access_token', access_token, httponly=True, secure=True, samesite='Strict')
#         response.set_cookie('refresh_token', refresh_token, httponly=True, secure=True, samesite='Strict')
#         g.response = response

#     # Allow the request to proceed

# from web.models.* import *
# web/apis/models/__init__.py
from . import products
from . import pages
from . import users
from . import baskets
from . import orders
from . import addresses
from . import favorites
from . comments                                                                                                                                     import Comment
# from .file_uploads import FileUpload, TagImage, CategoryImage, ProductImage
# from .orders import Order, OrderItem
from . import roles
from . import tags 
# from .tags import Tag, ProductTag, products_tags
from . import chats
# from .categories import Category, products_categories
from . import categories
# from .transactions import Transaction

__all__ = [
    
    "users",
    "products",
    "basket",
    
    "addresses",
    "product",
    
    "Page",
    "products_pages",
    "users_pages",
    
    "User",
    "Basket",
    "Favorite",
    "Comment",
    
    "FileUpload",
    "TagImage",
    "CategoryImage",
    "ProductImage",
    
    "Order",
    "OrderItem",
    
    "Role",
    "UserRole",
    "users_roles",
    
    "Tag",
    "ProductTag",
    "products_tags",
    
    "Chat",
    
    "Category",
    "products_categories",
    
    "Transaction"
    
]
