from flask_migrate import Migrate
from flask_mail import Mail
from flask_moment import Moment
from flask_session import Session

# Load environment variables
from dotenv import load_dotenv
load_dotenv()
from os import getenv

# Initialize extensions
f_session = Session()
mail = Mail()
migrate = Migrate()
moment = Moment()

from authlib.integrations.flask_client import OAuth
oauth = OAuth()

from flask_wtf.csrf import CSRFProtect
csrf = CSRFProtect()

from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()

from flask_bcrypt import Bcrypt
bcrypt = Bcrypt()

from flask_cors import CORS
cors = CORS()

from redis import Redis
# Initialize Redis client
redis = Redis.from_url(getenv('REDIS_URL', 'redis://localhost:6379/0'))

# Initialize Flask-Limiter with IP-based rate limiting
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
limiter = Limiter(
    key_func=get_remote_address,
    # default_limits=["200 per day", "50 per hour"]
    default_limits=["1 per second", "5 per minute"],  # Allow up to 1 request per second or a burst of 5 in a minute
    storage_uri=getenv('REDIS_URL', 'redis://localhost:6379/0')  # Ensure the Redis URL is correct
)


from flask_jwt_extended import JWTManager #, create_access_token, jwt_required, get_jwt_identity
jwt = JWTManager()

from faker import Faker
fake = Faker()

def config_app(app, config_name):
    """Configure app settings based on environment."""
    from web.config import app_config
    app.config.from_object(app_config[config_name])
    
# from flask_socketio import SocketIO
# socketio = SocketIO()
from flask_socketio import SocketIO
socketio = SocketIO(manage_session=False, cors_allowed_origins="*")

# from elasticsearch import Elasticsearch
# elastic_search=Elasticsearch(['http://localhost:9200'])

def init_ext(app):
    """Initialize all extensions."""
    db.init_app(app)
    f_session.init_app(app)
    bcrypt.init_app(app)
    cors.init_app(app)

    # s_manager.init_app(app)
    jwt.init_app(app)
    limiter.init_app(app)
    mail.init_app(app)
    migrate.init_app(app, db)
    moment.init_app(app)
    oauth.init_app(app)
    socketio.init_app(app)
    csrf.init_app(app)
    
def make_available():
    """Provide application metadata."""
    products_links = {
        'salesnet_link': 'salenset.techa.tech',
        'barman_link': 'barman.techa.tech',
        'paysafe_link': 'paysafe.techa.tech',
        'intellect_link': 'intellect.techa.tech',
        'workforce_link': 'workforce.techa.tech'
    }
    app_data = {
        'app_name': 'Salesnet',
        'hype': 'Your Digital Learning Companion.',
        'app_desc': 'Elite software engr team with special interest in artificial intelligence, data and hacking..',
        'app_desc_long': 'Elite software engr team with special interest in artificial intelligence, data and hacking..\n\
            Salesnet m-powers people & powers businesses to stay relevant with technologies and advancements.',
        'app_location': 'Graceland Estate, Lekki, Lagos, Nigeria.',
        'app_email': 'hi@techa.tech',
        'app_logo': getenv('LOGO_URL'),
        'site_logo': getenv('LOGO_URL'),
        'site_link': 'https://www.techa.tech',
        'whatsapp_link': 'https://www.techa.tech',
        'terms_link': 'https://www.techa.tech/terms',
        'policy_link': 'https://www.techa.tech/policy',
        'cookie_link': 'https://www.techa.tech/cookie',
        'github_link': 'https://github.com/russiantech',
        'fb_link': 'https://www.facebook.com/RussianTechs',
        'x_link': 'https://twitter.com/chris_jsmes',
        'instagram_link': 'https://www.instagram.com/chrisjsmz/',
        'linkedin_link': 'https://www.linkedin.com/in/chrisjsm',
        'youtube_link': 'https://www.youtube.com/@russian_developer',
    }

    # Combine app_data and products_links
    datas = {**app_data, **products_links}
    return datas
