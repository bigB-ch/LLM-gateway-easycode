import uuid
import os
import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import select, text

from database import init_db, async_session, engine
from models.user import User
from crypto import hash_password
from routes.auth import router as auth_router
from routes.keys import router as keys_router
from routes.users import router as users_router
from routes.reports import router as reports_router
from routes.plans import router as plans_router
from routes.system import router as system_router
from routes.store import router as store_router
from consumer import run_consumer
from middleware import setup_logging, RequestIDMiddleware
import redis_client

logger = setup_logging("admin")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Admin starting up, initializing database")
    await init_db()
    logger.info("Database initialized")

    # Auto-create admin user on first startup
    admin_email = os.getenv("ADMIN_EMAIL", "admin@example.com")
    admin_password = os.getenv("ADMIN_PASSWORD", "Admin123")
    async with async_session() as session:
        result = await session.execute(select(User).where(User.email == admin_email))
        if result.scalar_one_or_none() is None:
            admin_user = User(
                id=uuid.uuid4(),
                username="admin",
                email=admin_email,
                password_hash=hash_password(admin_password),
                role="super_admin",
            )
            session.add(admin_user)
            await session.commit()
            logger.info(f"Admin user created: {admin_email}")

    consumer_task = asyncio.create_task(run_consumer())
    logger.info("Consumer started")
    yield
    consumer_task.cancel()
    logger.info("Admin shutting down")


app = FastAPI(title="LLM Gateway Admin", lifespan=lifespan)

# Request ID middleware
app.add_middleware(RequestIDMiddleware)

_cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(keys_router)
app.include_router(users_router)
app.include_router(reports_router)
app.include_router(plans_router)
app.include_router(system_router)
app.include_router(store_router)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "internal_error", "request_id": getattr(request.state, "request_id", None)},
    )


@app.get("/admin/api/health")
async def health():
    db_ok = False
    redis_ok = False
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        pass
    try:
        await redis_client.redis.ping()
        redis_ok = True
    except Exception:
        pass
    status = "ok" if (db_ok and redis_ok) else "degraded" if (db_ok or redis_ok) else "down"
    return {
        "status": status,
        "database": "ok" if db_ok else "unavailable",
        "redis": "ok" if redis_ok else "unavailable",
    }
