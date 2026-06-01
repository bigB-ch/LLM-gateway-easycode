import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import init_db
from routes.auth import router as auth_router
from routes.keys import router as keys_router
from routes.users import router as users_router
from routes.reports import router as reports_router
from routes.plans import router as plans_router
from consumer import run_consumer


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    consumer_task = asyncio.create_task(run_consumer())
    yield
    consumer_task.cancel()


app = FastAPI(title="LLM Gateway Admin", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(keys_router)
app.include_router(users_router)
app.include_router(reports_router)
app.include_router(plans_router)


@app.get("/admin/api/health")
async def health():
    return {"status": "ok"}
