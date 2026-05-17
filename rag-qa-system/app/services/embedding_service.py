"""
RAG 问答系统 - Embedding 服务模块
文本向量化和 Embedding 模型管理
支持 Ollama HTTP API 调用
"""

from typing import List, Optional
import time
import numpy as np
import httpx

from app.config import settings
from app.core.logger import get_logger

logger = get_logger(__name__)


class EmbeddingService:
    """
    Embedding 服务
    支持 Ollama HTTP API 调用
    """

    _instance: Optional["EmbeddingService"] = None
    _initialized: bool = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if EmbeddingService._initialized:
            return
        self._initialize()
        EmbeddingService._initialized = True

    def _initialize(self):
        """初始化 Embedding 服务"""
        provider = settings.embedding_provider
        logger.info(f"正在初始化 Embedding 服务，provider={provider}, model={settings.embedding_model}")

        if provider != "ollama":
            raise ValueError(f"当前仅支持 Ollama provider，当前配置为: {provider}")

        # 验证 Ollama 服务可用性
        self._check_ollama_connection()

        logger.info(f"Embedding 服务初始化完成，base_url={settings.embedding_base_url}")

    def _check_ollama_connection(self) -> bool:
        """检查 Ollama 连接是否正常"""
        try:
            with httpx.Client(timeout=5.0) as client:
                response = client.get(f"{settings.embedding_base_url}/api/tags")
                if response.status_code == 200:
                    logger.info("Ollama 服务连接正常")
                    return True
                else:
                    logger.warning(f"Ollama 服务返回异常状态码: {response.status_code}")
                    return False
        except Exception as e:
            logger.warning(f"无法连接到 Ollama 服务: {str(e)}")
            return False

    def _call_ollama_api(self, texts: List[str]) -> List[List[float]]:
        """
        调用 Ollama Embedding API

        Args:
            texts: 文本列表

        Returns:
            向量列表
        """
        embeddings = []

        with httpx.Client(timeout=settings.embedding_timeout) as client:
            for text in texts:
                # 清理特殊字符
                cleaned_text = text.replace('\x00', '').strip()
                if not cleaned_text:
                    # 返回零向量
                    embeddings.append([0.0] * settings.embedding_dimension)
                    continue

                payload = {
                    "model": settings.embedding_model,
                    "prompt": cleaned_text
                }

                for attempt in range(settings.embedding_max_retries):
                    try:
                        response = client.post(
                            f"{settings.embedding_base_url}/api/embeddings",
                            json=payload
                        )

                        if response.status_code == 200:
                            data = response.json()
                            embedding = data.get("embedding", [])
                            # L2 normalize
                            embedding = self._normalize(embedding)
                            embeddings.append(embedding)
                            break
                        else:
                            logger.warning(
                                f"Ollama API 返回错误: status={response.status_code}, "
                                f"attempt={attempt + 1}/{settings.embedding_max_retries}"
                            )
                            if attempt == settings.embedding_max_retries - 1:
                                raise Exception(f"Ollama API 调用失败: {response.status_code}")

                    except httpx.TimeoutException:
                        logger.warning(f"Ollama API 超时，attempt={attempt + 1}/{settings.embedding_max_retries}")
                        if attempt == settings.embedding_max_retries - 1:
                            raise Exception("Ollama API 调用超时")
                    except Exception as e:
                        logger.error(f"Ollama API 调用异常: {str(e)}")
                        if attempt == settings.embedding_max_retries - 1:
                            raise

        return embeddings

    def _normalize(self, vector: List[float]) -> List[float]:
        """
        L2 归一化向量

        Args:
            vector: 输入向量

        Returns:
            归一化后的向量
        """
        arr = np.array(vector, dtype=np.float32)
        norm = np.linalg.norm(arr)

        if norm > 1e-10:
            arr = arr / norm

        return arr.tolist()

    def encode(self, texts: str | List[str], **kwargs) -> List[List[float]]:
        """
        将文本编码为向量

        Args:
            texts: 单个文本或文本列表
            **kwargs: 额外参数（兼容旧接口）

        Returns:
            向量列表
        """
        try:
            if isinstance(texts, str):
                texts = [texts]

            logger.debug(f"开始向量化 {len(texts)} 个文本")

            start_time = time.time()
            embeddings = self._call_ollama_api(texts)
            elapsed = time.time() - start_time

            logger.debug(f"向量化完成，耗时: {elapsed:.2f}秒")

            return embeddings

        except Exception as e:
            logger.error(f"文本向量化失败: {str(e)}")
            raise

    def encode_single(self, text: str) -> List[float]:
        """
        将单个文本编码为向量

        Args:
            text: 输入文本

        Returns:
            向量
        """
        return self.encode(text)[0]

    def get_embedding_dimension(self) -> int:
        """获取向量维度"""
        return settings.embedding_dimension

    def check_health(self) -> bool:
        """
        检查 Embedding 服务健康状态

        Returns:
            是否健康
        """
        try:
            test_text = "这是一个测试文本"
            result = self.encode(test_text)

            if not result or len(result) == 0:
                return False

            embedding = result[0]
            if len(embedding) != settings.embedding_dimension:
                logger.warning(
                    f"向量维度不匹配: 配置={settings.embedding_dimension}, 实际={len(embedding)}"
                )
                return False

            # 验证 L2 范数接近 1
            norm = np.linalg.norm(embedding)
            if abs(norm - 1.0) > 0.01:
                logger.warning(f"向量未正确归一化: L2={norm}")

            return True

        except Exception as e:
            logger.error(f"Embedding 健康检查失败: {str(e)}")
            return False


# 全局 Embedding 服务实例
embedding_service = EmbeddingService()


def get_embedding_service() -> EmbeddingService:
    """获取 Embedding 服务实例"""
    return embedding_service
