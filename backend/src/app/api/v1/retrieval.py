# -*- coding: utf-8 -*-
"""
检索服务路由

本模块提供检索相关接口：
- 混合检索
- 向量检索
- 关键词检索
- 查询改写
- 融合测试

注意：路由层只做参数校验和响应封装，业务逻辑在services层。
"""

import time
from typing import List, Optional

from fastapi import APIRouter, Depends, Query

from app.common.response import success_response
from app.schemas.retrieval import (
    RetrievalRequest,
    RetrievalResponse,
    FusionRequest,
    QueryRewriteRequest,
    QueryRewriteResponse,
    RetrievalStatistics,
    QueryRewriteConfig,
)
from app.services.retrieval_service import RetrievalService, get_retrieval_service
from app.services.query_rewrite_service import get_rewrite_service

router = APIRouter()


def get_retrieval_service() -> RetrievalService:
    """获取检索服务实例"""
    return RetrievalService()


@router.post("/hybrid")
async def hybrid_search(
    request: RetrievalRequest,
    service: RetrievalService = Depends(get_retrieval_service)
):
    """
    混合检索

    结合向量检索和关键词检索，返回融合后的结果。
    支持RRF融合和加权融合两种方式。
    自动进行查询改写（规范化、多查询生成）。

    Args:
        request: 检索请求参数
            - query: 查询文本
            - top_k: 返回数量
            - doc_ids: 限定文档ID列表
            - fusion_method: 融合方法（rrf/weighted/rank）
            - enable_rewrite: 是否启用查询改写

    Returns:
        检索结果列表，包含向量检索评分和关键词检索评分
    """
    results = service.hybrid_search(request)
    return success_response(data=results.model_dump())


@router.post("/vector")
async def vector_search(
    query: str = Query(..., description="查询文本"),
    top_k: int = Query(10, ge=1, le=100, description="返回数量"),
    doc_ids: Optional[List[int]] = Query(None, description="限定文档ID列表"),
    service: RetrievalService = Depends(get_retrieval_service)
):
    """
    向量检索

    基于语义相似度进行向量检索（Milvus）。

    Args:
        query: 查询文本
        top_k: 返回数量
        doc_ids: 限定的文档ID列表

    Returns:
        向量检索结果
    """
    results = service.vector_search(query, top_k, doc_ids)
    return success_response(data=results)


@router.post("/keyword")
async def keyword_search(
    query: str = Query(..., description="查询文本"),
    top_k: int = Query(10, ge=1, le=100, description="返回数量"),
    doc_ids: Optional[List[int]] = Query(None, description="限定文档ID列表"),
    service: RetrievalService = Depends(get_retrieval_service)
):
    """
    关键词检索

    基于关键词匹配进行全文检索（MySQL BM25）。

    Args:
        query: 查询文本
        top_k: 返回数量
        doc_ids: 限定的文档ID列表

    Returns:
        关键词检索结果
    """
    results = service.keyword_search(query, top_k, doc_ids)
    return success_response(data=results)


@router.get("/suggest")
async def search_suggest(
    query: str = Query(..., description="查询文本"),
    limit: int = Query(5, ge=1, le=20, description="返回数量"),
    service: RetrievalService = Depends(get_retrieval_service)
):
    """
    检索建议

    根据已有文本提供检索建议。

    Args:
        query: 查询文本
        limit: 返回数量

    Returns:
        建议列表
    """
    suggestions = service.get_suggestions(query, limit)
    return success_response(data=suggestions)


@router.post("/rewrite", response_model=QueryRewriteResponse)
async def query_rewrite(
    request: QueryRewriteRequest,
):
    """
    查询改写

    对查询进行规范化、多查询生成、子查询分解等处理。
    支持 HyDE（假设答案生成）和后退提示（宏观背景问题）。

    Args:
        request: 查询改写请求
            - query: 原始查询
            - enable_multi_query: 是否启用多查询生成
            - enable_subquery: 是否启用子查询分解
            - enable_hyde: 是否启用HyDE
            - enable_background: 是否启用后退提示

    Returns:
        查询改写结果
    """
    start_time = time.time()
    trace_id = f"rewrite_{int(time.time() * 1000)}"

    logger.info(
        "开始查询改写",
        extra={
            "traceId": trace_id,
            "method": "query_rewrite",
            "uri": "/api/v1/retrieval/rewrite",
            "query": request.query,
            "enable_multi_query": request.enable_multi_query,
            "enable_subquery": request.enable_subquery,
            "enable_hyde": request.enable_hyde,
            "enable_background": request.enable_background
        }
    )

    rewrite_service = get_rewrite_service()
    result = rewrite_service.rewrite(
        query=request.query,
        enable_multi_query=request.enable_multi_query,
        enable_subquery=request.enable_subquery,
        enable_hyde=request.enable_hyde,
        enable_background=request.enable_background,
        max_queries=request.max_queries,
    )

    # 构建详细响应
    response = QueryRewriteResponse(
        original_query=result.original_query,
        normalized_query=result.normalized_query,
        multi_queries=result.multi_queries,
        sub_queries=result.sub_queries,
        hyde_answer=result.hyde_answer,
        background_query=result.background_query,
        rewrite_time_ms=result.rewrite_time_ms,
        removed_stopwords=result.removed_stopwords,
        normalization_details={
            "original": result.normalization_details.original if result.normalization_details else None,
            "normalized": result.normalization_details.normalized if result.normalization_details else None,
            "removed_count": len(result.removed_stopwords) if result.removed_stopwords else 0
        } if result.normalization_details else None,
        multi_query_generation_time_ms=result.multi_query_details.generation_time_ms if result.multi_query_details else 0,
        subquery_generation_time_ms=result.decompose_details.generation_time_ms if result.decompose_details else 0,
        hyde_generation_time_ms=result.hyde_details.generation_time_ms if result.hyde_details else 0,
        hyde_success=result.hyde_details.success if result.hyde_details else False,
        backward_generation_time_ms=result.backward_details.generation_time_ms if result.backward_details else 0,
        backward_success=result.backward_details.success if result.backward_details else False,
    )

    logger.info(
        "查询改写完成",
        extra={
            "traceId": trace_id,
            "method": "query_rewrite",
            "uri": "/api/v1/retrieval/rewrite",
            "query": request.query,
            "rewrite_time_ms": result.rewrite_time_ms,
            "multi_query_count": len(result.multi_queries),
            "subquery_count": len(result.sub_queries),
            "hyde_success": response.hyde_success,
            "backward_success": response.backward_success
        }
    )

    return success_response(data=response.model_dump())


@router.get("/rewrite/normalize")
async def normalize_query(
    query: str = Query(..., description="查询文本"),
):
    """
    查询规范化

    仅对查询进行规范化处理（去停用词、标点归一化、统一大小写）。

    Args:
        query: 查询文本

    Returns:
        规范化结果
    """
    rewrite_service = get_rewrite_service()
    normalized = rewrite_service.normalize_only(query)

    return success_response(data={
        "original": query,
        "normalized": normalized
    })


@router.get("/rewrite/config")
async def get_rewrite_config():
    """
    获取查询改写配置

    返回当前查询改写服务的配置信息。

    Returns:
        查询改写配置
    """
    rewrite_service = get_rewrite_service()

    config = QueryRewriteConfig(
        enable_normalize=True,
        enable_multi_query=True,
        enable_subquery=True,
        enable_hyde=False,
        enable_background=False,
        use_llm=False,
        max_queries=5,
        remove_stopwords=True
    )

    return success_response(data=config.model_dump())


@router.post("/rewrite/config")
async def update_rewrite_config(
    config: QueryRewriteConfig,
):
    """
    更新查询改写配置

    更新查询改写服务的配置（内存级别，不持久化）。

    Args:
        config: 新的查询改写配置

    Returns:
        更新后的配置
    """
    from app.services.query_rewrite_service import reset_rewrite_service

    # 重置服务实例，下次获取时会使用新配置
    reset_rewrite_service()

    logger.info(
        "查询改写配置已更新",
        extra={
            "enable_normalize": config.enable_normalize,
            "enable_multi_query": config.enable_multi_query,
            "enable_subquery": config.enable_subquery,
            "enable_hyde": config.enable_hyde,
            "enable_background": config.enable_background,
            "use_llm": config.use_llm,
            "max_queries": config.max_queries
        }
    )

    return success_response(data=config.model_dump())


@router.get("/statistics", response_model=RetrievalStatistics)
async def get_statistics():
    """
    获取检索统计信息

    返回向量和关键词索引的统计信息。

    Returns:
        检索统计信息
    """
    from app.services.embedding_service import get_embedding_service
    from app.services.keyword_service import get_keyword_index_service

    try:
        embedding_service = get_embedding_service()
        keyword_service = get_keyword_index_service()

        # 获取关键词统计
        keyword_stats = keyword_service.get_statistics()

        # 获取向量统计（从Milvus获取）
        stats = RetrievalStatistics(
            total_vectors=0,  # TODO: 从Milvus获取
            total_keywords=keyword_stats.total_terms,
            avg_vector_search_time_ms=0,
            avg_keyword_search_time_ms=0,
            avg_fusion_time_ms=0,
        )

        return success_response(data=stats)

    except Exception as e:
        return success_response(data=RetrievalStatistics())


@router.post("/fusion")
async def test_fusion(
    request: FusionRequest,
):
    """
    融合测试

    测试不同融合方法的效果。

    Args:
        request: 融合请求
            - vector_results: 向量检索结果
            - keyword_results: 关键词检索结果
            - method: 融合方法（rrf/weighted/rank）
            - rrf_k: RRF参数k
            - vector_weight: 向量权重
            - keyword_weight: 关键词权重

    Returns:
        融合结果
    """
    from app.services.retrieval_service import RetrievalService
    from app.services.fusion_service import get_fusion_service

    service = RetrievalService()

    # 转换结果
    vector_items = service._convert_to_items(request.vector_results)
    keyword_items = service._convert_to_items(request.keyword_results)

    fusion_service = get_fusion_service()

    # 执行融合
    if request.method == "rrf":
        fused_items = fusion_service.rrf_fusion(
            vector_results=vector_items,
            keyword_results=keyword_items,
            k=request.rrf_k,
        )
    elif request.method == "weighted":
        fused_items = fusion_service.weighted_fusion(
            vector_results=vector_items,
            keyword_results=keyword_items,
            vector_weight=request.vector_weight,
            keyword_weight=request.keyword_weight,
        )
    else:
        fused_items = fusion_service.rank_fusion(
            vector_results=vector_items,
            keyword_results=keyword_items,
        )

    # 转换回结果格式
    fused_results = service._convert_to_results(fused_items)

    return success_response(data=fused_results)


# 添加日志导入
import logging
logger = logging.getLogger(__name__)
