"""
Milvus Collection 重建脚本
用于在 schema 变更后重建向量数据库
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pymilvus import connections, utility, Collection
from app.config import settings
from app.core.logger import get_logger

logger = get_logger(__name__)


def reset_collection():
    """重建 Milvus Collection"""
    collection_name = settings.milvus_collection_name
    
    try:
        # 连接 Milvus
        logger.info(f"正在连接 Milvus ({settings.milvus_host}:{settings.milvus_port})...")
        connections.connect(
            alias="default",
            host=settings.milvus_host,
            port=settings.milvus_port,
            user=settings.milvus_user if settings.milvus_user else None,
            password=settings.milvus_password if settings.milvus_password else None
        )
        logger.info("Milvus 连接成功")
        
        # 检查 collection 是否存在
        if utility.has_collection(collection_name):
            collection = Collection(collection_name)
            stats = collection.num_entities
            logger.info(f"当前 Collection '{collection_name}' 存在，包含 {stats} 条数据")
            
            # 询问用户是否删除
            confirm = input(f"\n警告：删除 Collection 将清除所有向量数据！\n确认删除 '{collection_name}' 并重建？(yes/no): ")
            
            if confirm.lower() == 'yes':
                logger.info(f"正在删除 Collection: {collection_name}")
                utility.drop_collection(collection_name)
                logger.info("Collection 已删除")
            else:
                logger.info("操作已取消")
                return
        
        # 重新创建 collection（通过 VectorStore）
        from app.core.vectorstore import VectorStore
        
        logger.info("正在重建 Collection...")
        vs = VectorStore()
        vs._create_collection(collection_name)
        
        logger.info(f"✓ Collection '{collection_name}' 重建成功！")
        logger.info("请注意：所有现有的向量数据已丢失，需要重新上传文档")
        
    except Exception as e:
        logger.error(f"重建失败: {str(e)}")
        raise
    finally:
        connections.disconnect("default")


if __name__ == "__main__":
    print("=" * 50)
    print("Milvus Collection 重建工具")
    print("=" * 50)
    reset_collection()
