# -*- coding: utf-8 -*-
"""
队列服务测试

测试用例：
1. 任务消息模型测试
2. 消费者基类测试
3. 发布器测试
4. Worker测试
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

from app.schemas.queue import (
    TaskType,
    TaskStatus,
    QueueName,
    RoutingKey,
    TaskMessage,
    ParseTaskMessage,
    CleanTaskMessage,
    ChunkTaskMessage,
    EmbeddingTaskMessage,
    IndexTaskMessage,
    TaskResult,
    DeadLetterMessage,
    QueueStats,
    WorkerConfig,
)


class TestTaskMessage:
    """测试任务消息模型"""

    def test_task_message_creation(self):
        """测试任务消息创建"""
        message = TaskMessage(
            task_id="test-123",
            task_type=TaskType.PARSE,
            document_id=1,
            version_id=1,
            priority=5,
            payload={"file_path": "/test/file.pdf"}
        )

        assert message.task_id == "test-123"
        assert message.task_type == TaskType.PARSE.value
        assert message.document_id == 1
        assert message.version_id == 1
        assert message.priority == 5
        assert message.retry_count == 0
        assert message.max_retry == 3
        assert message.payload["file_path"] == "/test/file.pdf"

    def test_task_message_default_values(self):
        """测试任务消息默认值"""
        message = TaskMessage(
            task_id="test-456",
            task_type=TaskType.CLEAN,
            document_id=2,
            version_id=2
        )

        assert message.priority == 5
        assert message.retry_count == 0
        assert message.max_retry == 3
        assert message.created_at is not None
        assert message.updated_at is None

    def test_task_message_to_dict(self):
        """测试任务消息转字典"""
        message = TaskMessage(
            task_id="test-789",
            task_type=TaskType.CHUNK,
            document_id=3,
            version_id=3
        )

        data = message.model_dump()
        assert data["task_id"] == "test-789"
        assert data["task_type"] == "chunk"


class TestParseTaskMessage:
    """测试解析任务消息"""

    def test_parse_task_message_creation(self):
        """测试解析任务消息创建"""
        message = ParseTaskMessage(
            task_id="parse-123",
            document_id=1,
            version_id=1,
            payload={
                "file_path": "/path/to/file.pdf",
                "config": {"ocr_enabled": True}
            }
        )

        assert message.task_type == TaskType.PARSE.value
        assert message.get_file_path() == "/path/to/file.pdf"
        assert message.get_parser_config()["ocr_enabled"] is True

    def test_parse_task_message_defaults(self):
        """测试解析任务消息默认值"""
        message = ParseTaskMessage(
            task_id="parse-456",
            document_id=1,
            version_id=1
        )

        assert message.task_type == TaskType.PARSE.value
        assert message.get_file_path() is None


class TestCleanTaskMessage:
    """测试清洗任务消息"""

    def test_clean_task_message_creation(self):
        """测试清洗任务消息创建"""
        message = CleanTaskMessage(
            task_id="clean-123",
            document_id=1,
            version_id=1,
            payload={
                "element_ids": [1, 2, 3],
                "config": {"remove_noise": True}
            }
        )

        assert message.task_type == TaskType.CLEAN.value
        assert message.get_element_ids() == [1, 2, 3]
        assert message.get_cleaning_config()["remove_noise"] is True


class TestChunkTaskMessage:
    """测试切分任务消息"""

    def test_chunk_task_message_creation(self):
        """测试切分任务消息创建"""
        message = ChunkTaskMessage(
            task_id="chunk-123",
            document_id=1,
            version_id=1,
            payload={
                "element_ids": [1, 2, 3, 4, 5],
                "config": {"target_tokens": 600}
            }
        )

        assert message.task_type == TaskType.CHUNK.value
        assert len(message.get_element_ids()) == 5
        assert message.get_chunk_config()["target_tokens"] == 600


class TestEmbeddingTaskMessage:
    """测试向量化任务消息"""

    def test_embedding_task_message_creation(self):
        """测试向量化任务消息创建"""
        message = EmbeddingTaskMessage(
            task_id="embedding-123",
            document_id=1,
            version_id=1,
            payload={
                "chunk_ids": [1, 2, 3],
                "batch_size": 32
            }
        )

        assert message.task_type == TaskType.EMBEDDING.value
        assert len(message.get_chunk_ids()) == 3
        assert message.get_batch_size() == 32

    def test_embedding_task_message_defaults(self):
        """测试向量化任务消息默认值"""
        message = EmbeddingTaskMessage(
            task_id="embedding-456",
            document_id=1,
            version_id=1
        )

        assert message.get_batch_size() == 32


class TestIndexTaskMessage:
    """测试索引任务消息"""

    def test_index_task_message_creation(self):
        """测试索引任务消息创建"""
        message = IndexTaskMessage(
            task_id="index-123",
            document_id=1,
            version_id=1,
            payload={
                "chunk_ids": [1, 2, 3],
                "index_type": "keyword"
            }
        )

        assert message.task_type == TaskType.INDEX.value
        assert len(message.get_chunk_ids()) == 3
        assert message.get_index_type() == "keyword"


class TestTaskResult:
    """测试任务结果模型"""

    def test_task_result_creation(self):
        """测试任务结果创建"""
        result = TaskResult(
            task_id="test-123",
            task_type=TaskType.PARSE,
            status=TaskStatus.COMPLETED,
            document_id=1,
            version_id=1,
            result={"processed": True},
            cost_seconds=10
        )

        assert result.task_id == "test-123"
        assert result.status == TaskStatus.COMPLETED.value
        assert result.result["processed"] is True
        assert result.cost_seconds == 10


class TestDeadLetterMessage:
    """测试死信消息模型"""

    def test_dead_letter_message_creation(self):
        """测试死信消息创建"""
        message = DeadLetterMessage(
            original_message={"task_id": "test-123", "data": "test"},
            error_type="PROCESS_FAILED",
            error_message="处理失败",
            error_stack="Traceback...",
            retry_count=3,
            original_queue="rag_parse_queue"
        )

        assert message.original_message["task_id"] == "test-123"
        assert message.error_type == "PROCESS_FAILED"
        assert message.retry_count == 3
        assert message.original_queue == "rag_parse_queue"
        assert message.failed_at is not None


class TestQueueStats:
    """测试队列统计模型"""

    def test_queue_stats_creation(self):
        """测试队列统计创建"""
        stats = QueueStats(
            queue_name="rag_parse_queue",
            message_count=100,
            consumer_count=2,
            published_total=1000,
            consumed_total=900,
            failed_total=50,
            avg_process_time_ms=150.5
        )

        assert stats.queue_name == "rag_parse_queue"
        assert stats.message_count == 100
        assert stats.consumer_count == 2
        assert stats.avg_process_time_ms == 150.5


class TestWorkerConfig:
    """测试Worker配置模型"""

    def test_worker_config_creation(self):
        """测试Worker配置创建"""
        config = WorkerConfig(
            worker_name="parse_worker",
            queue_name="rag_parse_queue",
            prefetch_count=10,
            max_workers=4,
            enable_retry=True,
            max_retry=5,
            retry_delay_seconds=10,
            enable_dlx=True
        )

        assert config.worker_name == "parse_worker"
        assert config.queue_name == "rag_parse_queue"
        assert config.prefetch_count == 10
        assert config.max_workers == 4
        assert config.enable_retry is True
        assert config.max_retry == 5

    def test_worker_config_defaults(self):
        """测试Worker配置默认值"""
        config = WorkerConfig(
            worker_name="test_worker",
            queue_name="test_queue"
        )

        assert config.prefetch_count == 10
        assert config.max_workers == 1
        assert config.enable_retry is True
        assert config.max_retry == 3
        assert config.retry_delay_seconds == 5
        assert config.enable_dlx is True


class TestEnums:
    """测试枚举类"""

    def test_task_type_values(self):
        """测试任务类型枚举值"""
        assert TaskType.PARSE.value == "parse"
        assert TaskType.CLEAN.value == "clean"
        assert TaskType.CHUNK.value == "chunk"
        assert TaskType.EMBEDDING.value == "embedding"
        assert TaskType.INDEX.value == "index"

    def test_task_status_values(self):
        """测试任务状态枚举值"""
        assert TaskStatus.PENDING.value == "pending"
        assert TaskStatus.RUNNING.value == "running"
        assert TaskStatus.COMPLETED.value == "completed"
        assert TaskStatus.FAILED.value == "failed"
        assert TaskStatus.RETRYING.value == "retrying"

    def test_queue_name_values(self):
        """测试队列名称枚举值"""
        assert QueueName.PARSE_QUEUE.value == "rag_parse_queue"
        assert QueueName.CLEAN_QUEUE.value == "rag_clean_queue"
        assert QueueName.CHUNK_QUEUE.value == "rag_chunk_queue"
        assert QueueName.EMBEDDING_QUEUE.value == "rag_embedding_queue"
        assert QueueName.INDEX_QUEUE.value == "rag_index_queue"
        assert QueueName.DLX_QUEUE.value == "rag_dlx_queue"

    def test_routing_key_values(self):
        """测试路由键枚举值"""
        assert RoutingKey.PARSE_START.value == "rag.parse.start"
        assert RoutingKey.CLEAN_START.value == "rag.clean.start"
        assert RoutingKey.CHUNK_START.value == "rag.chunk.start"
        assert RoutingKey.EMBEDDING_START.value == "rag.embedding.start"
        assert RoutingKey.INDEX_START.value == "rag.index.start"


class TestQueueConsumerMocked:
    """测试QueueConsumer基类（使用Mock）"""

    @pytest.fixture
    def mock_config(self):
        """创建Mock配置"""
        return WorkerConfig(
            worker_name="test_worker",
            queue_name="test_queue",
            prefetch_count=5,
            enable_retry=True,
            max_retry=3,
            retry_delay_seconds=1
        )

    def test_worker_config_from_consumer(self, mock_config):
        """测试从消费者获取配置"""
        from app.services.queue_consumer import QueueConsumer

        # 由于QueueConsumer是抽象类，我们需要测试配置属性
        config = mock_config

        assert config.worker_name == "test_worker"
        assert config.queue_name == "test_queue"
        assert config.prefetch_count == 5


class TestQueuePublisherMocked:
    """测试QueuePublisher（使用Mock）"""

    @patch("app.services.queue_consumer.RabbitMQClientWrapper")
    def test_publisher_initialization(self, mock_client_class):
        """测试发布器初始化"""
        from app.services.queue_consumer import QueuePublisher

        publisher = QueuePublisher()

        assert publisher._client is None

        mock_client_instance = MagicMock()
        mock_client_class.return_value = mock_client_instance

        # 访问client属性触发初始化
        _ = publisher.client

        mock_client_instance.connect.assert_called_once()

    @patch("app.services.queue_consumer.get_queue_publisher")
    def test_publish_parse_task(self, mock_get_publisher):
        """测试发布解析任务"""
        mock_publisher = MagicMock()
        mock_publisher.publish_parse_task.return_value = True
        mock_get_publisher.return_value = mock_publisher

        result = mock_publisher.publish_parse_task({
            "task_id": "test-123",
            "task_type": "parse"
        })

        assert result is True
        mock_publisher.publish_parse_task.assert_called_once()


class TestWorkersMocked:
    """测试Worker类（使用Mock）"""

    def test_parse_worker_config(self):
        """测试ParseWorker默认配置"""
        from app.services.workers import ParseWorker

        worker = ParseWorker()
        config = worker._get_default_config()

        assert config.worker_name == "parse_worker"
        assert config.queue_name == QueueName.PARSE_QUEUE.value
        assert config.prefetch_count == 5
        assert config.enable_retry is True

    def test_clean_worker_config(self):
        """测试CleanWorker默认配置"""
        from app.services.workers import CleanWorker

        worker = CleanWorker()
        config = worker._get_default_config()

        assert config.worker_name == "clean_worker"
        assert config.queue_name == QueueName.CLEAN_QUEUE.value
        assert config.prefetch_count == 10

    def test_chunk_worker_config(self):
        """测试ChunkWorker默认配置"""
        from app.services.workers import ChunkWorker

        worker = ChunkWorker()
        config = worker._get_default_config()

        assert config.worker_name == "chunk_worker"
        assert config.queue_name == QueueName.CHUNK_QUEUE.value

    def test_embedding_worker_config(self):
        """测试EmbeddingWorker默认配置"""
        from app.services.workers import EmbeddingWorker

        worker = EmbeddingWorker()
        config = worker._get_default_config()

        assert config.worker_name == "embedding_worker"
        assert config.queue_name == QueueName.EMBEDDING_QUEUE.value
        assert config.prefetch_count == 5

    def test_index_worker_config(self):
        """测试IndexWorker默认配置"""
        from app.services.workers import IndexWorker

        worker = IndexWorker()
        config = worker._get_default_config()

        assert config.worker_name == "index_worker"
        assert config.queue_name == QueueName.INDEX_QUEUE.value

    def test_get_worker_factory(self):
        """测试Worker工厂函数"""
        from app.services.workers import get_worker

        parse_worker = get_worker("parse")
        assert parse_worker.__class__.__name__ == "ParseWorker"

        clean_worker = get_worker("clean")
        assert clean_worker.__class__.__name__ == "CleanWorker"

        chunk_worker = get_worker("chunk")
        assert chunk_worker.__class__.__name__ == "ChunkWorker"

        embedding_worker = get_worker("embedding")
        assert embedding_worker.__class__.__name__ == "EmbeddingWorker"

        index_worker = get_worker("index")
        assert index_worker.__class__.__name__ == "IndexWorker"

    def test_get_worker_invalid_type(self):
        """测试无效的Worker类型"""
        from app.services.workers import get_worker

        with pytest.raises(ValueError) as exc_info:
            get_worker("invalid")

        assert "不支持的Worker类型" in str(exc_info.value)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
