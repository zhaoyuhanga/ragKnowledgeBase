"""
RAG 问答系统 - ChromaDB 向量数据库模块
向量存储和检索操作
"""

from typing import List, Dict, Optional, Any
from pathlib import Path

import chromadb
from chromadb.config import Settings as ChromaSettings
from chromadb.api.models.Collection import Collection

from app.config import settings
from app.core.logger import get_logger

logger = get_logger(__name__)


class VectorStore:
    """
    ChromaDB 向量存储管理器
    负责向量数据库的初始化、文档向量化和检索
    """
    
    _instance: Optional["VectorStore"] = None
    _client: Optional[chromadb.PersistentClient] = None
    _collection: Optional[Collection] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if VectorStore._client is not None:
            return
        self._initialize()
    
    def _initialize(self):
        """初始化 ChromaDB 客户端"""
        logger.info("正在初始化 ChromaDB...")
        
        try:
            # 确保持久化目录存在
            persist_dir = Path(settings.chroma_persist_dir)
            persist_dir.mkdir(parents=True, exist_ok=True)
            
            # 创建持久化客户端
            VectorStore._client = chromadb.PersistentClient(
                path=str(persist_dir),
                settings=ChromaSettings(
                    anonymized_telemetry=False,  # 禁用匿名遥测
                    allow_reset=True,  # 允许重置
                )
            )
            
            # 获取或创建 Collection
            if settings.chroma_auto_create_collection:
                VectorStore._collection = self._client.get_or_create_collection(
                    name=settings.chroma_collection_name,
                    metadata={"dimension": settings.embedding_dimension}
                )
            else:
                VectorStore._collection = self._client.get_collection(
                    name=settings.chroma_collection_name
                )
            
            logger.info(f"ChromaDB 初始化完成，Collection: {settings.chroma_collection_name}")
            
        except Exception as e:
            logger.error(f"ChromaDB 初始化失败: {str(e)}")
            raise
    
    @property
    def client(self) -> chromadb.PersistentClient:
        """获取 ChromaDB 客户端"""
        if VectorStore._client is None:
            self._initialize()
        return VectorStore._client
    
    @property
    def collection(self) -> Collection:
        """获取当前 Collection"""
        if VectorStore._collection is None:
            self._initialize()
        return VectorStore._collection
    
    def add_vectors(
        self,
        documents: List[str],
        embeddings: List[List[float]],
        ids: List[str],
        metadatas: List[Dict[str, Any]] = None
    ) -> bool:
        """
        添加向量到数据库
        
        Args:
            documents: 文档文本列表
            embeddings: 向量列表
            ids: 向量 ID 列表
            metadatas: 元数据列表
            
        Returns:
            是否成功
        """
        try:
            logger.info(f"正在添加 {len(documents)} 个向量到 ChromaDB...")
            
            self.collection.add(
                documents=documents,
                embeddings=embeddings,
                ids=ids,
                metadatas=metadatas
            )
            
            logger.info(f"成功添加 {len(documents)} 个向量")
            return True
            
        except Exception as e:
            logger.error(f"添加向量失败: {str(e)}")
            raise
    
    def search_vectors(
        self,
        query_embedding: List[float],
        n_results: int = None,
        where: Dict[str, Any] = None,
        where_document: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        检索最相似的向量
        
        Args:
            query_embedding: 查询向量
            n_results: 返回结果数量
            where: 元数据过滤条件
            where_document: 文档内容过滤条件
            
        Returns:
            检索结果，包含 ids, distances, documents, metadatas
        """
        try:
            if n_results is None:
                n_results = settings.retrieval_top_k
            
            logger.debug(f"正在检索向量，top_k={n_results}")
            
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=where,
                where_document=where_document,
                include=["documents", "metadatas", "distances"]
            )
            
            # 处理结果，过滤低于阈值的
            filtered_results = self._filter_by_threshold(results)
            
            logger.debug(f"检索完成，返回 {len(filtered_results.get('ids', [[]])[0])} 条结果")
            return filtered_results
            
        except Exception as e:
            logger.error(f"向量检索失败: {str(e)}")
            raise
    
    def _filter_by_threshold(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """根据相似度阈值过滤结果
        
        注意：embedding 模型启用了 L2 归一化，使用余弦相似度时：
        - 相似度 = 1 - distance / 2 （归一化后距离范围 [0, 2]）
        - 距离阈值 = 2 * (1 - similarity_threshold)
        """
        if not results or "distances" not in results:
            return results
        
        distances = results.get("distances", [[]])[0]
        threshold = settings.similarity_threshold
        
        # 归一化后的距离阈值: distance <= 2 * (1 - threshold)
        max_distance = 2 * (1 - threshold)
        
        # 计算通过阈值的结果索引
        valid_indices = [
            i for i, dist in enumerate(distances) 
            if dist <= max_distance
        ]
        
        if not valid_indices:
            logger.debug(f"没有通过相似度阈值 ({threshold}) 的结果")
            return {
                "ids": [[]],
                "distances": [[]],
                "documents": [[]],
                "metadatas": [[]]
            }
        
        # 过滤结果
        filtered = {}
        for key, value in results.items():
            if isinstance(value, list) and len(value) > 0:
                filtered[key] = [[value[0][i] for i in valid_indices]]
            else:
                filtered[key] = value
        
        return filtered
    
    def delete_vectors(self, ids: List[str]) -> bool:
        """
        删除指定 ID 的向量
        
        Args:
            ids: 要删除的向量 ID 列表
            
        Returns:
            是否成功
        """
        try:
            logger.info(f"正在删除 {len(ids)} 个向量...")
            self.collection.delete(ids=ids)
            logger.info(f"成功删除向量")
            return True
        except Exception as e:
            logger.error(f"删除向量失败: {str(e)}")
            raise
    
    def delete_by_document_id(self, document_id: int) -> bool:
        """
        根据文档 ID 删除所有关联的向量
        
        Args:
            document_id: 文档 ID
            
        Returns:
            是否成功
        """
        try:
            logger.info(f"正在删除文档 {document_id} 关联的向量...")
            self.collection.delete(
                where={"document_id": document_id}
            )
            logger.info(f"成功删除文档关联的向量")
            return True
        except Exception as e:
            logger.error(f"删除文档向量失败: {str(e)}")
            raise
    
    def reset(self) -> bool:
        """
        重置向量数据库
        警告：此操作会删除所有数据
        """
        try:
            logger.warning("正在重置向量数据库...")
            self.client.reset()
            
            # 重新创建 Collection
            VectorStore._collection = self.client.get_or_create_collection(
                name=settings.chroma_collection_name,
                metadata={"dimension": settings.embedding_dimension}
            )
            
            logger.warning("向量数据库已重置")
            return True
        except Exception as e:
            logger.error(f"重置向量数据库失败: {str(e)}")
            raise
    
    def get_collection_info(self) -> Dict[str, Any]:
        """
        获取 Collection 信息
        
        Returns:
            Collection 信息字典
        """
        try:
            collection = self.collection
            return {
                "name": collection.name,
                "count": collection.count(),
                "metadata": collection.metadata
            }
        except Exception as e:
            logger.error(f"获取 Collection 信息失败: {str(e)}")
            return {}
    
    def check_health(self) -> bool:
        """
        检查向量数据库健康状态
        
        Returns:
            是否健康
        """
        try:
            # 尝试获取 Collection 信息
            info = self.get_collection_info()
            return "name" in info
        except Exception as e:
            logger.error(f"向量数据库健康检查失败: {str(e)}")
            return False


# 全局向量存储实例
vector_store = VectorStore()


def get_vector_store() -> VectorStore:
    """获取向量存储实例"""
    return vector_store
