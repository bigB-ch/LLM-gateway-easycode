import uuid
import os
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select

from database import init_db, async_session
from models.user import User
from crypto import hash_password
from routes.auth import router as auth_router
from routes.keys import router as keys_router
from routes.users import router as users_router
from routes.reports import router as reports_router
from routes.plans import router as plans_router
from routes.system import router as system_router
from consumer import run_consumer


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()

    # Auto-create admin user on first startup
    admin_email = os.getenv("ADMIN_EMAIL", "admin@example.com")
    admin_password = os.getenv("ADMIN_PASSWORD", "admin123")
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

    consumer_task = asyncio.create_task(run_consumer())
    yield
    consumer_task.cancel()


app = FastAPI(title="LLM Gateway Admin", lifespan=lifespan)

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


@app.get("/admin/api/health")
async def health():
    return {"status": "ok"}
