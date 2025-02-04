from flask import Blueprint, app, render_template

showcase_bp = Blueprint('showcase', __name__)

@showcase_bp.route('/')
def index():
    try:
        return render_template('showcase/index.html')
    except Exception as e:
        print(f"Something went wrong: {e}")
        return f"Something went wrong: {e}"
    
from flask import jsonify
@showcase_bp.route("/routes")
def site_map():
    try:
        links = []
        # for rule in app.url_map.iter_rules():
        for rule in app.url_map._rules:
            """ Filter out rules we can't navigate to in a browser, and rules that require parameters """
            links.append({'url': rule.rule, 'view': rule.endpoint})
        return jsonify(links), 200
    except Exception as e:
        print(f"Something went wrong: {e}")
        return f"Something went wrong: {e}"

@showcase_bp.route('/redis-check')
def redis_check():
    
    from redis import Redis
    from os import getenv

    redis = Redis.from_url(getenv('REDIS_URL', 'redis://localhost:6379/0'))
    try:
        redis.ping()
        print("Connected to Redis!")
        return f"<h1>Connected to Redis!</h1>"
    
    except Exception as e:
        print(f"Could not connect to Redis: {e}")
        return f"Could not connect to Redis: {e}"