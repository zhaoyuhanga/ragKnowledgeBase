"""
RAG 问答系统 - 文档管理 API 模块
提供文档上传、查询、删除等接口
"""

import math
from typing import Optional
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.services.document_service import document_service
from app.schemas.document import (
    DocumentUploadResponse,
    DocumentItem,
    DocumentDetailResponse,
    DocumentContentResponse,
    DocumentListResponse,
    DocumentDeleteResponse,
    ChunkItem,
)
from app.schemas.common import DataResponse, ErrorResponse
from app.core.logger import get_logger, document_logger
from app.config import settings

logger = get_logger(__name__)
router = APIRouter(prefix="/documents", tags=["文档管理"])


@router.post(
    "/upload",
    response_model=DataResponse[DocumentUploadResponse],
    summary="上传文档",
    description="上传文档并自动进行解析、切分和向量化存储。支持 PDF、Markdown、TXT、DOCX 格式。",
)
async def upload_document(
    file: UploadFile = File(..., description="要上传的文件"),
    db: Session = Depends(get_db),
):
    """
    上传并处理文档
    
    **入参说明：**
    - `file`: 上传的文档文件（必填）
    
    **出参说明：**
    - `id`: 文档 ID
    - `filename`: 文件名
    - `file_type`: 文件类型
    - `file_size`: 文件大小（字节）
    - `status`: 处理状态（0=处理中, 1=已完成, 2=失败）
    
    **返回示例：**
    ```json
    {
        "success": true,
        "message": "文档上传成功，正在处理中...",
        "code": 200,
        "data": {
            "id": 1,
            "filename": "技术文档.pdf",
            "file_type": "pdf",
            "file_size": 1024000,
            "status": 0
        }
    }
    ```
    """
    # 验证文件类型
    file_type = file.filename.split(".")[-1].lower() if "." in file.filename else ""
    if file_type not in settings.allowed_extensions_list:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件类型: {file_type}，支持的类型: {settings.allowed_extensions}"
        )
    
    # 验证文件大小
    file_content = await file.read()
    if len(file_content) > settings.max_file_size:
        raise HTTPException(
            status_code=400,
            detail=f"文件大小超过限制，最大 {settings.max_file_size / 1024 / 1024}MB"
        )
    
    # 重置文件指针
    await file.seek(0)
    
    try:
        document = await document_service.upload_document(
            file_content=file_content,
            filename=file.filename,
            db=db,
        )
        
        return DataResponse(
            success=True,
            message="文档上传成功，正在处理中...",
            data=DocumentUploadResponse(
                id=document.id,
                filename=document.filename,
                file_type=document.file_type,
                file_size=document.file_size,
                status=document.status,
            )
        )
    except ValueError as e:
        document_logger.log_upload(file.filename, len(file_content), "failed", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"文档上传失败: {str(e)}")
        document_logger.log_upload(file.filename, len(file_content), "failed", error=str(e))
        raise HTTPException(status_code=500, detail="文档上传失败")


@router.get(
    "",
    response_model=DataResponse[DocumentListResponse],
    summary="获取文档列表",
    description="分页获取文档列表，支持按状态、来源类型、LLM模型等过滤。",
)
def get_documents(
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=20, ge=1, le=100, description="每页数量"),
    status: Optional[int] = Query(default=None, description="状态过滤: 0=处理中, 1=已完成, 2=失败"),
    source_type: Optional[str] = Query(default=None, description="来源类型过滤: local(本地导入) | ai_generated(AI生成)"),
    llm_model: Optional[str] = Query(default=None, description="LLM模型过滤"),
    llm_provider: Optional[str] = Query(default=None, description="LLM提供商过滤"),
    generated_at_start: Optional[str] = Query(default=None, description="AI生成时间开始 (ISO格式)"),
    generated_at_end: Optional[str] = Query(default=None, description="AI生成时间结束 (ISO格式)"),
    question_keyword: Optional[str] = Query(default=None, description="AI生成时的原始问题关键词"),
    db: Session = Depends(get_db),
):
    """
    获取文档列表
    
    **入参说明：**
    - `page`: 页码（默认 1）
    - `page_size`: 每页数量（默认 20，最大 100）
    - `status`: 状态过滤（可选）
    - `source_type`: 来源类型过滤（可选）
    - `llm_model`: LLM模型过滤（可选）
    - `llm_provider`: LLM提供商过滤（可选）
    - `generated_at_start`: AI生成时间开始（可选）
    - `generated_at_end`: AI生成时间结束（可选）
    - `question_keyword`: 原始问题关键词（可选）
    
    **出参说明：**
    - `items`: 文档列表
    - `total`: 总记录数
    - `page`: 当前页码
    - `page_size`: 每页数量
    - `total_pages`: 总页数
    """
    from datetime import datetime
    
    skip = (page - 1) * page_size
    
    # 转换时间参数
    gen_start = None
    gen_end = None
    if generated_at_start:
        gen_start = datetime.fromisoformat(generated_at_start)
    if generated_at_end:
        gen_end = datetime.fromisoformat(generated_at_end)
    
    documents, total = document_service.get_document_list(
        db=db,
        skip=skip,
        limit=page_size,
        status=status,
        source_type=source_type,
        llm_model=llm_model,
        llm_provider=llm_provider,
        generated_at_start=gen_start,
        generated_at_end=gen_end,
        question_keyword=question_keyword,
    )
    
    return DataResponse(
        success=True,
        message="查询成功",
        data=DocumentListResponse(
            items=[
                DocumentItem(
                    id=doc.id,
                    filename=doc.filename,
                    file_type=doc.file_type,
                    file_size=doc.file_size,
                    status=doc.status,
                    chunk_count=doc.chunk_count,
                    created_at=doc.created_at,
                    updated_at=doc.updated_at,
                    source_type=doc.source_type,
                    generated_from_question=doc.generated_from_question,
                    generated_at=doc.generated_at,
                    llm_model=doc.llm_model,
                    llm_provider=doc.llm_provider,
                )
                for doc in documents
            ],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=math.ceil(total / page_size) if total > 0 else 0,
        )
    )


@router.get(
    "/{document_id}",
    response_model=DataResponse[DocumentDetailResponse],
    summary="获取文档详情",
    description="根据文档 ID 获取文档详细信息。",
)
def get_document(
    document_id: int,
    db: Session = Depends(get_db),
):
    """
    获取文档详情
    
    **入参说明：**
    - `document_id`: 文档 ID（路径参数）
    
    **出参说明：**
    - 文档详细信息（包括 AI 生成相关字段）
    """
    document = document_service.get_document(document_id, db)
    
    if not document:
        raise HTTPException(status_code=404, detail="文档不存在")
    
    return DataResponse(
        success=True,
        message="查询成功",
        data=DocumentDetailResponse(
            id=document.id,
            filename=document.filename,
            file_path=document.file_path,
            file_type=document.file_type,
            file_size=document.file_size,
            content_hash=document.content_hash,
            status=document.status,
            chunk_count=document.chunk_count,
            error_message=document.error_message,
            created_at=document.created_at,
            updated_at=document.updated_at,
            source_type=document.source_type,
            generated_from_question=document.generated_from_question,
            generated_at=document.generated_at,
            llm_model=document.llm_model,
            llm_provider=document.llm_provider,
        )
    )


@router.get(
    "/{document_id}/preview",
    response_model=DataResponse[DocumentContentResponse],
    summary="预览文档内容",
    description="获取文档的文本内容预览。",
)
def preview_document(
    document_id: int,
    db: Session = Depends(get_db),
):
    """
    预览文档内容
    
    **入参说明：**
    - `document_id`: 文档 ID（路径参数）
    
    **出参说明：**
    - `document_id`: 文档 ID
    - `filename`: 文件名
    - `content`: 文档内容（合并的文本）
    - `chunk_count`: 块数量
    """
    document = document_service.get_document(document_id, db)
    
    if not document:
        raise HTTPException(status_code=404, detail="文档不存在")
    
    content = document_service.get_document_content(document_id, db)
    chunks = document_service.get_document_chunks(document_id, db)
    
    return DataResponse(
        success=True,
        message="查询成功",
        data=DocumentContentResponse(
            document_id=document_id,
            filename=document.filename,
            content=content or "",
            chunk_count=len(chunks),
        )
    )


@router.get(
    "/{document_id}/chunks",
    response_model=DataResponse,
    summary="获取文档块列表",
    description="获取文档的所有文本块。",
)
def get_document_chunks(
    document_id: int,
    db: Session = Depends(get_db),
):
    """
    获取文档块列表
    
    **入参说明：**
    - `document_id`: 文档 ID（路径参数）
    
    **出参说明：**
    - 文档块列表
    """
    document = document_service.get_document(document_id, db)
    
    if not document:
        raise HTTPException(status_code=404, detail="文档不存在")
    
    chunks = document_service.get_document_chunks(document_id, db)
    
    return DataResponse(
        success=True,
        message="查询成功",
        data=[
            ChunkItem(
                id=chunk.id,
                document_id=chunk.document_id,
                chunk_index=chunk.chunk_index,
                content=chunk.content,
                char_count=chunk.char_count,
                vector_id=chunk.vector_id,
                created_at=chunk.created_at,
                source_type=chunk.source_type,
                generated_from_question=chunk.generated_from_question,
                generated_at=chunk.generated_at,
                llm_model=chunk.llm_model,
                llm_provider=chunk.llm_provider,
            )
            for chunk in chunks
        ]
    )


@router.delete(
    "/{document_id}",
    response_model=DataResponse[DocumentDeleteResponse],
    summary="删除文档",
    description="删除指定文档，同时删除向量数据库中的关联向量。",
)
def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
):
    """
    删除文档
    
    **入参说明：**
    - `document_id`: 文档 ID（路径参数）
    
    **出参说明：**
    - `success`: 是否成功
    - `message`: 响应消息
    - `document_id`: 删除的文档 ID
    """
    success = document_service.delete_document(document_id, db)
    
    if not success:
        raise HTTPException(status_code=404, detail="文档不存在")
    
    document_logger.log_operation("delete_document", "success", details={"document_id": document_id})
    
    return DataResponse(
        success=True,
        message="文档删除成功",
        data=DocumentDeleteResponse(
            success=True,
            message="文档删除成功",
            document_id=document_id,
        )
    )
