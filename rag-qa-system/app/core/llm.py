"""
RAG 问答系统 - DeepSeek LLM 模块
大语言模型调用接口
"""

from typing import List, Dict, Optional, Any
import time

from openai import OpenAI

from app.config import settings
from app.core.logger import get_logger

logger = get_logger(__name__)


class LLMClient:
    """
    DeepSeek LLM 客户端
    封装与 DeepSeek API 的交互
    """

    _instance: Optional["LLMClient"] = None
    _client: Optional[OpenAI] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if LLMClient._client is not None:
            return
        self._initialize()

    def _initialize(self):
        """初始化 OpenAI 客户端（兼容 DeepSeek API）"""
        logger.info("正在初始化 DeepSeek LLM 客户端...")

        if not settings.deepseek_api_key:
            logger.warning("未配置 DeepSeek API Key，LLM 功能将不可用")
            return

        try:
            LLMClient._client = OpenAI(
                api_key=settings.deepseek_api_key,
                base_url=settings.deepseek_base_url,
                timeout=settings.deepseek_timeout,
                max_retries=settings.deepseek_max_retries,
            )
            logger.info("DeepSeek LLM 客户端初始化完成")
        except Exception as e:
            logger.error(f"LLM 客户端初始化失败: {str(e)}")
            raise

    @property
    def client(self) -> Optional[OpenAI]:
        """获取 OpenAI 客户端"""
        return LLMClient._client

    @property
    def is_available(self) -> bool:
        """检查 LLM 是否可用"""
        return self._client is not None and bool(settings.deepseek_api_key)

    def generate(
        self,
        prompt: str,
        system_prompt: str = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> str:
        """
        生成文本回答

        Args:
            prompt: 用户输入提示
            system_prompt: 系统提示（可选）
            temperature: 温度参数，控制随机性
            max_tokens: 最大生成 token 数
            **kwargs: 其他 OpenAI 参数

        Returns:
            生成的文本
        """
        if not self.is_available:
            raise RuntimeError("LLM 客户端未初始化或 API Key 未配置")

        start_time = time.time()

        try:
            messages = []

            if system_prompt:
                messages.append({
                    "role": "system",
                    "content": system_prompt
                })

            messages.append({
                "role": "user",
                "content": prompt
            })

            logger.debug(f"正在调用 DeepSeek API，模型: {settings.deepseek_model}")

            response = self._client.chat.completions.create(
                model=settings.deepseek_model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )

            elapsed = (time.time() - start_time) * 1000
            logger.info(f"DeepSeek API 调用完成，耗时: {elapsed:.2f}ms")

            if response.choices and len(response.choices) > 0:
                return response.choices[0].message.content.strip()
            else:
                logger.warning("API 返回空结果")
                return ""

        except Exception as e:
            elapsed = (time.time() - start_time) * 1000
            logger.error(f"DeepSeek API 调用失败: {str(e)}，耗时: {elapsed:.2f}ms")
            raise

    def generate_with_context(
        self,
        question: str,
        context: List[str],
        history: List[dict] = None,
        system_prompt: str = None,
        temperature: float = 0.3,
        max_tokens: int = 2000
    ) -> str:
        """
        基于上下文生成回答

        Args:
            question: 用户问题
            context: 检索到的上下文文档列表
            system_prompt: 系统提示（可选）
            temperature: 温度参数
            max_tokens: 最大 token 数

        Returns:
            生成的文本回答
        """
        context_text = "\n\n".join([
            f"[文档 {i+1}]:\n{doc}"
            for i, doc in enumerate(context)
        ])

        # 根据是否有上下文决定提示词
        if context and len(context) > 0:
            prompt = f"""基于以下参考文档回答用户问题。请充分利用文档中的信息。

【参考文档】
{context_text}

【用户问题】
{question}

请根据参考文档回答问题，回答时提及参考文档编号。"""
        else:
            # 无参考文档时，让 AI 直接基于知识回答
            prompt = f"""【用户问题】
{question}

请直接回答用户的问题，基于你的专业知识给出准确、详细的答案。"""

        default_system = "你是一个专业的知识库问答助手，请基于提供的参考文档准确回答用户问题。如果文档中没有相关信息，请明确告知用户。"

        if history and len(history) > 0:
            messages = []
            messages.append({"role": "system", "content": system_prompt or default_system})
            messages.extend(history)
            messages.append({"role": "user", "content": prompt})
            response = self._client.chat.completions.create(
                model=settings.deepseek_model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            if response.choices and len(response.choices) > 0:
                return response.choices[0].message.content.strip()
            return ""
        return self.generate(
            prompt=prompt,
            system_prompt=system_prompt or default_system,
            temperature=temperature,
            max_tokens=max_tokens
        )

    def generate_stream(
        self,
        prompt: str,
        system_prompt: str = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ):
        """
        流式生成文本回答

        Args:
            prompt: 用户输入提示
            system_prompt: 系统提示（可选）
            temperature: 温度参数
            max_tokens: 最大生成 token 数
            **kwargs: 其他 OpenAI 参数

        Yields:
            每个 token 的增量文本
        """
        if not self.is_available:
            raise RuntimeError("LLM 客户端未初始化或 API Key 未配置")

        try:
            messages = []

            if system_prompt:
                messages.append({
                    "role": "system",
                    "content": system_prompt
                })

            messages.append({
                "role": "user",
                "content": prompt
            })

            logger.debug(f"正在调用 DeepSeek API（流式），模型: {settings.deepseek_model}")

            stream = self._client.chat.completions.create(
                model=settings.deepseek_model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
                **kwargs
            )

            for chunk in stream:
                if chunk.choices and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta.content
                    if delta:
                        yield delta

        except Exception as e:
            logger.error(f"DeepSeek API 流式调用失败: {str(e)}")
            raise

    def generate_with_context_stream(
        self,
        question: str,
        context: List[str],
        history: List[dict] = None,
        system_prompt: str = None,
        temperature: float = 0.3,
        max_tokens: int = 2000
    ):
        """
        基于上下文流式生成回答

        Args:
            question: 用户问题
            context: 检索到的上下文文档列表
            history: 对话历史
            system_prompt: 系统提示
            temperature: 温度参数
            max_tokens: 最大 token 数

        Yields:
            每个 token 的增量文本
        """
        context_text = "\n\n".join([
            f"[文档 {i+1}]:\n{doc}"
            for i, doc in enumerate(context)
        ])

        # 根据是否有上下文决定提示词
        if context and len(context) > 0:
            prompt = f"""基于以下参考文档回答用户问题。请充分利用文档中的信息。

【参考文档】
{context_text}

【用户问题】
{question}

请根据参考文档回答问题，回答时提及参考文档编号。"""
        else:
            # 无参考文档时，让 AI 直接基于知识回答
            prompt = f"""【用户问题】
{question}

请直接回答用户的问题，基于你的专业知识给出准确、详细的答案。"""

        default_system = "你是一个专业的知识库问答助手，请基于提供的参考文档准确回答用户问题。如果文档中没有相关信息，请明确告知用户。"

        if history and len(history) > 0:
            messages = []
            messages.append({"role": "system", "content": system_prompt or default_system})
            messages.extend(history)
            messages.append({"role": "user", "content": prompt})

            stream = self._client.chat.completions.create(
                model=settings.deepseek_model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
            )
            for chunk in stream:
                if chunk.choices and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta.content
                    if delta:
                        yield delta
        else:
            yield from self.generate_stream(
                prompt=prompt,
                system_prompt=system_prompt or default_system,
                temperature=temperature,
                max_tokens=max_tokens
            )

    def check_connection(self) -> bool:
        """检查 API 连接是否正常"""
        if not self.is_available:
            return False

        try:
            response = self._client.chat.completions.create(
                model=settings.deepseek_model,
                messages=[{"role": "user", "content": "你好"}],
                max_tokens=10,
            )
            return True
        except Exception as e:
            logger.error(f"API 连接检查失败: {str(e)}")
            return False


# 全局 LLM 客户端实例
llm_client = LLMClient()


def get_llm_client() -> LLMClient:
    """获取 LLM 客户端实例"""
    return llm_client


# 默认系统提示
DEFAULT_SYSTEM_PROMPT = """你是一个专业的知识库问答助手。

回答规则：
1. 如果提供了参考文档，请基于这些文档准确回答问题
2. 如果没有提供参考文档（或文档为空），请基于你的专业知识直接回答
3. 回答要清晰、准确、详细，适当使用结构化格式
4. 可以引用文档中的原话来支持回答（如果有文档的话）
5. 如果有多个相关文档，综合它们的信息给出完整回答
6. 永远不要回复"无法回答"、"知识库中没有相关内容"等拒绝性内容
7. 可以结合通用知识、业界最佳实践给出完整答案

请开始回答："""

# AI 生成模式专用提示
# 当本地知识库没有检索到相关内容时，使用此提示词让 AI 自由回答
AI_GENERATE_SYSTEM_PROMPT = """你是一个知识渊博的技术专家。请直接回答用户的问题。

回答规则：
1. 如果提供了参考文档片段，优先基于这些片段进行回答和扩展
2. 如果没有提供参考文档（或文档为空），请基于你的专业知识直接回答
3. 回答要专业、准确、详细，适当使用结构化格式（如列表、流程图等）
4. 可以结合通用知识、业界最佳实践给出完整答案
5. 永远不要回复"无法回答"、"没有相关信息"等拒绝性内容
6. 如果问题需要代码示例，请提供清晰可用的代码
7. 回答长度适中，既要全面又不冗余

请直接开始回答用户问题："""
