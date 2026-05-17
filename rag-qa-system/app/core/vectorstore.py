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
            # AI 生成相关字段
            FieldSchema(name="source_type", dtype=DataType.VARCHAR, max_length=20),
            FieldSchema(name="generated_from_question", dtype=DataType.VARCHAR, max_length=65535),
            FieldSchema(name="generated_at", dtype=DataType.VARCHAR, max_length=64),
            FieldSchema(name="llm_model", dtype=DataType.VARCHAR, max_length=100),
            FieldSchema(name="llm_provider", dtype=DataType.VARCHAR, max_length=50),
            # 向量字段
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=dim)
        ]

        schema = CollectionSchema(
            fields=fields,
            description="Knowledge base vector collection",
            enable_dynamic_field=True  # 支持动态字段
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
        """添加向量到数据库
        
        Args:
            documents: 文档内容列表
            embeddings: 向量列表
            ids: ID列表
            metadatas: 元数据列表，支持以下字段:
                - document_id: 文档ID
                - chunk_index: 块序号
                - filename: 文件名
                - source_type: 来源类型 (local/ai_generated)
                - generated_from_question: AI生成时的原始问题
                - generated_at: AI生成时间
                - llm_model: LLM模型
                - llm_provider: LLM提供商
        """
        try:
            logger.info(f"正在添加 {len(documents)} 个向量到 Milvus...")

            if metadatas is None:
                metadatas = [{} for _ in range(len(documents))]

            # 获取 collection 的字段列表
            schema_fields = {field.name for field in self.collection.schema.fields}
            logger.debug(f"Collection 字段: {schema_fields}")

            # 构建数据列表，只包含 collection 中存在的字段
            data_dict = {}
            
            # 基础字段
            if "id" in schema_fields:
                data_dict["id"] = ids
            if "document_id" in schema_fields:
                data_dict["document_id"] = [metadatas[i].get("document_id", 0) if i < len(metadatas) else 0 for i in range(len(documents))]
            if "chunk_index" in schema_fields:
                data_dict["chunk_index"] = [metadatas[i].get("chunk_index", j) if i < len(metadatas) else j for i, j in enumerate(range(len(documents)))]
            if "content" in schema_fields:
                data_dict["content"] = documents
            if "filename" in schema_fields:
                data_dict["filename"] = [metadatas[i].get("filename", "") if i < len(metadatas) else "" for i in range(len(documents))]
            
            # AI 生成相关字段（可选，兼容旧 schema）
            if "source_type" in schema_fields:
                data_dict["source_type"] = [metadatas[i].get("source_type", "local") if i < len(metadatas) else "local" for i in range(len(documents))]
            if "generated_from_question" in schema_fields:
                data_dict["generated_from_question"] = [metadatas[i].get("generated_from_question", "") if i < len(metadatas) else "" for i in range(len(documents))]
            if "generated_at" in schema_fields:
                data_dict["generated_at"] = [metadatas[i].get("generated_at", "") if i < len(metadatas) else "" for i in range(len(documents))]
            if "llm_model" in schema_fields:
                data_dict["llm_model"] = [metadatas[i].get("llm_model", "") if i < len(metadatas) else "" for i in range(len(documents))]
            if "llm_provider" in schema_fields:
                data_dict["llm_provider"] = [metadatas[i].get("llm_provider", "") if i < len(metadatas) else "" for i in range(len(documents))]
            
            # 向量字段
            if "embedding" in schema_fields:
                data_dict["embedding"] = embeddings

            # 按照 schema 定义的顺序构建数据
            data_list = []
            field_names = []
            for field in self.collection.schema.fields:
                if field.name in data_dict:
                    data_list.append(data_dict[field.name])
                    field_names.append(field.name)
            
            logger.debug(f"插入数据包含 {len(data_list)} 个字段: {field_names}")

            self.collection.insert(data_list)
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
        where_document: Dict[str, Any] = None,
        source_type: str = None
    ) -> Dict[str, Any]:
        """检索最相似的向量
        
        Args:
            query_embedding: 查询向量
            n_results: 返回数量
            where: 过滤条件
            where_document: 文档过滤条件
            source_type: 来源类型过滤: local(本地导入) | ai_generated(AI生成) | None(全部)
        """
        try:
            if n_results is None:
                n_results = runtime_config.retrieval_top_k

            schema_fields = {field.name for field in self.collection.schema.fields}
            logger.debug(f"正在检索向量，top_k={n_results}, source_type={source_type}, schema_fields={schema_fields}")

            search_params = {
                "metric_type": settings.milvus_metric_type,
                "params": {"nprobe": 16}
            }

            expr = None
            
            # 处理 document_id 过滤
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
            
            # 处理 source_type 过滤（仅当字段存在时）
            if source_type and source_type != "all":
                if "source_type" in schema_fields:
                    source_expr = f'source_type == "{source_type}"'
                    if expr:
                        expr = f"({expr}) and {source_expr}"
                    else:
                        expr = source_expr
                    logger.debug(f"使用 source_type 过滤: {source_expr}")
                else:
                    logger.warning(f"source_type 字段不存在于 schema，跳过过滤")
            
            logger.debug(f"最终查询表达式: {expr}")

            enable_mmr = runtime_config.enable_mmr

            if enable_mmr and n_results > 1:
                raw_limit = min(n_results * 3, 100)
            else:
                raw_limit = n_results

            # 动态获取 output_fields
            output_fields = ["id", "document_id", "chunk_index", "content", "filename"]
            if "source_type" in schema_fields:
                output_fields.extend(["source_type", "generated_from_question", "generated_at", "llm_model", "llm_provider"])

            results = self.collection.search(
                data=[query_embedding],
                anns_field="embedding",
                param=search_params,
                limit=raw_limit,
                expr=expr,
                output_fields=output_fields
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
                    content = hit.get("content") if hasattr(hit, 'get') else getattr(hit, 'entity', {}).get('content', '') or ""
                    docs_list.append(content)
                    
                    # 动态构建 metadata
                    metadata = {
                        "document_id": hit.get("document_id") if hasattr(hit, 'get') else getattr(hit, 'entity', {}).get('document_id'),
                        "chunk_index": hit.get("chunk_index") if hasattr(hit, 'get') else getattr(hit, 'entity', {}).get('chunk_index'),
                        "filename": hit.get("filename") if hasattr(hit, 'get') else getattr(hit, 'entity', {}).get('filename', ''),
                    }
                    
                    # AI 生成相关字段（仅当存在时添加）
                    if "source_type" in schema_fields:
                        metadata["source_type"] = hit.get("source_type") if hasattr(hit, 'get') else getattr(hit, 'entity', {}).get('source_type', "local") or "local"
                        metadata["generated_from_question"] = hit.get("generated_from_question") if hasattr(hit, 'get') else getattr(hit, 'entity', {}).get('generated_from_question')
                        metadata["generated_at"] = hit.get("generated_at") if hasattr(hit, 'get') else getattr(hit, 'entity', {}).get('generated_at')
                        metadata["llm_model"] = hit.get("llm_model") if hasattr(hit, 'get') else getattr(hit, 'entity', {}).get('llm_model')
                        metadata["llm_provider"] = hit.get("llm_provider") if hasattr(hit, 'get') else getattr(hit, 'entity', {}).get('llm_provider')
                    else:
                        metadata["source_type"] = "local"
                    
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
            if hasattr(hit, 'get'):
                return hit.get('embedding')
            if hasattr(hit, 'fields') and 'embedding' in hit.fields:
                return getattr(hit, 'embedding', None)
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
