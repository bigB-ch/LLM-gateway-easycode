import redis.asyncio as aioredis
from config import REDIS_URL

redis = aioredis.from_url(REDIS_URL, decode_responses=True)


async def get_redis():
    return redis
