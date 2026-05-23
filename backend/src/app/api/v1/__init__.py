# -*- coding: utf-8 -*-
"""
API v1路由模块

本模块包含v1版本的API路由注册。
"""

from fastapi import APIRouter

from app.api.v1 import documents, health, retrieval, qa, import_tasks, parse, cleaning, chunks, embedding, keyword, queue

# 创建v1主路由
api_router = APIRouter()

# 注册子路由
api_router.include_router(health.router, prefix="/health", tags=["健康检查"])
api_router.include_router(documents.router, prefix="/documents", tags=["文档管理"])
api_router.include_router(import_tasks.router, prefix="/import-tasks", tags=["导入任务"])
api_router.include_router(parse.router, prefix="", tags=["文档解析"])
api_router.include_router(retrieval.router, prefix="/retrieval", tags=["检索服务"])
api_router.include_router(qa.router, prefix="/qa", tags=["问答服务"])
api_router.include_router(cleaning.router, prefix="/cleaning", tags=["清洗服务"])
api_router.include_router(chunks.router, prefix="/chunks", tags=["切分服务"])
api_router.include_router(embedding.router, prefix="/embedding", tags=["向量化服务"])
api_router.include_router(keyword.router, prefix="/keyword", tags=["关键词索引服务"])
api_router.include_router(queue.router, prefix="/queue", tags=["队列管理"])

__all__ = ["api_router"]
