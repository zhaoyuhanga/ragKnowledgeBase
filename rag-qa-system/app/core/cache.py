"""
RAG 问答系统 - Redis 缓存模块
热点问答缓存和会话管理
"""

import json
from typing import Optional, Any

import redis

from app.config import settings
from app.core.logger import get_logger

logger = get_logger(__name__)


class RedisCache:
    """
    Redis 缓存管理器
    提供问答缓存和会话存储功能
    """

    _instance: Optional["RedisCache"] = None
    _client: Optional[redis.Redis] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if RedisCache._client is not None:
            return
        self._initialize()

    def _initialize(self):
        """初始化 Redis 连接"""
        logger.info("正在初始化 Redis 连接...")

        try:
            RedisCache._client = redis.Redis(
                host=settings.redis_host,
                port=settings.redis_port,
                db=settings.redis_db,
                password=settings.redis_password if settings.redis_password else None,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
            )

            self._client.ping()
            logger.info("Redis 连接初始化完成")

        except redis.ConnectionError as e:
            logger.warning(f"Redis 连接失败，将禁用缓存功能: {str(e)}")
            RedisCache._client = None
        except Exception as e:
            logger.error(f"Redis 初始化异常: {str(e)}")
            RedisCache._client = None

    @property
    def client(self) -> Optional[redis.Redis]:
        """获取 Redis 客户端"""
        return RedisCache._client

    @property
    def is_available(self) -> bool:
        """检查 Redis 是否可用"""
        if self._client is None:
            return False
        try:
            self._client.ping()
            return True
        except:
            return False

    def _make_key(self, key: str) -> str:
        """生成带前缀的键名"""
        return f"{settings.redis_key_prefix}{key}"

    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        if not self.is_available:
            return None

        try:
            full_key = self._make_key(key)
            value = self._client.get(full_key)

            if value is None:
                return None

            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value

        except Exception as e:
            logger.warning(f"获取缓存失败: {key}, {str(e)}")
            return None

    def set(
        self,
        key: str,
        value: Any,
        ttl: int = None
    ) -> bool:
        """设置缓存值"""
        if not self.is_available:
            return False

        try:
            full_key = self._make_key(key)

            if isinstance(value, (dict, list)):
                value = json.dumps(value, ensure_ascii=False)

            ttl = ttl or settings.cache_default_ttl

            self._client.setex(full_key, ttl, value)
            logger.debug(f"缓存已设置: {key}, TTL={ttl}s")
            return True

        except Exception as e:
            logger.warning(f"设置缓存失败: {key}, {str(e)}")
            return False

    def delete(self, key: str) -> bool:
        """删除缓存"""
        if not self.is_available:
            return False

        try:
            full_key = self._make_key(key)
            self._client.delete(full_key)
            logger.debug(f"缓存已删除: {key}")
            return True
        except Exception as e:
            logger.warning(f"删除缓存失败: {key}, {str(e)}")
            return False

    def clear_pattern(self, pattern: str) -> int:
        """删除匹配模式的所有缓存"""
        if not self.is_available:
            return 0

        try:
            full_pattern = self._make_key(pattern)
            keys = self._client.keys(full_pattern)

            if keys:
                count = self._client.delete(*keys)
                logger.info(f"已删除 {count} 个缓存键")
                return count
            return 0
        except Exception as e:
            logger.warning(f"批量删除缓存失败: {pattern}, {str(e)}")
            return 0

    def clear_all(self) -> bool:
        """清空所有应用缓存"""
        return self.clear_pattern("*") > 0

    def get_qa_cache(self, question: str) -> Optional[dict]:
        """获取问答缓存"""
        import hashlib
        key = f"qa:{hashlib.md5(question.encode()).hexdigest()}"
        return self.get(key)

    def set_qa_cache(
        self,
        question: str,
        answer: str,
        sources: list = None,
        ttl: int = 3600
    ) -> bool:
        """设置问答缓存"""
        import hashlib
        key = f"qa:{hashlib.md5(question.encode()).hexdigest()}"

        value = {
            "answer": answer,
            "sources": sources or [],
        }

        return self.set(key, value, ttl)

    def check_health(self) -> bool:
        """检查 Redis 健康状态"""
        if not self.is_available:
            return False

        try:
            return self._client.ping()
        except:
            return False


# 全局缓存实例
redis_cache = RedisCache()


def get_redis_cache() -> RedisCache:
    """获取缓存实例"""
    return redis_cache
