import traceback
import jsonschema
from flask import request
from flask_jwt_extended import current_user, jwt_required
from sqlalchemy import and_, func, or_
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
def handle_connect():
    try:
        sid = request.sid
        data = connection_manager.connect(sid)
        return connection_manager.notify('connect_response', (data, sid))
    except Exception as e:
        # traceback.print_exc()
        error, _ = error_response(f'error while connecting: {str(e)}')
        return connection_manager.notify('connect_response', data=error)

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

@sio.on('save_chat_request', namespace='/api/chats')
@jwt_required()
def save(data):
    try:
        # Ensure the user is authenticated
        if not current_user:
            error, _ = error_response('Kindly sign in to enjoy a seamless chat experience.')
            return connection_manager.notify('save_chat_response', data=error)

        # Validate incoming data against the schema
        jsonschema.validate(instance=data, schema=chat_event_schemas['save_chat_request'])

        sender = current_user
        recipient_username = data.get('to_username')
        group_id = data.get('group_id')

        # Ensure either recipient username or group ID is provided
        if not recipient_username and not group_id:
            error, _ = error_response('Either recipient username or group id is required.')
            return connection_manager.notify('save_chat_response', data=error)

        # Handle one-on-one messaging
        if recipient_username:
            recipient = User.get_user(recipient_username)
            if not recipient:
                error, _ = error_response(f'Invalid recipient username <{recipient_username}>.', include_status_code=False)
                return connection_manager.notify('save_chat_response', error)

            # Check if a group already exists between the sender and recipient
            group = Group.query.join(user_group).filter(
                and_(
                    or_(
                        user_group.c.user_id == sender.id, 
                        user_group.c.user_id == recipient.id), 
                        Group.group_type == 'one_on_one')
            ).group_by(
                Group.id).having(
                func.count(user_group.c.user_id) == 2).first()
            
            # Create a new group if it doesn't exist
            if not group:
                def get_or_create_group(name, description, is_private=True, group_type="one_on_one"):
                    # Check if group already exists
                    existing_group = db.session.query(Group).filter_by(name=name).first()
                    if existing_group:
                        print(f"Group '{name}' already exists with ID: {existing_group.id}.")
                        return existing_group  # Return existing group

                    # Create new group if it doesn't exist
                    new_group = Group(name=name, description=description, is_private=is_private, group_type=group_type)
                    db.session.add(new_group)
                    db.session.commit()  # Commit to save the new group
                    print(f"Created new group '{name}' with ID: {new_group.id}.")
                    return new_group

                usernames = sorted([sender.username, recipient.username])
                group_name = f"rm_{usernames[0]}_{usernames[1]}_group"
                group_description = f"A chat group between {usernames[0]} and {usernames[1]}"
                # group = Group(name=group_name, description=f"A chat group between {usernames[0]} and {usernames[1]}", group_type='one_on_one')
                group = get_or_create_group(group_name, group_description)
                
                # Add users to the group only if they are not already members
                def add_users_to_group(group, users):
                    for user in users:
                        if user not in group.users:
                            group.users.append(user)  # Use append instead of extend for a single user
                            print(f"Added user {user.id} to group {group.id}.")
                        else:
                            print(f"User {user.id} is already a member of group {group.id}.")

                # Assuming sender and recipient are User objects and group is a Group object
                add_users_to_group(group, [sender, recipient])

                # Commit changes to the database
                db.session.add(group)
                db.session.commit()


        # Handle multi-user messaging
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
        data, status = success_response('Chat saved successfully', data=new_chat.get_summary())
        print(new_chat.get_summary(), "\n" )
        print(data, status)
        print(connection_manager.get_active_connections())
        
        # connection_manager.notify('save_chat_response', data)
        return connection_manager.notify_group('save_chat_response', data, group_id=group.id)
        # return connection_manager.notify_group('save_chat_response', data)

    except jsonschema.exceptions.ValidationError as e:
        error, _ = error_response(f'Validation error: {str(e)}')
        return connection_manager.notify('save_chat_response', data=error)

    except Exception as e:
        traceback.print_exc()
        error, _ = error_response(f'An error occurred: {str(e)}')
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

# for group chat/messaging
@sio.on('create_group_request', namespace='/api/chats')
@jwt_required()
def create_group(data):
    try:
        if not current_user:
            error, _ = error_response('Kindly sign in to create a group.')
            return connection_manager.notify('create_group_response', data=error)

        group_name = data.get('group_name')
        user_ids = data.get('user_ids', [])  # List of user IDs to include in the group

        if not group_name:
            error, _ = error_response('Group name is required.')
            return connection_manager.notify('create_group_response', data=error)

        # Create the group
        group = Group(name=group_name, description=data.get('description', ''), group_type='multi_user')

        # Add the creator as the first member
        group.users.append(current_user)

        # Add additional users if provided
        for user_id in user_ids:
            user = User.query.get(user_id)
            if user:
                group.users.append(user)

        db.session.add(group)
        db.session.commit()

        data = success_response('Group created successfully.', data={'group_id': group.id})
        return connection_manager.notify('create_group_response', data)

    except Exception as e:
        traceback.print_exc()
        error, _ = error_response(f'An error occurred: {str(e)}', str(e))
        return connection_manager.notify('create_group_response', data=error)
 
