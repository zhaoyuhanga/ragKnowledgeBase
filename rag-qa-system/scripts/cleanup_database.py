"""
数据库和缓存清理脚本
危险操作：清空 documents、qa_logs 表和 Redis 缓存

使用前请务必：
1. 备份重要数据
2. 确认在测试环境执行
3. 修改数据库连接信息（如需要）

用法：
    python scripts/cleanup_database.py [--dry-run]
"""

import argparse
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def cleanup_database(dry_run: bool = False):
    """
    清理数据库和缓存

    Args:
        dry_run: 如果为 True，只打印操作不实际执行
    """
    from app.config import settings
    from sqlalchemy import create_engine, text

    print("=" * 60)
    print("数据库和缓存清理脚本")
    print("=" * 60)
    print(f"MySQL Host: {settings.mysql_host}:{settings.mysql_port}")
    print(f"MySQL Database: {settings.mysql_database}")
    print(f"Redis: {settings.redis_host}:{settings.redis_port}")
    print(f"Dry Run: {dry_run}")
    print("=" * 60)

    # 1. MySQL 清理
    print("\n[1/3] MySQL 数据库清理...")

    try:
        engine = create_engine(settings.mysql_url, pool_pre_ping=True)

        with engine.connect() as conn:
            # 检查表是否存在
            result = conn.execute(text("SHOW TABLES"))
            tables = [row[0] for row in result]
            print(f"  发现表: {tables}")

            # 检查 documents 表
            if 'documents' in tables:
                doc_count = conn.execute(text("SELECT COUNT(*) FROM documents")).scalar()
                print(f"  documents 表记录数: {doc_count}")

                if doc_count > 0 and not dry_run:
                    print("  警告: 即将删除所有文档记录！")

            # 检查 qa_logs 表
            if 'qa_logs' in tables:
                log_count = conn.execute(text("SELECT COUNT(*) FROM qa_logs")).scalar()
                print(f"  qa_logs 表记录数: {log_count}")

        engine.dispose()

    except Exception as e:
        print(f"  MySQL 连接失败: {e}")
        return False

    # 2. 确认执行
    if not dry_run:
        print("\n  确认清理操作（输入 'yes' 继续）: ", end="")
        confirm = input().strip().lower()
        if confirm != 'yes':
            print("  操作已取消")
            return False

    # 3. 执行清理
    if dry_run:
        print("\n[2/3] 执行清理（DRY RUN）...")
        print("  [DRY RUN] TRUNCATE TABLE documents")
        print("  [DRY RUN] TRUNCATE TABLE qa_logs")
    else:
        print("\n[2/3] 执行 MySQL 清理...")

        try:
            engine = create_engine(settings.mysql_url, pool_pre_ping=True)

            with engine.connect() as conn:
                # 关闭外键检查
                conn.execute(text("SET FOREIGN_KEY_CHECKS = 0"))

                # 清空 documents（会级联删除 document_chunks）
                conn.execute(text("TRUNCATE TABLE documents"))
                print("  documents 表已清空")

                # 清空 qa_logs
                conn.execute(text("TRUNCATE TABLE qa_logs"))
                print("  qa_logs 表已清空")

                # 重新启用外键检查
                conn.execute(text("SET FOREIGN_KEY_CHECKS = 1"))
                conn.commit()

            engine.dispose()

        except Exception as e:
            print(f"  MySQL 清理失败: {e}")
            return False

    # 4. Redis 清理
    print("\n[3/3] Redis 缓存清理...")

    if dry_run:
        print("  [DRY RUN] FLUSHDB")
    else:
        try:
            import redis
            r = redis.Redis(
                host=settings.redis_host,
                port=settings.redis_port,
                db=settings.redis_db,
                password=settings.redis_password if settings.redis_password else None,
                decode_responses=True
            )

            # 检查当前键数量
            key_count = len(r.keys('*'))
            print(f"  当前 Redis 键数量: {key_count}")

            # 清理 RAG 相关缓存
            patterns = ['qa:*', 'doc:*', 'embed:*', 'session:*']
            total_deleted = 0

            for pattern in patterns:
                keys = r.keys(pattern)
                if keys:
                    r.delete(*keys)
                    total_deleted += len(keys)
                    print(f"  已删除 {len(keys)} 个匹配 '{pattern}' 的键")

            print(f"  共删除 {total_deleted} 个缓存键")

        except Exception as e:
            print(f"  Redis 清理失败: {e}")
            # Redis 失败不阻断流程

    print("\n" + "=" * 60)
    if dry_run:
        print("DRY RUN 完成，未执行实际操作")
    else:
        print("清理完成！")
    print("=" * 60)

    return True


def main():
    parser = argparse.ArgumentParser(description="数据库和缓存清理脚本")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="只打印操作不实际执行"
    )
    args = parser.parse_args()

    success = cleanup_database(dry_run=args.dry_run)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
