@echo off
chcp 65001 >nul
title RAG知识库系统 - Worker服务

echo.
echo ========================================
echo   RAG知识库系统 - Worker服务
echo ========================================
echo.
echo  Worker类型: %1
echo.

cd /d "%~dp0"
set PYTHONPATH=%CD%

if "%~1"=="" (
    echo 启动所有 Worker...
    python -m src.app.services.run_worker all
) else (
    echo 启动 %1 Worker...
    python -m src.app.services.run_worker %1
)
