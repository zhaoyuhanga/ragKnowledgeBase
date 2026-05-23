#!/bin/bash
# ================================================
# RAG知识库系统 - Docker启动脚本（Linux/macOS）
# ================================================

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo ""
echo "================================================"
echo "  RAG知识库系统 - Docker服务启动"
echo "================================================"
echo ""

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# 检查Docker是否安装
if ! command -v docker &> /dev/null; then
    echo -e "${RED}[错误] 未安装Docker，请先安装Docker Desktop${NC}"
    exit 1
fi

# 启动依赖服务
echo -e "${YELLOW}[1/2]${NC} 启动依赖服务（MySQL、Redis、Milvus、RabbitMQ）..."
docker compose -f docker-compose.dev.yml up -d

if [ $? -eq 0 ]; then
    echo -e "      ${GREEN}服务启动成功${NC}"
else
    echo -e "      ${RED}服务启动失败${NC}"
    exit 1
fi

echo ""
echo -e "${YELLOW}[2/2]${NC} 等待服务就绪..."
echo "      MySQL 3308"
echo "      Redis 6379"
echo "      Milvus 19530"
echo "      RabbitMQ 5672/15672"
echo ""

# 等待服务健康检查
sleep 30

echo ""
echo "================================================"
echo "  服务已启动"
echo "================================================"
echo ""
echo "管理地址："
echo "  - RabbitMQ管理界面: http://localhost:15672"
echo "  - Milvus管理界面: http://localhost:9091"
echo ""
echo "停止命令："
echo "  docker compose -f docker-compose.dev.yml down"
echo ""
