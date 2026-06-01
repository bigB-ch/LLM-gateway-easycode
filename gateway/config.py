import os
from dotenv import load_dotenv

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")

CIRCUIT_BREAKER_CONFIG = {
    "openai":       {"failure_threshold": 5, "timeout_seconds": 30, "half_open_ttl": 30},
    "anthropic":    {"failure_threshold": 5, "timeout_seconds": 30, "half_open_ttl": 30},
    "google":       {"failure_threshold": 5, "timeout_seconds": 30, "half_open_ttl": 30},
    "deepseek":     {"failure_threshold": 3, "timeout_seconds": 30, "half_open_ttl": 60},
    "qwen":         {"failure_threshold": 3, "timeout_seconds": 30, "half_open_ttl": 60},
}

UPSTREAM_TIMEOUT = 30
MAX_RETRIES = 2
RETRY_BACKOFF_BASE = 1.0
