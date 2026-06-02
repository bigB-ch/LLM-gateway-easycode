# LLM Gateway

大模型 API 网关中转平台

## 两种启动方式

### 方式一：Docker Compose（生产/一键启动）

```bash
cp .env.example .env
# 编辑 .env 填入 OPENAI_API_KEY 等配置
docker compose up -d
# 访问 https://localhost/admin
```

### 方式二：本地开发（调试/热重载）

**1. 启动基础设施（PostgreSQL + Redis）**

```bash
docker compose -f docker-compose.dev.yml up -d
```

**2. 启动应用服务**

Windows:
```bat
start_dev.bat
```

Linux/Mac:
```bash
# 终端 1 - Admin
cd admin && DOTENV_PATH=../.env.dev uvicorn main:app --port 8001 --reload

# 终端 2 - Gateway
cd gateway && DOTENV_PATH=../.env.dev uvicorn main:app --port 8000 --reload

# 终端 3 - Frontend
cd frontend && npm run dev
```

**3. 访问**
- 管理后台: http://localhost:5173/admin
- Gateway API: http://localhost:8000
- Admin API: http://localhost:8001
- 默认管理员: admin@example.com / admin123

## 配置 OpenAI API Key

开发模式：在 `.env.dev` 中添加 `OPENAI_API_KEY=sk-xxx`

生产模式：在 `.env` 中添加 `OPENAI_API_KEY=sk-xxx`

或通过 Admin API 动态配置供应商 Key（登录管理后台 → 系统设置）。
