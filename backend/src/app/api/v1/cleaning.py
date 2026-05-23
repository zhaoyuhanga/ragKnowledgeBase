# -*- coding: utf-8 -*-
"""
清洗接口路由

本模块提供文档清洗相关的API接口：
- 清洗规则管理（CRUD）
- 文档清洗执行
- 清洗日志查询
"""

from typing import Optional

from fastapi import APIRouter, Query
from pydantic import BaseModel

from app.common.logging import logger
from app.common.response import success_response, error_response
from app.models.document import Document, DocumentVersion
from app.models.parse import DocumentElement
from app.schemas.cleaning import (
    BatchCleaningRequest,
    CleaningConfig,
    CleaningLogResponse,
    CleaningResult,
    CleaningRuleCreate,
    CleaningRuleResponse,
    CleaningRuleUpdate,
)
from app.services.clean_service import get_clean_service

router = APIRouter(prefix="/cleaning", tags=["清洗服务"])


# ================================================
# 清洗规则管理接口
# ================================================

@router.post("/rules", response_model=BaseModel)
async def create_cleaning_rule(rule_data: CleaningRuleCreate):
    """
    创建清洗规则

    Args:
        rule_data: 规则创建数据

    Returns:
        创建的规则信息
    """
    try:
        service = get_clean_service()
        rule = service.create_rule(rule_data)
        return success_response(data=rule.model_dump(), message="清洗规则创建成功")
    except Exception as e:
        logger.error(f"创建清洗规则失败: {str(e)}")
        return error_response(message=f"创建清洗规则失败: {str(e)}")


@router.put("/rules/{rule_id}", response_model=BaseModel)
async def update_cleaning_rule(rule_id: int, rule_data: CleaningRuleUpdate):
    """
    更新清洗规则

    Args:
        rule_id: 规则ID
        rule_data: 规则更新数据

    Returns:
        更新的规则信息
    """
    try:
        service = get_clean_service()
        rule = service.update_rule(rule_id, rule_data)
        return success_response(data=rule.model_dump(), message="清洗规则更新成功")
    except Exception as e:
        logger.error(f"更新清洗规则失败: {str(e)}")
        return error_response(message=f"更新清洗规则失败: {str(e)}")


@router.delete("/rules/{rule_id}", response_model=BaseModel)
async def delete_cleaning_rule(rule_id: int):
    """
    删除清洗规则

    Args:
        rule_id: 规则ID

    Returns:
        删除结果
    """
    try:
        service = get_clean_service()
        service.delete_rule(rule_id)
        return success_response(message="清洗规则删除成功")
    except Exception as e:
        logger.error(f"删除清洗规则失败: {str(e)}")
        return error_response(message=f"删除清洗规则失败: {str(e)}")


@router.get("/rules", response_model=BaseModel)
async def list_cleaning_rules(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    scope: Optional[str] = Query(None, description="适用范围筛选"),
    rule_type: Optional[str] = Query(None, description="规则类型筛选"),
    enabled_only: bool = Query(False, description="是否只返回启用的规则")
):
    """
    获取清洗规则列表

    Args:
        page: 页码
        page_size: 每页数量
        scope: 适用范围筛选
        rule_type: 规则类型筛选
        enabled_only: 是否只返回启用的规则

    Returns:
        规则列表和总数
    """
    try:
        service = get_clean_service()
        rules, total = service.list_rules(
            page=page,
            page_size=page_size,
            scope=scope,
            rule_type=rule_type,
            enabled_only=enabled_only
        )
        return success_response(data={
            "items": [r.model_dump() for r in rules],
            "total": total,
            "page": page,
            "page_size": page_size
        }, message="获取清洗规则列表成功")
    except Exception as e:
        logger.error(f"获取清洗规则列表失败: {str(e)}")
        return error_response(message=f"获取清洗规则列表失败: {str(e)}")


@router.get("/rules/{rule_id}", response_model=BaseModel)
async def get_cleaning_rule(rule_id: int):
    """
    获取清洗规则详情

    Args:
        rule_id: 规则ID

    Returns:
        规则详情
    """
    try:
        service = get_clean_service()
        rules, _ = service.list_rules(page=1, page_size=1)
        for rule in rules:
            if rule.id == rule_id:
                return success_response(data=rule.model_dump(), message="获取清洗规则详情成功")
        return error_response(message="清洗规则不存在", code="BIZ_2001")
    except Exception as e:
        logger.error(f"获取清洗规则详情失败: {str(e)}")
        return error_response(message=f"获取清洗规则详情失败: {str(e)}")


# ================================================
# 文档清洗接口
# ================================================

@router.post("/documents/{document_id}", response_model=BaseModel)
async def clean_document(
    document_id: int,
    version_id: Optional[int] = None,
    config: Optional[CleaningConfig] = None
):
    """
    清洗文档

    对指定文档的解析元素进行清洗处理，包括编码修复、噪声过滤、重复检测、脱敏和质量评分。

    Args:
        document_id: 文档ID
        version_id: 版本ID（可选，默认使用最新版本）
        config: 清洗配置（可选，使用默认配置）

    Returns:
        清洗结果
    """
    try:
        from core.database import SessionLocal

        service = get_clean_service()
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
            elements = db.query(DocumentElement).filter(
                DocumentElement.version_id == version.id
            ).order_by(DocumentElement.reading_order).all()

            if not elements:
                return error_response(message="文档没有可清洗的元素", code="BIZ_2003")

            logger.info(
                f"开始清洗文档",
                extra={
                    "document_id": document_id,
                    "version_id": version.id,
                    "element_count": len(elements)
                }
            )

            # 执行清洗
            result = service.clean_document(
                document_id=document_id,
                version_id=version.id,
                elements=elements,
                config=config
            )

            # 更新文档状态
            document.status = 4  # 已清洗
            db.commit()

            return success_response(
                data=result.model_dump(),
                message=f"文档清洗成功，共处理 {result.total_elements} 个元素"
            )

        finally:
            db.close()

    except Exception as e:
        logger.error(f"清洗文档失败: {str(e)}")
        return error_response(message=f"清洗文档失败: {str(e)}")


@router.post("/documents/batch", response_model=BaseModel)
async def batch_clean_documents(request: BatchCleaningRequest):
    """
    批量清洗文档

    Args:
        request: 批量清洗请求

    Returns:
        批量清洗结果
    """
    try:
        from core.database import SessionLocal

        service = get_clean_service()
        db = SessionLocal()

        results = []
        success_count = 0
        failed_count = 0

        try:
            for document_id in request.document_ids:
                try:
                    # 获取文档和版本
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
                    ).all()

                    # 执行清洗
                    result = service.clean_document(
                        document_id=document_id,
                        version_id=version.id,
                        elements=elements,
                        config=request.config
                    )

                    # 更新状态
                    document.status = 4
                    db.commit()

                    results.append({
                        "document_id": document_id,
                        "success": True,
                        "total_elements": result.total_elements,
                        "processing_time_ms": result.processing_time_ms
                    })
                    success_count += 1

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
            "total": len(request.document_ids),
            "success_count": success_count,
            "failed_count": failed_count,
            "results": results
        }, message=f"批量清洗完成，成功 {success_count} 个，失败 {failed_count} 个")

    except Exception as e:
        logger.error(f"批量清洗文档失败: {str(e)}")
        return error_response(message=f"批量清洗文档失败: {str(e)}")


# ================================================
# 清洗日志接口
# ================================================

@router.get("/logs", response_model=BaseModel)
async def list_cleaning_logs(
    document_id: int = Query(..., description="文档ID"),
    version_id: Optional[int] = Query(None, description="版本ID"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量")
):
    """
    获取清洗日志列表

    Args:
        document_id: 文档ID
        version_id: 版本ID
        page: 页码
        page_size: 每页数量

    Returns:
        清洗日志列表
    """
    try:
        from app.models.cleaning import CleaningLog
        from core.database import SessionLocal

        db = SessionLocal()
        try:
            query = db.query(CleaningLog).filter(
                CleaningLog.document_id == document_id
            )

            if version_id:
                query = query.filter(CleaningLog.version_id == version_id)

            total = query.count()
            logs = query.order_by(
                CleaningLog.created_at.desc()
            ).offset((page - 1) * page_size).limit(page_size).all()

            items = []
            for log in logs:
                items.append(CleaningLogResponse(
                    id=log.id,
                    document_id=log.document_id,
                    version_id=log.version_id,
                    element_id=log.element_id,
                    rule_id=log.rule_id,
                    rule_name=log.rule_name,
                    rule_type=log.rule_type,
                    action=log.action,
                    before_content=log.before_content,
                    after_content=log.after_content,
                    hit_count=log.hit_count,
                    created_at=log.created_at.isoformat() if log.created_at else None
                ))

            return success_response(data={
                "items": [item.model_dump() for item in items],
                "total": total,
                "page": page,
                "page_size": page_size
            }, message="获取清洗日志列表成功")

        finally:
            db.close()

    except Exception as e:
        logger.error(f"获取清洗日志列表失败: {str(e)}")
        return error_response(message=f"获取清洗日志列表失败: {str(e)}")
