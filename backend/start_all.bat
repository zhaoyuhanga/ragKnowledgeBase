@echo off
chcp 65001 >nul
title RAG知识库系统 - 一键启动

echo.
echo ========================================
echo   RAG知识库系统 - 一键启动
echo ========================================
echo.
echo 项目目录: %~dp0
echo.

cd /d "%~dp0"

echo [1/2] 启动 API 服务...
start "RAG-API" cmd /k "set PYTHONPATH=%CD% && uvicorn src.main:app --reload --host 127.0.0.1 --port 8011"

timeout /t 1 /nobreak >nul

echo [2/2] 启动 Worker 服务...
start "RAG-Worker" cmd /k "set PYTHONPATH=%CD% && python -m src.app.services.run_worker all"

echo.
echo ========================================
echo   服务已启动，请查看新窗口
echo ========================================
echo.
echo API地址: http://127.0.0.1:8011
echo Swagger: http://127.0.0.1:8011/docs
echo.
echo 按任意键退出...
pause >nul
