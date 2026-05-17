"""
Milvus Collection 重建脚本
危险操作：删除旧 collection 并重建 2560 维的新 collection

使用前请务必：
1. 备份重要数据
2. 确认 EMBEDDING_DIMENSION 已更新为 2560
3. 确保 Ollama embedding 服务正常运行

用法：
    python scripts/rebuild_milvus_collection.py [--dry-run]
"""

import argparse
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def rebuild_collection(dry_run: bool = False):
    """
    重建 Milvus Collection

    Args:
        dry_run: 如果为 True，只打印操作不实际执行
    """
    from pymilvus import connections, utility, Collection
    from app.config import settings

    print("=" * 60)
    print("Milvus Collection 重建脚本")
    print("=" * 60)
    print(f"Milvus Host: {settings.milvus_host}:{settings.milvus_port}")
    print(f"Collection Name: {settings.milvus_collection_name}")
    print(f"Embedding Dimension: {settings.embedding_dimension}")
    print(f"Dry Run: {dry_run}")
    print("=" * 60)

    # 连接 Milvus
    print("\n[1/4] 连接到 Milvus...")
    try:
        connections.connect(
            host=settings.milvus_host,
            port=settings.milvus_port,
            user=settings.milvus_user or None,
            password=settings.milvus_password or None
        )
        print("  连接成功")
    except Exception as e:
        print(f"  连接失败: {e}")
        return False

    collection_name = settings.milvus_collection_name

    # 检查旧 collection
    print(f"\n[2/4] 检查 Collection '{collection_name}'...")
    if utility.has_collection(collection_name):
        print(f"  Collection 存在，实体数量: ", end="")

        try:
            collection = Collection(collection_name)
            collection.load()
            count = collection.num_entities
            print(f"{count}")
            print(f"  警告: 将删除 {count} 个实体！")
        except Exception as e:
            print(f"无法获取实体数量: {e}")

        if dry_run:
            print("  [DRY RUN] 跳过删除操作")
        else:
            confirm = input("\n  确认删除 Collection? (yes/no): ")
            if confirm.lower() != 'yes':
                print("  操作已取消")
                connections.disconnect("default")
                return False

            print(f"  删除 Collection '{collection_name}'...")
            try:
                utility.drop_collection(collection_name)
                print("  删除成功")
            except Exception as e:
                print(f"  删除失败: {e}")
                connections.disconnect("default")
                return False
    else:
        print(f"  Collection 不存在，跳过删除")

    # 创建新 Collection
    print(f"\n[3/4] 创建新 Collection '{collection_name}'...")
    if dry_run:
        print("  [DRY RUN] 跳过创建操作")
    else:
        try:
            from pymilvus import CollectionSchema, FieldSchema, DataType

            dim = settings.embedding_dimension

            fields = [
                FieldSchema(name="id", dtype=DataType.VARCHAR, max_length=256, is_primary=True, auto_id=False),
                FieldSchema(name="document_id", dtype=DataType.INT64),
                FieldSchema(name="chunk_index", dtype=DataType.INT64),
                FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=65535),
                FieldSchema(name="filename", dtype=DataType.VARCHAR, max_length=512),
                FieldSchema(name="source_type", dtype=DataType.VARCHAR, max_length=20),
                FieldSchema(name="generated_from_question", dtype=DataType.VARCHAR, max_length=65535),
                FieldSchema(name="generated_at", dtype=DataType.VARCHAR, max_length=64),
                FieldSchema(name="llm_model", dtype=DataType.VARCHAR, max_length=100),
                FieldSchema(name="llm_provider", dtype=DataType.VARCHAR, max_length=50),
                FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=dim)
            ]

            schema = CollectionSchema(
                fields=fields,
                description=f"Knowledge base vector collection (dimension={dim})",
                enable_dynamic_field=True
            )

            collection = Collection(name=collection_name, schema=schema)

            # 创建索引
            index_params = {
                "metric_type": settings.milvus_metric_type,
                "index_type": settings.milvus_index_type,
                "params": {"nlist": settings.milvus_nlist}
            }

            collection.create_index(
                field_name="embedding",
                index_params=index_params
            )

            collection.load()
            print(f"  创建成功，维度: {dim}")
        except Exception as e:
            print(f"  创建失败: {e}")
            connections.disconnect("default")
            return False

    # 验证
    print(f"\n[4/4] 验证新 Collection...")
    if dry_run:
        print("  [DRY RUN] 跳过验证")
    else:
        try:
            if utility.has_collection(collection_name):
                new_collection = Collection(collection_name)
                new_collection.load()
                print(f"  Collection 验证成功，实体数量: {new_collection.num_entities}")
            else:
                print("  验证失败: Collection 不存在")
                connections.disconnect("default")
                return False
        except Exception as e:
            print(f"  验证失败: {e}")
            connections.disconnect("default")
            return False

    connections.disconnect("default")

    print("\n" + "=" * 60)
    if dry_run:
        print("DRY RUN 完成，未执行实际操作")
    else:
        print("重建完成！")
    print("=" * 60)

    return True


def main():
    parser = argparse.ArgumentParser(description="Milvus Collection 重建脚本")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="只打印操作不实际执行"
    )
    args = parser.parse_args()

    success = rebuild_collection(dry_run=args.dry_run)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
