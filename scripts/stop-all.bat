@echo off
chcp 65001 >nul
REM ================================================
REM RAG知识库系统 - 停止脚本（Windows）
REM 说明：停止所有RAG相关服务
REM ================================================

echo.
echo ================================================
echo   RAG知识库系统 - 停止服务
echo ================================================
echo.

REM 停止后端服务
echo [1/2] 停止后端服务...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq RAG后端服务*" >nul 2>&1
taskkill /F /FI "IMAGENAME eq uvicorn.exe" >nul 2>&1
echo       已发送停止信号

REM 停止前端服务（如果有）
echo [2/2] 停止前端服务...
taskkill /F /IM node.exe /FI "WINDOWTITLE eq *rag*" >nul 2>&1

echo.
echo [完成] 所有服务已停止
echo.

pause
