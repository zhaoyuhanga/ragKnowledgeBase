#!/bin/bash
# ================================================
# RAG知识库系统 - Docker停止脚本（Linux/macOS）
# ================================================

# 颜色定义
GREEN='\033[0;32m'
NC='\033[0m'

echo ""
echo "================================================"
echo "  RAG知识库系统 - Docker服务停止"
echo "================================================"
echo ""

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# 停止Docker服务
echo -e "${GREEN}[完成]${NC} Docker服务已停止"
docker compose -f docker-compose.dev.yml down

echo ""
