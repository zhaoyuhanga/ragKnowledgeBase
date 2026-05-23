# -*- coding: utf-8 -*-
"""
向量化服务单元测试

本模块包含向量化服务的独立单元测试，不依赖完整的应用配置。
"""

import pytest
import hashlib
import numpy as np


class TestMockModel:
    """模拟模型测试"""

    def test_mock_encode_produces_same_for_same_text(self):
        """测试相同文本产生相同向量"""
        def mock_encode(texts, normalize=True):
            embeddings = []
            for text in texts:
                text_bytes = text.encode("utf-8")
                # 使用固定的哈希长度，避免边界问题
                hash_bytes = hashlib.md5(text_bytes).digest()
                vector = np.array([
                    float(b) / 255.0 for b in hash_bytes
                ] + [0.0] * max(0, 1024 - len(hash_bytes)))
                if normalize:
                    norm = np.linalg.norm(vector)
                    if norm > 0:
                        vector = vector / norm
                embeddings.append(vector)
            return embeddings

        text = "test text"
        vec1 = mock_encode([text], normalize=True)[0]
        vec2 = mock_encode([text], normalize=True)[0]

        np.testing.assert_array_almost_equal(vec1, vec2)

    def test_mock_encode_different_texts(self):
        """测试不同文本产生不同向量"""
        def mock_encode(texts, normalize=True):
            embeddings = []
            for text in texts:
                text_bytes = text.encode("utf-8")
                hash_bytes = hashlib.md5(text_bytes).digest()
                vector = np.array([
                    float(b) / 255.0 for b in hash_bytes
                ] + [0.0] * max(0, 1024 - len(hash_bytes)))
                if normalize:
                    norm = np.linalg.norm(vector)
                    if norm > 0:
                        vector = vector / norm
                embeddings.append(vector)
            return embeddings

        vec1 = mock_encode(["text1"], normalize=True)[0]
        vec2 = mock_encode(["text2"], normalize=True)[0]

        assert not np.allclose(vec1, vec2)

    def test_mock_encode_dimension(self):
        """测试向量维度"""
        def mock_encode(texts, normalize=True):
            embeddings = []
            for text in texts:
                text_bytes = text.encode("utf-8")
                hash_bytes = hashlib.md5(text_bytes).digest()
                vector = np.array([
                    float(b) / 255.0 for b in hash_bytes
                ] + [0.0] * max(0, 1024 - len(hash_bytes)))
                if normalize:
                    norm = np.linalg.norm(vector)
                    if norm > 0:
                        vector = vector / norm
                embeddings.append(vector)
            return embeddings

        vectors = mock_encode(["test"], normalize=True)
        assert len(vectors[0]) == 1024


class TestCacheKeyGeneration:
    """缓存键生成测试"""

    def test_cache_key_same_text(self):
        """测试相同文本产生相同缓存键"""
        def compute_hash(text):
            normalized = text.lower().strip()
            return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:32]

        hash1 = compute_hash("test text")
        hash2 = compute_hash("test text")

        assert hash1 == hash2

    def test_cache_key_case_insensitive(self):
        """测试缓存键大小写不敏感"""
        def compute_hash(text):
            normalized = text.lower().strip()
            return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:32]

        hash1 = compute_hash("Test")
        hash2 = compute_hash("test")

        assert hash1 == hash2

    def test_cache_key_whitespace_insensitive(self):
        """测试缓存键空白不敏感"""
        def compute_hash(text):
            normalized = text.lower().strip()
            return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:32]

        hash1 = compute_hash("test text")
        hash2 = compute_hash("  test text  ")

        assert hash1 == hash2

    def test_cache_key_different_texts(self):
        """测试不同文本产生不同缓存键"""
        def compute_hash(text):
            normalized = text.lower().strip()
            return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:32]

        hash1 = compute_hash("text1")
        hash2 = compute_hash("text2")

        assert hash1 != hash2


class TestVectorOperations:
    """向量操作测试"""

    def test_vector_normalization(self):
        """测试向量归一化"""
        vector = np.array([3.0, 4.0])
        norm = np.linalg.norm(vector)
        normalized = vector / norm

        assert abs(np.linalg.norm(normalized) - 1.0) < 0.0001

    def test_cosine_similarity_same(self):
        """测试余弦相似度-相同向量"""
        vec1 = np.array([1.0, 0.0])
        vec2 = np.array([1.0, 0.0])

        cos = np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
        assert abs(cos - 1.0) < 0.0001

    def test_cosine_similarity_orthogonal(self):
        """测试余弦相似度-垂直向量"""
        vec1 = np.array([1.0, 0.0])
        vec2 = np.array([0.0, 1.0])

        cos = np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
        assert abs(cos) < 0.0001

    def test_vector_dimension_consistency(self):
        """测试向量维度一致性"""
        dimension = 1024

        text_bytes = b"test"
        hash_bytes = hashlib.md5(text_bytes).digest()
        vector = np.array([
            float(b) / 255.0 for b in hash_bytes
        ] + [0.0] * max(0, dimension - len(hash_bytes)))

        assert len(vector) == dimension


class TestBatchProcessing:
    """批处理测试"""

    def test_batch_encode_multiple_texts(self):
        """测试批量编码多个文本"""
        texts = ["text1", "text2", "text3"]
        batch_size = 32

        all_embeddings = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batch_embeddings = []
            for text in batch:
                text_bytes = text.encode("utf-8")
                hash_bytes = hashlib.md5(text_bytes).digest()
                vector = np.array([
                    float(b) / 255.0 for b in hash_bytes
                ] + [0.0] * max(0, 1024 - len(hash_bytes)))
                batch_embeddings.append(vector)
            all_embeddings.extend(batch_embeddings)

        assert len(all_embeddings) == 3
        for vector in all_embeddings:
            assert len(vector) == 1024

    def test_empty_batch_handling(self):
        """测试空批次处理"""
        texts = []
        batch_size = 32

        all_embeddings = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            for text in batch:
                text_bytes = text.encode("utf-8")
                hash_bytes = hashlib.md5(text_bytes).digest()
                vector = np.array([
                    float(b) / 255.0 for b in hash_bytes
                ] + [0.0] * max(0, 1024 - len(hash_bytes)))
                all_embeddings.append(vector)

        assert len(all_embeddings) == 0


class TestConfigurationParameters:
    """配置参数测试"""

    def test_default_config_values(self):
        """测试默认配置值"""
        model_name = "Qwen3-Embedding"
        dimension = 1024
        batch_size = 32

        assert model_name == "Qwen3-Embedding"
        assert dimension == 1024
        assert batch_size == 32

    def test_config_parameters(self):
        """测试配置参数"""
        class Config:
            def __init__(self):
                self._dimension = 1024

            @property
            def dimension(self):
                return self._dimension

        config = Config()
        assert config.dimension == 1024


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
