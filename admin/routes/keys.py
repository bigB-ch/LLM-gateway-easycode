import uuid
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.api_key import ApiKey
from models.audit_log import AuditLog
from crypto import generate_api_key
from dependencies import get_current_user, require_admin
import redis_client

router = APIRouter(prefix="/admin/api/keys", tags=["keys"])


class CreateKeyRequest(BaseModel):
    name: str | None = None
    rate_limit: int = 60


class KeyResponse(BaseModel):
    id: str
    key_prefix: str
    name: str | None
    rate_limit: int
    status: str
    last_used_at: str | None
    expires_at: str | None
    created_at: str


def _key_to_response(key: ApiKey) -> dict:
    return {
        "id": str(key.id),
        "key_prefix": key.key_prefix,
        "name": key.name,
        "rate_limit": key.rate_limit,
        "status": key.status,
        "last_used_at": key.last_used_at.isoformat() if key.last_used_at else None,
        "expires_at": key.expires_at.isoformat() if key.expires_at else None,
        "created_at": key.created_at.isoformat(),
    }


@router.post("")
async def create_key(req: CreateKeyRequest, user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db), request: Request = None):
    r = redis_client.redis
    rate_key = f"key_create_rate:{user['user_id']}"
    count = await r.get(rate_key)
    if count and int(count) >= 5:
        raise HTTPException(status_code=429, detail={"error": "too_many_keys_per_hour"})
    await r.incr(rate_key)
    if not count:
        await r.expire(rate_key, 3600)

    active_count = await db.execute(
        select(func.count(ApiKey.id)).where(ApiKey.user_id == user["user_id"], ApiKey.status == "active")
    )
    if active_count.scalar() >= 5:
        raise HTTPException(status_code=400, detail={"error": "max_active_keys"})

    raw_key, prefix, hashed = generate_api_key()
    expires_at = datetime.now(timezone.utc) + timedelta(days=90)

    api_key = ApiKey(
        id=uuid.uuid4(),
        user_id=user["user_id"],
        key_hash=hashed,
        key_prefix=prefix,
        name=req.name,
        rate_limit=req.rate_limit,
        expires_at=expires_at,
    )
    db.add(api_key)

    await r.hset(f"apikey:{hashed}", mapping={
        "user_id": user["user_id"],
        "rate_limit": str(req.rate_limit),
        "status": "active",
    })

    audit = AuditLog(
        user_id=user["user_id"],
        action="key.create",
        resource=prefix,
        detail={"key_id": str(api_key.id)},
        ip=request.client.host if request else None,
    )
    db.add(audit)
    await db.commit()

    return {"api_key": raw_key, "key_prefix": prefix, "message": "store_key_now"}


@router.get("")
async def list_keys(user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ApiKey).where(ApiKey.user_id == user["user_id"]).order_by(ApiKey.created_at.desc())
    )
    keys = result.scalars().all()
    return {"items": [_key_to_response(k) for k in keys]}


@router.post("/{key_id}/revoke")
async def revoke_key(key_id: str, user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ApiKey).where(ApiKey.id == key_id, ApiKey.user_id == user["user_id"]))
    key = result.scalar_one_or_none()
    if key is None:
        raise HTTPException(status_code=404, detail={"error": "key_not_found"})

    key.status = "revoked"
    r = redis_client.redis
    await r.delete(f"apikey:{key.key_hash}")
    await db.commit()
    return {"message": "key_revoked"}
