# ================================================
# RAG知识库系统 - Docker停止脚本（Windows）
# ================================================

@echo off
chcp 65001 >nul

echo.
echo ================================================
echo   RAG知识库系统 - Docker服务停止
echo ================================================
echo.

set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%"

REM 停止Docker服务
echo 停止Docker服务...
docker compose -f docker-compose.dev.yml down

echo.
echo [完成] Docker服务已停止
echo.

pause
