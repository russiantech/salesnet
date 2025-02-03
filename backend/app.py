from os import getenv
from web import create_app

# app = create_app('development')  # Set to 'production' if needed
app = create_app('production')  # Set to 'production' if needed

from flask import jsonify
@app.route("/routes")
def site_map():
    links = []
    # for rule in app.url_map.iter_rules():
    for rule in app.url_map._rules:
        """ Filter out rules we can't navigate to in a browser, and rules that require parameters """
        links.append({'url': rule.rule, 'view': rule.endpoint})
    return jsonify(links), 200

@app.route("/redis-test")
def test_render_redis():
    import redis
    try:
        r = redis.Redis(host='red-cug0gotsvqrc73fukjn0', port=6379)
        r.ping()  # Test connection
        print("Connected to Redis!")
    except redis.exceptions.ConnectionError as e:
        print(f"Connection error: {e}")

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(getenv("PORT", 5000)))
    
    # from web.extensions import socketio as sio
    # sio.run(app=app, host='0.0.0.0', port=int(getenv("PORT", 5000)))
    
