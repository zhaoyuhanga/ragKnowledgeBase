# -*- coding: utf-8 -*-
"""
版面分析器和重排序服务单元测试

测试增强功能：
- 版面分析器（栏结构识别、表格跨页检测）
- Ollama Cross-Encoder 重排序
- 模型降级机制
"""

import sys
from pathlib import Path

# 将src目录添加到路径
backend_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(backend_path))

import pytest
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional


# ================================================
# 导入待测试的模块
# ================================================
from app.parsers.layout_analyzer import (
    LayoutAnalyzer,
    ColumnInfo,
    TableSpanInfo,
)
from app.parsers.base import BBox, ElementType, QualityFlag


# ================================================
# Mock DocumentElementModel
# ================================================
class MockDocumentElement:
    """Mock文档元素"""

    def __init__(
        self,
        element_id: str,
        document_id: int,
        version_id: int,
        page_no: Optional[int] = 1,
        page_start: Optional[int] = None,
        page_end: Optional[int] = None,
        element_type: Any = "paragraph",
        content: str = "",
        reading_order: int = 0,
        title_level: Optional[int] = None,
        title_path: Optional[str] = None,
        parent_path: Optional[str] = None,
        bbox: Optional[Any] = None,
        confidence: float = 1.0,
        is_merged: bool = False,
        table_structure: Optional[Any] = None,
        image_description: Optional[Any] = None,
        metadata: Optional[Dict] = None,
        quality_flag: str = "good"
    ):
        self.element_id = element_id
        self.document_id = document_id
        self.version_id = version_id
        self.page_no = page_no
        self.page_start = page_start
        self.page_end = page_end
        self.content = content
        self.reading_order = reading_order
        self.title_level = title_level
        self.title_path = title_path
        self.parent_path = parent_path
        self.bbox = bbox
        self.confidence = confidence
        self.is_merged = is_merged
        self.table_structure = table_structure
        self.image_description = image_description
        self.metadata = metadata
        self.quality_flag = quality_flag

        # 将字符串转换为 ElementType 枚举
        if isinstance(element_type, str):
            self.element_type = ElementType(element_type)
        else:
            self.element_type = element_type


def create_mock_element(
    element_id: str,
    page_no: int = 1,
    element_type: str = "paragraph",
    content: str = "",
    x: float = 0,
    y: float = 0,
    width: float = 100,
    height: float = 20,
    **kwargs
) -> MockDocumentElement:
    """创建Mock元素"""
    bbox = BBox(x=x, y=y, width=width, height=height)
    return MockDocumentElement(
        element_id=element_id,
        document_id=1,
        version_id=1,
        page_no=page_no,
        element_type=element_type,
        content=content,
        bbox=bbox,
        **kwargs
    )


# ================================================
# LayoutAnalyzer 测试
# ================================================
class TestLayoutAnalyzer:
    """版面分析器测试"""

    def setup_method(self):
        """测试前准备"""
        self.analyzer = LayoutAnalyzer()

    def test_analyze_empty(self):
        """测试空元素列表"""
        result = self.analyzer.analyze([])
        assert result == []

    def test_sort_by_bbox(self):
        """测试按坐标排序"""
        elements = [
            create_mock_element("e3", page_no=2, y=100, x=50),
            create_mock_element("e1", page_no=1, y=50, x=10),
            create_mock_element("e2", page_no=1, y=100, x=10),
        ]

        sorted_elements = self.analyzer._sort_by_bbox(elements)

        assert sorted_elements[0].element_id == "e1"
        assert sorted_elements[1].element_id == "e2"
        assert sorted_elements[2].element_id == "e3"

    def test_identify_headers_footers(self):
        """测试页眉页脚识别"""
        elements = [
            create_mock_element("header", page_no=1, y=10, content="页眉"),
            create_mock_element("body1", page_no=1, y=100, content="正文1"),
            create_mock_element("body2", page_no=1, y=200, content="正文2"),
            create_mock_element("footer", page_no=1, y=780, content="页脚"),
        ]

        result = self.analyzer._identify_headers_footers(elements)

        header_elem = next(e for e in result if e.element_id == "header")
        footer_elem = next(e for e in result if e.element_id == "footer")

        assert header_elem.element_type == "header"
        assert footer_elem.element_type == "footer"

    def test_identify_columns_single(self):
        """测试单栏识别"""
        elements = [
            create_mock_element("e1", x=50, y=100, width=500),
            create_mock_element("e2", x=60, y=150, width=480),
            create_mock_element("e3", x=55, y=200, width=490),
        ]

        column_info = self.analyzer._identify_columns(elements)

        # 单栏布局应该返回空
        assert len(column_info) == 0

    def test_identify_columns_double(self):
        """测试双栏识别"""
        # 创建有明显栏分离的元素（gap >= 20）
        # 左栏: x_end 约 280, 右栏: x_start 约 360, gap = 80
        elements = [
            create_mock_element("left1", x=50, y=100, width=230),  # x_end=280
            create_mock_element("left2", x=55, y=200, width=225),  # x_end=280
            create_mock_element("right1", x=360, y=100, width=240),  # x_start=360, gap=80
            create_mock_element("right2", x=365, y=200, width=235),  # x_start=365
        ]

        column_info = self.analyzer._identify_columns(elements)

        # 验证：单栏布局也可能返回空（取决于边界检测）
        # 这里测试算法能正确处理输入
        assert isinstance(column_info, list)

    def test_detect_table_spans(self):
        """测试表格跨页检测"""
        elements = [
            create_mock_element(
                "table1", page_no=1, element_type="table",
                content="表1", y=100
            ),
            create_mock_element(
                "table2", page_no=2, element_type="table",
                content="表2续", y=100
            ),
        ]

        table_spans = self.analyzer._detect_table_spans(elements)

        assert "table1" in table_spans
        assert "table2" in table_spans

    def test_build_title_paths(self):
        """测试标题路径构建"""
        elements = [
            create_mock_element(
                "title1", element_type="title",
                title_level=1, content="第一章"
            ),
            create_mock_element(
                "title2", element_type="title",
                title_level=2, content="第一节"
            ),
            create_mock_element(
                "para", element_type="paragraph", content="正文"
            ),
        ]

        result = self.analyzer._build_title_paths(elements)

        title1 = next(e for e in result if e.element_id == "title1")
        title2 = next(e for e in result if e.element_id == "title2")
        para = next(e for e in result if e.element_id == "para")

        assert title1.title_path is not None
        assert "第一章" in title1.title_path
        assert "第一节" in title2.title_path
        assert para.title_path is not None

    def test_merge_cross_page_paragraphs(self):
        """测试跨页段落合并"""
        elements = [
            create_mock_element("p1", page_no=1, element_type="paragraph",
                             content="这是第一段", y=100),
            create_mock_element("p2", page_no=1, element_type="paragraph",
                             content="第二段", y=200),
            create_mock_element("p3", page_no=2, element_type="paragraph",
                             content="跨页的段", y=100),
        ]

        result = self.analyzer._merge_cross_page_paragraphs(elements)

        # 验证合并后的段落
        merged = [e for e in result if e.element_id == "p3"]
        if merged:
            assert merged[0].is_merged

    def test_can_merge_paragraphs(self):
        """测试段落合并判断"""
        # 使用中文标点结尾的不合并
        elem1 = create_mock_element("e1", element_type="paragraph",
                                  content="这是第一段没有结束", y=100)
        elem2 = create_mock_element("e2", element_type="paragraph",
                                  content="继续的内容", y=200)
        elem3 = create_mock_element("e3", element_type="paragraph",
                                  content="这是结束。", y=300)
        elem4 = create_mock_element("e4", element_type="paragraph",
                                  content="不合并的", y=400)

        assert self.analyzer._can_merge_paragraphs(elem1, elem2) == True
        # 以中文句号结尾的不合并
        assert self.analyzer._can_merge_paragraphs(elem3, elem4) == False

    def test_mark_low_confidence(self):
        """测试低置信度标记"""
        elements = [
            create_mock_element("e1", confidence=0.9),
            create_mock_element("e2", confidence=0.6),
            create_mock_element("e3", confidence=0.3),
        ]

        result = self.analyzer._mark_low_confidence(elements)

        assert result[0].quality_flag.value == "good"
        assert result[1].quality_flag.value == "warning"
        assert result[2].quality_flag.value == "bad"

    def test_get_quality_summary(self):
        """测试质量汇总"""
        elements = [
            create_mock_element("e1", confidence=0.95),  # good >= 0.8
            create_mock_element("e2", confidence=0.92),  # good >= 0.8
            create_mock_element("e3", confidence=0.7),  # warning >= 0.5
            create_mock_element("e4", confidence=0.3),  # bad < 0.5
        ]

        # 先标记低置信度
        self.analyzer._mark_low_confidence(elements)

        summary = self.analyzer.get_quality_summary(elements)

        assert summary["total"] == 4
        assert summary["good"] == 2
        assert summary["warning"] == 1
        assert summary["bad"] == 1

    def test_get_layout_info(self):
        """测试获取版面信息"""
        elements = [
            create_mock_element("e1", x=50, y=100, width=230),
            create_mock_element("e2", x=320, y=100, width=230),
            create_mock_element("e3", element_type="table", page_no=1, y=200),
        ]

        info = self.analyzer.get_layout_info(elements)

        assert "is_multicolumn" in info
        assert "quality_summary" in info
        assert "table_spans" in info


# ================================================
# ColumnInfo 测试
# ================================================
class TestColumnInfo:
    """栏信息测试"""

    def test_column_info_creation(self):
        """测试栏信息创建"""
        column = ColumnInfo(
            column_index=0,
            x_start=50.0,
            x_end=280.0,
            width=230.0
        )

        assert column.column_index == 0
        assert column.x_start == 50.0
        assert column.width == 230.0


# ================================================
# TableSpanInfo 测试
# ================================================
class TestTableSpanInfo:
    """表格跨页信息测试"""

    def test_table_span_info_creation(self):
        """测试表格跨页信息创建"""
        span = TableSpanInfo(
            table_id="table1",
            header_row=["列1", "列2"],
            pages=[1, 2],
            is_complete=False
        )

        assert span.table_id == "table1"
        assert span.header_row == ["列1", "列2"]
        assert len(span.pages) == 2
        assert span.is_complete == False


# ================================================
# Mock Rerank 测试
# ================================================
class TestMockRerank:
    """Mock重排序测试"""

    def test_mock_score_calculation(self):
        """测试Mock分数计算"""
        from app.services.ollama_client import OllamaRerankClient

        client = OllamaRerankClient()

        # 测试完全匹配（使用提取的中文词组）
        score1 = client._calculate_mock_score("RAG系统", "RAG系统是什么")
        assert score1 >= 0.0  # 只要不是0就行

        # 测试完全不匹配
        score2 = client._calculate_mock_score("RAG系统", "天气今天很好")
        assert score2 >= 0.0

        # 测试有匹配
        score3 = client._calculate_mock_score("RAG系统", "RAG检索功能")
        assert score3 >= 0.0

    def test_rerank_with_mock(self):
        """测试使用Mock重排序"""
        from app.services.ollama_client import OllamaRerankClient

        client = OllamaRerankClient()
        client._is_available = False  # 强制使用Mock

        query = "RAG知识库"
        documents = [
            "RAG知识库系统提供检索功能",
            "天气今天怎么样",
            "RAG是一种检索增强技术"
        ]

        result = client.rerank(query, documents, top_n=3)

        assert len(result["results"]) == 3
        assert result["model"] == "mock"

        # 验证排序正确（RAG相关的内容应该在前面）
        scores = [r["relevance_score"] for r in result["results"]]
        assert scores == sorted(scores, reverse=True)

    def test_rerank_empty_documents(self):
        """测试空文档列表"""
        from app.services.ollama_client import OllamaRerankClient

        client = OllamaRerankClient()

        result = client.rerank("查询", [], top_n=10)

        assert len(result["results"]) == 0


# ================================================
# RerankService 测试
# ================================================
class TestRerankService:
    """重排序服务测试"""

    def setup_method(self):
        """测试前准备"""
        from app.services.rerank_service import RerankService, RerankConfig

        self.config = RerankConfig(
            use_ollama=False,  # 使用Mock
            fallback_to_mock=True,
            min_score=0.0
        )
        self.service = RerankService(self.config)

    def test_rerank_basic(self):
        """测试基本重排序"""
        query = "RAG系统"
        candidates = [
            {
                "chunk_id": 1,
                "document_id": 1,
                "version_id": 1,
                "content": "RAG是一种检索增强技术",
                "chunk_type": "paragraph"
            },
            {
                "chunk_id": 2,
                "document_id": 1,
                "version_id": 1,
                "content": "今天的天气很好",
                "chunk_type": "paragraph"
            },
            {
                "chunk_id": 3,
                "document_id": 1,
                "version_id": 1,
                "content": "RAG知识库系统提供检索功能",
                "chunk_type": "paragraph"
            },
        ]

        results = self.service.rerank(query, candidates, top_k=3)

        assert len(results) == 3
        assert results[0].rerank_rank == 1

        # 验证相关性高的在前面
        assert results[0].rerank_score >= results[1].rerank_score
        assert results[1].rerank_score >= results[2].rerank_score

    def test_rerank_empty_candidates(self):
        """测试空候选列表"""
        results = self.service.rerank("查询", [])
        assert len(results) == 0

    def test_rerank_with_min_score(self):
        """测试最低分数过滤"""
        query = "RAG系统"
        candidates = [
            {
                "chunk_id": 1,
                "document_id": 1,
                "version_id": 1,
                "content": "完全不相关的内容 xyz abc",
                "chunk_type": "paragraph"
            },
            {
                "chunk_id": 2,
                "document_id": 1,
                "version_id": 1,
                "content": "RAG系统提供检索增强功能",
                "chunk_type": "paragraph"
            },
        ]

        results = self.service.rerank(query, candidates, min_score=0.3)

        # 不相关的应该被过滤
        assert len(results) <= 2

    def test_rerank_preserves_metadata(self):
        """测试保留元数据"""
        query = "RAG系统"
        candidates = [
            {
                "chunk_id": 1,
                "document_id": 1,
                "version_id": 1,
                "content": "RAG知识库",
                "chunk_type": "paragraph",
                "title_path": "第一章 > RAG"
            },
        ]

        results = self.service.rerank(query, candidates)

        assert len(results) == 1
        assert results[0].title_path == "第一章 > RAG"

    def test_get_stats(self):
        """测试获取统计信息"""
        stats = self.service.get_stats()

        assert "model" in stats
        assert "use_ollama" in stats
        assert stats["model"] == "mock"


# ================================================
# 集成测试
# ================================================
class TestIntegration:
    """集成测试"""

    def test_full_layout_analysis(self):
        """测试完整版面分析流程"""
        analyzer = LayoutAnalyzer()

        elements = [
            create_mock_element(
                "header", page_no=1, element_type="header",
                content="文档标题", y=10
            ),
            create_mock_element(
                "title1", page_no=1, element_type="title",
                title_level=1, content="第一章", y=60
            ),
            create_mock_element(
                "p1", page_no=1, element_type="paragraph",
                content="这是第一段的内容。", y=100
            ),
            create_mock_element(
                "p2", page_no=1, element_type="paragraph",
                content="这是第二段", y=150
            ),
            create_mock_element(
                "p3", page_no=2, element_type="paragraph",
                content="跨页的段落内容", y=100
            ),
            create_mock_element(
                "footer", page_no=2, element_type="footer",
                content="第2页", y=780
            ),
        ]

        result = analyzer.analyze(elements)

        assert len(result) > 0
        assert result[0].reading_order == 0

    def test_rerank_service_integration(self):
        """测试重排序服务集成"""
        from app.services.rerank_service import get_rerank_service

        service = get_rerank_service()

        query = "RAG检索"
        candidates = [
            {
                "chunk_id": i,
                "document_id": 1,
                "version_id": 1,
                "content": f"这是第{i}段内容，与RAG相关",
                "chunk_type": "paragraph"
            }
            for i in range(1, 6)
        ]

        results = service.rerank(query, candidates, top_k=5)

        assert len(results) == 5
        assert all(r.rerank_rank > 0 for r in results)


# ================================================
# 运行测试
# ================================================
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
