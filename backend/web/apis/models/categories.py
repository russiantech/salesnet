from slugify import slugify
from sqlalchemy import event, func
from sqlalchemy.orm import backref, validates
from web.extensions import db

# from apis.ecommerce_api.factory import db
# from apis.products.models import products_categories

products_categories = \
    db.Table(
        "products_categories",
        db.Column("category_id", db.Integer, db.ForeignKey("categories.id")),
        db.Column("product_id", db.Integer, db.ForeignKey("products.id"))
        )

class Category(db.Model):
    __tablename__ = 'categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(140), unique=True)
    slug = db.Column(db.String(140), index=True, unique=True)
    description = db.Column(db.String(255))
    
    is_deleted = db.Column(db.Boolean(), nullable=False, default=False)
    created_at = db.Column(db.DateTime, index=True, nullable=False, default=func.now())
    updated_at = db.Column(db.DateTime, nullable=False, default=func.now(), onupdate=func.now())
    
    products = db.relationship('Product', secondary=products_categories, lazy='dynamic', back_populates='categories')
    # Self-referential relationship + nested categorization using same table.
    parent_id = db.Column(db.Integer, db.ForeignKey('categories.id'), index=True, nullable=True)
    parent = db.relationship('Category', remote_side=[id], backref=backref('children', lazy='dynamic'))
    
    @validates('parent_id')
    def validate_parent(self, key, parent_id):
        if parent_id is not None and parent_id == self.id:
            raise ValueError("A category cannot be its own parent.")
        
        # Check for circular references
        current = self
        while current.parent:
            if current.parent.id == self.id:
                raise ValueError("Circular reference detected.")
            current = current.parent
        
        return parent_id

    # def get_summary(self, include_products=None):
    #     data = {
    #         'id': self.id,
    #         'parent_id': self.parent_id,
    #         'name': self.name,
    #         'description': self.description,
    #         'image_urls': [image.file_path.replace('\\', '/') for image in self.images] if self.images else None,
    #         'children': [child.get_summary() for child in self.children] if self.children else None,
    #         'parent': self.parent.get_summary() if self.parent else None  # Changed here
    #     }
        
    #     if include_products and self.products:
    #         data['products'] = [product.get_summary() for product in self.products]
        
    #     return data

    def get_summary(self, include_products=None, depth=0, max_depth=5):
        data = {
            'id': self.id,
            'parent_id': self.parent_id,
            'name': self.name,
            'description': self.description,
            'image_urls': [image.file_path.replace('\\', '/') for image in self.images] if self.images else None,
            'children': [child.get_summary(depth=depth + 1, max_depth=max_depth) for child in self.children] if self.children else None,
            'parent': self.parent.get_summary(depth=depth + 1, max_depth=max_depth) if self.parent and depth < max_depth else None
        }
        
        if include_products and self.products:
            data['products'] = [product.get_summary() for product in self.products]
        
        return data

    
    def __repr__(self):
        return self.name

@event.listens_for(Category.name, 'set')
def receive_set(target, value, oldvalue, initiator):
    target.slug = slugify(value)  # Removed unicode() as it is not necessary in Python 3



