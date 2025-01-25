# from datetime import datetime, timezone

from sqlalchemy import func
from web.extensions import db

users_roles = db.Table(
    'users_roles',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('role_id', db.Integer, db.ForeignKey('roles.id'), primary_key=True)
)

class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    description = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=func.now())
    users = db.relationship('User', secondary=users_roles, back_populates='roles')

    def get_summary(self, include_user=False):
        data = {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'created_at': self.created_at
        }
      
        if include_user:
            data['users'] = [ user.get_summary() for user in self.users ]
        
        return data
            

# # class Role(db.Model):
# #     __tablename__ = 'roles'
# #     id = db.Column(db.Integer, primary_key=True)
# #     name = db.Column(db.String(80), unique=True, nullable=False)
# #     description = db.Column(db.String(100), nullable=True)
# #     created_at = db.Column(db.DateTime, nullable=False,  default=datetime.now(timezone.utc))
# #     users = db.relationship('User', secondary="users_roles", back_populates='roles')
#     # user_roles = db.relationship("UserRole", back_populates="role", overlaps='user,users_roles')
#     # user_roles = db.relationship('UserRole', back_populates='role', overlaps='users')

# # class UserRole(db.Model):
# #     __tablename__ = 'users_roles'

# #     user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
# #     role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), primary_key=True)

# #     user = db.relationship('User', back_populates='user_roles', foreign_keys=[user_id])
# #     role = db.relationship('Role', back_populates='user_roles', foreign_keys=[role_id])

# #     created_at = db.Column(db.DateTime, nullable=False, default=datetime.now(timezone.utc))

# #     __mapper_args__ = {
# #         'primary_key': [user_id, role_id]
# #     }

# # users_roles = db.Table(
# #     'users_roles',
# #     db.Column('user_id', db.Integer, db.ForeignKey('users.id')),
# #     db.Column('role_id', db.Integer, db.ForeignKey('roles.id')),
# #     keep_existing=True
# # )


# # 

# class Role(db.Model):
#     __tablename__ = 'roles'
#     id = db.Column(db.Integer, primary_key=True)
#     name = db.Column(db.String(80), unique=True, nullable=False)
#     description = db.Column(db.String(100), nullable=True)
#     created_at = db.Column(db.DateTime, nullable=False,  default=func.now())

# class UserRole(db.Model):
#     __tablename__ = 'users_roles'

#     user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
#     role_id = db.Column(db.Integer, db.ForeignKey("roles.id"))

#     # users = db.relationship("User", foreign_keys=[user_id], backref='roles')
#     user = db.relationship("User", foreign_keys=[user_id], backref='users_roles')
#     role = db.relationship("Role", foreign_keys=[role_id], backref='users_roles')

#     created_at = db.Column(db.DateTime, nullable=False,  default=func.now())

#     __mapper_args__ = {'primary_key': [user_id, role_id]}


# users_roles = db.Table(
#     'users_roles',
#     db.Column('user_id', db.Integer, db.ForeignKey('users.id')),
#     db.Column('role_id', db.Integer, db.ForeignKey('roles.id')),
#     keep_existing=True
# )