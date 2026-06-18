import os
import json
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator

from adapters import create_adapters
from routes import router as gateway_router, set_adapters
from redis_client import redis
from middleware.logging import setup_logging, request_id_middleware

logger = setup_logging("gateway")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Gateway starting up")

    # Load supplier configs from Redis, fallback to env vars
    supplier_configs = {}
    try:
        config_data = await redis.hgetall("supplier_configs")
        if config_data:
            for provider, cfg_str in config_data.items():
                supplier_configs[provider] = json.loads(cfg_str)
            logger.info(f"Loaded {len(supplier_configs)} supplier configs from Redis")
        elif os.getenv("OPENAI_API_KEY"):
            supplier_configs["openai"] = {
                "api_key": os.getenv("OPENAI_API_KEY"),
                "base_url": os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
            }
            logger.info("Loaded supplier config from env vars")
        else:
            logger.warning("No supplier configs found in Redis or env vars")
    except Exception as e:
        logger.warning(f"Redis unavailable, falling back to env vars: {e}")
        if os.getenv("OPENAI_API_KEY"):
            supplier_configs["openai"] = {
                "api_key": os.getenv("OPENAI_API_KEY"),
                "base_url": os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
            }

    adapters = create_adapters(supplier_configs)
    set_adapters(adapters)

    # Load pricing from Redis
    try:
        from pricing import reload_pricing
        await reload_pricing()
        logger.info("Pricing loaded from Redis")
    except Exception as e:
        logger.warning(f"Failed to load pricing from Redis: {e}")

    yield

    logger.info("Gateway shutting down")


app = FastAPI(title="LLM Gateway", lifespan=lifespan)

# Request ID middleware (uses @app.middleware("http") for streaming safety)
request_id_middleware(app)

_cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Instrumentator().instrument(app).expose(app)

from admin_routes import router as admin_router

app.include_router(gateway_router)
app.include_router(admin_router)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "internal_error", "request_id": getattr(request.state, "request_id", None)},
    )


@app.get("/health")
async def health():
    redis_ok = False
    try:
        await redis.ping()
        redis_ok = True
    except Exception:
        pass
    return {
        "status": "ok" if redis_ok else "degraded",
        "redis": "ok" if redis_ok else "unavailable",
    }
