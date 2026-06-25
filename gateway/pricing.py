import logging as _logging
_logger = _logging.getLogger("pricing")

# Fallback pricing — overridden by Redis "pricing_config" if admin customizes
_DEFAULT_PRICING = {
    "deepseek-v4-flash":  {"prompt": 1,  "completion": 2,   "cache": 0.02},
    "deepseek-v4-pro":    {"prompt": 3,  "completion": 6,   "cache": 0.025},
}
_DEFAULT_MARKUP = 1.5
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
            raw_models = cfg.get("models", _DEFAULT_PRICING)
            raw_markup = cfg.get("markup", _DEFAULT_MARKUP)
            # Validate pricing values
            if not isinstance(raw_markup, (int, float)) or raw_markup <= 0 or raw_markup > 100:
                _logger.warning(f"Invalid markup {raw_markup}, using default {_DEFAULT_MARKUP}")
                raw_markup = _DEFAULT_MARKUP
            if isinstance(raw_models, dict):
                validated = {}
                for m, prices in raw_models.items():
                    if isinstance(prices, dict):
                        p = prices.get("prompt", 0)
                        c = prices.get("completion", 0)
                        if (isinstance(p, (int, float)) and isinstance(c, (int, float))
                                and p >= 0 and c >= 0):
                            validated[m] = prices
                        else:
                            _logger.warning(f"Invalid pricing for model '{m}', skipping")
                if validated:
                    PRICING = validated
                else:
                    _logger.warning("No valid pricing models found, keeping defaults")
            else:
                _logger.warning("Invalid pricing config format, keeping defaults")
            MARKUP = raw_markup
    except Exception:
        import traceback
        _logger.warning(f"Failed to reload pricing from Redis: {traceback.format_exc()}")
    _last_reload = _time.time()


def get_pricing():
    return PRICING, MARKUP


async def calculate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> tuple[int, int]:
    """Return (cost_fen, bill_fen). Pricing values are CNY per 1M tokens."""
    await reload_pricing()
    pricing = PRICING.get(model)
    if pricing is None:
        _logger.warning(f"Unknown model '{model}' — using default pricing (prompt=1, completion=1)")
        pricing = {"prompt": 1, "completion": 1}
    if pricing.get("per_use"):
        cost_fen = round(pricing["per_use"] * 100)
        bill_fen = round(cost_fen * MARKUP)
        return cost_fen, bill_fen
    prompt_cost = (prompt_tokens / 1_000_000) * pricing["prompt"]
    completion_cost = (completion_tokens / 1_000_000) * pricing["completion"]
    cost_fen = round((prompt_cost + completion_cost) * 100)
    bill_fen = round(cost_fen * MARKUP)
    return cost_fen, bill_fen
