# -*- coding: utf-8 -*-
"""
反馈分析与优化测试

测试反馈分析、优化规则引擎、清洗规则优化等功能。
"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime

from app.services.feedback_analyzer import (
    FeedbackAnalyzer,
    IssueClassification,
    RootCauseAnalysis,
    ImprovementSuggestion,
    AnalysisResult,
)
from app.services.optimization_engine import (
    OptimizationRuleEngine,
    TriggerCondition,
    RuleMatchResult,
)
from app.services.cleaning_optimizer import (
    CleaningRuleOptimizer,
    ProblemPattern,
    RuleOptimization,
)


class TestFeedbackAnalyzer:
    """测试反馈分析器"""

    def test_analyzer_initialization(self):
        """测试分析器初始化"""
        analyzer = FeedbackAnalyzer()
        assert analyzer is not None
        assert hasattr(analyzer, "ISSUE_TYPE_RETRIEVAL")
        assert hasattr(analyzer, "ISSUE_TYPE_GENERATION")
        assert hasattr(analyzer, "ISSUE_TYPE_BOTH")

    def test_detect_retrieval_issue_empty(self):
        """测试检测检索问题-空结果"""
        analyzer = FeedbackAnalyzer()

        qa_log = MagicMock()
        qa_log.references = None
        qa_log.retrieval_time_ms = 100

        is_issue, reason = analyzer._detect_retrieval_issue(qa_log)
        assert is_issue is True
        assert "为空" in reason

    def test_detect_retrieval_issue_empty_list(self):
        """测试检测检索问题-空列表"""
        analyzer = FeedbackAnalyzer()

        qa_log = MagicMock()
        qa_log.references = []
        qa_log.retrieval_time_ms = 100

        is_issue, reason = analyzer._detect_retrieval_issue(qa_log)
        assert is_issue is True

    def test_detect_retrieval_issue_low_score(self):
        """测试检测检索问题-低分"""
        analyzer = FeedbackAnalyzer()

        qa_log = MagicMock()
        qa_log.references = [
            {"score": 0.1},
            {"score": 0.15},
        ]
        qa_log.retrieval_time_ms = 100

        is_issue, reason = analyzer._detect_retrieval_issue(qa_log)
        assert is_issue is True
        assert "过低" in reason

    def test_detect_retrieval_issue_good_score(self):
        """测试检测检索问题-高分"""
        analyzer = FeedbackAnalyzer()

        qa_log = MagicMock()
        qa_log.references = [
            {"score": 0.8},
            {"score": 0.75},
        ]
        qa_log.retrieval_time_ms = 100

        is_issue, reason = analyzer._detect_retrieval_issue(qa_log)
        assert is_issue is False

    def test_detect_retrieval_issue_timeout(self):
        """测试检测检索问题-超时"""
        analyzer = FeedbackAnalyzer()

        qa_log = MagicMock()
        qa_log.references = [{"score": 0.7}]
        qa_log.retrieval_time_ms = 6000  # 超过5秒

        is_issue, reason = analyzer._detect_retrieval_issue(qa_log)
        assert is_issue is True
        assert "超时" in reason

    def test_detect_generation_issue_no_answer(self):
        """测试检测生成问题-无答案"""
        analyzer = FeedbackAnalyzer()

        qa_log = MagicMock()
        qa_log.answer = None
        qa_log.references = None

        is_issue, reason = analyzer._detect_generation_issue(qa_log)
        assert is_issue is True
        assert "未生成答案" in reason

    def test_detect_generation_issue_cannot_answer(self):
        """测试检测生成问题-无法回答"""
        analyzer = FeedbackAnalyzer()

        qa_log = MagicMock()
        qa_log.answer = "抱歉，我无法回答这个问题。"
        qa_log.references = [{"score": 0.8, "chunk_id": 1}]

        is_issue, reason = analyzer._detect_generation_issue(qa_log)
        assert is_issue is True
        assert "否定表述" in reason

    def test_detect_generation_issue_too_short(self):
        """测试检测生成问题-答案过短"""
        analyzer = FeedbackAnalyzer()

        qa_log = MagicMock()
        qa_log.answer = "不知道"
        qa_log.references = None

        is_issue, reason = analyzer._detect_generation_issue(qa_log)
        assert is_issue is True

    def test_detect_generation_issue_normal(self):
        """测试检测生成问题-正常"""
        analyzer = FeedbackAnalyzer()

        qa_log = MagicMock()
        qa_log.answer = "RAG系统是一种检索增强生成技术，它通过从知识库中检索相关文档来增强生成模型的回答质量。"
        qa_log.references = [{"score": 0.8, "chunk_id": 1}]

        is_issue, reason = analyzer._detect_generation_issue(qa_log)
        assert is_issue is False

    def test_analyze_feedback_reason(self):
        """测试分析反馈原因"""
        analyzer = FeedbackAnalyzer()

        # 测试关键词匹配
        assert analyzer._analyze_feedback_reason("答案不准确") == "retrieval_inaccurate"
        assert analyzer._analyze_feedback_reason("回答错误") == "answer_incorrect"
        assert analyzer._analyze_feedback_reason("找不到相关内容") == "retrieval_empty"
        assert analyzer._analyze_feedback_reason("无法回答这个问题") == "answer_cant_answer"

    def test_classify_issue_positive_feedback(self):
        """测试分类-正面反馈"""
        analyzer = FeedbackAnalyzer()

        qa_log = MagicMock()
        qa_log.references = None

        classification = analyzer._classify_issue(
            qa_log, feedback_type=1, feedback_reason=None, quality_score=5
        )

        assert classification.issue_type == "unknown"
        assert classification.issue_category == "helpful"

    def test_classify_issue_retrieval_problem(self):
        """测试分类-检索问题"""
        analyzer = FeedbackAnalyzer()

        qa_log = MagicMock()
        qa_log.references = None
        qa_log.retrieval_time_ms = 100
        qa_log.answer = "这是一个正常的回答内容"

        classification = analyzer._classify_issue(
            qa_log, feedback_type=0, feedback_reason=None, quality_score=2
        )

        assert classification.issue_type == "retrieval"
        assert classification.confidence == 0.9

    def test_classify_issue_generation_problem(self):
        """测试分类-生成问题"""
        analyzer = FeedbackAnalyzer()

        qa_log = MagicMock()
        qa_log.references = [{"score": 0.8, "chunk_id": 1}]
        qa_log.answer = "抱歉，无法回答"
        qa_log.retrieval_time_ms = 100

        classification = analyzer._classify_issue(
            qa_log, feedback_type=0, feedback_reason=None, quality_score=2
        )

        assert classification.issue_type == "generation"

    def test_extract_keywords(self):
        """测试关键词提取"""
        analyzer = FeedbackAnalyzer()

        keywords = analyzer._extract_keywords("RAG系统如何提高检索准确性？")
        # 关键词提取使用正则[\w\u4e00-\u9fa5]{2,}，会匹配连续的中英混合字符
        assert len(keywords) > 0
        # 检查提取的关键词数量
        assert len(keywords) <= 10  # 限制返回前10个

    def test_extract_keywords_empty(self):
        """测试关键词提取-空文本"""
        analyzer = FeedbackAnalyzer()

        keywords = analyzer._extract_keywords("")
        assert keywords == []

    def test_extract_keywords_chinese(self):
        """测试关键词提取-纯中文"""
        analyzer = FeedbackAnalyzer()

        keywords = analyzer._extract_keywords("这是一个测试问题")
        assert len(keywords) > 0


class TestOptimizationRuleEngine:
    """测试优化规则引擎"""

    def test_engine_initialization(self):
        """测试引擎初始化"""
        engine = OptimizationRuleEngine()
        assert engine is not None
        assert hasattr(engine, "OPERATORS")

    def test_parse_trigger_condition_empty(self):
        """测试解析触发条件-空"""
        engine = OptimizationRuleEngine()

        conditions = engine._parse_trigger_condition(None)
        assert conditions == []

    def test_parse_trigger_condition_dict(self):
        """测试解析触发条件-字典格式"""
        engine = OptimizationRuleEngine()

        condition_json = '{"issue_category__eq": "retrieval_inaccurate", "retrieval_score__gte": 3}'
        conditions = engine._parse_trigger_condition(condition_json)

        assert len(conditions) == 2
        assert any(c.condition_type == "issue_category" for c in conditions)
        assert any(c.operator == "eq" for c in conditions)

    def test_create_condition(self):
        """测试创建条件"""
        engine = OptimizationRuleEngine()

        condition = engine._create_condition("issue_category__eq", "retrieval")
        assert condition is not None
        assert condition.condition_type == "issue_category"
        assert condition.operator == "eq"
        assert condition.value == "retrieval"

    def test_operators_eq(self):
        """测试操作符-等于"""
        engine = OptimizationRuleEngine()

        op = engine.OPERATORS["eq"]
        assert op("test", "test") is True
        assert op("test", "other") is False

    def test_operators_gt(self):
        """测试操作符-大于"""
        engine = OptimizationRuleEngine()

        op = engine.OPERATORS["gt"]
        assert op(5, 3) is True
        assert op(3, 5) is False
        assert op(5, 5) is False

    def test_operators_gte(self):
        """测试操作符-大于等于"""
        engine = OptimizationRuleEngine()

        op = engine.OPERATORS["gte"]
        assert op(5, 3) is True
        assert op(5, 5) is True
        assert op(3, 5) is False

    def test_operators_lt(self):
        """测试操作符-小于"""
        engine = OptimizationRuleEngine()

        op = engine.OPERATORS["lt"]
        assert op(3, 5) is True
        assert op(5, 3) is False
        assert op(5, 5) is False

    def test_operators_lte(self):
        """测试操作符-小于等于"""
        engine = OptimizationRuleEngine()

        op = engine.OPERATORS["lte"]
        assert op(3, 5) is True
        assert op(5, 5) is True
        assert op(5, 3) is False

    def test_operators_in(self):
        """测试操作符-在列表中"""
        engine = OptimizationRuleEngine()

        op = engine.OPERATORS["in"]
        assert op("a", ["a", "b", "c"]) is True
        assert op("d", ["a", "b", "c"]) is False

    def test_operators_not_in(self):
        """测试操作符-不在列表中"""
        engine = OptimizationRuleEngine()

        op = engine.OPERATORS["not_in"]
        assert op("d", ["a", "b", "c"]) is True
        assert op("a", ["a", "b", "c"]) is False

    def test_operators_contains(self):
        """测试操作符-包含"""
        engine = OptimizationRuleEngine()

        op = engine.OPERATORS["contains"]
        assert op("hello world", "world") is True
        assert op("hello world", "foo") is False

    def test_operators_between(self):
        """测试操作符-范围"""
        engine = OptimizationRuleEngine()

        op = engine.OPERATORS["between"]
        assert op(5, [1, 10]) is True
        assert op(0, [1, 10]) is False
        assert op(11, [1, 10]) is False

    def test_evaluate_condition(self):
        """测试评估条件"""
        engine = OptimizationRuleEngine()

        analysis = MagicMock()
        analysis.issue_category = "retrieval_inaccurate"
        analysis.retrieval_score = 2

        # 等于条件
        condition = TriggerCondition(
            condition_type="issue_category",
            operator="eq",
            value="retrieval_inaccurate"
        )
        assert engine._evaluate_condition(analysis, condition) is True

        # 大于条件
        condition = TriggerCondition(
            condition_type="retrieval_score",
            operator="gt",
            value=3
        )
        assert engine._evaluate_condition(analysis, condition) is False


class TestCleaningRuleOptimizer:
    """测试清洗规则优化器"""

    def test_optimizer_initialization(self):
        """测试优化器初始化"""
        optimizer = CleaningRuleOptimizer()
        assert optimizer is not None
        assert hasattr(optimizer, "PROBLEM_PATTERNS")

    def test_problem_patterns_exist(self):
        """测试问题模式定义"""
        optimizer = CleaningRuleOptimizer()

        assert "乱码文本" in optimizer.PROBLEM_PATTERNS
        assert "页眉残留" in optimizer.PROBLEM_PATTERNS
        assert "广告噪声" in optimizer.PROBLEM_PATTERNS

    def test_match_pattern_regex(self):
        """测试匹配模式-正则"""
        optimizer = CleaningRuleOptimizer()

        pattern_config = {
            "type": "regex",
            "pattern": r"[\ufffd]{2,}"
        }

        # 使用Unicode替换字符（\ufffd）
        assert optimizer._match_pattern("测试文本\ufffd\ufffd测试", pattern_config) is True
        assert optimizer._match_pattern("正常文本", pattern_config) is False

    def test_match_pattern_keyword(self):
        """测试匹配模式-关键词"""
        optimizer = CleaningRuleOptimizer()

        pattern_config = {
            "type": "keyword",
            "keywords": ["广告", "推广"]
        }

        assert optimizer._match_pattern("这是广告内容", pattern_config) is True
        assert optimizer._match_pattern("这是正常内容", pattern_config) is False

    def test_match_pattern_no_match(self):
        """测试匹配模式-不匹配"""
        optimizer = CleaningRuleOptimizer()

        pattern_config = {
            "type": "unknown"
        }

        assert optimizer._match_pattern("测试内容", pattern_config) is False


class TestRuleOptimization:
    """测试规则优化数据类"""

    def test_rule_optimization_creation(self):
        """测试创建规则优化"""
        optimization = RuleOptimization(
            optimization_id=None,
            optimization_type="add",
            target_rule_id=None,
            rule_name="测试规则",
            rule_type="cleaning",
            rule_config={"pattern": "test"},
            priority=1,
            reason="测试原因",
            problem_pattern="test_pattern",
            status=0
        )

        assert optimization.optimization_type == "add"
        assert optimization.rule_name == "测试规则"
        assert optimization.priority == 1


class TestRuleMatchResult:
    """测试规则匹配结果"""

    def test_match_result_creation(self):
        """测试创建匹配结果"""
        result = RuleMatchResult(
            matched=True,
            rule_id=1,
            rule_name="测试规则",
            confidence=0.9,
            matched_conditions=["condition1"]
        )

        assert result.matched is True
        assert result.rule_id == 1
        assert result.confidence == 0.9


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
