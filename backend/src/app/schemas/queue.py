# -*- coding: utf-8 -*-
"""
队列消息模型

本模块定义队列消息的数据结构：
1. 任务消息模型
2. 消息状态枚举
3. 消息结果模型
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class TaskType(str, Enum):
    """任务类型枚举"""
    PARSE = "parse"          # 解析任务
    CLEAN = "clean"          # 清洗任务
    CHUNK = "chunk"          # 切分任务
    EMBEDDING = "embedding"  # 向量化任务
    INDEX = "index"          # 索引任务


class TaskStatus(str, Enum):
    """任务状态枚举"""
    PENDING = "pending"       # 待处理
    RUNNING = "running"       # 处理中
    COMPLETED = "completed"   # 已完成
    FAILED = "failed"         # 失败
    RETRYING = "retrying"     # 重试中


class QueueName(str, Enum):
    """队列名称枚举"""
    PARSE_QUEUE = "rag_parse_queue"         # 解析队列
    CLEAN_QUEUE = "rag_clean_queue"          # 清洗队列
    CHUNK_QUEUE = "rag_chunk_queue"          # 切分队列
    EMBEDDING_QUEUE = "rag_embedding_queue"  # 向量化队列
    INDEX_QUEUE = "rag_index_queue"          # 索引队列
    DLX_QUEUE = "rag_dlx_queue"             # 死信队列


class RoutingKey(str, Enum):
    """路由键枚举"""
    PARSE_START = "rag.parse.start"         # 解析开始
    PARSE_COMPLETE = "rag.parse.complete"    # 解析完成
    PARSE_FAILED = "rag.parse.failed"        # 解析失败
    CLEAN_START = "rag.clean.start"          # 清洗开始
    CLEAN_COMPLETE = "rag.clean.complete"    # 清洗完成
    CLEAN_FAILED = "rag.clean.failed"        # 清洗失败
    CHUNK_START = "rag.chunk.start"          # 切分开始
    CHUNK_COMPLETE = "rag.chunk.complete"    # 切分完成
    CHUNK_FAILED = "rag.chunk.failed"        # 切分失败
    EMBEDDING_START = "rag.embedding.start"  # 向量化开始
    EMBEDDING_COMPLETE = "rag.embedding.complete"  # 向量化完成
    EMBEDDING_FAILED = "rag.embedding.failed"  # 向量化失败
    INDEX_START = "rag.index.start"          # 索引开始
    INDEX_COMPLETE = "rag.index.complete"    # 索引完成
    INDEX_FAILED = "rag.index.failed"        # 索引失败


class TaskMessage(BaseModel):
    """
    任务消息模型

    定义队列消息的通用结构。
    """
    task_id: str = Field(..., description="任务唯一ID")
    task_type: TaskType = Field(..., description="任务类型")
    document_id: int = Field(..., description="文档ID")
    version_id: int = Field(..., description="版本ID")
    priority: int = Field(default=5, ge=1, le=10, description="优先级 1-10")
    retry_count: int = Field(default=0, description="当前重试次数")
    max_retry: int = Field(default=3, description="最大重试次数")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: Optional[datetime] = Field(default=None, description="更新时间")
    started_at: Optional[datetime] = Field(default=None, description="开始时间")
    completed_at: Optional[datetime] = Field(default=None, description="完成时间")
    payload: Dict[str, Any] = Field(default_factory=dict, description="任务参数")
    error_info: Optional[Dict[str, Any]] = Field(default=None, description="错误信息")

    class Config:
        """Pydantic配置"""
        use_enum_values = True


class ParseTaskMessage(TaskMessage):
    """
    解析任务消息

    继承自TaskMessage，添加解析任务特有的字段。
    """
    task_type: TaskType = Field(default=TaskType.PARSE, description="任务类型")
    payload: Dict[str, Any] = Field(default_factory=dict, description="任务参数，包含file_path等信息")

    def get_file_path(self) -> Optional[str]:
        """获取文件路径"""
        return self.payload.get("file_path")

    def get_parser_config(self) -> Dict[str, Any]:
        """获取解析配置"""
        return self.payload.get("config", {})


class CleanTaskMessage(TaskMessage):
    """
    清洗任务消息

    继承自TaskMessage，添加清洗任务特有的字段。
    """
    task_type: TaskType = Field(default=TaskType.CLEAN, description="任务类型")
    payload: Dict[str, Any] = Field(default_factory=dict, description="任务参数")

    def get_cleaning_config(self) -> Dict[str, Any]:
        """获取清洗配置"""
        return self.payload.get("config", {})

    def get_element_ids(self) -> List[int]:
        """获取元素ID列表"""
        return self.payload.get("element_ids", [])


class ChunkTaskMessage(TaskMessage):
    """
    切分任务消息

    继承自TaskMessage，添加切分任务特有的字段。
    """
    task_type: TaskType = Field(default=TaskType.CHUNK, description="任务类型")
    payload: Dict[str, Any] = Field(default_factory=dict, description="任务参数")

    def get_chunk_config(self) -> Dict[str, Any]:
        """获取切分配置"""
        return self.payload.get("config", {})

    def get_element_ids(self) -> List[int]:
        """获取元素ID列表"""
        return self.payload.get("element_ids", [])


class EmbeddingTaskMessage(TaskMessage):
    """
    向量化任务消息

    继承自TaskMessage，添加向量化任务特有的字段。
    """
    task_type: TaskType = Field(default=TaskType.EMBEDDING, description="任务类型")
    payload: Dict[str, Any] = Field(default_factory=dict, description="任务参数")

    def get_chunk_ids(self) -> List[int]:
        """获取Chunk ID列表"""
        return self.payload.get("chunk_ids", [])

    def get_batch_size(self) -> int:
        """获取批处理大小"""
        return self.payload.get("batch_size", 32)


class IndexTaskMessage(TaskMessage):
    """
    索引任务消息

    继承自TaskMessage，添加索引任务特有的字段。
    """
    task_type: TaskType = Field(default=TaskType.INDEX, description="任务类型")
    payload: Dict[str, Any] = Field(default_factory=dict, description="任务参数")

    def get_chunk_ids(self) -> List[int]:
        """获取Chunk ID列表"""
        return self.payload.get("chunk_ids", [])

    def get_index_type(self) -> str:
        """获取索引类型"""
        return self.payload.get("index_type", "milvus")


class TaskResult(BaseModel):
    """
    任务结果模型

    定义任务执行后的返回结果。
    """
    task_id: str = Field(..., description="任务ID")
    task_type: TaskType = Field(..., description="任务类型")
    status: TaskStatus = Field(..., description="任务状态")
    document_id: int = Field(..., description="文档ID")
    version_id: int = Field(..., description="版本ID")
    result: Optional[Dict[str, Any]] = Field(default=None, description="任务结果")
    error_type: Optional[str] = Field(default=None, description="错误类型")
    error_message: Optional[str] = Field(default=None, description="错误信息")
    cost_seconds: Optional[int] = Field(default=None, description="耗时（秒）")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    completed_at: Optional[datetime] = Field(default=None, description="完成时间")

    class Config:
        """Pydantic配置"""
        use_enum_values = True


class DeadLetterMessage(BaseModel):
    """
    死信消息模型

    定义进入死信队列的消息结构。
    """
    original_message: Dict[str, Any] = Field(..., description="原始消息")
    error_type: str = Field(..., description="错误类型")
    error_message: str = Field(..., description="错误信息")
    error_stack: Optional[str] = Field(default=None, description="错误堆栈")
    failed_at: datetime = Field(default_factory=datetime.now, description="失败时间")
    retry_count: int = Field(default=0, description="重试次数")
    original_queue: str = Field(..., description="原始队列名称")

    class Config:
        """Pydantic配置"""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class QueueStats(BaseModel):
    """
    队列统计模型

    定义队列的统计信息。
    """
    queue_name: str = Field(..., description="队列名称")
    message_count: int = Field(default=0, description="当前消息数")
    consumer_count: int = Field(default=0, description="消费者数量")
    published_total: int = Field(default=0, description="累计发布数")
    consumed_total: int = Field(default=0, description="累计消费数")
    failed_total: int = Field(default=0, description="累计失败数")
    avg_process_time_ms: float = Field(default=0.0, description="平均处理时间（毫秒）")


class WorkerConfig(BaseModel):
    """Worker配置模型"""
    worker_name: str = Field(..., description="Worker名称")
    queue_name: str = Field(..., description="监听的队列名称")
    prefetch_count: int = Field(default=10, description="预取消息数")
    max_workers: int = Field(default=1, description="最大工作线程数")
    enable_retry: bool = Field(default=True, description="是否启用重试")
    max_retry: int = Field(default=3, description="最大重试次数")
    retry_delay_seconds: int = Field(default=5, description="重试延迟（秒）")
    enable_dlx: bool = Field(default=True, description="是否启用死信队列")
