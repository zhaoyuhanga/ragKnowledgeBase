"""
RAG 问答系统 - Reranker 服务模块
跨编码器重排序服务
支持 Ollama API 调用
"""

from typing import List, Dict, Optional, Any, Tuple
import time
import httpx

from app.config import settings
from app.core.logger import get_logger

logger = get_logger(__name__)


class RerankerCandidate:
    """Reranker 候选结果"""

    def __init__(
        self,
        index: int,
        vector_id: str,
        document_id: int,
        chunk_index: int,
        content: str,
        filename: str,
        score: float,
        metadata: Dict[str, Any] = None
    ):
        self.index = index
        self.vector_id = vector_id
        self.document_id = document_id
        self.chunk_index = chunk_index
        self.content = content
        self.filename = filename
        self.score = score
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "index": self.index,
            "vector_id": self.vector_id,
            "document_id": self.document_id,
            "chunk_index": self.chunk_index,
            "content": self.content,
            "filename": self.filename,
            "score": self.score,
            "metadata": self.metadata,
        }

    def __repr__(self):
        return f"<RerankerCandidate(index={self.index}, score={self.score:.4f})>"


class RerankResult:
    """Rerank 结果"""

    def __init__(
        self,
        candidates: List[RerankerCandidate],
        rerank_time_ms: float,
        original_count: int,
        is_degraded: bool = False,
        degrade_reason: str = None
    ):
        self.candidates = candidates
        self.rerank_time_ms = rerank_time_ms
        self.original_count = original_count
        self.is_degraded = is_degraded
        self.degrade_reason = degrade_reason

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "candidates": [c.to_dict() for c in self.candidates],
            "rerank_time_ms": self.rerank_time_ms,
            "original_count": self.original_count,
            "final_count": len(self.candidates),
            "is_degraded": self.is_degraded,
            "degrade_reason": self.degrade_reason,
        }


class RerankerService:
    """
    Reranker 服务
    使用 Cross-Encoder 对检索结果进行重排序
    """

    _instance: Optional["RerankerService"] = None
    _initialized: bool = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if RerankerService._initialized:
            return
        self._initialize()
        RerankerService._initialized = True

    def _initialize(self):
        """初始化 Reranker 服务"""
        self.enabled = settings.reranker_enabled
        self.model = settings.reranker_model
        self.base_url = settings.reranker_base_url
        self.timeout = settings.reranker_timeout
        self.max_retries = settings.reranker_max_retries
        self.recall_k = settings.reranker_recall_k
        self.top_k = settings.reranker_top_k

        if self.enabled:
            logger.info(f"Reranker 服务初始化，enabled=True, model={self.model}")
        else:
            logger.info("Reranker 已禁用，将使用原始检索排序")

    def is_available(self) -> bool:
        """检查 Reranker 是否可用"""
        if not self.enabled:
            return False

        try:
            with httpx.Client(timeout=5.0) as client:
                response = client.get(f"{self.base_url}/api/tags")
                return response.status_code == 200
        except Exception as e:
            logger.warning(f"Reranker 服务不可用: {e}")
            return False

    def rerank(
        self,
        query: str,
        candidates: List[Dict[str, Any]]
    ) -> RerankResult:
        """
        对候选结果进行重排序

        Args:
            query: 用户问题
            candidates: 候选文档列表，每个元素包含:
                - vector_id: 向量 ID
                - document_id: 文档 ID
                - chunk_index: 块序号
                - content: 文档内容
                - filename: 文件名
                - score: 原始相似度分数
                - 其他 metadata

        Returns:
            RerankResult: 重排序结果
        """
        start_time = time.time()
        original_count = len(candidates)

        # 如果 Reranker 未启用或候选为空，直接返回
        if not self.enabled or not candidates:
            return RerankResult(
                candidates=[
                    RerankerCandidate(
                        index=i,
                        vector_id=c.get("vector_id", ""),
                        document_id=c.get("document_id", 0),
                        chunk_index=c.get("chunk_index", 0),
                        content=c.get("content", ""),
                        filename=c.get("filename", ""),
                        score=c.get("similarity", c.get("score", 0.0)),
                        metadata=c
                    )
                    for i, c in enumerate(candidates)
                ],
                rerank_time_ms=0,
                original_count=original_count,
                is_degraded=True,
                degrade_reason="reranker_disabled" if not self.enabled else "empty_candidates"
            )

        try:
            # 准备输入数据
            query_doc_pairs = []
            for c in candidates:
                content = c.get("content", "")
                # 截断过长的内容以节省 token
                if len(content) > 1000:
                    content = content[:1000] + "..."
                query_doc_pairs.append({
                    "query": query,
                    "document": content,
                    "original_score": c.get("similarity", c.get("score", 0.0)),
                    "vector_id": c.get("vector_id", ""),
                    "document_id": c.get("document_id", 0),
                    "chunk_index": c.get("chunk_index", 0),
                    "filename": c.get("filename", ""),
                })

            # 调用 Ollama Rerank API
            reranked_scores = self._call_rerank_api(query, [p["document"] for p in query_doc_pairs])

            if reranked_scores is None:
                # API 调用失败，降级为原始排序
                logger.warning("Reranker API 调用失败，降级为原始排序")
                return self._degrade_to_original(candidates, original_count, "api_failure", start_time)

            # 构建重排序结果
            scored_candidates = []
            for i, (pair, rerank_score) in enumerate(zip(query_doc_pairs, reranked_scores)):
                candidate = RerankerCandidate(
                    index=i,
                    vector_id=pair["vector_id"],
                    document_id=pair["document_id"],
                    chunk_index=pair["chunk_index"],
                    content=pair["document"],
                    filename=pair["filename"],
                    score=rerank_score,
                    metadata={
                        "original_score": pair["original_score"],
                        "rerank_score": rerank_score,
                        "rank_change": i - self._get_original_rank(pair["vector_id"], candidates)
                    }
                )
                scored_candidates.append(candidate)

            # 按 rerank score 排序
            scored_candidates.sort(key=lambda x: x.score, reverse=True)

            # 取 top_k
            final_candidates = scored_candidates[:self.top_k]
            # 重新编号
            for i, c in enumerate(final_candidates):
                c.index = i

            elapsed_ms = (time.time() - start_time) * 1000

            logger.info(
                f"Rerank 完成: 原始 {original_count} -> 重排 {len(final_candidates)}, "
                f"耗时 {elapsed_ms:.2f}ms"
            )

            return RerankResult(
                candidates=final_candidates,
                rerank_time_ms=elapsed_ms,
                original_count=original_count,
                is_degraded=False
            )

        except Exception as e:
            logger.error(f"Rerank 失败: {e}")
            return self._degrade_to_original(candidates, original_count, str(e), start_time)

    def _call_rerank_api(
        self,
        query: str,
        documents: List[str]
    ) -> Optional[List[float]]:
        """
        调用 Ollama Rerank API

        Args:
            query: 查询文本
            documents: 文档列表

        Returns:
            重排序分数列表，失败返回 None
        """
        if not documents:
            return []

        for attempt in range(self.max_retries):
            try:
                with httpx.Client(timeout=self.timeout) as client:
                    payload = {
                        "model": self.model,
                        "query": query,
                        "documents": documents
                    }

                    response = client.post(
                        f"{self.base_url}/api/rerank",
                        json=payload
                    )

                    if response.status_code == 200:
                        data = response.json()
                        results = data.get("results", [])
                        # 返回分数列表，按输入顺序排列
                        return [r.get("score", 0.0) for r in results]
                    else:
                        logger.warning(
                            f"Rerank API 返回错误: status={response.status_code}, "
                            f"attempt={attempt + 1}/{self.max_retries}"
                        )

            except httpx.TimeoutException:
                logger.warning(f"Rerank API 超时，attempt={attempt + 1}/{self.max_retries}")
            except Exception as e:
                logger.error(f"Rerank API 调用异常: {e}")

        return None

    def _get_original_rank(self, vector_id: str, candidates: List[Dict]) -> int:
        """获取候选在原始列表中的排名"""
        for i, c in enumerate(candidates):
            if c.get("vector_id") == vector_id:
                return i
        return -1

    def _degrade_to_original(
        self,
        candidates: List[Dict[str, Any]],
        original_count: int,
        reason: str,
        start_time: float
    ) -> RerankResult:
        """降级为原始排序"""
        elapsed_ms = (time.time() - start_time) * 1000

        reranked_candidates = [
            RerankerCandidate(
                index=i,
                vector_id=c.get("vector_id", ""),
                document_id=c.get("document_id", 0),
                chunk_index=c.get("chunk_index", 0),
                content=c.get("content", ""),
                filename=c.get("filename", ""),
                score=c.get("similarity", c.get("score", 0.0)),
                metadata={"degrade_reason": reason}
            )
            for i, c in enumerate(candidates)
        ]

        # 取 top_k
        final_candidates = reranked_candidates[:self.top_k]
        for i, c in enumerate(final_candidates):
            c.index = i

        return RerankResult(
            candidates=final_candidates,
            rerank_time_ms=elapsed_ms,
            original_count=original_count,
            is_degraded=True,
            degrade_reason=reason
        )

    def check_health(self) -> bool:
        """检查 Reranker 服务健康状态"""
        if not self.enabled:
            return True  # 未启用视为健康

        try:
            with httpx.Client(timeout=5.0) as client:
                response = client.get(f"{self.base_url}/api/tags")
                return response.status_code == 200
        except Exception as e:
            logger.error(f"Reranker 健康检查失败: {e}")
            return False


# 全局 Reranker 服务实例
reranker_service = RerankerService()


def get_reranker_service() -> RerankerService:
    """获取 Reranker 服务实例"""
    return reranker_service
