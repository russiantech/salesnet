
import traceback
from flask import request
from flask_socketio import emit
import jsonschema
from web.apis.utils.serializers import PageSerializer, error_response, success_response
from web.extensions import db, socketio as sio
from web.apis.models.chats import Chat, Group  # Assuming your models are in models.py
from web.apis import api_bp as chat_bp

@sio.on('send_message')
def handle_send_message(data):
    message = Chat(
        text=data.get('text'),
        media=data.get('media'),
        sticker=data.get('sticker'),
        user_id=data.get('user_id')
    )
    db.session.add(message)
    db.session.commit()
    
    emit('receive_message', message.get_summary(), broadcast=True)

@chat_bp.route('/chats', methods=['GET'])
@chat_bp.route('/chats/<int:chat_id>', methods=['GET'])
def get_chats(chat_id=None):
    try:
        if chat_id:
            chat = Chat.query.get(chat_id)
            if not chat:
                return error_response("chat not found.", 404)
            return success_response("chat fetched successfully.", data=chat.get_summary())

        # Pagination
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)

        chats = Chat.query.order_by(Chat.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        data = PageSerializer(pagination_obj=chats, resource_name='chats').get_data()
        return success_response("chats fetched successfully q.", data=data)

    except Exception as e:
        return error_response(f"Error fetching chats: {str(e)}")

@chat_bp.route('/chats/<int:group_id>/conversations', methods=['GET'])
def get_conversation(group_id):
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 20, type=int)

    # ... (authentication and user ID retrieval)

    # Query with pagination
    # chats = db.session.query(Chat).filter(
    #     (Chat.sender_id == current_user.id) & (Chat.recipient_id == recipient_id) |
    #     (Chat.sender_id == recipient_id) & (Chat.recipient_id == current_user.id)
    # ).order_by(Chat.created_at).paginate(page, limit, False)
    chats = fetch_conversations(group_id)

    data = PageSerializer(pagination_obj=chats, resource_name="chats").get_data()
    return success_response("Conversations fetched successfully", data=data)

@chat_bp.route('/chats', methods=['POST'])
def create_chat():
    try:
        data = request.json
        chat = Chat(
            text=data.get('text'),
            media=data.get('media'),
            sticker=data.get('sticker'),
            user_id=data.get('user_id', current_user.id)
        )
        db.session.add(chat)
        db.session.commit()
        return success_response("Chat created successfully.", data=chat.get_summary(), status_code=201)
    except Exception:
        traceback.print_exc()
        return error_response()
    
@chat_bp.route('/chats/<int:chat_id>', methods=['PUT'])
def update_chat():
    try:
        data = request.json
        chat = Chat(
            text=data.get('text'),
            media=data.get('media'),
            sticker=data.get('sticker'),
            user_id=data.get('user_id')
        )
        db.session.add(chat)
        db.session.commit()
        return success_response("Chat created successfully.", data=chat.get_summary(), status_code=201)
    except Exception:
        traceback.print_exc()
        return error_response()

@chat_bp.route('/chats/<int:chat_id>', methods=['DELETE'])
def remove_chats(chat_id):
    try:
        if chat_id:
            chat = Chat.query.get(chat_id)
            if not chat:
                return error_response("chat not found.", 404)
            db.session.delete(chat)
            db.session.commit()
            return success_response("chat deleted successfully.")
        
        return error_response(f"Error fetching chats: {str(e)}")
    except Exception as e:
        return error_response(f"Error fetching chats: {str(e)}")

@chat_bp.route('/groups', methods=['GET'])
def get_groups():
    try:
        groups = Group.query.all()
        data = PageSerializer(items=[groups], resource_name="groups").get_data()
        return success_response("Groups fetched successfully", data=data)
    except Exception:
        traceback.print_exc()
        return error_response(f"Could not fetch groups, unexpected error occured.")
    
@chat_bp.route('/groups', methods=['POST'])
def create_group():
    try:
        data = request.json
        group = Group(name=data.get('name'), description=data.get('description'))
        db.session.add(group)
        db.session.commit()
        return success_response(f"Group <{group.name}> created successfully", data=group.get_summary())
    except Exception:
        traceback.print_exc()
        return error_response(f"Could not fetch groups, unexpected error occured.")

# ===============
from web.extensions import socketio as sio
from flask_jwt_extended import current_user
from web.apis.utils.chats import connection_manager, fetch_conversations
@sio.on('connect', namespace='/chat')
def handle_connect():
    username = current_user.username if current_user.is_authenticated else None
    if username:
        connection_manager.connect(username, request.sid)

@sio.on('disconnect', namespace='/chat')
def handle_disconnect():
    username = current_user.username if current_user.is_authenticated else None
    if username:
        connection_manager.disconnect(username)

@sio.on('save-chat-request', namespace='/chat')
def save_chat(data):
    try:
        jsonschema.validate(data, event_schemas['save-chat-request'])
        to_username = data['to']
        fro_user = current_user

        if not fro_user.is_authenticated:
            return connection_manager.notify('save-chat-response', error_response('User not authenticated'), fro_user.username)

        # Create a new chat entry
        chat = Chat(
            text=data.get('text'),
            media=data.get('media'),
            sticker=data.get('sticker'),
            user_id=fro_user.id
        )
        db.session.add(chat)
        db.session.commit()

        connection_manager.notify('save-chat-response', success_response('Chat saved successfully', chat.get_summary()), to_username)
    except jsonschema.ValidationError as e:
        connection_manager.notify('save-chat-response', error_response(False, 'Invalid data', error_message=str(e)), fro_user.username)
    except Exception as e:
        connection_manager.notify('save-chat-response', error_response(False, 'Error saving chat', error_message=str(e)), fro_user.username)


