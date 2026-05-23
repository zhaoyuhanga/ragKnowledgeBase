# -*- coding: utf-8 -*-
"""
切分服务测试

测试切分服务的各项功能：
- 切分策略选择
- 语义切片
- Token约束控制
- Overlap处理
- 图表特殊切分
"""

import pytest
from unittest.mock import MagicMock, patch

from app.services.chunk_service import (
    ChunkService,
    ChunkBuilder,
    ChunkStrategy,
    TokenCounter,
)
from app.schemas.chunk import ChunkConfigRequest
from app.models.parse import DocumentElement, ElementType


class TestTokenCounter:
    """Token计数器测试"""

    def test_count_empty(self):
        """测试空文本计数"""
        counter = TokenCounter()
        assert counter.count("") == 0
        assert counter.count(None) == 0

    def test_count_chinese(self):
        """测试中文计数"""
        counter = TokenCounter()
        # 粗略估算：中文约1.5字符/token
        text = "中" * 10
        count = counter.count(text)
        assert count > 0

    def test_count_english(self):
        """测试英文计数"""
        counter = TokenCounter()
        text = "a" * 10
        count = counter.count(text)
        assert count > 0


class TestChunkBuilder:
    """Chunk构建器测试"""

    def test_empty_chunk(self):
        """测试空Chunk"""
        builder = ChunkBuilder()
        assert builder.is_empty() is True
        assert builder.content == ""

    def test_add_element(self):
        """测试添加元素"""
        builder = ChunkBuilder()

        # 创建模拟元素
        element = MagicMock()
        element.element_id = "elem-001"
        element.content = "测试内容"
        element.page_no = 1
        element.title_path = "第一章 > 第一节"

        builder.add_element(element)

        assert builder.content == "测试内容"
        assert "elem-001" in builder.element_ids
        assert builder.page_start == 1
        assert builder.page_end == 1

    def test_add_multiple_elements(self):
        """测试添加多个元素"""
        builder = ChunkBuilder()

        for i in range(3):
            element = MagicMock()
            element.element_id = f"elem-{i}"
            element.content = f"内容{i}"
            element.page_no = i + 1
            element.title_path = None
            builder.add_element(element)

        assert "内容0\n内容1\n内容2" == builder.content
        assert len(builder.element_ids) == 3

    def test_get_content_hash(self):
        """测试内容哈希"""
        builder = ChunkBuilder()
        builder.content = "测试内容"

        hash1 = builder.get_content_hash()
        hash2 = builder.get_content_hash()

        assert hash1 == hash2
        assert len(hash1) == 32  # MD5哈希长度


class TestChunkService:
    """切分服务测试类"""

    def setup_method(self):
        """测试前准备"""
        self.service = ChunkService()

    def test_analyze_structure_with_titles(self):
        """测试有标题的文档结构分析"""
        elements = [
            self._create_element("title-1", ElementType.TITLE, "标题1", level=1),
            self._create_element("title-2", ElementType.TITLE, "标题2", level=2),
            self._create_element("para-1", ElementType.PARAGRAPH, "段落1内容"),
        ]

        analysis = self.service._analyze_structure(elements)

        assert analysis["has_titles"] is True
        assert analysis["total_elements"] == 3
        assert 1 in analysis["title_levels"]
        assert 2 in analysis["title_levels"]

    def test_analyze_structure_with_tables(self):
        """测试有表格的文档结构分析"""
        elements = [
            self._create_element("table-1", ElementType.TABLE, "表格内容"),
            self._create_element("para-1", ElementType.PARAGRAPH, "段落内容"),
        ]

        analysis = self.service._analyze_structure(elements)

        assert analysis["has_tables"] is True
        assert analysis["has_images"] is False

    def test_select_strategy_title_based(self):
        """测试选择基于标题的切分策略"""
        analysis = {
            "has_titles": True,
            "title_levels": {1: 5, 2: 10},
            "has_tables": False,
            "has_images": False,
            "avg_paragraph_length": 100
        }
        config = ChunkConfigRequest()

        strategy = self.service._select_strategy(analysis, config)

        assert strategy == ChunkStrategy.TITLE_BASED

    def test_select_strategy_mixed(self):
        """测试选择混合切分策略"""
        analysis = {
            "has_titles": False,
            "title_levels": {},
            "has_tables": True,
            "has_images": False,
            "avg_paragraph_length": 500
        }
        config = ChunkConfigRequest()

        strategy = self.service._select_strategy(analysis, config)

        assert strategy == ChunkStrategy.MIXED

    def test_select_strategy_semantic(self):
        """测试选择语义切分策略"""
        analysis = {
            "has_titles": False,
            "title_levels": {},
            "has_tables": False,
            "has_images": False,
            "avg_paragraph_length": 600
        }
        config = ChunkConfigRequest()

        strategy = self.service._select_strategy(analysis, config)

        assert strategy == ChunkStrategy.SEMANTIC

    def test_split_into_sentences(self):
        """测试句子拆分"""
        text = "这是第一个句子。这是第二个句子？这是第三个句子！还有第四个句子。"

        sentences = self.service._split_into_sentences(text)

        assert len(sentences) >= 3
        assert any("第一" in s for s in sentences)

    def test_split_by_char_count(self):
        """测试按字符数拆分"""
        text = "测试文本" * 100
        config = ChunkConfigRequest(max_tokens=100)  # 设置较小值

        chunks = self.service._split_by_char_count(text, config)

        assert len(chunks) > 1
        for chunk in chunks:
            assert chunk.char_count <= config.max_tokens * 2  # 粗略估算

    def test_is_semantic_boundary_chinese(self):
        """测试中文语义边界检测"""
        elements = [
            self._create_element("para-1", ElementType.PARAGRAPH, "第一段内容"),
            self._create_element("para-2", ElementType.PARAGRAPH, "但是新的转折来了"),
        ]

        is_boundary = self.service._is_semantic_boundary(elements[1], elements)

        assert is_boundary is True

    def test_is_semantic_boundary_number(self):
        """测试数字编号语义边界检测"""
        elements = [
            self._create_element("para-1", ElementType.PARAGRAPH, "内容1"),
            self._create_element("para-2", ElementType.PARAGRAPH, "2. 这是第二条内容"),
        ]

        is_boundary = self.service._is_semantic_boundary(elements[1], elements)

        assert is_boundary is True

    def test_merge_short_chunks(self):
        """测试合并过短chunk"""
        config = ChunkConfigRequest(min_tokens=50, target_tokens=600)

        chunks = [
            ChunkBuilder(content="短内容", char_count=4, chunk_type="paragraph"),
            ChunkBuilder(content="这是一段比较长的内容，可以被合并进去", char_count=20, chunk_type="paragraph"),
        ]

        # 模拟token计数
        with patch.object(self.service, '_token_counter', TokenCounter()):
            merged = self.service._merge_short_chunks(chunks, config)

        assert len(merged) <= len(chunks)

    def test_apply_overlap(self):
        """测试Overlap应用"""
        config = ChunkConfigRequest(overlap_tokens=50)

        chunks = [
            ChunkBuilder(content="这是第一段非常长的内容" * 50, char_count=500),
            ChunkBuilder(content="这是第二段内容" * 20, char_count=200),
        ]

        with patch.object(self.service, '_token_counter', TokenCounter()):
            result = self.service._apply_overlap(chunks, config)

        assert len(result) == 2

    def test_generate_chunk_id(self):
        """测试Chunk ID生成"""
        id1 = self.service._generate_chunk_id(1, 1, 0)
        id2 = self.service._generate_chunk_id(1, 1, 0)
        id3 = self.service._generate_chunk_id(1, 1, 1)

        assert id1.startswith("chunk_1_1_")
        assert id1 == id2  # 相同参数应该产生相同ID
        assert id1 != id3  # 不同参数应该产生不同ID

    def test_calculate_statistics(self):
        """测试统计信息计算"""
        from app.schemas.chunk import ChunkElement

        chunks = [
            ChunkElement(
                chunk_id="c1", chunk_index=0, content="内容1",
                token_count=100, char_count=50, chunk_type="paragraph",
                quality_score=0.9
            ),
            ChunkElement(
                chunk_id="c2", chunk_index=1, content="内容2",
                token_count=200, char_count=100, chunk_type="paragraph",
                quality_score=0.8
            ),
            ChunkElement(
                chunk_id="c3", chunk_index=2, content="内容3",
                token_count=150, char_count=75, chunk_type="table",
                quality_score=0.3
            ),
        ]

        stats = self.service._calculate_statistics(chunks)

        assert stats["total_chunks"] == 3
        assert stats["avg_tokens"] == 150
        assert stats["min_tokens"] == 100
        assert stats["max_tokens"] == 200
        assert stats["chunk_type_distribution"]["paragraph"] == 2
        assert stats["chunk_type_distribution"]["table"] == 1

    def test_calculate_statistics_empty(self):
        """测试空统计信息"""
        stats = self.service._calculate_statistics([])

        assert stats["total_chunks"] == 0
        assert stats["avg_tokens"] == 0

    def _create_element(
        self,
        element_id: str,
        element_type: ElementType,
        content: str,
        level: int = None
    ) -> DocumentElement:
        """创建测试用元素"""
        element = MagicMock(spec=DocumentElement)
        element.element_id = element_id
        element.element_type = element_type.value
        element.content = content
        element.title_level = level
        element.title_path = None
        element.page_no = 1
        element.table_structure = None
        element.image_description = None
        element.confidence = 0.9
        return element


class TestChunkSplitStrategies:
    """切分策略测试"""

    def setup_method(self):
        """测试前准备"""
        self.service = ChunkService()

    def test_split_by_title(self):
        """测试基于标题的切分"""
        elements = [
            self._create_element("title-1", ElementType.TITLE, "第一章", level=1),
            self._create_element("title-2", ElementType.TITLE, "第一节", level=2),
            self._create_element("para-1", ElementType.PARAGRAPH, "这是第一节的第一段内容"),
            self._create_element("para-2", ElementType.PARAGRAPH, "这是第一节的第二段内容"),
            self._create_element("title-3", ElementType.TITLE, "第二节", level=2),
            self._create_element("para-3", ElementType.PARAGRAPH, "这是第二节的内容"),
        ]

        config = ChunkConfigRequest(split_by_title=True)
        cleaned_map = {}

        chunks = self.service._split_by_title(elements, cleaned_map, config)

        # 验证标题被正确识别
        assert len(chunks) > 0

    def test_split_by_semantic(self):
        """测试语义切分"""
        elements = []
        for i in range(10):
            elements.append(
                self._create_element(
                    f"para-{i}",
                    ElementType.PARAGRAPH,
                    f"这是第{i}段的内容，" * 50  # 长内容
                )
            )

        config = ChunkConfigRequest(
            target_tokens=200,
            max_tokens=300,
            merge_short_chunks=False
        )
        cleaned_map = {}

        chunks = self.service._split_by_semantic(elements, cleaned_map, config)

        # 验证内容被正确切分
        assert len(chunks) >= 5  # 10段内容应该被分成多个chunk

    def test_split_mixed_with_table(self):
        """测试混合切分（包含表格）"""
        elements = [
            self._create_element("title-1", ElementType.TITLE, "文档标题", level=1),
            self._create_element("para-1", ElementType.PARAGRAPH, "这是正文内容"),
            self._create_element("table-1", ElementType.TABLE, "表1"),
        ]

        # 设置表格结构
        table_element = elements[2]
        table_element.table_structure = {
            "headers": [["列1", "列2"]],
            "rows": [["数据1", "数据2"]] * 100,  # 长表格
            "caption": "测试表格"
        }

        config = ChunkConfigRequest()
        cleaned_map = {}

        chunks = self.service._split_mixed(elements, cleaned_map, config)

        # 验证表格被正确处理
        table_chunks = [c for c in chunks if c.chunk_type == "table"]
        assert len(table_chunks) >= 1


class TestChunkConfig:
    """切分配置测试"""

    def test_default_config(self):
        """测试默认配置"""
        config = ChunkConfigRequest()

        assert config.target_tokens == 600
        assert config.max_tokens == 900
        assert config.min_tokens == 120
        assert config.overlap_tokens == 100
        assert config.semantic_threshold == 0.85

    def test_custom_config(self):
        """测试自定义配置"""
        config = ChunkConfigRequest(
            target_tokens=500,
            max_tokens=800,
            min_tokens=100,
            overlap_tokens=80,
            split_by_title=False
        )

        assert config.target_tokens == 500
        assert config.max_tokens == 800
        assert config.split_by_title is False

    def test_config_validation(self):
        """测试配置验证"""
        # 正常范围应该通过
        config = ChunkConfigRequest(target_tokens=1000)
        assert config.target_tokens == 1000

        # 注意：Pydantic的ge/le约束会在这里生效
        # 如果超过限制会抛出验证错误


class TestChunkElement:
    """Chunk元素测试"""

    def test_chunk_element_creation(self):
        """测试Chunk元素创建"""
        from app.schemas.chunk import ChunkElement

        chunk = ChunkElement(
            chunk_id="test-001",
            chunk_index=0,
            content="测试内容",
            chunk_type="paragraph",
            token_count=10,
            char_count=5,
            element_ids=["elem-1"]
        )

        assert chunk.chunk_id == "test-001"
        assert chunk.token_count == 10
        assert chunk.has_previous_overlap is False
        assert chunk.has_next_overlap is False

    def test_chunk_element_with_overlap(self):
        """测试带Overlap的Chunk元素"""
        from app.schemas.chunk import ChunkElement

        chunk = ChunkElement(
            chunk_id="test-002",
            chunk_index=1,
            content="第二段内容",
            chunk_type="paragraph",
            token_count=10,
            char_count=5,
            has_previous_overlap=True,
            overlap_with_previous="前一段的结尾"
        )

        assert chunk.has_previous_overlap is True
        assert chunk.overlap_with_previous == "前一段的结尾"

    def _create_element(
        self,
        element_id: str,
        element_type: ElementType,
        content: str,
        level: int = None
    ) -> DocumentElement:
        """创建测试用元素"""
        element = MagicMock(spec=DocumentElement)
        element.element_id = element_id
        element.element_type = element_type.value
        element.content = content
        element.title_level = level
        element.title_path = None
        element.page_no = 1
        element.table_structure = None
        element.image_description = None
        element.confidence = 0.9
        return element
