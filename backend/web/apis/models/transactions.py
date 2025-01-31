from sqlalchemy import func, or_
from web.extensions import db

class Transaction(db.Model):
    __tablename__ = 'transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=True)
    
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(255))
    currency = db.Column(db.String(3), nullable=False)
    payment_method = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), default='pending')
    refference = db.Column(db.String(100), unique=True, nullable=False)
    
    user = db.relationship('User', back_populates='transactions')
    order = db.relationship('Order', backref='transactions')  # Added backref for easier access
    product = db.relationship('Product', backref='transactions')  # Added backref for easier access
    
    is_deleted = db.Column(db.Boolean(), nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=func.now())
    updated_at = db.Column(db.DateTime, nullable=False, default=func.now(), onupdate=func.now())
    
    @staticmethod
    def get_transaction(refference: str):
        """
        Static method to fetch a transaction from the database by refference or transaction ID.
        
        Args:
            username (str): The refference or transaction ID or to search for.
        
        Returns:
            Transaction: The transaction object if found, otherwise None.
        
        Raises:
            ValueError: If the refference is empty.
        """
        if not refference:
            raise ValueError("refference cannot be empty")
        
        # Attempt to fetch the transaction by either username or transaction ID or email
        transaction = db.session.query(Transaction).filter(or_(Transaction.refference == refference, Transaction.id == refference)).first()
        
        return transaction

    def get_summary(self, include_user=False, include_order=False, include_product=False):
        """Return a summary of the transaction with optional details."""
        summary = {
            "id": self.id,
            "amount": self.amount,
            "currency": self.currency,
            "status": self.status,
            "description": self.description,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
        
        if include_user and self.user:
            summary['user'] = self.user.get_summary()
            # summary['user'] = {
            #     "id": self.user.id,
            #     "username": self.user.username,
            #     "email": self.user.email,
            #     "phone": self.user.phone
            # }
        
        if include_order and self.order:
            summary['order'] = self.order.get_summary()
            # summary['order'] = {
            #     "id": self.order.id,
            #     "amount": self.order.amount,
            #     "currency": self.order.currency,
            #     "status": self.order.status
            # }
        
        if include_product and self.product:
            summary['product'] = self.product.get_summary()
            # summary['product'] = {
            #     "id": self.product.id,
            #     "name": self.product.name,
            #     "price": self.product.price,
            #     "description": self.product.description
            # }
        
        return summary
