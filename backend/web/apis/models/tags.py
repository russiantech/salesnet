from datetime import datetime

from slugify import slugify
from sqlalchemy import event, Column, Integer, ForeignKey, UniqueConstraint, func

from web.extensions import db

products_tags = db.Table(
    'products_tags',
    db.Column('product_id', db.Integer, db.ForeignKey('products.id')),
    db.Column('tag_id', db.Integer, db.ForeignKey('tags.id')),
    keep_existing=True
)

class Tag(db.Model):
    __tablename__ = 'tags'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True)
    slug = db.Column(db.String(140), index=True, unique=True)
    description = db.Column(db.String(140))
    
    is_deleted = db.Column(db.Boolean(), nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, index=True, default=func.now())
    updated_at = db.Column(db.DateTime, nullable=False, default=func.now(), onupdate=func.now())

    products = db.relationship('Product', secondary=products_tags, back_populates='tags')  # Specify back_populates
    pages = db.relationship('Page', secondary="pages_tags", back_populates='tags')  # Specify back_populates

    def __repr__(self):
        return self.name

    def get_summary(self, include_products=False):
        data = {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'image_urls': [image.file_path.replace('\\', '/') for image in self.images]
        }
        if self.products and include_products:
            data['products'] = [ product.get_summary() for product in self.products]

        return data
    
@event.listens_for(Tag.name, 'set')
def receive_set(target, value, oldvalue, initiator):
    target.slug = slugify(str(value))


class ProductTag(db.Model):
    __tablename__ = 'product_tags'

    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    tag_id = Column(Integer, ForeignKey("tags.id"), nullable=False)

    product = db.relationship("Product", foreign_keys=[product_id], backref='product_tags')
    tag = db.relationship("Tag", foreign_keys=[tag_id], backref='product_tags')

    __mapper_args__ = {'primary_key': [product_id, tag_id]}
    __table_args__ = (UniqueConstraint('product_id', 'tag_id', name='same_tag_for_same_product'),)
