from sqlalchemy import func
from web.apis.utils.custom_mixins import SearchableMixin
from web.extensions import db

products_pages = \
    db.Table(
        "products_pages",
        db.Column("page_id", db.Integer, db.ForeignKey("pages.id") ),
        db.Column("product_id", db.Integer, db.ForeignKey("products.id") )
        )

users_pages = \
    db.Table(
        "users_pages",
        db.Column("user_id", db.Integer, db.ForeignKey("users.id") ),
        db.Column("page_id", db.Integer, db.ForeignKey("pages.id") )
        )
class Page(db.Model, SearchableMixin):
    __tablename__ = 'pages'
    __searchable__ = ['name', 'username', 'email', 'phone', 'description']

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    username = db.Column(db.String(64), index=True, unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    avatar = db.Column(db.String(1000))
    email = db.Column(db.String(120), index=True, unique=True, nullable=False)
    valid_email = db.Column(db.Boolean(), index=True, nullable=False, default=False)
    phone = db.Column(db.String(120), index=True, unique=True)
    socials = db.Column(db.JSON, default=None)  # Socials: {'fb': '@chrisjsm', 'insta': '@chris', 'twit': '@chris', 'linkedin': '', 'whats': '@techa'}
    address = db.Column(db.JSON)  # Location: {'region': 'USA', 'city': 'London', 'street': 'Beach House, 27 California', 'zipcode': '1099990'}
    whats_app = db.Column(db.String(120), index=True, unique=True)
    bank = db.Column(db.JSON)  # Bank accounts: {'opay': 702656127, 'fcmb': 5913408010}
    password = db.Column(db.String(500), index=True, nullable=False)
    reviews = db.Column(db.Integer)

    is_deleted = db.Column(db.Boolean(), nullable=False, index=True, default=False)
    created_at = db.Column(db.DateTime, nullable=False, index=True, default=func.now())
    updated_at = db.Column(db.DateTime, nullable=False, default=func.now(), onupdate=func.now())

    # Relationships
    # user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    users = db.relationship('User', secondary=users_pages, lazy='dynamic', back_populates='pages')
    products = db.relationship('Product', secondary=products_pages, lazy='dynamic', back_populates='pages')

    def get_summary(self, include_products=False, include_roles=False, include_pages=False):
        """Generate a summary of the page instance."""
        data = {
            'id': self.id,
            'name': self.name,
            'avatar': self.avatar,
            'email': self.email,
            'phone': self.phone,
            'description': self.description,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
        }
        # Optionally include additional data based on flags (e.g., include products, roles, or pages)
        if include_products:
            data['products'] = [product.id for product in self.products]
        if include_roles:
            data['roles'] = [role.name for role in self.roles]
        if include_pages:
            data['pages'] = [page.id for page in self.pages]
        return data
      