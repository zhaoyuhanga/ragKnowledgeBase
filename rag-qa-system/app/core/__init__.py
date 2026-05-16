"""
RAG 问答系统 - 核心模块
数据库、向量存储、缓存、大模型客户端
"""

from app.core.database import Base, engine, get_db, init_db, check_db_connection
from app.core.vectorstore import vector_store, get_vector_store
from app.core.cache import redis_cache, get_redis_cache
from app.core.llm import llm_client, get_llm_client, DEFAULT_SYSTEM_PROMPT
from app.core.logger import get_logger, app_logger, document_logger, knowledge_logger, qa_logger, system_logger

__all__ = [
    # 数据库
    "Base",
    "engine", 
    "get_db",
    "init_db",
    "check_db_connection",
    # 向量存储
    "vector_store",
    "get_vector_store",
    # 缓存
    "redis_cache",
    "get_redis_cache",
    # LLM
    "llm_client",
    "get_llm_client",
    "DEFAULT_SYSTEM_PROMPT",
    # 日志
    "get_logger",
    "app_logger",
    "document_logger",
    "knowledge_logger",
    "qa_logger",
    "system_logger",
]
