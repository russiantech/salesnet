
from flask import request
from flask_jwt_extended import current_user, get_jwt, get_jwt_identity, jwt_required
from web.extensions import socketio as sio, redis as redis_client

# Initialize Redis connection
class ConnectionManager:
    def __init__(self):
        self.redis_key = 'active_connections'

    @jwt_required(optional=True)
    def connect_x(self, socket_id):
        # Attempt to get the current user's identity from the JWT token
        user = get_jwt_identity()  # This will return None if the user is not authenticated

        if user:
            username = str(user)  # Use the user's identity (e.g., username)
            print("Authenticated user:", username)
        else:
            # If no user is found, retrieve all claims
            claims = get_jwt()  # Get all claims from the JWT
            username = str(claims.get('username', request.remote_addr))  # Fallback to IP if username not found
            print("No authenticated user, using claims or IP:", username)

        # Check if the username already exists in Redis
        existing_username = redis_client.hget(self.redis_key, request.remote_addr)

        # If the user was previously connected with IP, update the socket ID for the new username
        if existing_username:
            print(f"Existing connection found for IP: {request.remote_addr}. Updating socket ID for username: {username}")
            redis_client.hset(self.redis_key, username, socket_id)  # Update the new username's socket ID
            # Optionally, remove the old entry if needed
            redis_client.hdel(self.redis_key, existing_username)  # Remove old entry if username is different
        else:
            # Store the socket ID in Redis for the new username
            redis_client.hset(self.redis_key, username, socket_id)

        redis_client.expire(self.redis_key, 3600)  # Set expiration for the connection

    @jwt_required(optional=True)
    def connect(self, socket_id):
        # Attempt to get the current user's identity from the JWT token
        user = get_jwt_identity()  # This will return None if the user is not authenticated

        if user:
            username = str(user)  # Use the user's identity (e.g., username)
            print("Authenticated user:", username)
        else:
            # If no user is found, retrieve all claims
            claims = get_jwt()  # Get all claims from the JWT
            username = str(claims.get('username', request.remote_addr))  # Fallback to IP if username not found
            print("No authenticated user, using claims or IP:", username)

        # Check if the user is already connected with the same IP
        existing_username = redis_client.hget(self.redis_key, request.remote_addr)

        if existing_username:
            # If the existing username is the same as the current one, update the socket ID
            # if existing_username == username:
            if existing_username.decode('utf-8') == username:
                print(f"User {username} is already connected. Updating socket ID.")
                redis_client.hset(self.redis_key, username, socket_id)  # Update socket ID
            else:
                print(f"Connection conflict: {existing_username} is already connected from IP: {request.remote_addr}.")
                # Here you can either reject the new connection or handle it as needed
                return {"message": "Connection conflict. User already connected."}, 409
        else:
            # Store the socket ID in Redis for the new username
            redis_client.hset(self.redis_key, username, socket_id)

        redis_client.expire(self.redis_key, 3600)  # Set expiration for the connection

    def disconnect(self, username):
        if username is not None:
            redis_client.hdel(self.redis_key, username)

    def get_socket(self, username):
        socket_id = redis_client.hget(self.redis_key, username)
        # Decode bytes to string if socket_id is not None and is of type bytes
        if socket_id and isinstance(socket_id, bytes):
            socket_id = socket_id.decode('utf-8')
        return socket_id
    
    def notify(self, event, data, username=None):
        if username is None:
            username = request.remote_addr  # Use user's IP address as a fallback
        socket_id = self.get_socket(username) or request.sid
        # socket_id = self.get_socket(username)
        if socket_id:
            print(f"Emitting event '{event}' to socket ID: {socket_id} for user {username} with data {data}")
            try:
                sio.emit(event, data, room=socket_id, namespace='/api/chats')
                return True
            except Exception as e:
                print(f"Error emitting event: {e}")
                return False
        else:
            print(f"No socket ID found for username: {username}")
            return None

    def notify_group(self, event, data, group_id):
        # Get all users in the group
        group = Group.query.get(group_id)
        if not group:
            return  # Group does not exist

        # Get all active connections for users in the group
        for user in group.users:
            # Attempt to get the socket ID using username first, then email
            socket_id = self.get_socket(user.username) or self.get_socket(user.email)
        
            if socket_id:
                print(f"Emitting group event '{event}' to socket ID: {socket_id} for users {user.username} with data {data}")
                # sio.emit(event, data, room=socket_id)
                sio.emit(event, data, room=socket_id, namespace='/api/chats')
                
    def current_socket_id(self):
        return request.sid
    
    def get_active_connections(self):
        # Return all active connections
        return redis_client.hgetall(self.redis_key)

connection_manager = ConnectionManager()

from web.extensions import db
from web.apis.models.chats import Chat, Group

def create_chat(user_id, group_id, media_type, media_url):
    chat = Chat(
        user_id=user_id,
        group_id=group_id,
        content_type=media_type,
        content=media_url
    )
    db.session.add(chat)
    db.session.commit()
    return chat

def create_reply(user_id, group_id, content_type, content, reply_to_id):
    reply_chat = Chat(
        user_id=user_id,
        group_id=group_id,
        content_type=content_type,
        content=content,
        reply_to_id=reply_to_id
    )
    db.session.add(reply_chat)
    db.session.commit()
    return reply_chat

def fetch_conversations(group_id):
    chats = Chat.query.filter_by(group_id=group_id).order_by(Chat.created_at.asc()).all()
    
    
def fetch_conversation02(group_id):
    chats = Chat.query.filter_by(group_id=group_id).order_by(Chat.created_at.asc()).all()
    
    # Group chats by their reply relationships
    chat_dict = {}
    for chat in chats:
        chat_dict[chat.id] = {
            'chat': chat,
            'replies': []
        }
    
    for chat in chats:
        if chat.reply_to_id:
            chat_dict[chat.reply_to_id]['replies'].append(chat)
    
    return chat_dict

def delete_chat(chat_id, user_id):
    chat = Chat.query.get(chat_id)
    # if chat and (chat.user_id == user_id or chat.chat_room.users.any(id=user_id)):
    if chat:
        if (chat.user_id == user_id):
            # db.session.commit()
            chat.from_deleted = True
            return True
        elif chat.chat_room.users.any(id=user_id):
            # db.session.delete(chat)
            chat.to_deleted = True
            return True
        
    return False

def fetch_group_conversations(group_id):
    return Chat.query.filter_by(group_id=group_id).order_by(Chat.created_at.asc()).all()

def fetch_conversations_between_users(user1_id, user2_id):
    chat_room = Group.query.filter(
        Group.users.any(id=user1_id),
        Group.users.any(id=user2_id)
    ).first()
    
    if chat_room:
        return Chat.query.filter_by(group_id=chat_room.id).order_by(Chat.created_at.asc()).all()
    return []