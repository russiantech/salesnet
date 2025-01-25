from sqlalchemy import func
from web.extensions import db

class Address(db.Model):
    __tablename__ = 'addresses'

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(140), nullable=False)
    last_name = db.Column(db.String(140), nullable=False)
    city = db.Column(db.String(140), nullable=False)
    country = db.Column(db.String(140), nullable=False)
    zip_code = db.Column(db.String(140), nullable=False)
    street_address = db.Column(db.String(140), nullable=False)
    phone_number = db.Column(db.String(140), nullable=True)  # nullable because I have not implemented it

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    user = db.relationship('User', backref='addresses')

    is_deleted = db.Column(db.Boolean(), nullable=False, default=False)
    created_at = db.Column(db.DateTime, index=True, nullable=False, default=func.now())
    updated_at = db.Column(db.DateTime, nullable=False, default=func.now(), onupdate=func.now())

    def get_summary(self, include_user=False):
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'address': self.street_address,
            'zip_code': self.zip_code,
            'city': self.city,
            'country': self.country,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }

        if include_user and self.user:
            # data['user'] = {'id': self.user_id, 'username': self.user.username}
            data['user'] = [user.get_summary() for user in self.user]

        return data
