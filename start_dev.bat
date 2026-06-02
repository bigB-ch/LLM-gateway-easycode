@echo off
echo === LLM Gateway 开发模式 ===
echo.
echo 确保已启动基础设施：
echo   docker compose -f docker-compose.dev.yml up -d
echo.
echo 启动 Admin 服务 (端口 8001)...
start "Admin" cmd /c "cd /d D:\code\llm-gateway\admin && set DOTENV_PATH=..\.env.dev && python -m uvicorn main:app --host 0.0.0.0 --port 8001 --reload"
echo 启动 Gateway 服务 (端口 8000)...
start "Gateway" cmd /c "cd /d D:\code\llm-gateway\gateway && set DOTENV_PATH=..\.env.dev && python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload"
echo 启动 Frontend (端口 5173)...
start "Frontend" cmd /c "cd /d D:\code\llm-gateway\frontend && npm run dev"
echo.
echo 管理后台: http://localhost:5173/admin
echo Gateway API: http://localhost:8000
echo Admin API: http://localhost:8001
echo.
pause
