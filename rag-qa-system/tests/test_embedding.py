"""
RAG 问答系统 - Embedding 服务测试模块
测试 Ollama Embedding 功能
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from app.config import settings


class TestEmbeddingConfig:
    """Embedding 配置测试"""

    def test_ollama_config_values(self):
        """测试 Ollama 配置默认值"""
        assert settings.embedding_provider == "ollama"
        assert settings.embedding_model == "batiai/qwen3-embedding:4b-q6"
        assert settings.embedding_dimension == 2560
        assert settings.embedding_base_url == "http://localhost:11434"
        assert settings.embedding_timeout == 60
        assert settings.embedding_max_retries == 3

    def test_embedding_dimension_matches_ollama(self):
        """验证维度配置与 Ollama 模型一致"""
        # Ollama qwen3-embedding-4b 输出 2560 维
        assert settings.embedding_dimension == 2560


class TestEmbeddingService:
    """Embedding 服务测试"""

    @pytest.fixture
    def mock_httpx_client(self):
        """Mock httpx.Client"""
        with patch('httpx.Client') as mock_client:
            # Mock tags endpoint
            mock_response_tags = Mock()
            mock_response_tags.status_code = 200

            # Mock embeddings endpoint
            mock_response_embed = Mock()
            mock_response_embed.status_code = 200
            mock_response_embed.json.return_value = {
                "embedding": [0.1] * 2560
            }

            mock_instance = MagicMock()
            mock_instance.__enter__ = Mock(return_value=mock_instance)
            mock_instance.__exit__ = Mock(return_value=False)
            mock_instance.get.return_value = mock_response_tags
            mock_instance.post.return_value = mock_response_embed

            mock_client.return_value = mock_instance
            yield mock_client

    def test_encode_single_returns_vector(self, mock_httpx_client):
        """测试 encode_single 返回正确维度的向量"""
        from app.services.embedding_service import EmbeddingService

        with patch.object(EmbeddingService, '_check_ollama_connection', return_value=True):
            service = EmbeddingService()

            result = service.encode_single("测试文本")

            assert isinstance(result, list)
            assert len(result) == 2560
            # 验证是归一化的
            norm = np.linalg.norm(result)
            assert abs(norm - 1.0) < 0.01

    def test_encode_batch_returns_vectors(self, mock_httpx_client):
        """测试批量编码返回正确结果"""
        from app.services.embedding_service import EmbeddingService

        with patch.object(EmbeddingService, '_check_ollama_connection', return_value=True):
            service = EmbeddingService()

            texts = ["文本1", "文本2", "文本3"]
            result = service.encode(texts)

            assert isinstance(result, list)
            assert len(result) == 3
            for vec in result:
                assert len(vec) == 2560
                norm = np.linalg.norm(vec)
                assert abs(norm - 1.0) < 0.01

    def test_encode_handles_empty_string(self, mock_httpx_client):
        """测试处理空字符串"""
        from app.services.embedding_service import EmbeddingService

        with patch.object(EmbeddingService, '_check_ollama_connection', return_value=True):
            service = EmbeddingService()

            result = service.encode("")

            assert isinstance(result, list)
            assert len(result) == 1
            # 空字符串应返回零向量
            assert all(v == 0.0 for v in result[0])

    def test_encode_handles_null_character(self, mock_httpx_client):
        """测试处理包含空字符的文本"""
        from app.services.embedding_service import EmbeddingService

        with patch.object(EmbeddingService, '_check_ollama_connection', return_value=True):
            service = EmbeddingService()

            result = service.encode("测试\x00文本")

            assert isinstance(result, list)
            assert len(result) == 1

    def test_normalize_function(self):
        """测试 L2 归一化函数"""
        from app.services.embedding_service import EmbeddingService

        with patch('httpx.Client'):
            service = EmbeddingService()

            # 测试非零向量归一化
            vector = [1.0, 2.0, 3.0, 4.0]
            normalized = service._normalize(vector)

            norm = np.linalg.norm(normalized)
            assert abs(norm - 1.0) < 0.001

            # 测试零向量
            zero_vector = [0.0, 0.0, 0.0, 0.0]
            normalized_zero = service._normalize(zero_vector)
            assert all(v == 0.0 for v in normalized_zero)

    def test_get_embedding_dimension(self):
        """测试获取向量维度"""
        from app.services.embedding_service import EmbeddingService

        with patch('httpx.Client'):
            service = EmbeddingService()

            dim = service.get_embedding_dimension()
            assert dim == 2560

    def test_check_health_success(self, mock_httpx_client):
        """测试健康检查成功"""
        from app.services.embedding_service import EmbeddingService

        with patch.object(EmbeddingService, '_check_ollama_connection', return_value=True):
            service = EmbeddingService()
            result = service.check_health()
            assert result is True

    def test_check_health_failure(self):
        """测试健康检查失败"""
        from app.services.embedding_service import EmbeddingService

        with patch('httpx.Client') as mock_client:
            mock_client.side_effect = Exception("Connection failed")

            # 重置 singleton 以重新初始化
            EmbeddingService._initialized = False
            EmbeddingService._instance = None

            # 连接失败时只记录警告，不抛出异常
            service = EmbeddingService()
            # 由于 mock 抛出异常，_check_ollama_connection 返回 False
            # 但初始化不会失败，只是记录警告
            assert service is not None


class TestEmbeddingIntegration:
    """Embedding 集成测试（需要 Ollama 服务运行）"""

    @pytest.fixture
    def embedding_service(self):
        """获取 Embedding 服务实例"""
        from app.services.embedding_service import get_embedding_service
        return get_embedding_service()

    def test_ollama_service_available(self, embedding_service):
        """测试 Ollama 服务可用性（需要实际运行）"""
        # 此测试需要 Ollama 服务运行在 localhost:11434
        is_healthy = embedding_service.check_health()
        # 如果服务不可用，跳过测试
        if not is_healthy:
            pytest.skip("Ollama 服务未运行，跳过集成测试")

    def test_encode_produces_normalized_vectors(self, embedding_service):
        """测试编码产生归一化向量"""
        is_healthy = embedding_service.check_health()
        if not is_healthy:
            pytest.skip("Ollama 服务未运行，跳过集成测试")

        text = "这是一个测试"
        result = embedding_service.encode_single(text)

        assert len(result) == 2560
        norm = np.linalg.norm(result)
        assert abs(norm - 1.0) < 0.01

    def test_batch_encode_produces_normalized_vectors(self, embedding_service):
        """测试批量编码产生归一化向量"""
        is_healthy = embedding_service.check_health()
        if not is_healthy:
            pytest.skip("Ollama 服务未运行，跳过集成测试")

        texts = ["文本一", "文本二", "文本三"]
        results = embedding_service.encode(texts)

        assert len(results) == 3
        for vec in results:
            assert len(vec) == 2560
            norm = np.linalg.norm(vec)
            assert abs(norm - 1.0) < 0.01

    def test_similarity_computation(self, embedding_service):
        """测试相似度计算（点积）"""
        is_healthy = embedding_service.check_health()
        if not is_healthy:
            pytest.skip("Ollama 服务未运行，跳过集成测试")

        # 相同文本应该有高相似度
        vec1 = embedding_service.encode_single("机器学习")
        vec2 = embedding_service.encode_single("机器学习")

        similarity = np.dot(vec1, vec2)
        assert similarity > 0.99, f"相同文本相似度应接近1，实际: {similarity}"

        # 不同文本相似度应该较低
        vec3 = embedding_service.encode_single("烹饪美食")
        similarity_diff = np.dot(vec1, vec3)
        assert similarity_diff < similarity, "不同文本相似度应该低于相同文本"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
