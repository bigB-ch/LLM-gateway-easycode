import os
from pathlib import Path
from dotenv import load_dotenv

# 支持从 DOTENV_PATH 环境变量加载 .env 文件
env_path = os.getenv("DOTENV_PATH")
if env_path:
    load_dotenv(env_path)
else:
    # Docker 模式：尝试加载 .env，不存在就用默认值
    load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://gateway:gateway@postgres:5432/llm_gateway",
)
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")
JWT_SECRET = os.getenv("JWT_SECRET")
if not JWT_SECRET:
    raise RuntimeError("JWT_SECRET environment variable is required. Generate one with: openssl rand -hex 32")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7

SMTP_HOST = os.getenv("SMTP_HOST", "localhost")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM = os.getenv("SMTP_FROM", "noreply@example.com")
