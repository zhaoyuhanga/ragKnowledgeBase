# -*- coding: utf-8 -*-
"""
切分相关数据Schema

本模块定义切分服务相关的数据模型：
- 切分配置请求/响应模型
- 切分结果模型
- Chunk响应模型
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ================================================
# 切分配置相关模型
# ================================================

class ChunkConfigRequest(BaseModel):
    """切分配置请求模型"""
    target_tokens: int = Field(default=600, description="目标Token数", ge=100, le=2000)
    max_tokens: int = Field(default=900, description="最大Token数", ge=200, le=3000)
    min_tokens: int = Field(default=120, description="最小Token数", ge=50, le=500)
    overlap_tokens: int = Field(default=100, description="重叠Token数", ge=0, le=500)
    semantic_threshold: float = Field(default=0.85, description="语义切分阈值", ge=0.0, le=1.0)
    split_by_title: bool = Field(default=True, description="是否按标题切分")
    split_by_paragraph: bool = Field(default=True, description="是否按段落切分")
    merge_short_chunks: bool = Field(default=True, description="是否合并过短片段")
    preserve_tables: bool = Field(default=True, description="是否保留表格完整性")
    preserve_images: bool = Field(default=True, description="是否保留图片完整性")


class ChunkingStrategy(str):
    """切分策略枚举"""
    TITLE_BASED = "title_based"           # 基于标题的切分
    SEMANTIC = "semantic"                 # 语义切分
    FIXED_SIZE = "fixed_size"             # 固定大小切分
    MIXED = "mixed"                       # 混合切分


# ================================================
# Chunk元素相关模型
# ================================================

class ChunkElement(BaseModel):
    """Chunk元素模型"""
    chunk_id: str = Field(..., description="Chunk唯一ID")
    chunk_index: int = Field(..., description="Chunk索引")
    content: str = Field(..., description="Chunk内容")
    enhanced_content: Optional[str] = Field(None, description="增强内容")
    chunk_type: str = Field(..., description="Chunk类型：paragraph/table/image/chart/code/list")
    token_count: int = Field(..., description="Token数量")
    char_count: int = Field(..., description="字符数量")
    title_path: Optional[str] = Field(None, description="标题层级路径")
    chapter_path: Optional[str] = Field(None, description="章节路径")
    page_start: Optional[int] = Field(None, description="起始页码")
    page_end: Optional[int] = Field(None, description="结束页码")
    quality_score: Optional[float] = Field(None, description="质量评分")
    element_ids: List[str] = Field(default_factory=list, description="来源元素ID列表")
    # 表格相关字段
    table_summary: Optional[str] = Field(None, description="表格摘要")
    table_schema: Optional[Dict[str, Any]] = Field(None, description="表结构")
    # 图片相关字段
    image_description: Optional[Dict[str, Any]] = Field(None, description="图片描述")
    # 重叠相关字段
    has_previous_overlap: bool = Field(default=False, description="是否与前一个Chunk有重叠")
    has_next_overlap: bool = Field(default=False, description="是否与后一个Chunk有重叠")
    overlap_with_previous: Optional[str] = Field(None, description="与前一个Chunk的重叠内容")
    overlap_with_next: Optional[str] = Field(None, description="与后一个Chunk的重叠内容")


# ================================================
# 切分结果相关模型
# ================================================

class ChunkingResult(BaseModel):
    """切分结果模型"""
    document_id: int = Field(..., description="文档ID")
    version_id: int = Field(..., description="版本ID")
    total_elements: int = Field(..., description="处理的元素总数")
    total_chunks: int = Field(..., description="生成的Chunk总数")
    strategy_used: str = Field(..., description="使用的切分策略")
    config: ChunkConfigRequest = Field(..., description="使用的切分配置")
    chunks: List[ChunkElement] = Field(default_factory=list, description="生成的Chunk列表")
    statistics: Dict[str, Any] = Field(default_factory=dict, description="切分统计信息")
    processing_time_ms: int = Field(..., description="处理耗时（毫秒）")


class ChunkStatistics(BaseModel):
    """切分统计信息"""
    total_chunks: int = Field(..., description="总Chunk数")
    avg_tokens: float = Field(..., description="平均Token数")
    min_tokens: int = Field(..., description="最小Token数")
    max_tokens: int = Field(..., description="最大Token数")
    avg_length: float = Field(..., description="平均字符长度")
    chunk_type_distribution: Dict[str, int] = Field(..., description="Chunk类型分布")
    quality_distribution: Dict[str, int] = Field(..., description="质量分布")


# ================================================
# Chunk查询相关模型
# ================================================

class ChunkListItem(BaseModel):
    """Chunk列表项模型"""
    id: int = Field(..., description="Chunk数据库ID")
    chunk_id: str = Field(..., description="Chunk唯一ID")
    chunk_index: int = Field(..., description="Chunk索引")
    chunk_type: str = Field(..., description="Chunk类型")
    content: str = Field(..., description="内容摘要（前100字符）")
    token_count: int = Field(..., description="Token数量")
    page_start: Optional[int] = Field(None, description="起始页码")
    page_end: Optional[int] = Field(None, description="结束页码")
    title_path: Optional[str] = Field(None, description="标题路径")
    quality_score: Optional[float] = Field(None, description="质量评分")
    status: int = Field(..., description="状态")
    created_at: Optional[str] = Field(None, description="创建时间")

    class Config:
        from_attributes = True


class ChunkDetailResponse(BaseModel):
    """Chunk详情响应模型"""
    id: int = Field(..., description="Chunk数据库ID")
    chunk_id: str = Field(..., description="Chunk唯一ID")
    document_id: int = Field(..., description="文档ID")
    version_id: int = Field(..., description="版本ID")
    chunk_index: int = Field(..., description="Chunk索引")
    content: str = Field(..., description="完整内容")
    enhanced_content: Optional[str] = Field(None, description="增强内容")
    content_hash: str = Field(..., description="内容Hash")
    chunk_type: str = Field(..., description="Chunk类型")
    title_path: Optional[str] = Field(None, description="标题路径")
    chapter_path: Optional[str] = Field(None, description="章节路径")
    page_start: Optional[int] = Field(None, description="起始页码")
    page_end: Optional[int] = Field(None, description="结束页码")
    token_count: int = Field(..., description="Token数量")
    char_count: int = Field(..., description="字符数量")
    element_ids: List[str] = Field(default_factory=list, description="来源元素ID列表")
    quality_score: Optional[float] = Field(None, description="质量评分")
    table_summary: Optional[str] = Field(None, description="表格摘要")
    table_schema: Optional[Dict[str, Any]] = Field(None, description="表结构")
    image_description: Optional[Dict[str, Any]] = Field(None, description="图片描述")
    is_duplicate: int = Field(..., description="是否重复")
    duplicate_of: Optional[int] = Field(None, description="重复的Chunk ID")
    status: int = Field(..., description="状态")
    vector_id: Optional[int] = Field(None, description="向量ID")
    keyword_indexed: int = Field(..., description="是否已建关键词索引")
    created_at: Optional[str] = Field(None, description="创建时间")
    updated_at: Optional[str] = Field(None, description="更新时间")

    class Config:
        from_attributes = True


# ================================================
# 批量操作相关模型
# ================================================

class BatchChunkingRequest(BaseModel):
    """批量切分请求模型"""
    document_ids: List[int] = Field(..., description="文档ID列表")
    config: Optional[ChunkConfigRequest] = Field(None, description="切分配置")


class BatchChunkingResponse(BaseModel):
    """批量切分响应模型"""
    total_documents: int = Field(..., description="总文档数")
    success_count: int = Field(..., description="成功数量")
    failed_count: int = Field(..., description="失败数量")
    total_chunks: int = Field(..., description="总生成的Chunk数")
    results: List[ChunkingResult] = Field(default_factory=list, description="各文档的切分结果")
