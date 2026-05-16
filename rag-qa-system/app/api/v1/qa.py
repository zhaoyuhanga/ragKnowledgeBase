"""
RAG 问答系统 - 问答 API 模块
提供问答查询、历史记录等接口
"""

import math
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.services.qa_service import qa_service
from app.services.document_service import document_service
from app.schemas.qa import (
    QAAskRequest,
    QAAskResponse,
    QAHistoryItem,
    QAHistoryResponse,
)
from app.schemas.common import DataResponse
from app.core.logger import get_logger, qa_logger
from app.config import settings

logger = get_logger(__name__)
router = APIRouter(prefix="/qa", tags=["问答"])


@router.post(
    "/ask",
    response_model=DataResponse[QAAskResponse],
    summary="提交问答请求",
    description="提交问题并获取基于知识库的回答。支持缓存和来源追溯。",
)
async def ask_question(
    request: QAAskRequest,
    db: Session = Depends(get_db),
):
    """
    提交问答请求
    
    **入参说明：**
    - `question`: 用户问题（必填，1-1000字符）
    - `session_id`: 会话 ID（可选，用于多轮对话）
    - `top_k`: 检索的文档数量（可选，默认 5）
    - `temperature`: 生成温度参数（可选，默认 0.3）
    
    **出参说明：**
    - `answer`: 系统回答
    - `sources`: 回答来源列表
    - `cache_hit`: 是否命中缓存
    - `response_time_ms`: 响应耗时（毫秒）
    
    **返回示例：**
    ```json
    {
        "success": true,
        "message": "操作成功",
        "code": 200,
        "data": {
            "answer": "RAG 是检索增强生成技术...",
            "sources": [
                {
                    "chunk_id": 1,
                    "document_id": 1,
                    "filename": "技术文档.pdf",
                    "content": "RAG（Retrieval-Augmented Generation）...",
                    "similarity": 0.85
                }
            ],
            "cache_hit": false,
            "response_time_ms": 1500
        }
    }
    ```
    """
    result = await qa_service.ask(
        question=request.question,
        db=db,
        session_id=request.session_id,
        top_k=request.top_k,
        temperature=request.temperature,
    )
    
    return DataResponse(
        success=True,
        message="问答处理完成",
        data=QAAskResponse(
            answer=result["answer"],
            sources=result["sources"],
            cache_hit=result["cache_hit"],
            response_time_ms=result["response_time_ms"],
            error=result.get("error"),
        )
    )


@router.get(
    "/history",
    response_model=DataResponse[QAHistoryResponse],
    summary="获取问答历史",
    description="分页获取问答历史记录。",
)
def get_qa_history(
    session_id: Optional[str] = Query(default=None, description="会话 ID"),
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db),
):
    """
    获取问答历史
    
    **入参说明：**
    - `session_id`: 会话 ID（可选）
    - `page`: 页码（默认 1）
    - `page_size`: 每页数量（默认 20）
    
    **出参说明：**
    - `items`: 历史记录列表
    - `total`: 总记录数
    - `page`: 当前页码
    - `page_size`: 每页数量
    - `total_pages`: 总页数
    """
    skip = (page - 1) * page_size
    
    logs, total = qa_service.get_qa_history(
        db=db,
        session_id=session_id,
        skip=skip,
        limit=page_size,
    )
    
    return DataResponse(
        success=True,
        message="查询成功",
        data=QAHistoryResponse(
            items=[
                QAHistoryItem(
                    id=log.id,
                    question=log.question,
                    answer=log.answer,
                    referenced_chunks=log.referenced_chunks,
                    response_time_ms=log.response_time_ms,
                    cache_hit=log.cache_hit,
                    session_id=log.session_id,
                    created_at=log.created_at,
                )
                for log in logs
            ],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=math.ceil(total / page_size) if total > 0 else 0,
        )
    )
