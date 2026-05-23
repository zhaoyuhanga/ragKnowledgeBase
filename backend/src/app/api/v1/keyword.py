# -*- coding: utf-8 -*-
"""
关键词索引接口路由

本模块提供关键词索引相关的API接口：
- 索引构建
- 关键词检索
- 索引统计
"""

from typing import Optional

from fastapi import APIRouter, Query
from pydantic import BaseModel

from app.common.logging import logger
from app.common.response import success_response, error_response
from app.schemas.keyword import KeywordSearchRequest
from app.services.keyword_service import get_keyword_index_service

router = APIRouter(prefix="/keyword", tags=["关键词索引服务"])


# ================================================
# 索引构建接口
# ================================================

@router.post("/index/{document_id}", response_model=BaseModel)
async def build_keyword_index(
    document_id: int,
    version_id: Optional[int] = None
):
    """
    构建关键词索引

    对文档的Chunks进行分词并构建倒排索引。

    Args:
        document_id: 文档ID
        version_id: 版本ID

    Returns:
        索引构建结果
    """
    try:
        service = get_keyword_index_service()
        result = service.build_index(
            document_id=document_id,
            version_id=version_id
        )

        return success_response(
            data=result,
            message=f"关键词索引构建成功，共索引 {result.indexed_chunks} 个Chunk，{result.total_terms} 个词项"
        )

    except Exception as e:
        logger.error(f"构建关键词索引失败: {str(e)}")
        return error_response(message=f"构建关键词索引失败: {str(e)}")


@router.post("/index/batch", response_model=BaseModel)
async def batch_build_keyword_index(document_ids: list[int]):
    """
    批量构建关键词索引

    Args:
        document_ids: 文档ID列表

    Returns:
        批量构建结果
    """
    try:
        service = get_keyword_index_service()

        total_chunks = 0
        total_terms = 0
        success_count = 0
        failed_count = 0
        results = []

        for doc_id in document_ids:
            try:
                result = service.build_index(document_id=doc_id)
                total_chunks += result.indexed_chunks
                total_terms += result.total_terms
                success_count += 1
                results.append({
                    "document_id": doc_id,
                    "success": True,
                    "indexed_chunks": result.indexed_chunks,
                    "total_terms": result.total_terms
                })
            except Exception as e:
                failed_count += 1
                results.append({
                    "document_id": doc_id,
                    "success": False,
                    "error": str(e)
                })

        return success_response(data={
            "total_documents": len(document_ids),
            "success_count": success_count,
            "failed_count": failed_count,
            "total_chunks": total_chunks,
            "total_terms": total_terms,
            "results": results
        }, message=f"批量索引构建完成，成功 {success_count} 个，失败 {failed_count} 个")

    except Exception as e:
        logger.error(f"批量构建关键词索引失败: {str(e)}")
        return error_response(message=f"批量构建关键词索引失败: {str(e)}")


# ================================================
# 关键词检索接口
# ================================================

@router.post("/search", response_model=BaseModel)
async def search_by_keyword(
    query: str,
    top_k: int = Query(default=50, ge=1, le=200, description="返回结果数量"),
    document_ids: Optional[str] = Query(default=None, description="文档ID列表，逗号分隔"),
    chunk_types: Optional[str] = Query(default=None, description="Chunk类型列表，逗号分隔")
):
    """
    关键词检索

    根据关键词检索匹配的Chunks。

    Args:
        query: 查询文本
        top_k: 返回结果数量
        document_ids: 文档ID筛选
        chunk_types: Chunk类型筛选

    Returns:
        检索结果
    """
    try:
        # 解析参数
        doc_ids = None
        if document_ids:
            doc_ids = [int(x.strip()) for x in document_ids.split(",") if x.strip()]

        types_list = None
        if chunk_types:
            types_list = [x.strip() for x in chunk_types.split(",") if x.strip()]

        # 构建请求
        request = KeywordSearchRequest(
            query=query,
            top_k=top_k,
            document_ids=doc_ids,
            chunk_types=types_list
        )

        # 执行检索
        service = get_keyword_index_service()
        result = service.search(request)

        return success_response(data=result, message=f"检索成功，返回 {result.total_results} 条结果")

    except Exception as e:
        logger.error(f"关键词检索失败: {str(e)}")
        return error_response(message=f"关键词检索失败: {str(e)}")


# ================================================
# 索引统计接口
# ================================================

@router.get("/statistics", response_model=BaseModel)
async def get_index_statistics():
    """
    获取索引统计信息

    Returns:
        统计信息
    """
    try:
        service = get_keyword_index_service()
        stats = service.get_statistics()

        return success_response(data=stats, message="获取统计信息成功")

    except Exception as e:
        logger.error(f"获取索引统计失败: {str(e)}")
        return error_response(message=f"获取索引统计失败: {str(e)}")
