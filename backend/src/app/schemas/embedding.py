# -*- coding: utf-8 -*-
"""
向量化相关数据Schema

本模块定义向量化服务相关的数据模型：
- 向量请求/响应模型
- Embedding配置模型
- 向量检索结果模型
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


# ================================================
# 向量化配置模型
# ================================================

class EmbeddingConfigRequest(BaseModel):
    """向量化配置请求模型"""
    model_config = ConfigDict(protected_namespaces=())
    
    model_name: str = Field(default="Qwen3-Embedding", description="模型名称")
    dimension: int = Field(default=1024, description="向量维度")
    batch_size: int = Field(default=32, description="批处理大小")
    normalize: bool = Field(default=True, description="是否归一化向量")


# ================================================
# 向量请求/响应模型
# ================================================

class EmbeddingRequest(BaseModel):
    """向量请求模型"""
    model_config = ConfigDict(protected_namespaces=())
    
    texts: List[str] = Field(..., description="待向量化的文本列表", min_length=1)
    normalize: bool = Field(default=True, description="是否归一化")
    model_name: Optional[str] = Field(None, description="指定模型名称")


class EmbeddingResponse(BaseModel):
    """向量响应模型"""
    model_config = ConfigDict(protected_namespaces=())
    
    embeddings: List[List[float]] = Field(..., description="向量列表")
    model_name: str = Field(..., description="使用的模型名称")
    dimension: int = Field(..., description="向量维度")
    count: int = Field(..., description="向量数量")
    cached_count: int = Field(default=0, description="从缓存获取的数量")


class SingleEmbeddingRequest(BaseModel):
    """单个向量请求模型"""
    model_config = ConfigDict(protected_namespaces=())
    
    text: str = Field(..., description="待向量化的文本", min_length=1)
    normalize: bool = Field(default=True, description="是否归一化")
    model_name: Optional[str] = Field(None, description="指定模型名称")


class SingleEmbeddingResponse(BaseModel):
    """单个向量响应模型"""
    model_config = ConfigDict(protected_namespaces=())
    
    embedding: List[float] = Field(..., description="向量")
    model_name: str = Field(..., description="使用的模型名称")
    dimension: int = Field(..., description="向量维度")
    cached: bool = Field(default=False, description="是否从缓存获取")


# ================================================
# Chunk向量化相关模型
# ================================================

class ChunkEmbeddingRequest(BaseModel):
    """Chunk向量化请求模型"""
    document_id: int = Field(..., description="文档ID")
    version_id: Optional[int] = Field(None, description="版本ID")
    chunk_ids: Optional[List[int]] = Field(None, description="指定Chunk ID列表，为空则处理全部")
    use_cache: bool = Field(default=True, description="是否使用缓存")


class ChunkEmbeddingResult(BaseModel):
    """单个Chunk向量化结果"""
    chunk_id: int = Field(..., description="Chunk数据库ID")
    vector_id: int = Field(..., description="向量ID")
    embedding: List[float] = Field(..., description="向量")
    cached: bool = Field(default=False, description="是否从缓存获取")


class ChunkEmbeddingResponse(BaseModel):
    """Chunk向量化响应模型"""
    document_id: int = Field(..., description="文档ID")
    version_id: int = Field(..., description="版本ID")
    total_chunks: int = Field(..., description="总Chunk数")
    processed_chunks: int = Field(..., description="已处理数")
    cached_count: int = Field(..., description="缓存命中数")
    results: List[ChunkEmbeddingResult] = Field(default_factory=list, description="向量化结果")
    processing_time_ms: int = Field(..., description="处理耗时（毫秒）")


# ================================================
# 向量检索相关模型
# ================================================

class VectorSearchRequest(BaseModel):
    """向量检索请求模型"""
    query: str = Field(..., description="查询文本", min_length=1)
    top_k: int = Field(default=10, description="返回结果数量", ge=1, le=100)
    document_ids: Optional[List[int]] = Field(None, description="文档ID筛选")
    chunk_types: Optional[List[str]] = Field(None, description="Chunk类型筛选")
    min_quality_score: Optional[float] = Field(None, description="最低质量评分", ge=0.0, le=1.0)
    filter_expr: Optional[str] = Field(None, description="Milvus过滤表达式")


class VectorSearchResult(BaseModel):
    """单个向量检索结果"""
    chunk_id: int = Field(..., description="Chunk ID")
    vector_id: int = Field(..., description="向量ID")
    distance: float = Field(..., description="向量距离/相似度")
    content: str = Field(..., description="Chunk内容")
    title_path: Optional[str] = Field(None, description="标题路径")
    page_start: Optional[int] = Field(None, description="起始页码")
    page_end: Optional[int] = Field(None, description="结束页码")
    chunk_type: str = Field(..., description="Chunk类型")
    quality_score: Optional[float] = Field(None, description="质量评分")


class VectorSearchResponse(BaseModel):
    """向量检索响应模型"""
    query: str = Field(..., description="查询文本")
    top_k: int = Field(..., description="请求的TopK")
    total_results: int = Field(..., description="实际返回结果数")
    results: List[VectorSearchResult] = Field(default_factory=list, description="检索结果")
    query_embedding_cached: bool = Field(default=False, description="查询向量是否从缓存获取")
    processing_time_ms: int = Field(..., description="处理耗时（毫秒）")


# ================================================
# 批量操作相关模型
# ================================================

class BatchEmbeddingRequest(BaseModel):
    """批量向量化请求模型"""
    chunks: List[Dict[str, Any]] = Field(..., description="Chunk列表")
    normalize: bool = Field(default=True, description="是否归一化")


class BatchEmbeddingResponse(BaseModel):
    """批量向量化响应模型"""
    total: int = Field(..., description="总数")
    success: int = Field(..., description="成功数")
    failed: int = Field(..., description="失败数")
    cached_count: int = Field(..., description="缓存命中数")
    embeddings: List[Dict[str, Any]] = Field(default_factory=list, description="向量结果")
    processing_time_ms: int = Field(..., description="处理耗时（毫秒）")


# ================================================
# 向量统计相关模型
# ================================================

class VectorStatistics(BaseModel):
    """向量统计信息"""
    collection_name: str = Field(..., description="集合名称")
    total_vectors: int = Field(..., description="总向量数")
    indexed_vectors: int = Field(..., description="已建索引向量数")
    dimension: int = Field(..., description="向量维度")
    index_type: str = Field(..., description="索引类型")
    metric_type: str = Field(..., description="距离度量类型")
    cache_size: int = Field(default=0, description="缓存条目数")
    cache_hit_rate: float = Field(default=0.0, description="缓存命中率")


class CacheStatistics(BaseModel):
    """缓存统计信息"""
    query_cache_size: int = Field(..., description="查询缓存数量")
    doc_cache_size: int = Field(..., description="文档缓存数量")
    total_size: int = Field(..., description="总缓存数量")
    hit_count: int = Field(..., description="命中次数")
    miss_count: int = Field(..., description="未命中次数")
    hit_rate: float = Field(..., description="命中率")


# ================================================
# 向量管理相关模型
# ================================================

class VectorDeleteRequest(BaseModel):
    """向量删除请求模型"""
    document_id: int = Field(..., description="文档ID")
    version_id: Optional[int] = Field(None, description="版本ID")
    chunk_ids: Optional[List[int]] = Field(None, description="指定Chunk ID列表")


class VectorDeleteResponse(BaseModel):
    """向量删除响应模型"""
    document_id: int = Field(..., description="文档ID")
    deleted_count: int = Field(..., description="删除数量")
    cache_cleared: int = Field(..., description="清除缓存数量")
    processing_time_ms: int = Field(..., description="处理耗时（毫秒）")


class VectorRebuildRequest(BaseModel):
    """向量重建请求模型"""
    document_id: int = Field(..., description="文档ID")
    version_id: Optional[int] = Field(None, description="版本ID")
    chunk_ids: Optional[List[int]] = Field(None, description="指定Chunk ID列表")
    rebuild_index: bool = Field(default=True, description="是否重建索引")


class VectorRebuildResponse(BaseModel):
    """向量重建响应模型"""
    document_id: int = Field(..., description="文档ID")
    deleted_count: int = Field(..., description="删除的旧向量数")
    created_count: int = Field(..., description="创建的新向量数")
    index_rebuilt: bool = Field(..., description="索引是否已重建")
    processing_time_ms: int = Field(..., description="处理耗时（毫秒）")
