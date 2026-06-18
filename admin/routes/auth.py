from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from services.auth_service import (
    register_user, get_user_by_email, send_verification_code,
    verify_code_and_activate, authenticate_user,
)
from jwt_utils import create_access_token, create_refresh_token, store_refresh_jti, consume_refresh_jti
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
async def register(req: RegisterRequest, request: Request, db: AsyncSession = Depends(get_db)):
    r = redis_client.redis
    client_ip = request.client.host if request.client else "unknown"
    rate_key = f"register_rate:{client_ip}"
    # 临时禁用频率限制以便测试
    # attempts = await r.get(rate_key)
    # if attempts and int(attempts) >= 5:
    #     raise HTTPException(status_code=429, detail={"error": "too_many_registrations"})
    # await r.incr(rate_key)
    # await r.expire(rate_key, 3600)

    existing = await get_user_by_email(db, req.email)
    if existing:
        raise HTTPException(status_code=409, detail={"error": "email_exists"})
    from services.auth_service import validate_password
    pw_error = validate_password(req.password)
    if pw_error:
        raise HTTPException(status_code=422, detail={"error": pw_error})
    user = await register_user(db, req.username, req.email, req.password)
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
    refresh_token, jti = create_refresh_token(str(user.id))
    await store_refresh_jti(r, jti, str(user.id))
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user={"id": str(user.id), "username": user.username, "email": user.email, "role": user.role},
    )


@router.post("/login")
async def login(req: LoginRequest, request: Request, db: AsyncSession = Depends(get_db)):
    r = redis_client.redis
    client_ip = request.client.host if request.client else "unknown"
    rate_key = f"login_rate:{client_ip}"
    attempts = await r.get(rate_key)
    if attempts and int(attempts) >= 10:
        raise HTTPException(status_code=429, detail={"error": "too_many_login_attempts"})

    from services.auth_service import authenticate_user_by_username
    if "@" in req.login:
        user = await authenticate_user(db, req.login, req.password)
    else:
        user = await authenticate_user_by_username(db, req.login, req.password)
    if user is None:
        await r.incr(rate_key)
        await r.expire(rate_key, 900)
        raise HTTPException(status_code=401, detail={"error": "invalid_credentials"})
    from datetime import datetime, timezone
    user.last_login_at = datetime.now(timezone.utc)
    await db.commit()
    access_token = create_access_token(str(user.id), user.role)
    refresh_token, jti = create_refresh_token(str(user.id))
    await store_refresh_jti(r, jti, str(user.id))
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user={"id": str(user.id), "username": user.username, "email": user.email, "role": user.role, "balance": user.balance},
    )


@router.post("/refresh")
async def refresh(refresh_token: str, request: Request, db: AsyncSession = Depends(get_db)):
    r = redis_client.redis
    client_ip = request.client.host if request.client else "unknown"
    rate_key = f"refresh_rate:{client_ip}"
    attempts = await r.get(rate_key)
    if attempts and int(attempts) >= 30:
        raise HTTPException(status_code=429, detail={"error": "too_many_refresh_attempts"})
    await r.incr(rate_key)
    await r.expire(rate_key, 900)

    try:
        from jwt_utils import decode_token
        payload = decode_token(refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401)
        user_id = await consume_refresh_jti(r, payload.get("jti", ""))
        if user_id is None:
            raise HTTPException(status_code=401)
        from models.user import User
        from sqlalchemy import select
        user_result = await db.execute(select(User).where(User.id == payload["sub"]))
        user = user_result.scalar_one_or_none()
        if user is None or user.status != "active":
            raise HTTPException(status_code=401)
        new_access = create_access_token(str(user.id), user.role)
        new_refresh, new_jti = create_refresh_token(str(user.id))
        await store_refresh_jti(r, new_jti, str(user.id))
        return {"access_token": new_access, "refresh_token": new_refresh}
    except HTTPException:
        raise
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
    return {
        "id": str(u.id),
        "username": u.username,
        "email": u.email,
        "role": u.role,
        "balance": u.balance,
        "created_at": u.created_at.isoformat(),
        "last_login_at": u.last_login_at.isoformat() if u.last_login_at else None,
    }


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    email: EmailStr
    code: str
    new_password: str


@router.post("/forgot-password")
async def forgot_password(req: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    """Send a password reset verification code to the registered email."""
    user = await get_user_by_email(db, req.email)
    if user is None:
        raise HTTPException(status_code=404, detail={"error": "email_not_found"})
    if user.status != "active":
        raise HTTPException(status_code=403, detail={"error": "account_not_active"})
    r = redis_client.redis
    ok = await send_verification_code(r, req.email)
    if not ok:
        raise HTTPException(status_code=429, detail={"error": "too_many_codes"})
    return {"message": "reset_code_sent", "email": req.email}


@router.post("/reset-password")
async def reset_password(req: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    """Reset password using email, verification code, and new password."""
    user = await get_user_by_email(db, req.email)
    if user is None:
        raise HTTPException(status_code=404, detail={"error": "email_not_found"})

    r = redis_client.redis
    code_key = f"verification_code:{req.email}"
    stored = await r.get(code_key)
    if stored is None or stored != req.code:
        raise HTTPException(status_code=400, detail={"error": "invalid_or_expired_code"})

    from services.auth_service import validate_password
    pw_error = validate_password(req.new_password)
    if pw_error:
        raise HTTPException(status_code=422, detail={"error": pw_error})

    from crypto import hash_password
    user.password_hash = hash_password(req.new_password)
    await db.commit()

    await r.delete(code_key)
    return {"message": "password_reset_success"}


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
