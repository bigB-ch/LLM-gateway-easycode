import hashlib
import asyncio
import time
from fastapi import Request, HTTPException
from redis_client import redis


def hash_key(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


async def verify_api_key(request: Request) -> dict:
    t_start = time.monotonic()

    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        elapsed = time.monotonic() - t_start
        if elapsed < 0.015:
            await asyncio.sleep(0.015 - elapsed)
        raise HTTPException(status_code=401, detail={"error": "invalid_api_key"})

    raw_key = auth[7:]
    key_hash = hash_key(raw_key)

    try:
        data = await redis.hgetall(f"apikey:{key_hash}")
    except Exception:
        raise HTTPException(status_code=503, detail={"error": "service_unavailable"})

    elapsed = time.monotonic() - t_start
    if elapsed < 0.015:
        await asyncio.sleep(0.015 - elapsed)

    if not data or data.get("status") != "active":
        raise HTTPException(status_code=401, detail={"error": "invalid_api_key"})

    return {
        "user_id": data["user_id"],
        "rate_limit": int(data.get("rate_limit", 60)),
    }
