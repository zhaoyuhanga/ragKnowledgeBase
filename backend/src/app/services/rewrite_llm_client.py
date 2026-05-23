# -*- coding: utf-8 -*-
"""
查询改写专用LLM客户端

本模块提供查询改写专用的LLM客户端封装，支持：
- DeepSeek
- OpenAI
- Ollama

用于：
- 多查询生成
- 子查询分解
- HyDE假设答案生成
- 后退提示生成
"""

import time
from typing import Any, Dict, List, Optional

import httpx

from app.common.logging import logger
from core.config import settings


class RewriteLLMClient:
    """
    查询改写专用LLM客户端

    封装不同LLM服务的调用接口，提供统一的生成接口。
    """

    def __init__(
        self,
        provider: str = "deepseek",
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: int = 60
    ):
        """
        初始化LLM客户端

        Args:
            provider: LLM提供商（deepseek/openai/ollama）
            api_key: API密钥
            model_name: 模型名称
            base_url: API地址
            timeout: 超时时间（秒）
        """
        self._provider = provider.lower()
        self._api_key = api_key or settings.llm.api_key
        self._model_name = model_name or settings.llm.model_name
        self._base_url = base_url or settings.llm.base_url
        self._timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """获取HTTP客户端"""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self._timeout),
                limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
            )
        return self._client

    async def close(self) -> None:
        """关闭客户端"""
        if self._client is not None and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    def generate(self, prompt: str, max_tokens: int = 500) -> str:
        """
        同步生成接口（兼容同步场景）

        Args:
            prompt: 提示词
            max_tokens: 最大Token数

        Returns:
            生成的文本
        """
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # 如果已经在事件循环中，创建任务
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(self._sync_generate, prompt, max_tokens)
                    return future.result(timeout=self._timeout)
            else:
                return asyncio.run(self._async_generate(prompt, max_tokens))
        except Exception as e:
            logger.error(f"LLM生成失败: {str(e)}")
            return ""

    def _sync_generate(self, prompt: str, max_tokens: int = 500) -> str:
        """
        同步生成实现

        Args:
            prompt: 提示词
            max_tokens: 最大Token数

        Returns:
            生成的文本
        """
        start_time = time.time()

        try:
            headers = self._get_headers()
            data = self._get_request_body(prompt, max_tokens)

            with httpx.Client(timeout=self._timeout) as client:
                response = client.post(
                    self._get_api_url(),
                    headers=headers,
                    json=data
                )

                if response.status_code == 200:
                    result = self._parse_response(response.json())
                    cost_ms = int((time.time() - start_time) * 1000)

                    logger.info(
                        f"LLM生成成功，耗时: {cost_ms}ms",
                        extra={
                            "provider": self._provider,
                            "model": self._model_name,
                            "prompt_length": len(prompt),
                            "response_length": len(result),
                            "cost_ms": cost_ms
                        }
                    )
                    return result
                else:
                    logger.error(
                        f"LLM生成失败: HTTP {response.status_code}",
                        extra={"status_code": response.status_code, "response": response.text}
                    )
                    return ""

        except Exception as e:
            logger.error(f"LLM生成异常: {str(e)}")
            return ""

    async def _async_generate(self, prompt: str, max_tokens: int = 500) -> str:
        """
        异步生成实现

        Args:
            prompt: 提示词
            max_tokens: 最大Token数

        Returns:
            生成的文本
        """
        start_time = time.time()

        try:
            client = await self._get_client()
            headers = self._get_headers()
            data = self._get_request_body(prompt, max_tokens)

            response = await client.post(
                self._get_api_url(),
                headers=headers,
                json=data
            )

            if response.status_code == 200:
                result = self._parse_response(response.json())
                cost_ms = int((time.time() - start_time) * 1000)

                logger.info(
                    f"LLM生成成功，耗时: {cost_ms}ms",
                    extra={
                        "provider": self._provider,
                        "model": self._model_name,
                        "prompt_length": len(prompt),
                        "response_length": len(result),
                        "cost_ms": cost_ms
                    }
                )
                return result
            else:
                logger.error(
                    f"LLM生成失败: HTTP {response.status_code}",
                    extra={"status_code": response.status_code, "response": response.text}
                )
                return ""

        except Exception as e:
            logger.error(f"LLM生成异常: {str(e)}")
            return ""

    def _get_headers(self) -> Dict[str, str]:
        """获取请求头"""
        headers = {
            "Content-Type": "application/json"
        }

        if self._provider == "deepseek":
            headers["Authorization"] = f"Bearer {self._api_key}"
        elif self._provider == "openai":
            headers["Authorization"] = f"Bearer {self._api_key}"

        return headers

    def _get_api_url(self) -> str:
        """获取API URL"""
        if self._provider == "deepseek":
            return f"{self._base_url}/chat/completions"
        elif self._provider == "openai":
            return f"{self._base_url}/chat/completions"
        elif self._provider == "ollama":
            return f"{self._base_url}/api/generate"
        else:
            return f"{self._base_url}/chat/completions"

    def _get_request_body(self, prompt: str, max_tokens: int) -> Dict[str, Any]:
        """获取请求体"""
        if self._provider == "ollama":
            return {
                "model": self._model_name,
                "prompt": prompt,
                "stream": False
            }
        else:
            return {
                "model": self._model_name,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "max_tokens": max_tokens,
                "temperature": 0.7
            }

    def _parse_response(self, response: Dict[str, Any]) -> str:
        """解析响应"""
        if self._provider == "ollama":
            return response.get("response", "")
        else:
            choices = response.get("choices", [])
            if choices and len(choices) > 0:
                return choices[0].get("message", {}).get("content", "")
            return ""

    def health_check(self) -> bool:
        """
        健康检查

        Returns:
            服务是否可用
        """
        try:
            if self._provider == "ollama":
                with httpx.Client(timeout=5) as client:
                    response = client.get(f"{self._base_url}/api/tags")
                    return response.status_code == 200
            else:
                return bool(self._api_key)
        except Exception as e:
            logger.warning(f"LLM健康检查失败: {str(e)}")
            return False


# 全局客户端实例
_rewrite_llm_client: Optional[RewriteLLMClient] = None


def get_rewrite_llm_client() -> Optional[RewriteLLMClient]:
    """
    获取查询改写专用LLM客户端

    Returns:
        LLM客户端实例，如果未配置则返回None
    """
    global _rewrite_llm_client
    if _rewrite_llm_client is None:
        try:
            _rewrite_llm_client = RewriteLLMClient(
                provider=settings.llm.provider,
                api_key=settings.llm.api_key,
                model_name=settings.llm.model_name,
                base_url=settings.llm.base_url
            )
            if not _rewrite_llm_client.health_check():
                logger.warning("LLM服务不可用，查询改写将使用规则模式")
                _rewrite_llm_client = None
        except Exception as e:
            logger.warning(f"初始化LLM客户端失败: {str(e)}")
            _rewrite_llm_client = None

    return _rewrite_llm_client
