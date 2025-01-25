import traceback
import jsonschema
from flask import request
from flask_jwt_extended import current_user, jwt_required
from sqlalchemy import func
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
    username = currentUsername or current_user.username if current_user else str(True)
    connection_manager.connect(username, sid)

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

# @sio.on('save_chat_request', namespace='/chats')
# @sio.on('save_chat_request', namespace='/chats/<int:group_id>')
# def save(group_id=None):
#     try:
#         if not current_user:
#             return connection_manager.notify('save_chat_response', error_response('User not authenticated'))

#         data = json.loads(data) if isinstance(data, str) else data
#         jsonschema.validate(instance=data, schema=chat_event_schemas['save_chat_request'])

#         to_username = data['to_username']
#         fro_user = current_user
#         to_user = User.get_user(to_username)

#         if not fro_user or not to_user:
#             data =  error_response('Invalid users.')
#             return connection_manager.notify('save_chat_response', data, current_user.username)

#         # Check or create chat room
#         participants = (fro_user, to_user)
#         group = Group.query.join(user_group).filter(
#             user_group.c.user_id.in_([user.id for user in participants])
#         ).group_by(Group.id).having(func.count(user_group.c.user_id) == len(participants)).first()

#         if not group:
#             room_name = data['group_name'] or f"rm_{fro_user.username}_x_{to_user.username}"
#             group = Group.create_group(users=participants, name=room_name, description="A group for chatting")

#         new_chat = Chat(
#             group_id=group.id, 
#             user_id=fro_user.id, 
#             text=data.get('text'), 
#             media_url=data.get('media_url'), 
#             sticker=data.get('sticker')
#             )
#         db.session.add(new_chat)
#         db.session.commit()
        
#         data = success_response('Chat saved successfully', data=new_chat.get_summary())
#         return connection_manager.notify_group('save_chat_response', data, group_id=group.id)
    
#     except jsonschema.exceptions.ValidationError as e:
#         traceback.print_exc()
#         return connection_manager.notify('save_chat_response', error_response(f'Validation error _ {str(e)}') )
#     except Exception as e:
#         traceback.print_exc()
#         return connection_manager.notify('save_chat_response', error_response('An error occurred', str(e)))
# @sio.on('save_chat_request')

# @sio.on('save_chat_request', namespace='/api/chats')
# # @sio.on('save_chat_request', namespace='/chats/<int:group_id>')
# def save(data, group_id=None):
#     try:
#         sid = request.sid
        
#         # Check if user is authenticated
#         if not current_user:
#             error, _= error_response('Kindly sign in to enjoy seamless chat experience.')
#             # return connection_manager.notify('save_chat_response', data, sid)
#             print(connection_manager.notify('save_chat_response', data=error, username=request.remote_addr))
        
#         print("save_chat_request event received", sid)

#         # Parse and validate incoming data
#         data = json.loads(data) if isinstance(data, str) else data
#         jsonschema.validate(instance=data, schema=chat_event_schemas['save_chat_request'])

#         fro_user = current_user
#         to_usernames = data.get('to_usernames', [])  # List of recipient usernames
        
#         if not to_usernames:
#             return connection_manager.notify('save_chat_response', error_response('No recipients provided.'))

#         # Retrieve user objects for the recipients
#         to_users = [User.get_user(username) for username in to_usernames]
#         if any(user is None for user in to_users):
#             return connection_manager.notify('save_chat_response', error_response('One or more invalid users.'))

#         # Check or create a new chat group
#         participants = [fro_user] + to_users
#         group = Group.query.join(user_group).filter(
#             user_group.c.user_id.in_([user.id for user in participants])
#         ).group_by(Group.id).having(func.count(user_group.c.user_id) == len(participants)).first()

#         if not group:
#             room_name = data.get('group_name') or f"rm_{fro_user.username}_group"
#             group = Group.create_group(users=participants, name=room_name, description="A group for chatting")

#         # Create and save the chat message
#         new_chat = Chat(
#             group_id=group.id,
#             user_id=fro_user.id,
#             text=data.get('text'),
#             media_url=data.get('media_url'),
#             sticker=data.get('sticker')
#         )
        
#         # Begin transaction
#         with db.session.begin():
#             db.session.add(new_chat)
#             db.session.commit()

#         # Notify success to the group
#         response_data = success_response('Chat saved successfully', data=new_chat.get_summary())
#         return connection_manager.notify_group('save_chat_response', response_data, group_id=group.id)

#     except jsonschema.exceptions.ValidationError as e:
#         traceback.print_exc()
#         return connection_manager.notify('save_chat_response', error_response(f'Validation error: {str(e)}'))
#     except Exception as e:
#         username = current_user.username if current_user else str(True)
#         traceback.print_exc()
#         return connection_manager.notify('save_chat_response', error_response('An error occurred', str(e)), username)

@sio.on('save_chat_response', namespace='/api/chats')
@jwt_required()
def save_response(data):
    try:
        print("save_chat_response event received", request.sid, data)
    except Exception as e:
        print(e)
        
@sio.on('save_chat_request', namespace='/api/chats')
@jwt_required()
def save(data):
    try:
        # print("save_chat_request event", request.sid, data)
        # sio.emit('save_chat_response', data=data)
        # print(connection_manager.get_active_connections(),
        #       connection_manager.get_socket(request.remote_addr),
        #       connection_manager.get_socket(current_user.username),
        #       request.sid
        #       )
        # connection_manager.notify('save_chat_response', data=data)
        if not current_user:
            error, _= error_response('Kindly sign in to enjoy seamless chat experience.')
            return connection_manager.notify('save_chat_response', data=error)

        try:
            # data['from_username'] = current_user.username if data['from_username'] and data['from_username'] is None else None
            jsonschema.validate(instance=data, schema=chat_event_schemas['save_chat_request'])
        except Exception as e:
            error, _= error_response(f"{e}")
            return connection_manager.notify('save_chat_response', error)
        
        # event_schema = chat_event_schemas.get('save-chat-request')
        # jsonschema.validate(instance=data, schema=event_schema)

        sender = current_user
        recipient_username = data.get('to_username')
        group_id = data.get('group_id')
        # print(sender, recipient_username, group_id)
        if not recipient_username and not group_id:
            print("Either recipient username or group id is required.")
            error, _= error_response('Either recipient username or group id is required.')
            return connection_manager.notify('save_chat_response', data=error)

        if recipient_username:
            recipient = User.get_user(recipient_username)
            if not recipient:
                # error, _= error_response(f'Invalid recipient username <{recipient_username}>.')
                error, _= error_response(f'Invalid recipient username <{recipient_username}>.', include_status_code=False)
                # print(error, status)
                return connection_manager.notify('save_chat_response', data=error)

            # Check if a group already exists between the sender and recipient
            group = Group.query.join(user_group).filter(
                (user_group.c.user_id == sender.id) | (user_group.c.user_id == recipient.id)
            ).group_by(Group.id).having(func.count(user_group.c.user_id) == 2).first()

            if not group:
                # Create a new group for the sender and recipient
                group = Group(name=f"rm_{sender.username}_{recipient.username}_group", description="A group for chatting")
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

    except jsonschema.exceptions.ValidationError as e:
        traceback.print_exc()
        error, _ = error_response(f'Validation error: {str(e)}')
        return connection_manager.notify('save_chat_response', data=error)
    except Exception as e:
        traceback.print_exc()
        error, _= error_response('An error occurred', str(e))
        return connection_manager.notify('save_chat_response', data=error)

@sio.on('save_chat_response', namespace='/api/chats')
def save_chat_response(data):
    try:
        # print(f"Emitting event '{event}' to socket ID: {socket_id, self.get_socket(username)} for user {username}\n with data {data}")
        print(f"save_chat_response event emitted with\n {data}")
    except Exception as e:
        traceback.print_exc()
        error, _= error_response('An error occurred', str(e))
        return connection_manager.notify('save_chat_response', data=error)
    
@sio.on('save_chat_response')
def save_chat_response2(data):
    try:
        # print(f"Emitting event '{event}' to socket ID: {socket_id, self.get_socket(username)} for user {username}\n with data {data}")
        print(f"save_chat_response event emitted with\n {data}")
    except Exception as e:
        traceback.print_exc()
        error, _= error_response('An error occurred', str(e))
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

