import time
from fastapi import HTTPException
from redis_client import redis

SLIDING_WINDOW_LUA = """
local key = KEYS[1]
local window = tonumber(ARGV[1])
local limit = tonumber(ARGV[2])
local now = tonumber(ARGV[3])

redis.call('ZREMRANGEBYSCORE', key, 0, now - window)
local current = redis.call('ZCARD', key)
if current >= limit then
    return 0
end
redis.call('ZADD', key, now, now .. ':' .. string.format('%.0f', now * 1e6 % 1e6))
redis.call('EXPIRE', key, window)
return 1
"""


async def check_rate_limit(user_id: str, rate_limit: int, window: int = 60) -> None:
    key = f"ratelimit:{user_id}"
    now = time.time()
    result = await redis.eval(SLIDING_WINDOW_LUA, 1, key, str(window), str(rate_limit), str(now))
    if result == 0:
        raise HTTPException(
            status_code=429,
            detail={"error": "rate_limit_exceeded", "retry_after": window},
            headers={"Retry-After": str(window)},
        )
