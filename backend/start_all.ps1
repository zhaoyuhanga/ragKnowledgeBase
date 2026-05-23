# RAG知识库系统 - 一键启动脚本
# 同时启动 API 和 Worker 服务

param(
    [switch]$ApiOnly,      # 只启动 API
    [switch]$WorkerOnly,   # 只启动 Worker
    [string]$WorkerType = "all"  # Worker类型: all, parse, clean, chunk, embedding, index
)

$ErrorActionPreference = "Stop"

$BackendDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$env:PYTHONPATH = $BackendDir

$Host.UI.RawUI.WindowTitle = "RAG知识库"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  RAG知识库系统 - 一键启动" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "项目目录: $BackendDir" -ForegroundColor Gray
Write-Host "Worker类型: $WorkerType" -ForegroundColor Gray
Write-Host ""

# 检查Python是否可用
try {
    $pythonVersion = python --version 2>&1 | Out-String
    Write-Host "Python版本: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "[错误] Python未安装或未添加到PATH" -ForegroundColor Red
    exit 1
}

function Start-Service-InNewWindow {
    param(
        [string]$Title,
        [string]$Command,
        [string]$Color
    )
    
    $scriptContent = @"
Set-Location '$BackendDir'
`$env:PYTHONPATH = '$BackendDir'
Write-Host ''
Write-Host '========================================' -ForegroundColor Cyan
Write-Host '  $Title' -ForegroundColor Cyan
Write-Host '========================================' -ForegroundColor Cyan
Write-Host ''
$Command
"@
    
    Start-Process powershell -ArgumentList "-NoExit", "-Command", $scriptContent
    Write-Host "[启动] $Title" -ForegroundColor $Color
}

# 根据参数启动服务
if ($ApiOnly) {
    # 只启动 API
    Start-Service-InNewWindow -Title "API 服务" -Command "uvicorn src.main:app --reload --host 127.0.0.1 --port 8011" -Color Green
} elseif ($WorkerOnly) {
    # 只启动 Worker
    Start-Service-InNewWindow -Title "Worker 服务 ($WorkerType)" -Command "python -m src.app.services.run_worker $WorkerType" -Color Yellow
} else {
    # 启动全部服务
    Write-Host "[1/2] 启动 API 服务..." -ForegroundColor Yellow
    Start-Service-InNewWindow -Title "API 服务 (http://127.0.0.1:8011)" -Command "uvicorn src.main:app --reload --host 127.0.0.1 --port 8011" -Color Green
    
    Start-Sleep -Milliseconds 500
    
    Write-Host "[2/2] 启动 Worker 服务 ($WorkerType)..." -ForegroundColor Yellow
    Start-Service-InNewWindow -Title "Worker 服务 ($WorkerType)" -Command "python -m src.app.services.run_worker $WorkerType" -Color Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  服务已在新窗口中启动" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "API地址: http://127.0.0.1:8011" -ForegroundColor Gray
Write-Host "Swagger: http://127.0.0.1:8011/docs" -ForegroundColor Gray
Write-Host "ReDoc:   http://127.0.0.1:8011/redoc" -ForegroundColor Gray
Write-Host ""
Write-Host "使用参数:" -ForegroundColor Cyan
Write-Host "  -ApiOnly     只启动 API 服务" -ForegroundColor Gray
Write-Host "  -WorkerOnly  只启动 Worker 服务" -ForegroundColor Gray
Write-Host "  -WorkerType  Worker类型 (all/parse/clean/chunk/embedding/index)" -ForegroundColor Gray
Write-Host ""
