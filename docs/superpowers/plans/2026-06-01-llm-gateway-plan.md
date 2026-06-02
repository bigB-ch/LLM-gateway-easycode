# LLM Gateway 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建大模型 API 网关中转平台 — Gateway (认证/限流/转发) + Admin (用户/计费/报表) + 管理后台前端

**Architecture:** Gateway (FastAPI, :8000) 负责热路径，Admin (FastAPI, :8001) 负责温路径，两者共享 PostgreSQL + Redis。单机 Docker Compose 起步，Nginx 统一 443 入口。

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy 2.0 (async), Redis, PostgreSQL 16, Nginx, Docker Compose, Vue 3 + Vite

---

## Phase 1: 基础设施与项目脚手架

### Task 1: 创建项目目录结构和 Docker Compose

**Files:**
- Create: `llm-gateway/docker-compose.yml`
- Create: `llm-gateway/.env.example`
- Create: `llm-gateway/.gitignore`
- Create: `llm-gateway/gateway/Dockerfile`
- Create: `llm-gateway/gateway/requirements.txt`
- Create: `llm-gateway/admin/Dockerfile`
- Create: `llm-gateway/admin/requirements.txt`
- Create: `llm-gateway/frontend/Dockerfile`

- [ ] **Step 1: 创建 .gitignore**

```
__pycache__/
*.pyc
.env
*.pem
secrets/
.venv/
node_modules/
dist/
*.egg-info/
.pytest_cache/
```

- [ ] **Step 2: 创建 .env.example**

```bash
# Domain
DOMAIN=localhost

# PostgreSQL
POSTGRES_DB=llm_gateway
POSTGRES_USER=gateway
POSTGRES_PASSWORD=change-me-in-production

# Redis (single instance for dev)
REDIS_URL=redis://redis:6379

# JWT
JWT_SECRET=change-me-use-openssl-rand-hex-64

# Email (SMTP for verification codes)
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=noreply@example.com
SMTP_PASSWORD=change-me
SMTP_FROM=noreply@example.com

# Admin initial user
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=admin123

# Grafana (optional)
GRAFANA_PASSWORD=admin
```

- [ ] **Step 3: 创建 gateway/requirements.txt**

```
fastapi==0.115.6
uvicorn[standard]==0.34.0
httpx==0.28.1
redis==5.2.1
prometheus-fastapi-instrumentator==7.0.1
python-dotenv==1.0.1
```

- [ ] **Step 4: 创建 gateway/Dockerfile**

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

- [ ] **Step 5: 创建 admin/requirements.txt**

```
fastapi==0.115.6
uvicorn[standard]==0.34.0
sqlalchemy[asyncio]==2.0.36
asyncpg==0.30.0
alembic==1.14.0
redis==5.2.1
bcrypt==4.2.1
pyjwt==2.10.1
python-dotenv==1.0.1
aiosmtplib==3.0.2
cryptography==44.0.0
prometheus-fastapi-instrumentator==7.0.1
```

- [ ] **Step 6: 创建 admin/Dockerfile**

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
```

- [ ] **Step 7: 创建 frontend/Dockerfile**

```dockerfile
FROM node:22-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx-frontend.conf /etc/nginx/conf.d/default.conf
```

- [ ] **Step 8: 创建 docker-compose.yml**

```yaml
services:
  nginx:
    image: nginx:alpine
    ports:
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
    depends_on:
      - gateway
      - admin
      - frontend
    restart: always
    networks:
      - internal

  gateway:
    build: ./gateway
    expose:
      - "8000"
    env_file: .env
    depends_on:
      redis:
        condition: service_healthy
    restart: always
    networks:
      - internal

  admin:
    build: ./admin
    expose:
      - "8001"
    env_file: .env
    environment:
      - DATABASE_URL=postgresql+asyncpg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: always
    networks:
      - internal

  frontend:
    build: ./frontend
    expose:
      - "80"
    restart: always
    networks:
      - internal

  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - pg_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
      interval: 5s
      timeout: 5s
      retries: 5
    restart: always
    networks:
      - internal

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 5s
      retries: 5
    restart: always
    networks:
      - internal

volumes:
  pg_data:
  redis_data:

networks:
  internal:
    driver: bridge
```

- [ ] **Step 9: 验证目录结构**

Run: `ls -la D:/code/llm-gateway/ && ls -la D:/code/llm-gateway/gateway/ && ls -la D:/code/llm-gateway/admin/`
Expected: 所有文件就位

---

## Phase 2: Admin 服务 — 数据库与模型

### Task 2: Admin 入口和配置

**Files:**
- Create: `llm-gateway/admin/main.py`
- Create: `llm-gateway/admin/config.py`
- Create: `llm-gateway/admin/database.py`

- [ ] **Step 1: 创建 config.py**

```python
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://gateway:gateway@postgres:5432/llm_gateway",
)
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")
JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7

SMTP_HOST = os.getenv("SMTP_HOST", "localhost")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM = os.getenv("SMTP_FROM", "noreply@example.com")
```

- [ ] **Step 2: 创建 database.py**

```python
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

from config import DATABASE_URL

engine = create_async_engine(DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
```

- [ ] **Step 3: 创建 main.py**

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(title="LLM Gateway Admin", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/admin/api/health")
async def health():
    return {"status": "ok"}
```

---

### Task 3: SQLAlchemy 模型

**Files:**
- Create: `llm-gateway/admin/models/__init__.py`
- Create: `llm-gateway/admin/models/user.py`
- Create: `llm-gateway/admin/models/api_key.py`
- Create: `llm-gateway/admin/models/plan.py`
- Create: `llm-gateway/admin/models/usage_log.py`
- Create: `llm-gateway/admin/models/recharge_record.py`
- Create: `llm-gateway/admin/models/audit_log.py`
- Create: `llm-gateway/admin/models/system_config.py`

- [ ] **Step 1: 创建 models/__init__.py**

```python
from database import Base
from models.user import User
from models.api_key import ApiKey
from models.plan import Plan, UserPlan
from models.usage_log import UsageLog
from models.recharge_record import RechargeRecord
from models.audit_log import AuditLog
from models.system_config import SystemConfig

__all__ = [
    "Base", "User", "ApiKey", "Plan", "UserPlan",
    "UsageLog", "RechargeRecord", "AuditLog", "SystemConfig",
]
```

- [ ] **Step 2: 创建 models/user.py**

```python
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, BigInteger, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from database import Base


def utcnow():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(16), default="customer", nullable=False)
    balance: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(16), default="active", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    api_keys = relationship("ApiKey", back_populates="user")
```

- [ ] **Step 3: 创建 models/api_key.py**

```python
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from database import Base


def utcnow():
    return datetime.now(timezone.utc)


class ApiKey(Base):
    __tablename__ = "api_keys"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    key_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    key_prefix: Mapped[str] = mapped_column(String(8), nullable=False)
    name: Mapped[str | None] = mapped_column(String(128))
    rate_limit: Mapped[int] = mapped_column(Integer, default=60, nullable=False)
    model_allowlist: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(16), default="active", nullable=False)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    user = relationship("User", back_populates="api_keys")
```

- [ ] **Step 4: 创建 models/plan.py**

```python
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, BigInteger, Integer, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from database import Base


def utcnow():
    return datetime.now(timezone.utc)


class Plan(Base):
    __tablename__ = "plans"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    token_quota: Mapped[int] = mapped_column(BigInteger, nullable=False)
    price: Mapped[int] = mapped_column(BigInteger, nullable=False)
    duration_days: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    status: Mapped[str] = mapped_column(String(16), default="active", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


class UserPlan(Base):
    __tablename__ = "user_plans"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    plan_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("plans.id"), nullable=False)
    token_remaining: Mapped[int] = mapped_column(BigInteger, nullable=False)
    purchased_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
```

- [ ] **Step 5: 创建 models/usage_log.py**

```python
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, BigInteger, Integer, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from database import Base


def utcnow():
    return datetime.now(timezone.utc)


class UsageLog(Base):
    __tablename__ = "usage_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    request_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    api_key_prefix: Mapped[str] = mapped_column(String(8), nullable=False)
    model: Mapped[str] = mapped_column(String(64), nullable=False)
    provider: Mapped[str] = mapped_column(String(32), nullable=False)
    prompt_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    completion_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    cost: Mapped[int] = mapped_column(BigInteger, nullable=False)
    bill_cost: Mapped[int] = mapped_column(BigInteger, nullable=False)
    latency_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    error_msg: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
```

- [ ] **Step 6: 创建 models/recharge_record.py**

```python
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, BigInteger, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from database import Base


def utcnow():
    return datetime.now(timezone.utc)


class RechargeRecord(Base):
    __tablename__ = "recharge_records"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    amount: Mapped[int] = mapped_column(BigInteger, nullable=False)
    method: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(16), default="pending", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
```

- [ ] **Step 7: 创建 models/audit_log.py**

```python
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, INET, JSONB
from database import Base


def utcnow():
    return datetime.now(timezone.utc)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    resource: Mapped[str | None] = mapped_column(String(128))
    detail: Mapped[dict | None] = mapped_column(JSONB)
    ip: Mapped[str | None] = mapped_column(INET)
    user_agent: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
```

- [ ] **Step 8: 创建 models/system_config.py**

```python
from datetime import datetime, timezone
from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB
from database import Base


def utcnow():
    return datetime.now(timezone.utc)


class SystemConfig(Base):
    __tablename__ = "system_config"

    key: Mapped[str] = mapped_column(String(128), primary_key=True)
    value: Mapped[dict] = mapped_column(JSONB, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)
```

- [ ] **Step 9: 验证模型可导入**

Run: `cd D:/code/llm-gateway/admin && python -c "from models import User, ApiKey, Plan, UserPlan, UsageLog, RechargeRecord, AuditLog, SystemConfig; print('All models OK')"`
Expected: `All models OK`

- [ ] **Step 10: Commit**

```bash
git add admin/models/ admin/main.py admin/config.py admin/database.py
git commit -m "feat: add admin service models and db setup"
```

---

### Task 4: Redis 工具和加密工具

**Files:**
- Create: `llm-gateway/admin/redis_client.py`
- Create: `llm-gateway/admin/crypto.py`

- [ ] **Step 1: 创建 redis_client.py**

```python
import redis.asyncio as aioredis
from config import REDIS_URL

redis = aioredis.from_url(REDIS_URL, decode_responses=True)


async def get_redis():
    return redis
```

- [ ] **Step 2: 创建 crypto.py**

```python
import hashlib
import secrets
import bcrypt


def hash_api_key(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()


def generate_api_key() -> tuple[str, str, str]:
    raw = "sk-" + secrets.token_hex(32)
    prefix = raw[:10]
    hashed = hash_api_key(raw)
    return raw, prefix, hashed


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode(), password_hash.encode())


def generate_verification_code() -> str:
    return str(secrets.randbelow(900000) + 100000)
```

- [ ] **Step 3: Commit**

```bash
git add admin/redis_client.py admin/crypto.py
git commit -m "feat: add redis client and crypto utilities"
```

---

## Phase 3: Admin 服务 — 认证

### Task 5: JWT 工具

**Files:**
- Create: `llm-gateway/admin/jwt_utils.py`

- [ ] **Step 1: 创建 jwt_utils.py**

```python
from datetime import datetime, timedelta, timezone
import jwt
from config import JWT_SECRET, JWT_ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_DAYS


def create_access_token(user_id: str, role: str) -> str:
    payload = {
        "sub": user_id,
        "role": role,
        "type": "access",
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def create_refresh_token(user_id: str) -> str:
    payload = {
        "sub": user_id,
        "type": "refresh",
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
```

- [ ] **Step 2: Commit**

```bash
git add admin/jwt_utils.py
git commit -m "feat: add JWT utility functions"
```

---

### Task 6: 注册和邮箱验证

**Files:**
- Create: `llm-gateway/admin/services/__init__.py`
- Create: `llm-gateway/admin/services/auth_service.py`
- Create: `llm-gateway/admin/services/email_service.py`
- Create: `llm-gateway/admin/routes/__init__.py`
- Create: `llm-gateway/admin/routes/auth.py`
- Create: `llm-gateway/admin/dependencies.py`

- [ ] **Step 1: 创建 services/email_service.py**

```python
import aiosmtplib
from email.mime.text import MIMEText
from config import SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, SMTP_FROM


async def send_verification_email(to_email: str, code: str):
    body = f"您的验证码是：{code}，5分钟内有效。请勿将验证码透露给他人。"
    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = "LLM Gateway 邮箱验证码"
    msg["From"] = SMTP_FROM
    msg["To"] = to_email

    await aiosmtplib.send(
        msg,
        hostname=SMTP_HOST,
        port=SMTP_PORT,
        username=SMTP_USER,
        password=SMTP_PASSWORD,
        use_tls=True,
    )
```

- [ ] **Step 2: 创建 services/auth_service.py**

```python
import uuid
from datetime import datetime, timedelta, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User
from crypto import hash_password, verify_password, generate_verification_code
import redis_client


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
```

- [ ] **Step 3: 创建 dependencies.py**

```python
from fastapi import Depends, HTTPException, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from jwt_utils import decode_token

security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: AsyncSession = Depends(get_db),
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
```

- [ ] **Step 4: 创建 routes/auth.py**

```python
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
    email: EmailStr
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
    user = await authenticate_user(db, req.email, req.password)
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
```

- [ ] **Step 5: 更新 admin/main.py 注册路由**

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import init_db
from routes.auth import router as auth_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(title="LLM Gateway Admin", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)


@app.get("/admin/api/health")
async def health():
    return {"status": "ok"}
```

- [ ] **Step 6: Commit**

```bash
git add admin/services/ admin/routes/ admin/dependencies.py admin/main.py
git commit -m "feat: add auth routes — register, verify, login, refresh"
```

---

## Phase 4: Admin 服务 — 业务功能

### Task 7: API Key 管理

**Files:**
- Create: `llm-gateway/admin/routes/keys.py`

- [ ] **Step 1: 创建 routes/keys.py**

```python
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
    # 每小时最多5次
    r = redis_client.redis
    rate_key = f"key_create_rate:{user['user_id']}"
    count = await r.get(rate_key)
    if count and int(count) >= 5:
        raise HTTPException(status_code=429, detail={"error": "too_many_keys_per_hour"})
    await r.incr(rate_key)
    if not count:
        await r.expire(rate_key, 3600)

    # 每用户最多5个活跃Key
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

    # 同步到Redis
    await r.hset(f"apikey:{hashed}", mapping={
        "user_id": user["user_id"],
        "rate_limit": str(req.rate_limit),
        "status": "active",
    })

    # 审计日志
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
```

- [ ] **Step 2: 更新 admin/main.py，注册 keys 路由**

在 `app.include_router(auth_router)` 后加入：
```python
from routes.keys import router as keys_router
app.include_router(keys_router)
```

- [ ] **Step 3: Commit**

```bash
git add admin/routes/keys.py admin/main.py
git commit -m "feat: add API key management routes"
```

---

### Task 8: 用户管理（管理员功能）

**Files:**
- Create: `llm-gateway/admin/routes/users.py`

- [ ] **Step 1: 创建 routes/users.py**

```python
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.user import User
from dependencies import get_current_user, require_admin

router = APIRouter(prefix="/admin/api/users", tags=["users"])


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
```

- [ ] **Step 2: 更新 admin/main.py，注册 users 路由**

```python
from routes.users import router as users_router
app.include_router(users_router)
```

- [ ] **Step 3: Commit**

```bash
git add admin/routes/users.py admin/main.py
git commit -m "feat: add user management routes (admin)"
```

---

### Task 9: 用量报表与 Dashboard

**Files:**
- Create: `llm-gateway/admin/routes/reports.py`

- [ ] **Step 1: 创建 routes/reports.py**

```python
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.usage_log import UsageLog
from models.user import User
from dependencies import get_current_user, require_admin

router = APIRouter(prefix="/admin/api/reports", tags=["reports"])


@router.get("/dashboard")
async def dashboard(user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """客户首页数据：今日调用、今日消费、余额"""
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    # 今日调用量
    call_result = await db.execute(
        select(func.count(UsageLog.id)).where(
            UsageLog.user_id == user["user_id"],
            UsageLog.created_at >= today_start,
        )
    )
    today_calls = call_result.scalar() or 0

    # 今日消费
    cost_result = await db.execute(
        select(func.coalesce(func.sum(UsageLog.bill_cost), 0)).where(
            UsageLog.user_id == user["user_id"],
            UsageLog.created_at >= today_start,
            UsageLog.status == "success",
        )
    )
    today_cost = cost_result.scalar() or 0

    # 用户余额
    user_result = await db.execute(select(User).where(User.id == user["user_id"]))
    u = user_result.scalar_one()
    balance = u.balance

    return {
        "today_calls": today_calls,
        "today_cost_yuan": round(today_cost / 100, 2),
        "balance_yuan": round(balance / 100, 2),
    }


@router.get("/trend")
async def trend(
    days: int = Query(7, le=30),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """最近N天消费趋势"""
    now = datetime.now(timezone.utc)
    start = now - timedelta(days=days)

    result = await db.execute(
        select(
            func.date(UsageLog.created_at).label("day"),
            func.coalesce(func.sum(UsageLog.bill_cost), 0).label("total"),
        )
        .where(UsageLog.user_id == user["user_id"], UsageLog.created_at >= start, UsageLog.status == "success")
        .group_by(text("day"))
        .order_by(text("day"))
    )
    rows = result.all()
    return {
        "trend": [
            {"date": str(row.day), "cost_yuan": round(row.total / 100, 2)}
            for row in rows
        ]
    }


@router.get("/usage")
async def usage_details(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, le=100),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """用量明细列表"""
    offset = (page - 1) * page_size
    result = await db.execute(
        select(UsageLog)
        .where(UsageLog.user_id == user["user_id"])
        .order_by(UsageLog.created_at.desc())
        .limit(page_size)
        .offset(offset)
    )
    logs = result.scalars().all()
    return {
        "items": [
            {
                "id": str(log.id),
                "request_id": log.request_id,
                "model": log.model,
                "provider": log.provider,
                "prompt_tokens": log.prompt_tokens,
                "completion_tokens": log.completion_tokens,
                "cost_yuan": round(log.bill_cost / 100, 4),
                "latency_ms": log.latency_ms,
                "status": log.status,
                "created_at": log.created_at.isoformat(),
            }
            for log in logs
        ]
    }
```

- [ ] **Step 2: 更新 admin/main.py，注册 reports 路由**

```python
from routes.reports import router as reports_router
app.include_router(reports_router)
```

- [ ] **Step 3: Commit**

```bash
git add admin/routes/reports.py admin/main.py
git commit -m "feat: add dashboard and usage report routes"
```

---

### Task 10: 套餐管理

**Files:**
- Create: `llm-gateway/admin/routes/plans.py`

- [ ] **Step 1: 创建 routes/plans.py**

```python
import uuid
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.plan import Plan, UserPlan
from models.user import User
from dependencies import get_current_user, require_admin

router = APIRouter(prefix="/admin/api/plans", tags=["plans"])


class PlanCreate(BaseModel):
    name: str
    description: str | None = None
    token_quota: int
    price: int
    duration_days: int = 30


def _plan_to_response(p: Plan) -> dict:
    return {
        "id": str(p.id),
        "name": p.name,
        "description": p.description,
        "token_quota": p.token_quota,
        "price": p.price,
        "price_yuan": round(p.price / 100, 2),
        "duration_days": p.duration_days,
        "status": p.status,
    }


@router.get("")
async def list_plans(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Plan).where(Plan.status == "active").order_by(Plan.price))
    plans = result.scalars().all()
    return {"items": [_plan_to_response(p) for p in plans]}


@router.post("")
async def create_plan(
    req: PlanCreate,
    db: AsyncSession = Depends(get_db),
    _admin: dict = Depends(require_admin),
):
    plan = Plan(
        id=uuid.uuid4(),
        name=req.name,
        description=req.description,
        token_quota=req.token_quota,
        price=req.price,
        duration_days=req.duration_days,
    )
    db.add(plan)
    await db.commit()
    return _plan_to_response(plan)


@router.post("/{plan_id}/purchase")
async def purchase_plan(
    plan_id: str,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    plan_result = await db.execute(select(Plan).where(Plan.id == plan_id, Plan.status == "active"))
    plan = plan_result.scalar_one_or_none()
    if plan is None:
        raise HTTPException(status_code=404, detail={"error": "plan_not_found"})

    user_result = await db.execute(select(User).where(User.id == user["user_id"]))
    u = user_result.scalar_one()

    if u.balance < plan.price:
        raise HTTPException(status_code=400, detail={"error": "insufficient_balance"})

    u.balance -= plan.price

    from datetime import datetime, timedelta, timezone
    up = UserPlan(
        id=uuid.uuid4(),
        user_id=u.id,
        plan_id=plan.id,
        token_remaining=plan.token_quota,
        expires_at=datetime.now(timezone.utc) + timedelta(days=plan.duration_days),
    )
    db.add(up)
    await db.commit()
    return {"message": "purchased", "balance_yuan": round(u.balance / 100, 2)}
```

- [ ] **Step 2: 更新 admin/main.py，注册 plans 路由**

```python
from routes.plans import router as plans_router
app.include_router(plans_router)
```

- [ ] **Step 3: Commit**

```bash
git add admin/routes/plans.py admin/main.py
git commit -m "feat: add plan management and purchase routes"
```

---

### Task 11: Stream 消费者（用量日志批量写入）

**Files:**
- Create: `llm-gateway/admin/consumer.py`
- Modify: `llm-gateway/admin/main.py`

- [ ] **Step 1: 创建 consumer.py**

```python
import asyncio
import json
import os
import logging
from sqlalchemy import text
from database import engine
import redis_client

logger = logging.getLogger("consumer")
STREAM_KEY = "usage_log_stream"
GROUP_NAME = "usage_consumers"
DLQ_KEY = "usage_log_dlq"
MAX_RETRIES = 3


async def ensure_group():
    r = redis_client.redis
    try:
        await r.xgroup_create(STREAM_KEY, GROUP_NAME, id="0", mkstream=True)
    except Exception:
        pass  # group already exists


async def batch_insert(messages: list[tuple[str, dict]]) -> list[str]:
    """批量插入PG，返回成功的message_id列表"""
    if not messages:
        return []

    values_clauses = []
    params = {}
    msg_ids = []
    for i, (msg_id, data) in enumerate(messages):
        msg_ids.append(msg_id)
        idx = i
        values_clauses.append(
            f"(:rid_{idx}, :uid_{idx}, :prefix_{idx}, :model_{idx}, :provider_{idx}, "
            f":pt_{idx}, :ct_{idx}, :cost_{idx}, :bcost_{idx}, :lat_{idx}, :status_{idx}, :err_{idx}) "
            f"ON CONFLICT (request_id) DO NOTHING"
        )
        params.update({
            f"rid_{idx}": data.get("request_id", ""),
            f"uid_{idx}": data.get("user_id", ""),
            f"prefix_{idx}": data.get("api_key_prefix", ""),
            f"model_{idx}": data.get("model", ""),
            f"provider_{idx}": data.get("provider", ""),
            f"pt_{idx}": int(data.get("prompt_tokens", 0)),
            f"ct_{idx}": int(data.get("completion_tokens", 0)),
            f"cost_{idx}": int(data.get("cost", 0)),
            f"bcost_{idx}": int(data.get("bill_cost", 0)),
            f"lat_{idx}": int(data.get("latency_ms", 0)),
            f"status_{idx}": data.get("status", "error"),
            f"err_{idx}": data.get("error_msg", ""),
        })

    sql = (
        "INSERT INTO usage_logs "
        "(request_id, user_id, api_key_prefix, model, provider, prompt_tokens, completion_tokens, cost, bill_cost, latency_ms, status, error_msg) "
        "VALUES " + ", ".join(values_clauses)
    )

    async with engine.begin() as conn:
        await conn.execute(text(sql), params)

    return msg_ids


async def run_consumer():
    await ensure_group()
    r = redis_client.redis
    consumer_name = f"admin-{os.getpid()}"

    while True:
        try:
            messages = await r.xreadgroup(
                GROUP_NAME, consumer_name, {STREAM_KEY: ">"},
                count=100, block=5000,
            )
            if messages:
                for stream_name, entries in messages:
                    parsed = [(eid, json.loads(data)) for eid, data in entries]
                    acked = await batch_insert(parsed)
                    for eid in acked:
                        await r.xack(STREAM_KEY, GROUP_NAME, eid)

                    # 未ACK的 -> 重试
                    for eid, data in parsed:
                        if eid not in acked:
                            retries = await r.hget(f"dlq_retry:{eid}", "count")
                            retries = int(retries or 0) + 1
                            if retries > MAX_RETRIES:
                                await r.xadd(DLQ_KEY, {**data, "retries": str(retries)})
                                await r.xack(STREAM_KEY, GROUP_NAME, eid)
                                await r.delete(f"dlq_retry:{eid}")
                            else:
                                await r.hset(f"dlq_retry:{eid}", "count", str(retries))

            # 处理pending消息
            pending_info = await r.xpending(STREAM_KEY, GROUP_NAME)
            if pending_info and pending_info.get("pending", 0) > 100:
                pending_msgs = await r.xpending_range(
                    STREAM_KEY, GROUP_NAME, min="-", max="+", count=50,
                )
                for entry in pending_msgs:
                    msg = await r.xrange(STREAM_KEY, entry["message_id"], entry["message_id"])
                    if msg:
                        eid, data = msg[0]
                        parsed = json.loads(data)
                        acked = await batch_insert([(eid, parsed)])
                        for eid2 in acked:
                            await r.xack(STREAM_KEY, GROUP_NAME, eid2)

        except Exception as e:
            logger.error(f"Consumer error: {e}")
            await asyncio.sleep(1)
```

- [ ] **Step 2: 更新 admin/main.py 启动 consumer**

在 `lifespan` 函数中加入 consumer 启动：

```python
import asyncio

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    consumer_task = asyncio.create_task(run_consumer())
    yield
    consumer_task.cancel()
```

同时导入:
```python
from consumer import run_consumer
```

- [ ] **Step 3: Commit**

```bash
git add admin/consumer.py admin/main.py
git commit -m "feat: add Redis Stream consumer for batch usage log writing"
```

---

## Phase 5: Gateway 服务

### Task 12: Gateway 入口和配置

**Files:**
- Create: `llm-gateway/gateway/main.py`
- Create: `llm-gateway/gateway/config.py`
- Create: `llm-gateway/gateway/redis_client.py`

- [ ] **Step 1: 创建 gateway/config.py**

```python
import os
from dotenv import load_dotenv

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")

CIRCUIT_BREAKER_CONFIG = {
    "openai":       {"failure_threshold": 5, "timeout_seconds": 30, "half_open_ttl": 30},
    "anthropic":    {"failure_threshold": 5, "timeout_seconds": 30, "half_open_ttl": 30},
    "google":       {"failure_threshold": 5, "timeout_seconds": 30, "half_open_ttl": 30},
    "deepseek":     {"failure_threshold": 3, "timeout_seconds": 30, "half_open_ttl": 60},
    "qwen":         {"failure_threshold": 3, "timeout_seconds": 30, "half_open_ttl": 60},
}

UPSTREAM_TIMEOUT = 30
MAX_RETRIES = 2
RETRY_BACKOFF_BASE = 1.0
```

- [ ] **Step 2: 创建 gateway/redis_client.py**

```python
import redis.asyncio as aioredis
from config import REDIS_URL

redis = aioredis.from_url(REDIS_URL, decode_responses=True)
```

- [ ] **Step 3: 创建 gateway/main.py**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI(title="LLM Gateway")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

Instrumentator().instrument(app).expose(app)


@app.get("/health")
async def health():
    return {"status": "ok"}
```

- [ ] **Step 4: Commit**

```bash
git add gateway/
git commit -m "feat: add gateway service scaffold"
```

---

### Task 13: Gateway 认证中间件

**Files:**
- Create: `llm-gateway/gateway/middleware/__init__.py`
- Create: `llm-gateway/gateway/middleware/auth.py`

- [ ] **Step 1: 创建 middleware/auth.py**

```python
import hashlib
import asyncio
import time
from fastapi import Request, HTTPException
from redis_client import redis


def hash_key(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


async def verify_api_key(request: Request) -> dict:
    """验证API Key，返回 {user_id, rate_limit}。统一错误消息防枚举。"""
    t_start = time.monotonic()

    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        elapsed = time.monotonic() - t_start
        if elapsed < 0.015:
            await asyncio.sleep(0.015 - elapsed)
        raise HTTPException(status_code=401, detail={"error": "invalid_api_key"})

    raw_key = auth[7:]
    key_hash = hash_key(raw_key)

    try:
        data = await redis.hgetall(f"apikey:{key_hash}")
    except Exception:
        raise HTTPException(status_code=503, detail={"error": "service_unavailable"})

    elapsed = time.monotonic() - t_start
    if elapsed < 0.015:
        await asyncio.sleep(0.015 - elapsed)

    if not data or data.get("status") != "active":
        raise HTTPException(status_code=401, detail={"error": "invalid_api_key"})

    return {
        "user_id": data["user_id"],
        "rate_limit": int(data.get("rate_limit", 60)),
    }
```

- [ ] **Step 2: Commit**

```bash
git add gateway/middleware/
git commit -m "feat: add gateway API key auth middleware"
```

---

### Task 14: 滑动窗口限流

**Files:**
- Create: `llm-gateway/gateway/middleware/ratelimit.py`

- [ ] **Step 1: 创建 middleware/ratelimit.py**

```python
import time
from fastapi import HTTPException
from redis_client import redis

SLIDING_WINDOW_LUA = """
local key = KEYS[1]
local window = tonumber(ARGV[1])
local limit = tonumber(ARGV[2])
local now = tonumber(ARGV[3])

redis.call('ZREMRANGEBYSCORE', key, 0, now - window)
local current = redis.call('ZCARD', key)
if current >= limit then
    return 0
end
redis.call('ZADD', key, now, now .. ':' .. string.format('%.0f', now * 1e6 % 1e6))
redis.call('EXPIRE', key, window)
return 1
"""


async def check_rate_limit(user_id: str, rate_limit: int, window: int = 60) -> None:
    key = f"ratelimit:{user_id}"
    now = time.time()
    result = await redis.eval(SLIDING_WINDOW_LUA, 1, key, str(window), str(rate_limit), str(now))
    if result == 0:
        raise HTTPException(
            status_code=429,
            detail={"error": "rate_limit_exceeded", "retry_after": window},
            headers={"Retry-After": str(window)},
        )
```

- [ ] **Step 2: Commit**

```bash
git add gateway/middleware/ratelimit.py
git commit -m "feat: add sliding window rate limiter (Redis Lua)"
```

---

### Task 15: 供应商适配器框架 + OpenAI 适配器

**Files:**
- Create: `llm-gateway/gateway/adapters/__init__.py`
- Create: `llm-gateway/gateway/adapters/base.py`
- Create: `llm-gateway/gateway/adapters/openai.py`
- Create: `llm-gateway/gateway/schemas.py`

- [ ] **Step 1: 创建 schemas.py**

```python
from pydantic import BaseModel
from typing import Any


class UnifiedMessage(BaseModel):
    role: str
    content: str


class UnifiedRequest(BaseModel):
    model: str
    messages: list[UnifiedMessage]
    temperature: float | None = None
    max_tokens: int | None = None
    stream: bool = False
    top_p: float | None = None


class UnifiedChoice(BaseModel):
    index: int
    message: UnifiedMessage | None = None
    delta: dict | None = None
    finish_reason: str | None = None


class UnifiedUsage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class UnifiedResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    model: str
    choices: list[UnifiedChoice]
    usage: UnifiedUsage | None = None
    provider: str = ""
```

- [ ] **Step 2: 创建 adapters/base.py**

```python
from abc import ABC, abstractmethod
import httpx
from schemas import UnifiedRequest, UnifiedResponse


class BaseAdapter(ABC):
    model_patterns: list[str] = []
    provider_name: str = ""

    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url
        self._client: httpx.AsyncClient | None = None

    async def get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client

    @abstractmethod
    async def chat_completion(self, request: UnifiedRequest) -> UnifiedResponse:
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        ...

    def matches(self, model: str) -> bool:
        return any(model.startswith(p) for p in self.model_patterns)
```

- [ ] **Step 3: 创建 adapters/openai.py**

```python
import httpx
from adapters.base import BaseAdapter
from schemas import UnifiedRequest, UnifiedResponse, UnifiedChoice, UnifiedMessage, UnifiedUsage


class OpenAIAdapter(BaseAdapter):
    model_patterns = ["gpt-", "o1-", "o3-"]
    provider_name = "openai"

    async def chat_completion(self, request: UnifiedRequest) -> UnifiedResponse:
        client = await self.get_client()
        body = {
            "model": request.model,
            "messages": [{"role": m.role, "content": m.content} for m in request.messages],
            "stream": False,
        }
        if request.temperature is not None:
            body["temperature"] = request.temperature
        if request.max_tokens is not None:
            body["max_tokens"] = request.max_tokens

        resp = await client.post(
            f"{self.base_url}/chat/completions",
            json=body,
            headers={"Authorization": f"Bearer {self.api_key}"},
        )
        resp.raise_for_status()
        data = resp.json()

        return UnifiedResponse(
            id=data["id"],
            model=data["model"],
            choices=[
                UnifiedChoice(
                    index=c["index"],
                    message=UnifiedMessage(
                        role=c["message"]["role"],
                        content=c["message"]["content"],
                    ),
                    finish_reason=c.get("finish_reason"),
                )
                for c in data["choices"]
            ],
            usage=UnifiedUsage(
                prompt_tokens=data["usage"]["prompt_tokens"],
                completion_tokens=data["usage"]["completion_tokens"],
                total_tokens=data["usage"]["total_tokens"],
            ),
            provider="openai",
        )

    async def health_check(self) -> bool:
        try:
            client = await self.get_client()
            resp = await client.get(
                f"{self.base_url}/models",
                headers={"Authorization": f"Bearer {self.api_key}"},
            )
            return resp.status_code == 200
        except Exception:
            return False
```

- [ ] **Step 4: 创建 adapters/__init__.py**

```python
from adapters.base import BaseAdapter
from adapters.openai import OpenAIAdapter

ADAPTER_CLASSES = [OpenAIAdapter]


def create_adapters(supplier_configs: dict[str, dict]) -> list[BaseAdapter]:
    adapters = []
    for name, config in supplier_configs.items():
        for cls in ADAPTER_CLASSES:
            if cls.provider_name == name:
                adapters.append(cls(
                    api_key=config["api_key"],
                    base_url=config["base_url"],
                ))
    return adapters


def find_adapter(model: str, adapters: list[BaseAdapter]) -> BaseAdapter | None:
    for adapter in adapters:
        if adapter.matches(model):
            return adapter
    return None
```

- [ ] **Step 5: Commit**

```bash
git add gateway/adapters/ gateway/schemas.py
git commit -m "feat: add adapter framework and OpenAI adapter"
```

---

### Task 16: 熔断器

**Files:**
- Create: `llm-gateway/gateway/circuit_breaker.py`

- [ ] **Step 1: 创建 circuit_breaker.py**

```python
import time
from enum import Enum
from redis_client import redis


class CBState(str, Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


async def get_cb_state(provider: str) -> dict:
    key = f"cb:{provider}"
    data = await redis.hgetall(key)
    if not data:
        return {"status": CBState.CLOSED, "failure_count": 0, "last_failure_time": 0}
    return {
        "status": CBState(data.get("status", "closed")),
        "failure_count": int(data.get("failure_count", 0)),
        "last_failure_time": float(data.get("last_failure_time", 0)),
    }


async def should_attempt(provider: str, config: dict) -> bool:
    state = await get_cb_state(provider)
    if state["status"] == CBState.CLOSED:
        return True
    if state["status"] == CBState.OPEN:
        elapsed = time.time() - state["last_failure_time"]
        if elapsed > config["half_open_ttl"]:
            await redis.hset(f"cb:{provider}", "status", CBState.HALF_OPEN)
            return True
        return False
    # HALF_OPEN: 允许探测
    return True


async def record_success(provider: str):
    await redis.hset(f"cb:{provider}", mapping={
        "status": CBState.CLOSED,
        "failure_count": "0",
        "last_failure_time": "0",
    })


async def record_failure(provider: str, config: dict):
    key = f"cb:{provider}"
    current = await redis.hget(key, "failure_count")
    count = int(current or 0) + 1

    if count >= config["failure_threshold"]:
        await redis.hset(key, mapping={
            "status": CBState.OPEN,
            "failure_count": str(count),
            "last_failure_time": str(time.time()),
        })
    else:
        await redis.hset(key, mapping={
            "status": CBState.CLOSED,
            "failure_count": str(count),
            "last_failure_time": str(time.time()),
        })
```

- [ ] **Step 2: Commit**

```bash
git add gateway/circuit_breaker.py
git commit -m "feat: add circuit breaker with Redis-backed state"
```

---

### Task 17: Gateway 核心路由 (chat/completions)

**Files:**
- Create: `llm-gateway/gateway/routes.py`
- Modify: `llm-gateway/gateway/main.py`
- Create: `llm-gateway/gateway/pricing.py`

- [ ] **Step 1: 创建 pricing.py（模型定价表）**

```python
PRICING = {
    "gpt-4":        {"prompt": 300, "completion": 600},    # 分/1K tokens，成本
    "gpt-4-turbo":  {"prompt": 100, "completion": 300},
    "gpt-3.5-turbo":{"prompt": 5,   "completion": 15},
    "claude-3-opus":{"prompt": 150, "completion": 750},
    "claude-3-sonnet":{"prompt": 30,"completion": 150},
    "gemini-pro":   {"prompt": 5,   "completion": 15},
    "deepseek-chat":{"prompt": 2,   "completion": 2},
    "qwen-turbo":   {"prompt": 5,   "completion": 5},
}
# 对外售价 = 成本 × 1.5 (50%毛利)
MARKUP = 1.5


def calculate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> tuple[int, int]:
    """返回 (cost成本分, bill_cost售价分)"""
    pricing = PRICING.get(model, {"prompt": 10, "completion": 10})
    prompt_cost = (prompt_tokens / 1000) * pricing["prompt"]
    completion_cost = (completion_tokens / 1000) * pricing["completion"]
    cost_cents = int((prompt_cost + completion_cost) * 100)
    bill_cents = int(cost_cents * MARKUP)
    return cost_cents, bill_cents
```

- [ ] **Step 2: 创建 routes.py**

```python
import uuid
import json
import time
import asyncio
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import StreamingResponse

from schemas import UnifiedRequest
from middleware.auth import verify_api_key
from middleware.ratelimit import check_rate_limit
from adapters import find_adapter
from circuit_breaker import should_attempt, record_success, record_failure
from pricing import calculate_cost
from config import CIRCUIT_BREAKER_CONFIG, UPSTREAM_TIMEOUT, MAX_RETRIES, RETRY_BACKOFF_BASE
from redis_client import redis

router = APIRouter(prefix="/v1")

# 适配器实例 — 生产应从Redis加载supplier配置
_adapters = []


def set_adapters(adapters):
    global _adapters
    _adapters = adapters


@router.post("/chat/completions")
async def chat_completions(request: Request):
    # 1. 认证
    auth_info = await verify_api_key(request)
    user_id = auth_info["user_id"]
    rate_limit = auth_info["rate_limit"]

    # 2. 限流
    await check_rate_limit(user_id, rate_limit)

    # 3. 解析请求
    body = await request.json()
    unified = UnifiedRequest(**body)
    request_id = f"req_{uuid.uuid4().hex[:16]}"

    # 4. 查找适配器
    adapter = find_adapter(unified.model, _adapters)
    if adapter is None:
        raise HTTPException(status_code=400, detail={"error": "invalid_model"})

    # 5. 熔断检查
    cb_config = CIRCUIT_BREAKER_CONFIG.get(adapter.provider_name, {"failure_threshold": 3, "timeout_seconds": 30, "half_open_ttl": 30})
    if not await should_attempt(adapter.provider_name, cb_config):
        raise HTTPException(status_code=503, detail={"error": "model_temporarily_unavailable"})

    # 6. 调用供应商(含重试)
    t_start = time.time()
    last_error = None
    for attempt in range(MAX_RETRIES + 1):
        try:
            response = await asyncio.wait_for(
                adapter.chat_completion(unified),
                timeout=UPSTREAM_TIMEOUT,
            )
            latency_ms = int((time.time() - t_start) * 1000)

            # 熔断记录成功
            await record_success(adapter.provider_name)

            # 计算费用
            if response.usage:
                cost, bill_cost = calculate_cost(
                    unified.model,
                    response.usage.prompt_tokens,
                    response.usage.completion_tokens,
                )
                response.usage.total_tokens = response.usage.prompt_tokens + response.usage.completion_tokens
            else:
                cost, bill_cost = 0, 0
                response.usage = None

            # 7. 写用量日志到Redis Stream
            log_entry = {
                "request_id": request_id,
                "user_id": user_id,
                "api_key_prefix": "",
                "model": unified.model,
                "provider": adapter.provider_name,
                "prompt_tokens": str(response.usage.prompt_tokens) if response.usage else "0",
                "completion_tokens": str(response.usage.completion_tokens) if response.usage else "0",
                "cost": str(cost),
                "bill_cost": str(bill_cost),
                "latency_ms": str(latency_ms),
                "status": "success",
                "error_msg": "",
            }
            await redis.xadd("usage_log_stream", log_entry)

            return response.model_dump()

        except asyncio.TimeoutError:
            last_error = "timeout"
        except Exception as e:
            last_error = str(e)

        if attempt < MAX_RETRIES:
            await asyncio.sleep(RETRY_BACKOFF_BASE * (2 ** attempt))

    # 8. 全部重试失败
    latency_ms = int((time.time() - t_start) * 1000)
    await record_failure(adapter.provider_name, cb_config)

    # 写错误日志
    log_entry = {
        "request_id": request_id,
        "user_id": user_id,
        "api_key_prefix": "",
        "model": unified.model,
        "provider": adapter.provider_name,
        "prompt_tokens": "0",
        "completion_tokens": "0",
        "cost": "0",
        "bill_cost": "0",
        "latency_ms": str(latency_ms),
        "status": "error",
        "error_msg": last_error or "unknown",
    }
    await redis.xadd("usage_log_stream", log_entry)

    raise HTTPException(status_code=503, detail={"error": "upstream_error"})


@router.get("/models")
async def list_models():
    models = []
    for adapter in _adapters:
        for pattern in adapter.model_patterns:
            models.append({"id": pattern.rstrip("-*"), "object": "model"})
    return {"object": "list", "data": models}
```

- [ ] **Step 3: 更新 gateway/main.py，注册路由**

```python
from routes import router as gateway_router

app.include_router(gateway_router)
```

- [ ] **Step 4: Commit**

```bash
git add gateway/routes.py gateway/main.py gateway/pricing.py
git commit -m "feat: add gateway chat/completions route with full pipeline"
```

---

### Task 18: Gateway 启动时加载适配器

**Files:**
- Modify: `llm-gateway/gateway/main.py`

- [ ] **Step 1: 更新 gateway/main.py，在 lifespan 中初始化适配器**

```python
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from adapters import create_adapters, ADAPTER_CLASSES
from routes import router as gateway_router, set_adapters
from redis_client import redis


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 从Redis加载供应商配置
    supplier_configs = {}
    config_data = await redis.hgetall("supplier_configs")
    if config_data:
        import json
        for provider, cfg_str in config_data.items():
            supplier_configs[provider] = json.loads(cfg_str)
    else:
        # 开发环境从环境变量加载
        if os.getenv("OPENAI_API_KEY"):
            supplier_configs["openai"] = {
                "api_key": os.getenv("OPENAI_API_KEY"),
                "base_url": os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
            }
    adapters = create_adapters(supplier_configs)
    set_adapters(adapters)
    yield


app = FastAPI(title="LLM Gateway", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

Instrumentator().instrument(app).expose(app)

app.include_router(gateway_router)


@app.get("/health")
async def health():
    return {"status": "ok"}
```

- [ ] **Step 2: Commit**

```bash
git add gateway/main.py
git commit -m "feat: load adapter configs from Redis on startup"
```

---

## Phase 6: Nginx 与部署

### Task 19: Nginx 配置

**Files:**
- Create: `llm-gateway/nginx/nginx.conf`

- [ ] **Step 1: 创建 nginx/nginx.conf**

```nginx
events {
    worker_connections 1024;
}

http {
    # 安全Header
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # 限流
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=300r/m;
    limit_req_zone $binary_remote_addr zone=admin_limit:10m rate=60r/m;
    limit_conn_zone $binary_remote_addr zone=conn_limit:10m;

    # 上游
    upstream gateway_upstream {
        least_conn;
        server gateway:8000;
    }

    upstream admin_upstream {
        server admin:8001;
    }

    upstream frontend_upstream {
        server frontend:80;
    }

    server {
        listen 443 ssl;
        http2 on;

        ssl_certificate     /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;
        ssl_protocols TLSv1.3;

        # 客户端最大body
        client_max_body_size 1m;

        # API 路由
        location /v1/ {
            limit_req zone=api_limit burst=50 nodelay;
            limit_conn conn_limit 50;
            proxy_pass http://gateway_upstream;
            proxy_http_version 1.1;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_read_timeout 120s;
            proxy_buffering off;  # SSE需要
        }

        # Admin API
        location /admin/api/ {
            limit_req zone=admin_limit burst=20 nodelay;
            proxy_pass http://admin_upstream;
            proxy_http_version 1.1;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        }

        # 管理后台前端
        location /admin/ {
            proxy_pass http://frontend_upstream/;
            proxy_set_header Host $host;
        }

        location / {
            proxy_pass http://frontend_upstream/;
            proxy_set_header Host $host;
        }

        # robots.txt
        location = /robots.txt {
            return 200 "User-agent: *\nDisallow: /admin/\n";
        }
    }
}
```

- [ ] **Step 2: 生成自签证书（开发用）**

```bash
mkdir -p D:/code/llm-gateway/nginx/ssl
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout D:/code/llm-gateway/nginx/ssl/key.pem \
  -out D:/code/llm-gateway/nginx/ssl/cert.pem \
  -subj "/CN=localhost"
```

- [ ] **Step 3: Commit**

```bash
git add nginx/
git commit -m "feat: add nginx config with SSL, rate limiting, routing"
```

---

## Phase 7: 管理后台前端 (Vue 3)

### Task 20: 前端脚手架与路由

**Files:**
- Create: `llm-gateway/frontend/package.json`
- Create: `llm-gateway/frontend/vite.config.js`
- Create: `llm-gateway/frontend/index.html`
- Create: `llm-gateway/frontend/nginx-frontend.conf`
- Create: `llm-gateway/frontend/src/main.js`
- Create: `llm-gateway/frontend/src/App.vue`
- Create: `llm-gateway/frontend/src/router.js`
- Create: `llm-gateway/frontend/src/api.js`

- [ ] **Step 1: 创建 package.json**

```json
{
  "name": "llm-gateway-frontend",
  "version": "1.0.0",
  "scripts": {
    "dev": "vite",
    "build": "vite build"
  },
  "dependencies": {
    "vue": "^3.5.0",
    "vue-router": "^4.4.0"
  },
  "devDependencies": {
    "@vitejs/plugin-vue": "^5.2.0",
    "vite": "^6.0.0"
  }
}
```

- [ ] **Step 2: 创建 vite.config.js**

```javascript
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    proxy: {
      '/admin/api': 'http://localhost:8001',
      '/v1': 'http://localhost:8000',
    }
  }
})
```

- [ ] **Step 3: 创建 index.html**

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>LLM Gateway</title>
</head>
<body>
  <div id="app"></div>
  <script type="module" src="/src/main.js"></script>
</body>
</html>
```

- [ ] **Step 4: 创建 nginx-frontend.conf**

```nginx
server {
    listen 80;
    root /usr/share/nginx/html;
    index index.html;
    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

- [ ] **Step 5: 创建 src/main.js**

```javascript
import { createApp } from 'vue'
import App from './App.vue'
import router from './router'

createApp(App).use(router).mount('#app')
```

- [ ] **Step 6: 创建 src/api.js**

```javascript
const BASE = '/admin/api'

function getToken() {
  return localStorage.getItem('access_token')
}

async function request(path, options = {}) {
  const headers = { 'Content-Type': 'application/json', ...options.headers }
  const token = getToken()
  if (token) headers['Authorization'] = `Bearer ${token}`
  const res = await fetch(`${BASE}${path}`, { ...options, headers })
  if (res.status === 401) {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    window.location = '/admin/login'
    throw new Error('unauthorized')
  }
  if (!res.ok) {
    const err = await res.json().catch(() => ({ error: 'request_failed' }))
    throw new Error(err.error || 'request_failed')
  }
  return res.json()
}

export const api = {
  login: (email, password) =>
    request('/auth/login', { method: 'POST', body: JSON.stringify({ email, password }) }),

  register: (username, email, password) =>
    request('/auth/register', { method: 'POST', body: JSON.stringify({ username, email, password }) }),

  sendCode: (email) =>
    request('/auth/send-code', { method: 'POST', body: JSON.stringify({ email }) }),

  verifyCode: (email, code) =>
    request('/auth/verify-code', { method: 'POST', body: JSON.stringify({ email, code }) }),

  getMe: () => request('/auth/me'),

  getDashboard: () => request('/reports/dashboard'),

  getTrend: (days = 7) => request(`/reports/trend?days=${days}`),

  getUsage: (page = 1) => request(`/reports/usage?page=${page}`),

  createKey: (name, rateLimit = 60) =>
    request('/keys', { method: 'POST', body: JSON.stringify({ name, rate_limit: rateLimit }) }),

  listKeys: () => request('/keys'),

  revokeKey: (id) => request(`/keys/${id}/revoke`, { method: 'POST' }),

  getPlans: () => request('/plans'),

  purchasePlan: (planId) => request(`/plans/${planId}/purchase`, { method: 'POST' }),
}
```

- [ ] **Step 7: 创建 src/router.js**

```javascript
import { createRouter, createWebHistory } from 'vue-router'
import Login from './pages/Login.vue'
import Register from './pages/Register.vue'
import Dashboard from './pages/Dashboard.vue'
import Keys from './pages/Keys.vue'
import Plans from './pages/Plans.vue'
import Usage from './pages/Usage.vue'

const routes = [
  { path: '/admin/login', component: Login },
  { path: '/admin/register', component: Register },
  { path: '/admin', component: Dashboard, meta: { auth: true } },
  { path: '/admin/keys', component: Keys, meta: { auth: true } },
  { path: '/admin/plans', component: Plans, meta: { auth: true } },
  { path: '/admin/usage', component: Usage, meta: { auth: true } },
  { path: '/:pathMatch(.*)*', redirect: '/admin' },
]

const router = createRouter({ history: createWebHistory(), routes })

router.beforeEach((to, _from, next) => {
  if (to.meta.auth && !localStorage.getItem('access_token')) {
    next('/admin/login')
  } else {
    next()
  }
})

export default router
```

- [ ] **Step 8: 创建 src/App.vue**

```vue
<template>
  <router-view />
</template>
```

- [ ] **Step 9: Commit**

```bash
git add frontend/
git commit -m "feat: add frontend scaffold with Vue 3 + Vue Router"
```

---

### Task 21: 前端页面 — 登录、注册

**Files:**
- Create: `llm-gateway/frontend/src/pages/Login.vue`
- Create: `llm-gateway/frontend/src/pages/Register.vue`

- [ ] **Step 1: 创建 Login.vue**

```vue
<template>
  <div style="max-width:400px;margin:100px auto;padding:32px;">
    <h2>登录 LLM Gateway</h2>
    <form @submit.prevent="login">
      <div><input v-model="email" type="email" placeholder="邮箱" required style="width:100%;padding:8px;margin:8px 0" /></div>
      <div><input v-model="password" type="password" placeholder="密码" required style="width:100%;padding:8px;margin:8px 0" /></div>
      <div v-if="error" style="color:red;margin:8px 0">{{ error }}</div>
      <button type="submit" :disabled="loading" style="width:100%;padding:10px;background:#4f46e5;color:white;border:none;border-radius:4px;cursor:pointer">
        {{ loading ? '登录中...' : '登录' }}
      </button>
    </form>
    <p style="margin-top:16px;text-align:center">
      还没有账号？<router-link to="/admin/register">注册</router-link>
    </p>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api'

const router = useRouter()
const email = ref('')
const password = ref('')
const loading = ref(false)
const error = ref('')

async function login() {
  loading.value = true
  error.value = ''
  try {
    const data = await api.login(email.value, password.value)
    localStorage.setItem('access_token', data.access_token)
    localStorage.setItem('refresh_token', data.refresh_token)
    router.push('/admin')
  } catch (e) {
    error.value = '邮箱或密码错误'
  } finally {
    loading.value = false
  }
}
</script>
```

- [ ] **Step 2: 创建 Register.vue**

```vue
<template>
  <div style="max-width:400px;margin:100px auto;padding:32px;">
    <h2>注册</h2>
    <form @submit.prevent="step === 1 ? sendCode() : verifyCode()">
      <div v-if="step === 1">
        <div><input v-model="username" placeholder="用户名" required style="width:100%;padding:8px;margin:8px 0" /></div>
        <div><input v-model="email" type="email" placeholder="邮箱" required style="width:100%;padding:8px;margin:8px 0" /></div>
        <div><input v-model="password" type="password" placeholder="密码" required style="width:100%;padding:8px;margin:8px 0" /></div>
      </div>
      <div v-else>
        <p>验证码已发送到 {{ email }}</p>
        <div><input v-model="code" placeholder="6位验证码" required style="width:100%;padding:8px;margin:8px 0" maxlength="6" /></div>
      </div>
      <div v-if="error" style="color:red;margin:8px 0">{{ error }}</div>
      <div v-if="success" style="color:green;margin:8px 0">{{ success }}</div>
      <button type="submit" :disabled="loading" style="width:100%;padding:10px;background:#4f46e5;color:white;border:none;border-radius:4px;cursor:pointer">
        {{ loading ? '处理中...' : step === 1 ? '发送验证码' : '验证并登录' }}
      </button>
    </form>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api'

const router = useRouter()
const step = ref(1)
const username = ref('')
const email = ref('')
const password = ref('')
const code = ref('')
const loading = ref(false)
const error = ref('')
const success = ref('')

async function sendCode() {
  loading.value = true
  error.value = ''
  try {
    await api.register(username.value, email.value, password.value)
    step.value = 2
    success.value = '验证码已发送，请查收邮件'
  } catch (e) {
    error.value = e.message === 'email_exists' ? '该邮箱已注册' : '注册失败，请稍后重试'
  } finally {
    loading.value = false
  }
}

async function verifyCode() {
  loading.value = true
  error.value = ''
  try {
    const data = await api.verifyCode(email.value, code.value)
    localStorage.setItem('access_token', data.access_token)
    localStorage.setItem('refresh_token', data.refresh_token)
    router.push('/admin')
  } catch (e) {
    error.value = '验证码错误或已过期'
  } finally {
    loading.value = false
  }
}
</script>
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/pages/Login.vue frontend/src/pages/Register.vue
git commit -m "feat: add login and register pages"
```

---

### Task 22: 前端页面 — Dashboard、Keys、Plans、Usage

**Files:**
- Create: `llm-gateway/frontend/src/pages/Dashboard.vue`
- Create: `llm-gateway/frontend/src/pages/Keys.vue`
- Create: `llm-gateway/frontend/src/pages/Plans.vue`
- Create: `llm-gateway/frontend/src/pages/Usage.vue`

- [ ] **Step 1: 创建 Dashboard.vue**

```vue
<template>
  <div style="max-width:800px;margin:0 auto;padding:32px;">
    <div style="display:flex;justify-content:space-between;align-items:center">
      <h2>LLM Gateway</h2>
      <nav>
        <router-link to="/admin" style="margin:0 8px">首页</router-link>
        <router-link to="/admin/keys" style="margin:0 8px">API Key</router-link>
        <router-link to="/admin/plans" style="margin:0 8px">套餐</router-link>
        <router-link to="/admin/usage" style="margin:0 8px">用量</router-link>
      </nav>
    </div>

    <div v-if="loading">加载中...</div>
    <template v-else>
      <div style="display:flex;gap:16px;margin:24px 0">
        <div style="flex:1;padding:24px;background:#f3f4f6;border-radius:8px;text-align:center">
          <div style="font-size:28px;font-weight:bold">{{ dashboard.today_calls }}</div>
          <div style="color:#6b7280">今日调用</div>
        </div>
        <div style="flex:1;padding:24px;background:#f3f4f6;border-radius:8px;text-align:center">
          <div style="font-size:28px;font-weight:bold">¥{{ dashboard.today_cost_yuan }}</div>
          <div style="color:#6b7280">今日消费</div>
        </div>
        <div style="flex:1;padding:24px;background:#f3f4f6;border-radius:8px;text-align:center">
          <div style="font-size:28px;font-weight:bold">¥{{ dashboard.balance_yuan }}</div>
          <div style="color:#6b7280">账户余额</div>
        </div>
      </div>

      <div style="background:#f9fafb;padding:24px;border-radius:8px;margin:16px 0">
        <h4>快速开始</h4>
        <code style="background:#1f2937;color:#f3f4f6;padding:12px;display:block;border-radius:4px;font-size:13px">
          curl {{ apiBase }}/v1/chat/completions \<br/>
          &nbsp;&nbsp;-H "Authorization: Bearer YOUR_API_KEY" \<br/>
          &nbsp;&nbsp;-d '{"model":"gpt-4","messages":[{"role":"user","content":"hello"}]}'
        </code>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { api } from '../api'

const loading = ref(true)
const dashboard = ref({ today_calls: 0, today_cost_yuan: 0, balance_yuan: 0 })
const apiBase = window.location.origin

onMounted(async () => {
  try {
    dashboard.value = await api.getDashboard()
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
})
</script>
```

- [ ] **Step 2: 创建 Keys.vue**

```vue
<template>
  <div style="max-width:800px;margin:0 auto;padding:32px;">
    <h2>API Key 管理</h2>
    <router-link to="/admin">← 返回首页</router-link>

    <div style="margin:24px 0">
      <button @click="showCreate = true" style="padding:10px 20px;background:#4f46e5;color:white;border:none;border-radius:4px;cursor:pointer">创建新 Key</button>
    </div>

    <div v-if="showCreate" style="background:#f9fafb;padding:24px;border-radius:8px;margin:16px 0">
      <h4>创建 API Key</h4>
      <input v-model="newKeyName" placeholder="Key 名称（可选）" style="padding:8px;margin:8px 0;width:100%" />
      <div style="margin:12px 0">
        <button @click="createKey" :disabled="creating" style="padding:8px 20px;background:#059669;color:white;border:none;border-radius:4px;cursor:pointer">
          {{ creating ? '创建中...' : '确认创建' }}
        </button>
        <button @click="showCreate = false" style="padding:8px 20px;margin-left:8px;background:#6b7280;color:white;border:none;border-radius:4px;cursor:pointer">取消</button>
      </div>
      <div v-if="newKey" style="background:#fef3c7;padding:16px;border-radius:4px;margin-top:16px">
        <strong>新 Key（仅显示一次，请立即复制保存）：</strong>
        <code style="display:block;margin-top:8px;word-break:break-all">{{ newKey }}</code>
      </div>
    </div>

    <div v-if="keys.length">
      <div v-for="key in keys" :key="key.id" style="border:1px solid #e5e7eb;border-radius:8px;padding:16px;margin:8px 0">
        <div style="display:flex;justify-content:space-between">
          <div>
            <code style="font-size:16px">{{ key.key_prefix }}****</code>
            <span v-if="key.name" style="margin-left:8px;color:#6b7280">{{ key.name }}</span>
            <span :style="'margin-left:8px;padding:2px 8px;border-radius:4px;font-size:12px;' + (key.status === 'active' ? 'background:#d1fae5;color:#059669' : 'background:#fee2e2;color:#dc2626')">{{ key.status }}</span>
          </div>
          <button v-if="key.status === 'active'" @click="revokeKey(key.id)" style="padding:4px 12px;background:#dc2626;color:white;border:none;border-radius:4px;cursor:pointer;font-size:12px">吊销</button>
        </div>
        <div style="color:#9ca3af;font-size:12px;margin-top:8px">
          创建于 {{ new Date(key.created_at).toLocaleDateString() }}
          <span v-if="key.last_used_at"> · 最后使用 {{ new Date(key.last_used_at).toLocaleString() }}</span>
        </div>
      </div>
    </div>
    <div v-else-if="!showCreate" style="color:#9ca3af;text-align:center;margin:48px 0">还没有 API Key</div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { api } from '../api'

const keys = ref([])
const showCreate = ref(false)
const newKeyName = ref('')
const newKey = ref('')
const creating = ref(false)

onMounted(async () => {
  const data = await api.listKeys()
  keys.value = data.items
})

async function createKey() {
  creating.value = true
  try {
    const data = await api.createKey(newKeyName.value || null)
    newKey.value = data.api_key
    const list = await api.listKeys()
    keys.value = list.items
    newKeyName.value = ''
  } catch (e) {
    alert(e.message)
  } finally {
    creating.value = false
  }
}

async function revokeKey(id) {
  if (!confirm('确定吊销此 Key？吊销后立即失效。')) return
  await api.revokeKey(id)
  const data = await api.listKeys()
  keys.value = data.items
}
</script>
```

- [ ] **Step 3: 创建 Plans.vue**

```vue
<template>
  <div style="max-width:800px;margin:0 auto;padding:32px;">
    <h2>套餐购买</h2>
    <router-link to="/admin">← 返回首页</router-link>

    <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:16px;margin:24px 0">
      <div v-for="plan in plans" :key="plan.id" style="border:1px solid #e5e7eb;border-radius:8px;padding:24px;text-align:center">
        <h3>{{ plan.name }}</h3>
        <p v-if="plan.description" style="color:#6b7280">{{ plan.description }}</p>
        <div style="font-size:28px;font-weight:bold;margin:16px 0">¥{{ plan.price_yuan }}</div>
        <div style="color:#6b7280;margin:8px 0">{{ (plan.token_quota / 10000).toFixed(0) }} 万 Token</div>
        <div style="color:#6b7280;margin:8px 0">{{ plan.duration_days }} 天有效</div>
        <button @click="purchase(plan.id)" style="width:100%;padding:10px;background:#4f46e5;color:white;border:none;border-radius:4px;cursor:pointer;margin-top:12px">
          购买
        </button>
      </div>
    </div>
    <div v-if="message" style="background:#d1fae5;padding:12px;border-radius:4px;margin:16px 0">{{ message }}</div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { api } from '../api'

const plans = ref([])
const message = ref('')

onMounted(async () => {
  const data = await api.getPlans()
  plans.value = data.items
})

async function purchase(planId) {
  try {
    await api.purchasePlan(planId)
    message.value = '购买成功！'
  } catch (e) {
    alert(e.message === 'insufficient_balance' ? '余额不足，请先充值' : '购买失败')
  }
}
</script>
```

- [ ] **Step 4: 创建 Usage.vue**

```vue
<template>
  <div style="max-width:800px;margin:0 auto;padding:32px;">
    <h2>用量明细</h2>
    <router-link to="/admin">← 返回首页</router-link>

    <table style="width:100%;border-collapse:collapse;margin-top:24px">
      <thead>
        <tr style="border-bottom:2px solid #e5e7eb;text-align:left">
          <th style="padding:8px">时间</th>
          <th style="padding:8px">模型</th>
          <th style="padding:8px">Token</th>
          <th style="padding:8px">费用</th>
          <th style="padding:8px">状态</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="log in logs" :key="log.id" style="border-bottom:1px solid #f3f4f6">
          <td style="padding:8px;font-size:13px">{{ new Date(log.created_at).toLocaleString() }}</td>
          <td style="padding:8px;font-size:13px">{{ log.model }}</td>
          <td style="padding:8px;font-size:13px">{{ log.prompt_tokens + log.completion_tokens }}</td>
          <td style="padding:8px">¥{{ log.cost_yuan }}</td>
          <td style="padding:8px">
            <span :style="'padding:2px 6px;border-radius:4px;font-size:12px;' + (log.status === 'success' ? 'background:#d1fae5;color:#059669' : 'background:#fee2e2;color:#dc2626')">{{ log.status }}</span>
          </td>
        </tr>
        <tr v-if="logs.length === 0">
          <td colspan="5" style="text-align:center;padding:48px;color:#9ca3af">暂无使用记录</td>
        </tr>
      </tbody>
    </table>
    <div style="margin-top:16px;text-align:center">
      <button v-if="page > 1" @click="loadPage(page - 1)" style="padding:8px 16px;margin:0 4px;border:1px solid #d1d5db;background:white;border-radius:4px;cursor:pointer">上一页</button>
      <button @click="loadPage(page + 1)" style="padding:8px 16px;margin:0 4px;border:1px solid #d1d5db;background:white;border-radius:4px;cursor:pointer">下一页</button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { api } from '../api'

const logs = ref([])
const page = ref(1)

async function loadPage(p) {
  page.value = p
  const data = await api.getUsage(p)
  logs.value = data.items
}

onMounted(() => loadPage(1))
</script>
```

- [ ] **Step 5: Commit**

```bash
git add frontend/src/pages/
git commit -m "feat: add dashboard, keys, plans, usage pages"
```

---

## Phase 8: 最终集成

### Task 23: Admin 初始管理员 Seed

**Files:**
- Create: `llm-gateway/admin/seed.py`

- [ ] **Step 1: 创建 seed.py**

```python
import asyncio
import os
from database import engine, async_session
from models.user import User
from crypto import hash_password


async def seed_admin():
    async with engine.begin() as conn:
        await conn.run_sync(User.metadata.create_all)

    email = os.getenv("ADMIN_EMAIL", "admin@example.com")
    password = os.getenv("ADMIN_PASSWORD", "admin123")

    async with async_session() as session:
        from sqlalchemy import select
        result = await session.execute(select(User).where(User.email == email))
        if result.scalar_one_or_none():
            print("Admin user already exists")
            return

        import uuid
        admin = User(
            id=uuid.uuid4(),
            username="admin",
            email=email,
            password_hash=hash_password(password),
            role="super_admin",
        )
        session.add(admin)
        await session.commit()
        print(f"Admin user created: {email}")


if __name__ == "__main__":
    asyncio.run(seed_admin())
```

- [ ] **Step 2: 更新 admin/Dockerfile，构建时运行 seed（或通过环境变量控制）**

不强制跑 seed，改为在 main.py 的 lifespan 中首次启动自动创建管理员：

在 `admin/main.py` 的 `lifespan` 中 `await init_db()` 之后加入：

```python
import os
from sqlalchemy import select
from models.user import User
from crypto import hash_password

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
```

需要在上方导入 `uuid`, `async_session`, `User`, `hash_password`。

- [ ] **Step 3: Commit**

```bash
git add admin/
git commit -m "feat: auto-create admin user on first startup"
```

---

## 验证清单

完成所有 Task 后，按以下步骤验证：

```bash
# 1. 启动全部服务
cd D:/code/llm-gateway
docker compose up -d

# 2. 验证服务健康
curl -k https://localhost/health
curl -k https://localhost/admin/api/health

# 3. 验证管理后台
# 浏览器打开 https://localhost/admin
# 用 admin@example.com / admin123 登录

# 4. 验证 API 调用（先通过管理后台创建一个 API Key）
curl -k https://localhost/v1/chat/completions \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"gpt-4","messages":[{"role":"user","content":"hello"}]}'
```
