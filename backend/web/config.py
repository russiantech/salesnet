
from datetime import timedelta
from os import getenv, path

from web.apis.utils.helpers import strtobool_custom

class Config:
    
    # Security
    SECRET_KEY = getenv('SECRET_KEY')
    RESET_PASS_TOKEN_MAX_AGE = 3600  # Token valid for 1 hour (3600 seconds)
    
    # Flask Jwt extended
    JWT_SECRET_KEY = SECRET_KEY
    # JWT_SECRET_KEY = getenv('JWT_SECRET_KEY', 'JWT_SUPER_SECRET')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(10 ** 6)
    JWT_AUTH_USERNAME_KEY = 'username'
    JWT_AUTH_HEADER_PREFIX = 'Bearer'
    JWT_TOKEN_LOCATION = ['headers', 'cookies', 'query_string', 'json']
    # JWT_TOKEN_LOCATION = ['headers', 'cookies', 'query_string', 'json']
    # JWT_TOKEN_LOCATION = ['headers', 'query_string', 'json', 'cookies']

    # print("JWT_SECRET_KEY", JWT_SECRET_KEY)
    # Payment
    RAVE_LIVE_SECRET_KEY = getenv('RAVE_LIVE_SECRET_KEY')
    RAVE_TEST_SECRET_KEY = getenv('RAVE_TEST_SECRET_KEY')
    
    """Base configuration."""
    # TESTING = getenv('TESTING') == True # This would'nt allow flask-mail send actual email in real time.
    DEBUG = getenv('DEBUG') == True
    FLASK_ENV = getenv('FLASK_ENV', 'production')
    WTF_CSRF_ENABLED = False  # Disable CSRF for development/testing
    
    # IMAGES_LOCATION = getenv('IMAGES_LOCATION')
    IMAGES_LOCATION = path.join(path.abspath(path.dirname(__file__)), 'static', 'images')
    
    # Database & Storages
    REDIS_URL = "redis://localhost:6379/0"
    SQLALCHEMY_DATABASE_URI = getenv('DATABASE_URI') # or 'sqlite:///'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_POOL_SIZE = 50
    SQLALCHEMY_POOL_TIMEOUT = 30
    SQLALCHEMY_MAX_OVERFLOW = 20

    # Mail configuration
    MAIL_SERVER = getenv('MAIL_SERVER', 'localhost')
    MAIL_PORT = int(getenv('MAIL_PORT', 25))
    MAIL_USE_TLS = getenv('MAIL_USE_TLS') is not None
    MAIL_USERNAME = getenv('MAIL_USERNAME')
    MAIL_PASSWORD = getenv('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = getenv('MAIL_DEFAULT_SENDER', 'Techa Support <support@techa.tech>')
    MAIL_DEBUG = 1

    # Miscellaneous
    LOG_TO_STDOUT = getenv('LOG_TO_STDOUT')
    ADMINS = ['jameschristo962@gmail.com', 'chrisjsmez@gmail.com']
    LANGUAGES = ['en', 'es']
    MS_TRANSLATOR_KEY = getenv('MS_TRANSLATOR_KEY')
    ELASTICSEARCH_URL = getenv('ELASTICSEARCH_URL')
    POSTS_PER_PAGE = 25

    # Uploads
    UPLOAD_FOLDER = getenv('UPLOAD_FOLDER', './uploads')
    MAX_CONTENT_PATH = int(getenv('MAX_CONTENT_PATH') or 1024 * 1024)  # Default to 1MB
    ALLOWED_EXTENSIONS = getenv('ALLOWED_EXTENSIONS', 'jpg, jpeg, png, gif, mov, mp4').split(',')

    # Session
    SESSION_TYPE = 'filesystem'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = True  # Ensure HTTPS

class DevelopmentConfig(Config):
    """Development-specific configuration."""
    FLASK_ENV = 'development'
    FLASK_DEBUG = True
    FLASK_APP = 'app.py'
    MAIL_DEBUG = True
    DEFAULT_MAIL_SENDER = getenv('DEFAULT_MAIL_SENDER') 
    DEFAULT_MAIL_TOKEN = getenv('mailtrap_token') 
    MAIL_SERVER = getenv('mailtrap_server')
    MAIL_PORT = getenv('mailtrap_port')
    MAIL_USERNAME = getenv('mailtrap_username')
    MAIL_PASSWORD = getenv('mailtrap_password')

class TestingConfig(Config):
    """Testing-specific configuration."""
    # TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///'  # In-memory database for tests
    
    # configuration of mail  
    MAIL_PORT = int(getenv('MAIL_PORT', 587))  # Ensure this is an integer
    MAIL_USE_TLS = bool(strtobool_custom(getenv('MAIL_USE_TLS', 'False'))) #ensure type is compatible to avoid Flask-Mail [SSL: WRONG_VERSION_NUMBER] wrong version number (_ssl.c:1123)
    MAIL_USE_SSL = bool(strtobool_custom(getenv('MAIL_USE_SSL', 'False')))
    MAIL_DEFAULT_SENDER = getenv('MAIL_DEFAULT_SENDER', 'Techa Support <support@techa.tech>')
    MAIL_SERVER = getenv('MAIL_SERVER')
    MAIL_USERNAME = getenv('MAIL_USERNAME')
    MAIL_PASSWORD = getenv('MAIL_PASSWORD')

class ProductionConfig(Config):
    TESTING = False
    DEBUG = True
    FLASK_ENV = 'production'
    
    # Mail configuration
    MAIL_DEBUG = False
    MAIL_DEFAULT_SENDER = ('Techa', getenv('DEFAULT_MAIL_SENDER', getenv('MAIL_USERNAME', 'hi@techa.tech')) )
    MAIL_SERVER = getenv('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(getenv('MAIL_PORT', 587))
    MAIL_USE_TLS = getenv('MAIL_USE_TLS') is not None
    MAIL_USERNAME = getenv('MAIL_USERNAME')
    MAIL_PASSWORD = getenv('MAIL_PASSWORD')

    SQLALCHEMY_ECHO = False
    # Add production-specific settings here
    
    """ prevents Shared Session Cookies, this can help ensure other similar browsers would not have access to same first logged-in user account """
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = True  # If using HTTPS
    """  SESSION_TYPE = 'redis' # 'filesystem', 'mongodb' etc #//only suitable for small projects """

app_config = {
    'testing': TestingConfig,
    'development': DevelopmentConfig,
    'production': ProductionConfig
}