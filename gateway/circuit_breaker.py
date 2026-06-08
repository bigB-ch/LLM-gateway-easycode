import time
import random
from enum import Enum
from redis_client import redis


class CBState(str, Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


SHOULD_ATTEMPT_SCRIPT = """
local status = redis.call('HGET', KEYS[1], 'status')
if status == false or status == 'closed' then
  return 1
end
if status == 'open' then
  local last_failure = tonumber(redis.call('HGET', KEYS[1], 'last_failure_time') or '0')
  local elapsed = tonumber(ARGV[1]) - last_failure
  if elapsed > tonumber(ARGV[2]) then
    redis.call('HSET', KEYS[1], 'status', 'half_open', 'probe_count', '1')
    return 1
  end
  return 0
end
if status == 'half_open' then
  local count = tonumber(redis.call('HGET', KEYS[1], 'probe_count') or '0')
  if count > 0 then
    redis.call('HINCRBY', KEYS[1], 'probe_count', -1)
    return 1
  end
  return 0
end
return 0
"""


async def get_cb_state(provider: str) -> dict:
    key = f"cb:{provider}"
    data = await redis.hgetall(key)
    if not data:
        return {"status": CBState.CLOSED, "failure_count": 0, "last_failure_time": 0}
    return {
        "status": CBState(data.get("status", "closed")),
        "failure_count": int(data.get("failure_count", 0)),
        "last_failure_time": float(data.get("last_failure_time", 0)),
    }


async def should_attempt(provider: str, config: dict) -> bool:
    key = f"cb:{provider}"
    now = time.time()
    half_open_ttl = config.get("half_open_ttl", 30)
    result = await redis.eval(SHOULD_ATTEMPT_SCRIPT, 1, key, str(now), str(half_open_ttl))
    return result == 1


async def record_success(provider: str):
    await redis.hset(f"cb:{provider}", mapping={
        "status": CBState.CLOSED,
        "failure_count": "0",
        "last_failure_time": "0",
        "probe_count": "0",
    })


async def record_failure(provider: str, config: dict):
    key = f"cb:{provider}"
    current = await redis.hget(key, "failure_count")
    count = int(current or 0) + 1

    if count >= config.get("failure_threshold", 3):
        await redis.hset(key, mapping={
            "status": CBState.OPEN,
            "failure_count": str(count),
            "last_failure_time": str(time.time()),
        })
    else:
        await redis.hset(key, mapping={
            "status": CBState.CLOSED,
            "failure_count": str(count),
            "last_failure_time": str(time.time()),
        })
    # Auto-expire CB state after 1 hour
    await redis.expire(key, 3600)
