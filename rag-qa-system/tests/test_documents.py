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
from app.utils.text_splitter import TextSplitter


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
        # 创建临时文件
        with tempfile.NamedTemporaryFile(mode='w', delete=False, encoding='utf-8') as f:
            f.write("test content")
            temp_path = f.name
        
        try:
            hash1 = self.parser.calculate_hash(temp_path)
            assert len(hash1) == 32  # MD5 哈希长度为 32
            
            # 再次计算应该得到相同结果
            hash2 = self.parser.calculate_hash(temp_path)
            assert hash1 == hash2
        finally:
            os.unlink(temp_path)


class TestTextSplitter:
    """文本切分器测试类"""
    
    def setup_method(self):
        """测试前准备"""
        self.splitter = TextSplitter(chunk_size=100, chunk_overlap=20)
    
    def test_split_short_text(self):
        """测试短文本切分"""
        text = "这是一个简短的测试文本。" * 3
        chunks = self.splitter.split_text(text)
        
        assert len(chunks) >= 1
        for chunk in chunks:
            assert len(chunk) <= 100
    
    def test_split_long_text(self):
        """测试长文本切分"""
        text = "这是一段测试文本。" * 50
        chunks = self.splitter.split_text(text)
        
        assert len(chunks) > 1
        for chunk in chunks:
            assert len(chunk) <= 100
    
    def test_split_empty_text(self):
        """测试空文本"""
        chunks = self.splitter.split_text("")
        assert len(chunks) == 0
    
    def test_split_whitespace_text(self):
        """测试只包含空白字符的文本"""
        chunks = self.splitter.split_text("   \n\n  ")
        assert len(chunks) == 0
    
    def test_split_with_paragraphs(self):
        """测试带段落分隔的文本"""
        text = "第一段内容。\n\n第二段内容。\n\n第三段内容。"
        chunks = self.splitter.split_text(text)
        
        assert len(chunks) >= 1
    
    def test_chunk_min_size_filter(self):
        """测试最小块大小过滤"""
        splitter = TextSplitter(chunk_size=500, chunk_overlap=50, min_chunk_size=50)
        text = "短" * 10  # 只有 10 个字符
        chunks = splitter.split_text(text)
        
        # 过短的块应该被过滤
        for chunk in chunks:
            assert len(chunk) >= 50
    
    def test_normalize_whitespace(self):
        """测试空白字符规范化"""
        text = "测试    文本\n\n\n\n段落"
        normalized = self.splitter._normalize_whitespace(text)
        
        # 多个空格应该被合并
        assert "    " not in normalized
        # 多个换行应该被规范化为两个
        assert "\n\n\n\n" not in normalized


# ============================================================
# 测试用例配置
# ============================================================
"""
测试数据

| 测试项 | 测试数据 | 预期结果 |
|--------|----------|----------|
| PDF类型识别 | "document.pdf" | "pdf" |
| Markdown类型识别 | "readme.md" | "md" |
| 不支持类型 | "app.exe" | None |
| 短文本切分 | 30字文本 | 1个块 |
| 长文本切分 | 500字文本 | 多个块 |
| 空文本 | "" | 空列表 |
| 最小块过滤 | 10字文本 | 过滤掉 |
"""


# ============================================================
# Mock 测试数据
# ============================================================
MOCK_DOCUMENTS = [
    {
        "filename": "技术文档.pdf",
        "file_type": "pdf",
        "content": "RAG（Retrieval-Augmented Generation）是检索增强生成的缩写...",
        "expected_chunks": 5,
    },
    {
        "filename": "用户手册.md",
        "file_type": "md",
        "content": "本手册介绍系统的使用方法...",
        "expected_chunks": 3,
    },
]


@pytest.fixture
def mock_db_session():
    """Mock 数据库会话"""
    session = Mock(spec=Session)
    return session


@pytest.fixture
def sample_pdf_content():
    """示例 PDF 内容"""
    return """
    第一章 RAG 技术概述
    
    RAG（Retrieval-Augmented Generation）是检索增强生成的缩写，
    它是一种结合了信息检索和文本生成的技术。
    
    第二章 技术原理
    
    RAG 系统的核心组件包括：
    1. 文档加载器
    2. 文本切分器
    3. 向量化模型
    4. 检索引擎
    5. 生成模型
    """
"""
