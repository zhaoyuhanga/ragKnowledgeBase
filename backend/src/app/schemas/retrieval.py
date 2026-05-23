# -*- coding: utf-8 -*-
"""
检索数据模型

本模块定义检索相关的Pydantic数据模型。
"""

from typing import List, Optional

from pydantic import BaseModel, Field


class RetrievalRequest(BaseModel):
    """检索请求模型"""
    query: str = Field(..., description="查询文本", min_length=1)
    top_k: int = Field(10, ge=1, le=100, description="返回数量")
    doc_ids: Optional[List[int]] = Field(None, description="限定文档ID列表")
    session_id: Optional[str] = Field(None, description="会话ID")
    user_id: Optional[int] = Field(None, description="用户ID")
    tenant_id: int = Field(1, description="租户ID")
    # 混合检索配置
    enable_rewrite: bool = Field(True, description="是否启用查询改写")
    fusion_method: str = Field("rank", description="融合方法：rrf/weighted/rank")
    vector_top_k: Optional[int] = Field(None, description="向量检索TopK")
    keyword_top_k: Optional[int] = Field(None, description="关键词检索TopK")
    # 过滤条件
    chunk_types: Optional[List[str]] = Field(None, description="Chunk类型筛选")
    min_quality_score: Optional[float] = Field(None, description="最低质量评分")
    active_versions_only: bool = Field(True, description="仅检索活跃版本")


class ChunkReference(BaseModel):
    """Chunk引用模型"""
    chunk_id: int = Field(..., description="Chunk ID")
    document_id: int = Field(..., description="文档ID")
    version_id: int = Field(..., description="版本ID")
    title_path: Optional[str] = Field(None, description="标题路径")
    page_start: Optional[int] = Field(None, description="起始页码")
    page_end: Optional[int] = Field(None, description="结束页码")
    content: str = Field(..., description="文本内容")
    score: float = Field(..., description="相关性评分")
    chunk_type: str = Field(..., description="块类型")


class RetrievalResult(BaseModel):
    """检索结果模型"""
    chunk: ChunkReference = Field(..., description="Chunk引用")
    vector_score: Optional[float] = Field(None, description="向量检索评分")
    keyword_score: Optional[float] = Field(None, description="关键词检索评分")
    fusion_score: Optional[float] = Field(None, description="融合评分")


class RetrievalResponse(BaseModel):
    """检索响应模型"""
    query: str = Field(..., description="查询文本")
    total: int = Field(..., description="结果总数")
    results: List[RetrievalResult] = Field(..., description="检索结果列表")
    retrieval_time_ms: int = Field(..., description="检索耗时(毫秒)")


class VectorSearchRequest(BaseModel):
    """向量检索请求模型"""
    query: str = Field(..., description="查询文本", min_length=1)
    top_k: int = Field(10, ge=1, le=100, description="返回数量")
    doc_ids: Optional[List[int]] = Field(None, description="限定文档ID列表")


class KeywordSearchRequest(BaseModel):
    """关键词检索请求模型"""
    query: str = Field(..., description="查询文本", min_length=1)
    top_k: int = Field(10, ge=1, le=100, description="返回数量")
    doc_ids: Optional[List[int]] = Field(None, description="限定文档ID列表")


class SuggestionResponse(BaseModel):
    """检索建议响应模型"""
    suggestions: List[str] = Field(..., description="建议列表")


# ================================================
# 检索融合相关模型
# ================================================

class FusionRequest(BaseModel):
    """融合请求模型"""
    vector_results: List[RetrievalResult] = Field(..., description="向量检索结果")
    keyword_results: List[RetrievalResult] = Field(..., description="关键词检索结果")
    method: str = Field("rrf", description="融合方法：rrf/weighted/rank")
    rrf_k: int = Field(60, description="RRF参数k")
    vector_weight: float = Field(0.6, description="向量权重")
    keyword_weight: float = Field(0.4, description="关键词权重")


class QueryRewriteRequest(BaseModel):
    """查询改写请求模型"""
    query: str = Field(..., description="查询文本", min_length=1)
    enable_multi_query: bool = Field(True, description="是否启用多查询生成")
    enable_subquery: bool = Field(True, description="是否启用子查询分解")
    enable_hyde: bool = Field(False, description="是否启用HyDE")
    enable_background: bool = Field(False, description="是否启用后退提示")
    max_queries: int = Field(5, description="最大生成查询数量")


class QueryRewriteResponse(BaseModel):
    """查询改写响应模型"""
    original_query: str = Field(..., description="原始查询")
    normalized_query: str = Field(..., description="规范化查询")
    multi_queries: List[str] = Field(default_factory=list, description="多查询列表")
    sub_queries: List[str] = Field(default_factory=list, description="子查询列表")
    hyde_answer: Optional[str] = Field(None, description="HyDE假设答案")
    background_query: Optional[str] = Field(None, description="后退提示查询")
    rewrite_time_ms: int = Field(0, description="改写总耗时(毫秒)")
    removed_stopwords: List[str] = Field(default_factory=list, description="被移除的停用词")
    normalization_details: Optional[dict] = Field(None, description="规范化详情")
    multi_query_generation_time_ms: int = Field(0, description="多查询生成耗时(毫秒)")
    subquery_generation_time_ms: int = Field(0, description="子查询分解耗时(毫秒)")
    hyde_generation_time_ms: int = Field(0, description="HyDE生成耗时(毫秒)")
    hyde_success: bool = Field(False, description="HyDE是否成功")
    backward_generation_time_ms: int = Field(0, description="后退提示生成耗时(毫秒)")
    backward_success: bool = Field(False, description="后退提示是否成功")


class QueryRewriteConfig(BaseModel):
    """查询改写配置模型"""
    enable_normalize: bool = Field(True, description="是否启用规范化")
    enable_multi_query: bool = Field(True, description="是否启用多查询生成")
    enable_subquery: bool = Field(True, description="是否启用子查询分解")
    enable_hyde: bool = Field(False, description="是否启用HyDE")
    enable_background: bool = Field(False, description="是否启用后退提示")
    use_llm: bool = Field(False, description="是否使用LLM增强")
    max_queries: int = Field(5, ge=1, le=10, description="最大生成查询数量")
    remove_stopwords: bool = Field(True, description="是否移除停用词")


class RetrievalStatistics(BaseModel):
    """检索统计信息"""
    total_vectors: int = Field(0, description="向量总数")
    total_keywords: int = Field(0, description="关键词索引总数")
    avg_vector_search_time_ms: float = Field(0, description="平均向量检索耗时")
    avg_keyword_search_time_ms: float = Field(0, description="平均关键词检索耗时")
    avg_fusion_time_ms: float = Field(0, description="平均融合耗时")
