# Fallback pricing — overridden by Redis "pricing_config" if admin customizes
_DEFAULT_PRICING = {
    # DeepSeek
    "deepseek-v4-flash":  {"prompt": 1,  "completion": 2,   "cache": 0.02},
    "deepseek-v4-pro":    {"prompt": 3,  "completion": 6,   "cache": 0.025},
    # Qwen / Alibaba
    "qwen-turbo":         {"prompt": 0.5,"completion": 0.5},
    "qwen-plus":          {"prompt": 0.8,"completion": 2,   "cache": 0.08},
    "qwen-max":           {"prompt": 2.8,"completion": 8.4},
    "qwen3.6-plus":       {"prompt": 2,  "completion": 12,  "cache": 0.2},
    # Zhipu GLM
    "glm-4.7":            {"prompt": 0.27,"completion": 1.1, "cache": 0.55},
    "glm-5":              {"prompt": 0.75,"completion": 2.4},
    "glm-5.1":            {"prompt": 6,  "completion": 24,  "cache": 1.2},
    # Moonshot Kimi
    "kimi-k2.5":          {"prompt": 0.55,"completion": 2.76},
    "kimi-k2.6":          {"prompt": 6.5,"completion": 27,  "cache": 1.0},
    # ByteDance Doubao
    "doubao-seedance-2-0-260128":     {"prompt": 51,"completion": 51},
    "doubao-seedance-2-0-fast-260128":{"prompt": 37,"completion": 37},
    # MiniMax
    "MiniMax-M2.5":       {"prompt": 2.1,"completion": 8.4},
    # Kuaishou Kling
    "kling-v1":           {"prompt": 75,"completion": 75},
    "kling-v1-5":         {"prompt": 75,"completion": 75},
    "kling-v1-6":         {"prompt": 75,"completion": 75},
    "kling-video-o1":     {"prompt": 75,"completion": 75},
    "kling-v2-1":         {"prompt": 0,  "completion": 0,  "per_use": 0.4},
    "kling-v2-1-master":  {"prompt": 0,  "completion": 0,  "per_use": 2},
    "kling-v2-master":    {"prompt": 0,  "completion": 0,  "per_use": 1},
    "kling-v2-5-turbo":   {"prompt": 0,  "completion": 0,  "per_use": 0.3},
    "kling-v2-6":         {"prompt": 0,  "completion": 0,  "per_use": 1.2},
    "kling-v3":           {"prompt": 0,  "completion": 0,  "per_use": 1.2},
    "kling-v3-omni":      {"prompt": 0,  "completion": 0,  "per_use": 1},
    # Xunfei MaaS
    "xunfei-qwen": {"prompt": 0.8, "completion": 2},
}
_DEFAULT_MARKUP = 1.5

# Runtime pricing — initialized from defaults, auto-refreshes from Redis every 10s
import time as _time
PRICING = dict(_DEFAULT_PRICING)
MARKUP = _DEFAULT_MARKUP
_last_reload = 0
_RELOAD_TTL = 10  # seconds


async def reload_pricing(force=False):
    """Reload pricing from Redis. Called on startup and periodically."""
    global PRICING, MARKUP, _last_reload
    if not force and _time.time() - _last_reload < _RELOAD_TTL:
        return
    try:
        from redis_client import redis
        import json
        data = await redis.get("pricing_config")
        if data:
            cfg = json.loads(data)
            PRICING = cfg.get("models", _DEFAULT_PRICING)
            MARKUP = cfg.get("markup", _DEFAULT_MARKUP)
    except Exception:
        pass
    _last_reload = _time.time()


def get_pricing():
    return PRICING, MARKUP


async def calculate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> tuple[int, int]:
    """Return (cost_fen, bill_fen). Pricing values are CNY per 1M tokens."""
    await reload_pricing()
    pricing = PRICING.get(model, {"prompt": 1, "completion": 1})
    if pricing.get("per_use"):
        cost_fen = round(pricing["per_use"] * 100)
        bill_fen = round(cost_fen * MARKUP)
        return cost_fen, bill_fen
    prompt_cost = (prompt_tokens / 1_000_000) * pricing["prompt"]
    completion_cost = (completion_tokens / 1_000_000) * pricing["completion"]
    cost_fen = round((prompt_cost + completion_cost) * 100)
    bill_fen = round(cost_fen * MARKUP)
    return cost_fen, bill_fen
