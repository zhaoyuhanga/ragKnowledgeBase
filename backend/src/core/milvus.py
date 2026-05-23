# -*- coding: utf-8 -*-
"""
Milvus向量数据库连接模块

本模块提供Milvus向量数据库的连接管理：
1. Milvus连接配置
2. 集合管理
3. 向量操作

使用示例：
    from core.milvus import get_milvus_client, milvus_client

    # 获取客户端
    client = get_milvus_client()

    # 插入向量
    client.insert(collection_name="documents", vectors=[[0.1, 0.2, ...]])
"""

import time
from typing import Any, Dict, List, Optional

from pymilvus import (
    Collection,
    CollectionSchema,
    DataType,
    FieldSchema,
    connections,
    utility
)

from app.common.logging import logger
from core.config import settings


# 全局客户端实例
_milvus_client: Optional[Any] = None


class MilvusClient:
    """
    Milvus客户端封装类

    提供向量数据库的操作方法。
    """

    def __init__(self):
        """初始化Milvus客户端"""
        self._connected = False
        self._alias = settings.milvus.alias
        self._loaded_collections: set = set()
        self._load_check_interval = 0.5
        self._max_load_wait_seconds = 30

    def connect(self) -> None:
        """
        连接到Milvus服务器
        """
        if self._connected:
            return

        try:
            connections.connect(
                alias=self._alias,
                host=settings.milvus.host,
                port=settings.milvus.port,
                timeout=settings.milvus.timeout
            )
            self._connected = True
            logger.info(
                "Milvus连接成功",
                extra={
                    "host": settings.milvus.host,
                    "port": settings.milvus.port
                }
            )
        except Exception as e:
            logger.error(
                f"Milvus连接失败: {str(e)}",
                extra={
                    "host": settings.milvus.host,
                    "port": settings.milvus.port,
                    "error": str(e)
                }
            )
            raise

    def disconnect(self) -> None:
        """
        断开Milvus连接
        """
        if self._connected:
            connections.disconnect(alias=self._alias)
            self._connected = False
            logger.info("Milvus连接已断开")

    def is_connected(self) -> bool:
        """
        检查是否已连接

        Returns:
            是否已连接
        """
        return self._connected

    def create_collection(
        self,
        collection_name: str,
        dimension: int = 1024,
        description: str = "",
        primary_field_name: str = "id",
        vector_field_name: str = "embedding",
        index_type: str = "IVF_FLAT",
        metric_type: str = "IP"
    ) -> Collection:
        """
        创建集合

        Args:
            collection_name: 集合名称
            dimension: 向量维度
            description: 集合描述
            primary_field_name: 主键字段名
            vector_field_name: 向量字段名
            index_type: 索引类型
            metric_type: 距离度量类型

        Returns:
            Collection: 集合对象
        """
        # 检查集合是否已存在
        if utility.has_collection(collection_name, using=self._alias):
            logger.info(f"集合 {collection_name} 已存在")
            return self.get_collection(collection_name)

        # 定义字段
        fields = [
            FieldSchema(
                name=primary_field_name,
                dtype=DataType.INT64,
                is_primary=True,
                auto_id=True,
                description="主键ID"
            ),
            FieldSchema(
                name="document_id",
                dtype=DataType.INT64,
                description="文档ID"
            ),
            FieldSchema(
                name="version_id",
                dtype=DataType.INT64,
                description="文档版本ID"
            ),
            FieldSchema(
                name="chunk_id",
                dtype=DataType.INT64,
                description="切分块ID"
            ),
            FieldSchema(
                name="title_path",
                dtype=DataType.VARCHAR,
                max_length=500,
                description="标题路径"
            ),
            FieldSchema(
                name="page_start",
                dtype=DataType.INT32,
                description="起始页码"
            ),
            FieldSchema(
                name="page_end",
                dtype=DataType.INT32,
                description="结束页码"
            ),
            FieldSchema(
                name="chunk_type",
                dtype=DataType.VARCHAR,
                max_length=50,
                description="块类型"
            ),
            FieldSchema(
                name="quality_score",
                dtype=DataType.FLOAT,
                description="质量评分"
            ),
            FieldSchema(
                name=vector_field_name,
                dtype=DataType.FLOAT_VECTOR,
                dim=dimension,
                description="向量"
            )
        ]

        # 创建schema
        schema = CollectionSchema(
            fields=fields,
            description=description or f"RAG知识库 {collection_name} 集合"
        )

        # 创建集合
        collection = Collection(
            name=collection_name,
            schema=schema,
            using=self._alias
        )

        # 创建索引
        index_params = {
            "metric_type": metric_type,
            "index_type": index_type,
            "params": {"nlist": 128}
        }

        collection.create_index(
            field_name=vector_field_name,
            index_params=index_params
        )

        logger.info(
            f"集合 {collection_name} 创建成功",
            extra={
                "collection_name": collection_name,
                "dimension": dimension,
                "index_type": index_type,
                "metric_type": metric_type
            }
        )

        return collection

    def get_collection(self, collection_name: str) -> Collection:
        """
        获取集合

        Args:
            collection_name: 集合名称

        Returns:
            Collection: 集合对象
        """
        return Collection(name=collection_name, using=self._alias)

    def insert(
        self,
        collection_name: str,
        entities: List[Dict[str, Any]]
    ) -> List[int]:
        """
        插入向量数据

        Args:
            collection_name: 集合名称
            entities: 实体列表

        Returns:
            List[int]: 插入的ID列表
        """
        collection = self.get_collection(collection_name)
        result = collection.insert(entities)
        
        # 确保 flush 完成 - 使用 flush 并等待数据真正持久化
        collection.flush()
        
        # 强制同步等待，确保数据可被搜索
        self._wait_for_flush_complete(collection_name)
        
        # 更新集合加载状态 - 新插入的数据需要重新加载才能被搜索
        if collection_name in self._loaded_collections:
            self._loaded_collections.discard(collection_name)
            logger.info(
                f"集合 {collection_name} 数据已更新，需要重新加载后才能搜索新数据",
                extra={"collection_name": collection_name, "inserted_count": len(entities)}
            )
        
        logger.info(
            f"Milvus插入并flush完成",
            extra={"collection_name": collection_name, "count": len(entities)}
        )
        
        return result.primary_keys
    
    def _wait_for_flush_complete(self, collection_name: str, timeout: float = 10.0) -> bool:
        """
        等待 flush 完成，确保数据可被搜索
        
        Args:
            collection_name: 集合名称
            timeout: 超时时间（秒）
            
        Returns:
            bool: 是否等待成功
        """
        start_time = time.time()
        try:
            while time.time() - start_time < timeout:
                # 使用 utility 检查集合统计信息，确保数据已刷新
                collection = self.get_collection(collection_name)
                entities_before = collection.num_entities
                
                # 再次获取确认数据已刷新
                time.sleep(0.1)
                entities_after = collection.num_entities
                
                if entities_before == entities_after:
                    logger.debug(
                        f"Flush完成确认",
                        extra={"collection_name": collection_name, "entities": entities_after}
                    )
                    return True
                    
            logger.warning(
                f"Flush等待超时",
                extra={"collection_name": collection_name, "timeout": timeout}
            )
            return False
            
        except Exception as e:
            logger.warning(
                f"Flush状态检查失败: {str(e)}",
                extra={"collection_name": collection_name}
            )
            return False
    
    def _ensure_collection_loaded(self, collection_name: str) -> None:
        """
        确保集合已加载到内存中用于搜索
        
        Args:
            collection_name: 集合名称
        """
        if collection_name in self._loaded_collections:
            return
            
        try:
            collection = self.get_collection(collection_name)
            
            # 加载集合到内存
            logger.info(f"正在加载集合 {collection_name} 到内存...")
            collection.load()
            
            # 等待加载完成
            self._wait_for_load_complete(collection_name)
            
            # 标记为已加载
            self._loaded_collections.add(collection_name)
            
            logger.info(
                f"集合 {collection_name} 加载完成",
                extra={"collection_name": collection_name, "entities": collection.num_entities}
            )
            
        except Exception as e:
            logger.error(
                f"加载集合失败: {str(e)}",
                extra={"collection_name": collection_name, "error": str(e)}
            )
            raise
    
    def _wait_for_load_complete(self, collection_name: str, timeout: float = 30.0) -> bool:
        """
        等待集合加载完成
        
        Args:
            collection_name: 集合名称
            timeout: 超时时间（秒）
            
        Returns:
            bool: 是否等待成功
        """
        start_time = time.time()
        try:
            # Milvus 的 load 操作是同步的，这里只是日志记录
            while time.time() - start_time < timeout:
                collection = self.get_collection(collection_name)
                
                # 检查集合状态 - 如果集合可以正常获取统计信息，说明已加载
                try:
                    stats = collection.num_entities
                    logger.debug(
                        f"集合加载状态确认",
                        extra={"collection_name": collection_name, "entities": stats}
                    )
                    return True
                except Exception:
                    time.sleep(self._load_check_interval)
                    continue
                    
            logger.warning(
                f"集合加载等待超时",
                extra={"collection_name": collection_name, "timeout": timeout}
            )
            return False
            
        except Exception as e:
            logger.warning(
                f"加载状态检查失败: {str(e)}",
                extra={"collection_name": collection_name}
            )
            return False
    
    def is_collection_loaded(self, collection_name: str) -> bool:
        """
        检查集合是否已加载
        
        Args:
            collection_name: 集合名称
            
        Returns:
            bool: 是否已加载
        """
        return collection_name in self._loaded_collections
    
    def reload_collection(self, collection_name: str) -> None:
        """
        重新加载集合（当有新数据插入后调用）
        
        Args:
            collection_name: 集合名称
        """
        if collection_name in self._loaded_collections:
            self._loaded_collections.discard(collection_name)
        self._ensure_collection_loaded(collection_name)

    def search(
        self,
        collection_name: str,
        vectors: List[List[float]],
        search_params: Dict[str, Any],
        limit: int = 10,
        output_fields: Optional[List[str]] = None,
        expr: Optional[str] = None
    ) -> List[List[Dict[str, Any]]]:
        """
        搜索向量

        Args:
            collection_name: 集合名称
            vectors: 查询向量列表
            search_params: 搜索参数
            limit: 返回结果数量
            output_fields: 输出字段
            expr: 过滤表达式

        Returns:
            List[List[Dict]]: 搜索结果
        """
        # 确保集合已加载（带状态跟踪，避免重复加载）
        self._ensure_collection_loaded(collection_name)
        
        collection = self.get_collection(collection_name)

        results = collection.search(
            data=vectors,
            anns_field="embedding",
            param=search_params,
            limit=limit,
            output_fields=output_fields or ["document_id", "version_id", "chunk_id", "title_path", "chunk_type"],
            expr=expr
        )

        # 格式化结果
        formatted_results = []
        for hits in results:
            hits_list = []
            for hit in hits:
                hit_dict = {
                    "id": hit.id,
                    "distance": hit.distance,
                    "document_id": hit.entity.get("document_id"),
                    "version_id": hit.entity.get("version_id"),
                    "chunk_id": hit.entity.get("chunk_id"),
                    "title_path": hit.entity.get("title_path"),
                    "chunk_type": hit.entity.get("chunk_type")
                }
                hits_list.append(hit_dict)
            formatted_results.append(hits_list)

        return formatted_results

    def delete_by_ids(
        self,
        collection_name: str,
        ids: List[int]
    ) -> None:
        """
        根据ID删除实体

        Args:
            collection_name: 集合名称
            ids: 要删除的ID列表
        """
        collection = self.get_collection(collection_name)
        expr = f"id in {ids}"
        collection.delete(expr)

    def drop_collection(self, collection_name: str) -> None:
        """
        删除集合

        Args:
            collection_name: 集合名称
        """
        if utility.has_collection(collection_name, using=self._alias):
            utility.drop_collection(collection_name, using=self._alias)
            logger.info(f"集合 {collection_name} 已删除")


def get_milvus_client() -> MilvusClient:
    """
    获取Milvus客户端实例

    Returns:
        MilvusClient: Milvus客户端实例
    """
    global _milvus_client
    if _milvus_client is None:
        _milvus_client = MilvusClient()
        _milvus_client.connect()
    return _milvus_client


def close_milvus_client() -> None:
    """
    关闭Milvus客户端
    """
    global _milvus_client
    if _milvus_client is not None:
        _milvus_client.disconnect()
        _milvus_client = None


# 创建全局客户端实例
def init_milvus() -> MilvusClient:
    """
    初始化Milvus连接

    Returns:
        MilvusClient: Milvus客户端实例
    """
    client = get_milvus_client()

    # 创建默认集合（如果不存在）
    try:
        client.create_collection(
            collection_name="document_chunks",
            dimension=settings.embedding.dimension,
            description="RAG知识库文档块向量集合"
        )
    except Exception as e:
        logger.warning(f"创建默认集合失败（可能已存在）: {str(e)}")

    return client
