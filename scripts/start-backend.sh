#!/bin/bash
# ================================================
# RAG知识库系统 - 快速启动脚本（Linux/macOS）
# 环境：本地开发环境
# 说明：启动所有必要的服务
# ================================================

# 设置工作目录
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR/.."

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo ""
echo "================================================"
echo "  RAG知识库系统 - 快速启动"
echo "================================================"
echo ""

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}[错误] 未找到Python3，请先安装Python 3.12+${NC}"
    exit 1
fi

# 检查后端依赖
echo -e "${YELLOW}[1/3]${NC} 检查后端依赖..."
cd backend
if ! python3 -c "import fastapi" &> /dev/null; then
    echo "      安装后端依赖..."
    pip install -r requirements.txt -q
fi

# 创建必要的目录
echo -e "${YELLOW}[2/3]${NC} 创建必要目录..."
mkdir -p ./logs
mkdir -p ./data/uploads
mkdir -p ./data/temp

# 启动后端服务
echo -e "${YELLOW}[3/3]${NC} 启动后端服务..."
echo ""
echo "================================================"
echo "  后端服务启动中..."
echo "  API地址: http://127.0.0.1:8011"
echo "  API文档: http://127.0.0.1:8011/docs"
echo "================================================"
echo ""
echo "提示：按 Ctrl+C 停止服务"
echo ""

# 切换到src目录并设置PYTHONPATH
cd backend/src
export PYTHONPATH="${PWD}"

# 启动服务
python3 -m uvicorn main:app --host 127.0.0.1 --port 8011 --reload
