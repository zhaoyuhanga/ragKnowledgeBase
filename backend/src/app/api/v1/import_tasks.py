# -*- coding: utf-8 -*-
"""
导入任务路由

本模块提供导入任务相关接口：
- 任务详情 /api/v1/import-tasks/{task_id}
- 任务列表 /api/v1/import-tasks

注意：路由层只做参数校验和响应封装，业务逻辑在services层。
"""

from typing import Optional

from fastapi import APIRouter, Depends, Query

from app.common.response import success_response, page_response
from app.services.document_service import ImportTaskService
from core.database import SessionLocal

router = APIRouter(prefix="/import-tasks", tags=["导入任务"])


def get_import_task_service() -> ImportTaskService:
    """获取导入任务服务实例"""
    return ImportTaskService()


@router.get("/{task_id}")
async def get_import_task(
    task_id: str,
    service: ImportTaskService = Depends(get_import_task_service)
):
    """
    任务详情接口

    根据任务ID获取导入任务的详细信息。

    Args:
        task_id: 任务ID

    Returns:
        任务详情
    """
    task = service.get_task_by_id(task_id)

    if not task:
        return success_response(
            data=None,
            message="任务不存在"
        )

    task_data = {
        "id": task.id,
        "task_id": task.task_id,
        "document_id": task.document_id,
        "version_id": task.version_id,
        "task_type": task.task_type,
        "task_status": task.task_status,
        "priority": task.priority,
        "progress": task.progress,
        "retry_count": task.retry_count,
        "max_retry": task.max_retry,
        "error_type": task.error_type,
        "error_message": task.error_message,
        "started_at": task.started_at.isoformat() if task.started_at else None,
        "completed_at": task.completed_at.isoformat() if task.completed_at else None,
        "cost_seconds": task.cost_seconds,
        "created_at": task.created_at.isoformat() if task.created_at else None
    }

    return success_response(data=task_data)


@router.get("")
async def list_import_tasks(
    page_no: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    document_id: Optional[int] = Query(None, description="文档ID"),
    task_type: Optional[str] = Query(None, description="任务类型"),
    task_status: Optional[str] = Query(None, description="任务状态")
):
    """
    任务列表接口

    获取导入任务列表，支持分页查询和多种筛选条件。

    Args:
        page_no: 页码，默认1
        page_size: 每页数量，默认20，最大100
        document_id: 文档ID筛选
        task_type: 任务类型筛选
        task_status: 任务状态筛选

    Returns:
        分页后的任务列表
    """
    db = SessionLocal()
    try:
        from app.models.document import ImportTask

        query = db.query(ImportTask)

        # 添加筛选条件
        if document_id:
            query = query.filter(ImportTask.document_id == document_id)
        if task_type:
            query = query.filter(ImportTask.task_type == task_type)
        if task_status:
            query = query.filter(ImportTask.task_status == task_status)

        # 获取总数
        total = query.count()

        # 分页查询
        offset = (page_no - 1) * page_size
        items = query.order_by(ImportTask.created_at.desc()).offset(offset).limit(page_size).all()

        # 转换为字典
        result_items = []
        for task in items:
            result_items.append({
                "id": task.id,
                "task_id": task.task_id,
                "document_id": task.document_id,
                "task_type": task.task_type,
                "task_status": task.task_status,
                "status_name": task.status_name,
                "progress": task.progress,
                "created_at": task.created_at.isoformat() if task.created_at else None
            })

        return page_response(
            items=result_items,
            total=total,
            page_no=page_no,
            page_size=page_size
        )
    finally:
        db.close()
