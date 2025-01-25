from sqlalchemy import CheckConstraint, func
from web.extensions import db

# class Message(db.Model):
#     __tablename__ = 'message'
    
#     id = db.Column(db.Integer, primary_key=True)
#     sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
#     chat_room_id = db.Column(db.Integer, db.ForeignKey('chat_room.id'), nullable=False)
#     content_type = db.Column(db.String(20))  # e.g., 'text', 'image', 'video'
#     content = db.Column(db.Text)  # Actual content
#     timestamp = db.Column(db.DateTime, default=datetime.utcnow)
#     seen = db.Column(db.Boolean, default=False)
#     reply_to_id = db.Column(db.Integer, db.ForeignKey('message.id'), nullable=True)  # Optional reference to another message
#     reply_to_message = db.relationship('Message', remote_side=[id], backref='replies')


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

    reply_to_id = db.Column(db.Integer, db.ForeignKey('chats.id'), nullable=True)  # Optional reference to another message
    reply_to_chat = db.relationship('Chat', remote_side=[id], backref='replies')
    
    # chat_room_id = db.Column(db.Integer, db.ForeignKey('chat_room.id'), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    user = db.relationship('User', back_populates='chats')

    is_deleted = db.Column(db.Boolean(), nullable=False, index=True, default=False)
    created_at = db.Column(db.DateTime, nullable=False, index=True, default=func.now())
    updated_at = db.Column(db.DateTime, nullable=False, default=func.now(), onupdate=func.now())

    __table_args__ = (
        CheckConstraint(
            "text IS NOT NULL OR sticker IS NOT NULL OR media IS NOT NULL",
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
            'media': self.media,
            'last_seen': self.last_seen,
            'last_message': self.text if self.text and self.recent else None,
            'from_deleted': self.from_deleted,
            'to_deleted': self.to_deleted,
            'created_at': self.created_at.isoformat() + 'Z' if self.created_at is not None else None,
            'updated_at': self.updated_at.isoformat() + 'Z' if self.updated_at is not None else None,
        }

        if include_user:
            data['user'] = self.user.get_summary()

        return data

# UserGroup model (for many-to-many relationship between User and Group)
""" Purpose:
This model is used for establishing a many-to-many relationship between User and Group. 
It allows users to be part of multiple groups and groups to have multiple users.
Necessity:
Keep it if you plan to implement group chats where multiple users can participate in discussions. 
This model is essential for managing group memberships. 
"""
user_group = db.Table('user_group',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('group_id', db.Integer, db.ForeignKey('groups.id'), primary_key=True),
    db.Column('role', db.String(20), nullable=False, default='member')  # Role field
)

# user_chat_room = db.Table('user_chat_room',
#     db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
#     db.Column('chat_room_id', db.Integer, db.ForeignKey('chat_room.id'), primary_key=True),
#     db.Column('roles', db.String(20), nullable=False, default='member')  # Role field
# )

# class UserChatRoom(db.Model):
#     __tablename__ = 'user_chat_room'
    
#     user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
#     chat_room_id = db.Column(db.Integer, db.ForeignKey('chat_room.id'), primary_key=True)
    
# Group model
""" Purpose:
This model represents a group chat. It can hold information about the group, such as its name and its members.
Necessity:
Keep it if you intend to implement group chats. 
This model will help you manage group-related functionalities, such as creating groups, adding/removing members, and retrieving group chats.
 """

class Group(db.Model):
    __tablename__ = 'groups'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text)
    is_private = db.Column(db.Boolean(), default=False)  # Indicates if the group is private
    created_at = db.Column(db.DateTime, nullable=False, default=func.now())
    updated_at = db.Column(db.DateTime, nullable=False, default=func.now(), onupdate=func.now())
    
    users = db.relationship('User', secondary='user_group', back_populates='groups')
    # users = db.relationship('User', secondary='user_chat_room', back_populates='chat_rooms')
    chats = db.relationship('Chat', backref='group', lazy=True)
    
    def __repr__(self):
        return f'<Group {self.name}>'


# class ChatRoom(db.Model):
#     __tablename__ = 'chat_room'
    
#     id = db.Column(db.Integer, primary_key=True)
#     name = db.Column(db.String(80), nullable=False)
#     description = db.Column(db.Text)
#     is_private = db.Column(db.Boolean(), default=False)  # Indicates if the group is private
#     is_group = db.Column(db.Boolean, default=False)
#     users = db.relationship('User', secondary='user_chat_room', back_populates='chat_rooms')
#     chats = db.relationship('Chat', backref='chat_room', lazy=True)
    
#     created_at = db.Column(db.DateTime, nullable=False, default=func.now())
#     updated_at = db.Column(db.DateTime, nullable=False, default=func.now(), onupdate=func.now())
