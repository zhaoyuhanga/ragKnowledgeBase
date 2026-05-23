# -*- coding: utf-8 -*-
"""
Worker模块

本模块包含所有消息队列的Worker实现：
1. ParseWorker - 解析任务消费者
2. CleanWorker - 清洗任务消费者
3. ChunkWorker - 切分任务消费者
4. EmbeddingWorker - 向量化任务消费者
5. IndexWorker - 索引任务消费者
"""

from typing import Any, Dict, Optional

from app.schemas.queue import (
    QueueName,
    RoutingKey,
    TaskMessage,
    WorkerConfig,
)
from app.services.embedding_service import get_embedding_service, get_chunk_embedding_service, ChunkEmbeddingService
from app.services.parse_service import get_parse_service, ParseService
from app.services.clean_service import get_clean_service, CleanService
from app.services.chunk_service import get_chunk_service, ChunkService
from app.services.keyword_service import get_keyword_index_service, KeywordIndexService
from app.common.logging import logger
from app.services.queue_consumer import QueueConsumer


class ParseWorker(QueueConsumer):
    """
    解析任务Worker

    负责消费解析队列中的任务，执行文档解析操作。
    """

    def __init__(self, config: Optional[WorkerConfig] = None):
        """初始化解析Worker"""
        super().__init__(config)
        self._parse_service: Optional[ParseService] = None

    def _get_default_config(self) -> WorkerConfig:
        """获取默认配置"""
        return WorkerConfig(
            worker_name="parse_worker",
            queue_name=QueueName.PARSE_QUEUE.value,
            prefetch_count=5,
            max_workers=2,
            enable_retry=True,
            max_retry=3,
            retry_delay_seconds=10,
            enable_dlx=True
        )

    def get_routing_key(self) -> str:
        """获取监听的路由键"""
        return RoutingKey.PARSE_START.value

    @property
    def parse_service(self) -> ParseService:
        """获取解析服务"""
        if self._parse_service is None:
            self._parse_service = get_parse_service()
        return self._parse_service

    def process_message(self, message: Dict[str, Any]) -> bool:
        """
        处理解析任务消息

        Args:
            message: 消息内容

        Returns:
            是否处理成功
        """
        try:
            task_id = message.get("task_id")
            document_id = message.get("document_id")
            version_id = message.get("version_id")
            payload = message.get("payload", {})

            logger.info(
                f"开始处理解析任务",
                extra={
                    "task_id": task_id,
                    "document_id": document_id,
                    "version_id": version_id
                }
            )

            # 调用解析服务
            result = self.parse_service.parse_document(
                document_id=document_id,
                version_id=version_id
            )

            # 发布清洗任务
            self._publish_clean_task(message, result)

            logger.info(
                f"解析任务处理完成",
                extra={
                    "task_id": task_id,
                    "document_id": document_id,
                    "result": result
                }
            )

            return True

        except Exception as e:
            logger.error(
                f"解析任务处理失败: {str(e)}",
                extra={
                    "task_id": message.get("task_id"),
                    "error": str(e)
                }
            )
            return False

    def _publish_clean_task(
        self,
        original_message: Dict[str, Any],
        parse_result: Dict[str, Any]
    ) -> None:
        """
        发布清洗任务

        Args:
            original_message: 原始消息
            parse_result: 解析结果
        """
        from app.services.queue_consumer import get_queue_publisher

        publisher = get_queue_publisher()

        clean_task = {
            "task_id": f"{original_message.get('task_id')}_clean",
            "task_type": "clean",
            "document_id": original_message.get("document_id"),
            "version_id": original_message.get("version_id"),
            "priority": original_message.get("priority", 5),
            "retry_count": 0,
            "max_retry": 3,
            "payload": {
                "parse_result": parse_result,
                "element_ids": parse_result.get("element_ids", [])
            }
        }

        success = publisher.publish_clean_task(clean_task)

        if success:
            logger.info(
                f"清洗任务已发布",
                extra={
                    "original_task_id": original_message.get("task_id"),
                    "new_task_id": clean_task["task_id"]
                }
            )
        else:
            logger.warning(
                f"清洗任务发布失败",
                extra={"task_id": clean_task["task_id"]}
            )


class CleanWorker(QueueConsumer):
    """
    清洗任务Worker

    负责消费清洗队列中的任务，执行文档清洗操作。
    """

    def __init__(self, config: Optional[WorkerConfig] = None):
        """初始化清洗Worker"""
        super().__init__(config)
        self._clean_service: Optional[CleanService] = None

    def _get_default_config(self) -> WorkerConfig:
        """获取默认配置"""
        return WorkerConfig(
            worker_name="clean_worker",
            queue_name=QueueName.CLEAN_QUEUE.value,
            prefetch_count=10,
            max_workers=2,
            enable_retry=True,
            max_retry=3,
            retry_delay_seconds=5,
            enable_dlx=True
        )

    def get_routing_key(self) -> str:
        """获取监听的路由键"""
        return RoutingKey.CLEAN_START.value

    @property
    def clean_service(self) -> CleanService:
        """获取清洗服务"""
        if self._clean_service is None:
            self._clean_service = get_clean_service()
        return self._clean_service

    def process_message(self, message: Dict[str, Any]) -> bool:
        """
        处理清洗任务消息

        Args:
            message: 消息内容

        Returns:
            是否处理成功
        """
        try:
            task_id = message.get("task_id")
            document_id = message.get("document_id")
            version_id = message.get("version_id")
            payload = message.get("payload", {})

            logger.info(
                f"开始处理清洗任务",
                extra={
                    "task_id": task_id,
                    "document_id": document_id,
                    "version_id": version_id
                }
            )

            # 获取待清洗的元素
            from app.models.parse import DocumentElement
            from core.database import SessionLocal
            db = SessionLocal()
            try:
                elements = db.query(DocumentElement).filter(
                    DocumentElement.version_id == version_id
                ).order_by(DocumentElement.reading_order).all()
            finally:
                db.close()

            # 调用清洗服务
            result = self.clean_service.clean_document(
                document_id=document_id,
                version_id=version_id,
                elements=elements
            )

            # 发布切分任务
            self._publish_chunk_task(message, result)

            logger.info(
                f"清洗任务处理完成",
                extra={
                    "task_id": task_id,
                    "document_id": document_id,
                    "cleaned_count": result.success_count
                }
            )

            return True

        except Exception as e:
            logger.error(
                f"清洗任务处理失败: {str(e)}",
                extra={
                    "task_id": message.get("task_id"),
                    "error": str(e)
                }
            )
            return False

    def _publish_chunk_task(
        self,
        original_message: Dict[str, Any],
        clean_result: "CleaningResult"
    ) -> None:
        """
        发布切分任务

        Args:
            original_message: 原始消息
            clean_result: 清洗结果 (CleaningResult Pydantic 模型)
        """
        from app.services.queue_consumer import get_queue_publisher

        publisher = get_queue_publisher()

        # 从 CleaningResult 中提取元素ID列表
        cleaned_element_ids = [elem.element_id for elem in clean_result.elements] if clean_result.elements else []

        chunk_task = {
            "task_id": f"{original_message.get('task_id')}_chunk",
            "task_type": "chunk",
            "document_id": original_message.get("document_id"),
            "version_id": original_message.get("version_id"),
            "priority": original_message.get("priority", 5),
            "retry_count": 0,
            "max_retry": 3,
            "payload": {
                "clean_result": clean_result.model_dump(),
                "cleaned_element_ids": cleaned_element_ids
            }
        }

        success = publisher.publish_chunk_task(chunk_task)

        if success:
            logger.info(
                f"切分任务已发布",
                extra={
                    "original_task_id": original_message.get("task_id"),
                    "new_task_id": chunk_task["task_id"]
                }
            )
        else:
            logger.warning(
                f"切分任务发布失败",
                extra={"task_id": chunk_task["task_id"]}
            )


class ChunkWorker(QueueConsumer):
    """
    切分任务Worker

    负责消费切分队列中的任务，执行文档切分操作。
    """

    def __init__(self, config: Optional[WorkerConfig] = None):
        """初始化切分Worker"""
        super().__init__(config)
        self._chunk_service: Optional[ChunkService] = None

    def _get_default_config(self) -> WorkerConfig:
        """获取默认配置"""
        return WorkerConfig(
            worker_name="chunk_worker",
            queue_name=QueueName.CHUNK_QUEUE.value,
            prefetch_count=10,
            max_workers=2,
            enable_retry=True,
            max_retry=3,
            retry_delay_seconds=5,
            enable_dlx=True
        )

    def get_routing_key(self) -> str:
        """获取监听的路由键"""
        return RoutingKey.CHUNK_START.value

    @property
    def chunk_service(self) -> ChunkService:
        """获取切分服务"""
        if self._chunk_service is None:
            self._chunk_service = get_chunk_service()
        return self._chunk_service

    def process_message(self, message: Dict[str, Any]) -> bool:
        """
        处理切分任务消息

        Args:
            message: 消息内容

        Returns:
            是否处理成功
        """
        try:
            task_id = message.get("task_id")
            document_id = message.get("document_id")
            version_id = message.get("version_id")
            payload = message.get("payload", {})

            logger.info(
                f"开始处理切分任务",
                extra={
                    "task_id": task_id,
                    "document_id": document_id,
                    "version_id": version_id
                }
            )

            # 获取待切分的元素
            from app.models.parse import DocumentElement
            from core.database import SessionLocal as ChunkSessionLocal
            db_chunk = ChunkSessionLocal()
            try:
                elements = db_chunk.query(DocumentElement).filter(
                    DocumentElement.version_id == version_id
                ).order_by(DocumentElement.reading_order).all()
            finally:
                db_chunk.close()

            if not elements:
                logger.warning(f"文档没有可切分的元素", extra={"document_id": document_id, "version_id": version_id})
                return True

            # 调用切分服务
            result = self.chunk_service.chunk_document(
                document_id=document_id,
                version_id=version_id,
                elements=elements
            )

            # 保存Chunks到数据库
            saved_ids = self.chunk_service.save_chunks(
                document_id=document_id,
                version_id=version_id,
                chunks=result.chunks
            )

            # 同时发布向量化任务和关键词索引任务
            self._publish_embedding_task(message, {"chunk_ids": saved_ids})
            self._publish_index_task(message, {"chunk_ids": saved_ids})

            logger.info(
                f"切分任务处理完成",
                extra={
                    "task_id": task_id,
                    "document_id": document_id,
                    "chunk_count": result.total_chunks
                }
            )

            return True

        except Exception as e:
            logger.error(
                f"切分任务处理失败: {str(e)}",
                extra={
                    "task_id": message.get("task_id"),
                    "error": str(e)
                }
            )
            return False

    def _publish_embedding_task(
        self,
        original_message: Dict[str, Any],
        chunk_result: Dict[str, Any]
    ) -> None:
        """
        发布向量化任务

        Args:
            original_message: 原始消息
            chunk_result: 切分结果
        """
        from app.services.queue_consumer import get_queue_publisher

        publisher = get_queue_publisher()

        embedding_task = {
            "task_id": f"{original_message.get('task_id')}_embedding",
            "task_type": "embedding",
            "document_id": original_message.get("document_id"),
            "version_id": original_message.get("version_id"),
            "priority": original_message.get("priority", 5),
            "retry_count": 0,
            "max_retry": 3,
            "payload": {
                "chunk_result": chunk_result,
                "chunk_ids": chunk_result.get("chunk_ids", [])
            }
        }

        success = publisher.publish_embedding_task(embedding_task)

        if success:
            logger.info(
                f"向量化任务已发布",
                extra={
                    "original_task_id": original_message.get("task_id"),
                    "new_task_id": embedding_task["task_id"]
                }
            )
        else:
            logger.warning(
                f"向量化任务发布失败",
                extra={"task_id": embedding_task["task_id"]}
            )

    def _publish_index_task(
        self,
        original_message: Dict[str, Any],
        chunk_result: Dict[str, Any]
    ) -> None:
        """
        发布索引任务（关键词索引）

        Args:
            original_message: 原始消息
            chunk_result: 切分结果
        """
        from app.services.queue_consumer import get_queue_publisher

        publisher = get_queue_publisher()

        index_task = {
            "task_id": f"{original_message.get('task_id')}_index",
            "task_type": "index",
            "document_id": original_message.get("document_id"),
            "version_id": original_message.get("version_id"),
            "priority": original_message.get("priority", 5),
            "retry_count": 0,
            "max_retry": 3,
            "payload": {
                "chunk_result": chunk_result,
                "chunk_ids": chunk_result.get("chunk_ids", []),
                "index_type": "keyword"
            }
        }

        success = publisher.publish_index_task(index_task)

        if success:
            logger.info(
                f"索引任务已发布",
                extra={
                    "original_task_id": original_message.get("task_id"),
                    "new_task_id": index_task["task_id"]
                }
            )
        else:
            logger.warning(
                f"索引任务发布失败",
                extra={"task_id": index_task["task_id"]}
            )


class EmbeddingWorker(QueueConsumer):
    """
    向量化任务Worker

    负责消费向量化队列中的任务，执行文本向量化操作。
    """

    def __init__(self, config: Optional[WorkerConfig] = None):
        """初始化向量化Worker"""
        super().__init__(config)
        self._embedding_service: Optional[ChunkEmbeddingService] = None

    def _get_default_config(self) -> WorkerConfig:
        """获取默认配置"""
        return WorkerConfig(
            worker_name="embedding_worker",
            queue_name=QueueName.EMBEDDING_QUEUE.value,
            prefetch_count=5,
            max_workers=2,
            enable_retry=True,
            max_retry=3,
            retry_delay_seconds=10,
            enable_dlx=True
        )

    def get_routing_key(self) -> str:
        """获取监听的路由键"""
        return RoutingKey.EMBEDDING_START.value

    @property
    def embedding_service(self) -> ChunkEmbeddingService:
        """获取向量化服务"""
        if self._embedding_service is None:
            self._embedding_service = get_chunk_embedding_service()
        return self._embedding_service

    def process_message(self, message: Dict[str, Any]) -> bool:
        """
        处理向量化任务消息

        Args:
            message: 消息内容

        Returns:
            是否处理成功
        """
        try:
            task_id = message.get("task_id")
            document_id = message.get("document_id")
            version_id = message.get("version_id")
            payload = message.get("payload", {})

            logger.info(
                f"开始处理向量化任务",
                extra={
                    "task_id": task_id,
                    "document_id": document_id,
                    "version_id": version_id,
                    "chunk_count": len(payload.get("chunk_ids", []))
                }
            )

            chunk_ids = payload.get("chunk_ids", [])
            batch_size = payload.get("batch_size", 32)

            # 调用向量化服务
            result = self.embedding_service.embed_document_chunks(
                document_id=document_id,
                version_id=version_id,
                chunk_ids=chunk_ids if chunk_ids else None
            )

            logger.info(
                f"向量化任务处理完成",
                extra={
                    "task_id": task_id,
                    "document_id": document_id,
                    "embedded_count": result.processed_chunks
                }
            )

            return True

        except Exception as e:
            logger.error(
                f"向量化任务处理失败: {str(e)}",
                extra={
                    "task_id": message.get("task_id"),
                    "error": str(e)
                }
            )
            return False


class IndexWorker(QueueConsumer):
    """
    索引任务Worker

    负责消费索引队列中的任务，执行关键词索引构建操作。
    """

    def __init__(self, config: Optional[WorkerConfig] = None):
        """初始化索引Worker"""
        super().__init__(config)
        self._keyword_service: Optional[KeywordIndexService] = None

    def _get_default_config(self) -> WorkerConfig:
        """获取默认配置"""
        return WorkerConfig(
            worker_name="index_worker",
            queue_name=QueueName.INDEX_QUEUE.value,
            prefetch_count=10,
            max_workers=2,
            enable_retry=True,
            max_retry=3,
            retry_delay_seconds=5,
            enable_dlx=True
        )

    def get_routing_key(self) -> str:
        """获取监听的路由键"""
        return RoutingKey.INDEX_START.value

    @property
    def keyword_service(self) -> KeywordIndexService:
        """获取关键词索引服务"""
        if self._keyword_service is None:
            self._keyword_service = get_keyword_index_service()
        return self._keyword_service

    def process_message(self, message: Dict[str, Any]) -> bool:
        """
        处理索引任务消息

        Args:
            message: 消息内容

        Returns:
            是否处理成功
        """
        try:
            task_id = message.get("task_id")
            document_id = message.get("document_id")
            version_id = message.get("version_id")
            payload = message.get("payload", {})

            logger.info(
                f"开始处理索引任务",
                extra={
                    "task_id": task_id,
                    "document_id": document_id,
                    "version_id": version_id,
                    "chunk_count": len(payload.get("chunk_ids", []))
                }
            )

            chunk_ids = payload.get("chunk_ids", [])
            index_type = payload.get("index_type", "keyword")

            if index_type == "keyword":
                # 构建关键词索引
                result = self.keyword_service.build_index(
                    document_id=document_id,
                    chunk_ids=chunk_ids
                )
            else:
                logger.warning(f"不支持的索引类型: {index_type}")
                return True

            logger.info(
                f"索引任务处理完成",
                extra={
                    "task_id": task_id,
                    "document_id": document_id,
                    "indexed_count": result.indexed_chunks
                }
            )

            return True

        except Exception as e:
            logger.error(
                f"索引任务处理失败: {str(e)}",
                extra={
                    "task_id": message.get("task_id"),
                    "error": str(e)
                }
            )
            return False


# Worker工厂函数
def get_worker(worker_type: str) -> QueueConsumer:
    """
    获取指定类型的Worker实例

    Args:
        worker_type: Worker类型 (parse/clean/chunk/embedding/index)

    Returns:
        Worker实例
    """
    worker_map = {
        "parse": ParseWorker,
        "clean": CleanWorker,
        "chunk": ChunkWorker,
        "embedding": EmbeddingWorker,
        "index": IndexWorker
    }

    worker_class = worker_map.get(worker_type)
    if not worker_class:
        raise ValueError(f"不支持的Worker类型: {worker_type}")

    return worker_class()


def run_worker(worker_type: str) -> None:
    """
    运行指定类型的Worker

    Args:
        worker_type: Worker类型
    """
    worker = get_worker(worker_type)
    logger.info(f"启动{worker_type} Worker...")
    worker.start_consuming()
