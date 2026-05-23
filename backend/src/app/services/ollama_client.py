# -*- coding: utf-8 -*-
"""
Ollama 客户端

本模块提供 Ollama 服务的客户端封装，包括：
- 单条和批量文本向量化
- Cross-Encoder 重排序
- 健康检查
- 连接池管理
- 错误重试机制
- 模型降级支持

所有代码注释使用中文，所有日志输出中文。
"""

import time
from typing import Any, Dict, List, Optional, Tuple

import httpx
import numpy as np

from app.common.logging import logger
from core.config import settings


class OllamaClient:
    """
    Ollama Embedding 客户端

    封装 Ollama /api/embeddings 接口调用，支持单条和批量向量化。
    """

    def __init__(
        self,
        host: Optional[str] = None,
        model_name: Optional[str] = None,
        timeout: Optional[int] = None,
        retry_times: Optional[int] = None
    ):
        """
        初始化 Ollama 客户端

        Args:
            host: Ollama 服务地址，默认使用配置
            model_name: 模型名称，默认使用配置
            timeout: 请求超时时间，默认使用配置
            retry_times: 重试次数，默认使用配置
        """
        self._config = settings.embedding
        self._host = host or self._config.ollama_host
        self._model_name = model_name or self._config.model_name
        self._timeout = timeout or self._config.ollama_timeout
        self._retry_times = retry_times or self._config.ollama_retry_times
        
        self._client: Optional[httpx.AsyncClient] = None
        self._is_healthy: Optional[bool] = None
        self._last_health_check: float = 0
        self._health_check_interval: float = 30  # 健康检查缓存30秒

    async def _get_client(self) -> httpx.AsyncClient:
        """
        获取 HTTP 客户端实例（懒加载）

        Returns:
            httpx.AsyncClient 实例
        """
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self._timeout),
                limits=httpx.Limits(max_keepalive_connections=10, max_connections=20)
            )
        return self._client

    async def close(self) -> None:
        """关闭客户端连接"""
        if self._client is not None and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def health_check(self) -> bool:
        """
        检查 Ollama 服务健康状态

        使用缓存避免频繁请求。

        Returns:
            服务是否健康
        """
        current_time = time.time()
        
        # 缓存检查，避免频繁请求
        if self._is_healthy is not None:
            if current_time - self._last_health_check < self._health_check_interval:
                return self._is_healthy

        try:
            client = await self._get_client()
            response = await client.get(f"{self._host}/api/tags")
            
            if response.status_code == 200:
                self._is_healthy = True
                logger.info(
                    "Ollama 服务健康检查通过",
                    extra={"host": self._host}
                )
            else:
                self._is_healthy = False
                logger.warning(
                    f"Ollama 服务健康检查失败: HTTP {response.status_code}",
                    extra={"host": self._host, "status_code": response.status_code}
                )
        except Exception as e:
            self._is_healthy = False
            logger.warning(
                f"Ollama 服务健康检查异常: {str(e)}",
                extra={"host": self._host, "error": str(e)}
            )
        
        self._last_health_check = current_time
        return self._is_healthy

    async def embed_single(
        self,
        text: str,
        normalize: bool = True
    ) -> np.ndarray:
        """
        单条文本向量化

        Args:
            text: 待向量化的文本
            normalize: 是否归一化

        Returns:
            向量 (numpy 数组)
        """
        if not text or not text.strip():
            logger.warning("收到空文本，返回零向量")
            return np.zeros(self._config.dimension)

        for attempt in range(self._retry_times):
            try:
                client = await self._get_client()
                
                response = await client.post(
                    f"{self._host}/api/embeddings",
                    json={
                        "model": self._model_name,
                        "prompt": text
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    embedding = result.get("embedding", [])
                    
                    if not embedding:
                        logger.warning(
                            "Ollama 返回空向量",
                            extra={"text_length": len(text)}
                        )
                        return np.zeros(self._config.dimension)
                    
                    vector = np.array(embedding)
                    
                    # 归一化
                    if normalize:
                        vector = self._normalize(vector)
                    
                    return vector
                else:
                    logger.warning(
                        f"Ollama 请求失败: HTTP {response.status_code}",
                        extra={
                            "attempt": attempt + 1,
                            "status_code": response.status_code
                        }
                    )
                    
            except httpx.TimeoutException:
                logger.warning(
                    f"Ollama 请求超时 (尝试 {attempt + 1}/{self._retry_times})",
                    extra={"timeout": self._timeout}
                )
            except httpx.ConnectError:
                logger.warning(
                    f"Ollama 连接失败 (尝试 {attempt + 1}/{self._retry_times})",
                    extra={"host": self._host}
                )
            except Exception as e:
                logger.warning(
                    f"Ollama 请求异常 (尝试 {attempt + 1}/{self._retry_times}): {str(e)}",
                    extra={"error": str(e)}
                )
            
            # 重试前等待
            if attempt < self._retry_times - 1:
                await self._async_sleep(0.5 * (attempt + 1))

        # 所有重试都失败
        logger.error(
            f"Ollama 向量化失败，已重试 {self._retry_times} 次",
            extra={"text_length": len(text)}
        )
        return np.zeros(self._config.dimension)

    async def embed_batch(
        self,
        texts: List[str],
        normalize: bool = True
    ) -> List[np.ndarray]:
        """
        批量文本向量化

        注意：Ollama 原生不支持批量接口，这里循环调用。
        考虑性能，生产环境可使用 sentence-transformers 直接调用。

        Args:
            texts: 待向量化的文本列表
            normalize: 是否归一化

        Returns:
            向量列表
        """
        if not texts:
            return []

        embeddings = []
        
        for i, text in enumerate(texts):
            vector = await self.embed_single(text, normalize)
            embeddings.append(vector)
            
            # 进度日志
            if (i + 1) % 10 == 0:
                logger.info(
                    f"批量向量化进度",
                    extra={
                        "current": i + 1,
                        "total": len(texts),
                        "progress_percent": round((i + 1) / len(texts) * 100, 1)
                    }
                )

        return embeddings

    def _normalize(self, vector: np.ndarray) -> np.ndarray:
        """
        向量归一化（L2归一化）

        Args:
            vector: 原始向量

        Returns:
            归一化后的向量
        """
        norm = np.linalg.norm(vector)
        if norm > 0:
            return vector / norm
        return vector

    @staticmethod
    async def _async_sleep(seconds: float) -> None:
        """异步等待"""
        import asyncio
        await asyncio.sleep(seconds)


class OllamaClientSync:
    """
    Ollama 向量化客户端（同步版本）

    用于不支持异步的场景。
    """

    def __init__(
        self,
        host: Optional[str] = None,
        model_name: Optional[str] = None,
        timeout: Optional[int] = None,
        retry_times: Optional[int] = None
    ):
        """
        初始化同步客户端

        Args:
            host: Ollama 服务地址
            model_name: 模型名称
            timeout: 超时时间
            retry_times: 重试次数
        """
        self._config = settings.embedding
        self._host = host or self._config.ollama_host
        self._model_name = model_name or self._config.model_name
        self._timeout = timeout or self._config.ollama_timeout
        self._retry_times = retry_times or self._config.ollama_retry_times
        self._client: Optional[httpx.Client] = None

    def _get_client(self) -> httpx.Client:
        """获取同步 HTTP 客户端"""
        if self._client is None:
            self._client = httpx.Client(
                timeout=httpx.Timeout(self._timeout),
                limits=httpx.Limits(max_keepalive_connections=10, max_connections=20)
            )
        return self._client

    def close(self) -> None:
        """关闭客户端"""
        if self._client is not None:
            self._client.close()
            self._client = None

    def health_check(self) -> bool:
        """
        检查 Ollama 服务健康状态（同步版本）

        Returns:
            服务是否健康
        """
        try:
            client = self._get_client()
            response = client.get(f"{self._host}/api/tags")
            return response.status_code == 200
        except Exception as e:
            logger.warning(
                f"Ollama 健康检查失败: {str(e)}",
                extra={"host": self._host}
            )
            return False

    def embed_single(
        self,
        text: str,
        normalize: bool = True
    ) -> np.ndarray:
        """
        单条文本向量化（同步版本）

        Args:
            text: 待向量化的文本
            normalize: 是否归一化

        Returns:
            向量 (numpy 数组)
        """
        if not text or not text.strip():
            return np.zeros(self._config.dimension)

        for attempt in range(self._retry_times):
            try:
                client = self._get_client()
                
                response = client.post(
                    f"{self._host}/api/embeddings",
                    json={
                        "model": self._model_name,
                        "prompt": text
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    embedding = result.get("embedding", [])
                    
                    if not embedding:
                        return np.zeros(self._config.dimension)
                    
                    vector = np.array(embedding)
                    
                    if normalize:
                        vector = self._normalize(vector)
                    
                    return vector
                else:
                    logger.warning(
                        f"Ollama 请求失败: HTTP {response.status_code}",
                        extra={"attempt": attempt + 1}
                    )
                    
            except Exception as e:
                logger.warning(
                    f"Ollama 请求异常: {str(e)}",
                    extra={"attempt": attempt + 1}
                )
            
            if attempt < self._retry_times - 1:
                time.sleep(0.5 * (attempt + 1))

        return np.zeros(self._config.dimension)

    def embed_batch(
        self,
        texts: List[str],
        normalize: bool = True
    ) -> List[np.ndarray]:
        """
        批量文本向量化（同步版本）

        Args:
            texts: 文本列表
            normalize: 是否归一化

        Returns:
            向量列表
        """
        return [self.embed_single(text, normalize) for text in texts]

    def _normalize(self, vector: np.ndarray) -> np.ndarray:
        """向量归一化"""
        norm = np.linalg.norm(vector)
        if norm > 0:
            return vector / norm
        return vector


# 全局客户端实例
_ollama_client: Optional[OllamaClient] = None


class OllamaRerankClient:
    """
    Ollama Cross-Encoder 重排序客户端

    封装 Ollama 的 rerank 接口，用于文档重排序。
    支持模型降级（Ollama 不可用时使用 Mock）。

    Ollama 本身不直接支持 rerank，但可以通过以下方式模拟：
    1. 使用 /api/generate 接口生成相关性评分
    2. 使用本地部署的 Cross-Encoder 模型
    3. 降级到 Mock 评分
    """

    def __init__(
        self,
        host: Optional[str] = None,
        model_name: Optional[str] = None,
        timeout: Optional[int] = None,
        fallback_to_mock: bool = True
    ):
        """
        初始化 Rerank 客户端

        Args:
            host: Ollama 服务地址
            model_name: 模型名称
            timeout: 超时时间
            fallback_to_mock: Ollama 不可用时是否降级到 Mock
        """
        self._config = settings.embedding
        self._host = host or self._config.ollama_host
        self._model_name = model_name or "cross-encoder"  # 重排序模型
        self._timeout = timeout or self._config.ollama_timeout
        self._fallback_to_mock = fallback_to_mock

        self._client: Optional[httpx.Client] = None
        self._is_available: Optional[bool] = None
        self._last_check: float = 0
        self._check_interval: float = 60  # 1分钟检查一次

    def _get_client(self) -> httpx.Client:
        """获取HTTP客户端"""
        if self._client is None:
            self._client = httpx.Client(
                timeout=httpx.Timeout(self._timeout),
                limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
            )
        return self._client

    def close(self) -> None:
        """关闭客户端"""
        if self._client is not None:
            self._client.close()
            self._client = None

    def health_check(self) -> bool:
        """
        健康检查

        检查 Ollama 服务是否可用。

        Returns:
            服务是否可用
        """
        current_time = time.time()

        if self._is_available is not None:
            if current_time - self._last_check < self._check_interval:
                return self._is_available

        try:
            client = self._get_client()
            response = client.get(f"{self._host}/api/tags")

            if response.status_code == 200:
                self._is_available = True
                logger.info(
                    "Ollama Rerank 服务健康检查通过",
                    extra={"host": self._host}
                )
            else:
                self._is_available = False
                logger.warning(
                    f"Ollama Rerank 服务健康检查失败: HTTP {response.status_code}",
                    extra={"host": self._host}
                )

        except Exception as e:
            self._is_available = False
            logger.warning(
                f"Ollama Rerank 服务健康检查异常: {str(e)}",
                extra={"host": self._host, "error": str(e)}
            )

        self._last_check = current_time
        return self._is_available

    def rerank(
        self,
        query: str,
        documents: List[str],
        top_n: int = 10,
        return_documents: bool = True
    ) -> Dict[str, Any]:
        """
        对文档进行重排序

        Args:
            query: 查询文本
            documents: 文档列表
            top_n: 返回前N个结果
            return_documents: 是否返回文档内容

        Returns:
            重排序结果，包含：
            - results: 重排序后的文档列表（按相关性降序）
            - model: 使用的模型
            - usage: 使用统计
        """
        start_time = time.time()

        if not documents:
            return {
                "results": [],
                "model": "mock",
                "usage": {"tokens": 0}
            }

        # 检查 Ollama 是否可用
        if self._is_available is None:
            self.health_check()

        if self._is_available and not self._fallback_to_mock:
            # 尝试使用 Ollama
            try:
                return self._rerank_with_ollama(query, documents, top_n, return_documents)
            except Exception as e:
                logger.warning(f"Ollama Rerank 调用失败: {str(e)}，使用 Mock 评分")
                return self._rerank_with_mock(query, documents, top_n, return_documents)
        else:
            # 使用 Mock 评分
            return self._rerank_with_mock(query, documents, top_n, return_documents)

    def _rerank_with_ollama(
        self,
        query: str,
        documents: List[str],
        top_n: int,
        return_documents: bool
    ) -> Dict[str, Any]:
        """
        使用 Ollama 进行重排序

        注意：Ollama 原生不支持 rerank，这里通过生成相关性评分来模拟。
        实际生产环境中建议使用专门的 Cross-Encoder 模型服务。

        Args:
            query: 查询文本
            documents: 文档列表
            top_n: 返回前N个结果
            return_documents: 是否返回文档内容

        Returns:
            重排序结果
        """
        try:
            client = self._get_client()

            # 构建评分 Prompt
            scored_docs = []

            for i, doc in enumerate(documents):
                prompt = f"""请评估以下查询和文档之间的相关性。
只返回一个0到1之间的分数，其中1表示完全相关，0表示完全不相关。

查询: {query}

文档: {doc[:500]}  # 限制长度

相关性分数:"""

                response = client.post(
                    f"{self._host}/api/generate",
                    json={
                        "model": self._model_name,
                        "prompt": prompt,
                        "stream": False,
                        "options": {"temperature": 0.1}
                    }
                )

                if response.status_code == 200:
                    result = response.json()
                    response_text = result.get("response", "").strip()

                    # 尝试解析分数
                    try:
                        score = float(response_text)
                        score = max(0.0, min(1.0, score))  # 限制在 [0, 1]
                    except ValueError:
                        # 解析失败，使用 Mock 评分
                        score = self._calculate_mock_score(query, doc)

                    scored_docs.append({
                        "index": i,
                        "document": doc,
                        "relevance_score": score
                    })
                else:
                    # API 调用失败，使用 Mock
                    score = self._calculate_mock_score(query, doc)
                    scored_docs.append({
                        "index": i,
                        "document": doc,
                        "relevance_score": score
                    })

            # 按相关性分数降序排序
            scored_docs.sort(key=lambda x: x["relevance_score"], reverse=True)

            # 取前 top_n 个
            top_docs = scored_docs[:top_n]

            # 构建结果
            results = []
            for rank, item in enumerate(top_docs):
                doc_result = {
                    "index": item["index"],
                    "relevance_score": item["relevance_score"],
                    "rank": rank + 1
                }
                if return_documents:
                    doc_result["document"] = item["document"]
                results.append(doc_result)

            cost_ms = int((time.time() - start_time) * 1000)

            logger.info(
                f"Ollama Rerank 完成，耗时: {cost_ms}ms",
                extra={
                    "query_length": len(query),
                    "document_count": len(documents),
                    "returned_count": len(results),
                    "cost_ms": cost_ms
                }
            )

            return {
                "results": results,
                "model": self._model_name,
                "usage": {"tokens": len(query) + sum(len(d) for d in documents)}
            }

        except Exception as e:
            logger.error(f"Ollama Rerank 异常: {str(e)}")
            raise

    def _rerank_with_mock(
        self,
        query: str,
        documents: List[str],
        top_n: int,
        return_documents: bool
    ) -> Dict[str, Any]:
        """
        使用 Mock 评分进行重排序

        当 Ollama 不可用时使用简单的文本重叠计算相关性。

        Args:
            query: 查询文本
            documents: 文档列表
            top_n: 返回前N个结果
            return_documents: 是否返回文档内容

        Returns:
            重排序结果
        """
        start_time = time.time()
        scored_docs = []

        for i, doc in enumerate(documents):
            score = self._calculate_mock_score(query, doc)
            scored_docs.append({
                "index": i,
                "document": doc,
                "relevance_score": score
            })

        # 按相关性分数降序排序
        scored_docs.sort(key=lambda x: x["relevance_score"], reverse=True)

        # 取前 top_n 个
        top_docs = scored_docs[:top_n]

        # 构建结果
        results = []
        for rank, item in enumerate(top_docs):
            doc_result = {
                "index": item["index"],
                "relevance_score": item["relevance_score"],
                "rank": rank + 1
            }
            if return_documents:
                doc_result["document"] = item["document"]
            results.append(doc_result)

        cost_ms = int((time.time() - start_time) * 1000)

        logger.info(
            f"Mock Rerank 完成，耗时: {cost_ms}ms",
            extra={
                "query_length": len(query),
                "document_count": len(documents),
                "returned_count": len(results),
                "cost_ms": cost_ms
            }
        )

        return {
            "results": results,
            "model": "mock",
            "usage": {"tokens": 0}
        }

    def _calculate_mock_score(self, query: str, document: str) -> float:
        """
        计算 Mock 相关性分数

        使用简单的文本重叠计算相关性分数。
        支持中英文混合，使用字符级匹配。

        Args:
            query: 查询文本
            document: 文档文本

        Returns:
            相关性分数 [0, 1]
        """
        if not query or not document:
            return 0.0

        query_lower = query.lower()
        doc_lower = document.lower()

        # 中英文混合处理：按空格分词 + 提取2-4字的词组
        def extract_terms(text: str) -> set:
            terms = set()
            # 空格分词
            for word in text.split():
                if word:
                    terms.add(word)
            # 中文字符序列（2-4字）
            import re
            chinese_terms = re.findall(r'[\u4e00-\u9fff]{2,4}', text)
            terms.update(chinese_terms)
            return terms

        query_terms = extract_terms(query_lower)
        doc_terms = extract_terms(doc_lower)

        if not query_terms or not doc_terms:
            # 如果没有提取到词，使用字符交集
            query_chars = set(query_lower)
            doc_chars = set(doc_lower)
            if query_chars and doc_chars:
                intersection = len(query_chars & doc_chars)
                total = len(query_chars | doc_chars)
                return intersection / total if total > 0 else 0.0
            return 0.0

        # 计算 Jaccard 相似度
        intersection = len(query_terms & doc_terms)
        union = len(query_terms | doc_terms)
        jaccard = intersection / union if union > 0 else 0.0

        # 计算查询覆盖率
        query_coverage = sum(1 for term in query_terms if term in doc_lower) / len(query_terms)

        # 综合评分
        score = 0.6 * jaccard + 0.4 * query_coverage

        return min(1.0, max(0.0, score))


# 全局 Rerank 客户端实例
_ollama_rerank_client: Optional[OllamaRerankClient] = None


def get_ollama_client() -> OllamaClient:
    """
    获取 Ollama 客户端实例（单例模式）

    Returns:
        OllamaClient 实例
    """
    global _ollama_client
    if _ollama_client is None:
        _ollama_client = OllamaClient()
    return _ollama_client


def get_ollama_rerank_client() -> OllamaRerankClient:
    """
    获取 Ollama Rerank 客户端实例

    Returns:
        OllamaRerankClient 实例
    """
    global _ollama_rerank_client
    if _ollama_rerank_client is None:
        _ollama_rerank_client = OllamaRerankClient()
    return _ollama_rerank_client


def close_ollama_clients() -> None:
    """关闭所有 Ollama 客户端"""
    global _ollama_client, _ollama_rerank_client

    if _ollama_client is not None:
        import asyncio
        try:
            asyncio.get_event_loop().run_until_complete(_ollama_client.close())
        except Exception:
            pass
        _ollama_client = None

    if _ollama_rerank_client is not None:
        _ollama_rerank_client.close()
        _ollama_rerank_client = None
