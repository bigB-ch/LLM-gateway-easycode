import json
import time
import asyncio
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from admin_auth import require_admin, get_current_user
from redis_client import redis
from adapters import create_adapters, find_adapter, BaseAdapter
from routes import set_adapters, get_adapters
from circuit_breaker import get_cb_state, record_success

router = APIRouter(prefix="/gateway/admin")


class SupplierUpsert(BaseModel):
    provider: str
    api_key: str
    base_url: str
    balance: float | None = None


class AdminChatRequest(BaseModel):
    model: str
    messages: list[dict]
    temperature: float | None = None
    max_tokens: int | None = None


async def reload_adapters():
    configs = {}
    data = await redis.hgetall("supplier_configs")
    if data:
        for provider, cfg_str in data.items():
            configs[provider] = json.loads(cfg_str)
    adapters = create_adapters(configs)
    set_adapters(adapters)


# ── Supplier Management ──

@router.get("/suppliers")
async def list_suppliers(_admin: dict = Depends(require_admin)):
    data = await redis.hgetall("supplier_configs")
    suppliers = []
    for provider, cfg_str in data.items():
        cfg = json.loads(cfg_str)
        key = cfg.get("api_key", "")
        masked = key[:10] + "..." + key[-4:] if len(key) > 14 else "***"
        cb = await get_cb_state(provider)
        suppliers.append({
            "provider": provider,
            "api_key_masked": masked,
            "base_url": cfg.get("base_url", ""),
            "balance": cfg.get("balance", 0),
            "cb_status": cb["status"],
            "cb_failure_count": cb["failure_count"],
        })
    return suppliers


@router.post("/suppliers")
async def upsert_supplier(body: SupplierUpsert, _admin: dict = Depends(require_admin)):
    cfg = json.dumps({"api_key": body.api_key, "base_url": body.base_url, "balance": body.balance or 0})
    await redis.hset("supplier_configs", body.provider, cfg)
    await reload_adapters()
    return {
        "provider": body.provider,
        "api_key_masked": body.api_key[:10] + "..." + body.api_key[-4:] if len(body.api_key) > 14 else "***",
        "base_url": body.base_url,
    }


@router.delete("/suppliers/{provider}")
async def delete_supplier(provider: str, _admin: dict = Depends(require_admin)):
    await redis.hdel("supplier_configs", provider)
    await reload_adapters()
    return {"message": f"supplier {provider} deleted"}


@router.post("/suppliers/{provider}/health")
async def health_check_supplier(provider: str, _admin: dict = Depends(require_admin)):
    data = await redis.hget("supplier_configs", provider)
    if not data:
        raise HTTPException(status_code=404, detail={"error": "supplier_not_found"})
    cfg = json.loads(data)
    from adapters import ADAPTER_CLASSES
    adapter_cls = next(
        (cls for cls in ADAPTER_CLASSES if cls.provider_name == provider), None
    )
    if adapter_cls is None:
        return {"provider": provider, "healthy": False, "error": "no_adapter_class"}
    adapter = adapter_cls(api_key=cfg["api_key"], base_url=cfg["base_url"])
    try:
        healthy = await asyncio.wait_for(adapter.health_check(), timeout=10)
        return {"provider": provider, "healthy": healthy}
    except asyncio.TimeoutError:
        return {"provider": provider, "healthy": False, "error": "timeout"}
    except Exception as e:
        return {"provider": provider, "healthy": False, "error": str(e)}


@router.post("/suppliers/{provider}/balance")
async def check_balance(provider: str, _admin: dict = Depends(require_admin)):
    data = await redis.hget("supplier_configs", provider)
    if not data:
        raise HTTPException(status_code=404, detail={"error": "supplier_not_found"})
    cfg = json.loads(data)

    from adapters import ADAPTER_CLASSES
    adapter_cls = next(
        (cls for cls in ADAPTER_CLASSES if cls.provider_name == provider), None
    )
    if adapter_cls is None:
        return {"provider": provider, "balance": None, "error": "no_adapter_class"}

    adapter = adapter_cls(api_key=cfg["api_key"], base_url=cfg["base_url"])
    try:
        result = await asyncio.wait_for(adapter.get_balance(), timeout=10)
        if result:
            # Save balance to config
            cfg["balance"] = result["balance"]
            await redis.hset("supplier_configs", provider, json.dumps(cfg))
            return {"provider": provider, "balance": result["balance"], "currency": result["currency"]}
        return {"provider": provider, "balance": None, "error": "not_supported"}
    except asyncio.TimeoutError:
        return {"provider": provider, "balance": None, "error": "timeout"}
    except Exception as e:
        return {"provider": provider, "balance": None, "error": str(e)}


# ── Circuit Breaker Management ──

@router.get("/circuit-breakers")
async def list_circuit_breakers(_admin: dict = Depends(require_admin)):
    data = await redis.hgetall("supplier_configs")
    providers = list(data.keys())
    breakers = []
    for provider in providers:
        cb = await get_cb_state(provider)
        breakers.append({
            "provider": provider,
            "status": cb["status"],
            "failure_count": cb["failure_count"],
            "last_failure_time": cb["last_failure_time"],
        })
    return breakers


@router.post("/circuit-breakers/{provider}/reset")
async def reset_circuit_breaker(provider: str, _admin: dict = Depends(require_admin)):
    await record_success(provider)
    return {"message": f"circuit breaker for {provider} reset to closed"}


# ── Playground Chat ──

@router.post("/chat")
async def admin_chat(body: AdminChatRequest, _user: dict = Depends(get_current_user)):
    adapters = get_adapters()
    adapter = find_adapter(body.model, adapters)
    if adapter is None:
        raise HTTPException(status_code=400, detail={"error": "invalid_model"})

    from schemas import UnifiedRequest, UnifiedMessage
    messages = [UnifiedMessage(**m) for m in body.messages]
    req = UnifiedRequest(
        model=body.model,
        messages=messages,
        temperature=body.temperature,
        max_tokens=body.max_tokens,
    )

    t_start = time.time()
    try:
        response = await asyncio.wait_for(adapter.chat_completion(req), timeout=120)
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail={"error": "timeout"})
    except Exception as e:
        raise HTTPException(status_code=502, detail={"error": str(e)})

    latency_ms = int((time.time() - t_start) * 1000)
    result = response.model_dump()
    result["latency_ms"] = latency_ms
    return result
