# -*- coding: utf-8 -*-
"""
图片解析器测试

测试图片解析器的 OCR 和视觉模型集成功能。
"""

import io
import os
import pytest
from unittest.mock import Mock, patch, MagicMock

from app.parsers.image_parser import ImageParser
from app.parsers.base import ImageDescription, ElementType, QualityFlag


class TestImageParserInit:
    """图片解析器初始化测试"""

    def test_parser_init(self):
        """测试解析器初始化"""
        parser = ImageParser()
        assert parser is not None
        assert len(parser.supported_extensions) > 0

    def test_supported_extensions(self):
        """测试支持的扩展名"""
        parser = ImageParser()
        expected_extensions = ["png", "jpg", "jpeg", "gif", "bmp", "tiff"]

        for ext in expected_extensions:
            assert ext in parser.supported_extensions

    def test_can_parse(self):
        """测试文件类型判断"""
        parser = ImageParser()

        assert parser.can_parse("test.png") is True
        assert parser.can_parse("test.jpg") is True
        assert parser.can_parse("test.jpeg") is True
        assert parser.can_parse("test.pdf") is False
        assert parser.can_parse("test.docx") is False


class TestImageParserPreprocess:
    """图像预处理测试"""

    def test_preprocess_returns_dict(self):
        """测试预处理返回字典"""
        parser = ImageParser()

        # 创建一个简单的测试图片
        from PIL import Image
        img = Image.new("RGB", (100, 100), color="red")
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        image_bytes = buffer.getvalue()

        result = parser._preprocess_image(image_bytes)

        assert isinstance(result, dict)
        assert "original" in result


class TestImageParserOCR:
    """OCR 测试"""

    def test_ocr_returns_tuple(self):
        """测试 OCR 返回元组"""
        parser = ImageParser()

        # 模拟预处理结果
        processed_image = {"original": b"fake image data"}

        with patch.object(parser, "_perform_ocr") as mock_ocr:
            mock_ocr.return_value = ("识别文字", 0.85)
            text, confidence = parser._perform_ocr(processed_image)

            assert isinstance(text, str)
            assert isinstance(confidence, float)

    def test_ocr_fallback(self):
        """测试 OCR 降级处理"""
        parser = ImageParser()

        # 没有 OCR 库时的降级处理
        processed_image = {"original": b"fake image data"}

        # 模拟所有 OCR 库都不可用
        with patch.dict("sys.modules", {"pytesseract": None, "easyocr": None}):
            text, confidence = parser._perform_ocr(processed_image)

            assert text == ""
            assert confidence == 0.0


class TestImageParserDescription:
    """图片描述测试"""

    def test_generate_description_returns_object(self):
        """测试描述生成返回对象"""
        parser = ImageParser()

        image_bytes = b"fake image data"

        # 模拟视觉模型客户端
        mock_description = ImageDescription(
            description="测试图片",
            confidence=0.9
        )

        with patch.object(parser, "_get_vision_client") as mock_get_client:
            mock_client = Mock()
            mock_client.describe.return_value = mock_description
            mock_client.health_check.return_value = True
            mock_get_client.return_value = mock_client

            with patch("core.config.settings") as mock_settings:
                mock_settings.vision.enabled = True

                description = parser._generate_description(image_bytes)

                assert isinstance(description, ImageDescription)
                assert description.description == "测试图片"

    def test_generate_description_disabled(self):
        """测试视觉模型禁用时返回默认描述"""
        parser = ImageParser()

        image_bytes = b"fake image data"

        with patch("core.config.settings") as mock_settings:
            mock_settings.vision.enabled = False

            description = parser._generate_description(image_bytes)

            assert isinstance(description, ImageDescription)
            assert description.description == "图片"
            assert description.confidence == 0.5

    def test_generate_description_service_unavailable(self):
        """测试服务不可用时返回默认描述"""
        parser = ImageParser()

        image_bytes = b"fake image data"

        with patch.object(parser, "_get_vision_client") as mock_get_client:
            mock_client = Mock()
            mock_client.health_check.return_value = False
            mock_get_client.return_value = mock_client

            with patch("core.config.settings") as mock_settings:
                mock_settings.vision.enabled = True

                description = parser._generate_description(image_bytes)

                assert isinstance(description, ImageDescription)
                assert description.description == "图片"
                assert description.confidence == 0.5

    def test_generate_description_with_chart_type(self):
        """测试图表类型识别"""
        parser = ImageParser()

        image_bytes = b"fake image data"

        mock_description = ImageDescription(
            description="柱状图展示季度销售数据",
            chart_type="柱状图",
            chart_data_summary="Q1:100, Q2:150, Q3:200, Q4:180",
            semantic_tags=["销售", "季度", "柱状图"],
            confidence=0.95
        )

        with patch.object(parser, "_get_vision_client") as mock_get_client:
            mock_client = Mock()
            mock_client.describe.return_value = mock_description
            mock_client.health_check.return_value = True
            mock_get_client.return_value = mock_client

            with patch("core.config.settings") as mock_settings:
                mock_settings.vision.enabled = True

                description = parser._generate_description(image_bytes)

                assert description.chart_type == "柱状图"
                assert "Q1" in description.chart_data_summary
                assert "销售" in description.semantic_tags


class TestImageParserQualityFlag:
    """质量标记测试"""

    def test_quality_flag_good(self):
        """测试高质量标记"""
        parser = ImageParser()

        flag = parser._get_quality_flag(0.9)
        assert flag == QualityFlag.GOOD

        flag = parser._get_quality_flag(0.8)
        assert flag == QualityFlag.GOOD

    def test_quality_flag_warning(self):
        """测试警告质量标记"""
        parser = ImageParser()

        flag = parser._get_quality_flag(0.7)
        assert flag == QualityFlag.WARNING

        flag = parser._get_quality_flag(0.5)
        assert flag == QualityFlag.WARNING

    def test_quality_flag_bad(self):
        """测试低质量标记"""
        parser = ImageParser()

        flag = parser._get_quality_flag(0.4)
        assert flag == QualityFlag.BAD

        flag = parser._get_quality_flag(0.1)
        assert flag == QualityFlag.BAD


class TestImageParserParse:
    """解析功能测试"""

    def test_parse_returns_list(self):
        """测试解析返回列表"""
        parser = ImageParser()

        # 创建一个临时测试图片
        from PIL import Image
        img = Image.new("RGB", (100, 100), color="blue")
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        image_bytes = buffer.getvalue()

        # 写入临时文件
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            f.write(image_bytes)
            temp_path = f.name

        try:
            # 模拟视觉模型
            mock_description = ImageDescription(
                description="蓝色测试图片",
                confidence=0.85
            )

            with patch.object(parser, "_generate_description", return_value=mock_description):
                with patch.object(parser, "_perform_ocr", return_value=("", 0.0)):
                    elements = parser.parse(temp_path, version_id=1, document_id=1)

                    assert isinstance(elements, list)
                    if elements:
                        element = elements[0]
                        assert element.element_type == ElementType.IMAGE
                        assert element.image_description is not None
        finally:
            os.unlink(temp_path)

    def test_parse_error_handling(self):
        """测试解析错误处理"""
        parser = ImageParser()

        # 使用不存在的文件
        elements = parser.parse("/nonexistent/file.png", version_id=1, document_id=1)

        assert isinstance(elements, list)
        assert len(elements) == 0


class TestImageParserVisionClient:
    """视觉模型客户端集成测试"""

    def test_get_vision_client_lazy_load(self):
        """测试视觉模型客户端懒加载"""
        parser = ImageParser()

        # 初始状态没有客户端
        assert parser._vision_client is None

        # 获取客户端
        with patch("app.services.vision_client.get_vision_client") as mock_get:
            mock_client = Mock()
            mock_get.return_value = mock_client

            client = parser._get_vision_client()

            assert client is mock_client
            # 应该被缓存
            assert parser._vision_client is mock_client

    def test_vision_client_multiple_calls_same_instance(self):
        """测试多次调用返回同一实例"""
        parser = ImageParser()

        with patch("app.services.vision_client.get_vision_client") as mock_get:
            mock_client = Mock()
            mock_get.return_value = mock_client

            client1 = parser._get_vision_client()
            client2 = parser._get_vision_client()

            assert client1 is client2
            assert client1 is mock_client
