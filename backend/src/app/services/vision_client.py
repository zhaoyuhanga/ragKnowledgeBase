# -*- coding: utf-8 -*-
"""
Ollama 视觉模型客户端

本模块提供 Ollama 视觉模型的客户端封装，用于图片多模态描述生成：
- 图片场景描述
- 图表类型识别（折线图、柱状图、饼图等）
- 图表数据提取和摘要
- 语义标签生成
"""

import base64
import json
import time
from typing import Any, Dict, List, Optional

import httpx

from app.common.logging import logger
from app.parsers.base import ImageDescription
from core.config import settings


class VisionClient:
    """
    Ollama 视觉模型客户端

    使用 Ollama 的视觉模型（如 qwen2.5-ocr、llava）生成图片描述。
    """

    def __init__(
        self,
        host: Optional[str] = None,
        model_name: Optional[str] = None,
        timeout: Optional[int] = None,
        retry_times: Optional[int] = None
    ):
        """
        初始化视觉模型客户端

        Args:
            host: Ollama 服务地址，默认使用配置
            model_name: 模型名称，默认使用配置
            timeout: 请求超时时间，默认使用配置
            retry_times: 重试次数，默认使用配置
        """
        self._config = settings.vision
        self._host = host or self._config.ollama_host
        self._model_name = model_name or self._config.model_name
        self._timeout = timeout or self._config.timeout
        self._retry_times = retry_times or self._config.retry_times
        self._enabled = self._config.enabled

        self._client: Optional[httpx.Client] = None

    def _get_client(self) -> httpx.Client:
        """
        获取 HTTP 客户端实例（懒加载）

        Returns:
            httpx.Client 实例
        """
        if self._client is None:
            self._client = httpx.Client(
                timeout=httpx.Timeout(self._timeout),
                limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
            )
        return self._client

    def close(self) -> None:
        """关闭客户端连接"""
        if self._client is not None:
            self._client.close()
            self._client = None

    def health_check(self) -> bool:
        """
        检查视觉模型服务健康状态

        Returns:
            服务是否健康
        """
        if not self._enabled:
            logger.info("视觉模型功能未启用，跳过健康检查")
            return False

        try:
            client = self._get_client()
            response = client.get(f"{self._host}/api/tags")
            if response.status_code == 200:
                # 检查指定模型是否存在
                models = response.json().get("models", [])
                model_names = [m.get("name", "") for m in models]
                if any(self._model_name in name for name in model_names):
                    logger.info(
                        f"视觉模型健康检查通过: {self._model_name}",
                        extra={"host": self._host}
                    )
                    return True
                else:
                    logger.warning(
                        f"视觉模型 {self._model_name} 未安装，请先运行: ollama pull {self._model_name}",
                        extra={"host": self._host, "model": self._model_name}
                    )
                    return False
            else:
                logger.warning(
                    f"视觉模型服务健康检查失败: HTTP {response.status_code}",
                    extra={"host": self._host, "status_code": response.status_code}
                )
                return False
        except Exception as e:
            logger.warning(
                f"视觉模型服务健康检查异常: {str(e)}",
                extra={"host": self._host, "error": str(e)}
            )
            return False

    def _encode_image(self, image_bytes: bytes) -> str:
        """
        将图片字节数据编码为 base64 字符串

        Args:
            image_bytes: 图片字节数据

        Returns:
            base64 编码字符串
        """
        return base64.b64encode(image_bytes).decode("utf-8")

    def _generate_description_prompt(self) -> str:
        """
        生成图片描述的提示词

        Returns:
            提示词文本
        """
        return """请分析这张图片并提供详细描述，遵循以下 JSON 格式：

{
    "description": "详细描述图片内容，包括场景、物体、文字等",
    "chart_type": "如果图片是图表，填写类型（折线图/柱状图/饼图/散点图/雷达图/热力图/其他图表/普通图片），否则填null",
    "chart_data_summary": "如果图片是图表，提取关键数据摘要（如：Q1-Q4销售额分别为100、150、200、180万元），否则填null",
    "alt_text": "图片的替代文本描述",
    "semantic_tags": ["标签1", "标签2", ...],
    "confidence": 0.95
}

请确保：
1. description 简洁但信息丰富，包含关键信息
2. chart_type 只在明显是图表时才填写
3. chart_data_summary 提取图表中的关键数据点
4. semantic_tags 包含3-8个相关标签
5. confidence 表示描述置信度(0-1)
6. 只输出JSON，不要有其他内容"""

    def describe(
        self,
        image_bytes: bytes,
        prompt: Optional[str] = None
    ) -> ImageDescription:
        """
        生成图片描述

        Args:
            image_bytes: 图片字节数据
            prompt: 自定义提示词（可选）

        Returns:
            图片描述对象
        """
        if not self._enabled:
            logger.info("视觉模型功能未启用，返回默认描述")
            return ImageDescription(
                description="图片",
                confidence=0.5
            )

        start_time = time.time()

        for attempt in range(self._retry_times):
            try:
                client = self._get_client()

                # 构造请求
                request_prompt = prompt or self._generate_description_prompt()
                image_base64 = self._encode_image(image_bytes)

                response = client.post(
                    f"{self._host}/api/generate",
                    json={
                        "model": self._model_name,
                        "prompt": request_prompt,
                        "images": [image_base64],
                        "stream": False,
                        "options": {
                            "temperature": 0.7,
                            "num_predict": 1024
                        }
                    }
                )

                cost_ms = int((time.time() - start_time) * 1000)

                if response.status_code == 200:
                    result = response.json()
                    response_text = result.get("response", "").strip()

                    # 尝试解析 JSON 响应
                    description = self._parse_response(response_text)

                    logger.info(
                        f"图片描述生成成功",
                        extra={
                            "model": self._model_name,
                            "cost_ms": cost_ms,
                            "chart_type": description.chart_type,
                            "confidence": description.confidence
                        }
                    )

                    return description
                else:
                    logger.warning(
                        f"视觉模型请求失败: HTTP {response.status_code}",
                        extra={
                            "attempt": attempt + 1,
                            "status_code": response.status_code
                        }
                    )

            except httpx.TimeoutException:
                logger.warning(
                    f"视觉模型请求超时 (尝试 {attempt + 1}/{self._retry_times})",
                    extra={"timeout": self._timeout}
                )
            except httpx.ConnectError:
                logger.warning(
                    f"视觉模型连接失败 (尝试 {attempt + 1}/{self._retry_times})",
                    extra={"host": self._host}
                )
            except json.JSONDecodeError as e:
                logger.warning(
                    f"视觉模型响应 JSON 解析失败: {str(e)}",
                    extra={"attempt": attempt + 1}
                )
            except Exception as e:
                logger.warning(
                    f"视觉模型请求异常 (尝试 {attempt + 1}/{self._retry_times}): {str(e)}",
                    extra={"error": str(e)}
                )

            # 重试前等待
            if attempt < self._retry_times - 1:
                time.sleep(1 * (attempt + 1))

        # 所有重试都失败
        cost_ms = int((time.time() - start_time) * 1000)
        logger.error(
            f"图片描述生成失败，已重试 {self._retry_times} 次",
            extra={"cost_ms": cost_ms}
        )

        return ImageDescription(
            description="图片描述生成失败",
            confidence=0.3
        )

    def _parse_response(self, response_text: str) -> ImageDescription:
        """
        解析模型响应文本

        尝试从响应中提取 JSON 并构建 ImageDescription 对象。

        Args:
            response_text: 模型响应文本

        Returns:
            图片描述对象
        """
        # 尝试直接解析 JSON
        try:
            data = json.loads(response_text)
            return ImageDescription(
                description=data.get("description", ""),
                chart_type=data.get("chart_type"),
                chart_data_summary=data.get("chart_data_summary"),
                alt_text=data.get("alt_text"),
                semantic_tags=data.get("semantic_tags", []),
                confidence=data.get("confidence", 0.8)
            )
        except json.JSONDecodeError:
            pass

        # 尝试从文本中提取 JSON（处理可能的 markdown 代码块）
        import re

        # 匹配 ```json ... ``` 格式
        json_pattern = r"```(?:json)?\s*([\s\S]*?)\s*```"
        matches = re.findall(json_pattern, response_text)
        for match in matches:
            try:
                data = json.loads(match.strip())
                return ImageDescription(
                    description=data.get("description", ""),
                    chart_type=data.get("chart_type"),
                    chart_data_summary=data.get("chart_data_summary"),
                    alt_text=data.get("alt_text"),
                    semantic_tags=data.get("semantic_tags", []),
                    confidence=data.get("confidence", 0.8)
                )
            except json.JSONDecodeError:
                continue

        # 尝试匹配 { ... } 格式
        brace_pattern = r"\{[\s\S]*\}"
        matches = re.findall(brace_pattern, response_text)
        for match in matches:
            try:
                data = json.loads(match)
                return ImageDescription(
                    description=data.get("description", ""),
                    chart_type=data.get("chart_type"),
                    chart_data_summary=data.get("chart_data_summary"),
                    alt_text=data.get("alt_text"),
                    semantic_tags=data.get("semantic_tags", []),
                    confidence=data.get("confidence", 0.8)
                )
            except json.JSONDecodeError:
                continue

        # 无法解析 JSON，返回基于原始文本的描述
        logger.warning("无法解析模型响应为 JSON，使用原始文本作为描述")
        return ImageDescription(
            description=response_text[:500] if len(response_text) > 500 else response_text,
            confidence=0.6
        )

    def describe_chart(self, image_bytes: bytes) -> ImageDescription:
        """
        专门用于图表图片的描述生成

        使用专门的图表分析提示词。

        Args:
            image_bytes: 图片字节数据

        Returns:
            图片描述对象
        """
        chart_prompt = """请分析这张图表图片，提供详细的数据摘要：

{
    "description": "图表的整体描述",
    "chart_type": "图表类型（折线图/柱状图/饼图/散点图/雷达图/热力图/其他）",
    "chart_data_summary": "关键数据摘要，如：'Q1-Q4销售额增长，分别为100万、150万、200万、180万，Q3最高'",
    "alt_text": "图表的替代文本",
    "semantic_tags": ["数据分析", "销售", "季度对比", ...],
    "confidence": 0.95
}

请务必：
1. 准确识别图表类型
2. 提取图表中的关键数据点和趋势
3. 标注最大值、最小值、变化趋势
4. 只输出JSON"""

        return self.describe(image_bytes, prompt=chart_prompt)


# 全局客户端实例
_vision_client: Optional[VisionClient] = None


def get_vision_client() -> VisionClient:
    """
    获取视觉模型客户端实例（单例模式）

    Returns:
        VisionClient 实例
    """
    global _vision_client
    if _vision_client is None:
        _vision_client = VisionClient()
    return _vision_client
