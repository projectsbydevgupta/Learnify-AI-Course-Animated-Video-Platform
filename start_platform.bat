@echo off
title AI Course Platform Launcher
echo ============================================================
echo      Starting AI Course Platform (Full Stack)
echo ============================================================
echo.

:: 1. Ensure Redis container is running
echo [1/4] Ensuring Redis container is running...
docker start redis-server >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [INFO] Creating new redis-server container...
    docker run -d --name redis-server -p 6379:6379 redis:alpine
)
echo [OK] Redis is active on port 6379.
echo.

:: 2. Launch FastAPI Backend in a new window
echo [2/4] Launching FastAPI Backend (Port 8000)...
start "Backend - FastAPI (Port 8000)" cmd /k "cd /d %~dp0backend && .\venv\Scripts\uvicorn.exe main:app --reload --port 8000"

:: 3. Launch Celery Worker in a new window
echo [3/4] Launching Celery Worker (Video & AI Pipeline)...
start "Worker - Celery (Background Pipeline)" cmd /k "cd /d %~dp0backend && .\venv\Scripts\celery.exe -A celery_app worker --loglevel=info -P solo"

:: 4. Launch Next.js Frontend in a new window
echo [4/4] Launching Next.js Frontend (Port 3000)...
start "Frontend - Next.js (Port 3000)" cmd /k "cd /d %~dp0frontend && npm run dev"

echo.
echo ============================================================
echo  All 3 services have been launched in separate windows!
echo  Open your browser at: http://localhost:3000
echo ============================================================
pause
