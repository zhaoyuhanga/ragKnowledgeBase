"""
RAG 问答系统 - 服务模块
统一导出所有服务
"""

from app.services.document_service import document_service, DocumentService
from app.services.qa_service import qa_service, QAService
from app.services.knowledge_service import knowledge_service, KnowledgeService
from app.services.embedding_service import embedding_service, EmbeddingService

__all__ = [
    "document_service",
    "DocumentService",
    "qa_service",
    "QAService",
    "knowledge_service",
    "KnowledgeService",
    "embedding_service",
    "EmbeddingService",
]
