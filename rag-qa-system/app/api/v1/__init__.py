"""
RAG 问答系统 - API v1 路由模块
包含所有 v1 版本的 API 路由
"""

from fastapi import APIRouter

from app.api.v1 import documents, qa, knowledge, system

api_router = APIRouter()

# 文档管理路由
api_router.include_router(documents.router)

# 问答路由
api_router.include_router(qa.router)

# 知识库管理路由
api_router.include_router(knowledge.router)

# 系统管理路由
api_router.include_router(system.router)
