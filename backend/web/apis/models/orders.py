'''
import enum
from apis.shared.columns import ColIntEnum

# https://www.michaelcho.me/product/using-python-enums-in-sqlalchemy-models
class OrderStatus(enum.IntEnum):
    processed = 1
    image = 2
    audio = 3
    reply = 4
    unknown = 5
'''
from sqlalchemy import func
from sqlalchemy.orm import relationship
from web.extensions import db

ORDER_STATUS = ['processed', 'shipped', 'in transit', 'delivered']

class Order(db.Model):
    __tablename__ = 'orders'

    id = db.Column(db.Integer, primary_key=True)
    # order_status = db.Column(ColIntEnum(OrderStatus), default=OrderStatus.text)
    order_status = db.Column(db.Integer)
    tracking_number = db.Column(db.String(140))

    address_id = db.Column(db.Integer, db.ForeignKey('addresses.id'), nullable=False)
    address = db.relationship('Address', backref='orders', lazy=False)

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    user = db.relationship('User', backref='orders')

    is_deleted = db.Column(db.Boolean(), nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=func.now())
    updated_at = db.Column(db.DateTime, nullable=False, default=func.now(), onupdate=func.now())

    def get_summary(self, include_order_items=False, include_users=False):
        dto = {
            'id': self.id,
            'user_id': self.user_id or None,
            'order_status': ORDER_STATUS[self.order_status],
            'tracking_number': self.tracking_number,
            'order_items_count': len(self.order_items) if self.order_items else 0,
            # Please notice how we retrieve the count, through len(), instead of count()
            # as we did in Product.get_summary() for comments, why? we declared the association in different places
            'address_id': self.address_id,
            'address': self.address.get_summary()
        }

        if include_order_items and self.order_items:
            dto['order_items'] = [oi.get_summary() for oi in self.order_items]
            
        if include_users and self.user:
            # dto['users'] = [user.get_summary() for user in self.user ]
            if isinstance(self.user, list):  # Check if self.user is a list (or other iterable)
                dto['users'] = [user.get_summary() for user in self.user]
            else:  # If it's a single user object
                dto['users'] = [self.user.get_summary()]


        return dto


class OrderItem(db.Model):
    __tablename__ = 'order_items'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(140), index=True, nullable=False)
    slug = db.Column(db.String(140))
    price = db.Column(db.Integer, index=True, nullable=False)
    quantity = db.Column(db.Integer, index=True, nullable=False)

    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    order = db.relationship('Order', backref='order_items')

    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    product = db.relationship('Product', backref='order_items')

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    user = db.relationship('User', backref='products_bought')

    is_deleted = db.Column(db.Boolean(), nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=func.now())
    updated_at = db.Column(db.DateTime, nullable=False, default=func.now(), onupdate=func.now())
    
    def get_summary(self):
        return {
            'name': self.name, 'slug': self.slug,
            'product_id': self.product_id,
            'price': self.price, 
            'quantity': self.quantity
        }