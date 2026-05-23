# -*- coding: utf-8 -*-
"""
向量化服务

本模块提供文本向量化服务，包括：
- Embedding模型加载与管理
- 批量向量化处理
- 向量缓存管理
- Chunk向量化入库
- Ollama 集成支持
"""

import asyncio
import hashlib
import time
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from app.common.exception import BusinessException, ErrorCode
from app.common.logging import logger
from app.schemas.embedding import (
    ChunkEmbeddingResult,
    ChunkEmbeddingResponse,
    EmbeddingResponse,
    SingleEmbeddingResponse,
)
from app.services.ollama_client import OllamaClientSync, get_ollama_client
from core.cache import EmbeddingCache, get_embedding_cache
from core.config import settings


class EmbeddingService:
    """
    向量化服务

    提供文本向量化的核心功能，支持 Ollama Qwen3-Embedding 模型和向量缓存。
    优先使用 Ollama 服务，降级使用 Mock 模型。
    """

    def __init__(self):
        """初始化向量化服务"""
        self._config = settings.embedding
        self._cache: Optional[EmbeddingCache] = None
        self._model = None
        self._model_type: Optional[str] = None  # "ollama" 或 "mock"
        self._initialized = False
        self._ollama_client: Optional[OllamaClientSync] = None

    @property
    def cache(self) -> EmbeddingCache:
        """获取缓存实例"""
        if self._cache is None:
            self._cache = get_embedding_cache()
        return self._cache

    @property
    def model_type(self) -> str:
        """
        获取当前模型类型

        Returns:
            "ollama" 或 "mock"
        """
        return self._model_type or "unknown"

    @property
    def is_ollama_available(self) -> bool:
        """
        检查 Ollama 是否可用

        Returns:
            Ollama 服务是否可用
        """
        if self._ollama_client is None:
            self._ollama_client = OllamaClientSync()
        return self._ollama_client.health_check()

    def _initialize_model(self) -> None:
        """初始化向量化模型"""
        if self._initialized:
            return

        try:
            model_name = self._config.model_name
            use_ollama = self._config.use_ollama
            fallback_to_mock = self._config.fallback_to_mock

            logger.info(
                f"初始化向量化模型",
                extra={
                    "model_name": model_name,
                    "use_ollama": use_ollama,
                    "fallback_to_mock": fallback_to_mock
                }
            )

            # 优先尝试使用 Ollama
            if use_ollama:
                ollama_client = OllamaClientSync()
                
                # 检查 Ollama 服务是否可用
                if ollama_client.health_check():
                    logger.info(
                        f"Ollama 服务可用，初始化 Ollama 客户端",
                        extra={"host": self._config.ollama_host}
                    )
                    self._ollama_client = ollama_client
                    self._model_type = "ollama"
                    
                    # 创建 Ollama 封装函数作为模型
                    self._model = self._create_ollama_model_wrapper()
                    self._initialized = True
                    logger.info(
                        f"向量化模型初始化成功",
                        extra={"model_type": "ollama", "model_name": model_name}
                    )
                    return
                else:
                    logger.warning(
                        f"Ollama 服务不可用",
                        extra={
                            "host": self._config.ollama_host,
                            "fallback_to_mock": fallback_to_mock
                        }
                    )
                    
                    if not fallback_to_mock:
                        raise BusinessException(
                            code=ErrorCode.INTERNAL_ERROR[0],
                            message=f"Ollama 服务不可用，且未启用降级到 Mock 模型"
                        )

            # 使用 Mock 模型
            logger.info(
                f"初始化 Mock 向量化模型（用于开发测试）",
                extra={"model_name": model_name}
            )
            self._model = self._create_mock_model()
            self._model_type = "mock"
            self._initialized = True

            logger.info(
                f"向量化模型初始化成功",
                extra={"model_type": self._model_type}
            )

        except BusinessException:
            raise
        except Exception as e:
            logger.error(f"向量化模型初始化失败: {str(e)}")
            raise BusinessException(
                code=ErrorCode.INTERNAL_ERROR[0],
                message=f"向量化模型初始化失败: {str(e)}"
            )

    def _create_ollama_model_wrapper(self) -> callable:
        """
        创建 Ollama 模型封装函数

        Returns:
            可调用的 embedding 函数
        """
        def ollama_encode(texts: List[str], normalize: bool = True) -> List[np.ndarray]:
            """
            Ollama 向量化封装

            Args:
                texts: 文本列表
                normalize: 是否归一化

            Returns:
                向量列表
            """
            if not texts:
                return []

            embeddings = []
            for text in texts:
                try:
                    # 确保 text 是字符串
                    if not isinstance(text, str):
                        text = str(text) if text is not None else ""
                    
                    if not text or not text.strip():
                        embeddings.append(np.zeros(self._config.dimension))
                        continue

                    # 调用 Ollama
                    vector = self._ollama_client.embed_single(text, normalize=normalize)
                    embeddings.append(vector)
                    
                except Exception as e:
                    logger.warning(
                        f"Ollama 向量化失败: {str(e)}, text={repr(text[:50])}",
                        extra={"error": str(e)}
                    )
                    embeddings.append(np.zeros(self._config.dimension))

            return embeddings

        return ollama_encode

    def _create_mock_model(self) -> callable:
        """
        创建模拟模型函数

        用于开发和测试，或当 Ollama 不可用时的降级方案。

        Returns:
            可调用的 embedding 函数
        """
        def mock_encode(texts: List[str], normalize: bool = True) -> List[np.ndarray]:
            """
            模拟向量化编码

            生成基于文本内容的伪向量，确保相同文本产生相同向量。

            Args:
                texts: 文本列表
                normalize: 是否归一化

            Returns:
                向量列表
            """
            embeddings = []
            for idx, text in enumerate(texts):
                try:
                    # 确保 text 是字符串
                    if not isinstance(text, str):
                        text = str(text) if text is not None else ""

                    if not text or not text.strip():
                        # 空文本返回零向量
                        vector = np.zeros(self._config.dimension)
                    else:
                        text_bytes = text.encode("utf-8")
                        text_hash = hashlib.md5(text_bytes).hexdigest()

                        # 生成向量（基于哈希值）
                        hex_chars = []
                        for i in range(0, min(len(text_hash) * 2, 2048), 2):
                            hex_pair = text_hash[i // 2 * 2:i // 2 * 2 + 2] if i // 2 * 2 < len(text_hash) else "00"
                            if len(hex_pair) == 2:
                                hex_chars.append(float(int(hex_pair, 16)) / 255.0)
                            else:
                                hex_chars.append(0.0)

                        vector = np.array(
                            hex_chars + [0.0] * max(0, self._config.dimension - len(hex_chars))
                        )

                    # 归一化
                    if normalize:
                        norm = np.linalg.norm(vector)
                        if norm > 0:
                            vector = vector / norm

                    embeddings.append(vector)
                except Exception as e:
                    logger.warning(
                        f"Mock 向量化失败: {str(e)}, text={repr(text[:50])}",
                        extra={"error": str(e)}
                    )
                    embeddings.append(np.zeros(self._config.dimension))

            return embeddings

        return mock_encode

    def encode(self, texts: List[str], normalize: bool = True) -> Tuple[List[np.ndarray], int]:
        """
        批量向量化

        Args:
            texts: 文本列表
            normalize: 是否归一化

        Returns:
            (向量列表, 缓存命中数量)
        """
        if not texts:
            return [], 0

        # 确保模型已初始化
        self._initialize_model()

        # 查询缓存
        cached_embeddings = []
        uncached_texts = []
        uncached_indices = []

        for i, text in enumerate(texts):
            cached = self._get_from_cache(text)
            if cached is not None:
                cached_embeddings.append((i, cached))
            else:
                uncached_texts.append(text)
                uncached_indices.append(i)

        # 计算未命中的向量
        if uncached_texts:
            uncached_embeddings = self._encode_batch(uncached_texts, normalize)

            # 写入缓存
            for text, embedding in zip(uncached_texts, uncached_embeddings):
                self._set_to_cache(text, embedding)
        else:
            uncached_embeddings = []

        # 合并结果
        all_embeddings = [None] * len(texts)
        for idx, embedding in cached_embeddings:
            all_embeddings[idx] = embedding
        for idx, embedding in zip(uncached_indices, uncached_embeddings):
            all_embeddings[idx] = embedding

        return all_embeddings, len(cached_embeddings)

    def _encode_batch(self, texts: List[str], normalize: bool = True) -> List[np.ndarray]:
        """
        批量编码（不涉及缓存）

        Args:
            texts: 文本列表
            normalize: 是否归一化

        Returns:
            向量列表
        """
        if not texts:
            return []

        # 确保模型已初始化
        self._initialize_model()

        if self._model is None:
            raise BusinessException(
                code=ErrorCode.INTERNAL_ERROR[0],
                message="向量化模型未正确初始化"
            )

        # 批量处理
        batch_size = self._config.batch_size
        all_embeddings = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batch_embeddings = self._model(batch, normalize=normalize)
            all_embeddings.extend(batch_embeddings)

        return all_embeddings

    def encode_single(self, text: str, normalize: bool = True) -> Tuple[np.ndarray, bool]:
        """
        单个文本向量化

        Args:
            text: 文本
            normalize: 是否归一化

        Returns:
            (向量, 是否来自缓存)
        """
        if not text:
            return np.zeros(self._config.dimension), False

        # 查询缓存
        cached = self._get_from_cache(text)
        if cached is not None:
            return cached, True

        # 向量化
        embeddings = self._encode_batch([text], normalize)
        embedding = embeddings[0] if embeddings else np.zeros(self._config.dimension)

        # 写入缓存
        self._set_to_cache(text, embedding)

        return embedding, False

    def _get_from_cache(self, text: str) -> Optional[np.ndarray]:
        """
        从缓存获取向量

        Args:
            text: 文本

        Returns:
            向量或None
        """
        try:
            cached_embedding = self.cache.get_doc_embedding(self._compute_hash(text))
            if cached_embedding is not None:
                return np.array(cached_embedding)
        except Exception as e:
            logger.warning(f"从缓存获取向量失败: {str(e)}")
        return None

    def _set_to_cache(self, text: str, embedding: np.ndarray) -> None:
        """
        设置向量到缓存

        Args:
            text: 文本
            embedding: 向量
        """
        try:
            text_hash = self._compute_hash(text)
            self.cache.set_doc_embedding(text_hash, embedding.tolist())
        except Exception as e:
            logger.warning(f"设置向量缓存失败: {str(e)}")

    def _compute_hash(self, text: str) -> str:
        """
        计算文本哈希

        Args:
            text: 文本

        Returns:
            哈希值
        """
        normalized = text.lower().strip()
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:32]

    def get_embedding_dimension(self) -> int:
        """
        获取向量维度

        Returns:
            向量维度
        """
        return self._config.dimension

    def get_model_name(self) -> str:
        """
        获取模型名称

        Returns:
            模型名称
        """
        return self._config.model_name

    def health_check(self) -> Dict[str, Any]:
        """
        健康检查

        检查 Ollama 服务和模型状态。

        Returns:
            健康检查结果字典
        """
        result = {
            "initialized": self._initialized,
            "model_type": self.model_type,
            "model_name": self._config.model_name,
            "ollama_available": False,
            "ollama_host": self._config.ollama_host,
            "use_ollama": self._config.use_ollama
        }

        # 检查 Ollama 服务
        if self._config.use_ollama:
            try:
                if self._ollama_client is None:
                    self._ollama_client = OllamaClientSync()
                result["ollama_available"] = self._ollama_client.health_check()
            except Exception as e:
                logger.warning(f"Ollama 健康检查异常: {str(e)}")
                result["ollama_available"] = False

        return result

    def get_model_info(self) -> Dict[str, Any]:
        """
        获取模型信息

        Returns:
            模型信息字典
        """
        return {
            "model_name": self._config.model_name,
            "model_type": self.model_type,
            "dimension": self._config.dimension,
            "batch_size": self._config.batch_size,
            "use_ollama": self._config.use_ollama,
            "ollama_host": self._config.ollama_host,
            "ollama_timeout": self._config.ollama_timeout,
            "fallback_to_mock": self._config.fallback_to_mock
        }


class ChunkEmbeddingService:
    """
    Chunk向量化服务

    负责将文档的Chunks向量化并存储到向量数据库。
    """

    def __init__(self):
        """初始化服务"""
        self._embedding_service = EmbeddingService()
        self._embedding_service._initialize_model()
        self._milvus_repo = None

    def _get_milvus_repo(self):
        """获取Milvus仓库实例"""
        if self._milvus_repo is None:
            from app.repositories.milvus_repository import MilvusRepository
            self._milvus_repo = MilvusRepository()
        return self._milvus_repo

    def embed_document_chunks(
        self,
        document_id: int,
        version_id: int,
        chunk_ids: Optional[List[int]] = None,
        use_cache: bool = True
    ) -> ChunkEmbeddingResponse:
        """
        将文档的Chunks向量化

        Args:
            document_id: 文档ID
            version_id: 版本ID
            chunk_ids: 指定Chunk ID列表，为空则处理全部
            use_cache: 是否使用缓存

        Returns:
            向量化结果
        """
        from app.models.chunk import DocumentChunk
        from core.database import SessionLocal

        start_time = time.time()
        db = SessionLocal()

        try:
            # 查询Chunks
            query = db.query(DocumentChunk).filter(
                DocumentChunk.document_id == document_id,
                DocumentChunk.version_id == version_id,
                DocumentChunk.status != 9  # 未删除
            )

            if chunk_ids:
                query = query.filter(DocumentChunk.id.in_(chunk_ids))

            chunks = query.all()

            if not chunks:
                return ChunkEmbeddingResponse(
                    document_id=document_id,
                    version_id=version_id,
                    total_chunks=0,
                    processed_chunks=0,
                    cached_count=0,
                    results=[],
                    processing_time_ms=int((time.time() - start_time) * 1000)
                )

            # 准备向量化
            texts_to_embed = []
            chunk_map = {}  # index -> (chunk, original_text)

            for i, chunk in enumerate(chunks):
                # 使用增强内容或原始内容
                text = chunk.enhanced_content if chunk.enhanced_content else chunk.content
                # 跳过空内容
                if not text:
                    text = ""
                if not text.strip():
                    logger.warning(
                        f"跳过空内容的Chunk",
                        extra={"chunk_id": chunk.id, "document_id": document_id, "content": repr(chunk.content), "enhanced": repr(chunk.enhanced_content)}
                    )
                    continue
                texts_to_embed.append(text)
                chunk_map[i] = (chunk, text)

            logger.info(
                f"准备向量化文本",
                extra={
                    "document_id": document_id,
                    "total_chunks": len(chunks),
                    "texts_to_embed_count": len(texts_to_embed),
                    "texts_sample": [t[:50] for t in texts_to_embed[:3]] if texts_to_embed else []
                }
            )

            if not texts_to_embed:
                logger.warning(
                    f"文档没有可向量化的Chunk内容",
                    extra={"document_id": document_id, "version_id": version_id}
                )
                return ChunkEmbeddingResponse(
                    document_id=document_id,
                    version_id=version_id,
                    total_chunks=len(chunks),
                    processed_chunks=0,
                    cached_count=0,
                    results=[],
                    processing_time_ms=int((time.time() - start_time) * 1000)
                )

            # 执行向量化
            try:
                embeddings, cached_count = self._embedding_service.encode(
                    texts_to_embed,
                    normalize=True
                )
                logger.info(
                    f"向量化执行成功",
                    extra={
                        "text_count": len(texts_to_embed),
                        "embedding_count": len(embeddings)
                    }
                )
            except Exception as encode_error:
                logger.error(f"向量化执行失败: {str(encode_error)}")
                raise

            # 存储到Milvus
            milvus_repo = self._get_milvus_repo()
            entities = []
            results = []
            processed_ids = []

            for i, (chunk, text) in chunk_map.items():
                embedding = embeddings[i]

                # 调试日志
                logger.info(
                    f"准备向量化Chunk",
                    extra={
                        "chunk_id": chunk.id,
                        "chunk_chunk_id": chunk.chunk_id,
                        "text_length": len(text),
                        "text_preview": text[:100] if text else "EMPTY"
                    }
                )

                # 构建实体 - Milvus 的 chunk_id 字段用整数主键
                entity = {
                    "document_id": document_id,
                    "version_id": version_id,
                    "chunk_id": chunk.id,  # 数据库主键，整数
                    "title_path": chunk.title_path or "",
                    "page_start": chunk.page_start or 0,
                    "page_end": chunk.page_end or 0,
                    "chunk_type": chunk.chunk_type,
                    "embedding": embedding.tolist(),
                    "quality_score": chunk.quality_score or 0.0
                }
                entities.append(entity)

                # 生成结果 - chunk_id 必须是整数（数据库主键 id），不是字符串 chunk_id
                result = ChunkEmbeddingResult(
                    chunk_id=chunk.id,  # 数据库主键，整数
                    vector_id=0,  # Milvus会自动生成
                    embedding=embedding.tolist(),
                    cached=False
                )
                results.append(result)
                processed_ids.append(chunk.id)  # 使用整数主键

            # 批量插入Milvus
            if entities:
                try:
                    vector_ids = milvus_repo.insert("document_chunks", entities)
                    
                    # 插入后确保数据可被搜索 - 调用 reload 重新加载集合
                    milvus_repo.ensure_collection_ready_for_search("document_chunks")
                    
                    # 更新结果中的vector_id
                    for i, result in enumerate(results):
                        if i < len(vector_ids):
                            result.vector_id = vector_ids[i]

                    logger.info(
                        f"Milvus插入成功",
                        extra={
                            "document_id": document_id,
                            "version_id": version_id,
                            "inserted_count": len(vector_ids),
                            "collection_reloaded": True
                        }
                    )
                except Exception as e:
                    logger.error(f"Milvus插入失败: {str(e)}")
                    # 记录详细错误，但继续处理
                    # 对于未成功插入的chunk，保留status=0状态，允许重试

                    # 尝试逐条插入以挽救部分数据
                    failed_indices = []
                    for i, entity in enumerate(entities):
                        try:
                            single_id = milvus_repo.insert("document_chunks", [entity])
                            if i < len(results):
                                results[i].vector_id = single_id[0] if single_id else 0
                        except Exception as single_error:
                            logger.warning(
                                f"单条Milvus插入失败",
                                extra={
                                    "chunk_index": i,
                                    "error": str(single_error)
                                }
                            )
                            failed_indices.append(i)
                            failed_indices.append(results[i].chunk_id if i < len(results) else None)
                    
                    # 尝试重新加载集合
                    try:
                        milvus_repo.ensure_collection_ready_for_search("document_chunks")
                    except Exception:
                        pass

                    logger.info(
                        f"Milvus批量插入完成，失败数量: {len(failed_indices)}",
                        extra={
                            "document_id": document_id,
                            "failed_indices": failed_indices
                        }
                    )

            # 更新数据库状态
            for chunk in chunks:
                chunk_index = chunks.index(chunk)
                if chunk_index < len(results):
                    if results[chunk_index].vector_id and results[chunk_index].vector_id > 0:
                        chunk.status = 1  # 已向量化
                        chunk.vector_id = results[chunk_index].vector_id
                    else:
                        chunk.status = 0  # 待向量化
                        chunk.vector_id = None
                else:
                    chunk.status = 0  # 待向量化

            db.commit()

            processing_time = int((time.time() - start_time) * 1000)

            logger.info(
                f"文档Chunk向量化完成",
                extra={
                    "document_id": document_id,
                    "version_id": version_id,
                    "total_chunks": len(chunks),
                    "cached_count": cached_count,
                    "processing_time_ms": processing_time
                }
            )

            return ChunkEmbeddingResponse(
                document_id=document_id,
                version_id=version_id,
                total_chunks=len(chunks),
                processed_chunks=len(chunks),
                cached_count=cached_count,
                results=results,
                processing_time_ms=processing_time
            )

        except Exception as e:
            db.rollback()
            logger.error(f"文档Chunk向量化失败: {str(e)}")
            raise BusinessException(
                code=ErrorCode.EMBEDDING_FAILED[0],
                message=f"文档Chunk向量化失败: {str(e)}"
            )
        finally:
            db.close()

    def delete_document_vectors(
        self,
        document_id: int,
        version_id: Optional[int] = None,
        chunk_ids: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """
        删除文档的向量

        Args:
            document_id: 文档ID
            version_id: 版本ID
            chunk_ids: 指定Chunk ID列表

        Returns:
            删除结果
        """
        from app.models.chunk import DocumentChunk
        from core.database import SessionLocal

        start_time = time.time()
        db = SessionLocal()

        try:
            # 查询要删除的Chunks
            query = db.query(DocumentChunk).filter(
                DocumentChunk.document_id == document_id,
                DocumentChunk.status.in_([1])  # 已向量化
            )

            if version_id:
                query = query.filter(DocumentChunk.version_id == version_id)

            if chunk_ids:
                query = query.filter(DocumentChunk.id.in_(chunk_ids))

            chunks = query.all()

            if not chunks:
                return {
                    "document_id": document_id,
                    "deleted_count": 0,
                    "cache_cleared": 0,
                    "processing_time_ms": int((time.time() - start_time) * 1000)
                }

            # 从Milvus删除
            milvus_repo = self._get_milvus_repo()
            chunk_id_list = [c.id for c in chunks]

            try:
                milvus_repo.delete_by_chunk_ids("document_chunks", chunk_id_list)
            except Exception as e:
                logger.warning(f"Milvus删除失败: {str(e)}")

            # 更新数据库状态
            for chunk in chunks:
                chunk.status = 0  # 待向量化
                chunk.vector_id = None

            db.commit()

            processing_time = int((time.time() - start_time) * 1000)

            logger.info(
                f"文档向量删除完成",
                extra={
                    "document_id": document_id,
                    "deleted_count": len(chunks),
                    "processing_time_ms": processing_time
                }
            )

            return {
                "document_id": document_id,
                "deleted_count": len(chunks),
                "cache_cleared": 0,
                "processing_time_ms": processing_time
            }

        except Exception as e:
            db.rollback()
            logger.error(f"删除文档向量失败: {str(e)}")
            raise BusinessException(
                code=ErrorCode.OPERATION_FAILED[0],
                message=f"删除文档向量失败: {str(e)}"
            )
        finally:
            db.close()


# 全局服务实例
_embedding_service: Optional[EmbeddingService] = None
_chunk_embedding_service: Optional[ChunkEmbeddingService] = None


def get_embedding_service() -> EmbeddingService:
    """获取向量化服务实例"""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service


def get_chunk_embedding_service() -> ChunkEmbeddingService:
    """获取Chunk向量化服务实例"""
    global _chunk_embedding_service
    if _chunk_embedding_service is None:
        _chunk_embedding_service = ChunkEmbeddingService()
    return _chunk_embedding_service
