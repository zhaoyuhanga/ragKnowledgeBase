# -*- coding: utf-8 -*-
"""
文档管理路由

本模块提供文档管理相关接口：
- 单文件上传 /api/v1/documents/upload
- 批量上传 /api/v1/documents/batch-upload
- 文档列表 /api/v1/documents
- 文档详情 /api/v1/documents/{id}
- 文档删除 /api/v1/documents/{id}
- 版本列表 /api/v1/documents/{id}/versions
- 版本详情 /api/v1/documents/{id}/versions/{version_id}

注意：路由层只做参数校验和响应封装，业务逻辑在services层。
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile

from app.common.response import success_response, page_response
from app.services.document_service import DocumentService

router = APIRouter()


def get_document_service() -> DocumentService:
    """获取文档服务实例"""
    return DocumentService()


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(..., description="上传的文件"),
    business_id: Optional[str] = Form(None, description="业务归属ID"),
    business_name: Optional[str] = Form(None, description="业务归属名称"),
    creator_id: Optional[int] = Form(None, description="创建人ID"),
    creator_name: Optional[str] = Form(None, description="创建人姓名"),
    service: DocumentService = Depends(get_document_service)
):
    """
    单文件上传接口

    上传单个文档文件，自动识别文件类型并保存。
    如果文件已存在（通过Hash检测），则关联到已有版本。

    Args:
        file: 上传的文件
        business_id: 业务归属ID
        business_name: 业务归属名称
        creator_id: 创建人ID
        creator_name: 创建人姓名

    Returns:
        上传结果，包含文档ID、版本ID等信息
    """
    result = service.upload_document(
        file=file,
        business_id=business_id,
        business_name=business_name,
        creator_id=creator_id,
        creator_name=creator_name
    )
    return success_response(data=result, message=result.get("message", "上传成功"))


@router.post("/batch-upload")
async def batch_upload_documents(
    files: List[UploadFile] = File(..., description="批量上传的文件，最多20个"),
    business_id: Optional[str] = Form(None, description="业务归属ID"),
    business_name: Optional[str] = Form(None, description="业务归属名称"),
    creator_id: Optional[int] = Form(None, description="创建人ID"),
    creator_name: Optional[str] = Form(None, description="创建人姓名"),
    service: DocumentService = Depends(get_document_service)
):
    """
    批量上传接口

    批量上传多个文档文件，支持最多20个文件同时上传。
    返回每个文件的上传结果，包括成功、失败、重复等信息。

    Args:
        files: 上传的文件列表
        business_id: 业务归属ID
        business_name: 业务归属名称
        creator_id: 创建人ID
        creator_name: 创建人姓名

    Returns:
        批量上传结果，包含成功数、失败数、重复数等统计
    """
    result = service.batch_upload(
        files=files,
        business_id=business_id,
        business_name=business_name,
        creator_id=creator_id,
        creator_name=creator_name
    )
    return success_response(data=result, message="批量上传完成")


@router.get("")
async def list_documents(
    page_no: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    business_id: Optional[str] = Query(None, description="业务归属ID"),
    status: Optional[int] = Query(None, description="状态：0-待解析 1-解析中 2-已解析 3-解析失败 9-已删除"),
    keyword: Optional[str] = Query(None, description="名称关键词搜索"),
    start_date: Optional[str] = Query(None, description="创建开始日期"),
    end_date: Optional[str] = Query(None, description="创建结束日期"),
    service: DocumentService = Depends(get_document_service)
):
    """
    文档列表接口

    获取文档列表，支持分页查询和多种筛选条件。

    Args:
        page_no: 页码，默认1
        page_size: 每页数量，默认20，最大100
        business_id: 业务归属ID
        status: 状态筛选
        keyword: 名称关键词搜索
        start_date: 创建开始日期（ISO格式）
        end_date: 创建结束日期（ISO格式）

    Returns:
        分页后的文档列表
    """
    result = service.list_documents(
        page_no=page_no,
        page_size=page_size,
        business_id=business_id,
        status=status,
        keyword=keyword,
        start_date=start_date,
        end_date=end_date
    )
    return page_response(
        items=result["items"],
        total=result["total"],
        page_no=page_no,
        page_size=page_size
    )


@router.get("/{document_id}")
async def get_document(
    document_id: int,
    service: DocumentService = Depends(get_document_service)
):
    """
    文档详情接口

    根据文档ID获取文档详细信息，包括文档信息和版本列表。

    Args:
        document_id: 文档ID

    Returns:
        文档详情，包含版本列表
    """
    document = service.get_document(document_id)
    return success_response(data=document)


@router.delete("/{document_id}")
async def delete_document(
    document_id: int,
    service: DocumentService = Depends(get_document_service)
):
    """
    文档删除接口

    软删除指定文档，将文档状态标记为已删除。

    Args:
        document_id: 文档ID

    Returns:
        删除结果
    """
    service.delete_document(document_id)
    return success_response(message="删除成功")


@router.get("/{document_id}/versions")
async def list_document_versions(
    document_id: int,
    service: DocumentService = Depends(get_document_service)
):
    """
    版本列表接口

    获取指定文档的所有版本列表。

    Args:
        document_id: 文档ID

    Returns:
        版本列表
    """
    versions = service.list_versions(document_id)
    return success_response(data={"items": versions})


@router.get("/{document_id}/versions/{version_id}")
async def get_document_version(
    document_id: int,
    version_id: int,
    service: DocumentService = Depends(get_document_service)
):
    """
    版本详情接口

    获取指定版本的详细信息。

    Args:
        document_id: 文档ID
        version_id: 版本ID

    Returns:
        版本详情
    """
    version = service.get_version(document_id, version_id)
    return success_response(data=version)


@router.post("/initialize")
async def initialize_system(
    service: DocumentService = Depends(get_document_service)
):
    """
    系统初始化接口

    清空所有数据库表和向量数据库，回到初始状态。
    此操作会删除所有文档、版本、Chunk、关键词索引等数据。

    警告：这是一个危险操作，请谨慎使用！

    Returns:
        初始化结果统计
    """
    result = service.initialize_system()
    return success_response(
        data=result,
        message="系统初始化完成，所有数据已清空"
    )
