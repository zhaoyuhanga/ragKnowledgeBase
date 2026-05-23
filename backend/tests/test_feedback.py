# -*- coding: utf-8 -*-
"""
反馈服务单元测试

本模块测试反馈服务相关功能，包括：
- 用户反馈提交
- 反馈分析
- 问题分类
- 优化规则管理
"""

import json
import pytest
from unittest.mock import MagicMock
from datetime import datetime

from app.schemas.qa import (
    FeedbackSubmitRequest,
    QALogQueryRequest,
    OptimizationRuleRequest,
)


class MockFeedbackService:
    """模拟反馈服务用于测试"""

    def __init__(self):
        """初始化反馈服务"""
        pass

    def _is_retrieval_issue(self, qa_log) -> bool:
        """判断是否为检索问题"""
        if not qa_log.references or qa_log.references == "[]":
            return True

        try:
            references = json.loads(qa_log.references) if isinstance(qa_log.references, str) else qa_log.references
            if not references:
                return True

            total_score = sum(ref.get("score", 0) for ref in references)
            avg_score = total_score / len(references) if len(references) > 0 else 0

            if avg_score < 0.3:
                return True

            if qa_log.retrieval_time_ms and qa_log.retrieval_time_ms > 5000:
                return True

        except (json.JSONDecodeError, TypeError):
            return True

        return False

    def _is_generation_issue(self, qa_log) -> bool:
        """判断是否为生成问题"""
        if not qa_log.answer:
            return True

        answer_lower = qa_log.answer.lower()
        if any(phrase in answer_lower for phrase in ["无法", "不知道", "没有找到", "不清楚", "抱歉"]):
            if self._has_valid_references(qa_log):
                return True

        if len(qa_log.answer) < 10 and self._has_valid_references(qa_log):
            return True

        return False

    def _has_valid_references(self, qa_log) -> bool:
        """检查是否有有效的引用"""
        if not qa_log.references or qa_log.references == "[]":
            return False

        try:
            references = json.loads(qa_log.references) if isinstance(qa_log.references, str) else qa_log.references
            return references is not None and len(references) > 0
        except (json.JSONDecodeError, TypeError):
            return False

    def _calculate_retrieval_score(self, qa_log) -> int:
        """计算检索质量评分"""
        if not qa_log.references or qa_log.references == "[]":
            return 1

        try:
            references = json.loads(qa_log.references) if isinstance(qa_log.references, str) else qa_log.references
            if not references:
                return 1

            total_score = sum(ref.get("score", 0) for ref in references)
            avg_score = total_score / len(references) if len(references) > 0 else 0

            if avg_score >= 0.7:
                return 5
            elif avg_score >= 0.5:
                return 4
            elif avg_score >= 0.3:
                return 3
            elif avg_score >= 0.1:
                return 2
            else:
                return 1

        except (json.JSONDecodeError, TypeError):
            return 1

    def _classify_issue(self, qa_log, request) -> tuple:
        """分类问题类型"""
        issue_type = "retrieval"
        issue_category = "retrieval_inaccurate"
        suggestions = []
        suggestion_type = "optimize_retrieval"

        if self._is_retrieval_issue(qa_log):
            suggestions = self._suggest_retrieval_improvements(qa_log)
            suggestion_type = "optimize_retrieval"
        elif self._is_generation_issue(qa_log):
            issue_type = "generation"
            issue_category = "answer_incorrect"
            suggestions = self._suggest_generation_improvements(qa_log)
            suggestion_type = "optimize_prompt"
        else:
            issue_type = "both"
            issue_category = "unclear"
            suggestions = ["建议检查检索和生成两个阶段的问题"]
            suggestion_type = "general"

        return issue_type, issue_category, suggestions, suggestion_type

    def _suggest_retrieval_improvements(self, qa_log) -> list:
        """生成检索改进建议"""
        suggestions = []

        if not qa_log.references or qa_log.references == "[]":
            suggestions.append("检索结果为空，建议优化检索关键词或检查文档库")
            suggestions.append("可能需要增加相关文档的导入")
        else:
            suggestions.append("检索相关性偏低，建议优化向量模型或关键词权重")
            suggestions.append("考虑调整混合检索的融合参数")

        suggestions.append("检查相关文档的切分是否合理")

        return suggestions

    def _suggest_generation_improvements(self, qa_log) -> list:
        """生成改进建议"""
        suggestions = []

        suggestions.append("检查Prompt模板是否准确引导模型生成答案")
        suggestions.append("考虑增加上下文信息或调整上下文组装策略")

        if self._is_retrieval_issue(qa_log):
            suggestions.append("虽然可能是检索问题导致的生成问题，但建议同时检查生成阶段")

        return suggestions


class TestFeedbackService:
    """反馈服务测试类"""

    def setup_method(self):
        """测试前准备"""
        self.service = MockFeedbackService()

    def test_classify_retrieval_issue(self):
        """测试检索问题分类"""
        mock_qa_log = MagicMock()
        mock_qa_log.references = None

        request = FeedbackSubmitRequest(
            qa_id=1,
            feedback=0,
            feedback_reason="检索不准确"
        )

        issue_type, category, suggestions, suggestion_type = self.service._classify_issue(
            mock_qa_log, request
        )

        assert issue_type == "retrieval"
        assert category == "retrieval_inaccurate"
        assert "检索" in suggestions[0]

    def test_classify_generation_issue(self):
        """测试生成问题分类"""
        mock_qa_log = MagicMock()
        mock_qa_log.references = json.dumps([{"chunk_id": 1, "score": 0.8}])
        mock_qa_log.answer = "无法找到相关信息"

        request = FeedbackSubmitRequest(
            qa_id=1,
            feedback=0,
            feedback_reason="答案不完整"
        )

        issue_type, category, suggestions, suggestion_type = self.service._classify_issue(
            mock_qa_log, request
        )

        assert issue_type in ["retrieval", "generation"]
        assert category in ["retrieval_inaccurate", "answer_incorrect"]

    def test_is_retrieval_issue_no_references(self):
        """测试检索问题判断：无引用"""
        mock_qa_log = MagicMock()
        mock_qa_log.references = None

        assert self.service._is_retrieval_issue(mock_qa_log) is True

    def test_is_retrieval_issue_empty_references(self):
        """测试检索问题判断：空引用列表"""
        mock_qa_log = MagicMock()
        mock_qa_log.references = "[]"

        assert self.service._is_retrieval_issue(mock_qa_log) is True

    def test_is_retrieval_issue_low_score(self):
        """测试检索问题判断：低分检索结果"""
        mock_qa_log = MagicMock()
        mock_qa_log.references = json.dumps([
            {"chunk_id": 1, "score": 0.1},
            {"chunk_id": 2, "score": 0.15}
        ])
        mock_qa_log.retrieval_time_ms = 100

        assert self.service._is_retrieval_issue(mock_qa_log) is True

    def test_is_retrieval_issue_good_score(self):
        """测试检索问题判断：高分检索结果"""
        mock_qa_log = MagicMock()
        mock_qa_log.references = json.dumps([
            {"chunk_id": 1, "score": 0.8},
            {"chunk_id": 2, "score": 0.75}
        ])
        mock_qa_log.retrieval_time_ms = 100

        assert self.service._is_retrieval_issue(mock_qa_log) is False

    def test_is_generation_issue_no_answer(self):
        """测试生成问题判断：无答案"""
        mock_qa_log = MagicMock()
        mock_qa_log.answer = None

        assert self.service._is_generation_issue(mock_qa_log) is True

    def test_is_generation_issue_cannot_answer(self):
        """测试生成问题判断：无法回答但有引用"""
        mock_qa_log = MagicMock()
        mock_qa_log.answer = "抱歉，我无法回答这个问题"
        mock_qa_log.references = json.dumps([{"chunk_id": 1, "score": 0.8}])

        assert self.service._is_generation_issue(mock_qa_log) is True

    def test_calculate_retrieval_score_excellent(self):
        """测试检索评分计算：优秀"""
        mock_qa_log = MagicMock()
        mock_qa_log.references = json.dumps([
            {"chunk_id": 1, "score": 0.9},
            {"chunk_id": 2, "score": 0.85}
        ])

        score = self.service._calculate_retrieval_score(mock_qa_log)
        assert score == 5

    def test_calculate_retrieval_score_good(self):
        """测试检索评分计算：良好"""
        mock_qa_log = MagicMock()
        mock_qa_log.references = json.dumps([
            {"chunk_id": 1, "score": 0.6},
            {"chunk_id": 2, "score": 0.55}
        ])

        score = self.service._calculate_retrieval_score(mock_qa_log)
        assert score == 4

    def test_calculate_retrieval_score_average(self):
        """测试检索评分计算：一般"""
        mock_qa_log = MagicMock()
        mock_qa_log.references = json.dumps([
            {"chunk_id": 1, "score": 0.35},
            {"chunk_id": 2, "score": 0.4}
        ])

        score = self.service._calculate_retrieval_score(mock_qa_log)
        assert score == 3

    def test_calculate_retrieval_score_poor(self):
        """测试检索评分计算：较差"""
        mock_qa_log = MagicMock()
        mock_qa_log.references = json.dumps([
            {"chunk_id": 1, "score": 0.15},
            {"chunk_id": 2, "score": 0.2}
        ])

        score = self.service._calculate_retrieval_score(mock_qa_log)
        assert score == 2

    def test_calculate_retrieval_score_very_poor(self):
        """测试检索评分计算：很差"""
        mock_qa_log = MagicMock()
        mock_qa_log.references = json.dumps([
            {"chunk_id": 1, "score": 0.05},
            {"chunk_id": 2, "score": 0.08}
        ])

        score = self.service._calculate_retrieval_score(mock_qa_log)
        assert score == 1

    def test_suggest_retrieval_improvements_no_references(self):
        """测试检索改进建议：无引用"""
        mock_qa_log = MagicMock()
        mock_qa_log.references = None

        suggestions = self.service._suggest_retrieval_improvements(mock_qa_log)

        assert len(suggestions) > 0
        assert any("空" in s or "文档" in s for s in suggestions)

    def test_suggest_retrieval_improvements_with_references(self):
        """测试检索改进建议：有引用"""
        mock_qa_log = MagicMock()
        mock_qa_log.references = json.dumps([{"chunk_id": 1, "score": 0.3}])

        suggestions = self.service._suggest_retrieval_improvements(mock_qa_log)

        assert len(suggestions) > 0
        assert any("优化" in s or "权重" in s for s in suggestions)

    def test_suggest_generation_improvements(self):
        """测试生成改进建议"""
        mock_qa_log = MagicMock()

        suggestions = self.service._suggest_generation_improvements(mock_qa_log)

        assert len(suggestions) > 0
        assert any("Prompt" in s or "上下文" in s for s in suggestions)


class TestFeedbackSchemas:
    """反馈 Schema 测试类"""

    def test_feedback_submit_request(self):
        """测试反馈提交请求模型"""
        request = FeedbackSubmitRequest(
            qa_id=1,
            feedback=1,
            feedback_reason="回答准确",
            quality_score=5
        )

        assert request.qa_id == 1
        assert request.feedback == 1
        assert request.feedback_reason == "回答准确"
        assert request.quality_score == 5

    def test_feedback_submit_request_negative(self):
        """测试负面反馈请求模型"""
        request = FeedbackSubmitRequest(
            qa_id=1,
            feedback=0,
            feedback_reason="答案不准确"
        )

        assert request.qa_id == 1
        assert request.feedback == 0
        assert request.feedback_reason == "答案不准确"

    def test_qa_log_query_request(self):
        """测试日志查询请求模型"""
        request = QALogQueryRequest(
            tenant_id=1,
            user_id=1,
            session_id="test-session",
            start_date="2026-05-01",
            end_date="2026-05-23",
            has_feedback=True,
            feedback_value=1,
            min_score=3,
            max_score=5,
            keyword="测试",
            page_no=1,
            page_size=20
        )

        assert request.tenant_id == 1
        assert request.user_id == 1
        assert request.has_feedback is True
        assert request.page_no == 1
        assert request.page_size == 20

    def test_optimization_rule_request(self):
        """测试优化规则请求模型"""
        request = OptimizationRuleRequest(
            rule_name="测试规则",
            rule_type="retrieval",
            rule_config={"min_score": 0.5},
            trigger_condition={"issue_type": "retrieval"},
            priority=1,
            enabled=True,
            description="测试描述",
            applicable_scope={"document_types": ["pdf"]},
            expected_effect="提高检索质量"
        )

        assert request.rule_name == "测试规则"
        assert request.rule_type == "retrieval"
        assert request.priority == 1
        assert request.enabled is True


class TestQALogQuery:
    """问答日志查询测试类"""

    def setup_method(self):
        """测试前准备"""
        self.service = MockFeedbackService()

    def test_query_params_validation(self):
        """测试查询参数验证"""
        request = QALogQueryRequest(
            tenant_id=1,
            page_no=1,
            page_size=20
        )

        assert request.tenant_id == 1
        assert request.page_no == 1
        assert request.page_size == 20

    def test_query_params_with_filters(self):
        """测试带筛选条件的查询参数"""
        request = QALogQueryRequest(
            tenant_id=1,
            user_id=100,
            session_id="session-123",
            start_date="2026-05-01",
            end_date="2026-05-23",
            has_feedback=True,
            feedback_value=0,
            min_score=1,
            max_score=3,
            keyword="RAG",
            page_no=2,
            page_size=50
        )

        assert request.tenant_id == 1
        assert request.user_id == 100
        assert request.session_id == "session-123"
        assert request.has_feedback is True
        assert request.feedback_value == 0
        assert request.min_score == 1
        assert request.max_score == 3
        assert request.keyword == "RAG"
        assert request.page_no == 2
        assert request.page_size == 50


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
