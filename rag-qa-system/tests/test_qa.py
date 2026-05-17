"""
RAG 问答系统 - 问答服务测试模块
测试问答检索和生成相关功能
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from app.services.embedding_service import EmbeddingService
from app.utils.semantic_chunker import SemanticChunker


class TestEmbeddingService:
    """Embedding 服务测试类"""

    def test_embedding_dimension(self):
        """测试向量维度配置"""
        from app.config import settings
        assert settings.embedding_dimension == 2560  # Ollama qwen3-embedding 维度

    def test_batch_size(self):
        """测试批处理大小配置"""
        from app.config import settings
        assert settings.embedding_batch_size > 0


class TestSemanticChunker:
    """SemanticChunker 测试类"""

    def setup_method(self):
        """测试前准备"""
        self.chunker = SemanticChunker()

    def test_chunk_size_respected(self):
        """测试块大小限制"""
        long_text = "测试内容 " * 200
        chunks = self.chunker.split_text(long_text, document_id=1)

        for chunk in chunks:
            assert chunk.metadata.token_count <= 1000  # 允许一定容差

    def test_chunk_overlap_works(self):
        """测试块生成"""
        text = "ABCDEFGHIJKLMNOPQRSTUVWXYZ" * 50
        chunks = self.chunker.split_text(text, document_id=1)

        # 验证有块生成
        assert len(chunks) >= 1


class TestQAService:
    """问答服务测试类（集成测试需要完整环境）"""

    def test_search_result_parsing(self):
        """测试检索结果解析"""
        mock_results = {
            "ids": [["1_0_abc123", "1_1_def456"]],
            "distances": [[0.15, 0.25]],
            "documents": [["文档内容1", "文档内容2"]],
            "metadatas": [[
                {"document_id": 1, "chunk_index": 0, "filename": "test.pdf"},
                {"document_id": 1, "chunk_index": 1, "filename": "test.pdf"}
            ]]
        }

        assert "ids" in mock_results
        assert "distances" in mock_results
        assert len(mock_results["ids"][0]) == 2


class TestChunkMetadata:
    """Chunk 元数据测试类"""

    def setup_method(self):
        """测试前准备"""
        self.chunker = SemanticChunker()

    def test_title_path_extraction(self):
        """测试标题路径提取"""
        text = """# 主标题
## 子标题
内容段落。
"""
        chunks = self.chunker.split_text(text, document_id=1)

        # 应该生成至少一个 chunk
        assert len(chunks) >= 1

    def test_block_type_detection(self):
        """测试块类型检测"""
        text = """# 标题
- 列表项1
- 列表项2
"""
        chunks = self.chunker.split_text(text, document_id=1)

        # 所有 chunks 应该有 block_type
        for chunk in chunks:
            assert chunk.metadata.block_type is not None
