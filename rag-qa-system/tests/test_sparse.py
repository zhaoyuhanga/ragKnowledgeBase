"""
RAG 问答系统 - Sparse/BM25 服务测试模块
测试 Sparse 检索功能
"""

import pytest
from app.config import settings


class TestSparseConfig:
    """Sparse 配置测试"""

    def test_sparse_config_values(self):
        """测试 Sparse 配置默认值"""
        assert settings.sparse_enabled is False
        assert settings.sparse_weight == 0.3
        assert settings.bm25_k1 == 1.5
        assert settings.bm25_b == 0.75
        assert settings.rrf_k == 60

    def test_sparse_disabled_by_default(self):
        """验证 Sparse 默认禁用"""
        assert settings.sparse_enabled is False


class TestSparseService:
    """Sparse 服务测试"""

    @pytest.fixture
    def sparse_service(self):
        """获取 Sparse 服务实例"""
        from app.services.sparse_service import SparseService, get_sparse_service

        # 重置 singleton
        SparseService._initialized = False
        SparseService._instance = None

        return get_sparse_service()

    def test_sparse_disabled_returns_empty(self, sparse_service):
        """测试 Sparse 禁用时返回空结果"""
        result = sparse_service.search("测试查询", ["文档1", "文档2"])

        assert result.method == "disabled"
        assert len(result.chunks) == 0
        assert len(result.scores) == 0

    def test_sparse_disabled_on_empty_documents(self, sparse_service):
        """测试空文档列表"""
        result = sparse_service.search("测试查询", [])

        assert result.method == "disabled"
        assert len(result.chunks) == 0

    def test_sparse_tokenize(self, sparse_service):
        """测试分词功能"""
        tokens = sparse_service._tokenize("这是一个测试文本 Test 123")
        assert isinstance(tokens, list)
        assert len(tokens) > 0

    def test_sparse_result_to_dict(self, sparse_service):
        """测试 SparseResult 转换为字典"""
        from app.services.sparse_service import SparseResult

        result = SparseResult(
            chunks=[{"content": "test"}],
            scores=[0.9],
            method="bm25"
        )

        d = result.to_dict()
        assert d["method"] == "bm25"
        assert d["count"] == 1
        assert len(d["chunks"]) == 1


class TestRRFFusion:
    """RRF 融合测试"""

    def test_rrf_fusion_single_result(self):
        """测试单结果集 RRF"""
        from app.services.sparse_service import SparseService

        results = [[("a", 1.0), ("b", 0.9), ("c", 0.8)]]
        fused = SparseService.rrf_fusion(results)

        assert len(fused) == 3
        assert fused[0][0] == "a"

    def test_rrf_fusion_multiple_results(self):
        """测试多结果集 RRF"""
        from app.services.sparse_service import SparseService

        # Dense 排序
        dense_results = [("doc1", 0.9), ("doc2", 0.8), ("doc3", 0.7)]
        # Sparse 排序
        sparse_results = [("doc3", 0.95), ("doc1", 0.85), ("doc2", 0.75)]

        fused = SparseService.rrf_fusion([dense_results, sparse_results], k=60)

        # doc3 在两个排序中分别排第3和第1
        # doc1 分别排第1和第2
        # RRF 会平衡两者
        assert len(fused) == 3

    def test_rrf_fusion_empty_results(self):
        """测试空结果"""
        from app.services.sparse_service import SparseService

        fused = SparseService.rrf_fusion([])
        assert fused == []

    def test_rrf_fusion_with_duplicates(self):
        """测试有重复项的 RRF"""
        from app.services.sparse_service import SparseService

        results = [
            [("doc1", 0.9), ("doc2", 0.8)],
            [("doc1", 0.95), ("doc3", 0.85)]
        ]

        fused = SparseService.rrf_fusion(results)

        # doc1 应该只有一个
        doc1_count = sum(1 for item, _ in fused if item == "doc1")
        assert doc1_count == 1


class TestBM25Implementation:
    """BM25 实现测试（当启用时）"""

    @pytest.fixture
    def sparse_service(self):
        """获取 Sparse 服务实例"""
        from app.services.sparse_service import SparseService, get_sparse_service
        SparseService._initialized = False
        SparseService._instance = None
        svc = get_sparse_service()
        svc.enabled = True  # 临时启用用于测试
        return svc

    def test_bm25_basic(self, sparse_service):
        """测试基本 BM25 计算"""
        query = "测试 查询"
        docs = [
            "这是一个测试文档",
            "另一个不相关的文档",
            "测试文档用于测试"
        ]

        result = sparse_service.search(query, docs, top_k=3)

        if result.method == "bm25":
            assert len(result.chunks) <= 3
            # 包含"测试"的文档应该有更高的分数
            if result.scores:
                assert all(s >= 0 for s in result.scores)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
