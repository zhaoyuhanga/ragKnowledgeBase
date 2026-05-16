"""
RAG 问答系统 - Milvus 向量数据库模块
向量存储和检索操作
"""

from typing import List, Dict, Optional, Any
import numpy as np

from pymilvus import (
    connections, Collection, FieldSchema, CollectionSchema,
    DataType, utility
)

from app.config import settings
from app.core.logger import get_logger
from app.core.runtime_config import runtime_config

logger = get_logger(__name__)


class VectorStore:
    """
    Milvus 向量存储管理器
    负责向量数据库的初始化、文档向量化和检索
    """

    _instance: Optional["VectorStore"] = None
    _connection: Optional[str] = None
    _collection: Optional[Collection] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if VectorStore._connection is None:
            self._initialize()

    def _initialize(self):
        """初始化 Milvus 连接"""
        logger.info(f"正在连接 Milvus ({settings.milvus_host}:{settings.milvus_port})...")

        try:
            alias = "default"

            if settings.milvus_user and settings.milvus_password:
                connections.connect(
                    alias=alias,
                    host=settings.milvus_host,
                    port=settings.milvus_port,
                    user=settings.milvus_user,
                    password=settings.milvus_password
                )
            else:
                connections.connect(
                    alias=alias,
                    host=settings.milvus_host,
                    port=settings.milvus_port
                )

            VectorStore._connection = alias
            logger.info("Milvus 连接成功")

            self._ensure_collection()

        except Exception as e:
            logger.error(f"Milvus 连接失败: {str(e)}")
            raise

    def _ensure_collection(self):
        """确保 Collection 存在"""
        collection_name = settings.milvus_collection_name

        if utility.has_collection(collection_name):
            VectorStore._collection = Collection(collection_name)
            VectorStore._collection.load()
            logger.info(f"已加载 Collection: {collection_name}")
        else:
            self._create_collection(collection_name)

    def _create_collection(self, collection_name: str):
        """创建 Collection"""
        logger.info(f"正在创建 Collection: {collection_name}")

        dim = settings.embedding_dimension

        fields = [
            FieldSchema(name="id", dtype=DataType.VARCHAR, max_length=256, is_primary=True, auto_id=False),
            FieldSchema(name="document_id", dtype=DataType.INT64),
            FieldSchema(name="chunk_index", dtype=DataType.INT64),
            FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=65535),
            FieldSchema(name="filename", dtype=DataType.VARCHAR, max_length=512),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=dim)
        ]

        schema = CollectionSchema(
            fields=fields,
            description="Knowledge base vector collection"
        )

        collection = Collection(name=collection_name, schema=schema)

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
        VectorStore._collection = collection
        logger.info(f"Collection 创建成功: {collection_name}")

    @property
    def collection(self) -> Collection:
        """获取当前 Collection"""
        if VectorStore._collection is None:
            self._ensure_collection()
        return VectorStore._collection

    def add_vectors(
        self,
        documents: List[str],
        embeddings: List[List[float]],
        ids: List[str],
        metadatas: List[Dict[str, Any]] = None
    ) -> bool:
        """添加向量到数据库"""
        try:
            logger.info(f"正在添加 {len(documents)} 个向量到 Milvus...")

            if metadatas is None:
                metadatas = [{} for _ in range(len(documents))]

            doc_ids_list = []
            doc_id_list = []
            chunk_idx_list = []
            content_list = []
            filename_list = []
            embedding_list = []

            for i, doc_id in enumerate(ids):
                metadata = metadatas[i] if i < len(metadatas) else {}
                doc_ids_list.append(doc_id)
                doc_id_list.append(metadata.get("document_id", 0))
                chunk_idx_list.append(metadata.get("chunk_index", 0))
                content_list.append(documents[i])
                filename_list.append(metadata.get("filename", ""))
                embedding_list.append(embeddings[i])

            data = [
                doc_ids_list,
                doc_id_list,
                chunk_idx_list,
                content_list,
                filename_list,
                embedding_list
            ]

            self.collection.insert(data)
            self.collection.flush()

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
        """检索最相似的向量"""
        try:
            if n_results is None:
                n_results = runtime_config.retrieval_top_k

            logger.debug(f"正在检索向量，top_k={n_results}")

            search_params = {
                "metric_type": settings.milvus_metric_type,
                "params": {"nprobe": 16}
            }

            expr = None
            if where:
                if "document_id" in where:
                    if isinstance(where["document_id"], dict):
                        if "$in" in where["document_id"]:
                            doc_ids = where["document_id"]["$in"]
                            expr = f"document_id in {doc_ids}"
                        elif "$eq" in where["document_id"]:
                            expr = f"document_id == {where['document_id']['$eq']}"
                    else:
                        expr = f"document_id == {where['document_id']}"

            enable_mmr = runtime_config.enable_mmr

            if enable_mmr and n_results > 1:
                raw_limit = min(n_results * 3, 100)
            else:
                raw_limit = n_results

            results = self.collection.search(
                data=[query_embedding],
                anns_field="embedding",
                param=search_params,
                limit=raw_limit,
                expr=expr,
                output_fields=["id", "document_id", "chunk_index", "content", "filename"]
            )

            search_results = results[0] if results else []

            processed_results = {
                "ids": [[]],
                "distances": [[]],
                "documents": [[]],
                "metadatas": [[]]
            }

            if search_results:
                if enable_mmr and n_results > 1:
                    reranked = self._mmr_rerank(search_results)
                else:
                    reranked = search_results

                ids_list = []
                distances_list = []
                docs_list = []
                metadatas_list = []

                for hit in reranked:
                    ids_list.append(hit.id)
                    distances_list.append(hit.distance)
                    content = hit.get("content") or ""
                    docs_list.append(content)
                    metadata = {
                        "document_id": hit.get("document_id"),
                        "chunk_index": hit.get("chunk_index"),
                        "filename": hit.get("filename")
                    }
                    metadatas_list.append(metadata)

                processed_results = {
                    "ids": [ids_list],
                    "distances": [distances_list],
                    "documents": [docs_list],
                    "metadatas": [metadatas_list]
                }

            filtered_results = self._filter_by_threshold(processed_results)

            logger.debug(f"检索完成，返回 {len(filtered_results.get('ids', [[]])[0])} 条结果")
            return filtered_results

        except Exception as e:
            logger.error(f"向量检索失败: {str(e)}")
            raise

    def _mmr_rerank(
        self,
        results: list,
        fetch_k: int = None,
        lambda_mult: float = None
    ) -> list:
        """
        Max Marginal Relevance (MMR) 重排序
        在相关性和多样性之间取得平衡，减少检索结果中的冗余

        MMR = argmax( relevance - lambda * diversity )
        diversity = max( similarity(selected_doc, candidate_doc) )
        """
        if not results:
            return results

        fetch_k = fetch_k or min(len(results), 100)
        lambda_mult = lambda_mult if lambda_mult is not None else runtime_config.mmr_diversity

        selected = []
        candidates = results[:fetch_k]

        while len(selected) < len(results):
            mmr_score = -float('inf')
            mmr_idx = -1
            mmr_item = None

            for i, candidate in enumerate(candidates):
                if candidate in selected:
                    continue

                rel = candidate.distance

                div = 0.0
                if selected:
                    cand_vec = self._get_hit_embedding(candidate)
                    if cand_vec is not None:
                        cand_vec = np.array(cand_vec)
                        for sel in selected:
                            sel_vec = self._get_hit_embedding(sel)
                            if sel_vec is not None:
                                sel_vec = np.array(sel_vec)
                                sim = float(np.dot(sel_vec, cand_vec) / (np.linalg.norm(sel_vec) * np.linalg.norm(cand_vec) + 1e-9))
                                div = max(div, sim)

                score = rel - lambda_mult * div
                if score > mmr_score:
                    mmr_score = score
                    mmr_idx = i
                    mmr_item = candidate

            if mmr_item is not None:
                selected.append(mmr_item)
                candidates.remove(mmr_item)
            else:
                break

            if len(selected) >= len(results):
                break

        return selected

    def _get_hit_embedding(self, hit) -> Optional[List[float]]:
        """从搜索结果中获取 embedding 向量"""
        try:
            if hasattr(hit, 'entity') and hasattr(hit.entity, 'embedding'):
                return hit.entity.get('embedding')
            if hasattr(hit, 'fields') and 'embedding' in hit.fields:
                return hit.get('embedding')
            return None
        except Exception:
            return None

    def _filter_by_threshold(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """根据相似度阈值过滤结果"""
        if not results or "distances" not in results:
            return results

        distances = results.get("distances", [[]])[0]
        threshold = runtime_config.similarity_threshold

        valid_indices = [
            i for i, dist in enumerate(distances)
            if dist >= threshold
        ]

        if not valid_indices:
            logger.debug(f"没有通过相似度阈值 ({threshold}) 的结果")
            return {
                "ids": [[]],
                "distances": [[]],
                "documents": [[]],
                "metadatas": [[]]
            }

        filtered = {}
        for key, value in results.items():
            if isinstance(value, list) and len(value) > 0 and len(value[0]) > 0:
                filtered[key] = [[value[0][i] for i in valid_indices]]
            else:
                filtered[key] = value

        return filtered

    def delete_vectors(self, ids: List[str]) -> bool:
        """删除指定 ID 的向量"""
        try:
            logger.info(f"正在删除 {len(ids)} 个向量...")

            for vector_id in ids:
                expr = f'id == "{vector_id}"'
                self.collection.delete(expr)

            self.collection.flush()
            logger.info(f"成功删除向量")
            return True
        except Exception as e:
            logger.error(f"删除向量失败: {str(e)}")
            raise

    def delete_by_document_id(self, document_id: int) -> bool:
        """根据文档 ID 删除所有关联的向量"""
        try:
            logger.info(f"正在删除文档 {document_id} 关联的向量...")

            expr = f"document_id == {document_id}"
            self.collection.delete(expr)
            self.collection.flush()

            logger.info(f"成功删除文档关联的向量")
            return True
        except Exception as e:
            logger.error(f"删除文档向量失败: {str(e)}")
            raise

    def reset(self) -> bool:
        """重置向量数据库"""
        try:
            logger.warning("正在重置向量数据库...")

            collection_name = settings.milvus_collection_name

            if utility.has_collection(collection_name):
                utility.drop_collection(collection_name)

            self._create_collection(collection_name)

            logger.warning("向量数据库已重置")
            return True
        except Exception as e:
            logger.error(f"重置向量数据库失败: {str(e)}")
            raise

    def get_collection_info(self) -> Dict[str, Any]:
        """获取 Collection 信息"""
        try:
            collection = self.collection
            stats = collection.num_entities
            return {
                "name": collection.name,
                "count": stats,
                "schema": collection.schema
            }
        except Exception as e:
            logger.error(f"获取 Collection 信息失败: {str(e)}")
            return {}

    def check_health(self) -> bool:
        """检查向量数据库健康状态"""
        try:
            info = self.get_collection_info()
            return "name" in info and info["name"] is not None
        except Exception as e:
            logger.error(f"向量数据库健康检查失败: {str(e)}")
            return False


vector_store = VectorStore()


def get_vector_store() -> VectorStore:
    """获取向量存储实例"""
    return vector_store
