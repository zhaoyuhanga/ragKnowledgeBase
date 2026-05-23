@echo off
chcp 65001 >nul
REM ================================================
REM RAG知识库系统 - 一键启动脚本（Windows）
REM 环境：本地开发环境
REM 说明：启动所有必要的服务
REM ================================================

echo.
echo ================================================
echo   RAG知识库系统 - 快速启动
echo ================================================
echo.

REM 设置工作目录
set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%.."

REM 检查Python环境
where python >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [错误] 未找到Python，请先安装Python 3.12+
    pause
    exit /b 1
)

REM 检查后端依赖
echo [1/3] 检查后端依赖...
cd /d "%SCRIPT_DIR%..\backend"
python -m pip show fastapi >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo       安装后端依赖...
    python -m pip install -r requirements.txt -q
)

REM 创建必要的目录
echo [2/3] 创建必要目录...
if not exist ".\logs" mkdir ".\logs"
if not exist ".\data\uploads" mkdir ".\data\uploads"
if not exist ".\data\temp" mkdir ".\data\temp"

REM 启动后端服务
echo [3/3] 启动后端服务...
echo.
echo ================================================
echo   后端服务启动中...
echo   API地址: http://127.0.0.1:8011
echo   API文档: http://127.0.0.1:8011/docs
echo ================================================
echo.
echo 提示：按 Ctrl+C 停止服务
echo.

cd /d "%SCRIPT_DIR%..\backend\src"
set PYTHONPATH=%cd%
start "RAG后端服务" cmd /k "python -m uvicorn main:app --host 127.0.0.1 --port 8011 --reload"

echo 等待服务启动...
timeout /t 5 /nobreak >nul

REM 检查服务是否启动成功
curl -s http://127.0.0.1:8011/health >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo.
    echo [成功] 后端服务已启动！
    echo.
    echo 可用接口：
    echo   - API文档: http://127.0.0.1:8011/docs
    echo   - 健康检查: http://127.0.0.1:8011/health
    echo.
) else (
    echo.
    echo [警告] 服务可能未正常启动，请检查日志
    echo.
)

echo 按任意键退出此窗口（服务继续运行）...
pause >nul
