# -*- coding: utf-8 -*-
"""
队列管理接口

本模块提供队列管理的REST API接口：
1. 任务发布接口
2. 队列状态查询
3. 死信队列管理
"""

import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from app.common.logging import logger
from app.common.response import success_response, error_response
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
    QueueStats,
    DeadLetterMessage,
)
from app.services.queue_consumer import get_queue_publisher, QueuePublisher
from core.config import settings


router = APIRouter(prefix="/queue", tags=["队列管理"])


def get_publisher() -> QueuePublisher:
    """获取队列发布器"""
    return get_queue_publisher()


class PublishTaskRequest(BaseModel):
    """发布任务请求模型"""
    task_type: TaskType = Field(..., description="任务类型")
    document_id: int = Field(..., description="文档ID")
    version_id: int = Field(..., description="版本ID")
    priority: int = Field(default=5, ge=1, le=10, description="优先级")
    max_retry: int = Field(default=3, ge=0, le=10, description="最大重试次数")
    payload: Dict[str, Any] = Field(default_factory=dict, description="任务参数")


class PublishParseTaskRequest(BaseModel):
    """发布解析任务请求"""
    document_id: int = Field(..., description="文档ID")
    version_id: int = Field(..., description="版本ID")
    priority: int = Field(default=5, ge=1, le=10, description="优先级")
    file_path: Optional[str] = Field(default=None, description="文件路径")
    config: Dict[str, Any] = Field(default_factory=dict, description="解析配置")


class PublishCleanTaskRequest(BaseModel):
    """发布清洗任务请求"""
    document_id: int = Field(..., description="文档ID")
    version_id: int = Field(..., description="版本ID")
    priority: int = Field(default=5, ge=1, le=10, description="优先级")
    element_ids: list[int] = Field(default_factory=list, description="元素ID列表")
    config: Dict[str, Any] = Field(default_factory=dict, description="清洗配置")


class PublishChunkTaskRequest(BaseModel):
    """发布切分任务请求"""
    document_id: int = Field(..., description="文档ID")
    version_id: int = Field(..., description="版本ID")
    priority: int = Field(default=5, ge=1, le=10, description="优先级")
    element_ids: list[int] = Field(default_factory=list, description="元素ID列表")
    config: Dict[str, Any] = Field(default_factory=dict, description="切分配置")


class PublishEmbeddingTaskRequest(BaseModel):
    """发布向量化任务请求"""
    document_id: int = Field(..., description="文档ID")
    version_id: int = Field(..., description="版本ID")
    priority: int = Field(default=5, ge=1, le=10, description="优先级")
    chunk_ids: list[int] = Field(default_factory=list, description="Chunk ID列表")
    batch_size: int = Field(default=32, description="批处理大小")


class PublishIndexTaskRequest(BaseModel):
    """发布索引任务请求"""
    document_id: int = Field(..., description="文档ID")
    version_id: int = Field(..., description="版本ID")
    priority: int = Field(default=5, ge=1, le=10, description="优先级")
    chunk_ids: list[int] = Field(default_factory=list, description="Chunk ID列表")
    index_type: str = Field(default="keyword", description="索引类型")


class PublishBatchTaskRequest(BaseModel):
    """批量发布任务请求"""
    task_type: TaskType = Field(..., description="任务类型")
    tasks: list[PublishTaskRequest] = Field(..., description="任务列表")


@router.post("/publish/parse", summary="发布解析任务")
async def publish_parse_task(
    request: PublishParseTaskRequest,
    publisher: QueuePublisher = Depends(get_publisher)
):
    """
    发布解析任务到队列

    Args:
        request: 解析任务请求
        publisher: 队列发布器

    Returns:
        发布结果
    """
    try:
        task_id = str(uuid.uuid4())

        task_data = {
            "task_id": task_id,
            "task_type": TaskType.PARSE.value,
            "document_id": request.document_id,
            "version_id": request.version_id,
            "priority": request.priority,
            "retry_count": 0,
            "max_retry": 3,
            "created_at": datetime.now().isoformat(),
            "payload": {
                "file_path": request.file_path,
                "config": request.config
            }
        }

        success = publisher.publish_parse_task(task_data)

        if success:
            logger.info(f"解析任务发布成功", extra={"task_id": task_id})
            return success_response(data={
                "task_id": task_id,
                "queue_name": QueueName.PARSE_QUEUE.value,
                "routing_key": RoutingKey.PARSE_START.value
            })
        else:
            return error_response(
                code="QUEUE_001",
                message="任务发布失败"
            )

    except Exception as e:
        logger.error(f"发布解析任务异常: {str(e)}")
        return error_response(
            code="QUEUE_002",
            message=f"发布解析任务异常: {str(e)}"
        )


@router.post("/publish/clean", summary="发布清洗任务")
async def publish_clean_task(
    request: PublishCleanTaskRequest,
    publisher: QueuePublisher = Depends(get_publisher)
):
    """
    发布清洗任务到队列

    Args:
        request: 清洗任务请求
        publisher: 队列发布器

    Returns:
        发布结果
    """
    try:
        task_id = str(uuid.uuid4())

        task_data = {
            "task_id": task_id,
            "task_type": TaskType.CLEAN.value,
            "document_id": request.document_id,
            "version_id": request.version_id,
            "priority": request.priority,
            "retry_count": 0,
            "max_retry": 3,
            "created_at": datetime.now().isoformat(),
            "payload": {
                "element_ids": request.element_ids,
                "config": request.config
            }
        }

        success = publisher.publish_clean_task(task_data)

        if success:
            logger.info(f"清洗任务发布成功", extra={"task_id": task_id})
            return success_response(data={
                "task_id": task_id,
                "queue_name": QueueName.CLEAN_QUEUE.value,
                "routing_key": RoutingKey.CLEAN_START.value
            })
        else:
            return error_response(
                code="QUEUE_001",
                message="任务发布失败"
            )

    except Exception as e:
        logger.error(f"发布清洗任务异常: {str(e)}")
        return error_response(
            code="QUEUE_002",
            message=f"发布清洗任务异常: {str(e)}"
        )


@router.post("/publish/chunk", summary="发布切分任务")
async def publish_chunk_task(
    request: PublishChunkTaskRequest,
    publisher: QueuePublisher = Depends(get_publisher)
):
    """
    发布切分任务到队列

    Args:
        request: 切分任务请求
        publisher: 队列发布器

    Returns:
        发布结果
    """
    try:
        task_id = str(uuid.uuid4())

        task_data = {
            "task_id": task_id,
            "task_type": TaskType.CHUNK.value,
            "document_id": request.document_id,
            "version_id": request.version_id,
            "priority": request.priority,
            "retry_count": 0,
            "max_retry": 3,
            "created_at": datetime.now().isoformat(),
            "payload": {
                "element_ids": request.element_ids,
                "config": request.config
            }
        }

        success = publisher.publish_chunk_task(task_data)

        if success:
            logger.info(f"切分任务发布成功", extra={"task_id": task_id})
            return success_response(data={
                "task_id": task_id,
                "queue_name": QueueName.CHUNK_QUEUE.value,
                "routing_key": RoutingKey.CHUNK_START.value
            })
        else:
            return error_response(
                code="QUEUE_001",
                message="任务发布失败"
            )

    except Exception as e:
        logger.error(f"发布切分任务异常: {str(e)}")
        return error_response(
            code="QUEUE_002",
            message=f"发布切分任务异常: {str(e)}"
        )


@router.post("/publish/embedding", summary="发布向量化任务")
async def publish_embedding_task(
    request: PublishEmbeddingTaskRequest,
    publisher: QueuePublisher = Depends(get_publisher)
):
    """
    发布向量化任务到队列

    Args:
        request: 向量化任务请求
        publisher: 队列发布器

    Returns:
        发布结果
    """
    try:
        task_id = str(uuid.uuid4())

        task_data = {
            "task_id": task_id,
            "task_type": TaskType.EMBEDDING.value,
            "document_id": request.document_id,
            "version_id": request.version_id,
            "priority": request.priority,
            "retry_count": 0,
            "max_retry": 3,
            "created_at": datetime.now().isoformat(),
            "payload": {
                "chunk_ids": request.chunk_ids,
                "batch_size": request.batch_size
            }
        }

        success = publisher.publish_embedding_task(task_data)

        if success:
            logger.info(f"向量化任务发布成功", extra={"task_id": task_id})
            return success_response(data={
                "task_id": task_id,
                "queue_name": QueueName.EMBEDDING_QUEUE.value,
                "routing_key": RoutingKey.EMBEDDING_START.value
            })
        else:
            return error_response(
                code="QUEUE_001",
                message="任务发布失败"
            )

    except Exception as e:
        logger.error(f"发布向量化任务异常: {str(e)}")
        return error_response(
            code="QUEUE_002",
            message=f"发布向量化任务异常: {str(e)}"
        )


@router.post("/publish/index", summary="发布索引任务")
async def publish_index_task(
    request: PublishIndexTaskRequest,
    publisher: QueuePublisher = Depends(get_publisher)
):
    """
    发布索引任务到队列

    Args:
        request: 索引任务请求
        publisher: 队列发布器

    Returns:
        发布结果
    """
    try:
        task_id = str(uuid.uuid4())

        task_data = {
            "task_id": task_id,
            "task_type": TaskType.INDEX.value,
            "document_id": request.document_id,
            "version_id": request.version_id,
            "priority": request.priority,
            "retry_count": 0,
            "max_retry": 3,
            "created_at": datetime.now().isoformat(),
            "payload": {
                "chunk_ids": request.chunk_ids,
                "index_type": request.index_type
            }
        }

        success = publisher.publish_index_task(task_data)

        if success:
            logger.info(f"索引任务发布成功", extra={"task_id": task_id})
            return success_response(data={
                "task_id": task_id,
                "queue_name": QueueName.INDEX_QUEUE.value,
                "routing_key": RoutingKey.INDEX_START.value
            })
        else:
            return error_response(
                code="QUEUE_001",
                message="任务发布失败"
            )

    except Exception as e:
        logger.error(f"发布索引任务异常: {str(e)}")
        return error_response(
            code="QUEUE_002",
            message=f"发布索引任务异常: {str(e)}"
        )


@router.post("/publish/batch", summary="批量发布任务")
async def publish_batch_tasks(
    request: PublishBatchTaskRequest,
    publisher: QueuePublisher = Depends(get_publisher)
):
    """
    批量发布任务到队列

    Args:
        request: 批量发布请求
        publisher: 队列发布器

    Returns:
        批量发布结果
    """
    try:
        results = {
            "total": len(request.tasks),
            "success": 0,
            "failed": 0,
            "tasks": []
        }

        publish_methods = {
            TaskType.PARSE: publisher.publish_parse_task,
            TaskType.CLEAN: publisher.publish_clean_task,
            TaskType.CHUNK: publisher.publish_chunk_task,
            TaskType.EMBEDDING: publisher.publish_embedding_task,
            TaskType.INDEX: publisher.publish_index_task,
        }

        publish_method = publish_methods.get(request.task_type)
        if not publish_method:
            return error_response(
                code="QUEUE_003",
                message=f"不支持的任务类型: {request.task_type}"
            )

        for task in request.tasks:
            task_id = str(uuid.uuid4())

            task_data = {
                "task_id": task_id,
                "task_type": task.task_type.value,
                "document_id": task.document_id,
                "version_id": task.version_id,
                "priority": task.priority,
                "retry_count": 0,
                "max_retry": task.max_retry,
                "created_at": datetime.now().isoformat(),
                "payload": task.payload
            }

            success = publish_method(task_data)
            results["tasks"].append({
                "task_id": task_id,
                "success": success
            })

            if success:
                results["success"] += 1
            else:
                results["failed"] += 1

        logger.info(
            f"批量任务发布完成",
            extra={
                "total": results["total"],
                "success": results["success"],
                "failed": results["failed"]
            }
        )

        return success_response(data=results)

    except Exception as e:
        logger.error(f"批量发布任务异常: {str(e)}")
        return error_response(
            code="QUEUE_002",
            message=f"批量发布任务异常: {str(e)}"
        )


@router.get("/queues", summary="获取队列列表")
async def list_queues():
    """
    获取所有队列的列表

    Returns:
        队列列表
    """
    try:
        queues = []

        for queue_name in QueueName:
            queue_info = {
                "name": queue_name.value,
                "display_name": queue_name.name.replace("_", " ").title()
            }
            queues.append(queue_info)

        return success_response(data={
            "queues": queues
        })

    except Exception as e:
        logger.error(f"获取队列列表异常: {str(e)}")
        return error_response(
            code="QUEUE_002",
            message=f"获取队列列表异常: {str(e)}"
        )


@router.get("/queues/{queue_name}/stats", summary="获取队列统计")
async def get_queue_stats(queue_name: str):
    """
    获取指定队列的统计信息

    Args:
        queue_name: 队列名称

    Returns:
        队列统计信息
    """
    try:
        valid_queues = [q.value for q in QueueName]
        if queue_name not in valid_queues:
            return error_response(
                code="QUEUE_004",
                message=f"队列不存在: {queue_name}"
            )

        publisher = get_publisher()
        stats = publisher.client.get_queue_stats(queue_name)

        return success_response(data=stats)

    except Exception as e:
        logger.error(f"获取队列统计异常: {str(e)}")
        return error_response(
            code="QUEUE_002",
            message=f"获取队列统计异常: {str(e)}"
        )


@router.get("/dlx/messages", summary="获取死信队列消息")
async def get_dlx_messages(
    limit: int = 10,
    offset: int = 0
):
    """
    获取死信队列中的消息

    Args:
        limit: 返回数量限制
        offset: 偏移量

    Returns:
        死信消息列表
    """
    try:
        publisher = get_publisher()
        result = publisher.client.get_dlx_messages(limit=limit, offset=offset)

        return success_response(data=result)

    except Exception as e:
        logger.error(f"获取死信消息异常: {str(e)}")
        return error_response(
            code="QUEUE_002",
            message=f"获取死信消息异常: {str(e)}"
        )


@router.delete("/dlx/messages/{message_id}", summary="删除死信消息")
async def delete_dlx_message(message_id: str):
    """
    删除指定的死信消息

    Args:
        message_id: 消息ID

    Returns:
        删除结果
    """
    try:
        publisher = get_publisher()
        result = publisher.client.delete_dlx_message(message_id)

        logger.info(f"删除死信消息", extra={"message_id": message_id, "result": result})
        return success_response(data=result)

    except Exception as e:
        logger.error(f"删除死信消息异常: {str(e)}")
        return error_response(
            code="QUEUE_002",
            message=f"删除死信消息异常: {str(e)}"
        )


@router.delete("/dlx/messages", summary="清空死信队列")
async def clear_dlx_messages():
    """
    清空死信队列中的所有消息

    Returns:
        清空结果
    """
    try:
        publisher = get_publisher()
        result = publisher.client.clear_dlx_messages()

        logger.info("清空死信队列", extra=result)
        return success_response(data=result)

    except Exception as e:
        logger.error(f"清空死信队列异常: {str(e)}")
        return error_response(
            code="QUEUE_002",
            message=f"清空死信队列异常: {str(e)}"
        )


@router.get("/health", summary="队列健康检查")
async def check_queue_health():
    """
    检查队列服务健康状态，包括 Worker 连接状态

    Returns:
        健康状态信息
    """
    try:
        from app.services.queue_consumer import get_queue_publisher

        publisher = get_publisher()
        result = {
            "rabbitmq_connected": False,
            "queues": {},
            "workers_status": {}
        }

        # 检查每个队列的状态
        queue_names = [
            ("parse", "rag_parse_queue", "rag.parse.start"),
            ("clean", "rag_clean_queue", "rag.clean.start"),
            ("chunk", "rag_chunk_queue", "rag.chunk.start"),
            ("embedding", "rag_embedding_queue", "rag.embedding.start"),
            ("index", "rag_index_queue", "rag.index.start"),
        ]

        connected_count = 0
        total_queues = len(queue_names)

        for worker_type, queue_name, routing_key in queue_names:
            try:
                stats = publisher.client.get_queue_stats(queue_name)
                result["queues"][worker_type] = {
                    "queue_name": queue_name,
                    "message_count": stats.get("message_count", 0),
                    "consumer_count": stats.get("consumer_count", 0),
                    "has_consumer": stats.get("consumer_count", 0) > 0
                }
                if stats.get("consumer_count", 0) > 0:
                    connected_count += 1
            except Exception as e:
                result["queues"][worker_type] = {
                    "queue_name": queue_name,
                    "error": str(e),
                    "has_consumer": False
                }

        result["rabbitmq_connected"] = connected_count > 0
        result["summary"] = {
            "total_queues": total_queues,
            "active_workers": connected_count,
            "worker_running": connected_count > 0
        }

        status_code = 200 if connected_count > 0 else 503
        return success_response(data=result)

    except Exception as e:
        logger.error(f"队列健康检查异常: {str(e)}")
        return error_response(
            code="QUEUE_005",
            message=f"队列健康检查异常: {str(e)}"
        )
