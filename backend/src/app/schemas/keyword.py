# -*- coding: utf-8 -*-
"""
关键词索引相关数据Schema

本模块定义关键词索引服务相关的数据模型。
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ================================================
# 关键词索引模型
# ================================================

class KeywordIndexRequest(BaseModel):
    """关键词索引请求模型"""
    document_id: int = Field(..., description="文档ID")
    version_id: Optional[int] = Field(None, description="版本ID")
    chunk_ids: Optional[List[int]] = Field(None, description="指定Chunk ID列表")


class KeywordIndexResult(BaseModel):
    """关键词索引结果"""
    chunk_id: int = Field(..., description="Chunk ID")
    terms: List[str] = Field(..., description="提取的关键词列表")
    indexed_count: int = Field(..., description="索引词项数量")


class KeywordIndexResponse(BaseModel):
    """关键词索引响应模型"""
    document_id: int = Field(..., description="文档ID")
    total_chunks: int = Field(..., description="处理的Chunk总数")
    indexed_chunks: int = Field(..., description="已索引Chunk数")
    total_terms: int = Field(..., description="总词项数")
    results: List[KeywordIndexResult] = Field(default_factory=list, description="索引结果")
    processing_time_ms: int = Field(..., description="处理耗时（毫秒）")


class KeywordSearchRequest(BaseModel):
    """关键词检索请求模型"""
    query: str = Field(..., description="查询文本", min_length=1)
    top_k: int = Field(default=50, description="返回结果数量", ge=1, le=200)
    document_ids: Optional[List[int]] = Field(None, description="文档ID筛选")
    chunk_types: Optional[List[str]] = Field(None, description="Chunk类型筛选")
    min_quality_score: Optional[float] = Field(None, description="最低质量评分")


class KeywordMatch(BaseModel):
    """关键词匹配结果"""
    chunk_id: int = Field(..., description="Chunk ID")
    term: str = Field(..., description="匹配的词项")
    field: str = Field(..., description="匹配的字段")
    tf: int = Field(..., description="词频")
    position: Optional[int] = Field(None, description="词项位置")
    weight: float = Field(..., description="权重")


class KeywordSearchResult(BaseModel):
    """关键词检索结果"""
    chunk_id: int = Field(..., description="Chunk ID")
    content: str = Field(..., description="Chunk内容")
    title_path: Optional[str] = Field(None, description="标题路径")
    page_start: Optional[int] = Field(None, description="起始页码")
    page_end: Optional[int] = Field(None, description="结束页码")
    score: float = Field(..., description="BM25评分")
    matches: List[KeywordMatch] = Field(default_factory=list, description="匹配详情")


class KeywordSearchResponse(BaseModel):
    """关键词检索响应模型"""
    query: str = Field(..., description="查询文本")
    top_k: int = Field(..., description="请求的TopK")
    total_results: int = Field(..., description="实际返回结果数")
    results: List[KeywordSearchResult] = Field(default_factory=list, description="检索结果")
    processing_time_ms: int = Field(..., description="处理耗时（毫秒）")


class IndexStatistics(BaseModel):
    """索引统计信息"""
    total_chunks: int = Field(..., description="已索引的Chunk总数")
    total_terms: int = Field(..., description="总词项数")
    avg_terms_per_chunk: float = Field(..., description="每Chunk平均词项数")
    field_distribution: Dict[str, int] = Field(..., description="字段分布")


class TermFrequency(BaseModel):
    """词频统计"""
    term: str = Field(..., description="词项")
    df: int = Field(..., description="文档频率")
    idf: float = Field(..., description="逆文档频率")


# ================================================
# 分词配置模型
# ================================================

class TokenizerConfig(BaseModel):
    """分词器配置模型"""
    analyzer: str = Field(default="standard", description="分词器类型：standard/ik/chinese")
    stopwords: Optional[List[str]] = Field(None, description="停用词列表")
    min_term_length: int = Field(default=2, description="最小词项长度")
    max_term_length: int = Field(default=20, description="最大词项长度")
    enable_synonym: bool = Field(default=False, description="是否启用同义词")
    enable_stemming: bool = Field(default=False, description="是否启用词干提取")
