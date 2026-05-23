# -*- coding: utf-8 -*-
"""
Ollama Embedding 测试

测试 Ollama 客户端和 Embedding 服务的集成。
"""

import pytest
import numpy as np

from app.services.ollama_client import OllamaClient, OllamaClientSync
from app.services.embedding_service import EmbeddingService


class TestOllamaClient:
    """Ollama 客户端测试"""

    def test_ollama_client_init(self):
        """测试 Ollama 客户端初始化"""
        client = OllamaClientSync()
        assert client._host is not None
        assert client._model_name is not None
        assert client._timeout > 0
        assert client._retry_times > 0

    def test_ollama_client_default_config(self):
        """测试默认配置"""
        client = OllamaClientSync()
        assert "localhost" in client._host or "11434" in str(client._timeout)
        assert "qwen" in client._model_name.lower() or "embedding" in client._model_name.lower()

    def test_normalize_function(self):
        """测试向量归一化"""
        client = OllamaClientSync()
        
        # 测试零向量
        zero_vector = np.zeros(1024)
        normalized = client._normalize(zero_vector)
        assert np.allclose(normalized, zero_vector)
        
        # 测试普通向量
        vector = np.array([1.0, 2.0, 3.0, 4.0])
        normalized = client._normalize(vector)
        
        # 检查归一化后的向量模长为1
        norm = np.linalg.norm(normalized)
        assert abs(norm - 1.0) < 1e-6

    def test_embed_single_empty_text(self):
        """测试空文本处理"""
        client = OllamaClientSync()
        vector = client.embed_single("")
        
        assert isinstance(vector, np.ndarray)
        assert len(vector) > 0

    def test_embed_batch_empty_list(self):
        """测试空列表处理"""
        client = OllamaClientSync()
        vectors = client.embed_batch([])
        
        assert isinstance(vectors, list)
        assert len(vectors) == 0

    def test_health_check_returns_bool(self):
        """测试健康检查返回布尔值"""
        client = OllamaClientSync()
        result = client.health_check()
        
        assert isinstance(result, bool)


class TestOllamaClientAsync:
    """Ollama 异步客户端测试"""

    @pytest.mark.asyncio
    async def test_async_client_init(self):
        """测试异步客户端初始化"""
        client = OllamaClient()
        assert client._host is not None
        assert client._model_name is not None
        
        await client.close()

    @pytest.mark.asyncio
    async def test_async_health_check(self):
        """测试异步健康检查"""
        client = OllamaClient()
        result = await client.health_check()
        
        assert isinstance(result, bool)
        await client.close()


class TestEmbeddingServiceWithOllama:
    """Embedding 服务 Ollama 集成测试"""

    def test_embedding_service_init(self):
        """测试 Embedding 服务初始化"""
        service = EmbeddingService()
        assert service._config is not None
        assert service._initialized is False

    def test_model_type_unknown_before_init(self):
        """测试初始化前模型类型未知"""
        service = EmbeddingService()
        assert service.model_type == "unknown"

    def test_get_model_info(self):
        """测试获取模型信息"""
        service = EmbeddingService()
        info = service.get_model_info()
        
        assert "model_name" in info
        assert "model_type" in info
        assert "dimension" in info
        assert "use_ollama" in info
        assert "ollama_host" in info

    def test_health_check(self):
        """测试健康检查"""
        service = EmbeddingService()
        result = service.health_check()
        
        assert "initialized" in result
        assert "model_type" in result
        assert "ollama_available" in result
        assert isinstance(result["ollama_available"], bool)

    def test_get_embedding_dimension(self):
        """测试获取向量维度"""
        service = EmbeddingService()
        dimension = service.get_embedding_dimension()
        
        assert dimension > 0
        assert dimension == 1024  # Qwen3-Embedding 维度

    def test_get_model_name(self):
        """测试获取模型名称"""
        service = EmbeddingService()
        name = service.get_model_name()
        
        assert name is not None
        assert len(name) > 0


class TestOllamaConfiguration:
    """Ollama 配置测试"""

    def test_use_ollama_config(self):
        """测试 Ollama 使用配置"""
        from core.config import settings
        
        assert hasattr(settings.embedding, "use_ollama")
        assert isinstance(settings.embedding.use_ollama, bool)

    def test_ollama_host_config(self):
        """测试 Ollama 主机配置"""
        from core.config import settings
        
        assert hasattr(settings.embedding, "ollama_host")
        assert settings.embedding.ollama_host is not None
        assert "11434" in settings.embedding.ollama_host or "localhost" in settings.embedding.ollama_host

    def test_ollama_timeout_config(self):
        """测试 Ollama 超时配置"""
        from core.config import settings
        
        assert hasattr(settings.embedding, "ollama_timeout")
        assert settings.embedding.ollama_timeout > 0

    def test_ollama_retry_config(self):
        """测试 Ollama 重试配置"""
        from core.config import settings
        
        assert hasattr(settings.embedding, "ollama_retry_times")
        assert settings.embedding.ollama_retry_times >= 0

    def test_fallback_to_mock_config(self):
        """测试降级到 Mock 配置"""
        from core.config import settings
        
        assert hasattr(settings.embedding, "fallback_to_mock")
        assert isinstance(settings.embedding.fallback_to_mock, bool)


class TestOllamaIntegration:
    """Ollama 集成测试（需要 Ollama 服务运行）"""

    @pytest.mark.skipif(
        True,  # 默认跳过，需要手动启用
        reason="需要 Ollama 服务运行"
    )
    def test_ollama_service_available(self):
        """测试 Ollama 服务可用性"""
        client = OllamaClientSync()
        is_healthy = client.health_check()
        
        assert is_healthy is True, "Ollama 服务不可用，请确保服务已启动"

    @pytest.mark.skipif(
        True,  # 默认跳过，需要手动启用
        reason="需要 Ollama 服务运行"
    )
    def test_ollama_embed_single(self):
        """测试 Ollama 单条向量化"""
        client = OllamaClientSync()
        
        text = "RAG知识库系统"
        vector = client.embed_single(text)
        
        assert isinstance(vector, np.ndarray)
        assert len(vector) == 1024  # Qwen3-Embedding 维度

    @pytest.mark.skipif(
        True,  # 默认跳过，需要手动启用
        reason="需要 Ollama 服务运行"
    )
    def test_ollama_same_text_same_vector(self):
        """测试相同文本产生相同向量"""
        client = OllamaClientSync()
        
        text = "测试文本"
        vec1 = client.embed_single(text)
        vec2 = client.embed_single(text)
        
        assert np.allclose(vec1, vec2), "相同文本应该产生相同向量"

    @pytest.mark.skipif(
        True,  # 默认跳过，需要手动启用
        reason="需要 Ollama 服务运行"
    )
    def test_ollama_different_text_different_vector(self):
        """测试不同文本产生不同向量"""
        client = OllamaClientSync()
        
        vec1 = client.embed_single("文本A")
        vec2 = client.embed_single("文本B")
        
        # 不同文本应该产生不同的向量
        # 使用余弦相似度判断
        similarity = np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
        assert similarity < 0.99, "不同文本应该产生不同的向量"

    @pytest.mark.skipif(
        True,  # 默认跳过，需要手动启用
        reason="需要 Ollama 服务运行"
    )
    def test_embedding_service_with_ollama(self):
        """测试 Embedding 服务使用 Ollama"""
        service = EmbeddingService()
        service._initialize_model()
        
        assert service._initialized is True
        assert service.model_type in ["ollama", "mock"]
        
        # 测试单条向量化
        text = "RAG知识库系统"
        vector, cached = service.encode_single(text)
        
        assert isinstance(vector, np.ndarray)
        assert len(vector) == 1024
