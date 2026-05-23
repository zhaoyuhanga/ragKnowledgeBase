# -*- coding: utf-8 -*-
"""
Milvus向量数据库仓库

本模块提供向量数据库的操作接口：
- Collection管理
- 向量插入
- 向量检索
- 向量删除
"""

from typing import Any, Dict, List, Optional
import time

from pymilvus import Collection, DataType, FieldSchema, CollectionSchema

from app.common.exception import BusinessException, ErrorCode
from app.common.logging import logger
from core.config import settings
from core.milvus import MilvusClient, get_milvus_client


class MilvusRepository:
    """
    Milvus向量数据库仓库

    提供向量数据库的CRUD操作。
    """

    def __init__(self):
        """初始化仓库"""
        self._client: Optional[MilvusClient] = None
        self._collection_name = "document_chunks"

    @property
    def client(self) -> MilvusClient:
        """获取Milvus客户端"""
        if self._client is None:
            self._client = get_milvus_client()
        return self._client

    def initialize_collection(self) -> Collection:
        """
        初始化集合

        创建document_chunks集合，如果已存在则直接返回。

        Returns:
            Collection: 集合对象
        """
        try:
            # 检查集合是否存在
            collection = self.client.create_collection(
                collection_name=self._collection_name,
                dimension=settings.embedding.dimension,
                description="RAG知识库文档块向量集合"
            )

            logger.info(
                f"Milvus集合初始化完成: {self._collection_name}",
                extra={"dimension": settings.embedding.dimension}
            )

            return collection

        except Exception as e:
            logger.error(f"Milvus集合初始化失败: {str(e)}")
            raise BusinessException(
                code=ErrorCode.INTERNAL_ERROR[0],
                message=f"Milvus集合初始化失败: {str(e)}"
            )

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
        if not entities:
            return []

        try:
            ids = self.client.insert(collection_name, entities)
            
            # 确保集合已准备好用于搜索（重新加载使新数据可见）
            self.ensure_collection_ready_for_search(collection_name)
            
            logger.info(
                f"Milvus插入成功",
                extra={
                    "collection_name": collection_name,
                    "count": len(entities)
                }
            )
            return ids

        except Exception as e:
            logger.error(f"Milvus插入失败: {str(e)}")
            raise BusinessException(
                code=ErrorCode.INTERNAL_ERROR[0],
                message=f"Milvus插入失败: {str(e)}"
            )

    def search(
        self,
        collection_name: str,
        vectors: List[List[float]],
        top_k: int = 10,
        expr: Optional[str] = None,
        output_fields: Optional[List[str]] = None
    ) -> List[List[Dict[str, Any]]]:
        """
        向量检索

        Args:
            collection_name: 集合名称
            vectors: 查询向量列表
            top_k: 返回结果数量
            expr: 过滤表达式
            output_fields: 输出字段

        Returns:
            List[List[Dict]]: 检索结果列表
        """
        if not vectors:
            return []

        try:
            # 搜索参数 - 增大 nprobe 以提高召回率和可见性
            # nprobe 越大，搜索的聚类中心越多，召回率越高，但速度会稍慢
            search_params = {
                "metric_type": "IP",  # 内积，适合归一化向量
                "index_type": "IVF_FLAT",
                "params": {"nprobe": 64}  # 从 10 增大到 64，显著提高召回率
            }

            if output_fields is None:
                output_fields = [
                    "document_id",
                    "version_id",
                    "chunk_id",
                    "title_path",
                    "page_start",
                    "page_end",
                    "chunk_type",
                    "quality_score"
                ]

            results = self.client.search(
                collection_name=collection_name,
                vectors=vectors,
                search_params=search_params,
                limit=top_k,
                output_fields=output_fields,
                expr=expr
            )

            logger.info(
                f"Milvus检索成功",
                extra={
                    "collection_name": collection_name,
                    "query_count": len(vectors),
                    "top_k": top_k
                }
            )

            return results

        except Exception as e:
            logger.error(f"Milvus检索失败: {str(e)}")
            raise BusinessException(
                code=ErrorCode.RETRIEVAL_FAILED[0],
                message=f"Milvus检索失败: {str(e)}"
            )

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
        if not ids:
            return

        try:
            self.client.delete_by_ids(collection_name, ids)
            logger.info(
                f"Milvus删除成功",
                extra={
                    "collection_name": collection_name,
                    "count": len(ids)
                }
            )

        except Exception as e:
            logger.error(f"Milvus删除失败: {str(e)}")
            raise BusinessException(
                code=ErrorCode.INTERNAL_ERROR[0],
                message=f"Milvus删除失败: {str(e)}"
            )

    def delete_by_chunk_ids(
        self,
        collection_name: str,
        chunk_ids: List[int]
    ) -> None:
        """
        根据Chunk ID删除实体

        注意：需要集合中包含chunk_id字段

        Args:
            collection_name: 集合名称
            chunk_ids: Chunk ID列表
        """
        if not chunk_ids:
            return

        try:
            collection = self.client.get_collection(collection_name)
            expr = f"chunk_id in {chunk_ids}"
            collection.delete(expr)
            collection.flush()
            
            # 确保删除生效 - 重新加载集合
            self.ensure_collection_ready_for_search(collection_name)

            logger.info(
                f"Milvus Chunk删除成功",
                extra={
                    "collection_name": collection_name,
                    "chunk_count": len(chunk_ids)
                }
            )

        except Exception as e:
            logger.error(f"Milvus Chunk删除失败: {str(e)}")
            # 不抛出异常，继续执行

    def delete_by_document(
        self,
        collection_name: str,
        document_id: int,
        version_id: Optional[int] = None
    ) -> int:
        """
        删除文档的所有向量

        Args:
            collection_name: 集合名称
            document_id: 文档ID
            version_id: 版本ID（可选）

        Returns:
            int: 删除数量
        """
        try:
            collection = self.client.get_collection(collection_name)

            # 构建过滤表达式
            if version_id:
                expr = f"document_id == {document_id} and version_id == {version_id}"
            else:
                expr = f"document_id == {document_id}"

            # 先查询要删除的数量
            # 然后删除
            collection.delete(expr)
            collection.flush()
            
            # 确保删除生效 - 重新加载集合
            self.ensure_collection_ready_for_search(collection_name)

            logger.info(
                f"Milvus文档向量删除成功",
                extra={
                    "collection_name": collection_name,
                    "document_id": document_id,
                    "version_id": version_id
                }
            )

            return 0  # 实际数量需要查询获取

        except Exception as e:
            logger.error(f"Milvus文档向量删除失败: {str(e)}")
            return 0

    def get_collection_stats(self, collection_name: str) -> Dict[str, Any]:
        """
        获取集合统计信息

        Args:
            collection_name: 集合名称

        Returns:
            Dict: 统计信息
        """
        try:
            collection = self.client.get_collection(collection_name)
            stats = collection.num_entities

            return {
                "collection_name": collection_name,
                "total_entities": stats,
                "dimension": settings.embedding.dimension
            }

        except Exception as e:
            logger.error(f"获取集合统计失败: {str(e)}")
            return {
                "collection_name": collection_name,
                "total_entities": 0,
                "dimension": settings.embedding.dimension,
                "error": str(e)
            }

    def exists(self, collection_name: str) -> bool:
        """
        检查集合是否存在

        Args:
            collection_name: 集合名称

        Returns:
            bool: 是否存在
        """
        try:
            from pymilvus import utility
            return utility.has_collection(collection_name, using=self.client._alias)
        except Exception:
            return False

    def get_collection_load_status(self, collection_name: str) -> Dict[str, Any]:
        """
        获取集合的加载状态信息
        
        Args:
            collection_name: 集合名称
            
        Returns:
            Dict: 加载状态信息
        """
        try:
            from pymilvus import utility
            is_loaded = self.client.is_collection_loaded(collection_name)
            
            return {
                "collection_name": collection_name,
                "is_loaded": is_loaded,
                "loaded_in_memory": is_loaded,
                "timestamp": time.time()
            }
        except Exception as e:
            logger.error(f"获取集合加载状态失败: {str(e)}")
            return {
                "collection_name": collection_name,
                "is_loaded": False,
                "error": str(e)
            }
    
    def ensure_collection_ready_for_search(self, collection_name: str) -> bool:
        """
        确保集合已准备好用于搜索（加载到内存）
        
        Args:
            collection_name: 集合名称
            
        Returns:
            bool: 是否成功
        """
        try:
            if not self.client.is_collection_loaded(collection_name):
                logger.info(f"集合 {collection_name} 未加载，正在加载...")
                self.client.reload_collection(collection_name)
            return True
        except Exception as e:
            logger.error(f"确保集合加载失败: {str(e)}")
            return False


class VectorSearchService:
    """
    向量检索服务

    提供基于向量数据库的检索功能。
    """

    def __init__(self):
        """初始化服务"""
        self._repository = MilvusRepository()
        self._embedding_service = None

    @property
    def repository(self) -> MilvusRepository:
        """获取仓库实例"""
        return self._repository

    def _get_embedding_service(self):
        """获取向量化服务"""
        if self._embedding_service is None:
            from app.services.embedding_service import get_embedding_service
            self._embedding_service = get_embedding_service()

        if self._embedding_service is None:
            raise BusinessException(
                code=ErrorCode.INTERNAL_ERROR[0],
                message="向量化服务初始化失败: embedding_service 为 None"
            )

        return self._embedding_service

    def search_by_text(
        self,
        query: str,
        top_k: int = 10,
        document_ids: Optional[List[int]] = None,
        chunk_types: Optional[List[str]] = None,
        min_quality_score: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        根据文本检索

        Args:
            query: 查询文本
            top_k: 返回数量
            document_ids: 文档ID筛选
            chunk_types: Chunk类型筛选
            min_quality_score: 最低质量评分

        Returns:
            List[Dict]: 检索结果
        """
        try:
            # 获取向量化服务
            embedding_service = self._get_embedding_service()

            # 向量化查询文本
            try:
                embedding, cached = embedding_service.encode_single(query)
            except Exception as e:
                logger.error(f"文本向量化失败: {str(e)}")
                raise BusinessException(
                    code=ErrorCode.EMBEDDING_FAILED[0],
                    message=f"文本向量化失败: {str(e)}"
                )

            # 构建过滤表达式
            filters = []
            if document_ids:
                filters.append(f"document_id in {document_ids}")
            if chunk_types:
                type_str = ", ".join([f'"{ct}"' for ct in chunk_types])
                filters.append(f"chunk_type in [{type_str}]")
            if min_quality_score is not None:
                filters.append(f"quality_score >= {min_quality_score}")

            expr = " and ".join(filters) if filters else None

            # 执行检索
            results = self.repository.search(
                collection_name="document_chunks",
                vectors=[embedding.tolist()],
                top_k=top_k,
                expr=expr
            )

            # 格式化结果
            formatted_results = []
            if results and len(results) > 0:
                for hit in results[0]:
                    formatted_results.append({
                        "chunk_id": hit.get("chunk_id"),
                        "distance": hit.get("distance"),
                        "document_id": hit.get("document_id"),
                        "version_id": hit.get("version_id"),
                        "title_path": hit.get("title_path"),
                        "page_start": hit.get("page_start"),
                        "page_end": hit.get("page_end"),
                        "chunk_type": hit.get("chunk_type"),
                        "quality_score": hit.get("quality_score")
                    })

            return formatted_results

        except BusinessException:
            raise
        except Exception as e:
            logger.error(f"向量检索失败: {str(e)}")
            raise BusinessException(
                code=ErrorCode.RETRIEVAL_FAILED[0],
                message=f"向量检索失败: {str(e)}"
            )

    def batch_search_by_text(
        self,
        queries: List[str],
        top_k: int = 10,
        document_ids: Optional[List[int]] = None
    ) -> List[List[Dict[str, Any]]]:
        """
        批量文本检索

        Args:
            queries: 查询文本列表
            top_k: 返回数量
            document_ids: 文档ID筛选

        Returns:
            List[List[Dict]]: 批量检索结果
        """
        try:
            embedding_service = self._get_embedding_service()

            # 批量向量化
            try:
                embeddings, _ = embedding_service.encode(queries, normalize=True)
            except Exception as e:
                logger.error(f"批量文本向量化失败: {str(e)}")
                raise BusinessException(
                    code=ErrorCode.EMBEDDING_FAILED[0],
                    message=f"批量文本向量化失败: {str(e)}"
                )

            # 构建过滤表达式
            expr = None
            if document_ids:
                expr = f"document_id in {document_ids}"

            # 批量检索
            results = self.repository.search(
                collection_name="document_chunks",
                vectors=[e.tolist() for e in embeddings],
                top_k=top_k,
                expr=expr
            )

            # 格式化结果
            formatted_batch_results = []
            for hits in results:
                formatted_hits = []
                for hit in hits:
                    formatted_hits.append({
                        "chunk_id": hit.get("chunk_id"),
                        "distance": hit.get("distance"),
                        "document_id": hit.get("document_id"),
                        "version_id": hit.get("version_id"),
                        "title_path": hit.get("title_path"),
                        "chunk_type": hit.get("chunk_type"),
                        "quality_score": hit.get("quality_score")
                    })
                formatted_batch_results.append(formatted_hits)

            return formatted_batch_results

        except BusinessException:
            raise
        except Exception as e:
            logger.error(f"批量向量检索失败: {str(e)}")
            raise BusinessException(
                code=ErrorCode.RETRIEVAL_FAILED[0],
                message=f"批量向量检索失败: {str(e)}"
            )


# 全局仓库实例
_milvus_repository: Optional[MilvusRepository] = None
_vector_search_service: Optional[VectorSearchService] = None


def get_milvus_repository() -> MilvusRepository:
    """获取Milvus仓库实例"""
    global _milvus_repository
    if _milvus_repository is None:
        _milvus_repository = MilvusRepository()
    return _milvus_repository


def get_vector_search_service() -> VectorSearchService:
    """获取向量检索服务实例"""
    global _vector_search_service
    if _vector_search_service is None:
        _vector_search_service = VectorSearchService()
    return _vector_search_service
