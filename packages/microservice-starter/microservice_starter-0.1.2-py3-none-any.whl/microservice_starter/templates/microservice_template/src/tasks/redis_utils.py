from ..configs.cache import get_redis

redis_client = get_redis()


def redis_get(key):
    return redis_client.get(key)


def redis_set(key: str, max_age: int, data: any) -> None:
    redis_client.setex(key, max_age, data)


def redis_delete(key: str) -> None:
    redis_client.delete(key)
