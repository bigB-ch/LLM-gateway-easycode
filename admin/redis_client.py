import redis.asyncio as aioredis
from config import REDIS_URL

redis = aioredis.from_url(REDIS_URL, decode_responses=True, protocol=2)


async def get_redis():
    return redis


async def sync_balance_cache(user_id: str, balance: int):
    """Update the Redis balance cache for a user after balance changes.
    Called after topup, redeem, plan purchase, or any balance modification."""
    try:
        await redis.set(f"user_balance:{user_id}", str(balance), ex=3600)
    except Exception:
        pass
