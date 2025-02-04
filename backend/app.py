from os import getenv
from web import create_app

app = create_app('development')  # Set to 'production' if needed
# app = create_app('production')  # Set to 'production' if needed
print(app.config['REDIS_URL'])

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(getenv("PORT", 5000)))
    
    # from web.extensions import socketio as sio
    # sio.run(app=app, host='0.0.0.0', port=int(getenv("PORT", 5000)))