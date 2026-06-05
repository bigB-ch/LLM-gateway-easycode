from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import text

from config import DATABASE_URL

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()


_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_users_status ON users(status)",
    "CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at)",
    "CREATE INDEX IF NOT EXISTS idx_api_keys_user_id ON api_keys(user_id)",
    "CREATE INDEX IF NOT EXISTS idx_api_keys_status ON api_keys(status)",
    "CREATE INDEX IF NOT EXISTS idx_usage_logs_user_created ON usage_logs(user_id, created_at DESC)",
    "CREATE INDEX IF NOT EXISTS idx_usage_logs_created_at ON usage_logs(created_at)",
    "CREATE INDEX IF NOT EXISTS idx_recharge_user_id ON recharge_records(user_id)",
    "CREATE INDEX IF NOT EXISTS idx_recharge_status ON recharge_records(status)",
    "CREATE INDEX IF NOT EXISTS idx_user_plans_user_id ON user_plans(user_id)",
    "CREATE INDEX IF NOT EXISTS idx_user_plans_expires ON user_plans(expires_at)",
]


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        for sql in _INDEXES:
            try:
                await conn.execute(text(sql))
            except Exception:
                pass
