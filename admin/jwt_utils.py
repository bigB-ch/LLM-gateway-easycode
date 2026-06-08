import secrets
from datetime import datetime, timedelta, timezone
import jwt
from config import JWT_SECRET, JWT_ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_DAYS


def _make_jti() -> str:
    return secrets.token_hex(16)


def create_access_token(user_id: str, role: str) -> str:
    payload = {
        "sub": user_id,
        "role": role,
        "type": "access",
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def create_refresh_token(user_id: str) -> tuple[str, str]:
    jti = _make_jti()
    payload = {
        "sub": user_id,
        "jti": jti,
        "type": "refresh",
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM), jti


def decode_token(token: str) -> dict:
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])


async def store_refresh_jti(redis, jti: str, user_id: str, ttl_days: int = REFRESH_TOKEN_EXPIRE_DAYS):
    await redis.setex(f"refresh_jti:{jti}", ttl_days * 86400, user_id)


_CONSUME_JTI_SCRIPT = """
local val = redis.call('GET', KEYS[1])
if val then
  redis.call('DEL', KEYS[1])
end
return val
"""


async def consume_refresh_jti(redis, jti: str) -> str | None:
    """Atomically check and delete a refresh token JTI. Returns user_id if valid, None if already used."""
    key = f"refresh_jti:{jti}"
    user_id = await redis.eval(_CONSUME_JTI_SCRIPT, 1, key)
    return user_id if user_id else None
