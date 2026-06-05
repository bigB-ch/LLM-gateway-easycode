from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.user import User
from dependencies import get_current_user, require_admin

router = APIRouter(prefix="/admin/api/users", tags=["users"])


class TopupRequest(BaseModel):
    amount_yuan: float
    note: str | None = None


class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    role: str
    balance: int
    status: str
    created_at: str


def _user_to_response(u: User) -> dict:
    return {
        "id": str(u.id),
        "username": u.username,
        "email": u.email,
        "role": u.role,
        "balance": u.balance,
        "balance_yuan": round(u.balance / 100, 2),
        "status": u.status,
        "created_at": u.created_at.isoformat(),
    }


@router.get("")
async def list_users(
    cursor: str | None = Query(None),
    limit: int = Query(20, le=100),
    db: AsyncSession = Depends(get_db),
    _admin: dict = Depends(require_admin),
):
    query = select(User).order_by(User.created_at.desc()).limit(limit + 1)
    if cursor:
        query = query.where(User.created_at < cursor)
    result = await db.execute(query)
    users = result.scalars().all()
    has_more = len(users) > limit
    items = users[:limit]
    return {
        "items": [_user_to_response(u) for u in items],
        "has_more": has_more,
        "next_cursor": items[-1].created_at.isoformat() if has_more else None,
    }


@router.get("/{user_id}")
async def get_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    _admin: dict = Depends(require_admin),
):
    result = await db.execute(select(User).where(User.id == user_id))
    u = result.scalar_one_or_none()
    if u is None:
        raise HTTPException(status_code=404, detail={"error": "user_not_found"})
    return _user_to_response(u)


@router.post("/{user_id}/suspend")
async def suspend_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    _admin: dict = Depends(require_admin),
):
    result = await db.execute(select(User).where(User.id == user_id))
    u = result.scalar_one_or_none()
    if u is None:
        raise HTTPException(status_code=404)
    u.status = "suspended"
    await db.commit()
    return {"message": "user_suspended"}


@router.post("/{user_id}/activate")
async def activate_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    _admin: dict = Depends(require_admin),
):
    result = await db.execute(select(User).where(User.id == user_id))
    u = result.scalar_one_or_none()
    if u is None:
        raise HTTPException(status_code=404)
    u.status = "active"
    await db.commit()
    return {"message": "user_activated"}


@router.post("/{user_id}/topup")
async def topup_user(
    user_id: str,
    req: TopupRequest,
    db: AsyncSession = Depends(get_db),
    _admin: dict = Depends(require_admin),
):
    result = await db.execute(select(User).where(User.id == user_id))
    u = result.scalar_one_or_none()
    if u is None:
        raise HTTPException(status_code=404, detail={"error": "user_not_found"})
    amount_fen = int(req.amount_yuan * 100)
    u.balance += amount_fen
    await db.commit()
    return {
        "message": "topup_success",
        "user_id": str(u.id),
        "amount_yuan": req.amount_yuan,
        "balance_yuan": round(u.balance / 100, 2),
    }


class UpdateSettingsRequest(BaseModel):
    settings: dict


@router.get("/me/settings")
async def get_my_settings(
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.id == user["user_id"]))
    u = result.scalar_one_or_none()
    if u is None:
        raise HTTPException(status_code=404)
    return {"settings": u.settings or {}}


@router.put("/me/settings")
async def update_my_settings(
    req: UpdateSettingsRequest,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.id == user["user_id"]))
    u = result.scalar_one_or_none()
    if u is None:
        raise HTTPException(status_code=404)
    u.settings = req.settings
    await db.commit()
    return {"message": "settings_updated", "settings": u.settings}
