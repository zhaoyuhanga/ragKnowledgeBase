"""
RAG 问答系统 - Reranker 服务测试模块
测试 Reranker 功能
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from app.config import settings


class TestRerankerConfig:
    """Reranker 配置测试"""

    def test_reranker_config_values(self):
        """测试 Reranker 配置默认值"""
        assert settings.reranker_enabled is False  # 默认禁用
        assert settings.reranker_model == "bantai/qwen3-reranker:1.5b-q4"
        assert settings.reranker_recall_k == 50
        assert settings.reranker_top_k == 10
        assert settings.reranker_timeout == 30
        assert settings.reranker_max_retries == 2

    def test_reranker_disabled_by_default(self):
        """验证 Reranker 默认禁用"""
        assert settings.reranker_enabled is False


class TestRerankerService:
    """Reranker 服务测试"""

    @pytest.fixture
    def reranker_service(self):
        """获取 Reranker 服务实例"""
        from app.services.reranker_service import RerankerService, get_reranker_service

        # 重置 singleton
        RerankerService._initialized = False
        RerankerService._instance = None

        return get_reranker_service()

    def test_reranker_disabled_returns_original_order(self, reranker_service):
        """测试 Reranker 禁用时返回原始排序"""
        candidates = [
            {"vector_id": "1", "content": "内容1", "similarity": 0.9},
            {"vector_id": "2", "content": "内容2", "similarity": 0.8},
            {"vector_id": "3", "content": "内容3", "similarity": 0.7},
        ]

        result = reranker_service.rerank("测试查询", candidates)

        assert result.is_degraded is True
        assert result.degrade_reason == "reranker_disabled"
        assert len(result.candidates) == 3
        # 原始排序保持不变
        assert result.candidates[0].vector_id == "1"
        assert result.candidates[1].vector_id == "2"
        assert result.candidates[2].vector_id == "3"

    def test_reranker_empty_candidates(self, reranker_service):
        """测试空候选列表"""
        # 当 reranker 禁用时，空候选直接返回降级结果
        result = reranker_service.rerank("测试查询", [])

        assert result.is_degraded is True
        # 空列表 + reranker 禁用 = "reranker_disabled"（因为 enabled 检查在前）
        assert result.degrade_reason in ["reranker_disabled", "empty_candidates"]
        assert len(result.candidates) == 0

    def test_reranker_candidate_to_dict(self, reranker_service):
        """测试 RerankerCandidate 转换为字典"""
        from app.services.reranker_service import RerankerCandidate

        candidate = RerankerCandidate(
            index=0,
            vector_id="test_id",
            document_id=1,
            chunk_index=0,
            content="测试内容",
            filename="test.txt",
            score=0.95,
            metadata={"key": "value"}
        )

        d = candidate.to_dict()

        assert d["index"] == 0
        assert d["vector_id"] == "test_id"
        assert d["document_id"] == 1
        assert d["chunk_index"] == 0
        assert d["content"] == "测试内容"
        assert d["filename"] == "test.txt"
        assert d["score"] == 0.95
        assert d["metadata"]["key"] == "value"

    def test_reranker_top_k_limit(self, reranker_service):
        """测试 top_k 限制 - 仅当启用 reranker 时生效"""
        candidates = [
            {"vector_id": str(i), "content": f"内容{i}", "similarity": 1.0 - i * 0.1}
            for i in range(20)
        ]

        result = reranker_service.rerank("测试查询", candidates)

        # 当 reranker 禁用时，返回所有原始候选（不做 top_k 截断）
        # 当 reranker 启用时，默认 top_k = 10
        if reranker_service.enabled:
            assert len(result.candidates) == 10
        else:
            # reranker 禁用时，返回所有候选
            assert len(result.candidates) == 20

    def test_rerank_result_to_dict(self, reranker_service):
        """测试 RerankResult 转换为字典"""
        from app.services.reranker_service import RerankerCandidate, RerankResult

        candidates = [
            RerankerCandidate(
                index=0,
                vector_id="1",
                document_id=1,
                chunk_index=0,
                content="内容1",
                filename="test.txt",
                score=0.9
            )
        ]

        result = RerankResult(
            candidates=candidates,
            rerank_time_ms=100.5,
            original_count=10,
            is_degraded=False
        )

        d = result.to_dict()

        assert len(d["candidates"]) == 1
        assert d["rerank_time_ms"] == 100.5
        assert d["original_count"] == 10
        assert d["final_count"] == 1
        assert d["is_degraded"] is False


class TestRerankerIntegration:
    """Reranker 集成测试"""

    @pytest.fixture
    def reranker_service(self):
        """获取 Reranker 服务实例"""
        from app.services.reranker_service import get_reranker_service
        return get_reranker_service()

    def test_reranker_health_check_disabled(self, reranker_service):
        """测试 Reranker 禁用时的健康检查"""
        # 禁用状态下健康检查应该返回 True
        if not settings.reranker_enabled:
            assert reranker_service.check_health() is True

    def test_reranker_api_not_available_fallback(self, reranker_service):
        """测试 Reranker API 不可用时自动降级"""
        if not settings.reranker_enabled:
            pytest.skip("Reranker 已禁用，跳过测试")

        # 模拟 API 失败
        candidates = [
            {"vector_id": "1", "content": "内容1", "similarity": 0.9},
        ]

        with patch.object(
            reranker_service,
            '_call_rerank_api',
            return_value=None
        ):
            result = reranker_service.rerank("测试查询", candidates)
            assert result.is_degraded is True
            assert result.degrade_reason == "api_failure"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
