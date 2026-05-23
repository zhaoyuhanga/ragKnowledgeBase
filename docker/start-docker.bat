# ================================================
# RAG知识库系统 - Docker启动脚本（Windows）
# ================================================

@echo off
chcp 65001 >nul

echo.
echo ================================================
echo   RAG知识库系统 - Docker服务启动
echo ================================================
echo.

set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%"

REM 检查Docker是否安装
docker --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [错误] 未安装Docker，请先安装Docker Desktop
    pause
    exit /b 1
)

REM 启动依赖服务
echo [1/2] 启动依赖服务（MySQL、Redis、Milvus、RabbitMQ）...
docker compose -f docker-compose.dev.yml up -d

if %ERRORLEVEL% equ 0 (
    echo       服务启动成功
) else (
    echo       服务启动失败
    pause
    exit /b 1
)

echo.
echo [2/2] 等待服务就绪...
echo       MySQL 3308
echo       Redis 6379
echo       Milvus 19530
echo       RabbitMQ 5672/15672
echo.

REM 等待服务健康检查
timeout /t 30 /nobreak >nul

echo.
echo ================================================
echo   服务已启动
echo ================================================
echo.
echo 管理地址：
echo   - RabbitMQ管理界面: http://localhost:15672
echo   - Milvus管理界面: http://localhost:9091
echo.
echo 停止命令：
echo   docker compose -f docker-compose.dev.yml down
echo.

pause
