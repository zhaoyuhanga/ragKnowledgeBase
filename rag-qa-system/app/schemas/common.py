"""
RAG 问答系统 - 通用响应模型
定义统一的 API 响应格式
"""

from typing import TypeVar, Generic, Optional, Any
from pydantic import BaseModel, Field

T = TypeVar("T")


class ResponseBase(BaseModel):
    """
    响应基础模型
    所有 API 响应都应继承此模型
    """
    success: bool = Field(default=True, description="请求是否成功")
    message: str = Field(default="操作成功", description="响应消息")
    code: int = Field(default=200, description="状态码")


class DataResponse(ResponseBase, Generic[T]):
    """
    数据响应模型
    用于返回数据的响应
    """
    data: Optional[T] = Field(default=None, description="响应数据")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "操作成功",
                "code": 200,
                "data": {}
            }
        }


class PaginatedDataResponse(ResponseBase):
    """
    分页数据响应模型
    用于返回分页列表数据
    """
    data: Optional[list] = Field(default=None, description="数据列表")
    total: int = Field(default=0, description="总记录数")
    page: int = Field(default=1, description="当前页码")
    page_size: int = Field(default=20, description="每页记录数")
    total_pages: int = Field(default=0, description="总页数")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "查询成功",
                "code": 200,
                "data": [],
                "total": 100,
                "page": 1,
                "page_size": 20,
                "total_pages": 5
            }
        }


class ErrorResponse(ResponseBase):
    """
    错误响应模型
    用于返回错误信息
    """
    error: Optional[str] = Field(default=None, description="错误详情")
    detail: Optional[str] = Field(default=None, description="错误堆栈（仅开发环境）")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": False,
                "message": "请求参数错误",
                "code": 400,
                "error": "文件大小超过限制"
            }
        }


class HealthCheckResponse(BaseModel):
    """
    健康检查响应模型
    """
    status: str = Field(description="服务状态: healthy/unhealthy/degraded")
    mysql: bool = Field(description="MySQL 连接状态")
    redis: bool = Field(description="Redis 连接状态")
    chromadb: bool = Field(description="ChromaDB 连接状态")
    llm: bool = Field(description="LLM API 连接状态")
    embedding: bool = Field(description="Embedding 模型状态")
    version: str = Field(default="1.0.0", description="服务版本")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "mysql": True,
                "redis": True,
                "chromadb": True,
                "llm": True,
                "embedding": True,
                "version": "1.0.0"
            }
        }


class StatsResponse(BaseModel):
    """
    系统统计响应模型
    """
    documents: dict = Field(description="文档统计")
    chunks: dict = Field(description="文档块统计")
    vectors: dict = Field(description="向量统计")
    qa: dict = Field(description="问答统计")
    
    class Config:
        json_schema_extra = {
            "example": {
                "documents": {
                    "total": 10,
                    "processed": 8,
                    "failed": 1,
                    "processing": 1
                },
                "chunks": {
                    "total": 500
                },
                "vectors": {
                    "count": 500,
                    "collection_name": "knowledge_base"
                },
                "qa": {
                    "total_questions": 100,
                    "cached_questions": 30,
                    "cache_rate": 30.0,
                    "avg_response_time_ms": 1500.5
                }
            }
        }
