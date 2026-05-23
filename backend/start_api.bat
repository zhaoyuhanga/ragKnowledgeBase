@echo off
chcp 65001 >nul
title RAG知识库系统 - API服务

echo.
echo ========================================
echo   RAG知识库系统 - API服务
echo ========================================
echo.

cd /d "%~dp0"
set PYTHONPATH=%CD%

echo 启动中...
echo.

uvicorn src.main:app --reload --host 127.0.0.1 --port 8011
