@echo off
chcp 65001 >nul
REM ================================================
REM RAG知识库系统 - 数据库初始化脚本（Windows）
REM 说明：创建数据库和表结构
REM ================================================

echo.
echo ================================================
echo   RAG知识库系统 - 数据库初始化
echo ================================================
echo.

set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%..\backend"

REM 检查MySQL客户端
where mysql >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [警告] 未找到mysql客户端，尝试使用Python创建数据库...
    goto :python_init
)

REM 使用MySQL客户端初始化
echo [1/2] 创建数据库...
mysql -h localhost -P 3308 -u root -p123456 -e "CREATE DATABASE IF NOT EXISTS rag_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;" 2>nul
if %ERRORLEVEL% equ 0 (
    echo       数据库创建成功
) else (
    echo       数据库可能已存在或连接失败
)

REM 执行SQL初始化脚本
echo [2/2] 执行表结构初始化...
if exist "init.sql" (
    mysql -h localhost -P 3308 -u root -p123456 rag_db < init.sql 2>nul
    echo       表结构初始化完成
) else (
    echo       初始化脚本不存在，跳过
)

goto :end

:python_init
echo [1/2] 使用Python初始化数据库...
python -c "
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

echo [2/2] 创建ORM表结构...
python -c "
from sqlalchemy import create_engine, text
from core.config import settings

try:
    engine = create_engine(settings.database.url, echo=True)
    with engine.connect() as conn:
        # 创建表结构
        conn.execute(text('''
            CREATE TABLE IF NOT EXISTS documents (
                id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '\''主键ID'\'',
                tenant_id BIGINT NOT NULL DEFAULT 1 COMMENT '\''租户ID'\'',
                document_name VARCHAR(500) NOT NULL COMMENT '\''文档名称'\'',
                file_type VARCHAR(50) COMMENT '\''文件类型'\'',
                file_hash VARCHAR(64) COMMENT '\''文件哈希'\'',
                file_size BIGINT COMMENT '\''文件大小'\'',
                status VARCHAR(50) DEFAULT '\''pending'\'' COMMENT '\''状态'\'',
                current_version_id BIGINT COMMENT '\''当前版本ID'\'',
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '\''创建时间'\'',
                updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '\''更新时间'\'',
                creator_id BIGINT COMMENT '\''创建人ID'\'',
                updater_id BIGINT COMMENT '\''更新人ID'\'',
                is_deleted TINYINT NOT NULL DEFAULT 0 COMMENT '\''是否删除'\'',
                INDEX idx_documents_tenant (tenant_id),
                INDEX idx_documents_status (status),
                INDEX idx_documents_hash (file_hash)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='\''文档信息表'\''
        '''))
        conn.commit()
        print('       表结构创建成功')
except Exception as e:
    print(f'       表结构创建失败: {e}')
"

:end
echo.
echo [完成] 数据库初始化完成
echo.

pause
