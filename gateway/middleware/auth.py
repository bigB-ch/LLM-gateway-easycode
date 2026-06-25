import hashlib
import asyncio
import time
from fastapi import Request, HTTPException
from redis_client import redis


def hash_key(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


async def verify_api_key(request: Request, allow_anthropic_auth: bool = False) -> dict:
    t_start = time.monotonic()

    raw_key = None
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        raw_key = auth[7:]
    elif allow_anthropic_auth:
        # Anthropic SDK uses x-api-key header
        raw_key = request.headers.get("x-api-key", "")

    if not raw_key:
        raise HTTPException(status_code=401, detail={"error": "invalid_api_key"})

    key_hash = hash_key(raw_key)

    try:
        data = await redis.hgetall(f"apikey:{key_hash}")
    except Exception:
        raise HTTPException(status_code=503, detail={"error": "service_unavailable"})

    # Redis miss: fallback to database lookup
    if not data:
        import httpx
        try:
            async with httpx.AsyncClient(timeout=5) as hc:
                r = await hc.get(
                    f"http://admin:8001/admin/api/keys/internal/lookup/{key_hash}",
                    headers={"X-Internal-Auth": "llm-gateway-internal"},
                )
                if r.status_code == 200:
                    key_data = r.json()
                    # Rebuild Redis cache
                    await redis.hset(f"apikey:{key_hash}", mapping={
                        "user_id": key_data["user_id"],
                        "rate_limit": str(key_data.get("rate_limit", 60)),
                        "status": key_data.get("status", "active"),
                        "model_allowlist": key_data.get("model_allowlist", ""),
                        "key_prefix": key_data.get("key_prefix", ""),
                    })
                    data = await redis.hgetall(f"apikey:{key_hash}")
        except Exception:
            pass

    if not data or data.get("status") != "active":
        raise HTTPException(status_code=401, detail={"error": "invalid_api_key"})

    # Check cached balance and plan availability from Redis
    user_id = data["user_id"]
    balance = 0
    has_plans = False
    try:
        bal_str = await redis.get(f"user_balance:{user_id}")
        if bal_str is not None:
            balance = int(bal_str)
        else:
            # Cache miss — fetch from admin service and cache it
            import httpx
            try:
                async with httpx.AsyncClient(timeout=5) as hc:
                    r = await hc.get(
                        f"http://admin:8001/admin/api/users/internal/balance/{user_id}",
                        headers={"X-Internal-Auth": "llm-gateway-internal"},
                    )
                    if r.status_code == 200:
                        u = r.json()
                        balance = int(u.get("balance", 0))
                        await redis.set(f"user_balance:{user_id}", str(balance), ex=3600)
            except Exception:
                pass
        plan_str = await redis.get(f"user_has_plans:{user_id}")
        has_plans = plan_str == "1"
    except Exception:
        pass

    return {
        "user_id": user_id,
        "rate_limit": int(data.get("rate_limit", 60)),
        "balance": balance,
        "has_plans": has_plans,
        "model_allowlist": data.get("model_allowlist", ""),
        "key_prefix": data.get("key_prefix", ""),
    }
