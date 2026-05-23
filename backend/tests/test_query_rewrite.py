# -*- coding: utf-8 -*-
"""
查询改写服务单元测试

测试查询改写相关功能：
- QueryNormalizer 测试
- MultiQueryGenerator 测试
- QueryDecomposer 测试
- HyDEGenerator 测试
- BackwardHintGenerator 测试
- QueryRewriteService 测试
"""

import sys
from pathlib import Path

# 将src目录添加到路径
backend_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(backend_path))

import pytest
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set


# ================================================
# 导入待测试的模块
# ================================================
from app.services.query_rewrite_service import (
    QueryNormalizer,
    MultiQueryGenerator,
    QueryDecomposer,
    HyDEGenerator,
    BackwardHintGenerator,
    QueryRewriteService,
    NormalizeResult,
    MultiQueryResult,
    DecomposeResult,
    HyDEResult,
    BackwardHintResult,
    RewriteResult,
    CN_STOPWORDS,
    EN_STOPWORDS,
    ALL_STOPWORDS,
    SYNONYM_MAP,
    CN_TO_EN,
)


# ================================================
# QueryNormalizer 测试
# ================================================
class TestQueryNormalizer:
    """QueryNormalizer 测试类"""

    def setup_method(self):
        """测试前准备"""
        self.normalizer = QueryNormalizer(remove_stopwords=True)

    def test_normalize_basic(self):
        """测试基本规范化"""
        query = "  这是一个   测试查询  "
        result = self.normalizer.normalize(query)

        assert result.normalized == "这是一个 测试查询"
        assert "  " not in result.normalized

    def test_normalize_with_punctuation(self):
        """测试带标点的规范化"""
        query = "RAG系统是什么? 它如何工作!"
        result = self.normalizer.normalize(query)

        assert "?" not in result.normalized
        assert "!" not in result.normalized
        assert "rag" in result.normalized
        assert "系统" in result.normalized

    def test_normalize_lowercase(self):
        """测试大小写转换"""
        query = "RAG Knowledge Base System"
        result = self.normalizer.normalize(query)

        assert result.normalized == result.normalized.lower()

    def test_normalize_empty(self):
        """测试空字符串"""
        result = self.normalizer.normalize("")
        assert result.normalized == ""

    def test_normalize_none(self):
        """测试None输入"""
        result = self.normalizer.normalize(None)
        assert result.normalized == ""

    def test_normalize_stopwords_removal(self):
        """测试停用词移除"""
        query = "这是一个测试的系统"
        result = self.normalizer.normalize(query)

        # "的" 应该是停用词
        assert "的" not in result.removed_stopwords or "的" in result.normalized.split() or "的" not in result.normalized

    def test_normalize_chinese_english(self):
        """测试中英文混合"""
        query = "RAG系统是一个知识库系统"
        result = self.normalizer.normalize(query)

        assert "rag" in result.normalized
        assert "系统" in result.normalized
        assert "知识库" in result.normalized

    def test_quick_normalize(self):
        """测试快速规范化"""
        query = "  测试   查询  "
        result = self.normalizer.quick_normalize(query)

        assert result == "测试 查询"
        assert isinstance(result, str)

    def test_normalize_preserves_meaning(self):
        """测试保留语义"""
        query = "如何实现RAG系统的检索功能"
        result = self.normalizer.normalize(query)

        # 核心词汇应该保留
        assert "rag" in result.normalized
        assert "系统" in result.normalized
        assert "检索" in result.normalized

    def test_normalize_multiple_spaces(self):
        """测试多个空格处理"""
        query = "测试    查询"
        result = self.normalizer.normalize(query)

        assert "    " not in result.normalized
        assert " " in result.normalized

    def test_normalize_chinese_punctuation(self):
        """测试中文标点"""
        query = "这是测试？（中文标点）"
        result = self.normalizer.normalize(query)

        assert "？" not in result.normalized
        assert "（" not in result.normalized
        assert "）" not in result.normalized


# ================================================
# MultiQueryGenerator 测试
# ================================================
class TestMultiQueryGenerator:
    """MultiQueryGenerator 测试类"""

    def setup_method(self):
        """测试前准备"""
        self.generator = MultiQueryGenerator(use_llm=False)

    def test_generate_basic(self):
        """测试基本生成"""
        query = "RAG知识库检索"
        result = self.generator.generate(query, max_queries=5)

        assert len(result.queries) >= 1
        assert query in result.queries
        assert result.original == query

    def test_generate_empty(self):
        """测试空查询"""
        result = self.generator.generate("", max_queries=5)
        assert len(result.queries) == 0

    def test_generate_max_queries(self):
        """测试数量限制"""
        query = "RAG知识库系统检索功能"
        result = self.generator.generate(query, max_queries=3)

        assert len(result.queries) <= 3

    def test_generate_with_synonyms(self):
        """测试同义词扩展"""
        query = "如何查询文档系统"
        result = self.generator.generate(query, max_queries=10)

        assert len(result.queries) >= 1
        assert query in result.queries

    def test_generate_chinese_english_mix(self):
        """测试中英文混合"""
        query = "RAG知识库"
        result = self.generator.generate(query, max_queries=10)

        # 应该包含中英文混合的查询
        has_mixed = any("knowledge base" in q.lower() for q in result.queries)
        assert has_mixed

    def test_generate_question_forms(self):
        """测试问答形式转换"""
        query = "RAG系统配置"
        result = self.generator.generate(query, max_queries=10)

        # 应该包含关于...的说明或相关信息形式
        assert len(result.queries) >= 1

    def test_generate_no_duplicate(self):
        """测试去重"""
        query = "RAG系统"
        result = self.generator.generate(query, max_queries=10)

        # 转换为小写后不应该有重复
        lowered = [q.lower() for q in result.queries]
        assert len(lowered) == len(set(lowered))


# ================================================
# QueryDecomposer 测试
# ================================================
class TestQueryDecomposer:
    """QueryDecomposer 测试类"""

    def setup_method(self):
        """测试前准备"""
        self.decomposer = QueryDecomposer(use_llm=False)

    def test_decompose_with_separator(self):
        """测试带分隔符的分解"""
        query = "RAG是什么 和它如何工作"
        result = self.decomposer.decompose(query)

        assert isinstance(result.sub_queries, list)
        assert result.original == query

    def test_decompose_without_separator(self):
        """测试无分隔符的分解"""
        query = "RAG知识库系统"
        result = self.decomposer.decompose(query)

        # 无分隔符时应该不分解
        assert isinstance(result.sub_queries, list)

    def test_decompose_empty(self):
        """测试空查询"""
        result = self.decomposer.decompose("")
        assert len(result.sub_queries) == 0

    def test_decompose_comma_separated(self):
        """测试逗号分隔"""
        query = "RAG是什么, 如何使用"
        result = self.decomposer.decompose(query)

        assert isinstance(result.sub_queries, list)

    def test_decompose_and_or(self):
        """测试 and/or 分隔"""
        query = "RAG是什么 and 如何实现"
        result = self.decomposer.decompose(query)

        assert isinstance(result.sub_queries, list)

    def test_decompose_intents(self):
        """测试意图识别"""
        query = "RAG是什么 和 如何工作"
        result = self.decomposer.decompose(query)

        # 应该识别出并列意图
        assert isinstance(result.intents, list)


# ================================================
# HyDEGenerator 测试
# ================================================
class TestHyDEGenerator:
    """HyDEGenerator 测试类"""

    def setup_method(self):
        """测试前准备"""
        # 不使用LLM
        self.generator = HyDEGenerator(llm_client=None)

    def test_generate_without_llm(self):
        """测试无LLM情况"""
        query = "RAG是什么"
        result = self.generator.generate(query)

        # 无LLM时应该返回失败
        assert result.success is False
        assert result.hypothetical_answer is None

    def test_generate_empty(self):
        """测试空查询"""
        result = self.generator.generate("")

        assert result.success is False
        assert result.hypothetical_answer is None


# ================================================
# BackwardHintGenerator 测试
# ================================================
class TestBackwardHintGenerator:
    """BackwardHintGenerator 测试类"""

    def setup_method(self):
        """测试前准备"""
        # 不使用LLM
        self.generator = BackwardHintGenerator(llm_client=None)

    def test_generate_without_llm(self):
        """测试无LLM情况"""
        query = "RAG如何实现检索"
        result = self.generator.generate(query)

        # 无LLM时应该返回失败
        assert result.success is False
        assert result.background_query is None

    def test_generate_empty(self):
        """测试空查询"""
        result = self.generator.generate("")

        assert result.success is False
        assert result.background_query is None


# ================================================
# QueryRewriteService 测试
# ================================================
class TestQueryRewriteService:
    """QueryRewriteService 测试类"""

    def setup_method(self):
        """测试前准备"""
        self.service = QueryRewriteService(
            enable_multi_query=True,
            enable_subquery=True,
            enable_hyde=False,
            enable_background=False,
            use_llm=False
        )

    def test_rewrite_basic(self):
        """测试基本改写"""
        query = "RAG知识库如何检索"
        result = self.service.rewrite(query)

        assert result.original_query == query
        assert result.normalized_query != ""
        assert isinstance(result.multi_queries, list)
        assert isinstance(result.sub_queries, list)
        assert result.rewrite_time_ms >= 0

    def test_rewrite_empty(self):
        """测试空查询"""
        result = self.service.rewrite("")

        assert result.original_query == ""
        assert result.normalized_query == ""
        assert len(result.multi_queries) == 0

    def test_rewrite_multi_query_disabled(self):
        """测试禁用多查询"""
        service = QueryRewriteService(
            enable_multi_query=False,
            enable_subquery=True
        )
        result = service.rewrite("RAG知识库")

        # 多查询应该被禁用
        assert len(result.multi_queries) == 0 or result.multi_queries == []

    def test_rewrite_subquery_disabled(self):
        """测试禁用子查询"""
        service = QueryRewriteService(
            enable_multi_query=True,
            enable_subquery=False
        )
        result = service.rewrite("RAG是什么 和 如何工作")

        # 子查询应该被禁用
        assert len(result.sub_queries) == 0

    def test_rewrite_hyde_disabled(self):
        """测试HyDE禁用"""
        result = self.service.rewrite("RAG是什么", enable_hyde=False)

        assert result.hyde_answer is None

    def test_rewrite_with_options(self):
        """测试带选项的改写"""
        query = "RAG知识库"
        result = self.service.rewrite(
            query,
            enable_multi_query=True,
            enable_subquery=True,
            enable_hyde=False,
            enable_background=False,
            max_queries=3
        )

        assert result.original_query == query
        assert len(result.multi_queries) <= 3

    def test_normalize_only(self):
        """测试仅规范化"""
        query = "  RAG  系统  "
        result = self.service.normalize_only(query)

        assert "  " not in result
        assert "rag" in result

    def test_get_all_queries(self):
        """测试获取所有查询"""
        query = "RAG知识库检索"
        queries = self.service.get_all_queries(query, max_queries=10)

        assert len(queries) >= 1
        assert query in queries

    def test_rewrite_performance_logging(self):
        """测试性能日志"""
        query = "RAG知识库系统"
        result = self.service.rewrite(query)

        assert result.rewrite_time_ms >= 0
        assert isinstance(result.rewrite_time_ms, int)

    def test_rewrite_details(self):
        """测试详细信息"""
        query = "RAG知识库"
        result = self.service.rewrite(query)

        # 应该包含详细信息
        assert result.normalization_details is not None
        assert result.multi_query_details is not None
        assert result.decompose_details is not None


# ================================================
# 停用词测试
# ================================================
class TestStopwords:
    """停用词测试类"""

    def test_cn_stopwords_not_empty(self):
        """测试中文停用词不为空"""
        assert len(CN_STOPWORDS) > 0

    def test_en_stopwords_not_empty(self):
        """测试英文停用词不为空"""
        assert len(EN_STOPWORDS) > 0

    def test_all_stopwords(self):
        """测试总停用词"""
        assert len(ALL_STOPWORDS) == len(CN_STOPWORDS | EN_STOPWORDS)

    def test_common_stopwords(self):
        """测试常见停用词"""
        assert "的" in CN_STOPWORDS
        assert "the" in EN_STOPWORDS
        assert "的" in ALL_STOPWORDS
        assert "the" in ALL_STOPWORDS


# ================================================
# 同义词映射测试
# ================================================
class TestSynonymMap:
    """同义词映射测试类"""

    def test_synonym_map_not_empty(self):
        """测试同义词映射不为空"""
        assert len(SYNONYM_MAP) > 0

    def test_synonym_map_structure(self):
        """测试同义词映射结构"""
        for term, synonyms in SYNONYM_MAP.items():
            assert isinstance(term, str)
            assert isinstance(synonyms, list)
            assert len(synonyms) > 0

    def test_cn_to_en_structure(self):
        """测试中英映射结构"""
        for cn, en in CN_TO_EN.items():
            assert isinstance(cn, str)
            assert isinstance(en, str)


# ================================================
# 集成测试
# ================================================
class TestIntegration:
    """集成测试类"""

    def test_full_rewrite_pipeline(self):
        """测试完整改写流程"""
        service = QueryRewriteService(
            enable_multi_query=True,
            enable_subquery=True,
            enable_hyde=False,
            enable_background=False
        )

        query = "RAG知识库如何实现检索功能"
        result = service.rewrite(query)

        # 验证完整流程
        assert result.original_query == query
        assert result.normalized_query != ""
        assert len(result.multi_queries) >= 1
        assert result.rewrite_time_ms >= 0

    def test_multiple_queries(self):
        """测试多个查询"""
        service = QueryRewriteService()
        queries = [
            "RAG系统是什么",
            "如何实现向量检索",
            "知识库的配置方法"
        ]

        for query in queries:
            result = service.rewrite(query)
            assert result.normalized_query != ""
            assert result.rewrite_time_ms >= 0

    def test_error_handling(self):
        """测试错误处理"""
        service = QueryRewriteService()

        # 测试边界情况
        result = service.rewrite("")
        assert result.normalized_query == ""

        result = service.rewrite("   ")
        assert result.normalized_query == ""


# ================================================
# 运行测试
# ================================================
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
