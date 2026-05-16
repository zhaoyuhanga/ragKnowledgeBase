"""
RAG 问答系统 - 知识库管理 API 模块
提供知识库索引管理、统计、检索等接口
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.services.knowledge_service import knowledge_service
from app.services.qa_service import qa_service
from app.schemas.qa import (
    KnowledgeSearchRequest,
    KnowledgeSearchItem,
    KnowledgeSearchResponse,
    KnowledgeRebuildResponse,
    CacheClearResponse,
)
from app.schemas.common import DataResponse, StatsResponse
from app.core.logger import get_logger, knowledge_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/knowledge", tags=["知识库管理"])


@router.get(
    "/stats",
    response_model=DataResponse[StatsResponse],
    summary="获取知识库统计信息",
    description="获取知识库的统计信息，包括文档数量、向量数量、问答统计等。",
)
def get_knowledge_stats(
    db: Session = Depends(get_db),
):
    """
    获取知识库统计信息
    
    **入参说明：**
    - 无
    
    **出参说明：**
    - `documents`: 文档统计（total, processed, failed, processing）
    - `chunks`: 文档块统计
    - `vectors`: 向量统计
    - `qa`: 问答统计
    
    **返回示例：**
    ```json
    {
        "success": true,
        "message": "查询成功",
        "code": 200,
        "data": {
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
    ```
    """
    stats = knowledge_service.get_stats(db)
    
    return DataResponse(
        success=True,
        message="查询成功",
        data=stats
    )


@router.post(
    "/rebuild",
    response_model=DataResponse[KnowledgeRebuildResponse],
    summary="重建知识库索引",
    description="清空并重新构建整个知识库索引。请谨慎使用，此操作会清除所有向量数据。",
)
async def rebuild_knowledge_base(
    db: Session = Depends(get_db),
):
    """
    重建知识库索引
    
    **入参说明：**
    - 无
    
    **出参说明：**
    - `success`: 是否成功
    - `total_documents`: 处理的文档总数
    - `success_count`: 成功数量
    - `failed_count`: 失败数量
    - `total_chunks`: 生成的块总数
    - `duration_ms`: 耗时（毫秒）
    - `message`: 响应消息
    
    **返回示例：**
    ```json
    {
        "success": true,
        "message": "知识库重建完成",
        "code": 200,
        "data": {
            "success": true,
            "total_documents": 10,
            "success_count": 9,
            "failed_count": 1,
            "total_chunks": 450,
            "duration_ms": 30000,
            "message": "知识库重建完成"
        }
    }
    ```
    """
    knowledge_logger.log_operation("rebuild_index", "start")
    
    result = await knowledge_service.rebuild_index(db)
    
    return DataResponse(
        success=True,
        message="知识库重建完成",
        data=KnowledgeRebuildResponse(
            success=result["success"],
            total_documents=result["total_documents"],
            success_count=result["success_count"],
            failed_count=result["failed_count"],
            total_chunks=result["total_chunks"],
            duration_ms=result["duration_ms"],
            message="知识库重建完成",
        )
    )


@router.post(
    "/chunks/search",
    response_model=DataResponse[KnowledgeSearchResponse],
    summary="手动检索相关文档块",
    description="手动检索与查询最相关的文档块，用于调试和验证检索效果。",
)
def search_chunks(
    request: KnowledgeSearchRequest,
    db: Session = Depends(get_db),
):
    """
    手动检索相关文档块
    
    **入参说明：**
    - `query`: 检索查询（必填，1-500字符）
    - `top_k`: 返回结果数量（可选，默认 5）
    
    **出参说明：**
    - `query`: 原始查询
    - `results`: 检索结果列表
    - `total`: 结果数量
    
    **返回示例：**
    ```json
    {
        "success": true,
        "message": "检索完成",
        "code": 200,
        "data": {
            "query": "RAG 技术",
            "results": [
                {
                    "vector_id": "1_0_a1b2c3d4",
                    "document_id": 1,
                    "chunk_index": 0,
                    "filename": "技术文档.pdf",
                    "content": "RAG（Retrieval-Augmented Generation）...",
                    "similarity": 0.85
                }
            ],
            "total": 5
        }
    }
    ```
    """
    results = knowledge_service.search_chunks(
        query=request.query,
        db=db,
        top_k=request.top_k,
    )
    
    return DataResponse(
        success=True,
        message="检索完成",
        data=KnowledgeSearchResponse(
            query=request.query,
            results=[
                KnowledgeSearchItem(
                    vector_id=result["vector_id"],
                    document_id=result["document_id"],
                    chunk_index=result["chunk_index"],
                    filename=result["filename"],
                    content=result["content"],
                    similarity=result["similarity"],
                )
                for result in results
            ],
            total=len(results),
        )
    )


@router.delete(
    "/cache/clear",
    response_model=DataResponse[CacheClearResponse],
    summary="清空问答缓存",
    description="清空 Redis 中的所有问答缓存。",
)
def clear_qa_cache():
    """
    清空问答缓存
    
    **入参说明：**
    - 无
    
    **出参说明：**
    - `success`: 是否成功
    - `cleared_count`: 清空的缓存数量
    - `message`: 响应消息
    """
    cleared_count = qa_service.clear_cache()
    
    knowledge_logger.log_operation("clear_cache", "success", details={"cleared_count": cleared_count})
    
    return DataResponse(
        success=True,
        message="缓存清空成功",
        data=CacheClearResponse(
            success=True,
            cleared_count=cleared_count,
            message="缓存清空成功",
        )
    )
