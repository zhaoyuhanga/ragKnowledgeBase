#!/bin/bash
# ================================================
# RAG知识库系统 - 停止脚本（Linux/macOS）
# 说明：停止所有RAG相关服务
# ================================================

# 颜色定义
GREEN='\033[0;32m'
NC='\033[0m' # No Color

echo ""
echo "================================================"
echo "  RAG知识库系统 - 停止服务"
echo "================================================"
echo ""

# 停止后端服务
echo -e "${GREEN}[1/2]${NC} 停止后端服务..."
pkill -f "uvicorn src.main:app" 2>/dev/null || true
pkill -f "python.*uvicorn" 2>/dev/null || true
echo "      已发送停止信号"

# 停止前端服务（如果有）
echo -e "${GREEN}[2/2]${NC} 停止前端服务..."
pkill -f "node.*vite" 2>/dev/null || true
pkill -f "npm run dev" 2>/dev/null || true

echo ""
echo -e "${GREEN}[完成]${NC} 所有服务已停止"
echo ""
