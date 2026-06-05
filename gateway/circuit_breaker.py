import time
import random
from enum import Enum
from redis_client import redis


class CBState(str, Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


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
    state = await get_cb_state(provider)
    if state["status"] == CBState.CLOSED:
        return True
    if state["status"] == CBState.OPEN:
        elapsed = time.time() - state["last_failure_time"]
        if elapsed > config.get("half_open_ttl", 30):
            # Single probe: set half_open + probe flag
            await redis.hset(f"cb:{provider}", mapping={
                "status": CBState.HALF_OPEN,
                "probe_count": "1",
            })
            return True
        return False
    # HALF_OPEN: only allow if probe count hasn't been exceeded
    if state["status"] == CBState.HALF_OPEN:
        count = await redis.hget(f"cb:{provider}", "probe_count")
        if count and int(count) > 0:
            await redis.hincrby(f"cb:{provider}", "probe_count", -1)
            return True
        return False
    return True


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
