# -*- coding: utf-8 -*-
"""
RabbitMQ消息队列连接模块

本模块提供RabbitMQ消息队列的连接管理：
1. RabbitMQ连接池管理 - 复用长连接
2. 信道多路复用 - 在单个连接上复用多个信道
3. 生产者/消费者管理
4. 消息发布/订阅

设计原则：
- 每个连接可承载成百上千个轻量级的信道（Channel）
- 应用级维护一个长连接池，复用多个信道来处理不同任务
- 避免频繁建立TCP连接的开销，提升吞吐量
- Channel is closed 的根本原因是通道不可用，生产环境必须实现连接池 + 自动重连
- 设置合理的心跳（如 600 秒），并确保服务端配置匹配
- 避免跨线程共享 BlockingConnection
- 启用发布者确认并正确处理异常

使用示例：
    from core.mq import get_mq_client, publish_message

    # 获取连接池客户端
    client = get_mq_client()

    # 发布消息
    publish_message("rag.parse.queue", {"task_id": "xxx"})
"""

import json
import threading
from queue import Queue, Empty
from typing import Any, Dict, List, Optional

import pika
from pika.exceptions import AMQPConnectionError, AMQPChannelError, ChannelWrongStateError

from app.common.logging import logger
from core.config import settings


class RabbitMQConnectionPool:
    """
    RabbitMQ连接池
    
    核心原则：
    1. 复用长连接 - 保持连接活跃，避免频繁创建/销毁
    2. 自动重连 - 连接失效时自动重建
    3. 合理心跳 - 心跳600秒，与服务端配置匹配
    4. 线程安全 - 支持多线程并发访问
    
    注意：避免跨线程共享 BlockingConnection，每个线程使用独立的连接
    """

    def __init__(
        self,
        host: str = None,
        port: int = None,
        username: str = None,
        password: str = None,
        virtual_host: str = "/",
        pool_size: int = 5,
        heartbeat: int = 600,
        connection_timeout: int = 30
    ):
        """
        初始化连接池

        Args:
            host: RabbitMQ主机
            port: RabbitMQ端口
            username: 用户名
            password: 密码
            virtual_host: 虚拟主机
            pool_size: 连接池大小
            heartbeat: 心跳间隔（秒），默认600秒
            connection_timeout: 连接超时（秒）
        """
        self._host = host or settings.rabbitmq.host
        self._port = port or settings.rabbitmq.port
        self._username = username or settings.rabbitmq.username
        self._password = password or settings.rabbitmq.password
        self._virtual_host = virtual_host or settings.rabbitmq.virtual_host
        self._pool_size = pool_size or settings.rabbitmq.get("pool_size", 5)
        self._heartbeat = heartbeat
        self._connection_timeout = connection_timeout
        
        # 连接池
        self._pool: Queue = Queue(maxsize=self._pool_size)
        self._lock = threading.Lock()
        
        # 统计信息
        self._stats = {
            "total_connections": 0,
            "active_connections": 0,
            "total_publish": 0,
            "failed_publish": 0,
            "connection_errors": 0,
            "channel_errors": 0
        }
        self._stats_lock = threading.Lock()
        
        # 初始化连接池
        self._initialize_pool()

    def _get_connection_params(self) -> pika.ConnectionParameters:
        """获取连接参数"""
        credentials = pika.PlainCredentials(
            username=self._username,
            password=self._password
        )
        return pika.ConnectionParameters(
            host=self._host,
            port=self._port,
            virtual_host=self._virtual_host,
            credentials=credentials,
            heartbeat=self._heartbeat,
            connection_attempts=3,
            retry_delay=5,
            blocked_connection_timeout=self._connection_timeout
        )

    def _create_connection(self) -> Optional[pika.BlockingConnection]:
        """创建新连接"""
        try:
            connection = pika.BlockingConnection(self._get_connection_params())
            with self._stats_lock:
                self._stats["total_connections"] += 1
            logger.info(
                f"RabbitMQ连接创建成功",
                extra={
                    "host": self._host,
                    "port": self._port
                }
            )
            return connection
        except Exception as e:
            with self._stats_lock:
                self._stats["connection_errors"] += 1
            logger.error(f"创建RabbitMQ连接失败: {str(e)}")
            return None

    def _is_connection_valid(self, conn: pika.BlockingConnection) -> bool:
        """检查连接是否有效"""
        if conn is None:
            return False
        try:
            return conn.is_open
        except Exception:
            return False

    def _initialize_pool(self) -> None:
        """初始化连接池"""
        logger.info(f"初始化RabbitMQ连接池，大小: {self._pool_size}，心跳: {self._heartbeat}秒")
        
        for i in range(self._pool_size):
            connection = self._create_connection()
            if connection:
                self._pool.put(connection)
                with self._stats_lock:
                    self._stats["active_connections"] += 1

    def get_connection(self) -> Optional[pika.BlockingConnection]:
        """获取连接"""
        retry_count = 0
        max_retries = 3
        
        while retry_count < max_retries:
            try:
                # 尝试从池中获取连接
                try:
                    conn = self._pool.get(timeout=5)
                except Empty:
                    # 池为空，尝试创建新连接
                    with self._lock:
                        if self._pool.maxsize > self._pool_size:
                            # 允许临时扩容
                            pass
                        else:
                            # 等待
                            conn = self._pool.get(timeout=30)
                
                # 检查连接是否有效
                if not self._is_connection_valid(conn):
                    logger.warning("连接已关闭，重新创建")
                    conn = self._create_connection()
                    if not conn:
                        retry_count += 1
                        continue
                
                return conn
                
            except Empty:
                logger.error("获取RabbitMQ连接超时")
                return None
            except Exception as e:
                logger.warning(f"获取连接失败 (重试 {retry_count + 1}): {str(e)}")
                retry_count += 1
        
        return None

    def release_connection(self, conn: Optional[pika.BlockingConnection]) -> None:
        """释放连接回池中"""
        if conn is None:
            return
            
        try:
            if self._is_connection_valid(conn):
                self._pool.put(conn)
            else:
                # 连接无效，丢弃并新建补充
                logger.warning("连接无效，丢弃并新建")
                try:
                    conn.close()
                except Exception:
                    pass
                new_conn = self._create_connection()
                if new_conn:
                    self._pool.put(new_conn)
                else:
                    # 无法创建新连接，池大小临时减少
                    with self._stats_lock:
                        self._stats["active_connections"] -= 1
        except Exception as e:
            logger.warning(f"释放连接失败: {str(e)}")

    def publish(
        self,
        exchange: str,
        routing_key: str,
        message: Dict[str, Any],
        properties: Optional[pika.BasicProperties] = None
    ) -> bool:
        """
        发布消息

        Args:
            exchange: 交换机名称
            routing_key: 路由键
            message: 消息内容
            properties: 消息属性

        Returns:
            是否发布成功
        """
        conn = None
        try:
            # 获取连接
            conn = self.get_connection()
            if not conn:
                logger.error("无法获取RabbitMQ连接")
                with self._stats_lock:
                    self._stats["failed_publish"] += 1
                return False
            
            # 创建信道并发布
            channel = conn.channel()
            
            # 设置默认属性
            if properties is None:
                properties = pika.BasicProperties(
                    delivery_mode=2,  # 持久化
                    content_type="application/json"
                )
            
            # 发布消息
            channel.basic_publish(
                exchange=exchange,
                routing_key=routing_key,
                body=json.dumps(message, ensure_ascii=False),
                properties=properties
            )
            
            with self._stats_lock:
                self._stats["total_publish"] += 1
            
            logger.debug(
                f"消息发布成功",
                extra={
                    "routing_key": routing_key,
                    "task_id": message.get("task_id")
                }
            )
            return True
            
        except ChannelWrongStateError as e:
            # Channel关闭，丢弃连接
            logger.warning(f"Channel错误，丢弃连接: {str(e)}")
            with self._stats_lock:
                self._stats["failed_publish"] += 1
                self._stats["channel_errors"] += 1
            # 连接会被丢弃，在release_connection中会新建
            return False
            
        except AMQPConnectionError as e:
            # 连接错误
            logger.error(f"连接错误: {str(e)}")
            with self._stats_lock:
                self._stats["failed_publish"] += 1
                self._stats["connection_errors"] += 1
            # 关闭无效连接
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass
            return False
            
        except Exception as e:
            logger.error(f"消息发布失败: {str(e)}")
            with self._stats_lock:
                self._stats["failed_publish"] += 1
            return False
            
        finally:
            # 释放连接
            if conn:
                self.release_connection(conn)

    def get_stats(self) -> Dict[str, Any]:
        """获取连接池统计信息"""
        with self._stats_lock:
            stats = self._stats.copy()
        
        stats["pool_size"] = self._pool_size
        stats["pool_available"] = self._pool.qsize()
        stats["pool_max"] = self._pool.maxsize
        
        return stats

    def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        healthy = 0
        unhealthy = 0
        
        # 检查池中连接
        temp_items = []
        while not self._pool.empty():
            try:
                conn = self._pool.get_nowait()
                if self._is_connection_valid(conn):
                    healthy += 1
                    temp_items.append(conn)
                else:
                    unhealthy += 1
                    try:
                        conn.close()
                    except Exception:
                        pass
            except Empty:
                break
        
        # 放回有效连接
        for conn in temp_items:
            self._pool.put(conn)
        
        # 补充缺失的连接
        while unhealthy > 0 and (healthy + unhealthy) < self._pool_size:
            new_conn = self._create_connection()
            if new_conn:
                self._pool.put(new_conn)
                healthy += 1
            unhealthy -= 1
        
        return {
            "healthy": healthy > 0,
            "healthy_connections": healthy,
            "unhealthy_connections": unhealthy,
            "pool_size": self._pool_size
        }

    def close_all(self) -> None:
        """关闭所有连接"""
        logger.info("关闭RabbitMQ连接池...")
        
        while not self._pool.empty():
            try:
                conn = self._pool.get_nowait()
                try:
                    if conn.is_open:
                        conn.close()
                except Exception:
                    pass
            except Empty:
                break
        
        with self._stats_lock:
            self._stats["active_connections"] = 0
        
        logger.info("RabbitMQ连接池已关闭")


class RabbitMQClient:
    """
    RabbitMQ客户端封装类

    基于连接池的RabbitMQ客户端，提供消息队列的操作方法。
    """

    def __init__(self):
        """初始化RabbitMQ客户端"""
        self._pool = RabbitMQConnectionPool(
            host=settings.rabbitmq.host,
            port=settings.rabbitmq.port,
            username=settings.rabbitmq.username,
            password=settings.rabbitmq.password,
            virtual_host=settings.rabbitmq.virtual_host,
            pool_size=settings.rabbitmq.pool_size or 5,
            heartbeat=600,  # 600秒心跳
            connection_timeout=settings.rabbitmq.connection_timeout
        )
        self._exchange_name = settings.rabbitmq.exchange.name
        self._exchange_type = settings.rabbitmq.exchange.type
        self._is_initialized = False

    def _get_init_connection(self):
        """获取初始化专用的连接"""
        import pika
        credentials = pika.PlainCredentials(
            username=settings.rabbitmq.username,
            password=settings.rabbitmq.password
        )
        params = pika.ConnectionParameters(
            host=settings.rabbitmq.host,
            port=settings.rabbitmq.port,
            virtual_host=settings.rabbitmq.virtual_host,
            credentials=credentials,
            heartbeat=600
        )
        return pika.BlockingConnection(params)

    def initialize(self) -> None:
        """初始化客户端，创建交换机和队列"""
        if self._is_initialized:
            return
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                conn = self._get_init_connection()
                try:
                    channel = conn.channel()
                    
                    # 声明交换机
                    channel.exchange_declare(
                        exchange=self._exchange_name,
                        exchange_type=self._exchange_type,
                        durable=settings.rabbitmq.exchange.durable
                    )
                    
                    # 声明死信交换机
                    dlx_exchange = settings.rabbitmq.dead_letter.exchange
                    channel.exchange_declare(
                        exchange=dlx_exchange,
                        exchange_type="direct",
                        durable=settings.rabbitmq.dead_letter.durable
                    )
                    
                    # 声明死信队列
                    dlx_queue = settings.rabbitmq.dead_letter.queue
                    channel.queue_declare(
                        queue=dlx_queue,
                        durable=settings.rabbitmq.dead_letter.durable
                    )
                    channel.queue_bind(
                        queue=dlx_queue,
                        exchange=dlx_exchange,
                        routing_key=settings.rabbitmq.dead_letter.routing_key
                    )
                    
                    # 声明所有队列（每个队列使用独立的channel）
                    for queue_key, queue_config in settings.rabbitmq.queues.items():
                        queue_name = queue_config.name
                        try:
                            # 为每个队列创建新的channel，避免一个失败影响其他
                            q_channel = conn.channel()
                            try:
                                # 尝试删除旧队列（如果参数不匹配）
                                try:
                                    q_channel.queue_delete(queue=queue_name)
                                except Exception:
                                    pass
                                
                                # 重新声明队列
                                q_channel.queue_declare(
                                    queue=queue_name,
                                    durable=queue_config.durable,
                                    arguments={
                                        "x-dead-letter-exchange": dlx_exchange,
                                        "x-dead-letter-routing-key": settings.rabbitmq.dead_letter.routing_key
                                    }
                                )
                                q_channel.queue_bind(
                                    queue=queue_name,
                                    exchange=self._exchange_name,
                                    routing_key=queue_config.routing_key
                                )
                                logger.info(f"队列 {queue_name} 声明并绑定成功")
                            finally:
                                try:
                                    q_channel.close()
                                except Exception:
                                    pass
                        except Exception as e:
                            logger.warning(f"声明队列 {queue_name} 失败: {str(e)}")
                    
                    self._is_initialized = True
                    logger.info("RabbitMQ客户端初始化成功")
                    return
                    
                finally:
                    try:
                        conn.close()
                    except Exception:
                        pass
                        
            except Exception as e:
                logger.warning(f"RabbitMQ初始化失败 (尝试 {attempt + 1}/{max_retries}): {str(e)}")
                if attempt == max_retries - 1:
                    logger.error(f"RabbitMQ客户端初始化失败: {str(e)}")
                    # 不抛出异常，让服务可以继续运行

    def publish(
        self,
        routing_key: str,
        message: Dict[str, Any],
        properties: Optional[pika.BasicProperties] = None
    ) -> bool:
        """发布消息"""
        return self._pool.publish(
            exchange=self._exchange_name,
            routing_key=routing_key,
            message=message,
            properties=properties
        )

    def disconnect(self) -> None:
        """断开连接池"""
        self._pool.close_all()
        logger.info("RabbitMQ客户端连接池已关闭")

    def is_connected(self) -> bool:
        """检查是否已连接"""
        health = self._pool.health_check()
        return health.get("healthy", False)

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "pool_stats": self._pool.get_stats(),
            "initialized": self._is_initialized
        }


class MessagePublisher:
    """消息发布器（单例模式）"""
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._client = RabbitMQClient()
        self._client.initialize()
        self._initialized = True

    def publish_parse_task(self, task_data: Dict[str, Any]) -> bool:
        """发布解析任务"""
        return self._client.publish(routing_key="rag.parse.start", message=task_data)

    def publish_clean_task(self, task_data: Dict[str, Any]) -> bool:
        """发布清洗任务"""
        return self._client.publish(routing_key="rag.clean.start", message=task_data)

    def publish_chunk_task(self, task_data: Dict[str, Any]) -> bool:
        """发布切分任务"""
        return self._client.publish(routing_key="rag.chunk.start", message=task_data)

    def publish_embedding_task(self, task_data: Dict[str, Any]) -> bool:
        """发布向量化任务"""
        return self._client.publish(routing_key="rag.embedding.start", message=task_data)


# 全局客户端实例
_mq_client: Optional[RabbitMQClient] = None


def get_mq_client() -> RabbitMQClient:
    """获取RabbitMQ客户端实例"""
    global _mq_client
    if _mq_client is None:
        _mq_client = RabbitMQClient()
        _mq_client.initialize()
    return _mq_client


def close_mq_client() -> None:
    """关闭RabbitMQ客户端"""
    global _mq_client
    if _mq_client is not None:
        _mq_client.disconnect()
        _mq_client = None


def publish_message(routing_key: str, message: Dict[str, Any]) -> bool:
    """快捷发布消息"""
    client = get_mq_client()
    return client.publish(routing_key, message)


def init_mq() -> RabbitMQClient:
    """初始化RabbitMQ"""
    client = get_mq_client()
    logger.info("RabbitMQ初始化完成")
    return client


def get_mq_stats() -> Dict[str, Any]:
    """获取RabbitMQ统计信息"""
    client = get_mq_client()
    return client.get_stats()
