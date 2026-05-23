# -*- coding: utf-8 -*-
"""
文档数据模型

本模块定义文档相关的Pydantic数据模型：
- 文档创建、更新、响应模型
- 版本响应模型
- 导入任务响应模型
- 上传请求/响应模型
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ================================================
# 文档相关模型
# ================================================

class DocumentBase(BaseModel):
    """文档基础模型"""
    name: str = Field(..., description="文档名称", min_length=1, max_length=255)
    doc_type: str = Field(..., description="文档类型")
    business_id: Optional[str] = Field(None, description="业务归属ID")
    business_name: Optional[str] = Field(None, description="业务归属名称")


class DocumentCreate(DocumentBase):
    """文档创建模型"""
    creator_id: Optional[int] = Field(None, description="创建人ID")
    creator_name: Optional[str] = Field(None, description="创建人姓名")


class DocumentUpdate(BaseModel):
    """文档更新模型"""
    name: Optional[str] = Field(None, description="文档名称")
    business_id: Optional[str] = Field(None, description="业务归属ID")
    business_name: Optional[str] = Field(None, description="业务归属名称")


class DocumentListItem(BaseModel):
    """文档列表项模型"""
    id: int = Field(..., description="文档ID")
    name: str = Field(..., description="文档名称")
    doc_type: str = Field(..., description="文档类型")
    business_id: Optional[str] = Field(None, description="业务归属ID")
    business_name: Optional[str] = Field(None, description="业务归属名称")
    current_version_id: Optional[int] = Field(None, description="当前版本ID")
    total_versions: int = Field(..., description="版本总数")
    status: int = Field(..., description="状态：0-待解析 1-解析中 2-已解析 3-解析失败 9-已删除")
    status_name: str = Field(..., description="状态名称")
    total_pages: int = Field(default=0, description="总页数")
    total_chunks: int = Field(default=0, description="总Chunk数")
    creator_name: Optional[str] = Field(None, description="创建人姓名")
    created_at: Optional[str] = Field(None, description="创建时间")

    class Config:
        from_attributes = True


class DocumentDetailResponse(BaseModel):
    """文档详情响应模型"""
    id: int = Field(..., description="文档ID")
    name: str = Field(..., description="文档名称")
    doc_type: str = Field(..., description="文档类型")
    business_id: Optional[str] = Field(None, description="业务归属ID")
    business_name: Optional[str] = Field(None, description="业务归属名称")
    current_version_id: Optional[int] = Field(None, description="当前版本ID")
    total_versions: int = Field(..., description="版本总数")
    status: int = Field(..., description="状态")
    status_name: str = Field(..., description="状态名称")
    total_pages: int = Field(default=0, description="总页数")
    total_chunks: int = Field(default=0, description="总Chunk数")
    creator_id: Optional[int] = Field(None, description="创建人ID")
    creator_name: Optional[str] = Field(None, description="创建人姓名")
    created_at: Optional[str] = Field(None, description="创建时间")
    updated_at: Optional[str] = Field(None, description="更新时间")
    versions: List[Dict[str, Any]] = Field(default_factory=list, description="版本列表")

    class Config:
        from_attributes = True


# ================================================
# 版本相关模型
# ================================================

class VersionListItem(BaseModel):
    """版本列表项模型"""
    id: int = Field(..., description="版本ID")
    version: int = Field(..., description="版本号")
    file_name: str = Field(..., description="文件名")
    file_size: int = Field(..., description="文件大小")
    file_hash: Optional[str] = Field(None, description="文件哈希")
    status: int = Field(..., description="状态")
    parse_status: Optional[str] = Field(None, description="解析状态")
    parse_progress: int = Field(default=0, description="解析进度")
    total_pages: int = Field(default=0, description="总页数")
    uploader_name: Optional[str] = Field(None, description="上传人姓名")
    uploaded_at: Optional[str] = Field(None, description="上传时间")
    parsed_at: Optional[str] = Field(None, description="解析完成时间")

    class Config:
        from_attributes = True


class VersionDetailResponse(BaseModel):
    """版本详情响应模型"""
    id: int = Field(..., description="版本ID")
    document_id: int = Field(..., description="文档ID")
    version: int = Field(..., description="版本号")
    file_name: str = Field(..., description="文件名")
    file_size: int = Field(..., description="文件大小")
    file_hash: str = Field(..., description="文件哈希")
    file_path: str = Field(..., description="文件路径")
    mime_type: Optional[str] = Field(None, description="MIME类型")
    storage_type: str = Field(..., description="存储类型")
    status: int = Field(..., description="状态")
    parse_status: Optional[str] = Field(None, description="解析状态")
    parse_progress: int = Field(default=0, description="解析进度")
    parse_confidence: Optional[str] = Field(None, description="解析置信度")
    total_pages: int = Field(default=0, description="总页数")
    total_elements: int = Field(default=0, description="解析元素总数")
    uploader_id: Optional[int] = Field(None, description="上传人ID")
    uploader_name: Optional[str] = Field(None, description="上传人姓名")
    uploaded_at: Optional[str] = Field(None, description="上传时间")
    parsed_at: Optional[str] = Field(None, description="解析完成时间")
    error_message: Optional[str] = Field(None, description="错误信息")
    created_at: Optional[str] = Field(None, description="创建时间")

    class Config:
        from_attributes = True


# ================================================
# 上传相关模型
# ================================================

class UploadResult(BaseModel):
    """单个文件上传结果"""
    document_id: int = Field(..., description="文档ID")
    version_id: int = Field(..., description="版本ID")
    task_id: Optional[str] = Field(None, description="任务ID")
    name: str = Field(..., description="文件名")
    doc_type: str = Field(..., description="文档类型")
    file_size: int = Field(..., description="文件大小")
    file_hash: str = Field(..., description="文件哈希")
    is_duplicate: bool = Field(..., description="是否重复文件")
    status: str = Field(..., description="状态")
    message: str = Field(..., description="结果消息")

    class Config:
        from_attributes = True


class FailedFile(BaseModel):
    """上传失败的文件"""
    name: str = Field(..., description="文件名")
    error: str = Field(..., description="错误信息")


class BatchUploadResponse(BaseModel):
    """批量上传响应模型"""
    total: int = Field(..., description="总文件数")
    success: int = Field(..., description="成功数")
    failed: int = Field(..., description="失败数")
    duplicates: int = Field(..., description="重复数")
    documents: List[Dict[str, Any]] = Field(default_factory=list, description="成功上传的文档")
    failed_files: List[FailedFile] = Field(default_factory=list, description="失败的文件")

    class Config:
        from_attributes = True


# ================================================
# 导入任务相关模型
# ================================================

class ImportTaskResponse(BaseModel):
    """导入任务响应模型"""
    id: int = Field(..., description="任务主键ID")
    task_id: str = Field(..., description="任务唯一ID")
    document_id: Optional[int] = Field(None, description="关联文档ID")
    version_id: Optional[int] = Field(None, description="关联版本ID")
    task_type: str = Field(..., description="任务类型")
    task_status: str = Field(..., description="任务状态")
    priority: int = Field(..., description="优先级")
    progress: int = Field(..., description="进度")
    retry_count: int = Field(..., description="重试次数")
    max_retry: int = Field(..., description="最大重试次数")
    error_type: Optional[str] = Field(None, description="错误类型")
    error_message: Optional[str] = Field(None, description="错误信息")
    started_at: Optional[str] = Field(None, description="开始时间")
    completed_at: Optional[str] = Field(None, description="完成时间")
    cost_seconds: Optional[int] = Field(None, description="耗时(秒)")
    created_at: Optional[str] = Field(None, description="创建时间")

    class Config:
        from_attributes = True


class ImportTaskListItem(BaseModel):
    """导入任务列表项模型"""
    id: int = Field(..., description="任务ID")
    task_id: str = Field(..., description="任务唯一ID")
    document_id: Optional[int] = Field(None, description="文档ID")
    task_type: str = Field(..., description="任务类型")
    task_status: str = Field(..., description="任务状态")
    status_name: str = Field(..., description="状态名称")
    progress: int = Field(..., description="进度")
    created_at: Optional[str] = Field(None, description="创建时间")

    class Config:
        from_attributes = True
