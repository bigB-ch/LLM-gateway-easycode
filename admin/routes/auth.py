from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from services.auth_service import (
    register_user, get_user_by_email, send_verification_code,
    verify_code_and_activate, authenticate_user,
)
from jwt_utils import create_access_token, create_refresh_token
from dependencies import get_current_user
import redis_client

router = APIRouter(prefix="/admin/api/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str


class SendCodeRequest(BaseModel):
    email: EmailStr


class VerifyCodeRequest(BaseModel):
    email: EmailStr
    code: str


class LoginRequest(BaseModel):
    login: str  # username or email
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    user: dict


@router.post("/register")
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    existing = await get_user_by_email(db, req.email)
    if existing:
        raise HTTPException(status_code=409, detail={"error": "email_exists"})
    from services.auth_service import validate_password
    pw_error = validate_password(req.password)
    if pw_error:
        raise HTTPException(status_code=422, detail={"error": pw_error})
    user = await register_user(db, req.username, req.email, req.password)
    r = redis_client.redis
    ok = await send_verification_code(r, req.email)
    if not ok:
        raise HTTPException(status_code=429, detail={"error": "too_many_codes"})
    return {"message": "verification_code_sent", "email": req.email}


@router.post("/send-code")
async def send_code(req: SendCodeRequest):
    r = redis_client.redis
    ok = await send_verification_code(r, req.email)
    if not ok:
        raise HTTPException(status_code=429, detail={"error": "too_many_codes"})
    return {"message": "verification_code_sent"}


@router.post("/verify-code")
async def verify_code(req: VerifyCodeRequest, db: AsyncSession = Depends(get_db)):
    r = redis_client.redis
    user = await verify_code_and_activate(r, db, req.email, req.code)
    if user is None:
        raise HTTPException(status_code=400, detail={"error": "invalid_code"})
    access_token = create_access_token(str(user.id), user.role)
    refresh_token = create_refresh_token(str(user.id))
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user={"id": str(user.id), "username": user.username, "email": user.email, "role": user.role},
    )


@router.post("/login")
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    from services.auth_service import authenticate_user_by_username
    if "@" in req.login:
        user = await authenticate_user(db, req.login, req.password)
    else:
        user = await authenticate_user_by_username(db, req.login, req.password)
    if user is None:
        raise HTTPException(status_code=401, detail={"error": "invalid_credentials"})
    access_token = create_access_token(str(user.id), user.role)
    refresh_token = create_refresh_token(str(user.id))
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user={"id": str(user.id), "username": user.username, "email": user.email, "role": user.role, "balance": user.balance},
    )


@router.post("/refresh")
async def refresh(refresh_token: str, db: AsyncSession = Depends(get_db)):
    try:
        from jwt_utils import decode_token
        payload = decode_token(refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401)
        from models.user import User
        from sqlalchemy import select
        user_result = await db.execute(select(User).where(User.id == payload["sub"]))
        user = user_result.scalar_one_or_none()
        if user is None or user.status != "active":
            raise HTTPException(status_code=401)
        new_access = create_access_token(str(user.id), user.role)
        new_refresh = create_refresh_token(str(user.id))
        return {"access_token": new_access, "refresh_token": new_refresh}
    except Exception:
        raise HTTPException(status_code=401, detail={"error": "invalid_token"})


@router.get("/me")
async def me(user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    from models.user import User
    from sqlalchemy import select
    result = await db.execute(select(User).where(User.id == user["user_id"]))
    u = result.scalar_one_or_none()
    if u is None:
        raise HTTPException(status_code=404)
    return {"id": str(u.id), "username": u.username, "email": u.email, "role": u.role, "balance": u.balance}


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str


@router.put("/password")
async def change_password(
    req: ChangePasswordRequest,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from models.user import User
    from sqlalchemy import select
    from crypto import verify_password, hash_password
    from services.auth_service import validate_password

    result = await db.execute(select(User).where(User.id == user["user_id"]))
    u = result.scalar_one_or_none()
    if u is None:
        raise HTTPException(status_code=404)

    if not verify_password(req.old_password, u.password_hash):
        raise HTTPException(status_code=400, detail={"error": "旧密码错误"})

    pw_error = validate_password(req.new_password)
    if pw_error:
        raise HTTPException(status_code=422, detail={"error": pw_error})

    u.password_hash = hash_password(req.new_password)
    await db.commit()
    return {"message": "密码修改成功"}
