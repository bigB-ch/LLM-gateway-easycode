import os
import json
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from adapters import create_adapters
from routes import router as gateway_router, set_adapters
from redis_client import redis


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load supplier configs from Redis, fallback to env vars
    supplier_configs = {}
    config_data = await redis.hgetall("supplier_configs")
    if config_data:
        for provider, cfg_str in config_data.items():
            supplier_configs[provider] = json.loads(cfg_str)
    else:
        if os.getenv("OPENAI_API_KEY"):
            supplier_configs["openai"] = {
                "api_key": os.getenv("OPENAI_API_KEY"),
                "base_url": os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
            }
    adapters = create_adapters(supplier_configs)
    set_adapters(adapters)
    yield


app = FastAPI(title="LLM Gateway", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

Instrumentator().instrument(app).expose(app)

app.include_router(gateway_router)


@app.get("/health")
async def health():
    return {"status": "ok"}
