class Product(db.Model):
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    slug = db.Column(db.String, index=True, unique=True)
    description = db.Column(db.Text, nullable=False)

    price = db.Column(db.Integer, nullable=False)
    stock = db.Column(db.Integer, nullable=False)

    created_at = db.Column(db.DateTime(), default=datetime.utcnow, index=True, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    publish_on = db.Column(db.DateTime, index=True, default=datetime.utcnow)

    tags = relationship('Tag', secondary=products_tags, backref='products')
    categories = relationship('Category', secondary=products_categories, backref='products')

    comments = relationship('Comment', backref='product', lazy='dynamic')