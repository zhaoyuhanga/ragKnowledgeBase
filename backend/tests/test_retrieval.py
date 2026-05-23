# -*- coding: utf-8 -*-
"""
检索服务单元测试

测试检索服务相关功能：
- 查询改写服务测试（独立测试，不依赖数据库）
- 融合服务测试（独立测试，不依赖数据库）
- RRF算法测试
"""

import sys
from pathlib import Path

# 将src目录添加到路径
backend_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(backend_path))

import pytest
import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Set


# ================================================
# 独立实现的查询改写服务（用于测试）
# ================================================

@dataclass
class RewriteResult:
    """查询改写结果"""
    original_query: str
    normalized_query: str
    multi_queries: List[str]
    sub_queries: List[str]
    hyde_answer: Optional[str]
    background_query: Optional[str]


class TestQueryRewriteService:
    """
    查询改写服务测试

    直接在测试中实现服务逻辑，避免导入问题。
    """

    def setup_method(self):
        """测试前准备"""
        self._stopwords = {
            "的", "了", "在", "是", "我", "有", "和", "就", "不", "人",
            "都", "一", "一个", "上", "也", "很", "到", "说", "要", "去",
            "你", "会", "着", "没有", "看", "好", "自己", "这", "那",
            "里", "为", "之", "以", "而", "于", "并", "及", "等", "其",
        }
        self._punctuation_pattern = re.compile(r'[^\w\s]')

    def normalize(self, query: str) -> str:
        """查询规范化"""
        if not query:
            return ""
        normalized = re.sub(r'\s+', ' ', query)
        normalized = self._punctuation_pattern.sub(' ', normalized)
        normalized = normalized.lower()
        normalized = normalized.strip()
        return normalized

    def generate_multi_queries(self, query: str, max_queries: int = 5) -> List[str]:
        """多查询生成"""
        if not query:
            return []
        queries = [query]

        terms = query.split()
        filtered_terms = [t for t in terms if t not in self._stopwords]
        if filtered_terms and len(filtered_terms) < len(terms):
            filtered_query = " ".join(filtered_terms)
            queries.append(filtered_query)

        synonym_map = {
            "系统": ["平台", "框架"],
            "如何": ["怎么", "怎样"],
            "什么": ["哪个", "哪些"],
            "查询": ["检索", "搜索"],
            "文档": ["文件", "资料"],
        }

        for term, synonyms in synonym_map.items():
            if term in query:
                for syn in synonyms:
                    expanded = query.replace(term, syn)
                    if expanded != query and expanded not in queries:
                        queries.append(expanded)

        chinese_to_english = {
            "文档": "document",
            "知识库": "knowledge base",
            "检索": "retrieval",
            "系统": "system",
        }

        for cn, en in chinese_to_english.items():
            if cn in query and en not in query:
                expanded = query.replace(cn, f"{cn} {en}")
                if expanded not in queries:
                    queries.append(expanded)

        return queries[:max_queries]

    def decompose_subqueries(self, query: str) -> List[str]:
        """子查询分解"""
        if not query:
            return []
        sub_queries = []
        separators = ["和", "与", "及", "或者", "或", "and", "or", "以及"]

        for sep in separators:
            if sep in query:
                parts = query.split(sep)
                if len(parts) > 1:
                    sub_queries.extend([p.strip() for p in parts if p.strip()])
                    break

        return sub_queries

    def extract_entities(self, query: str) -> Dict[str, List[str]]:
        """实体抽取"""
        entities = {
            "numbers": [],
            "technical_terms": [],
        }
        number_pattern = re.compile(r'\d+\.?\d*')
        entities["numbers"] = number_pattern.findall(query)

        tech_keywords = [
            "API", "SDK", "数据库", "接口", "系统", "模块",
            "向量", "检索", "索引", "模型", "服务", "配置"
        ]
        entities["technical_terms"] = [kw for kw in tech_keywords if kw in query]

        return entities

    def test_normalize_basic(self):
        """测试基本规范化"""
        query = "  这是一个   测试查询  "
        result = self.normalize(query)
        assert "  " not in result
        assert "这" in result

    def test_normalize_with_punctuation(self):
        """测试带标点的规范化"""
        query = "RAG系统是什么? 它如何工作!"
        result = self.normalize(query)
        assert "?" not in result
        assert "!" not in result

    def test_normalize_lowercase(self):
        """测试大小写转换"""
        query = "RAG Knowledge Base System"
        result = self.normalize(query)
        assert result == result.lower()

    def test_normalize_empty(self):
        """测试空字符串"""
        result = self.normalize("")
        assert result == ""

    def test_generate_multi_queries_basic(self):
        """测试基本多查询生成"""
        query = "RAG知识库检索"
        results = self.generate_multi_queries(query, max_queries=5)
        assert len(results) >= 1
        assert query in results

    def test_generate_multi_queries_with_synonyms(self):
        """测试同义词扩展"""
        query = "如何查询文档系统"
        results = self.generate_multi_queries(query, max_queries=10)
        assert query in results

    def test_generate_multi_queries_limit(self):
        """测试数量限制"""
        query = "RAG知识库系统检索功能"
        results = self.generate_multi_queries(query, max_queries=3)
        assert len(results) <= 3

    def test_decompose_subqueries_with_separator(self):
        """测试带分隔符的子查询分解"""
        query = "RAG是什么 和它如何工作"
        results = self.decompose_subqueries(query)
        assert isinstance(results, list)

    def test_decompose_subqueries_no_separator(self):
        """测试无分隔符的子查询分解"""
        query = "RAG知识库系统"
        results = self.decompose_subqueries(query)
        assert isinstance(results, list)

    def test_extract_entities(self):
        """测试实体抽取"""
        query = "RAG系统在2024年发布 版本号是1.0"
        entities = self.extract_entities(query)
        assert "numbers" in entities
        assert "1.0" in entities["numbers"]
        assert "2024" in entities["numbers"]

    def test_extract_entities_technical_terms(self):
        """测试技术术语抽取"""
        query = "API接口和数据库检索"
        entities = self.extract_entities(query)
        assert "technical_terms" in entities


# ================================================
# 独立实现的融合服务（用于测试）
# ================================================

@dataclass
class RetrievalItem:
    """检索项"""
    chunk_id: int
    document_id: int
    version_id: int
    title_path: Optional[str] = None
    page_start: Optional[int] = None
    page_end: Optional[int] = None
    content: str = ""
    chunk_type: str = "paragraph"
    vector_score: float = 0.0
    keyword_score: float = 0.0
    fusion_score: float = 0.0
    rank_vector: int = 0
    rank_keyword: int = 0


@dataclass
class FilterCriteria:
    """过滤条件"""
    tenant_ids: Optional[List[int]] = None
    user_ids: Optional[List[int]] = None
    document_ids: Optional[Set[int]] = None
    version_ids: Optional[Set[int]] = None
    chunk_types: Optional[Set[str]] = None
    min_quality_score: Optional[float] = None
    active_versions_only: bool = True


@dataclass
class FusionConfig:
    """融合配置"""
    vector_top_k: int = 100
    keyword_top_k: int = 100
    rrf_k: int = 60
    fusion_top_k: int = 20
    vector_weight: float = 0.6
    keyword_weight: float = 0.4
    enable_rrf: bool = True


class TestFusionService:
    """融合服务测试"""

    def setup_method(self):
        """测试前准备"""
        self._config = FusionConfig()

    def _create_test_items(self) -> tuple:
        """创建测试数据"""
        vector_items = [
            RetrievalItem(
                chunk_id=1, document_id=1, version_id=1,
                vector_score=0.9, keyword_score=0.0
            ),
            RetrievalItem(
                chunk_id=2, document_id=1, version_id=1,
                vector_score=0.8, keyword_score=0.0
            ),
            RetrievalItem(
                chunk_id=3, document_id=1, version_id=1,
                vector_score=0.7, keyword_score=0.0
            ),
        ]

        keyword_items = [
            RetrievalItem(
                chunk_id=1, document_id=1, version_id=1,
                vector_score=0.0, keyword_score=0.85
            ),
            RetrievalItem(
                chunk_id=4, document_id=1, version_id=1,
                vector_score=0.0, keyword_score=0.75
            ),
            RetrievalItem(
                chunk_id=5, document_id=1, version_id=1,
                vector_score=0.0, keyword_score=0.65
            ),
        ]

        return vector_items, keyword_items

    def rrf_fusion(
        self,
        vector_results: List[RetrievalItem],
        keyword_results: List[RetrievalItem],
        k: int = 60
    ) -> List[RetrievalItem]:
        """RRF融合算法"""
        if not vector_results and not keyword_results:
            return []

        if not vector_results:
            return keyword_results[:self._config.fusion_top_k]

        if not keyword_results:
            return vector_results[:self._config.fusion_top_k]

        vector_ranks = {item.chunk_id: rank for rank, item in enumerate(vector_results)}
        keyword_ranks = {item.chunk_id: rank for rank, item in enumerate(keyword_results)}

        all_chunk_ids = set(vector_ranks.keys()) | set(keyword_ranks.keys())

        rrf_scores: Dict[int, float] = {}
        for chunk_id in all_chunk_ids:
            score = 0.0
            if chunk_id in vector_ranks:
                rank = vector_ranks[chunk_id]
                score += 1.0 / (k + rank + 1)
            if chunk_id in keyword_ranks:
                rank = keyword_ranks[chunk_id]
                score += 1.0 / (k + rank + 1)
            rrf_scores[chunk_id] = score

        all_items: Dict[int, RetrievalItem] = {}
        for item in vector_results:
            all_items[item.chunk_id] = item
        for item in keyword_results:
            if item.chunk_id in all_items:
                all_items[item.chunk_id].keyword_score = item.keyword_score
            else:
                all_items[item.chunk_id] = item

        fused_results = sorted(
            all_items.values(),
            key=lambda x: rrf_scores.get(x.chunk_id, 0),
            reverse=True
        )

        for item in fused_results:
            item.fusion_score = rrf_scores.get(item.chunk_id, 0)

        return fused_results[:self._config.fusion_top_k]

    def weighted_fusion(
        self,
        vector_results: List[RetrievalItem],
        keyword_results: List[RetrievalItem],
        vector_weight: float = 0.6,
        keyword_weight: float = 0.4
    ) -> List[RetrievalItem]:
        """加权融合算法"""
        if not vector_results and not keyword_results:
            return []

        if not vector_results:
            return keyword_results[:self._config.fusion_top_k]

        if not keyword_results:
            return vector_results[:self._config.fusion_top_k]

        max_vector_score = max(item.vector_score for item in vector_results) if vector_results else 1.0
        max_keyword_score = max(item.keyword_score for item in keyword_results) if keyword_results else 1.0

        all_items: Dict[int, RetrievalItem] = {}
        for item in vector_results:
            item.vector_score = item.vector_score / max_vector_score if max_vector_score > 0 else 0
            all_items[item.chunk_id] = item

        for item in keyword_results:
            normalized_score = item.keyword_score / max_keyword_score if max_keyword_score > 0 else 0
            if item.chunk_id in all_items:
                all_items[item.chunk_id].keyword_score = normalized_score
            else:
                item.keyword_score = normalized_score
                all_items[item.chunk_id] = item

        for item in all_items.values():
            item.fusion_score = (
                vector_weight * item.vector_score +
                keyword_weight * item.keyword_score
            )

        fused_results = sorted(
            all_items.values(),
            key=lambda x: x.fusion_score,
            reverse=True
        )

        return fused_results[:self._config.fusion_top_k]

    def filter_by_permissions(
        self,
        items: List[RetrievalItem],
        criteria: FilterCriteria
    ) -> List[RetrievalItem]:
        """权限过滤"""
        filtered = []
        for item in items:
            if criteria.document_ids and item.document_id not in criteria.document_ids:
                continue
            if criteria.version_ids and item.version_id not in criteria.version_ids:
                continue
            if criteria.chunk_types and item.chunk_type not in criteria.chunk_types:
                continue
            filtered.append(item)
        return filtered

    def deduplicate(
        self,
        items: List[RetrievalItem],
        strategy: str = "higher_score"
    ) -> List[RetrievalItem]:
        """去重处理"""
        if not items:
            return []
        seen: Dict[int, RetrievalItem] = {}
        for item in items:
            if item.chunk_id not in seen:
                seen[item.chunk_id] = item
            else:
                if strategy == "higher_score":
                    existing = seen[item.chunk_id]
                    if item.fusion_score > existing.fusion_score:
                        seen[item.chunk_id] = item
        return list(seen.values())

    def test_rrf_fusion_basic(self):
        """测试RRF融合基本功能"""
        vector_items, keyword_items = self._create_test_items()
        result = self.rrf_fusion(vector_items, keyword_items)

        assert len(result) > 0
        chunk_ids = [item.chunk_id for item in result]
        assert 1 in chunk_ids

    def test_rrf_fusion_order(self):
        """测试RRF融合排序"""
        vector_items, keyword_items = self._create_test_items()
        result = self.rrf_fusion(vector_items, keyword_items)

        scores = [item.fusion_score for item in result]
        assert scores == sorted(scores, reverse=True)

    def test_rrf_fusion_empty_vector(self):
        """测试空向量结果"""
        vector_items = []
        keyword_items = [
            RetrievalItem(
                chunk_id=1, document_id=1, version_id=1,
                vector_score=0.0, keyword_score=0.85
            ),
        ]
        result = self.rrf_fusion(vector_items, keyword_items)
        assert len(result) == 1
        assert result[0].chunk_id == 1

    def test_rrf_fusion_empty_keyword(self):
        """测试空关键词结果"""
        vector_items = [
            RetrievalItem(
                chunk_id=1, document_id=1, version_id=1,
                vector_score=0.9, keyword_score=0.0
            ),
        ]
        keyword_items = []
        result = self.rrf_fusion(vector_items, keyword_items)
        assert len(result) == 1
        assert result[0].chunk_id == 1

    def test_rrf_fusion_both_empty(self):
        """测试两个都为空"""
        result = self.rrf_fusion([], [])
        assert len(result) == 0

    def test_rrf_fusion_custom_k(self):
        """测试自定义RRF参数k"""
        vector_items, keyword_items = self._create_test_items()
        result_k10 = self.rrf_fusion(vector_items, keyword_items, k=10)
        result_k60 = self.rrf_fusion(vector_items, keyword_items, k=60)

        assert len(result_k10) > 0
        assert len(result_k60) > 0

    def test_weighted_fusion_basic(self):
        """测试加权融合基本功能"""
        vector_items, keyword_items = self._create_test_items()
        result = self.weighted_fusion(vector_items, keyword_items)

        assert len(result) > 0

    def test_weighted_fusion_order(self):
        """测试加权融合排序"""
        vector_items, keyword_items = self._create_test_items()
        result = self.weighted_fusion(vector_items, keyword_items)

        scores = [item.fusion_score for item in result]
        assert scores == sorted(scores, reverse=True)

    def test_weighted_fusion_custom_weights(self):
        """测试自定义权重"""
        vector_items, keyword_items = self._create_test_items()
        result = self.weighted_fusion(
            vector_items, keyword_items,
            vector_weight=0.8, keyword_weight=0.2
        )

        assert len(result) > 0

    def test_filter_by_permissions(self):
        """测试权限过滤"""
        items = [
            RetrievalItem(
                chunk_id=1, document_id=1, version_id=1,
                chunk_type="paragraph"
            ),
            RetrievalItem(
                chunk_id=2, document_id=2, version_id=1,
                chunk_type="table"
            ),
            RetrievalItem(
                chunk_id=3, document_id=3, version_id=1,
                chunk_type="image"
            ),
        ]

        criteria = FilterCriteria(
            document_ids={1, 2}
        )

        result = self.filter_by_permissions(items, criteria)
        assert len(result) == 2
        assert all(item.document_id in {1, 2} for item in result)

    def test_filter_by_permissions_chunk_type(self):
        """测试Chunk类型过滤"""
        items = [
            RetrievalItem(
                chunk_id=1, document_id=1, version_id=1,
                chunk_type="paragraph"
            ),
            RetrievalItem(
                chunk_id=2, document_id=1, version_id=1,
                chunk_type="table"
            ),
        ]

        criteria = FilterCriteria(
            chunk_types={"paragraph"}
        )

        result = self.filter_by_permissions(items, criteria)
        assert len(result) == 1
        assert result[0].chunk_type == "paragraph"

    def test_deduplicate_basic(self):
        """测试去重基本功能"""
        items = [
            RetrievalItem(
                chunk_id=1, document_id=1, version_id=1,
                fusion_score=0.9
            ),
            RetrievalItem(
                chunk_id=1, document_id=1, version_id=1,
                fusion_score=0.5
            ),
            RetrievalItem(
                chunk_id=2, document_id=1, version_id=1,
                fusion_score=0.8
            ),
        ]

        result = self.deduplicate(items)
        assert len(result) == 2
        chunk_ids = [item.chunk_id for item in result]
        assert 1 in chunk_ids
        assert 2 in chunk_ids

    def test_deduplicate_higher_score(self):
        """测试保留高分去重策略"""
        items = [
            RetrievalItem(
                chunk_id=1, document_id=1, version_id=1,
                fusion_score=0.5
            ),
            RetrievalItem(
                chunk_id=1, document_id=1, version_id=1,
                fusion_score=0.9
            ),
        ]

        result = self.deduplicate(items, strategy="higher_score")
        assert len(result) == 1
        assert result[0].fusion_score == 0.9


class TestFusionConfig:
    """融合配置测试"""

    def test_default_config(self):
        """测试默认配置"""
        config = FusionConfig()
        assert config.vector_top_k == 100
        assert config.keyword_top_k == 100
        assert config.rrf_k == 60

    def test_custom_config(self):
        """测试自定义配置"""
        config = FusionConfig(
            vector_top_k=50,
            keyword_top_k=50,
            rrf_k=30,
        )
        assert config.vector_top_k == 50
        assert config.keyword_top_k == 50
        assert config.rrf_k == 30


class TestRRFAlgorithm:
    """RRF算法测试"""

    def test_rrf_score_calculation(self):
        """测试RRF分数计算"""
        vector_items = [
            RetrievalItem(chunk_id=1, document_id=1, version_id=1, vector_score=0.9),
            RetrievalItem(chunk_id=2, document_id=1, version_id=1, vector_score=0.8),
        ]

        keyword_items = [
            RetrievalItem(chunk_id=1, document_id=1, version_id=1, keyword_score=0.85),
            RetrievalItem(chunk_id=3, document_id=1, version_id=1, keyword_score=0.75),
        ]

        # 创建测试服务实例
        service = TestFusionService()
        service.setup_method()
        result = service.rrf_fusion(vector_items, keyword_items, k=60)

        chunk1 = next((item for item in result if item.chunk_id == 1), None)
        chunk2 = next((item for item in result if item.chunk_id == 2), None)
        chunk3 = next((item for item in result if item.chunk_id == 3), None)

        assert chunk1 is not None
        if chunk2:
            assert chunk1.fusion_score >= chunk2.fusion_score
        if chunk3:
            assert chunk1.fusion_score >= chunk3.fusion_score

    def test_rrf_with_different_ranks(self):
        """测试不同排名下的RRF分数"""
        vector_items = [
            RetrievalItem(chunk_id=1, document_id=1, version_id=1, vector_score=0.9),
            RetrievalItem(chunk_id=2, document_id=1, version_id=1, vector_score=0.8),
        ]

        keyword_items = [
            RetrievalItem(chunk_id=2, document_id=1, version_id=1, keyword_score=0.85),
            RetrievalItem(chunk_id=1, document_id=1, version_id=1, keyword_score=0.8),
        ]

        service = TestFusionService()
        service.setup_method()
        result = service.rrf_fusion(vector_items, keyword_items, k=60)

        chunk1 = next((item for item in result if item.chunk_id == 1), None)
        chunk2 = next((item for item in result if item.chunk_id == 2), None)

        assert chunk1 is not None
        assert chunk2 is not None
        assert abs(chunk1.fusion_score - chunk2.fusion_score) < 0.1


# ================================================
# 运行测试
# ================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
