# -*- coding: utf-8 -*-
"""
解析服务路由

本模块提供文档解析相关接口：
- 触发文档解析 /api/v1/documents/{id}/parse
- 查询解析状态 /api/v1/documents/{id}/parse-status
- 获取解析元素 /api/v1/documents/{id}/elements
- 获取元素详情 /api/v1/documents/{id}/elements/{element_id}
- 重新解析 /api/v1/documents/{id}/reparse

注意：路由层只做参数校验和响应封装，业务逻辑在services层。
"""

from typing import Optional

from fastapi import APIRouter, Depends, Query

from app.common.response import success_response, page_response
from app.services.parse_service import get_parse_service, ParseService

router = APIRouter(tags=["文档解析"])


def get_parse_service_instance() -> ParseService:
    """获取解析服务实例"""
    return get_parse_service()


@router.post("/documents/{document_id}/parse")
async def parse_document(
    document_id: int,
    version_id: Optional[int] = Query(None, description="版本ID，不传则使用最新版本"),
    service: ParseService = Depends(get_parse_service_instance)
):
    """
    触发文档解析接口

    根据文档ID触发文档解析任务，返回解析任务信息。

    Args:
        document_id: 文档ID
        version_id: 版本ID

    Returns:
        解析任务信息
    """
    result = service.parse_document(document_id, version_id)
    return success_response(data=result, message="解析任务已创建")


@router.get("/documents/{document_id}/parse-status")
async def get_parse_status(
    document_id: int,
    service: ParseService = Depends(get_parse_service_instance)
):
    """
    查询解析状态接口

    查询文档的解析状态，包括解析进度、质量统计等。

    Args:
        document_id: 文档ID

    Returns:
        解析状态信息
    """
    result = service.get_parse_status(document_id)
    return success_response(data=result)


@router.get("/documents/{document_id}/elements")
async def get_elements(
    document_id: int,
    page_no: Optional[int] = Query(None, description="页码筛选"),
    element_type: Optional[str] = Query(None, description="元素类型筛选"),
    quality_flag: Optional[str] = Query(None, description="质量标记筛选"),
    page_index: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    service: ParseService = Depends(get_parse_service_instance)
):
    """
    获取解析元素列表接口

    获取文档的解析元素列表，支持分页和筛选。

    Args:
        document_id: 文档ID
        page_no: 页码筛选
        element_type: 元素类型筛选
        quality_flag: 质量标记筛选
        page_index: 页码
        page_size: 每页数量

    Returns:
        分页后的元素列表
    """
    # 获取所有元素（这里简化处理，实际可以优化为数据库分页）
    all_elements = service.get_elements(
        document_id=document_id,
        page_no=page_no,
        element_type=element_type,
        quality_flag=quality_flag
    )

    # 手动分页
    total = len(all_elements)
    start = (page_index - 1) * page_size
    end = start + page_size
    items = all_elements[start:end]

    return page_response(
        items=items,
        total=total,
        page_no=page_index,
        page_size=page_size
    )


@router.get("/documents/{document_id}/elements/{element_id}")
async def get_element_detail(
    document_id: int,
    element_id: str,
    service: ParseService = Depends(get_parse_service_instance)
):
    """
    获取元素详情接口

    获取指定元素的详细信息。

    Args:
        document_id: 文档ID
        element_id: 元素ID

    Returns:
        元素详情
    """
    from core.database import SessionLocal
    from app.models.parse import DocumentElement

    db = SessionLocal()
    try:
        element = db.query(DocumentElement).filter(
            DocumentElement.document_id == document_id,
            DocumentElement.element_id == element_id
        ).first()

        if not element:
            return success_response(
                data=None,
                message="元素不存在"
            )

        return success_response(data={
            "id": element.id,
            "element_id": element.element_id,
            "document_id": element.document_id,
            "version_id": element.version_id,
            "page_no": element.page_no,
            "element_type": element.element_type,
            "content": element.content,
            "enhanced_content": element.enhanced_content,
            "reading_order": element.reading_order,
            "title_level": element.title_level,
            "title_path": element.title_path,
            "bbox": element.bbox,
            "confidence": element.confidence,
            "is_merged": bool(element.is_merged),
            "table_structure": element.table_structure,
            "image_description": element.image_description,
            "metadata": element.element_metadata,
            "quality_flag": element.quality_flag,
            "created_at": element.created_at.isoformat() if element.created_at else None
        })
    finally:
        db.close()


@router.post("/documents/{document_id}/reparse")
async def reparse_document(
    document_id: int,
    service: ParseService = Depends(get_parse_service_instance)
):
    """
    重新解析文档接口

    清除旧解析结果，重新解析文档。

    Args:
        document_id: 文档ID

    Returns:
        重新解析结果
    """
    from core.database import SessionLocal
    from app.models.parse import DocumentElement

    db = SessionLocal()
    try:
        # 删除旧元素
        db.query(DocumentElement).filter(
            DocumentElement.document_id == document_id
        ).delete()
        db.commit()

        # 触发重新解析
        result = service.parse_document(document_id)
        return success_response(data=result, message="重新解析完成")
    finally:
        db.close()


@router.post("/documents/{document_id}/parse-sync")
async def parse_document_sync(
    document_id: int,
    version_id: Optional[int] = Query(None, description="版本ID，不传则使用最新版本"),
    enable_cleaning: bool = Query(True, description="是否启用清洗"),
    enable_chunking: bool = Query(True, description="是否启用切分"),
    enable_embedding: bool = Query(True, description="是否启用向量化"),
    service: ParseService = Depends(get_parse_service_instance)
):
    """
    同步解析文档接口（完整流程）

    一次性完成解析、清洗、切分和向量化，适用于Worker未运行的场景。

    Args:
        document_id: 文档ID
        version_id: 版本ID
        enable_cleaning: 是否启用清洗
        enable_chunking: 是否启用切分
        enable_embedding: 是否启用向量化

    Returns:
        完整处理结果
    """
    result = service.parse_document_sync(
        document_id=document_id,
        version_id=version_id,
        enable_cleaning=enable_cleaning,
        enable_chunking=enable_chunking,
        enable_embedding=enable_embedding
    )
    return success_response(data=result, message="同步解析完成")
