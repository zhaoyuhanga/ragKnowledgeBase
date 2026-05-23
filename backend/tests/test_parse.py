# -*- coding: utf-8 -*-
"""
解析服务测试模块

本模块提供文档解析服务的测试用例。
"""

import os
import sys
import tempfile
from typing import List
from unittest.mock import MagicMock, patch

import pytest

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


class TestElementType:
    """元素类型枚举测试"""

    def test_element_types(self):
        """测试元素类型定义"""
        from app.parsers.base import ElementType

        assert ElementType.TITLE.value == "title"
        assert ElementType.PARAGRAPH.value == "paragraph"
        assert ElementType.TABLE.value == "table"
        assert ElementType.IMAGE.value == "image"
        assert ElementType.CHART.value == "chart"
        assert ElementType.LIST.value == "list"
        assert ElementType.CODE.value == "code"
        assert ElementType.HEADER.value == "header"
        assert ElementType.FOOTER.value == "footer"


class TestDocumentElementModel:
    """文档元素模型测试"""

    def test_create_element(self):
        """测试创建文档元素"""
        from app.parsers.base import DocumentElementModel, ElementType

        element = DocumentElementModel(
            element_id="test-id-1",
            document_id=1,
            version_id=1,
            element_type=ElementType.PARAGRAPH,
            content="测试内容"
        )

        assert element.element_id == "test-id-1"
        assert element.document_id == 1
        assert element.version_id == 1
        assert element.element_type == ElementType.PARAGRAPH
        assert element.content == "测试内容"
        assert element.confidence == 1.0

    def test_generate_id(self):
        """测试自动生成ID"""
        from app.parsers.base import DocumentElementModel, ElementType

        element = DocumentElementModel(
            document_id=1,
            version_id=1,
            element_type=ElementType.PARAGRAPH
        )

        assert element.element_id is None
        element.generate_id()
        assert element.element_id is not None
        assert len(element.element_id) == 36  # UUID格式

    def test_to_dict(self):
        """测试转换为字典"""
        from app.parsers.base import DocumentElementModel, ElementType

        element = DocumentElementModel(
            element_id="test-id-1",
            document_id=1,
            version_id=1,
            element_type=ElementType.PARAGRAPH,
            content="测试内容"
        )

        data = element.to_dict()

        assert data["element_id"] == "test-id-1"
        assert data["document_id"] == 1
        assert data["element_type"] == "paragraph"
        assert data["content"] == "测试内容"

    def test_from_dict(self):
        """测试从字典创建"""
        from app.parsers.base import DocumentElementModel, ElementType

        data = {
            "element_id": "test-id-1",
            "document_id": 1,
            "version_id": 1,
            "element_type": "paragraph",
            "content": "测试内容"
        }

        element = DocumentElementModel.from_dict(data)

        assert element.element_id == "test-id-1"
        assert element.document_id == 1
        assert element.element_type == ElementType.PARAGRAPH


class TestTableStructure:
    """表格结构测试"""

    def test_to_text(self):
        """测试表格转文本"""
        from app.parsers.base import TableStructure

        table = TableStructure(
            headers=[["姓名", "年龄", "职业"]],
            rows=[
                ["张三", "25", "工程师"],
                ["李四", "30", "设计师"]
            ],
            row_count=3,
            col_count=3
        )

        text = table.to_text()
        assert "姓名" in text
        assert "张三" in text
        assert "李四" in text


class TestImageDescription:
    """图片描述测试"""

    def test_create_description(self):
        """测试创建图片描述"""
        from app.parsers.base import ImageDescription

        desc = ImageDescription(
            description="这是一张风景图",
            chart_type="风景",
            semantic_tags=["自然", "户外"]
        )

        assert desc.description == "这是一张风景图"
        assert desc.chart_type == "风景"
        assert "自然" in desc.semantic_tags


class TestParserRegistry:
    """解析器注册表测试"""

    def test_register_and_get(self):
        """测试注册和获取解析器"""
        from app.parsers.base import ParserRegistry, BaseParser

        registry = ParserRegistry()

        # 创建mock解析器
        mock_parser = MagicMock(spec=BaseParser)

        # 注册
        registry.register("pdf", mock_parser)

        # 获取
        parser = registry.get_parser("/path/to/test.pdf")
        assert parser is mock_parser

    def test_get_parser_not_found(self):
        """测试获取不存在的解析器"""
        from app.parsers.base import ParserRegistry

        registry = ParserRegistry()
        parser = registry.get_parser("/path/to/test.unknown")
        assert parser is None

    def test_list_parsers(self):
        """测试列出所有解析器"""
        from app.parsers.base import ParserRegistry, BaseParser

        registry = ParserRegistry()

        mock_parser1 = MagicMock(spec=BaseParser)
        mock_parser2 = MagicMock(spec=BaseParser)

        registry.register("pdf", mock_parser1)
        registry.register("docx", mock_parser2)

        parsers = registry.list_parsers()
        assert "pdf" in parsers
        assert "docx" in parsers


class TestWordParser:
    """Word文档解析器测试"""

    def test_can_parse(self):
        """测试文件类型判断"""
        from app.parsers.word_parser import WordParser

        parser = WordParser()
        assert parser.can_parse("test.docx") is True
        assert parser.can_parse("test.doc") is True
        assert parser.can_parse("test.pdf") is False

    def test_supported_extensions(self):
        """测试支持的扩展名"""
        from app.parsers.word_parser import WordParser

        parser = WordParser()
        assert "docx" in parser.supported_extensions
        assert "doc" in parser.supported_extensions


class TestPdfParser:
    """PDF文档解析器测试"""

    def test_can_parse(self):
        """测试文件类型判断"""
        from app.parsers.pdf_parser import PdfParser

        parser = PdfParser()
        assert parser.can_parse("test.pdf") is True
        assert parser.can_parse("test.docx") is False

    def test_is_scanned_pdf_logic(self):
        """测试扫描版PDF判断逻辑"""
        from app.parsers.pdf_parser import PdfParser

        parser = PdfParser()
        # 阈值默认为0.5
        assert parser._ocr_threshold == 0.5


class TestImageParser:
    """图片解析器测试"""

    def test_can_parse(self):
        """测试文件类型判断"""
        from app.parsers.image_parser import ImageParser

        parser = ImageParser()
        assert parser.can_parse("test.png") is True
        assert parser.can_parse("test.jpg") is True
        assert parser.can_parse("test.jpeg") is True
        assert parser.can_parse("test.pdf") is False

    def test_quality_flag(self):
        """测试质量标记"""
        from app.parsers.image_parser import ImageParser
        from app.parsers.base import QualityFlag

        parser = ImageParser()

        assert parser._get_quality_flag(0.9) == QualityFlag.GOOD
        assert parser._get_quality_flag(0.6) == QualityFlag.WARNING
        assert parser._get_quality_flag(0.3) == QualityFlag.BAD


class TestTableParser:
    """表格解析器测试"""

    def test_can_parse(self):
        """测试文件类型判断"""
        from app.parsers.table_parser import TableParser

        parser = TableParser()
        assert parser.can_parse("test.xlsx") is True
        assert parser.can_parse("test.xls") is True
        assert parser.can_parse("test.csv") is True
        assert parser.can_parse("test.pdf") is False


class TestTextParser:
    """文本解析器测试"""

    def test_can_parse(self):
        """测试文件类型判断"""
        from app.parsers.text_parser import TextParser

        parser = TextParser()
        assert parser.can_parse("test.txt") is True
        assert parser.can_parse("test.md") is True
        assert parser.can_parse("test.html") is True
        assert parser.can_parse("test.pdf") is False


class TestLayoutAnalyzer:
    """版面分析器测试"""

    def test_mark_low_confidence(self):
        """测试低置信度标记"""
        from app.parsers.layout_analyzer import LayoutAnalyzer
        from app.parsers.base import DocumentElementModel, ElementType, QualityFlag

        analyzer = LayoutAnalyzer()

        elements = [
            DocumentElementModel(
                element_id="1", document_id=1, version_id=1,
                element_type=ElementType.PARAGRAPH, confidence=0.9
            ),
            DocumentElementModel(
                element_id="2", document_id=1, version_id=1,
                element_type=ElementType.PARAGRAPH, confidence=0.6
            ),
            DocumentElementModel(
                element_id="3", document_id=1, version_id=1,
                element_type=ElementType.PARAGRAPH, confidence=0.3
            )
        ]

        result = analyzer._mark_low_confidence(elements)

        assert result[0].quality_flag == QualityFlag.GOOD
        assert result[1].quality_flag == QualityFlag.WARNING
        assert result[2].quality_flag == QualityFlag.BAD

    def test_get_quality_summary(self):
        """测试质量汇总"""
        from app.parsers.layout_analyzer import LayoutAnalyzer
        from app.parsers.base import DocumentElementModel, ElementType, QualityFlag

        analyzer = LayoutAnalyzer()

        elements = [
            DocumentElementModel(
                element_id="1", document_id=1, version_id=1,
                element_type=ElementType.PARAGRAPH, quality_flag=QualityFlag.GOOD
            ),
            DocumentElementModel(
                element_id="2", document_id=1, version_id=1,
                element_type=ElementType.PARAGRAPH, quality_flag=QualityFlag.GOOD
            ),
            DocumentElementModel(
                element_id="3", document_id=1, version_id=1,
                element_type=ElementType.PARAGRAPH, quality_flag=QualityFlag.WARNING
            )
        ]

        summary = analyzer.get_quality_summary(elements)

        assert summary["total"] == 3
        assert summary["good"] == 2
        assert summary["warning"] == 1
        assert summary["bad"] == 0

    def test_sort_by_bbox(self):
        """测试按坐标排序"""
        from app.parsers.layout_analyzer import LayoutAnalyzer
        from app.parsers.base import DocumentElementModel, ElementType, BBox

        analyzer = LayoutAnalyzer()

        elements = [
            DocumentElementModel(
                element_id="1", document_id=1, version_id=1,
                page_no=2, element_type=ElementType.PARAGRAPH,
                bbox=BBox(x=100, y=200, width=50, height=20)
            ),
            DocumentElementModel(
                element_id="2", document_id=1, version_id=1,
                page_no=1, element_type=ElementType.PARAGRAPH,
                bbox=BBox(x=50, y=100, width=50, height=20)
            ),
            DocumentElementModel(
                element_id="3", document_id=1, version_id=1,
                page_no=1, element_type=ElementType.PARAGRAPH,
                bbox=BBox(x=50, y=200, width=50, height=20)
            )
        ]

        result = analyzer._sort_by_bbox(elements)

        # 应该按页码、Y坐标排序
        assert result[0].element_id == "2"  # page=1, y=100
        assert result[1].element_id == "3"  # page=1, y=200
        assert result[2].element_id == "1"  # page=2


class TestParseService:
    """解析服务测试"""

    @patch("app.services.parse_service.SessionLocal")
    def test_get_status_not_found(self, mock_session):
        """测试获取不存在的文档状态"""
        from app.services.parse_service import ParseService
        from app.common.exception import BusinessException

        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        mock_db.query.return_value = mock_query
        mock_session.return_value = mock_db

        service = ParseService()

        with pytest.raises(BusinessException) as exc_info:
            service.get_parse_status(999)

        assert "文档不存在" in str(exc_info.value.message)


class TestParseAPI:
    """解析API测试"""

    def test_parse_service_instance(self):
        """测试获取解析服务实例"""
        from app.services.parse_service import get_parse_service

        service1 = get_parse_service()
        service2 = get_parse_service()

        # 应该是单例
        assert service1 is service2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
