# -*- coding: utf-8 -*-
"""
视觉模型客户端测试

测试 Ollama 视觉模型客户端和图片描述生成功能。
"""

import io
import base64
import json
import pytest
from unittest.mock import Mock, patch, MagicMock

from app.services.vision_client import VisionClient, get_vision_client
from app.parsers.base import ImageDescription


class TestVisionClientInit:
    """视觉模型客户端初始化测试"""

    def test_vision_client_init(self):
        """测试视觉模型客户端初始化"""
        client = VisionClient()
        assert client._host is not None
        assert client._model_name is not None
        assert client._timeout > 0
        assert client._retry_times > 0

    def test_vision_client_default_config(self):
        """测试默认配置"""
        client = VisionClient()
        assert "localhost" in client._host or "11434" in str(client._timeout)
        assert "qwen" in client._model_name.lower() or "llava" in client._model_name.lower()

    def test_vision_client_custom_config(self):
        """测试自定义配置"""
        client = VisionClient(
            host="http://custom-host:11434",
            model_name="llava:latest",
            timeout=300,
            retry_times=5
        )
        assert client._host == "http://custom-host:11434"
        assert client._model_name == "llava:latest"
        assert client._timeout == 300
        assert client._retry_times == 5

    def test_vision_client_enabled_default(self):
        """测试默认启用状态"""
        client = VisionClient()
        assert isinstance(client._enabled, bool)


class TestVisionClientImageEncoding:
    """图片编码测试"""

    def test_encode_image(self):
        """测试图片 base64 编码"""
        client = VisionClient()
        image_bytes = b"fake image data"
        encoded = client._encode_image(image_bytes)

        assert isinstance(encoded, str)
        # 验证 base64 解码后与原数据一致
        decoded = base64.b64decode(encoded)
        assert decoded == image_bytes

    def test_encode_empty_image(self):
        """测试空图片编码"""
        client = VisionClient()
        image_bytes = b""
        encoded = client._encode_image(image_bytes)

        assert isinstance(encoded, str)
        decoded = base64.b64decode(encoded)
        assert decoded == b""


class TestVisionClientPrompt:
    """提示词测试"""

    def test_generate_description_prompt(self):
        """测试描述提示词生成"""
        client = VisionClient()
        prompt = client._generate_description_prompt()

        assert isinstance(prompt, str)
        assert len(prompt) > 0
        # 验证提示词包含 JSON 格式要求
        assert "description" in prompt
        assert "chart_type" in prompt
        assert "semantic_tags" in prompt


class TestVisionClientResponseParsing:
    """响应解析测试"""

    def test_parse_valid_json_response(self):
        """测试解析有效的 JSON 响应"""
        client = VisionClient()
        response_text = json.dumps({
            "description": "测试图片描述",
            "chart_type": "折线图",
            "chart_data_summary": "Q1-Q4销售额增长",
            "alt_text": "季度销售趋势图",
            "semantic_tags": ["销售", "增长", "季度"],
            "confidence": 0.95
        })

        description = client._parse_response(response_text)

        assert isinstance(description, ImageDescription)
        assert description.description == "测试图片描述"
        assert description.chart_type == "折线图"
        assert description.chart_data_summary == "Q1-Q4销售额增长"
        assert description.alt_text == "季度销售趋势图"
        assert description.semantic_tags == ["销售", "增长", "季度"]
        assert description.confidence == 0.95

    def test_parse_json_with_code_block(self):
        """测试解析带代码块的 JSON 响应"""
        client = VisionClient()
        response_text = '''
```json
{
    "description": "测试图片",
    "chart_type": null,
    "chart_data_summary": null,
    "semantic_tags": ["测试"],
    "confidence": 0.8
}
```'''

        description = client._parse_response(response_text)

        assert isinstance(description, ImageDescription)
        assert description.description == "测试图片"
        assert description.chart_type is None
        assert description.confidence == 0.8

    def test_parse_plain_text_response(self):
        """测试解析纯文本响应（无法解析为 JSON）"""
        client = VisionClient()
        response_text = "这是一张包含文字的图片"

        description = client._parse_response(response_text)

        assert isinstance(description, ImageDescription)
        assert description.description == response_text
        assert description.confidence == 0.6  # 降级置信度

    def test_parse_invalid_json(self):
        """测试解析无效 JSON"""
        client = VisionClient()
        response_text = "```json\ninvalid json{```"

        description = client._parse_response(response_text)

        assert isinstance(description, ImageDescription)
        assert description.description is not None
        assert description.confidence == 0.6

    def test_parse_empty_response(self):
        """测试解析空响应"""
        client = VisionClient()
        description = client._parse_response("")

        assert isinstance(description, ImageDescription)
        assert description.description == ""


class TestVisionClientDisabled:
    """视觉模型禁用测试"""

    def test_describe_when_disabled(self):
        """测试视觉模型禁用时返回默认描述"""
        client = VisionClient()

        # 临时禁用
        original_enabled = client._enabled
        client._enabled = False

        image_bytes = b"fake image data"
        description = client.describe(image_bytes)

        assert isinstance(description, ImageDescription)
        assert description.description == "图片"
        assert description.confidence == 0.5

        # 恢复启用状态
        client._enabled = original_enabled


class TestVisionClientMock:
    """视觉模型 Mock 测试"""

    def test_describe_with_mock_response(self):
        """测试使用 Mock 响应"""
        client = VisionClient()

        # 创建一个 1x1 像素的 PNG 图片
        from PIL import Image
        img = Image.new("RGB", (1, 1), color="red")
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        image_bytes = buffer.getvalue()

        # 模拟健康检查成功
        with patch.object(client, "health_check", return_value=True):
            # 模拟 API 响应
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "response": json.dumps({
                    "description": "一张纯红色图片",
                    "chart_type": None,
                    "chart_data_summary": None,
                    "semantic_tags": ["纯色", "红色"],
                    "confidence": 0.9
                })
            }

            with patch.object(client, "_get_client") as mock_get_client:
                mock_get_client.return_value.post.return_value = mock_response

                description = client.describe(image_bytes)

                assert isinstance(description, ImageDescription)
                assert description.description == "一张纯红色图片"
                assert description.chart_type is None
                assert description.semantic_tags == ["纯色", "红色"]
                assert description.confidence == 0.9


class TestVisionClientErrorHandling:
    """错误处理测试"""

    def test_describe_timeout_handling(self):
        """测试超时处理"""
        client = VisionClient()

        # 模拟超时
        import httpx
        with patch.object(client, "health_check", return_value=True):
            with patch.object(client, "_get_client") as mock_get_client:
                mock_client = Mock()
                mock_client.post.side_effect = httpx.TimeoutException("请求超时")
                mock_get_client.return_value = mock_client

                image_bytes = b"fake image"
                description = client.describe(image_bytes)

                # 应该返回降级描述
                assert isinstance(description, ImageDescription)
                assert description.confidence < 0.5

    def test_describe_connection_error(self):
        """测试连接错误处理"""
        client = VisionClient()

        import httpx
        with patch.object(client, "health_check", return_value=True):
            with patch.object(client, "_get_client") as mock_get_client:
                mock_client = Mock()
                mock_client.post.side_effect = httpx.ConnectError("连接失败")
                mock_get_client.return_value = mock_client

                image_bytes = b"fake image"
                description = client.describe(image_bytes)

                assert isinstance(description, ImageDescription)
                assert description.confidence < 0.5


class TestVisionClientChartDescription:
    """图表描述测试"""

    def test_describe_chart(self):
        """测试图表描述方法"""
        client = VisionClient()

        from PIL import Image
        img = Image.new("RGB", (100, 100), color="blue")
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        image_bytes = buffer.getvalue()

        with patch.object(client, "health_check", return_value=True):
            with patch.object(client, "_get_client") as mock_get_client:
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = {
                    "response": json.dumps({
                        "description": "柱状图展示季度销售数据",
                        "chart_type": "柱状图",
                        "chart_data_summary": "Q1:100, Q2:150, Q3:200, Q4:180",
                        "semantic_tags": ["销售", "季度", "柱状图"],
                        "confidence": 0.95
                    })
                }
                mock_client = Mock()
                mock_client.post.return_value = mock_response
                mock_get_client.return_value = mock_client

                description = client.describe_chart(image_bytes)

                assert isinstance(description, ImageDescription)
                assert description.chart_type == "柱状图"
                assert "Q1" in description.chart_data_summary
                assert description.confidence == 0.95


class TestVisionClientSingleton:
    """单例模式测试"""

    def test_get_vision_client_singleton(self):
        """测试单例模式"""
        client1 = get_vision_client()
        client2 = get_vision_client()

        # 应该是同一个实例
        assert client1 is client2


class TestVisionClientHealthCheck:
    """健康检查测试"""

    def test_health_check_returns_bool(self):
        """测试健康检查返回布尔值"""
        client = VisionClient()
        result = client.health_check()
        assert isinstance(result, bool)

    def test_health_check_when_disabled(self):
        """测试禁用时的健康检查"""
        client = VisionClient()
        original_enabled = client._enabled
        client._enabled = False

        result = client.health_check()

        assert result is False

        client._enabled = original_enabled


class TestVisionClientConfiguration:
    """配置测试"""

    def test_vision_config_exists(self):
        """测试视觉模型配置存在"""
        from core.config import settings

        assert hasattr(settings, "vision")
        assert hasattr(settings.vision, "model_name")
        assert hasattr(settings.vision, "ollama_host")
        assert hasattr(settings.vision, "timeout")
        assert hasattr(settings.vision, "retry_times")
        assert hasattr(settings.vision, "enabled")

    def test_vision_config_defaults(self):
        """测试视觉模型配置默认值"""
        from core.config import settings

        assert settings.vision.model_name is not None
        assert settings.vision.timeout > 0
        assert settings.vision.retry_times >= 0
        assert isinstance(settings.vision.enabled, bool)


class TestVisionClientIntegration:
    """集成测试（需要 Ollama 视觉模型服务运行）"""

    @pytest.mark.skipif(
        True,  # 默认跳过，需要手动启用
        reason="需要 Ollama 视觉模型服务运行"
    )
    def test_ollama_vision_service_available(self):
        """测试 Ollama 视觉模型服务可用性"""
        client = VisionClient()
        is_healthy = client.health_check()

        assert is_healthy is True, "Ollama 视觉模型服务不可用，请确保服务已启动并拉取对应模型"

    @pytest.mark.skipif(
        True,  # 默认跳过，需要手动启用
        reason="需要 Ollama 视觉模型服务运行"
    )
    def test_describe_real_image(self):
        """测试真实图片描述"""
        client = VisionClient()

        # 使用一个简单的测试图片
        from PIL import Image
        img = Image.new("RGB", (200, 100), color=(255, 0, 0))
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        image_bytes = buffer.getvalue()

        description = client.describe(image_bytes)

        assert isinstance(description, ImageDescription)
        assert description.description is not None
        assert len(description.description) > 0
