// const socket = io.connect('http://localhost:5000/api/chats'); // Adjust the URL as necessary
// const socket = io.connect('http://localhost:5000'); // Adjust the URL if needed

// const socket = io();
const socket = io.connect('http://localhost:5000'); // Adjust the port if necessary

$(document).ready( () => {
    const username = "edet";
    try{
    
    socket.on('connect', () => {
        console.log('Connected to Socket.IO server with session ID:', socket.id);
    });
    
    socket.on('disconnect', () => {
        console.log('Disconnected from Socket.IO server');
    });

    // const socket = io();
    const validate = (data) => {
        if (typeof data === 'object' && !Array.isArray(data)) {
            return JSON.stringify(data); // Return the validated data
        } else {
            console.error('Data must be a dictionary.');
            return null; // Return null to indicate validation failure
        }
        
        };


    // on-messaging, emit `save-chat-request` event to inform the server
    $('#chat_form').on('submit', (e) => {
        e.preventDefault();
        const content = $('#chat_content');
        let data = {
            /* schema expects str & int */
            'to_username': $(content).attr("data-to_username").toString(), 
            'from_username': $(content).attr("data-from_username").toString(),
            'text': $(content).val().toString(),
            'sticker': ''.toString(),
            'media': ''.toString(),
            'sticker': $(content).files.length > 0 ? $(content).files[0] : null,
            'media_url': $(content).files.length > 0 ? $(content).files[0] : null,
            };

        //emit `save_chat_request` event to the server
        socket.emit('save_chat_request',  validate(data), (response) => {
            console.log("Received acknowledgment from server:", (response));
            $(content).val('').focus(); //reset input box
            $('#save_chat_request_btn').removeClass('disabled');
        });
        
        // Handling the response for the 'save-chat-request' event
        socket.on('save_chat_response', (response) => {
            console.log("save_chat_response", response);
            if (response && (response.message || response.error_message)){
                var response_data = response.success ? response.data : null;
                var response_fro_username = response_data ? response_data.fro_username  : '...';
                var response_message = response_data ? (response_data.text || response.message) : response.error_message;
                var response_time = response_data ? (moment(response_data.updated).fromNow() || moment(response_data.created).fromNow() ) :moment(new Date()).fromNow();

                var server_sid = response.server_sid;
                // Clone the message element
                var messages_div = $('#messages');
                var clonedMessage = $('#message').removeClass('d-none').clone();

                //format the message for sender by simply adding `.message-out` class
                if (socket.id === server_sid){
                    $(clonedMessage).addClass('message-out');
                }
                // Update the user name, message text, and time
                clonedMessage.find('h6.text-reset').text(response_fro_username);
                clonedMessage.find('span.extra-small.text-muted').text(response_time);
                clonedMessage.find('div.message-text p').text(response_message);

                if(response.success === false && response_message ){
                    clonedMessage.find('div.message-text p').addClass('text-danger'); //format text-red if error occured during request.
                }

                // Append the cloned and updated message to the '.message-body'
                $(messages_div).append(clonedMessage);

                // Animate scrolling to the bottom, scrollheight of the `messages_div`
                $('.chat-body').animate({ scrollTop: messages_div.prop("scrollHeight") }, 500);
                $(content).val('').focus(); //reset input box
                $('#save-chat-request-btn').removeClass('disabled');

            }
        });

    });

}catch(e){
console.log(e);
}


    // const socket = io('http://127.0.0.1:5000');

    
    // const username = prompt("Enter your username:");
    // socket.emit('connect', "username");

    // // Handle sending messages
    // $('#send-button').click(() => {
    //     const message = $('#message-input').val();
    //     if (message) {
    //         socket.emit('save_chat_request', { 
    //             text: message,
    //             to_usernames: ['user1', 'user2'], // Replace with actual usernames
    //             from_username: username 
    //         });
    //         $('#message-input').val('');
    //     }
    // });

    // Listen for incoming messages
    socket.on('save_chat_response', (data) => {
        if (data.success) {
            displayMessage(data.data.text, 'from_username');
        } else {
            alert(data.error);
        }
    });

    // // Display message in chat history
    // function displayMessage(message, type) {
    //     const msgElement = `<div class="message ${type}"><span class="msg">${message}</span></div>`;
    //     $('#chat-history').append(msgElement);
    //     $('#chat-history').scrollTop($('#chat-history')[0].scrollHeight);
    // }

    // // Handle user typing notifications
    // $('#message-input').on('keypress', () => {
    //     socket.emit('typing_request', { from_username: username });
    // });

    // socket.on('typing_response', (data) => {
    //     // Optionally display typing notification
    //     console.log(data.message);
    // });

    // // Fetch chat history
    socket.emit('fetch_chat_request', username);
});
