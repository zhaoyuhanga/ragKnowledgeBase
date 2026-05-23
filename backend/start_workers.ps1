# RAG知识库系统 - Worker启动脚本
# 使用方法: .\start_workers.ps1 [worker_type]
# 例如: .\start_workers.ps1 parse  (启动单个Worker)
#      .\start_workers.ps1        (启动所有Worker)

param(
    [string]$WorkerType = "all"
)

$ErrorActionPreference = "Stop"

# 设置Python路径
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$env:PYTHONPATH = "$ScriptDir\src"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "RAG知识库系统 - Worker启动脚本" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "项目目录: $env:PYTHONPATH" -ForegroundColor Gray
Write-Host "Worker类型: $WorkerType" -ForegroundColor Gray
Write-Host ""

# 检查Python是否可用
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Python版本: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "错误: Python未安装或未添加到PATH" -ForegroundColor Red
    exit 1
}

# 启动Worker
Write-Host "正在启动 Worker..." -ForegroundColor Yellow

try {
    python -m src.app.services.run_worker $WorkerType
} catch {
    Write-Host "错误: Worker启动失败" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}
