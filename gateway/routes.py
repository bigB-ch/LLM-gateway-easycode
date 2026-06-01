import uuid
import json
import time
import asyncio
from fastapi import APIRouter, Request, HTTPException

from schemas import UnifiedRequest
from middleware.auth import verify_api_key
from middleware.ratelimit import check_rate_limit
from adapters import find_adapter
from circuit_breaker import should_attempt, record_success, record_failure
from pricing import calculate_cost
from config import CIRCUIT_BREAKER_CONFIG, UPSTREAM_TIMEOUT, MAX_RETRIES, RETRY_BACKOFF_BASE
from redis_client import redis

router = APIRouter(prefix="/v1")

_adapters = []


def set_adapters(adapters):
    global _adapters
    _adapters = adapters


@router.post("/chat/completions")
async def chat_completions(request: Request):
    # 1. Auth
    auth_info = await verify_api_key(request)
    user_id = auth_info["user_id"]
    rate_limit = auth_info["rate_limit"]

    # 2. Rate limit
    await check_rate_limit(user_id, rate_limit)

    # 3. Parse request
    body = await request.json()
    unified = UnifiedRequest(**body)
    request_id = f"req_{uuid.uuid4().hex[:16]}"

    # 4. Find adapter
    adapter = find_adapter(unified.model, _adapters)
    if adapter is None:
        raise HTTPException(status_code=400, detail={"error": "invalid_model"})

    # 5. Circuit breaker check
    cb_config = CIRCUIT_BREAKER_CONFIG.get(
        adapter.provider_name,
        {"failure_threshold": 3, "timeout_seconds": 30, "half_open_ttl": 30},
    )
    if not await should_attempt(adapter.provider_name, cb_config):
        raise HTTPException(status_code=503, detail={"error": "model_temporarily_unavailable"})

    # 6. Call provider with retries
    t_start = time.time()
    last_error = None
    for attempt in range(MAX_RETRIES + 1):
        try:
            response = await asyncio.wait_for(
                adapter.chat_completion(unified),
                timeout=UPSTREAM_TIMEOUT,
            )
            latency_ms = int((time.time() - t_start) * 1000)

            await record_success(adapter.provider_name)

            if response.usage:
                cost, bill_cost = calculate_cost(
                    unified.model,
                    response.usage.prompt_tokens,
                    response.usage.completion_tokens,
                )
                response.usage.total_tokens = response.usage.prompt_tokens + response.usage.completion_tokens
            else:
                cost, bill_cost = 0, 0

            # 7. Write usage log to Redis Stream
            log_entry = {
                "request_id": request_id,
                "user_id": user_id,
                "api_key_prefix": "",
                "model": unified.model,
                "provider": adapter.provider_name,
                "prompt_tokens": str(response.usage.prompt_tokens) if response.usage else "0",
                "completion_tokens": str(response.usage.completion_tokens) if response.usage else "0",
                "cost": str(cost),
                "bill_cost": str(bill_cost),
                "latency_ms": str(latency_ms),
                "status": "success",
                "error_msg": "",
            }
            await redis.xadd("usage_log_stream", log_entry)

            return response.model_dump()

        except asyncio.TimeoutError:
            last_error = "timeout"
        except Exception as e:
            last_error = str(e)

        if attempt < MAX_RETRIES:
            await asyncio.sleep(RETRY_BACKOFF_BASE * (2 ** attempt))

    # All retries failed
    latency_ms = int((time.time() - t_start) * 1000)
    await record_failure(adapter.provider_name, cb_config)

    log_entry = {
        "request_id": request_id,
        "user_id": user_id,
        "api_key_prefix": "",
        "model": unified.model,
        "provider": adapter.provider_name,
        "prompt_tokens": "0",
        "completion_tokens": "0",
        "cost": "0",
        "bill_cost": "0",
        "latency_ms": str(latency_ms),
        "status": "error",
        "error_msg": last_error or "unknown",
    }
    await redis.xadd("usage_log_stream", log_entry)

    raise HTTPException(status_code=503, detail={"error": "upstream_error"})


@router.get("/models")
async def list_models():
    models = []
    for adapter in _adapters:
        for pattern in adapter.model_patterns:
            models.append({"id": pattern.rstrip("-*"), "object": "model"})
    return {"object": "list", "data": models}
