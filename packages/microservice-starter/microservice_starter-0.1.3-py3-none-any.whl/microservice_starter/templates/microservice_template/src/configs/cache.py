import redis

from .environment import get_environment_variables  # Import environment loader

# Load environment variables
env = get_environment_variables()

# Connect to Redis
redis_instance = redis.StrictRedis(
    host=env.REDIS_CONTAINER_NAME, port=env.REDIS_PORT, decode_responses=True
)


def get_redis():
    return redis_instance
