from datetime import datetime

from sqlalchemy import Column

from web.extensions import db

users_roles = db.Table(
    'users_roles',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id')),
    db.Column('role_id', db.Integer, db.ForeignKey('roles.id')),
    # keep_existing=True
     extend_existing=True 
)
# users_roles = db.Table(
#     'users_roles',
#     db.Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
#     db.Column('role_id', Integer, ForeignKey('roles.id'), primary_key=True),
#     extend_existing=True  # Add this line
# )

class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    description = db.Column(db.String(100), nullable=True)
    created_at = Column(db.DateTime, nullable=False, default=datetime.utcnow)
    users = db.relationship('User', secondary=users_roles, back_populates='roles')

class UserRole(db.Model):
    __tablename__ = 'users_roles'

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    role_id = db.Column(db.Integer, db.ForeignKey("roles.id"))

    # users = db.relationship("User", foreign_keys=[user_id], backref='roles')
    user = db.relationship("User", foreign_keys=[user_id], backref='users_roles')
    role = db.relationship("Role", foreign_keys=[role_id], backref='users_roles')

    created_at = Column(db.DateTime, nullable=False, default=datetime.utcnow)
    __mapper_args__ = {'primary_key': [user_id, role_id]}
