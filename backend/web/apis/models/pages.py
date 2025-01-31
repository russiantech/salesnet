from sqlalchemy import func, or_
# from web.apis.utils.custom_mixins import SearchableMixin
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

pages_tags = db.Table(
    'pages_tags',
    db.Column('page_id', db.Integer, db.ForeignKey('pages.id')),
    db.Column('tag_id', db.Integer, db.ForeignKey('tags.id')),
    keep_existing=True
)

pages_categories = db.Table(
    'pages_categories',
    db.Column('page_id', db.Integer, db.ForeignKey('pages.id')),
    db.Column('category_id', db.Integer, db.ForeignKey('categories.id')),
    keep_existing=True
)


class Page(db.Model):
    __tablename__ = 'pages'
    __searchable__ = ['name', 'username', 'email', 'phone', 'description']

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    username = db.Column(db.String(64), index=True, unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    avatar = db.Column(db.String(1000))
    slug = db.Column(db.String(255), unique=True, index=True, nullable=False)
    email = db.Column(db.String(120), index=True, unique=True, nullable=False)
    valid_email = db.Column(db.Boolean(), index=True, nullable=False, default=False)
    phone = db.Column(db.String(120), index=True, unique=True)
    password = db.Column(db.String(500), index=True, nullable=False)
    image = db.Column(db.String(255))  # Optional image URL
    about_me = db.Column(db.Text)  # Additional information about the user
    balance = db.Column(db.Float, default=0.0)  # User's balance
    withdrawal_password = db.Column(db.String(500))  # Password for withdrawals
    socials = db.Column(db.JSON, default=None)  # Social media links
    address = db.Column(db.JSON)  # User's address details
    whats_app = db.Column(db.String(120), index=True, unique=True)
    bank = db.Column(db.JSON)  # Bank account details
    reviews = db.Column(db.Integer, default=0)  # Number of reviews received

    is_deleted = db.Column(db.Boolean(), nullable=False, index=True, default=False)
    created_at = db.Column(db.DateTime, nullable=False, index=True, default=func.now())
    updated_at = db.Column(db.DateTime, nullable=False, default=func.now(), onupdate=func.now())

    # Relationships
    users = db.relationship('User', secondary=users_pages, lazy='dynamic', back_populates='pages')
    products = db.relationship('Product', secondary=products_pages, lazy='dynamic', back_populates='pages')
    tags = db.relationship('Tag', secondary=pages_tags, back_populates='pages')
    categories = db.relationship('Category', secondary=pages_categories, back_populates='pages')

    @staticmethod
    def get_page(identifier: str):
        """
        Static method to fetch a page from the database by ID or slug.
        
        Args:
            identifier (str): The page ID or slug to search for.
        
        Returns:
            Page: The page object if found, otherwise None.
        
        Raises:
            ValueError: If the identifier is empty.
        """
        if not identifier:
            raise ValueError("Identifier cannot be empty")
        
        # Attempt to fetch the page by either ID or slug
        page = db.session.query(Page).filter(
            or_(Page.id == identifier, Page.slug == identifier)
        ).first()
        
        return page

    def get_summary(self, include_products=False, include_users=False):
        """Generate a summary of the page instance."""
        data = {
            'id': self.id,
            'name': self.name,
            'username': self.username,
            'avatar': self.avatar,
            'slug': self.slug,
            'email': self.email,
            'phone': self.phone,
            'description': self.description,
            'about_me': self.about_me,
            'balance': self.balance,
            'valid_email': self.valid_email,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
        }
        # Optionally include additional data based on flags
        if include_products:
            # data['products'] = [product.id for product in self.products]
            data['products'] = [product.get_summary() for product in self.products]
        if include_users:
            # data['roles'] = [role.name for role in self.roles]
            data['users'] = [user.get_summary() for user in self.roles]
        return data

from slugify import slugify
from sqlalchemy import event

@event.listens_for(Page.name, 'set')
def receive_set(target, value, oldvalue, initiator):
    target.slug = slugify(str(value))
