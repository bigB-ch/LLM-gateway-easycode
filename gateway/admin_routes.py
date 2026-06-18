import json
import time
import asyncio
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from admin_auth import require_admin, get_current_user
from redis_client import redis
from adapters import create_adapters, find_adapter, BaseAdapter
from routes import set_adapters, get_adapters, _KNOWN_MODELS
from circuit_breaker import get_cb_state, record_success
from pricing import PRICING, MARKUP

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
        # Return stored balance if adapter not found
        stored_balance = cfg.get("balance", 0)
        return {"provider": provider, "balance": stored_balance, "currency": "CNY", "cached": True}

    adapter = adapter_cls(api_key=cfg["api_key"], base_url=cfg["base_url"])
    try:
        result = await asyncio.wait_for(adapter.get_balance(), timeout=10)
        if result:
            # Save balance to config
            cfg["balance"] = result["balance"]
            await redis.hset("supplier_configs", provider, json.dumps(cfg))
            return {"provider": provider, "balance": result["balance"], "currency": result["currency"]}
        # If adapter doesn't support balance query, return stored balance
        stored_balance = cfg.get("balance", 0)
        return {"provider": provider, "balance": stored_balance, "currency": "CNY", "cached": True}
    except asyncio.TimeoutError:
        stored_balance = cfg.get("balance", 0)
        return {"provider": provider, "balance": stored_balance, "currency": "CNY", "cached": True, "error": "timeout"}
    except Exception as e:
        stored_balance = cfg.get("balance", 0)
        return {"provider": provider, "balance": stored_balance, "currency": "CNY", "cached": True, "error": str(e)}


# ── Model Catalog ──

_MODEL_META = {
    "deepseek-v4-flash": {"tags": "Open Weights", "desc": "Efficient lightweight MoE model, 284B total/13B active params, native 1M+ context. Fast inference, low cost."},
    "deepseek-v4-pro": {"tags": "Open Weights", "desc": "Flagship MoE model, 1.6T total/49B active params, native 1M+ context. Top math, coding, reasoning."},
    "qwen-plus": {"tags": "text", "desc": "Qwen3 Plus model, merges thinking and non-thinking modes, reasoning surpasses QwQ."},
    "qwen3.6-plus": {"tags": "thinking,vision,text", "desc": "Qwen3.6 native vision-language Plus model, strong in agentic coding, OCR, multimodal recognition."},
    "glm-4.7": {"tags": "Reasoning,Tools,Open Weights,204.8K", "desc": "GLM-4.7 by Zhipu AI, supports reasoning and tool calling, 204.8K context."},
    "glm-5": {"tags": "Reasoning,Tools,Open Weights,204.8K", "desc": "GLM-5 next-gen model by Zhipu AI, enhanced reasoning and tool calling."},
    "glm-5.1": {"tags": "text,reasoning", "desc": "Zhipu latest model, coding ability close to Sonnet 4.6. Supports text generation and deep reasoning."},
    "kimi-k2.5": {"tags": "Reasoning,Tools,Files,Open Weights,Vision,262.1K", "desc": "Kimi-K2.5 supports reasoning, tool calling, file processing, vision, 262K context."},
    "kimi-k2.6": {"tags": "Reasoning,Tools,Files,Vision", "desc": "Kimi K2.6 - most intelligent model, top scores in HLE, SWE-Bench Pro, DeepSearchQA."},
    "MiniMax-M2.5": {"tags": "Tools,Open Weights,194K", "desc": "MiniMax-M2.5 flagship open-source model, SOTA in coding, tool calling and office scenarios."},
    "doubao-seedance-2-0-260128": {"tags": "video", "desc": "ByteDance Seedance 2.0 professional multi-modal video model, supports image/video/audio input."},
    "doubao-seedance-2-0-fast-260128": {"tags": "video", "desc": "Seedance 2.0 fast variant, inherits core features with faster generation speed."},
    "kling-v1": {"tags": "video", "desc": "Kuaishou Kling video generation model v1."},
    "kling-v2-1": {"tags": "text2video,img2video", "desc": "Kling v2.1 supports text-to-video and image-to-video generation."},
    "kling-v2-1-master": {"tags": "text2video,img2video", "desc": "Kling v2.1 master high-end video model with improved spatio-temporal attention and character dynamics."},
    "kling-v2-master": {"tags": "text2video,img2video", "desc": "Kling v2 master high-end video model from Kuaishou Kling AI."},
    "kling-v2-5-turbo": {"tags": "text2video,img2video", "desc": "Kling 2.5 Turbo: faster generation, lower cost, smoother motion."},
    "kling-v2-6": {"tags": "text2video,img2video", "desc": "Kling v2.6 supports text/image-to-video with synchronized audio generation."},
    "kling-v3": {"tags": "text2video,img2video", "desc": "Kling 3.0 AI professional video production system, supports native 2K/4K output, Canvas Agent."},
    "kling-v3-omni": {"tags": "text2video,img2video", "desc": "Kling 3.0 Omni multimodal video generation model."},
    "xunfei-qwen": {"tags": "text", "desc": "Xunfei MaaS Qwen model, hosted on iFlytek cloud."},
}

@router.get("/models")
async def list_models_catalog(_user: dict = Depends(get_current_user)):
    """Return models with user-facing prices (already includes markup)."""
    from pricing import reload_pricing, PRICING, MARKUP
    await reload_pricing()
    _pricing, _markup = PRICING, MARKUP
    models = []
    for provider, model_list in _KNOWN_MODELS.items():
        for model in model_list:
            pricing = _pricing.get(model, {"prompt": 10, "completion": 10})
            meta = _MODEL_META.get(model, {})
            models.append({
                "model": model,
                "provider": provider,
                "input_price": round(pricing["prompt"] * _markup, 4),
                "output_price": round(pricing["completion"] * _markup, 4),
                "cache_price": round(pricing.get("cache", 0) * _markup, 4),
                "per_use": round(pricing.get("per_use", 0) * _markup, 4),
                "tags": meta.get("tags", ""),
                "description": meta.get("desc", ""),
            })
    return {"object": "list", "data": models}


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
    # Rate limit: max 20 Playground calls per user per hour
    user_id = _user.get("user_id", "")
    rate_key = f"playground_rate:{user_id}"
    count = await redis.incr(rate_key)
    if count == 1:
        await redis.expire(rate_key, 3600)
    if count > 20:
        raise HTTPException(status_code=429, detail={"error": "playground_limit", "message": "每小时最多 20 次试用，请创建 API Key 正式调用"})

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
