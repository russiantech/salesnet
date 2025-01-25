from redis import Redis
from os import getenv

redis = Redis.from_url(getenv('REDIS_URL', 'redis://localhost:6379/0'))

try:
    redis.ping()
    print("Connected to Redis!")
except Exception as e:
    print(f"Could not connect to Redis: {e}")
