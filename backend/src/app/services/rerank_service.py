# -*- coding: utf-8 -*-
"""
重排序服务（增强版）

本模块提供增强的重排序（Rerank）功能，包括：
- Ollama Cross-Encoder 集成
- 模型降级机制
- Cross-Encoder 相关性评分
- 基于相关性的结果重排序
- 候选Chunk扩展

所有代码注释使用中文，所有日志输出中文。
"""

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from app.common.logging import logger
from core.config import settings


@dataclass
class RerankResult:
    """重排序结果"""
    chunk_id: int
    document_id: int
    version_id: int
    title_path: Optional[str]
    page_start: Optional[int]
    page_end: Optional[int]
    content: str
    chunk_type: str
    original_rank: int
    rerank_score: float
    rerank_rank: int
    rerank_model: str = "mock"


@dataclass
class RerankConfig:
    """重排序配置"""
    use_ollama: bool = True  # 是否使用 Ollama
    fallback_to_mock: bool = True  # Ollama 不可用时降级
    rerank_model: str = "cross-encoder"  # 重排序模型
    min_score: float = 0.0  # 最低分数阈值
    max_results: int = 20  # 最大返回结果数


class CrossEncoderReranker:
    """
    Cross-Encoder 重排序器

    支持多种重排序方式：
    1. Ollama Cross-Encoder（优先）
    2. Mock 评分（降级方案）
    """

    def __init__(self, config: Optional[RerankConfig] = None):
        """
        初始化重排序器

        Args:
            config: 重排序配置
        """
        self._config = config or RerankConfig()
        self._ollama_client = None
        self._mock_enabled = True
        self._initialized = False

    def _initialize(self) -> None:
        """初始化模型"""
        if self._initialized:
            return

        if self._config.use_ollama:
            try:
                from app.services.ollama_client import get_ollama_rerank_client

                self._ollama_client = get_ollama_rerank_client()

                # 检查 Ollama 是否可用
                if self._ollama_client.health_check():
                    self._mock_enabled = False
                    logger.info(
                        "Cross-Encoder 使用 Ollama Rerank",
                        extra={"model": self._config.rerank_model}
                    )
                else:
                    if self._config.fallback_to_mock:
                        self._mock_enabled = True
                        logger.warning("Ollama Rerank 不可用，降级到 Mock 评分")
                    else:
                        raise RuntimeError("Ollama Rerank 不可用")
            except Exception as e:
                if self._config.fallback_to_mock:
                    self._mock_enabled = True
                    logger.warning(f"初始化 Ollama Rerank 失败: {str(e)}，使用 Mock 评分")
                else:
                    raise
        else:
            self._mock_enabled = True
            logger.info("Cross-Encoder 使用 Mock 评分")

        self._initialized = True

    def score(self, query: str, documents: List[str]) -> List[float]:
        """
        计算(query, document)对的相关性分数

        Args:
            query: 查询文本
            documents: 文档列表

        Returns:
            相关性分数列表
        """
        self._initialize()

        if not documents:
            return []

        if self._mock_enabled or self._ollama_client is None:
            return self._mock_score(query, documents)
        else:
            try:
                result = self._ollama_client.rerank(
                    query=query,
                    documents=documents,
                    top_n=len(documents),
                    return_documents=False
                )

                # 提取分数
                scores = [0.0] * len(documents)
                for item in result.get("results", []):
                    idx = item.get("index", 0)
                    if idx < len(scores):
                        scores[idx] = item.get("relevance_score", 0.0)

                return scores

            except Exception as e:
                logger.warning(f"Ollama Rerank 失败: {str(e)}，使用 Mock 评分")
                return self._mock_score(query, documents)

    def _mock_score(self, query: str, documents: List[str]) -> List[float]:
        """
        模拟相关性评分

        使用简单的文本重叠计算相关性分数。

        Args:
            query: 查询文本
            documents: 文档列表

        Returns:
            相关性分数列表
        """
        scores = []
        query_terms = set(query.lower().split())

        for doc in documents:
            if not doc:
                scores.append(0.0)
                continue

            doc_terms = set(doc.lower().split())
            if not query_terms:
                scores.append(0.0)
                continue

            # 计算 Jaccard 相似度
            intersection = len(query_terms & doc_terms)
            union = len(query_terms | doc_terms)
            jaccard = intersection / union if union > 0 else 0.0

            # 计算查询覆盖率
            query_count = sum(1 for term in query_terms if term in doc.lower())
            coverage = query_count / len(query_terms)

            # 综合评分
            score = 0.6 * jaccard + 0.4 * coverage
            scores.append(score)

        return scores

    @property
    def model_name(self) -> str:
        """获取使用的模型名称"""
        if self._mock_enabled:
            return "mock"
        return self._config.rerank_model


class RerankService:
    """
    重排序服务

    提供检索结果的重排序功能：
    1. Cross-Encoder 相关性评分
    2. Ollama Cross-Encoder 集成
    3. 模型降级机制
    4. 结果重排序
    5. 邻接 Chunk 扩展
    6. 同表格/图表关联扩展
    """

    def __init__(self, config: Optional[RerankConfig] = None):
        """
        初始化服务

        Args:
            config: 重排序配置
        """
        self._reranker: Optional[CrossEncoderReranker] = None
        self._config = config or RerankConfig()
        self._service_config = settings.retrieval

    @property
    def reranker(self) -> CrossEncoderReranker:
        """获取重排序器"""
        if self._reranker is None:
            self._reranker = CrossEncoderReranker(self._config)
        return self._reranker

    def rerank(
        self,
        query: str,
        candidates: List[Dict[str, Any]],
        top_k: Optional[int] = None,
        min_score: Optional[float] = None
    ) -> List[RerankResult]:
        """
        重排序

        对候选 Chunk 进行 Cross-Encoder 相关性评分并重排序。

        Args:
            query: 查询文本
            candidates: 候选 Chunk 列表
            top_k: 返回数量，默认使用配置值
            min_score: 最低分数阈值，默认使用配置值

        Returns:
            重排序后的结果列表
        """
        start_time = time.time()
        trace_id = f"rerank_{int(time.time() * 1000)}"

        if not candidates:
            logger.info(
                "重排序跳过：候选列表为空",
                extra={"traceId": trace_id, "query": query[:50]}
            )
            return []

        try:
            # 1. 提取文档内容
            documents = [c.get("content", "") or "" for c in candidates]

            # 2. 计算相关性分数
            scores = self.reranker.score(query, documents)

            # 3. 构建带分数的结果
            scored_results = []
            for i, candidate in enumerate(candidates):
                result = RerankResult(
                    chunk_id=candidate.get("chunk_id", 0),
                    document_id=candidate.get("document_id", 0),
                    version_id=candidate.get("version_id", 0),
                    title_path=candidate.get("title_path"),
                    page_start=candidate.get("page_start"),
                    page_end=candidate.get("page_end"),
                    content=candidate.get("content", ""),
                    chunk_type=candidate.get("chunk_type", "paragraph"),
                    original_rank=i + 1,
                    rerank_score=scores[i] if i < len(scores) else 0.0,
                    rerank_rank=0,
                    rerank_model=self.reranker.model_name
                )
                scored_results.append(result)

            # 4. 按相关性分数排序
            scored_results.sort(key=lambda x: x.rerank_score, reverse=True)

            # 5. 更新排名
            for rank, result in enumerate(scored_results):
                result.rerank_rank = rank + 1

            # 6. 过滤低分结果
            effective_min_score = min_score if min_score is not None else self._config.min_score
            if effective_min_score > 0:
                scored_results = [r for r in scored_results if r.rerank_score >= effective_min_score]

            # 7. 限制返回数量
            effective_top_k = top_k if top_k is not None else self._service_config.rerank_top_k
            scored_results = scored_results[:effective_top_k]

            rerank_time_ms = int((time.time() - start_time) * 1000)

            logger.info(
                "重排序完成",
                extra={
                    "traceId": trace_id,
                    "method": "rerank",
                    "query": query[:100],
                    "candidate_count": len(candidates),
                    "result_count": len(scored_results),
                    "model": self.reranker.model_name,
                    "rerank_time_ms": rerank_time_ms,
                    "costMs": rerank_time_ms
                }
            )

            return scored_results

        except Exception as e:
            rerank_time_ms = int((time.time() - start_time) * 1000)
            logger.error(
                f"重排序失败: {str(e)}",
                extra={
                    "traceId": trace_id,
                    "query": query[:100],
                    "error": str(e),
                    "costMs": rerank_time_ms
                }
            )

            # 出错时返回原始排序
            return self._fallback_rerank(candidates, top_k)

    def _fallback_rerank(
        self,
        candidates: List[Dict[str, Any]],
        top_k: Optional[int] = None
    ) -> List[RerankResult]:
        """
        降级重排序

        当重排序失败时，使用原始顺序。

        Args:
            candidates: 候选列表
            top_k: 返回数量

        Returns:
            降级后的结果
        """
        effective_top_k = top_k if top_k is not None else self._service_config.rerank_top_k

        return [
            RerankResult(
                chunk_id=c.get("chunk_id", 0),
                document_id=c.get("document_id", 0),
                version_id=c.get("version_id", 0),
                title_path=c.get("title_path"),
                page_start=c.get("page_start"),
                page_end=c.get("page_end"),
                content=c.get("content", ""),
                chunk_type=c.get("chunk_type", "paragraph"),
                original_rank=i + 1,
                rerank_score=0.0,
                rerank_rank=i + 1,
                rerank_model="fallback"
            )
            for i, c in enumerate(candidates[:effective_top_k])
        ]

    def expand_adjacent_chunks(
        self,
        candidates: List[Dict[str, Any]],
        expansion_count: int = 2
    ) -> List[Dict[str, Any]]:
        """
        邻接 Chunk 扩展

        为每个候选 Chunk 添加其前后的相邻 Chunk。

        Args:
            candidates: 候选 Chunk 列表
            expansion_count: 前后扩展的数量

        Returns:
            扩展后的 Chunk 列表
        """
        if not candidates:
            return []

        chunk_ids = [c.get("chunk_id") for c in candidates if c.get("chunk_id")]

        if not chunk_ids:
            return candidates

        try:
            from app.models.chunk import DocumentChunk
            from core.database import SessionLocal

            db = SessionLocal()
            try:
                adjacent_chunks = db.query(DocumentChunk).filter(
                    DocumentChunk.id.in_(chunk_ids)
                ).all()

                doc_chunks: Dict[int, List[DocumentChunk]] = {}
                for chunk in adjacent_chunks:
                    if chunk.document_id not in doc_chunks:
                        doc_chunks[chunk.document_id] = []
                    doc_chunks[chunk.document_id].append(chunk)

                for doc_id in doc_chunks:
                    doc_chunks[doc_id].sort(key=lambda x: x.chunk_index)

                expanded = list(candidates)
                seen_ids = set(chunk_ids)

                for candidate in candidates:
                    chunk_id = candidate.get("chunk_id")
                    if not chunk_id:
                        continue

                    for doc_id, chunks in doc_chunks.items():
                        for i, chunk in enumerate(chunks):
                            if chunk.id == chunk_id:
                                # 向前扩展
                                for j in range(max(0, i - expansion_count), i):
                                    if chunks[j].id not in seen_ids:
                                        expanded.append({
                                            "chunk_id": chunks[j].id,
                                            "document_id": chunks[j].document_id,
                                            "version_id": chunks[j].version_id,
                                            "title_path": chunks[j].title_path,
                                            "page_start": chunks[j].page_start,
                                            "page_end": chunks[j].page_end,
                                            "content": chunks[j].content or "",
                                            "chunk_type": chunks[j].chunk_type,
                                            "is_expanded": True
                                        })
                                        seen_ids.add(chunks[j].id)

                                # 向后扩展
                                for j in range(i + 1, min(len(chunks), i + expansion_count + 1)):
                                    if chunks[j].id not in seen_ids:
                                        expanded.append({
                                            "chunk_id": chunks[j].id,
                                            "document_id": chunks[j].document_id,
                                            "version_id": chunks[j].version_id,
                                            "title_path": chunks[j].title_path,
                                            "page_start": chunks[j].page_start,
                                            "page_end": chunks[j].page_end,
                                            "content": chunks[j].content or "",
                                            "chunk_type": chunks[j].chunk_type,
                                            "is_expanded": True
                                        })
                                        seen_ids.add(chunks[j].id)
                                break

                logger.info(
                    "邻接 Chunk 扩展完成",
                    extra={
                        "original_count": len(candidates),
                        "expanded_count": len(expanded)
                    }
                )

                return expanded

            finally:
                db.close()

        except Exception as e:
            logger.warning(f"邻接 Chunk 扩展失败: {str(e)}")
            return candidates

    def expand_table_chunks(
        self,
        candidates: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        同表格/图表关联扩展

        为表格和图表 Chunk 添加相关的摘要和上下文。

        Args:
            candidates: 候选 Chunk 列表

        Returns:
            扩展后的 Chunk 列表
        """
        expanded = []

        for candidate in candidates:
            expanded.append(candidate)

            chunk_type = candidate.get("chunk_type", "")
            if chunk_type in ["table", "image", "chart"]:
                if chunk_type == "table":
                    table_summary = candidate.get("table_summary")
                    if table_summary:
                        summary_content = f"【表格摘要】{table_summary}\n\n{candidate.get('content', '')}"
                        candidate["content"] = summary_content

        return expanded

    def rerank_with_expansion(
        self,
        query: str,
        candidates: List[Dict[str, Any]],
        top_k: Optional[int] = None,
        expand_adjacent: bool = True,
        expand_tables: bool = True,
        min_score: Optional[float] = None
    ) -> List[RerankResult]:
        """
        带扩展的重排序

        完整的重排序流程：扩展 + 评分 + 排序。

        Args:
            query: 查询文本
            candidates: 候选 Chunk 列表
            top_k: 返回数量
            expand_adjacent: 是否扩展邻接 Chunk
            expand_tables: 是否扩展表格/图表
            min_score: 最低分数阈值

        Returns:
            重排序后的结果
        """
        start_time = time.time()
        trace_id = f"rerank_expand_{int(time.time() * 1000)}"

        try:
            # 1. 扩展（可选）
            if expand_adjacent:
                candidates = self.expand_adjacent_chunks(candidates)

            if expand_tables:
                candidates = self.expand_table_chunks(candidates)

            # 2. 去重
            seen_ids = set()
            unique_candidates = []
            for c in candidates:
                chunk_id = c.get("chunk_id")
                if chunk_id and chunk_id not in seen_ids:
                    unique_candidates.append(c)
                    seen_ids.add(chunk_id)

            logger.info(
                "带扩展重排序完成预处理",
                extra={
                    "traceId": trace_id,
                    "original_count": len(candidates),
                    "unique_count": len(unique_candidates)
                }
            )

            # 3. 重排序
            return self.rerank(query, unique_candidates, top_k, min_score)

        except Exception as e:
            logger.error(f"带扩展重排序失败: {str(e)}")
            return self._fallback_rerank(candidates, top_k)

    def get_stats(self) -> Dict[str, Any]:
        """
        获取重排序统计信息

        Returns:
            统计信息
        """
        return {
            "model": self.reranker.model_name,
            "use_ollama": self._config.use_ollama,
            "fallback_to_mock": self._config.fallback_to_mock,
            "rerank_model": self._config.rerank_model,
            "min_score": self._config.min_score,
            "max_results": self._config.max_results
        }


# 全局服务实例
_rerank_service: Optional[RerankService] = None


def get_rerank_service(config: Optional[RerankConfig] = None) -> RerankService:
    """
    获取重排序服务实例

    Args:
        config: 重排序配置

    Returns:
        RerankService 实例
    """
    global _rerank_service
    if _rerank_service is None:
        _rerank_service = RerankService(config)
    return _rerank_service


def reset_rerank_service() -> None:
    """重置服务实例"""
    global _rerank_service
    _rerank_service = None
