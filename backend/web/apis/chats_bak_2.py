import traceback
import jsonschema
from flask import request
from flask_jwt_extended import current_user, get_jwt_identity, jwt_required
from sqlalchemy import func
from web.apis.utils.helpers import extract_and_verify_jwt_ws
from web.apis.utils.decorators import jwt_required_ws
from web.apis.utils.chats import ConnectionManager
from web.apis.utils.serializers import PageSerializer, error_response, success_response
from web.extensions import db, socketio as sio
from web.apis.models.users import User
from web.apis.models.chats import Chat, Group, user_group
from web.apis.schemas.chats import chat_event_schemas

connection_manager = ConnectionManager()

@sio.on('is_authenticated', namespace='/api/chats')
def handle_auth_connect(username):
    sid = request.sid
    username = username or current_user.username if current_user else str(True)
    connection_manager.connect(username, sid)

@sio.on('is_anonymous', namespace='/api/chats')
def handle_auth_disconnect(username):
    username = username or current_user.username if current_user else str(True)
    connection_manager.disconnect(username)

@sio.on('connect', namespace='/api/chats')
def handle_connect(currentUsername):
    sid = request.sid
    print("connect event received", sid)
    username = currentUsername or current_user.username if current_user else request.remote_addr
    connection_manager.connect(username, sid)
    
    # sio.emit('save_chat_response', {'success': True, 'message': 'Test event received!'}, namespace='/api/chats')

@sio.on('typing_request', namespace='/api/chats')
def handle_typing(data):
    try:
        print("typing event received", sid)
        event_schema = chat_event_schemas['typing_request']
        jsonschema.validate(data, event_schema)

        from_username = data.get('from_username', connection_manager.get_socket(request.sid))
        if not User.get_user(from_username):
            data = error_response('Invalid user IDs in typing payload')
            return connection_manager.notify('typing_response', data)

        # Notify the recipient
        data = success_response(f'{from_username} is typing')
        connection_manager.notify('typing_response', data, data['to_username'])
    except Exception as e:
        return connection_manager.notify('typing_response', error_response(f'Error: {str(e)}'))

@sio.on('save_chat_response', namespace='/api/chats')
# @jwt_required()
def save_response(data):
    try:
        print("save_chat_response event received", request.sid, data)
    except Exception as e:
        print(e)
        
from jwt import ExpiredSignatureError, InvalidTokenError
@sio.on('save_chat_request', namespace='/api/chats')
@jwt_required()
def save(data):
    try:

        # Check if user is authenticated
        # current_user = get_jwt_identity()
        # if not current_user:
        #     error, _ = error_response('Kindly sign in to enjoy a seamless chat experience.')
        #     return connection_manager.notify('save_chat_response', data=error)
        # current_user = extract_and_verify_jwt_ws(data, connection_manager, 'save_chat_response')
        # # current_user = extract_and_verify_jwt_ws(data, connection_manager, 'save_chat_request')
        # if not current_user:
        #     # Authentication failed, response already sent
        #     return

        # Check if user is authenticated
        # current_user = get_jwt_identity()
        if not current_user:
            error, _ = error_response('Kindly sign in to enjoy a seamless chat experience.')
            return connection_manager.notify('save_chat_response', data=error)
        
        try:
            # data['from_username'] = current_user.username if data['from_username'] and data['from_username'] is None else None
            jsonschema.validate(instance=data, schema=chat_event_schemas['save_chat_request'])
        except Exception as e:
            error, _ = error_response(f"{e}")
            return connection_manager.notify('save_chat_response', error)
        
        sender = current_user
        recipient_username = data.get('to_username')
        group_id = data.get('group_id')
        # print(sender, recipient_username, group_id)
        if not recipient_username and not group_id:
            print("Either recipient username or group id is required.")
            error, _ = error_response('Either recipient username or group id is required.')
            return connection_manager.notify('save_chat_response', data=error)

        if recipient_username:
            recipient = User.get_user(recipient_username)
            if not recipient:
                # error, _ = error_response(f'Invalid recipient username <{recipient_username}>.')
                error, _ = error_response(f'Invalid recipient username <{recipient_username}>.', include_status_code=False)
                print(error, _)
                response = connection_manager.notify('save_chat_response', error)
                # response = sio.emit('save_chat_response', {'success': True, 'message': f'Invalid recipient username <{recipient_username}>.'}, namespace='/api/chats')
                return response

            # Check if a group already exists between the sender and recipient
            # group = Group.query.join(user_group).filter(
            #     (user_group.c.user_id == sender.id) | (user_group.c.user_id == recipient.id)
            # ).group_by(Group.id).having(func.count(user_group.c.user_id) == 2).first()

            # Check if a one-on-one group already exists
            group = Group.query.filter(
                Group.group_type == 'one_on_one',
                Group.users.any(User.id == sender.id),
                Group.users.any(User.id == recipient.id)
            ).group_by(Group.id).having(func.count(Group.users) == 2).first()
            
            if not group:
                # Generate a consistent group name
                usernames = sorted([sender.username, recipient.username])
                group_name = f"rm_{usernames[0]}_{usernames[1]}_group"

                # Create a new group for the sender and recipient
                group = Group(name=group_name, description=f"A Chat group b/w {sender.username, recipient.username}")
                # group.users.extend([sender, recipient])
                # Only add users if they are not already in the group
                if sender not in group.users:
                    group.users.append(sender)
                if recipient not in group.users:
                    group.users.append(recipient)
            
                db.session.add(group)
                db.session.commit()

        elif group_id:
            group = Group.query.get(group_id)
            if not group:
                error, _ = error_response(f'Invalid group id <{group_id}>.')
                return connection_manager.notify('save_chat_response', data=error)

        # Create and save the chat message
        new_chat = Chat(
            group_id=group.id,
            user_id=sender.id,
            text=data.get('text'),
            media_url=data.get('media_url'),
            sticker=data.get('sticker')
        )
        
        db.session.add(new_chat)
        db.session.commit()

        # Notify success to the group
        data = success_response('Chat saved successfully', data=new_chat.get_summary())
        return connection_manager.notify_group('save_chat_response', data, group_id=group.id)

    # except ExpiredSignatureError:
    #     # Handle expired token error
    #     error_response_data = {
    #         'success': False,
    #         'error': "Your session has expired. Please log in again."
    #     }
    #     connection_manager.notify('save_chat_response', data=error_response_data)

    # except InvalidTokenError:
    #     # Handle invalid token error
    #     error_response_data = {
    #         'success': False,
    #         'error': "Invalid token. Please log in again."
    #     }
    #     connection_manager.notify('save_chat_response', data=error_response_data)
        
    except jsonschema.exceptions.ValidationError as e:
        traceback.print_exc()
        error, _ = error_response(f'Validation error: {str(e)}')
        return connection_manager.notify('save_chat_response', data=error)
    
    except Exception as e:
        traceback.print_exc()
        error, _ = error_response(f'An error occurred {e}', str(e))
        return connection_manager.notify('save_chat_response', data=error)

@sio.on('save_chat_response', namespace='/api/chats')
def save_chat(data):
    try:
        # print(f"Emitting event '{event}' to socket ID: {socket_id, self.get_socket(username)} for user {username}\n with data {data}")
        print(f"save_chat_response event emitted with\n {data}")
    except Exception as e:
        traceback.print_exc()
        error, _ = error_response('An error occurred', str(e))
        return connection_manager.notify('save_chat_response', data=error)
    
# @sio.on('fetch_chat_request', namespace='/chats/<string:username>')
@sio.on('fetch_chat_request', namespace='/api/chats')
def fetch(username):
    try:
        print("fetch_chat_request event received", request.sid, username)
        username = current_user.username if current_user else username
        jsonschema.validate(username, chat_event_schemas['fetch_chat_request'])

        user = User.get_user(username)
        if not user:
            data = error_response(f'User {username} not found')
            return connection_manager.notify('fetch_chat_response', data)

        # chats = Chat.query.filter(Chat.group_id.in_([room.id for room in user.groups])).order_by(Chat.created.desc()).all()
        
        # Pagination
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)

        chats = Chat.query.filter(Chat.group_id.in_([room.id for room in user.groups])).order_by(Chat.created.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        data = PageSerializer(pagination_obj=chats, resource_name="chats").get_data()
        data = success_response('Chats fetched successfully.', data=data)
        return connection_manager.notify('fetch_chat_response', data)
    except jsonschema.exceptions.ValidationError as e:
        return connection_manager.notify('fetch_chat_response', error_response('Validation error', str(e)))
    except Exception as e:
        return connection_manager.notify('fetch_chat_response', error_response('An error occurred', str(e)))

# @sio.on('remove_chat_request', namespace='/chats/<int:chat_id>')
@sio.on('remove_chat_request', namespace='/api/chats')
def remove(data):
    try:
        print("remove_chat_request event received", request.sid)
        jsonschema.validate(data, chat_event_schemas['remove_chat_request'])
        username = data['user_id']

        chat = Chat.query.get(data['chat_id'])
        if not chat or (chat.from_user != username and chat.to_user != username):
            return connection_manager.notify('remove_chat_response', error_response('Chat not found or not authorized to_user remove'))

        chat.fro_deleted = chat.from_user == username
        chat.to_deleted = chat.to_user == username
        db.session.commit()
        data = success_response('Chat removed successfully')
        return connection_manager.notify('remove_chat_response', data )
    except jsonschema.exceptions.ValidationError as e:
        return connection_manager.notify('remove_chat_response', error_response('Validation error', str(e)))
    except Exception as e:
        return connection_manager.notify('remove_chat_response', error_response('An error occurred', str(e)))

@sio.on('update_chat_request', namespace='/api/chats')
def update(data):
    try:
        print("update event received", request.sid)
        jsonschema.validate(data, chat_event_schemas['update_chat_request'])
        username = data['from_username']
        chat = Chat.query.get(data['chat_id'])
        if not chat or chat.from_user != username:
            return connection_manager.notify('update_chat_response', error_response('Chat not found or not authorized to_user update'))
        chat.text = data['text']
        db.session.commit()
        data = success_response('Chat updated successfully', data=chat.get_summary())
        return connection_manager.notify('update_chat_response', data )
    except jsonschema.exceptions.ValidationError as e:
        data = error_response(f'Validation error: {e}')
        return connection_manager.notify('update_chat_response', data)
    except Exception as e:
        data = error_response(f'An error occurred: {e}')
        return connection_manager.notify('update_chat_response', data)

