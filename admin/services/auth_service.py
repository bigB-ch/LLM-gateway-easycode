import uuid
from datetime import datetime, timedelta, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User
from crypto import hash_password, verify_password, generate_verification_code
import redis_client


def validate_password(password: str) -> str | None:
    """Return error message if password is invalid, or None if valid."""
    if len(password) < 8:
        return "密码至少 8 位"
    if not any(c.isupper() for c in password):
        return "密码需包含大写字母"
    if not any(c.islower() for c in password):
        return "密码需包含小写字母"
    if not any(c.isdigit() for c in password):
        return "密码需包含数字"
    return None


async def register_user(db: AsyncSession, username: str, email: str, password: str) -> User:
    password_hash = hash_password(password)
    user = User(
        id=uuid.uuid4(),
        username=username,
        email=email,
        password_hash=password_hash,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def send_verification_code(redis, email: str) -> bool:
    ttl_key = f"email_cooldown:{email}"
    if await redis.exists(ttl_key):
        return False  # 60s cooldown

    daily_key = f"email_daily:{email}"
    daily_count = await redis.get(daily_key)
    if daily_count and int(daily_count) >= 5:
        return False

    code = generate_verification_code()
    code_key = f"verification_code:{email}"
    await redis.setex(code_key, 300, code)  # 5 min TTL
    await redis.setex(ttl_key, 60, "1")
    await redis.incr(daily_key)
    if not daily_count:
        await redis.expire(daily_key, 86400)

    from services.email_service import send_verification_email
    await send_verification_email(email, code)
    return True


async def verify_code_and_activate(redis, db: AsyncSession, email: str, code: str) -> User | None:
    code_key = f"verification_code:{email}"
    stored = await redis.get(code_key)
    if stored is None or stored != code:
        return None

    await redis.delete(code_key)
    user = await get_user_by_email(db, email)
    if user and user.status == "active":
        return user
    return None


async def authenticate_user(db: AsyncSession, email: str, password: str) -> User | None:
    user = await get_user_by_email(db, email)
    if user is None:
        return None
    if user.status != "active":
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


async def get_user_by_username(db: AsyncSession, username: str) -> User | None:
    result = await db.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()


async def authenticate_user_by_username(db: AsyncSession, username: str, password: str) -> User | None:
    user = await get_user_by_username(db, username)
    if user is None:
        return None
    if user.status != "active":
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user
