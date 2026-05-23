# -*- coding: utf-8 -*-
"""
Redis缓存模块

本模块提供Redis缓存管理：
1. Redis连接配置
2. 缓存操作接口
3. Embedding缓存

使用示例：
    from core.cache import get_redis_client, cache_embedding

    # 获取客户端
    client = get_redis_client()

    # 缓存向量
    cache_embedding("query_hash", embedding_vector)
"""

import json
from typing import Any, List, Optional

import redis

from app.common.logging import logger
from core.config import settings


# 全局客户端实例
_redis_client: Optional[redis.Redis] = None


class RedisClient:
    """
    Redis客户端封装类

    提供缓存的操作方法。
    """

    def __init__(self):
        """初始化Redis客户端"""
        self._client: Optional[redis.Redis] = None

    def connect(self) -> redis.Redis:
        """
        连接到Redis服务器

        Returns:
            Redis客户端实例
        """
        if self._client is None:
            self._client = redis.Redis(
                host=settings.redis.host,
                port=settings.redis.port,
                password=settings.redis.password if settings.redis.password else None,
                db=settings.redis.db,
                decode_responses=settings.redis.decode_responses,
                socket_timeout=settings.redis.socket_timeout,
                socket_connect_timeout=settings.redis.socket_connect_timeout
            )

            # 测试连接
            try:
                self._client.ping()
                logger.info(
                    "Redis连接成功",
                    extra={
                        "host": settings.redis.host,
                        "port": settings.redis.port
                    }
                )
            except redis.ConnectionError as e:
                logger.error(
                    f"Redis连接失败: {str(e)}",
                    extra={
                        "host": settings.redis.host,
                        "port": settings.redis.port,
                        "error": str(e)
                    }
                )
                raise

        return self._client

    def disconnect(self) -> None:
        """
        断开Redis连接
        """
        if self._client:
            self._client.close()
            self._client = None
            logger.info("Redis连接已断开")

    def is_connected(self) -> bool:
        """
        检查是否已连接

        Returns:
            是否已连接
        """
        if self._client is None:
            return False
        try:
            return self._client.ping()
        except Exception:
            return False

    def get(self, key: str) -> Optional[str]:
        """
        获取值

        Args:
            key: 键

        Returns:
            值，如果不存在返回None
        """
        return self._client.get(key)

    def set(
        self,
        key: str,
        value: str,
        ex: Optional[int] = None
    ) -> bool:
        """
        设置值

        Args:
            key: 键
            value: 值
            ex: 过期时间（秒）

        Returns:
            是否设置成功
        """
        return self._client.set(key, value, ex=ex)

    def delete(self, key: str) -> int:
        """
        删除键

        Args:
            key: 键

        Returns:
            删除的键数量
        """
        return self._client.delete(key)

    def exists(self, key: str) -> bool:
        """
        检查键是否存在

        Args:
            key: 键

        Returns:
            是否存在
        """
        return self._client.exists(key)

    def hget(self, name: str, key: str) -> Optional[str]:
        """
        获取哈希字段值

        Args:
            name: 哈希名称
            key: 字段

        Returns:
            字段值
        """
        return self._client.hget(name, key)

    def hset(self, name: str, key: str, value: str) -> int:
        """
        设置哈希字段值

        Args:
            name: 哈希名称
            key: 字段
            value: 值

        Returns:
            是否设置成功
        """
        return self._client.hset(name, key, value)

    def hgetall(self, name: str) -> dict:
        """
        获取所有哈希字段

        Args:
            name: 哈希名称

        Returns:
            所有字段和值
        """
        return self._client.hgetall(name)

    def incr(self, key: str) -> int:
        """
        递增

        Args:
            key: 键

        Returns:
            递增后的值
        """
        return self._client.incr(key)


def get_redis_client() -> redis.Redis:
    """
    获取Redis客户端实例

    Returns:
        Redis客户端实例
    """
    global _redis_client
    if _redis_client is None:
        _redis_client = RedisClient()
        return _redis_client.connect()
    return _redis_client


def close_redis_client() -> None:
    """
    关闭Redis客户端
    """
    global _redis_client
    if _redis_client is not None:
        if isinstance(_redis_client, RedisClient):
            _redis_client.disconnect()
        else:
            _redis_client.close()
        _redis_client = None


# Embedding缓存管理
class EmbeddingCache:
    """
    Embedding缓存管理器

    管理查询和文档向量的缓存。
    """

    QUERY_CACHE_PREFIX = "embedding:query:"
    DOC_CACHE_PREFIX = "embedding:doc:"

    def __init__(self, client: Optional[redis.Redis] = None):
        """
        初始化缓存管理器

        Args:
            client: Redis客户端实例
        """
        self._client = client or get_redis_client()
        self._ttl = settings.cache.embedding.get("ttl", 86400)

    def _normalize_query(self, query: str) -> str:
        """
        标准化查询文本

        Args:
            query: 原始查询

        Returns:
            标准化后的查询
        """
        import re
        # 去除多余空格、标点归一化、统一大小写
        query = re.sub(r'\s+', ' ', query)
        query = query.lower().strip()
        return query

    def _compute_hash(self, text: str) -> str:
        """
        计算文本哈希

        Args:
            text: 文本内容

        Returns:
            SHA256哈希
        """
        import hashlib
        normalized = self._normalize_query(text)
        return hashlib.sha256(normalized.encode()).hexdigest()

    def get_query_embedding(self, query: str) -> Optional[List[float]]:
        """
        获取查询向量缓存

        Args:
            query: 查询文本

        Returns:
            向量列表，如果不存在返回None
        """
        key = self.QUERY_CACHE_PREFIX + self._compute_hash(query)
        data = self._client.get(key)
        if data:
            return json.loads(data)
        return None

    def set_query_embedding(
        self,
        query: str,
        embedding: List[float],
        ttl: Optional[int] = None
    ) -> bool:
        """
        缓存查询向量

        Args:
            query: 查询文本
            embedding: 向量列表
            ttl: 过期时间（秒）

        Returns:
            是否设置成功
        """
        key = self.QUERY_CACHE_PREFIX + self._compute_hash(query)
        return self._client.set(
            key,
            json.dumps(embedding),
            ex=ttl or self._ttl
        )

    def get_doc_embedding(self, doc_id: str) -> Optional[List[float]]:
        """
        获取文档向量缓存

        Args:
            doc_id: 文档ID

        Returns:
            向量列表，如果不存在返回None
        """
        key = self.DOC_CACHE_PREFIX + doc_id
        data = self._client.get(key)
        if data:
            return json.loads(data)
        return None

    def set_doc_embedding(
        self,
        doc_id: str,
        embedding: List[float],
        ttl: Optional[int] = None
    ) -> bool:
        """
        缓存文档向量

        Args:
            doc_id: 文档ID
            embedding: 向量列表
            ttl: 过期时间（秒）

        Returns:
            是否设置成功
        """
        key = self.DOC_CACHE_PREFIX + doc_id
        return self._client.set(
            key,
            json.dumps(embedding),
            ex=ttl or self._ttl
        )

    def delete_doc_embedding(self, doc_id: str) -> int:
        """
        删除文档向量缓存

        Args:
            doc_id: 文档ID

        Returns:
            删除的键数量
        """
        key = self.DOC_CACHE_PREFIX + doc_id
        return self._client.delete(key)


# 全局缓存实例
_embedding_cache: Optional[EmbeddingCache] = None


def get_embedding_cache() -> EmbeddingCache:
    """
    获取Embedding缓存实例

    Returns:
        EmbeddingCache: Embedding缓存管理器
    """
    global _embedding_cache
    if _embedding_cache is None:
        _embedding_cache = EmbeddingCache()
    return _embedding_cache
