from sqlalchemy import CheckConstraint, Enum, func
from web.extensions import db

# class Chat(db.Model):
#     __tablename__ = 'chats'
#     id = db.Column(db.Integer, primary_key=True, autoincrement=True)
#     text = db.Column(db.Text)
#     media_url = db.Column(db.String(140))  # This is the correct column name
#     sticker = db.Column(db.String(140))
#     last_seen = db.Column(db.DateTime)
#     seen = db.Column(db.Boolean)
#     from_deleted = db.Column(db.Boolean, nullable=False)
#     to_deleted = db.Column(db.Boolean, nullable=False)
#     reply_on_id = db.Column(db.Integer, db.ForeignKey('chats.id'))
#     group_id = db.Column(db.Integer, db.ForeignKey('groups.id'), nullable=False)
#     user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
#     is_deleted = db.Column(db.Boolean, nullable=False)
#     created_at = db.Column(db.DateTime, nullable=False, default=func.now())
#     updated_at = db.Column(db.DateTime, nullable=False, default=func.now(), onupdate=func.now())

#     __table_args__ = (
#         db.CheckConstraint('text IS NOT NULL OR sticker IS NOT NULL OR media_url IS NOT NULL', name='at_least_one_content_check'),
#     )

class Chat(db.Model):
    __tablename__ = 'chats'

    id = db.Column(db.Integer, unique=True, primary_key=True, nullable=False)
    text = db.Column(db.Text)
    media_url = db.Column(db.String(140))
    sticker = db.Column(db.String(140))
    last_seen = db.Column(db.DateTime(timezone=True), default=func.now())
    seen = db.Column(db.Boolean, default=False)

    from_deleted = db.Column(db.Boolean(), default=False, nullable=False)
    to_deleted = db.Column(db.Boolean(), default=False, nullable=False)

    reply_on_id = db.Column(db.Integer, db.ForeignKey('chats.id'), nullable=True)  # Optional reference to another message
    reply_on = db.relationship('Chat', remote_side=[id], backref='replies')
    
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    users = db.relationship('User', back_populates='chats')

    is_deleted = db.Column(db.Boolean(), nullable=False, index=True, default=False)
    created_at = db.Column(db.DateTime, nullable=False, index=True, default=func.now())
    updated_at = db.Column(db.DateTime, nullable=False, default=func.now(), onupdate=func.now())

    # __table_args__ = (
    #     db.CheckConstraint(
    #         'text IS NOT NULL OR sticker IS NOT NULL OR media_url IS NOT NULL', 
    #         name='at_least_one_content_check'),
    # )
    __table_args__ = (
        CheckConstraint(
            "text IS NOT NULL OR sticker IS NOT NULL OR media_url IS NOT NULL",
            name="at_least_one_content_check",
        ),
    )

    def __repr__(self):
        return '<Chat {}>'.format(self.text)
    # Remember to define the relationship between the `Chat` and `User` models.

    def get_summary(self, include_user=False):
        data = {
            'id': self.id,
            'text': self.text if self.text else '',
            'sticker': self.sticker,
            'media': self.media_url,
            'last_seen': self.last_seen.isoformat() + 'Z' if self.last_seen is not None else None,
            # 'last_message': self.text if self.text and self.recent else None,
            'from_deleted': self.from_deleted,
            'to_deleted': self.to_deleted,
            'created_at': self.created_at.isoformat() + 'Z' if self.created_at is not None else None,
            'updated_at': self.updated_at.isoformat() + 'Z' if self.updated_at is not None else None,
        }

        if include_user:
            data['user'] = self.user.get_summary()

        return data

# UserGroup model (for many-to-many relationship between User and Group)
user_group = db.Table('user_group',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('group_id', db.Integer, db.ForeignKey('groups.id'), primary_key=True),
    db.Column('role', db.String(20), nullable=False, default='member')  # Role field
)

class Group(db.Model):
    __tablename__ = 'groups'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(255))
    is_private = db.Column(db.Boolean(), default=False)  # Indicates if the group is private
    group_type = db.Column(Enum('one_on_one', 'multi_user'), default='one_on_one')
    created_at = db.Column(db.DateTime, nullable=False, default=func.now())
    updated_at = db.Column(db.DateTime, nullable=False, default=func.now(), onupdate=func.now())
    
    users = db.relationship('User', secondary='user_group', back_populates='groups')
    chats = db.relationship('Chat', backref='group', lazy=True)
    
    __table_args__ = (
        db.UniqueConstraint('id', 'name', 'description', name='uq_id_name_description'),
    )
        
    @staticmethod
    def create_group(users, name=None, description=None, is_private=True):
        """Create a chat group for the given users."""
        if not users:
            raise ValueError("At least one user must be provided.")

        # Check for duplicates and valid users
        unique_users = set(users)  # Remove duplicates
        if len(unique_users) != len(users):
            raise ValueError("Duplicate users are not allowed.")

        # Create the new group
        new_group = Group(name=name, description=description, is_private=is_private)
        
        # Add users to the group
        for user in unique_users:
            if user not in new_group.users:  # Check if user is already in the group
                new_group.users.append(user)

        db.session.add(new_group)
        db.session.commit()

        return new_group.get_summary()  # Return summary of the created group
    
    def get_summary(self, include_users=False, include_chats=False):
        data = {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'is_private': self.is_private,
            'created_at': self.created_at.isoformat() + 'Z' if self.created_at is not None else None,
            'updated_at': self.updated_at.isoformat() + 'Z' if self.updated_at is not None else None,
        }

        if include_users and self.users:
            data['users'] = [user.get_summary() for user in self.users]
            
        if include_chats and self.chats:
            data['chats'] = [chat.get_summary() for chat in self.chats]

        return data
    
    def __repr__(self):
        return f'<Group {self.name}>'

# Group model
# class Group(db.Model):
#     __tablename__ = 'groups'
#     id = db.Column(db.Integer, primary_key=True)
#     name = db.Column(db.String(50), unique=True, nullable=False)
#     description = db.Column(db.Text)
#     is_private = db.Column(db.Boolean(), default=False)  # Indicates if the group is private
#     created_at = db.Column(db.DateTime, nullable=False, default=func.now())
#     updated_at = db.Column(db.DateTime, nullable=False, default=func.now(), onupdate=func.now())
    
#     users = db.relationship('User', secondary='user_group', back_populates='groups')
#     # users = db.relationship('User', secondary='user_chat_room', back_populates='chat_rooms')
#     chats = db.relationship('Chat', backref='group', lazy=True)
    
#     @staticmethod
#     def create_group(users, name=None, description=None):
#         """Create a chat group for the given users."""
#         if not users:
#             raise ValueError("At least one user must be provided.")

#         new_room = Group(name=name, description=description)
#         new_room.users.extend(users)

#         db.session.add(new_room)
#         db.session.commit()

#         return {
#             'room_id': new_room.id,
#             'room_name': new_room.name,
#             'description': new_room.description,
#             'users': [user.username for user in users],
#         }
        
#     def __repr__(self):
#         return f'<Group {self.name}>'

# Group model
# class Group_bak(db.Model):
#     __tablename__ = 'groups'
#     id = db.Column(db.Integer, primary_key=True)
#     name = db.Column(db.String(50), unique=True, nullable=False)
#     description = db.Column(db.Text)
#     is_private = db.Column(db.Boolean(), default=False)  # Indicates if the group is private
#     created_at = db.Column(db.DateTime, nullable=False, default=func.now())
#     updated_at = db.Column(db.DateTime, nullable=False, default=func.now(), onupdate=func.now())
    
#     users = db.relationship('User', secondary='user_group', back_populates='groups')
#     chats = db.relationship('Chat', backref='group', lazy=True)
    
#     @staticmethod
#     def create_group(self, users, name=None, description=None):
#         """Create a chat group for the given users."""
#         if not users:
#             raise ValueError("At least one user must be provided.")

#         # Check for duplicates and valid users
#         unique_users = set(users)  # Remove duplicates
#         if len(unique_users) != len(users):
#             raise ValueError("Duplicate users are not allowed.")

#         # Create the new group
#         new_room = Group(name=name, description=description)
        
#         # Add users to the group
#         for user in unique_users:
#             if user not in new_room.users:  # Check if user is already in the group
#                 new_room.users.append(user)

#         db.session.add(new_room)
#         db.session.commit()

#         return self.get_summary()
#         # return {
#         #     'room_id': new_room.id,
#         #     'room_name': new_room.name,
#         #     'description': new_room.description,
#         #     'users': [user.username for user in unique_users],
#         # }
    
#     def get_summary(self, include_users=False, include_chats=False):
#         data = {
#             'id': self.id,
#             'name': self.name,
#             'description': self.description,
#             'is_private': self.is_private,
#             'created_at': self.created_at.isoformat() + 'Z' if self.created_at is not None else None,
#             'updated_at': self.updated_at.isoformat() + 'Z' if self.updated_at is not None else None,
#         }

#         if include_users and self.users:
#             data['users'] = [user.get_summary() for user in self.users]
            
#         if include_chats and self.chats:
#             data['users'] = [chat.get_summary() for chat in self.chats]

#         return data
    
    
#     def __repr__(self):
#         return f'<Group {self.name}>'
