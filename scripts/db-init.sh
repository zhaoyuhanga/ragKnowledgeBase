#!/bin/bash
# ================================================
# RAG知识库系统 - 数据库初始化脚本（Linux/macOS）
# 说明：创建数据库和表结构
# ================================================

# 设置工作目录
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR/.."

# 颜色定义
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

echo ""
echo "================================================"
echo "  RAG知识库系统 - 数据库初始化"
echo "================================================"
echo ""

# 检查MySQL客户端
if command -v mysql &> /dev/null; then
    echo -e "${YELLOW}[1/2]${NC} 创建数据库..."
    mysql -h localhost -P 3308 -u root -p123456 -e "CREATE DATABASE IF NOT EXISTS rag_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;" 2>/dev/null
    echo -e "      ${GREEN}数据库创建成功${NC}"

    echo -e "${YELLOW}[2/2]${NC} 执行表结构初始化..."
    if [ -f "backend/init.sql" ]; then
        mysql -h localhost -P 3308 -u root -p123456 rag_db < backend/init.sql 2>/dev/null
        echo -e "      ${GREEN}表结构初始化完成${NC}"
    else
        echo "      初始化脚本不存在，跳过"
    fi
else
    echo -e "${YELLOW}[1/2]${NC} 使用Python初始化数据库..."
    cd backend
    python3 -c "
import pymysql
try:
    conn = pymysql.connect(
        host='localhost',
        port=3308,
        user='root',
        password='123456',
        charset='utf8mb4'
    )
    with conn.cursor() as cursor:
        cursor.execute('CREATE DATABASE IF NOT EXISTS rag_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci')
    conn.commit()
    conn.close()
    print('       数据库创建成功')
except Exception as e:
    print(f'       数据库创建失败: {e}')
"

    echo -e "${YELLOW}[2/2]${NC} 创建ORM表结构..."
    python3 -c "
from sqlalchemy import create_engine, text
from core.config import settings

try:
    engine = create_engine(settings.database.url, echo=True)
    with engine.connect() as conn:
        conn.execute(text('''
            CREATE TABLE IF NOT EXISTS documents (
                id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
                tenant_id BIGINT NOT NULL DEFAULT 1 COMMENT '租户ID',
                document_name VARCHAR(500) NOT NULL COMMENT '文档名称',
                file_type VARCHAR(50) COMMENT '文件类型',
                file_hash VARCHAR(64) COMMENT '文件哈希',
                file_size BIGINT COMMENT '文件大小',
                status VARCHAR(50) DEFAULT 'pending' COMMENT '状态',
                current_version_id BIGINT COMMENT '当前版本ID',
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                creator_id BIGINT COMMENT '创建人ID',
                updater_id BIGINT COMMENT '更新人ID',
                is_deleted TINYINT NOT NULL DEFAULT 0 COMMENT '是否删除',
                INDEX idx_documents_tenant (tenant_id),
                INDEX idx_documents_status (status),
                INDEX idx_documents_hash (file_hash)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='文档信息表'
        '''))
        conn.commit()
        print('       表结构创建成功')
except Exception as e:
    print(f'       表结构创建失败: {e}')
"
fi

echo ""
echo -e "${GREEN}[完成]${NC} 数据库初始化完成"
echo ""
