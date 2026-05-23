# -*- coding: utf-8 -*-
"""
切分接口路由

本模块提供文档切分相关的API接口：
- 文档切分执行
- Chunk查询
- 切分配置管理
"""

from typing import Optional

from fastapi import APIRouter, Query
from pydantic import BaseModel

from app.common.logging import logger
from app.common.response import success_response, error_response
from app.models.chunk import DocumentChunk
from app.models.document import Document, DocumentVersion
from app.schemas.chunk import (
    BatchChunkingRequest,
    BatchChunkingResponse,
    ChunkConfigRequest,
    ChunkDetailResponse,
    ChunkListItem,
    ChunkStatistics,
    ChunkingResult,
)
from app.services.chunk_service import get_chunk_service

router = APIRouter(prefix="/chunks", tags=["切分服务"])


# ================================================
# 文档切分接口
# ================================================

@router.post("/documents/{document_id}", response_model=BaseModel)
async def chunk_document(
    document_id: int,
    version_id: Optional[int] = None,
    config: Optional[ChunkConfigRequest] = None
):
    """
    切分文档

    对指定文档的清洗后元素进行语义切分，生成可检索的文本块。

    Args:
        document_id: 文档ID
        version_id: 版本ID（可选，默认使用最新版本）
        config: 切分配置（可选，使用默认配置）

    Returns:
        切分结果
    """
    try:
        from core.database import SessionLocal

        chunk_service = get_chunk_service()
        db = SessionLocal()

        try:
            # 获取文档信息
            document = db.query(Document).filter(
                Document.id == document_id,
                Document.is_deleted == 0
            ).first()

            if not document:
                return error_response(message=f"文档不存在，ID: {document_id}", code="BIZ_2001")

            # 获取版本信息
            if version_id:
                version = db.query(DocumentVersion).filter(
                    DocumentVersion.id == version_id,
                    DocumentVersion.document_id == document_id
                ).first()
            else:
                version = db.query(DocumentVersion).filter(
                    DocumentVersion.document_id == document_id
                ).order_by(DocumentVersion.version.desc()).first()

            if not version:
                return error_response(message="文档版本不存在", code="BIZ_2001")

            # 获取解析元素
            from app.models.parse import DocumentElement
            elements = db.query(DocumentElement).filter(
                DocumentElement.version_id == version.id
            ).order_by(DocumentElement.reading_order).all()

            if not elements:
                return error_response(message="文档没有可切分的元素", code="BIZ_2003")

            logger.info(
                f"开始切分文档",
                extra={
                    "document_id": document_id,
                    "version_id": version.id,
                    "element_count": len(elements)
                }
            )

            # 执行切分
            result = chunk_service.chunk_document(
                document_id=document_id,
                version_id=version.id,
                elements=elements,
                config=config
            )

            # 保存Chunks到数据库
            saved_ids = chunk_service.save_chunks(
                document_id=document_id,
                version_id=version.id,
                chunks=result.chunks
            )

            # 更新文档状态
            document.status = 5  # 已切分
            document.total_chunks = len(saved_ids)
            db.commit()

            logger.info(
                f"文档切分完成",
                extra={
                    "document_id": document_id,
                    "version_id": version.id,
                    "total_chunks": len(saved_ids)
                }
            )

            return success_response(
                data=result.model_dump(),
                message=f"文档切分成功，共生成 {result.total_chunks} 个Chunk"
            )

        finally:
            db.close()

    except Exception as e:
        logger.error(f"切分文档失败: {str(e)}")
        return error_response(message=f"切分文档失败: {str(e)}")


@router.post("/documents/batch", response_model=BaseModel)
async def batch_chunk_documents(request: BatchChunkingRequest):
    """
    批量切分文档

    Args:
        request: 批量切分请求

    Returns:
        批量切分结果
    """
    try:
        from core.database import SessionLocal
        from app.models.parse import DocumentElement

        chunk_service = get_chunk_service()
        db = SessionLocal()

        results = []
        success_count = 0
        failed_count = 0
        total_chunks = 0

        try:
            for document_id in request.document_ids:
                try:
                    # 获取文档
                    document = db.query(Document).filter(
                        Document.id == document_id,
                        Document.is_deleted == 0
                    ).first()

                    if not document:
                        results.append({
                            "document_id": document_id,
                            "success": False,
                            "message": "文档不存在"
                        })
                        failed_count += 1
                        continue

                    # 获取最新版本
                    version = db.query(DocumentVersion).filter(
                        DocumentVersion.document_id == document_id
                    ).order_by(DocumentVersion.version.desc()).first()

                    if not version:
                        results.append({
                            "document_id": document_id,
                            "success": False,
                            "message": "文档版本不存在"
                        })
                        failed_count += 1
                        continue

                    # 获取元素
                    elements = db.query(DocumentElement).filter(
                        DocumentElement.version_id == version.id
                    ).order_by(DocumentElement.reading_order).all()

                    # 执行切分
                    result = chunk_service.chunk_document(
                        document_id=document_id,
                        version_id=version.id,
                        elements=elements,
                        config=request.config
                    )

                    # 保存
                    saved_ids = chunk_service.save_chunks(
                        document_id=document_id,
                        version_id=version.id,
                        chunks=result.chunks
                    )

                    # 更新状态
                    document.status = 5
                    document.total_chunks = len(saved_ids)
                    db.commit()

                    results.append({
                        "document_id": document_id,
                        "success": True,
                        "total_chunks": len(saved_ids),
                        "strategy_used": result.strategy_used,
                        "processing_time_ms": result.processing_time_ms
                    })
                    success_count += 1
                    total_chunks += len(saved_ids)

                except Exception as e:
                    db.rollback()
                    results.append({
                        "document_id": document_id,
                        "success": False,
                        "message": str(e)
                    })
                    failed_count += 1

        finally:
            db.close()

        return success_response(data={
            "total_documents": len(request.document_ids),
            "success_count": success_count,
            "failed_count": failed_count,
            "total_chunks": total_chunks,
            "results": results
        }, message=f"批量切分完成，成功 {success_count} 个，失败 {failed_count} 个")

    except Exception as e:
        logger.error(f"批量切分文档失败: {str(e)}")
        return error_response(message=f"批量切分文档失败: {str(e)}")


# ================================================
# Chunk查询接口
# ================================================

@router.get("/documents/{document_id}", response_model=BaseModel)
async def list_document_chunks(
    document_id: int,
    version_id: Optional[int] = Query(None, description="版本ID"),
    chunk_type: Optional[str] = Query(None, description="Chunk类型筛选"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量")
):
    """
    获取文档的Chunk列表

    Args:
        document_id: 文档ID
        version_id: 版本ID
        chunk_type: Chunk类型筛选
        page: 页码
        page_size: 每页数量

    Returns:
        Chunk列表和统计信息
    """
    try:
        chunk_service = get_chunk_service()
        chunks, total = chunk_service.get_chunks(
            document_id=document_id,
            version_id=version_id,
            chunk_type=chunk_type,
            page=page,
            page_size=page_size
        )

        # 转换为响应模型
        items = []
        for chunk in chunks:
            items.append(ChunkListItem(
                id=chunk["id"],
                chunk_id=chunk["chunk_id"],
                chunk_index=chunk["chunk_index"],
                chunk_type=chunk["chunk_type"],
                content=chunk["content"][:100] + "..." if len(chunk["content"]) > 100 else chunk["content"],
                token_count=chunk["token_count"],
                page_start=chunk["page_start"],
                page_end=chunk["page_end"],
                title_path=chunk["title_path"],
                quality_score=chunk["quality_score"],
                status=chunk["status"],
                created_at=chunk["created_at"]
            ))

        return success_response(data={
            "items": [item.model_dump() for item in items],
            "total": total,
            "page": page,
            "page_size": page_size
        }, message="获取Chunk列表成功")

    except Exception as e:
        logger.error(f"获取Chunk列表失败: {str(e)}")
        return error_response(message=f"获取Chunk列表失败: {str(e)}")


@router.get("/{chunk_id}", response_model=BaseModel)
async def get_chunk_detail(chunk_id: int):
    """
    获取Chunk详情

    Args:
        chunk_id: Chunk数据库ID

    Returns:
        Chunk详情
    """
    try:
        chunk_service = get_chunk_service()
        chunk = chunk_service.get_chunk_by_id(chunk_id)

        if not chunk:
            return error_response(message="Chunk不存在", code="BIZ_2001")

        return success_response(data=chunk, message="获取Chunk详情成功")

    except Exception as e:
        logger.error(f"获取Chunk详情失败: {str(e)}")
        return error_response(message=f"获取Chunk详情失败: {str(e)}")


# ================================================
# 切分统计接口
# ================================================

@router.get("/documents/{document_id}/statistics", response_model=BaseModel)
async def get_chunk_statistics(document_id: int):
    """
    获取文档切分统计信息

    Args:
        document_id: 文档ID

    Returns:
        切分统计信息
    """
    try:
        from core.database import SessionLocal

        db = SessionLocal()
        try:
            # 获取所有Chunks
            chunks = db.query(DocumentChunk).filter(
                DocumentChunk.document_id == document_id,
                DocumentChunk.status != 9
            ).all()

            if not chunks:
                return error_response(message="文档没有Chunk", code="BIZ_2001")

            # 计算统计信息
            total_chunks = len(chunks)
            token_counts = [c.token_count for c in chunks]
            char_counts = [c.char_count for c in chunks]

            # 类型分布
            type_dist = {}
            for c in chunks:
                t = c.chunk_type
                type_dist[t] = type_dist.get(t, 0) + 1

            # 质量分布
            quality_dist = {"good": 0, "warning": 0, "bad": 0, "unknown": 0}
            for c in chunks:
                if c.quality_score is None:
                    quality_dist["unknown"] += 1
                elif c.quality_score >= 0.7:
                    quality_dist["good"] += 1
                elif c.quality_score >= 0.4:
                    quality_dist["warning"] += 1
                else:
                    quality_dist["bad"] += 1

            statistics = ChunkStatistics(
                total_chunks=total_chunks,
                avg_tokens=sum(token_counts) / total_chunks if total_chunks else 0,
                min_tokens=min(token_counts) if token_counts else 0,
                max_tokens=max(token_counts) if token_counts else 0,
                avg_length=sum(char_counts) / total_chunks if total_chunks else 0,
                chunk_type_distribution=type_dist,
                quality_distribution=quality_dist
            )

            return success_response(data=statistics.model_dump(), message="获取统计信息成功")

        finally:
            db.close()

    except Exception as e:
        logger.error(f"获取切分统计信息失败: {str(e)}")
        return error_response(message=f"获取切分统计信息失败: {str(e)}")
