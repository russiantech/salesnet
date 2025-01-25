
from sqlalchemy import func
from web.extensions import db

class Comment(db.Model):
    __tablename__ = 'comments'

    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    rating = db.Column(db.Integer, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    # user = db.relationship('User', backref=db.backref('comments'))
    user = db.relationship('User', back_populates='comments')
    user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id', ondelete='CASCADE'),  # Database-level ON DELETE CASCADE
        nullable=False
    )
    
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    product = db.relationship('Product', back_populates='comments')

    is_deleted = db.Column(db.Boolean(), nullable=False, index=True, default=False)
    created_at = db.Column(db.DateTime, nullable=False, index=True, default=func.now())
    updated_at = db.Column(db.DateTime, nullable=False, default=func.now(), onupdate=func.now())

    def get_summary(self, include_product=False, include_user=False):
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'content': self.content,
            'rating': self.rating,
            'created_at': self.created_at,
        }

        if include_product and self.product:
            data['product'] = self.product.get_summary()
            # data['product'] = {
            #     'id': self.product.id,
            #     'slug': self.product.slug,
            #     'name': self.product.name
            # }

        if include_user and self.user:
            data['user'] = self.user.get_summary()
            # data['user'] = {
            #     'id': self.user_id,
            #     'username': self.user.username
            # }
        return data
