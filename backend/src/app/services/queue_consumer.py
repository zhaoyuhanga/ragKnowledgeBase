# -*- coding: utf-8 -*-
"""
RabbitMQ消息队列消费者模块

本模块提供队列消息的消费者实现：
1. QueueConsumer 基类 - 提供通用消费者功能
2. 消息确认机制
3. 错误处理和重试
4. 死信队列处理
"""

import json
import signal
import threading
import time
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Callable, Dict, Optional

import pika
from pika.adapters.blocking_connection import BlockingChannel
from pika.exceptions import AMQPConnectionError, AMQPChannelError, ChannelClosedByBroker, ChannelWrongStateError

from app.common.logging import logger
from app.schemas.queue import (
    DeadLetterMessage,
    QueueName,
    RoutingKey,
    TaskMessage,
    TaskStatus,
    WorkerConfig,
)
from core.config import settings


class QueueConsumer(ABC):
    """
    队列消息消费者基类

    提供通用的消息消费功能，子类需要实现 process_message 方法。
    """

    def __init__(self, config: Optional[WorkerConfig] = None):
        """
        初始化消费者

        Args:
            config: Worker配置
        """
        self._config = config or self._get_default_config()
        self._connection: Optional[pika.BlockingConnection] = None
        self._channel: Optional[BlockingChannel] = None
        self._exchange_name = settings.rabbitmq.exchange.name
        self._is_running = False
        self._lock = threading.Lock()

        # 统计信息
        self._stats = {
            "consumed_total": 0,
            "success_total": 0,
            "failed_total": 0,
            "retry_total": 0,
        }

    @abstractmethod
    def _get_default_config(self) -> WorkerConfig:
        """获取默认配置，子类必须实现"""
        pass

    @abstractmethod
    def process_message(self, message: Dict[str, Any]) -> bool:
        """
        处理消息的核心方法，子类必须实现

        Args:
            message: 消息内容

        Returns:
            是否处理成功
        """
        pass

    @abstractmethod
    def get_routing_key(self) -> str:
        """获取监听的路由键"""
        pass

    def connect(self) -> None:
        """
        连接到RabbitMQ服务器
        """
        if self._connection and self._connection.is_open:
            return

        with self._lock:
            if self._connection and self._connection.is_open:
                return

            try:
                credentials = pika.PlainCredentials(
                    username=settings.rabbitmq.username,
                    password=settings.rabbitmq.password
                )

                parameters = pika.ConnectionParameters(
                    host=settings.rabbitmq.host,
                    port=settings.rabbitmq.port,
                    virtual_host=settings.rabbitmq.virtual_host,
                    credentials=credentials,
                    heartbeat=settings.rabbitmq.heartbeat,
                    connection_attempts=3,
                    retry_delay=5
                )

                self._connection = pika.BlockingConnection(parameters)
                self._channel = self._connection.channel()

                # 声明交换机
                self._channel.exchange_declare(
                    exchange=self._exchange_name,
                    exchange_type=settings.rabbitmq.exchange.type,
                    durable=settings.rabbitmq.exchange.durable
                )

                # 设置死信交换机
                self._setup_dlx()

                # 声明队列
                self._setup_queue()

                logger.info(
                    f"消费者连接成功",
                    extra={
                        "worker_name": self._config.worker_name,
                        "queue_name": self._config.queue_name
                    }
                )

            except AMQPConnectionError as e:
                logger.error(
                    f"消费者连接失败: {str(e)}",
                    extra={
                        "worker_name": self._config.worker_name,
                        "error": str(e)
                    }
                )
                raise

    def _setup_dlx(self) -> None:
        """设置死信交换机和队列"""
        dlx_name = "rag_dlx_exchange"
        dlx_queue = QueueName.DLX_QUEUE.value

        # 声明死信交换机
        self._channel.exchange_declare(
            exchange=dlx_name,
            exchange_type="direct",
            durable=True
        )

        # 声明死信队列
        self._channel.queue_declare(
            queue=dlx_queue,
            durable=True
        )

        # 绑定死信队列
        self._channel.queue_bind(
            queue=dlx_queue,
            exchange=dlx_name,
            routing_key="dlx"
        )

        logger.info("死信队列设置完成")

    def _setup_queue(self) -> None:
        """设置工作队列"""
        queue_name = self._config.queue_name

        # 直接声明队列，让 RabbitMQ 自动处理
        try:
            self._channel.queue_declare(
                queue=queue_name,
                durable=True,
                arguments={
                    "x-dead-letter-exchange": "rag_dlx_exchange",
                    "x-dead-letter-routing-key": "dlx"
                }
            )
            logger.info(
                f"队列 {queue_name} 声明成功",
                extra={"queue_name": queue_name}
            )
        except pika.exceptions.ChannelClosedByBroker as e:
            error_str = str(e)
            if "PRECONDITION_FAILED" in error_str or "inequivalent" in error_str:
                logger.info(
                    f"队列 {queue_name} 已存在但参数不同，保持现有配置",
                    extra={"queue_name": queue_name}
                )
            else:
                raise
        except Exception as e:
            logger.warning(
                f"声明队列 {queue_name} 失败: {str(e)}",
                extra={"queue_name": queue_name}
            )

        # 绑定队列到交换机
        routing_key = self.get_routing_key()
        try:
            self._channel.queue_bind(
                queue=queue_name,
                exchange=self._exchange_name,
                routing_key=routing_key
            )
            logger.info(
                f"队列 {queue_name} 已绑定到交换机",
                extra={
                    "queue_name": queue_name,
                    "routing_key": routing_key
                }
            )
        except pika.exceptions.ChannelClosedByBroker as e:
            error_str = str(e)
            if "inequivalent" in error_str or "PRECONDITION_FAILED" in error_str:
                logger.info(
                    f"队列 {queue_name} 已绑定，跳过",
                    extra={"queue_name": queue_name}
                )
            else:
                logger.warning(
                    f"绑定队列 {queue_name} 失败: {error_str}",
                    extra={"queue_name": queue_name}
                )
        except Exception as e:
            logger.warning(
                f"绑定队列 {queue_name} 失败: {str(e)}",
                extra={"queue_name": queue_name}
            )

    def disconnect(self) -> None:
        """
        断开RabbitMQ连接
        """
        with self._lock:
            if self._connection and self._connection.is_open:
                self._connection.close()
                logger.info(
                    f"消费者连接已断开",
                    extra={"worker_name": self._config.worker_name}
                )

    def _on_message(
        self,
        channel: BlockingChannel,
        method: pika.spec.Basic.Deliver,
        properties: pika.BasicProperties,
        body: bytes
    ) -> None:
        """
        消息处理回调

        Args:
            channel: 通道
            method: 投递信息
            properties: 消息属性
            body: 消息体
        """
        delivery_tag = method.delivery_tag
        start_time = time.time()

        try:
            # 解析消息
            message = json.loads(body.decode("utf-8"))
            logger.info(
                f"收到消息",
                extra={
                    "worker_name": self._config.worker_name,
                    "task_id": message.get("task_id"),
                    "task_type": message.get("task_type")
                }
            )

            # 检查是否超过最大重试次数
            retry_count = message.get("retry_count", 0)
            max_retry = message.get("max_retry", self._config.max_retry)

            if retry_count >= max_retry:
                # 超过最大重试次数，发送到死信队列
                self._send_to_dlx(message, "MAX_RETRY_EXCEEDED", "超过最大重试次数")
                channel.basic_ack(delivery_tag=delivery_tag)

                logger.warning(
                    f"消息超过最大重试次数，发送到死信队列",
                    extra={
                        "worker_name": self._config.worker_name,
                        "task_id": message.get("task_id"),
                        "retry_count": retry_count
                    }
                )
                return

            # 处理消息
            success = self.process_message(message)
            self._stats["consumed_total"] += 1

            if success:
                channel.basic_ack(delivery_tag=delivery_tag)
                self._stats["success_total"] += 1

                cost_time = int((time.time() - start_time) * 1000)
                logger.info(
                    f"消息处理成功",
                    extra={
                        "worker_name": self._config.worker_name,
                        "task_id": message.get("task_id"),
                        "cost_ms": cost_time
                    }
                )
            else:
                # 处理失败，根据配置决定是否重试
                self._handle_failure(channel, method, properties, message, None)

        except json.JSONDecodeError as e:
            # JSON解析失败，发送到死信队列
            self._stats["failed_total"] += 1
            self._send_to_dlx(
                {"raw_body": body.decode("utf-8", errors="replace")},
                "JSON_DECODE_ERROR",
                f"JSON解析失败: {str(e)}"
            )
            channel.basic_ack(delivery_tag=delivery_tag)

            logger.error(
                f"消息JSON解析失败",
                extra={
                    "worker_name": self._config.worker_name,
                    "error": str(e)
                }
            )

        except Exception as e:
            self._handle_failure(channel, method, properties, None, e)

    def _handle_failure(
        self,
        channel: BlockingChannel,
        method: pika.spec.Basic.Deliver,
        properties: pika.BasicProperties,
        message: Optional[Dict[str, Any]],
        error: Optional[Exception]
    ) -> None:
        """
        处理消息处理失败的情况

        Args:
            channel: 通道
            method: 投递信息
            properties: 消息属性
            message: 消息内容
            error: 异常对象
        """
        delivery_tag = method.delivery_tag
        error_msg = str(error) if error else "Unknown error"

        self._stats["failed_total"] += 1

        if message:
            retry_count = message.get("retry_count", 0)
            max_retry = message.get("max_retry", self._config.max_retry)

            if self._config.enable_retry and retry_count < max_retry:
                # 启用重试，增加重试计数后重新发布
                message["retry_count"] = retry_count + 1
                message["last_error"] = error_msg
                message["last_retry_at"] = datetime.now().isoformat()

                # 延迟重新发布
                time.sleep(self._config.retry_delay_seconds)

                # 重新发布到队列
                routing_key = self.get_routing_key()
                self._channel.basic_publish(
                    exchange=self._exchange_name,
                    routing_key=routing_key,
                    body=json.dumps(message, ensure_ascii=False),
                    properties=pika.BasicProperties(delivery_mode=2)
                )

                self._stats["retry_total"] += 1

                logger.warning(
                    f"消息处理失败，准备重试",
                    extra={
                        "worker_name": self._config.worker_name,
                        "task_id": message.get("task_id"),
                        "retry_count": retry_count + 1,
                        "error": error_msg
                    }
                )

                channel.basic_ack(delivery_tag=delivery_tag)
            else:
                # 不启用重试或超过最大次数，发送到死信队列
                self._send_to_dlx(message, type(error).__name__ if error else "PROCESS_FAILED", error_msg)
                channel.basic_ack(delivery_tag=delivery_tag)

                logger.error(
                    f"消息处理失败，已发送到死信队列",
                    extra={
                        "worker_name": self._config.worker_name,
                        "task_id": message.get("task_id"),
                        "error": error_msg
                    }
                )
        else:
            # 无法解析消息，直接发送到死信队列
            self._send_to_dlx(
                {"raw_body": method.routing_key},
                type(error).__name__ if error else "PROCESS_FAILED",
                error_msg
            )
            channel.basic_ack(delivery_tag=delivery_tag)

    def _send_to_dlx(
        self,
        message: Dict[str, Any],
        error_type: str,
        error_message: str
    ) -> None:
        """
        发送消息到死信队列

        Args:
            message: 原始消息
            error_type: 错误类型
            error_message: 错误信息
        """
        dlx_message = DeadLetterMessage(
            original_message=message,
            error_type=error_type,
            error_message=error_message,
            error_stack=None,
            retry_count=message.get("retry_count", 0),
            original_queue=self._config.queue_name
        )

        try:
            self._channel.basic_publish(
                exchange="rag_dlx_exchange",
                routing_key="dlx",
                body=json.dumps(dlx_message.model_dump(), ensure_ascii=False, default=str),
                properties=pika.BasicProperties(delivery_mode=2)
            )
        except Exception as e:
            logger.error(
                f"发送死信消息失败: {str(e)}",
                extra={"error": str(e)}
            )

    def start_consuming(self) -> None:
        """开始消费消息"""
        self.connect()

        if not self._channel:
            raise RuntimeError("Channel未初始化")

        # 设置QoS
        self._channel.basic_qos(prefetch_count=self._config.prefetch_count)

        # 注册信号处理
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        self._is_running = True

        logger.info(
            f"开始消费",
            extra={
                "worker_name": self._config.worker_name,
                "queue_name": self._config.queue_name,
                "routing_key": self.get_routing_key()
            }
        )

        while self._is_running:
            try:
                self._channel.basic_consume(
                    queue=self._config.queue_name,
                    on_message_callback=self._on_message,
                    auto_ack=False
                )
                self._channel.start_consuming()
            except (AMQPConnectionError, ChannelClosedByBroker, ChannelWrongStateError, AMQPChannelError) as e:
                if self._is_running:
                    logger.warning(
                        f"连接断开，准备重连: {str(e)}",
                        extra={"worker_name": self._config.worker_name}
                    )
                    self._channel = None
                    self._connection = None
                    time.sleep(5)
                    self.connect()
            except Exception as e:
                if self._is_running:
                    logger.error(
                        f"消费异常: {str(e)}",
                        extra={"worker_name": self._config.worker_name, "error": str(e)}
                    )
                    time.sleep(5)

    def stop_consuming(self) -> None:
        """停止消费消息"""
        self._is_running = False

        if self._channel and self._channel.is_open:
            try:
                self._channel.stop_consuming()
            except Exception as e:
                logger.warning(f"停止消费时出错: {str(e)}")

        self.disconnect()

        logger.info(
            f"消费者已停止",
            extra={
                "worker_name": self._config.worker_name,
                "stats": self._stats
            }
        )

    def _signal_handler(self, signum, frame) -> None:
        """信号处理"""
        logger.info(
            f"收到信号，准备停止",
            extra={
                "worker_name": self._config.worker_name,
                "signal": signum
            }
        )
        self.stop_consuming()

    def get_stats(self) -> Dict[str, Any]:
        """
        获取消费者统计信息

        Returns:
            统计信息字典
        """
        return {
            "worker_name": self._config.worker_name,
            "queue_name": self._config.queue_name,
            "is_running": self._is_running,
            "stats": self._stats.copy()
        }


class QueuePublisher:
    """
    队列消息发布器

    提供便捷的消息发布方法。
    """

    def __init__(self):
        """初始化发布器"""
        self._client: Optional[RabbitMQClientWrapper] = None

    @property
    def client(self) -> "RabbitMQClientWrapper":
        """获取客户端"""
        if self._client is None:
            self._client = RabbitMQClientWrapper()
            self._client.connect()
        return self._client

    def publish_parse_task(self, task_data: Dict[str, Any]) -> bool:
        """
        发布解析任务

        Args:
            task_data: 任务数据

        Returns:
            是否发布成功
        """
        return self.client.publish(
            routing_key=RoutingKey.PARSE_START.value,
            message=task_data
        )

    def publish_clean_task(self, task_data: Dict[str, Any]) -> bool:
        """
        发布清洗任务

        Args:
            task_data: 任务数据

        Returns:
            是否发布成功
        """
        return self.client.publish(
            routing_key=RoutingKey.CLEAN_START.value,
            message=task_data
        )

    def publish_chunk_task(self, task_data: Dict[str, Any]) -> bool:
        """
        发布切分任务

        Args:
            task_data: 任务数据

        Returns:
            是否发布成功
        """
        return self.client.publish(
            routing_key=RoutingKey.CHUNK_START.value,
            message=task_data
        )

    def publish_embedding_task(self, task_data: Dict[str, Any]) -> bool:
        """
        发布向量化任务

        Args:
            task_data: 任务数据

        Returns:
            是否发布成功
        """
        return self.client.publish(
            routing_key=RoutingKey.EMBEDDING_START.value,
            message=task_data
        )

    def publish_index_task(self, task_data: Dict[str, Any]) -> bool:
        """
        发布索引任务

        Args:
            task_data: 任务数据

        Returns:
            是否发布成功
        """
        return self.client.publish(
            routing_key=RoutingKey.INDEX_START.value,
            message=task_data
        )

    def close(self) -> None:
        """关闭发布器"""
        if self._client:
            self._client.disconnect()
            self._client = None


class RabbitMQClientWrapper:
    """
    RabbitMQ客户端封装

    提供消息队列的操作方法。
    """

    def __init__(self):
        """初始化客户端"""
        self._connection: Optional[pika.BlockingConnection] = None
        self._channel: Optional[BlockingChannel] = None
        self._exchange_name = settings.rabbitmq.exchange.name
        self._dlx_exchange = "rag_dlx_exchange"

    def _ensure_connection(self) -> None:
        """确保连接有效"""
        if not self._connection or not self._connection.is_open:
            self.connect()
        if not self._channel or not self._channel.is_open:
            self._channel = self._connection.channel()

    def connect(self) -> None:
        """连接到RabbitMQ服务器"""
        if self._connection and self._connection.is_open:
            return

        credentials = pika.PlainCredentials(
            username=settings.rabbitmq.username,
            password=settings.rabbitmq.password
        )

        parameters = pika.ConnectionParameters(
            host=settings.rabbitmq.host,
            port=settings.rabbitmq.port,
            virtual_host=settings.rabbitmq.virtual_host,
            credentials=credentials,
            heartbeat=settings.rabbitmq.heartbeat,
            connection_attempts=3,
            retry_delay=5
        )

        self._connection = pika.BlockingConnection(parameters)
        self._channel = self._connection.channel()

        # 声明交换机
        self._channel.exchange_declare(
            exchange=self._exchange_name,
            exchange_type=settings.rabbitmq.exchange.type,
            durable=settings.rabbitmq.exchange.durable
        )

        # 声明所有队列
        self._setup_queues()

        logger.info("RabbitMQ发布者客户端连接成功")

    def _setup_queues(self) -> None:
        """设置队列"""
        for queue_key, queue_config in settings.rabbitmq.queues.items():
            queue_name = queue_config.name
            
            # 直接声明队列
            try:
                self._channel.queue_declare(
                    queue=queue_name,
                    durable=True,
                    arguments={
                        "x-dead-letter-exchange": "rag_dlx_exchange",
                        "x-dead-letter-routing-key": "dlx"
                    }
                )
                logger.info(
                    f"队列 {queue_name} 声明成功",
                    extra={"queue_name": queue_name}
                )
            except pika.exceptions.ChannelClosedByBroker as e:
                error_str = str(e)
                if "PRECONDITION_FAILED" in error_str or "inequivalent" in error_str:
                    logger.info(
                        f"队列 {queue_name} 已存在但参数不同，保持现有配置",
                        extra={"queue_name": queue_name}
                    )
                else:
                    raise
            except Exception as e:
                logger.warning(
                    f"声明队列 {queue_name} 失败: {str(e)}",
                    extra={"queue_name": queue_name}
                )

            # 绑定队列到交换机
            try:
                self._channel.queue_bind(
                    queue=queue_name,
                    exchange=self._exchange_name,
                    routing_key=queue_config.routing_key
                )
            except pika.exceptions.ChannelClosedByBroker as e:
                error_str = str(e)
                if "inequivalent" in error_str or "PRECONDITION_FAILED" in error_str:
                    logger.info(
                        f"队列 {queue_name} 已绑定，跳过",
                        extra={"queue_name": queue_name}
                    )
                else:
                    logger.warning(
                        f"绑定队列 {queue_name} 失败: {error_str}",
                        extra={"queue_name": queue_name}
                    )
            except Exception as e:
                logger.warning(
                    f"绑定队列 {queue_name} 失败: {str(e)}",
                    extra={"queue_name": queue_name}
                )

        # 声明死信队列
        try:
            self._channel.queue_declare(
                queue=QueueName.DLX_QUEUE.value,
                durable=True
            )
        except pika.exceptions.ChannelClosedByBroker:
            pass  # 已存在
        except Exception:
            self._channel.queue_declare(
                queue=QueueName.DLX_QUEUE.value,
                durable=True
            )
        
        try:
            self._channel.exchange_declare(
                exchange=self._dlx_exchange,
                exchange_type="direct",
                durable=True
            )
            self._channel.queue_bind(
                queue=QueueName.DLX_QUEUE.value,
                exchange=self._dlx_exchange,
                routing_key="dlx"
            )
        except Exception as e:
            logger.info(f"死信交换机/队列已存在或绑定冲突: {str(e)}")

    def disconnect(self) -> None:
        """断开连接"""
        if self._connection and self._connection.is_open:
            self._connection.close()
            logger.info("RabbitMQ发布者客户端连接已关闭")

    def get_queue_stats(self, queue_name: str) -> Dict[str, Any]:
        """
        获取指定队列的统计信息

        Args:
            queue_name: 队列名称

        Returns:
            队列统计信息
        """
        try:
            self._ensure_connection()

            # 声明队列以确保存在（被动查询）
            result = self._channel.queue_declare(
                queue=queue_name,
                passive=True  # 只查询，不创建
            )

            message_count = result.method.message_count
            consumer_count = result.method.consumer_count

            logger.debug(
                f"获取队列统计成功",
                extra={
                    "queue_name": queue_name,
                    "message_count": message_count,
                    "consumer_count": consumer_count
                }
            )

            return {
                "queue_name": queue_name,
                "message_count": message_count,
                "consumer_count": consumer_count
            }

        except pika.exceptions.ChannelClosedByBroker as e:
            logger.warning(
                f"队列不存在或无法访问",
                extra={"queue_name": queue_name, "error": str(e)}
            )
            return {
                "queue_name": queue_name,
                "message_count": 0,
                "consumer_count": 0,
                "error": f"队列不存在: {queue_name}"
            }
        except Exception as e:
            logger.error(
                f"获取队列统计失败",
                extra={"queue_name": queue_name, "error": str(e)}
            )
            raise

    def get_dlx_messages(
        self,
        limit: int = 10,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        获取死信队列中的消息

        Args:
            limit: 返回数量限制
            offset: 偏移量

        Returns:
            死信消息列表和总数
        """
        try:
            self._ensure_connection()

            dlx_queue = QueueName.DLX_QUEUE.value
            messages = []
            total = 0

            # 先获取队列信息
            queue_result = self._channel.queue_declare(
                queue=dlx_queue,
                passive=True
            )
            total = queue_result.method.message_count

            if total == 0:
                return {
                    "messages": [],
                    "total": 0
                }

            # 使用 basic_get 逐条获取消息（支持偏移）
            count = 0
            skip_count = offset

            while count < limit:
                method, properties, body = self._channel.basic_get(
                    queue=dlx_queue,
                    auto_ack=False
                )

                if method is None:
                    # 没有更多消息
                    break

                if skip_count > 0:
                    # 跳过前面的消息
                    self._channel.basic_nack(
                        delivery_tag=method.delivery_tag,
                        requeue=True
                    )
                    skip_count -= 1
                    continue

                try:
                    message_data = json.loads(body.decode("utf-8"))

                    # 尝试解析原始消息
                    original_msg = message_data.get("original_message", {})
                    task_info = original_msg.get("task_id", "unknown")

                    message_info = {
                        "message_id": f"{method.delivery_tag}_{method.message_count}",
                        "task_id": original_msg.get("task_id", "unknown"),
                        "task_type": original_msg.get("task_type", "unknown"),
                        "document_id": original_msg.get("document_id"),
                        "error_type": message_data.get("error_type", "unknown"),
                        "error_message": message_data.get("error_message", ""),
                        "original_queue": message_data.get("original_queue", "unknown"),
                        "retry_count": message_data.get("retry_count", 0),
                        "failed_at": message_data.get("failed_at", ""),
                        "content": json.dumps(original_msg, ensure_ascii=False, default=str)
                    }
                    messages.append(message_info)

                except (json.JSONDecodeError, KeyError) as parse_err:
                    # 无法解析的消息
                    messages.append({
                        "message_id": f"{method.delivery_tag}_{method.message_count}",
                        "task_id": "unknown",
                        "task_type": "unknown",
                        "document_id": None,
                        "error_type": "PARSE_ERROR",
                        "error_message": f"消息解析失败: {str(parse_err)}",
                        "original_queue": "unknown",
                        "retry_count": 0,
                        "failed_at": "",
                        "content": body.decode("utf-8", errors="replace")
                    })

                # 确认消息并重新入队（消息已被消费但需要保留）
                self._channel.basic_ack(delivery_tag=method.delivery_tag)
                self._channel.basic_publish(
                    exchange=self._dlx_exchange,
                    routing_key="dlx",
                    body=body,
                    properties=pika.BasicProperties(delivery_mode=2)
                )

                count += 1

            logger.debug(
                f"获取死信消息成功",
                extra={
                    "total": total,
                    "returned": len(messages),
                    "offset": offset,
                    "limit": limit
                }
            )

            return {
                "messages": messages,
                "total": total
            }

        except Exception as e:
            logger.error(
                f"获取死信消息失败",
                extra={"error": str(e)}
            )
            raise

    def delete_dlx_message(self, message_id: str) -> Dict[str, Any]:
        """
        删除指定的死信消息

        Args:
            message_id: 消息ID（格式: deliveryTag_messageCount）

        Returns:
            删除结果
        """
        try:
            self._ensure_connection()

            dlx_queue = QueueName.DLX_QUEUE.value

            # 解析 message_id
            try:
                delivery_tag = int(message_id.split("_")[0])
            except (ValueError, IndexError):
                return {
                    "message_id": message_id,
                    "deleted": False,
                    "error": "无效的消息ID格式"
                }

            # 获取消息并确认删除
            found = False
            checked_count = 0

            while checked_count < 100:  # 最多检查100条
                method, properties, body = self._channel.basic_get(
                    queue=dlx_queue,
                    auto_ack=False
                )

                if method is None:
                    break

                if method.delivery_tag == delivery_tag:
                    # 找到目标消息，确认删除（不重新入队）
                    self._channel.basic_ack(delivery_tag=method.delivery_tag)
                    found = True
                    logger.info(
                        f"死信消息已删除",
                        extra={"message_id": message_id}
                    )
                    break
                else:
                    # 不是目标消息，重新入队
                    self._channel.basic_ack(delivery_tag=method.delivery_tag)
                    self._channel.basic_publish(
                        exchange=self._dlx_exchange,
                        routing_key="dlx",
                        body=body,
                        properties=pika.BasicProperties(delivery_mode=2)
                    )

                checked_count += 1

            if found:
                return {
                    "message_id": message_id,
                    "deleted": True
                }
            else:
                return {
                    "message_id": message_id,
                    "deleted": False,
                    "error": "消息未找到或已被删除"
                }

        except Exception as e:
            logger.error(
                f"删除死信消息失败",
                extra={"message_id": message_id, "error": str(e)}
            )
            raise

    def clear_dlx_messages(self) -> Dict[str, Any]:
        """
        清空死信队列中的所有消息

        Returns:
            清空结果
        """
        try:
            self._ensure_connection()

            dlx_queue = QueueName.DLX_QUEUE.value

            # 获取当前队列消息数量
            queue_result = self._channel.queue_declare(
                queue=dlx_queue,
                passive=True
            )
            message_count = queue_result.method.message_count

            deleted_count = 0

            # 逐条消费并确认删除
            while True:
                method, properties, body = self._channel.basic_get(
                    queue=dlx_queue,
                    auto_ack=False
                )

                if method is None:
                    break

                self._channel.basic_ack(delivery_tag=method.delivery_tag)
                deleted_count += 1

            logger.info(
                f"死信队列已清空",
                extra={"deleted_count": deleted_count}
            )

            return {
                "cleared": True,
                "deleted_count": deleted_count
            }

        except Exception as e:
            logger.error(
                f"清空死信队列失败",
                extra={"error": str(e)}
            )
            raise

    def publish(
        self,
        routing_key: str,
        message: Dict[str, Any],
        properties: Optional[pika.BasicProperties] = None
    ) -> bool:
        """
        发布消息

        Args:
            routing_key: 路由键
            message: 消息内容
            properties: 消息属性

        Returns:
            是否发布成功
        """
        try:
            if not self._channel or not self._channel.is_open:
                self.connect()

            if properties is None:
                properties = pika.BasicProperties(
                    delivery_mode=2,
                    content_type="application/json"
                )

            self._channel.basic_publish(
                exchange=self._exchange_name,
                routing_key=routing_key,
                body=json.dumps(message, ensure_ascii=False),
                properties=properties
            )

            logger.debug(
                f"消息已发布",
                extra={"routing_key": routing_key, "task_id": message.get("task_id")}
            )
            return True

        except Exception as e:
            logger.error(
                f"消息发布失败: {str(e)}",
                extra={"routing_key": routing_key, "error": str(e)}
            )
            return False


# 全局发布器实例
_queue_publisher: Optional[QueuePublisher] = None


def get_queue_publisher() -> QueuePublisher:
    """
    获取队列发布器实例

    Returns:
        QueuePublisher实例
    """
    global _queue_publisher
    if _queue_publisher is None:
        _queue_publisher = QueuePublisher()
    return _queue_publisher


def close_queue_publisher() -> None:
    """关闭队列发布器"""
    global _queue_publisher
    if _queue_publisher is not None:
        _queue_publisher.close()
        _queue_publisher = None
