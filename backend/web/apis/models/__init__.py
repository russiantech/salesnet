from web.extensions import db
from sqlalchemy import func

class BaseModel(db.Model):
    id = db.Column(db.Integer, index=True, primary_key=True)
    is_deleted = db.Column(db.Boolean(), nullable=False, default=False)
    created_at = db.Column(db.DateTime, index=True, nullable=False, default=func.now())
    updated_at = db.Column(db.DateTime, nullable=False, default=func.now(), onupdate=func.now())

    def get_or_default(self, ident, default=None):
        return self.get(ident) or default

# from web.models.* import *
# web/apis/models/__init__.py
from .addresses import Address
from .products import Product
from .pages import Page, products_pages, users_pages
from .users import User
from .baskets import Basket
from .favorites import Favorite
from .comments import Comment
from .file_uploads import FileUpload, TagImage, CategoryImage, ProductImage
from .orders import Order, OrderItem
from .roles import Role, users_roles #, UserRole
from .tags import Tag, ProductTag, products_tags
from .chats import Chat
from .categories import Category, products_categories
from .transactions import Transaction

__all__ = [
    
    "Address",
    "Product",
    
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
    # "UserRole",
    "users_roles",
    
    "Tag",
    "ProductTag",
    "products_tags",
    
    "Chat",
    
    "Category",
    "products_categories",
    
    "Transaction"
]



# web/models/__init__.py
# import importlib
# import os

# # def load_models():
# #     package = os.path.dirname(__file__)
# #     for module in os.listdir(package):
# #         if module.endswith('.py') and module != '__init__.py':
# #             importlib.import_module(f"web.models.{module[:-3]}")


# # def load_models():
# #     package = os.path.dirname(__file__)
# #     for module in os.listdir(package):
# #         if module.endswith('.py') and module != '__init__.py':
# #             try:
# #                 importlib.import_module(f"web.models.{module[:-3]}")
# #             except Exception as e:
# #                 print(f"Error importing {module}: {e}")

# # load_models()