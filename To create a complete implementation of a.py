To create a complete implementation of a chat feature in an eCommerce application using WebSockets for real-time communication, we will structure the solution into several key components:

1. **WebSocket Setup**: Establish a WebSocket server for real-time communication.
2. **API Endpoints**: Create RESTful API endpoints for managing chats, chat history, and groups.
3. **Database Models**: Utilize the provided SQLAlchemy models for chat and groups.
4. **Frontend Integration**: Outline how to connect the frontend to the WebSocket and API.

Below is a professional implementation outline:

### Step 1: WebSocket Setup

#### Install Required Packages

Make sure to install the necessary packages:

```bash
pip install Flask-SocketIO
```

#### WebSocket Server Implementation

Create a WebSocket server using Flask-SocketIO:

```python
from flask import Flask, request
from flask_socketio import SocketIO, emit
from web.extensions import db
from models import Chat, Group  # Assuming your models are in models.py

app = Flask(__name__)
socketio = SocketIO(app)

@socketio.on('connect')
def handle_connect():
    print("User connected")

@socketio.on('disconnect')
def handle_disconnect():
    print("User disconnected")

@socketio.on('send_message')
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

if __name__ == '__main__':
    socketio.run(app)
```

### Step 2: API Endpoints

#### Create RESTful API Endpoints

You can create a Flask blueprint for managing chat and group functionalities:

```python
from flask import Blueprint, jsonify, request
from web.extensions import db
from models import Chat, Group

chat_bp = Blueprint('chat', __name__)

@chat_bp.route('/chats', methods=['GET'])
def get_chats():
    chats = Chat.query.filter_by(is_deleted=False).all()
    return jsonify([chat.get_summary() for chat in chats])

@chat_bp.route('/chats', methods=['POST'])
def create_chat():
    data = request.json
    chat = Chat(
        text=data.get('text'),
        media=data.get('media'),
        sticker=data.get('sticker'),
        user_id=data.get('user_id')
    )
    db.session.add(chat)
    db.session.commit()
    return jsonify(chat.get_summary()), 201

@chat_bp.route('/chats/<int:chat_id>', methods=['DELETE'])
def delete_chat(chat_id):
    chat = Chat.query.get(chat_id)
    if chat:
        chat.is_deleted = True
        db.session.commit()
        return jsonify({'message': 'Chat deleted'}), 200
    return jsonify({'message': 'Chat not found'}), 404

@chat_bp.route('/groups', methods=['GET'])
def get_groups():
    groups = Group.query.all()
    return jsonify([{'id': group.id, 'name': group.name} for group in groups])

@chat_bp.route('/groups', methods=['POST'])
def create_group():
    data = request.json
    group = Group(name=data.get('name'), description=data.get('description'))
    db.session.add(group)
    db.session.commit()
    return jsonify({'id': group.id, 'name': group.name}), 201
```

### Step 3: Integrate with Frontend

You can use libraries like React or Vue.js to connect to your WebSocket server and API endpoints.

#### Example Frontend (React)

```javascript
import React, { useEffect, useState } from 'react';
import io from 'socket.io-client';

const socket = io('http://localhost:5000'); // Your server URL

const ChatComponent = () => {
    const [messages, setMessages] = useState([]);
    const [text, setText] = useState('');

    useEffect( () => {
        socket.on('receive_message', (message) => {
            setMessages((prevMessages) => [...prevMessages, message]);
        });

        return () => {
            socket.off('receive_message');
        };
    }, []);

    const sendMessage = () => {
        socket.emit('send_message', { text, user_id: 1 }); // Replace with actual user ID
        setText('');
    };

    return (
        <div>
            <div>
                {messages.map((msg) => (
                    <div key={msg.id}>{msg.text}</div>
                ))}
            </div>
            <input
                type="text"
                value={text}
                onChange={(e) => setText(e.target.value)}
            />
            <button onClick={sendMessage}>Send</button>
        </div>
    );
};

export default ChatComponent;
```

### Step 4: Manage Chat History

Ensure you have the necessary endpoints to retrieve chat history, which can be done using the existing `get_chats` endpoint.

### Conclusion

This implementation provides a complete framework for a chat feature in an eCommerce application, utilizing WebSockets for real-time communication and RESTful APIs for managing chat data and groups. Ensure to test thoroughly and consider adding features like user authentication, message encryption, and error handling for a more robust solution.