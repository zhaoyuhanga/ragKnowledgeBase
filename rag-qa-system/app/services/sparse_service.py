"""
RAG 问答系统 - Sparse/BM25 检索服务模块
预留接口，用于与 Dense 检索结果融合

注意：当前为最小可用版本，仅提供接口抽象
完整实现需要：
1. Milvus sparse vector 支持（需要 Milvus 2.4+）
2. 或使用外部 BM25 服务（如 Elasticsearch、Meilisearch）
3. 或使用本地 BM25 库（如 rank_bm25）
"""

from typing import List, Dict, Optional, Any, Tuple
import math
import re
from collections import Counter

from app.config import settings
from app.core.logger import get_logger

logger = get_logger(__name__)


class SparseResult:
    """Sparse 检索结果"""

    def __init__(
        self,
        chunks: List[Dict[str, Any]],
        scores: List[float],
        method: str = "bm25"
    ):
        self.chunks = chunks
        self.scores = scores
        self.method = method

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chunks": self.chunks,
            "scores": self.scores,
            "method": self.method,
            "count": len(self.chunks)
        }


class SparseService:
    """
    Sparse 检索服务（预留接口）

    提供 BM25/SPLADE 等稀疏检索能力
    用于与 Dense 检索结果进行 RRF 融合
    """

    _instance: Optional["SparseService"] = None
    _initialized: bool = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if SparseService._initialized:
            return
        self._initialize()
        SparseService._initialized = True

    def _initialize(self):
        """初始化 Sparse 服务"""
        self.enabled = settings.sparse_enabled
        self.weight = settings.sparse_weight
        self.bm25_k1 = settings.bm25_k1
        self.bm25_b = settings.bm25_b
        self.rrf_k = settings.rrf_k

        if self.enabled:
            logger.info(f"Sparse 服务已启用，weight={self.weight}, rrf_k={self.rrf_k}")
        else:
            logger.info("Sparse 检索未启用，将仅使用 Dense 检索")

    def is_available(self) -> bool:
        """检查 Sparse 服务是否可用"""
        return self.enabled

    def search(
        self,
        query: str,
        documents: List[str],
        top_k: int = 50,
        metadata: List[Dict[str, Any]] = None
    ) -> SparseResult:
        """
        Sparse 检索（预留接口）

        Args:
            query: 查询文本
            documents: 文档列表
            top_k: 返回数量
            metadata: 文档元数据列表

        Returns:
            SparseResult: 检索结果
        """
        if not self.enabled:
            logger.debug("Sparse 检索未启用，返回空结果")
            return SparseResult(chunks=[], scores=[], method="disabled")

        if not documents:
            return SparseResult(chunks=[], scores=[], method="bm25")

        try:
            # 简单 BM25 实现（仅作预留，实际生产应使用专业库或服务）
            chunks, scores = self._bm25_search(query, documents, top_k, metadata)

            logger.info(f"Sparse 检索完成，返回 {len(chunks)} 条结果")

            return SparseResult(chunks=chunks, scores=scores, method="bm25")

        except Exception as e:
            logger.error(f"Sparse 检索失败: {e}")
            return SparseResult(chunks=[], scores=[], method="error")

    def _bm25_search(
        self,
        query: str,
        documents: List[str],
        top_k: int,
        metadata: List[Dict[str, Any]]
    ) -> Tuple[List[Dict[str, Any]], List[float]]:
        """
        简单 BM25 实现

        注意：这是一个最小可用实现，仅用于预留接口
        实际生产环境应使用：
        1. Elasticsearch / OpenSearch
        2. Meilisearch
        3. rank_bm25 库
        4. 或 Milvus 的 sparse vector 支持
        """
        if not documents:
            return [], []

        # 分词（简单按空格和标点分词）
        query_terms = self._tokenize(query)
        doc_terms_list = [self._tokenize(doc) for doc in documents]

        # 计算 IDF
        N = len(documents)
        doc_freq = Counter()
        for terms in doc_terms_list:
            doc_freq.update(set(terms))

        idf = {}
        for term, df in doc_freq.items():
            idf[term] = math.log((N - df + 0.5) / (df + 0.5) + 1)

        # 计算每个文档的 BM25 分数
        scores = []
        avgdl = sum(len(terms) for terms in doc_terms_list) / N

        for doc, terms in zip(documents, doc_terms_list):
            score = 0.0
            dl = len(terms)

            term_counts = Counter(terms)

            for term in query_terms:
                if term in term_counts:
                    tf = term_counts[term]
                    term_idf = idf.get(term, 0)
                    # BM25 公式
                    numerator = tf * (self.bm25_k1 + 1)
                    denominator = tf + self.bm25_k1 * (1 - self.bm25_b + self.bm25_b * dl / avgdl)
                    score += term_idf * numerator / (denominator + 1e-10)

            scores.append(score)

        # 排序并返回 top_k
        indexed_scores = list(enumerate(scores))
        indexed_scores.sort(key=lambda x: x[1], reverse=True)

        top_results = indexed_scores[:top_k]

        result_chunks = []
        result_scores = []

        for idx, score in top_results:
            chunk = {
                "content": documents[idx],
                "score": score,
                "index": idx,
            }
            if metadata and idx < len(metadata):
                chunk.update(metadata[idx])

            result_chunks.append(chunk)
            result_scores.append(score)

        return result_chunks, result_scores

    def _tokenize(self, text: str) -> List[str]:
        """
        简单分词

        Args:
            text: 输入文本

        Returns:
            分词列表
        """
        # 简单分词：转小写，移除标点，按空格分词
        text = text.lower()
        # 保留中文字符、英文、数字
        text = re.sub(r"[^\w\s\u4e00-\u9fff]", " ", text)
        terms = text.split()
        # 移除过短的词
        return [t for t in terms if len(t) >= 2]

    @staticmethod
    def rrf_fusion(
        results_list: List[List[Tuple[Any, float]]],
        k: int = 60
    ) -> List[Tuple[Any, float]]:
        """
        Reciprocal Rank Fusion (RRF)

        将多个排序结果进行融合

        Args:
            results_list: 排序结果列表，每个元素是 [(item, score), ...]
            k: RRF 参数

        Returns:
            融合后的排序结果 [(item, rrf_score), ...]
        """
        if not results_list:
            return []

        if len(results_list) == 1:
            return results_list[0]

        rrf_scores: Dict[Any, Dict[str, float]] = {}

        for results in results_list:
            for rank, (item, original_score) in enumerate(results):
                if item not in rrf_scores:
                    rrf_scores[item] = {"rrf": 0.0, "original": original_score}
                rrf_scores[item]["rrf"] += 1.0 / (k + rank + 1)

        # 排序
        sorted_items = sorted(
            rrf_scores.items(),
            key=lambda x: x[1]["rrf"],
            reverse=True
        )

        return [(item, data["rrf"]) for item, data in sorted_items]

    def check_health(self) -> bool:
        """检查 Sparse 服务健康状态"""
        if not self.enabled:
            return True  # 未启用视为健康
        return True  # 当前为预留实现，始终返回健康


# 全局 Sparse 服务实例
sparse_service = SparseService()


def get_sparse_service() -> SparseService:
    """获取 Sparse 服务实例"""
    return sparse_service
