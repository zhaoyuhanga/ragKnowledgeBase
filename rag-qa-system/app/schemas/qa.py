"""
RAG 问答系统 - 问答 Schema 模块
问答相关的请求/响应数据模型
"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class QAAskRequest(BaseModel):
    """
    问答请求模型
    """
    question: str = Field(
        min_length=1, 
        max_length=1000, 
        description="用户问题"
    )
    session_id: Optional[str] = Field(
        default=None, 
        max_length=64,
        description="会话 ID（用于多轮对话）"
    )
    top_k: Optional[int] = Field(
        default=None,
        ge=1,
        le=20,
        description="检索的文档数量"
    )
    temperature: Optional[float] = Field(
        default=0.3,
        ge=0.0,
        le=2.0,
        description="生成温度参数"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "question": "什么是 RAG 技术？",
                "session_id": "user_123_session_001",
                "top_k": 5,
                "temperature": 0.3
            }
        }


class SourceItem(BaseModel):
    """
    回答来源项
    """
    chunk_id: Optional[int] = Field(description="文档块 ID")
    document_id: Optional[int] = Field(description="文档 ID")
    filename: str = Field(description="来源文件名")
    content: str = Field(description="来源文本内容（截取）")
    similarity: float = Field(description="相似度分数")

    class Config:
        json_schema_extra = {
            "example": {
                "chunk_id": 1,
                "document_id": 1,
                "filename": "技术文档.pdf",
                "content": "RAG（Retrieval-Augmented Generation）是检索增强生成的缩写...",
                "similarity": 0.85
            }
        }


class QAAskResponse(BaseModel):
    """
    问答响应模型
    """
    answer: str = Field(description="系统回答")
    sources: List[SourceItem] = Field(description="回答来源列表")
    cache_hit: bool = Field(description="是否命中缓存")
    response_time_ms: int = Field(description="响应耗时（毫秒）")
    error: Optional[str] = Field(description="错误信息", default=None)

    class Config:
        json_schema_extra = {
            "example": {
                "answer": "RAG（Retrieval-Augmented Generation）是检索增强生成的缩写...",
                "sources": [
                    {
                        "chunk_id": 1,
                        "document_id": 1,
                        "filename": "技术文档.pdf",
                        "content": "RAG（Retrieval-Augmented Generation）是检索增强生成的缩写...",
                        "similarity": 0.85
                    }
                ],
                "cache_hit": False,
                "response_time_ms": 1500
            }
        }


class QAHistoryItem(BaseModel):
    """
    问答历史项
    """
    id: int = Field(description="记录 ID")
    question: str = Field(description="用户问题")
    answer: Optional[str] = Field(description="系统回答")
    referenced_chunks: Optional[List[str]] = Field(description="引用的文档块 ID 列表（vector_id）")
    response_time_ms: Optional[int] = Field(description="响应耗时（毫秒）")
    cache_hit: bool = Field(description="是否命中缓存")
    session_id: Optional[str] = Field(description="会话 ID")
    created_at: datetime = Field(description="创建时间")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "question": "什么是 RAG 技术？",
                "answer": "RAG 是检索增强生成的缩写...",
                "referenced_chunks": [1, 2, 3],
                "response_time_ms": 1500,
                "cache_hit": False,
                "session_id": "user_123_session_001",
                "created_at": "2026-05-13T10:00:00"
            }
        }


class QAHistoryQuery(BaseModel):
    """
    问答历史查询参数
    """
    session_id: Optional[str] = Field(default=None, description="会话 ID")
    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=20, ge=1, le=100, description="每页数量")


class QAHistoryResponse(BaseModel):
    """
    问答历史响应
    """
    items: List[QAHistoryItem] = Field(description="历史记录列表")
    total: int = Field(description="总记录数")
    page: int = Field(description="当前页码")
    page_size: int = Field(description="每页数量")
    total_pages: int = Field(description="总页数")

    class Config:
        json_schema_extra = {
            "example": {
                "items": [],
                "total": 100,
                "page": 1,
                "page_size": 20,
                "total_pages": 5
            }
        }


class KnowledgeSearchRequest(BaseModel):
    """
    知识库检索请求
    """
    query: str = Field(
        min_length=1,
        max_length=500,
        description="检索查询"
    )
    top_k: Optional[int] = Field(
        default=5,
        ge=1,
        le=20,
        description="返回结果数量"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "query": "RAG 技术",
                "top_k": 5
            }
        }


class KnowledgeSearchItem(BaseModel):
    """
    知识库检索结果项
    """
    vector_id: str = Field(description="向量 ID")
    document_id: int = Field(description="文档 ID")
    chunk_index: int = Field(description="块序号")
    filename: str = Field(description="文件名")
    content: str = Field(description="文本内容")
    similarity: float = Field(description="相似度分数")

    class Config:
        json_schema_extra = {
            "example": {
                "vector_id": "1_0_a1b2c3d4",
                "document_id": 1,
                "chunk_index": 0,
                "filename": "技术文档.pdf",
                "content": "RAG（Retrieval-Augmented Generation）是检索增强生成的缩写...",
                "similarity": 0.85
            }
        }


class KnowledgeSearchResponse(BaseModel):
    """
    知识库检索响应
    """
    query: str = Field(description="原始查询")
    results: List[KnowledgeSearchItem] = Field(description="检索结果列表")
    total: int = Field(description="结果数量")

    class Config:
        json_schema_extra = {
            "example": {
                "query": "RAG 技术",
                "results": [],
                "total": 5
            }
        }


class KnowledgeRebuildResponse(BaseModel):
    """
    知识库重建响应
    """
    success: bool = Field(description="是否成功")
    total_documents: int = Field(description="处理的文档总数")
    success_count: int = Field(description="成功数量")
    failed_count: int = Field(description="失败数量")
    total_chunks: int = Field(description="生成的块总数")
    duration_ms: int = Field(description="耗时（毫秒）")
    message: str = Field(description="响应消息")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "total_documents": 10,
                "success_count": 9,
                "failed_count": 1,
                "total_chunks": 450,
                "duration_ms": 30000,
                "message": "知识库重建完成"
            }
        }


class CacheClearResponse(BaseModel):
    """
    缓存清空响应
    """
    success: bool = Field(description="是否成功")
    cleared_count: int = Field(description="清空的缓存数量")
    message: str = Field(description="响应消息")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "cleared_count": 50,
                "message": "缓存清空成功"
            }
        }
