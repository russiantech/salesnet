Here’s the complete code for your community-based chat application, including models for communities, groups, user roles, and announcements. You can copy and paste this directly into your project.

```python
from sqlalchemy import CheckConstraint, func
from web.extensions import db

# User Model
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    # Other user fields...

    groups = db.relationship('UserGroup', back_populates='user')

    def __repr__(self):
        return f'<User {self.username}>'

# Community Model
class Community(db.Model):
    __tablename__ = 'communities'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, nullable=False, default=func.now())
    updated_at = db.Column(db.DateTime, nullable=False, default=func.now(), onupdate=func.now())

    groups = db.relationship('Group', back_populates='community')
    announcements = db.relationship('Announcement', back_populates='community')

    def __repr__(self):
        return f'<Community {self.name}>'

# Group Model
class Group(db.Model):
    __tablename__ = 'groups'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text)
    is_private = db.Column(db.Boolean(), default=False)  # Indicates if the group is private
    community_id = db.Column(db.Integer, db.ForeignKey('communities.id'), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=func.now())
    updated_at = db.Column(db.DateTime, nullable=False, default=func.now(), onupdate=func.now())

    community = db.relationship('Community', back_populates='groups')
    members = db.relationship('UserGroup', back_populates='group')

    def __repr__(self):
        return f'<Group {self.name}>'

# UserGroup Model (Association Table)
class UserGroup(db.Model):
    __tablename__ = 'user_group'
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id'), primary_key=True)
    role = db.Column(db.String(20), nullable=False, default='member')  # Roles: admin, moderator, member
    joined_at = db.Column(db.DateTime, nullable=False, default=func.now())

    user = db.relationship('User', back_populates='groups')
    group = db.relationship('Group', back_populates='members')

# Chat Model
class Chat(db.Model):
    __tablename__ = 'chats'

    id = db.Column(db.Integer, unique=True, primary_key=True, nullable=False)
    text = db.Column(db.Text)
    media = db.Column(db.String(140))
    sticker = db.Column(db.String(140))
    last_seen = db.Column(db.DateTime(timezone=True), default=func.now())

    from_deleted = db.Column(db.Boolean(), default=False, nullable=False)
    to_deleted = db.Column(db.Boolean(), default=False, nullable=False)

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    user = db.relationship('User', back_populates='chat')

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

    def get_summary(self, include_user=False):
        data = {
            'id': self.id,
            'text': self.text if self.text else '',
            'sticker': self.sticker,
            'media': self.media,
            'last_seen': self.last_seen,
            'from_deleted': self.from_deleted,
            'to_deleted': self.to_deleted,
            'created': self.created_at.isoformat() + 'Z' if self.created_at is not None else None,
            'updated': self.updated_at.isoformat() + 'Z' if self.updated_at is not None else None,
        }

        if include_user:
            data['user'] = self.user.get_summary()

        return data

# Announcement Model
class Announcement(db.Model):
    __tablename__ = 'announcements'
    id = db.Column(db.Integer, primary_key=True)
    community_id = db.Column(db.Integer, db.ForeignKey('communities.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=func.now())
    
    community = db.relationship('Community', back_populates='announcements')

    def __repr__(self):
        return f'<Announcement {self.title}>'
```

### Summary of the Code
- **User Model**: Represents users in the system.
- **Community Model**: Represents a community that can contain multiple groups and announcements.
- **Group Model**: Represents groups within a community, allowing for various roles.
- **UserGroup Model**: Manages the relationship between users and groups, including their roles.
- **Chat Model**: Manages individual messages within groups.
- **Announcement Model**: Represents announcements within a community.

This structure should provide a solid foundation for building a community-based chat application similar to WhatsApp. Feel free to modify and expand upon it as needed!