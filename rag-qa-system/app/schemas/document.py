"""
RAG 问答系统 - 文档 Schema 模块
文档相关的请求/响应数据模型
"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class DocumentUploadResponse(BaseModel):
    """
    文档上传响应
    """
    id: int = Field(description="文档 ID")
    filename: str = Field(description="文件名")
    file_type: str = Field(description="文件类型")
    file_size: int = Field(description="文件大小（字节）")
    status: int = Field(description="处理状态: 0=处理中, 1=已完成, 2=失败")
    message: str = Field(default="文档上传成功，正在处理中...", description="响应消息")

    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "filename": "技术文档.pdf",
                "file_type": "pdf",
                "file_size": 1024000,
                "status": 0,
                "message": "文档上传成功，正在处理中..."
            }
        }


class DocumentItem(BaseModel):
    """
    文档列表项
    """
    id: int = Field(description="文档 ID")
    filename: str = Field(description="文件名")
    file_type: str = Field(description="文件类型")
    file_size: int = Field(description="文件大小（字节）")
    status: int = Field(description="处理状态: 0=处理中, 1=已完成, 2=失败")
    chunk_count: int = Field(description="切分块数量")
    created_at: datetime = Field(description="创建时间")
    updated_at: datetime = Field(description="更新时间")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "filename": "技术文档.pdf",
                "file_type": "pdf",
                "file_size": 1024000,
                "status": 1,
                "chunk_count": 50,
                "created_at": "2026-05-13T10:00:00",
                "updated_at": "2026-05-13T10:00:30"
            }
        }


class DocumentDetailResponse(BaseModel):
    """
    文档详情响应
    """
    id: int = Field(description="文档 ID")
    filename: str = Field(description="文件名")
    file_path: str = Field(description="文件存储路径")
    file_type: str = Field(description="文件类型")
    file_size: int = Field(description="文件大小（字节）")
    content_hash: Optional[str] = Field(description="文件内容哈希", default=None)
    status: int = Field(description="处理状态")
    chunk_count: int = Field(description="切分块数量")
    error_message: Optional[str] = Field(description="错误信息", default=None)
    created_at: datetime = Field(description="创建时间")
    updated_at: datetime = Field(description="更新时间")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "filename": "技术文档.pdf",
                "file_path": "/data/documents/abc123_技术文档.pdf",
                "file_type": "pdf",
                "file_size": 1024000,
                "content_hash": "d41d8cd98f00b204e9800998ecf8427e",
                "status": 1,
                "chunk_count": 50,
                "error_message": None,
                "created_at": "2026-05-13T10:00:00",
                "updated_at": "2026-05-13T10:00:30"
            }
        }


class DocumentContentResponse(BaseModel):
    """
    文档内容预览响应
    """
    document_id: int = Field(description="文档 ID")
    filename: str = Field(description="文件名")
    content: str = Field(description="文档内容（文本形式）")
    chunk_count: int = Field(description="块数量")

    class Config:
        json_schema_extra = {
            "example": {
                "document_id": 1,
                "filename": "技术文档.pdf",
                "content": "这是文档的第一部分内容...\n\n这是文档的第二部分内容...",
                "chunk_count": 50
            }
        }


class DocumentListQuery(BaseModel):
    """
    文档列表查询参数
    """
    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=20, ge=1, le=100, description="每页数量")
    status: Optional[int] = Field(default=None, description="状态过滤: 0=处理中, 1=已完成, 2=失败")


class DocumentListResponse(BaseModel):
    """
    文档列表响应
    """
    items: List[DocumentItem] = Field(description="文档列表")
    total: int = Field(description="总记录数")
    page: int = Field(description="当前页码")
    page_size: int = Field(description="每页数量")
    total_pages: int = Field(description="总页数")

    class Config:
        json_schema_extra = {
            "example": {
                "items": [],
                "total": 10,
                "page": 1,
                "page_size": 20,
                "total_pages": 1
            }
        }


class DocumentDeleteResponse(BaseModel):
    """
    文档删除响应
    """
    success: bool = Field(description="是否成功")
    message: str = Field(description="响应消息")
    document_id: int = Field(description="删除的文档 ID")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "文档删除成功",
                "document_id": 1
            }
        }


class ChunkItem(BaseModel):
    """
    文档块项
    """
    id: int = Field(description="块 ID")
    document_id: int = Field(description="文档 ID")
    chunk_index: int = Field(description="块序号")
    content: str = Field(description="文本内容")
    char_count: int = Field(description="字符数量")
    vector_id: Optional[str] = Field(description="向量 ID", default=None)
    created_at: datetime = Field(description="创建时间")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "document_id": 1,
                "chunk_index": 0,
                "content": "这是文档的第一个文本块内容...",
                "char_count": 500,
                "vector_id": "1_0_a1b2c3d4",
                "created_at": "2026-05-13T10:00:00"
            }
        }
