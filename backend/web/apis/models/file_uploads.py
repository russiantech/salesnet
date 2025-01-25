from sqlalchemy import func
from web.extensions import db

class FileUpload(db.Model):
    __tablename__ = 'file_uploads'
    id = db.Column('id', db.Integer, primary_key=True)
    type = db.Column('type', db.String(15))  # this will be our discriminator

    file_path = db.Column(db.String(140), nullable=False)
    file_name = db.Column(db.String(140), nullable=False)
    file_size = db.Column(db.Integer, nullable=False)
    original_name = db.Column(db.String(140), nullable=False)

    is_deleted = db.Column(db.Boolean(), nullable=False, index=True, default=False)
    created_at = db.Column(db.DateTime, nullable=False, index=True, default=func.now())
    updated_at = db.Column(db.DateTime, nullable=False, default=func.now(), onupdate=func.now())
    
    __mapper_args__ = {
        'polymorphic_on': type,
        'polymorphic_identity': 'FileUpload'
    }


class TagImage(FileUpload):
    tag_id = db.Column(db.Integer, db.ForeignKey('tags.id'), nullable=True)
    tag = db.relationship('Tag', backref='images')

    # Comments below have all been inherited from FileUpload
    # is_deleted = db.Column(db.Boolean(), nullable=False, index=True, default=False)
    # created_at = db.Column(db.DateTime, nullable=False, index=True, default=func.now())
    # updated_at = db.Column(db.DateTime, nullable=False, default=func.now(), onupdate=func.now())
    
    __mapper_args__ = {
        'polymorphic_identity': 'TagImage'
    }


class ProductImage(FileUpload):
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=True)
    product = db.relationship('Product', back_populates='images')
    
     # Comments below have all been inherited from FileUpload
    # is_deleted = db.Column(db.Boolean(), nullable=False, index=True, default=False)
    # created_at = db.Column(db.DateTime, nullable=False, index=True, default=func.now())
    # updated_at = db.Column(db.DateTime, nullable=False, default=func.now(), onupdate=func.now())

    __mapper_args__ = {
        'polymorphic_identity': 'ProductImage'
    }


class CategoryImage(FileUpload):
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    category = db.relationship('Category', backref='images')

    #  # Comments below have all been inherited from FileUpload
    # is_deleted = db.Column(db.Boolean(), nullable=False, index=True, default=False)
    # created_at = db.Column(db.DateTime, nullable=False, index=True, default=func.now())
    # updated_at = db.Column(db.DateTime, nullable=False, default=func.now(), onupdate=func.now())
    
    __mapper_args__ = {
        'polymorphic_identity': 'CategoryImage'
    }
