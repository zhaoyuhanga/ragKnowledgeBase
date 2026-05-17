"""
RAG 问答系统 - 文档服务测试模块
测试文档处理相关功能
"""

import pytest
import os
import tempfile
from unittest.mock import Mock, patch, AsyncMock
from sqlalchemy.orm import Session

from app.utils.file_parser import FileParser
from app.utils.semantic_chunker import SemanticChunker


class TestFileParser:
    """文件解析器测试类"""

    def setup_method(self):
        """测试前准备"""
        self.parser = FileParser()

    def test_get_file_type_pdf(self):
        """测试 PDF 文件类型识别"""
        result = self.parser.get_file_type("document.pdf")
        assert result == "pdf"

    def test_get_file_type_markdown(self):
        """测试 Markdown 文件类型识别"""
        assert self.parser.get_file_type("readme.md") == "md"
        assert self.parser.get_file_type("readme.markdown") == "md"

    def test_get_file_type_txt(self):
        """测试 TXT 文件类型识别"""
        result = self.parser.get_file_type("notes.txt")
        assert result == "txt"

    def test_get_file_type_docx(self):
        """测试 DOCX 文件类型识别"""
        result = self.parser.get_file_type("document.docx")
        assert result == "docx"

    def test_get_file_type_unsupported(self):
        """测试不支持的文件类型"""
        result = self.parser.get_file_type("document.exe")
        assert result is None

    def test_get_file_type_uppercase(self):
        """测试大写扩展名"""
        result = self.parser.get_file_type("document.PDF")
        assert result == "pdf"

    def test_calculate_hash(self):
        """测试文件哈希计算"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, encoding='utf-8') as f:
            f.write("test content")
            temp_path = f.name

        try:
            hash1 = self.parser.calculate_hash(temp_path)
            assert len(hash1) == 32  # MD5 哈希长度为 32

            hash2 = self.parser.calculate_hash(temp_path)
            assert hash1 == hash2
        finally:
            os.unlink(temp_path)


class TestSemanticChunker:
    """SemanticChunker 测试类"""

    def setup_method(self):
        """测试前准备"""
        self.chunker = SemanticChunker()

    def test_split_short_text(self):
        """测试短文本切分"""
        text = "这是一个简短的测试文本。" * 3
        chunks = self.chunker.split_text(text, document_id=1)

        assert len(chunks) >= 1
        for chunk in chunks:
            assert chunk.metadata.char_count <= 1000

    def test_split_long_text(self):
        """测试长文本切分"""
        # 创建一个超过 max_tokens 的长文本
        # 默认 max_tokens=900, 中文约 900 字
        text = "这是一段测试文本。" * 200  # 约 1600 字符
        chunks = self.chunker.split_text(text, document_id=1)

        # 长文本应该被拆分
        assert len(chunks) >= 1

    def test_split_empty_text(self):
        """测试空文本"""
        chunks = self.chunker.split_text("")
        assert len(chunks) == 0

    def test_split_whitespace_text(self):
        """测试只包含空白字符的文本"""
        chunks = self.chunker.split_text("   \n\n  ")
        assert len(chunks) == 0

    def test_split_with_paragraphs(self):
        """测试带段落分隔的文本"""
        text = "第一段内容。\n\n第二段内容。\n\n第三段内容。"
        chunks = self.chunker.split_text(text, document_id=1)

        assert len(chunks) >= 1

    def test_metadata_fields(self):
        """测试元数据字段"""
        text = "这是测试内容。" * 10
        chunks = self.chunker.split_text(text, document_id=123)

        assert len(chunks) > 0
        for chunk in chunks:
            assert chunk.metadata.document_id == 123
            assert chunk.metadata.chunk_index >= 0
            assert chunk.metadata.token_count > 0
            assert chunk.metadata.char_count > 0
            assert chunk.metadata.content_hash != ""
            assert chunk.metadata.chunk_version == "semantic-v1"


@pytest.fixture
def mock_db_session():
    """Mock 数据库会话"""
    session = Mock(spec=Session)
    return session
