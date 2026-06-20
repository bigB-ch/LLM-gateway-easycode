# Fallback pricing — overridden by Redis "pricing_config" if admin customizes
_DEFAULT_PRICING = {
    "deepseek-v4-flash":  {"prompt": 1,  "completion": 2,   "cache": 0.02},
    "deepseek-v4-pro":    {"prompt": 3,  "completion": 6,   "cache": 0.025},
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
