
from datetime import timedelta
from os import getenv, path

class Config:
    # Security
    SECRET_KEY = getenv('SECRET_KEY')  # Provide a default for local testing
    RESET_PASS_TOKEN_MAX_AGE = 3600  # Token valid for 1 hour

    # Flask JWT Extended
    JWT_SECRET_KEY = SECRET_KEY
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=10)  # Set expiration in days for clarity
    JWT_AUTH_USERNAME_KEY = 'username'
    JWT_AUTH_HEADER_PREFIX = 'Bearer'
    JWT_TOKEN_LOCATION = ['headers', 'cookies', 'query_string', 'json']

    # Payment Configuration
    FLUTTERWAVE_SK = getenv('FLUTTERWAVE_SK')
    FLUTTERWAVE_TK = getenv('FLUTTERWAVE_TK')

    # Base Configuration
    DEBUG = getenv('DEBUG', 'False') == 'True'
    FLASK_ENV = getenv('FLASK_ENV', 'production')
    WTF_CSRF_ENABLED = False  # Disable CSRF for development/testing
    IMAGES_LOCATION = path.join(path.abspath(path.dirname(__file__)), 'static', 'images')

    # Database & Storage Configuration
    REDIS_URL = getenv('REDIS_URL_DEV', 'redis://localhost:6379/0')
    SQLALCHEMY_DATABASE_URI = getenv('SQLALCHEMY_DATABASE_URI')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_POOL_SIZE = 50
    SQLALCHEMY_POOL_TIMEOUT = 30
    SQLALCHEMY_MAX_OVERFLOW = 20

    # Mail Configuration
    MAIL_SERVER = getenv('MAIL_SERVER', 'localhost')
    MAIL_PORT = int(getenv('MAIL_PORT', 25))
    MAIL_USE_TLS = getenv('MAIL_USE_TLS') is not None
    MAIL_USERNAME = getenv('MAIL_USERNAME')
    MAIL_PASSWORD = getenv('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = getenv('MAIL_DEFAULT_SENDER', 'Techa Support <support@techa.tech>')
    MAIL_DEBUG = 1

    # Payments
    STRIPE_SECRET_KEY = getenv('STRIPE_SECRET_KEY')
    PAYPAL_CLIENT_ID = getenv('PAYPAL_CLIENT_ID')
    PAYPAL_SECRET = getenv('PAYPAL_SECRET')
    PAYSTACK_SK = getenv('PAYSTACK_SK')

    # Miscellaneous
    LOG_TO_STDOUT = getenv('LOG_TO_STDOUT')
    ADMINS = ['jameschristo962@gmail.com', 'chrisjsmez@gmail.com']
    LANGUAGES = ['en', 'es']
    MS_TRANSLATOR_KEY = getenv('MS_TRANSLATOR_KEY')
    ELASTICSEARCH_URL = getenv('ELASTICSEARCH_URL')
    POSTS_PER_PAGE = 25

    # Uploads
    UPLOAD_FOLDER = getenv('UPLOAD_FOLDER', './uploads')
    MAX_CONTENT_PATH = int(getenv('MAX_CONTENT_PATH', 1024 * 1024))  # Default to 1MB
    ALLOWED_EXTENSIONS = getenv('ALLOWED_EXTENSIONS', 'jpg,jpeg,png,gif,mov,mp4').split(',')

    # Session Configuration
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = True  # Ensure HTTPS
    SESSION_TYPE = 'redis'
    SESSION_PERMANENT = False
    SESSION_USE_SIGNER = True
    SESSION_KEY_PREFIX = 'FLASK_SESSION'
    SESSION_REDIS = getenv('REDIS_URL_DEV', 'redis://localhost:6379/0')

    REDIS_CONFIG = {
        'CACHE_TYPE': 'redis',
        'CACHE_KEY_PREFIX': 'server_1',
        'CACHE_REDIS_HOST': getenv('REDIS_HOST_DEV', 'localhost'),
        'CACHE_REDIS_PORT': getenv('REDIS_PORT_DEV', 6379),
        'CACHE_REDIS_URL': REDIS_URL,
    }

class DevelopmentConfig(Config):
    REDIS_URL = getenv('REDIS_URL_DEV', 'redis://localhost:6379/0')
    SQLALCHEMY_DATABASE_URI = getenv('SQLALCHEMY_DATABASE_URI_DEV')
    FLASK_ENV = 'development'
    FLASK_DEBUG = True
    MAIL_DEBUG = True
    TESTING = False
    DEBUG = True

class ProductionConfig(Config):
    TESTING = False
    DEBUG = False  # Set to False in production
    FLASK_ENV = 'production'
    REDIS_URL = getenv('REDIS_URL')
    SQLALCHEMY_DATABASE_URI = getenv('SQLALCHEMY_DATABASE_URI')
    RAVE_SECRET_KEY = getenv('RAVE_LIVE_SECRET_KEY')

app_config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig
}
