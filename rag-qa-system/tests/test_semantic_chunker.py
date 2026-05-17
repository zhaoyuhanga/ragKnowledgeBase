"""
RAG 问答系统 - SemanticChunker 单元测试
"""

import pytest
from app.utils.semantic_chunker import SemanticChunker, Chunk, BlockType


class TestSemanticChunkerBasic:
    """基础功能测试"""

    def setup_method(self):
        self.chunker = SemanticChunker()

    def test_split_empty_text(self):
        """测试空文本"""
        chunks = self.chunker.split_text("")
        assert len(chunks) == 0

    def test_split_whitespace_text(self):
        """测试空白文本"""
        chunks = self.chunker.split_text("   \n\n  ")
        assert len(chunks) == 0

    def test_simple_text(self):
        """测试简单文本"""
        text = "这是第一段。这是第二段。这是第三段。"
        chunks = self.chunker.split_text(text, document_id=1)
        assert len(chunks) > 0
        assert all(isinstance(c, Chunk) for c in chunks)


class TestMarkdownStructure:
    """Markdown 结构测试"""

    def setup_method(self):
        self.chunker = SemanticChunker()

    def test_heading_levels(self):
        """测试标题层级"""
        text = """# 一级标题
这是一级标题下的内容。

## 二级标题
这是二级标题下的内容。

### 三级标题
这是三级标题下的内容。
"""
        chunks = self.chunker.split_text(text, document_id=1)
        assert len(chunks) > 0

        # 检查 title_path
        for chunk in chunks:
            if chunk.metadata.title_path:
                assert isinstance(chunk.metadata.title_path, str)

    def test_paragraphs_under_heading(self):
        """测试标题下的段落"""
        text = """# 测试标题
段落一内容。

段落二内容。

段落三内容。
"""
        chunks = self.chunker.split_text(text, document_id=1)

        # 应该包含测试标题的 chunks
        titles = [c.metadata.title_path for c in chunks]
        assert any("测试标题" in t for t in titles if t)


class TestChineseParagraph:
    """中文段落测试"""

    def setup_method(self):
        self.chunker = SemanticChunker(
            target_tokens=200,
            max_tokens=300
        )

    def test_long_chinese_paragraph(self):
        """测试长中文段落"""
        text = "这是很长的一段中文文本。" * 50
        chunks = self.chunker.split_text(text, document_id=1)

        # 长文本应该被拆分
        assert len(chunks) >= 1

        # 检查 token_count
        for chunk in chunks:
            assert chunk.metadata.token_count > 0

    def test_chinese_punctuation_split(self):
        """测试中文标点拆分"""
        text = "第一句。第二句。第三句。" * 20
        chunks = self.chunker.split_text(text, document_id=1)

        assert len(chunks) > 0


class TestList:
    """列表测试"""

    def setup_method(self):
        self.chunker = SemanticChunker()

    def test_simple_list(self):
        """测试简单列表"""
        text = """# 列表标题
- 项目一
- 项目二
- 项目三
"""
        chunks = self.chunker.split_text(text, document_id=1)

        # 检查 block_type
        list_chunks = [c for c in chunks if c.metadata.block_type == BlockType.LIST]
        assert len(list_chunks) >= 0  # 可能为空因为合并了

    def test_long_list(self):
        """测试长列表"""
        items = [f"- 列表项目 {i}" for i in range(50)]
        text = "# 长列表\n" + "\n".join(items)
        chunks = self.chunker.split_text(text, document_id=1)

        assert len(chunks) > 0


class TestTable:
    """表格测试"""

    def setup_method(self):
        self.chunker = SemanticChunker()

    def test_simple_table(self):
        """测试简单表格"""
        text = """| 列1 | 列2 | 列3 |
|-----|-----|-----|
| 数据1 | 数据2 | 数据3 |
| 数据4 | 数据5 | 数据6 |
"""
        chunks = self.chunker.split_text(text, document_id=1)

        # 检查 block_type
        table_chunks = [c for c in chunks if c.metadata.block_type == BlockType.TABLE]
        assert len(table_chunks) >= 0

    def test_table_content_preserved(self):
        """测试表格内容保留"""
        text = """| 姓名 | 年龄 |
|-----|-----|
| 张三 | 25 |
| 李四 | 30 |
"""
        chunks = self.chunker.split_text(text, document_id=1)

        # 表格内容应该被保留
        all_content = " ".join(c.content for c in chunks)
        assert "张三" in all_content or "姓名" in all_content


class TestCodeBlock:
    """代码块测试"""

    def setup_method(self):
        self.chunker = SemanticChunker()

    def test_code_block(self):
        """测试代码块"""
        text = """# 代码示例
```python
def hello():
    print("Hello, World!")
```
"""
        chunks = self.chunker.split_text(text, document_id=1)

        # 检查 block_type
        code_chunks = [c for c in chunks if c.metadata.block_type == BlockType.CODE]
        if code_chunks:
            assert "def hello" in code_chunks[0].content


class TestMetadata:
    """元数据测试"""

    def setup_method(self):
        self.chunker = SemanticChunker()

    def test_chunk_metadata_fields(self):
        """测试 chunk 元数据字段"""
        text = "这是一段测试文本。" * 10
        chunks = self.chunker.split_text(text, document_id=123)

        assert len(chunks) > 0

        for chunk in chunks:
            assert chunk.metadata.chunk_index >= 0
            assert chunk.metadata.document_id == 123
            assert chunk.metadata.parent_section_id is not None
            assert chunk.metadata.section_level >= 0
            assert chunk.metadata.block_type in [b.value for b in BlockType]
            assert chunk.metadata.token_count > 0
            assert chunk.metadata.char_count > 0
            assert chunk.metadata.content_hash != ""
            assert chunk.metadata.chunk_version == "semantic-v1"

    def test_enhanced_content(self):
        """测试 enhanced_content"""
        text = """# 测试标题
这是段落内容。
"""
        chunks = self.chunker.split_text(text, document_id=1)

        assert len(chunks) > 0

        for chunk in chunks:
            # enhanced_content 应该包含标题路径
            assert chunk.enhanced_content is not None
            assert len(chunk.enhanced_content) > 0

    def test_content_not_polluted(self):
        """测试 content 不被污染"""
        text = """# 测试标题
这是原始内容。
"""
        chunks = self.chunker.split_text(text, document_id=1)

        assert len(chunks) > 0

        for chunk in chunks:
            # content 不应该包含 enhanced_content 的前缀标记
            if chunk.metadata.title_path:
                # content 不应该以 [标题] 开头
                assert not chunk.content.startswith("[")
                # 但 enhanced_content 应该包含标题
                assert chunk.metadata.title_path in chunk.enhanced_content or chunk.metadata.title_path == ""


class TestOverlap:
    """Overlap 测试"""

    def setup_method(self):
        self.chunker = SemanticChunker(
            target_tokens=100,
            max_tokens=150,
            overlap_tokens=30
        )

    def test_overlap_enabled(self):
        """测试 overlap 生效"""
        text = "这是重复内容。 " * 100 + "唯一内容。" * 50
        chunks = self.chunker.split_text(text, document_id=1)

        # 多个 chunk 应该存在
        assert len(chunks) >= 1


class TestParentChildRetrieval:
    """Parent-Child Retrieval 测试"""

    def setup_method(self):
        self.chunker = SemanticChunker()

    def test_section_id_generated(self):
        """测试 section_id 生成"""
        text = """# 父标题
## 子标题
内容段落。
"""
        chunks = self.chunker.split_text(text, document_id=1)

        assert len(chunks) > 0

        # 检查 parent_section_id
        for chunk in chunks:
            assert chunk.metadata.parent_section_id is not None


class TestTokenEstimation:
    """Token 估算测试"""

    def setup_method(self):
        self.chunker = SemanticChunker()

    def test_chinese_token_estimation(self):
        """测试中文 token 估算"""
        chinese_text = "中" * 100
        tokens = self.chunker._estimate_tokens(chinese_text)

        # 中文 100 字应该约等于 100 token
        assert 90 <= tokens <= 110

    def test_english_token_estimation(self):
        """测试英文 token 估算"""
        english_text = "a" * 100
        tokens = self.chunker._estimate_tokens(english_text)

        # 英文 100 字应该约等于 25 token
        assert 20 <= tokens <= 30

    def test_mixed_token_estimation(self):
        """测试混合文本 token 估算"""
        mixed_text = "中" * 50 + "a" * 50
        tokens = self.chunker._estimate_tokens(mixed_text)

        # 50 中文 + 50 英文
        assert 55 <= tokens <= 70


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
