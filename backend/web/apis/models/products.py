from slugify import slugify
from sqlalchemy import event, func, or_
from sqlalchemy.orm import relationship

from web.extensions import db
from web.apis.models.users import products_users
from web.apis.models.categories import products_categories
from web.apis.models.tags import products_tags
from web.apis.models.pages import products_pages

class Product(db.Model):
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    # slug = db.Column(db.String, index=True, unique=True)
    slug = db.Column(db.String(255), unique=True, index=True, nullable=False)
    description = db.Column(db.Text, nullable=False)

    price = db.Column(db.Integer, nullable=False)
    stock = db.Column(db.Integer, nullable=False)

    publish_on = db.Column(db.DateTime, index=True, default=func.now())
    is_deleted = db.Column(db.Boolean(), nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=func.now())
    updated_at = db.Column(db.DateTime, nullable=False, default=func.now(), onupdate=func.now())

    users = db.relationship('User', secondary=products_users, lazy='dynamic', back_populates='products')
    pages = db.relationship('Page',  secondary=products_pages, lazy='dynamic', back_populates='products')
    tags = relationship('Tag', secondary=products_tags, back_populates='products')
    categories = relationship('Category', secondary=products_categories, back_populates='products')
    comments = relationship('Comment', back_populates='product', lazy='dynamic')
    images = relationship('ProductImage', back_populates='product', lazy='dynamic')
    
    def __repr__(self):
        return '<Product %r>' % self.name
    
    @staticmethod
    def get_product(identifier: str):
        """
        Static method to fetch a product from the database by ID or slug.
        
        Args:
            identifier (str): The product ID or slug to search for.
        
        Returns:
            Product: The product object if found, otherwise None.
        
        Raises:
            ValueError: If the identifier is empty.
        """
        if not identifier:
            raise ValueError("Identifier cannot be empty")
        
        # Attempt to fetch the product by either ID or slug
        product = db.session.query(Product).filter(
            or_(Product.id == identifier, Product.slug == identifier)
        ).first()
        
        return product

    def get_summary(self, include_user=False, include_page=False):
        data = {
            'id': self.id,
            # 'user_id': self.users.id if self.users else None,
            'name': self.name,
            'price': self.price,
            'stock': self.stock,
            'slug': self.slug,
            'comments_count': self.comments.count(),
            'tags': [{'id': t.id, 'name': t.name} for t in self.tags],
            'categories': [{'id': c.id, 'name': c.name} for c in self.categories],
            # 'image_urls': [i.file_path for i in self.images],
            'image_urls': [ image.file_path.replace('\\', '/') for image in self.images ] if self.images else None,
        }
        
        if include_user and self.users:
            data['users'] = [ user.get_summary() for user in self.users]
            
        if include_page and self.pages:
            data['pages'] = [ page.get_summary() for page in self.pages]
            
        return data


@event.listens_for(Product.name, 'set')
def receive_set(target, value, oldvalue, initiator):
    target.slug = slugify(str(value))