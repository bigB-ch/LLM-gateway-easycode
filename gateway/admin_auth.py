from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt

from config import JWT_SECRET, JWT_ALGORITHM

security = HTTPBearer(auto_error=False)


def decode_token(token: str) -> dict:
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
):
    if credentials is None:
        raise HTTPException(status_code=401, detail={"error": "unauthorized"})
    try:
        payload = decode_token(credentials.credentials)
        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail={"error": "unauthorized"})
        return {"user_id": payload["sub"], "role": payload["role"]}
    except Exception:
        raise HTTPException(status_code=401, detail={"error": "unauthorized"})


async def require_admin(user: dict = Depends(get_current_user)):
    if user["role"] not in ("admin", "super_admin"):
        raise HTTPException(status_code=403, detail={"error": "forbidden"})
    return user
