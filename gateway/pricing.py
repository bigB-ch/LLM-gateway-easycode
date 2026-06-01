PRICING = {
    "gpt-4":        {"prompt": 300, "completion": 600},
    "gpt-4-turbo":  {"prompt": 100, "completion": 300},
    "gpt-3.5-turbo":{"prompt": 5,   "completion": 15},
    "claude-3-opus":{"prompt": 150, "completion": 750},
    "claude-3-sonnet":{"prompt": 30,"completion": 150},
    "gemini-pro":   {"prompt": 5,   "completion": 15},
    "deepseek-chat":{"prompt": 2,   "completion": 2},
    "qwen-turbo":   {"prompt": 5,   "completion": 5},
}
MARKUP = 1.5


def calculate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> tuple[int, int]:
    pricing = PRICING.get(model, {"prompt": 10, "completion": 10})
    prompt_cost = (prompt_tokens / 1000) * pricing["prompt"]
    completion_cost = (completion_tokens / 1000) * pricing["completion"]
    cost_cents = int((prompt_cost + completion_cost) * 100)
    bill_cents = int(cost_cents * MARKUP)
    return cost_cents, bill_cents
