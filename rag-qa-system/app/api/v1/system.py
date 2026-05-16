"""
RAG 问答系统 - 系统管理 API 模块
提供健康检查、统计信息等系统接口
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.services.document_service import document_service
from app.services.knowledge_service import knowledge_service
from app.core.database import check_db_connection
from app.core.vectorstore import vector_store
from app.core.cache import redis_cache
from app.core.llm import llm_client
from app.core.runtime_config import runtime_config
from app.services.embedding_service import embedding_service
from app.schemas.common import HealthCheckResponse, DataResponse, StatsResponse
from app.core.logger import get_logger, system_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/system", tags=["系统管理"])


class ConfigUpdateRequest(BaseModel):
    """配置更新请求"""
    retrieval_top_k: int = None
    similarity_threshold: float = None
    deepseek_model: str = None
    chunk_size: int = None
    chunk_overlap: int = None


@router.get(
    "/health",
    response_model=HealthCheckResponse,
    summary="健康检查",
    description="检查系统各组件的运行状态，包括 MySQL、Redis、ChromaDB、LLM 和 Embedding 模型。",
)
def health_check(
    db: Session = Depends(get_db),
):
    """
    健康检查
    
    **入参说明：**
    - 无
    
    **出参说明：**
    - `status`: 服务整体状态（healthy/unhealthy/degraded）
    - `mysql`: MySQL 连接状态
    - `redis`: Redis 连接状态
    - `chromadb`: ChromaDB 连接状态
    - `llm`: LLM API 连接状态
    - `embedding`: Embedding 模型状态
    - `version`: 服务版本
    
    **返回示例：**
    ```json
    {
        "status": "healthy",
        "mysql": true,
        "redis": true,
        "chromadb": true,
        "llm": true,
        "embedding": true,
        "version": "1.0.0"
    }
    ```
    """
    # 检查各组件状态
    mysql_ok = check_db_connection()
    redis_ok = redis_cache.check_health()
    chromadb_ok = vector_store.check_health()
    llm_ok = llm_client.check_connection()
    embedding_ok = embedding_service.check_health()
    
    # 计算整体状态
    critical_services = [mysql_ok, chromadb_ok, embedding_ok]
    healthy_count = sum(critical_services)
    
    if all([mysql_ok, chromadb_ok, embedding_ok]):
        status = "healthy"
    elif healthy_count >= 2:
        status = "degraded"
    else:
        status = "unhealthy"
    
    system_logger.log_operation("health_check", status, details={
        "mysql": mysql_ok,
        "redis": redis_ok,
        "chromadb": chromadb_ok,
        "llm": llm_ok,
        "embedding": embedding_ok,
    })
    
    return HealthCheckResponse(
        status=status,
        mysql=mysql_ok,
        redis=redis_ok,
        chromadb=chromadb_ok,
        llm=llm_ok,
        embedding=embedding_ok,
        version="1.0.0",
    )


@router.get(
    "/stats",
    response_model=DataResponse[StatsResponse],
    summary="系统统计信息",
    description="获取系统的统计信息，包括文档、向量、问答等数据。",
)
def get_system_stats(
    db: Session = Depends(get_db),
):
    """
    获取系统统计信息
    
    **入参说明：**
    - 无
    
    **出参说明：**
    - `documents`: 文档统计
    - `chunks`: 文档块统计
    - `vectors`: 向量统计
    - `qa`: 问答统计
    """
    stats = knowledge_service.get_stats(db)
    
    return DataResponse(
        success=True,
        message="查询成功",
        data=stats,
    )


@router.get(
    "/config",
    summary="获取系统配置",
    description="获取当前系统配置信息。",
)
def get_config():
    """
    获取系统配置
    
    **入参说明：**
    - 无
    
    **出参说明：**
    - 当前系统配置信息（敏感信息已脱敏）
    """
    from app.config import settings
    
    # 脱敏处理
    safe_config = {
        "app_env": settings.app_env,
        "app_host": settings.app_host,
        "app_port": settings.app_port,
        "debug": settings.debug,
        "mysql_host": settings.mysql_host,
        "mysql_port": settings.mysql_port,
        "mysql_database": settings.mysql_database,
        "redis_host": settings.redis_host,
        "redis_port": settings.redis_port,
        "deepseek_base_url": settings.deepseek_base_url,
        "deepseek_model": settings.deepseek_model,
        "chroma_persist_dir": settings.chroma_persist_dir,
        "chroma_collection_name": settings.chroma_collection_name,
        "embedding_model": settings.embedding_model,
        "embedding_device": settings.embedding_device,
        "chunk_size": settings.chunk_size,
        "chunk_overlap": settings.chunk_overlap,
        "retrieval_top_k": settings.retrieval_top_k,
        "similarity_threshold": settings.similarity_threshold,
        "log_level": settings.log_level,
        "allowed_extensions": settings.allowed_extensions,
        "max_file_size": settings.max_file_size,
    }
    
    return {
        "success": True,
        "message": "配置信息获取成功",
        "data": safe_config,
    }


@router.post(
    "/config",
    summary="更新系统配置",
    description="更新运行时配置，支持动态修改。",
)
def update_config(config_req: ConfigUpdateRequest):
    """
    更新运行时配置
    
    **入参说明：**
    - `retrieval_top_k`: Top K 检索数 (1-50)
    - `similarity_threshold`: 相似度阈值 (0-1)
    - `deepseek_model`: DeepSeek 模型名称
    - `chunk_size`: 文档分块大小
    - `chunk_overlap`: 文档分块重叠
    
    **出参说明：**
    - 更新后的配置信息
    """
    update_dict = config_req.model_dump(exclude_none=True)
    
    if not update_dict:
        return {
            "success": False,
            "message": "没有需要更新的配置",
            "data": None,
        }
    
    updated = runtime_config.update(update_dict)
    
    logger.info(f"Runtime config updated: {updated}")
    
    return {
        "success": True,
        "message": f"成功更新 {len(updated)} 项配置",
        "data": runtime_config.get_all(),
    }


@router.get(
    "/config/runtime",
    summary="获取运行时配置",
    description="获取当前生效的运行时配置，用于问答检索。",
)
def get_runtime_config():
    """
    获取运行时配置
    
    **出参说明：**
    - 当前生效的运行时配置
    """
    return {
        "success": True,
        "message": "运行时配置获取成功",
        "data": runtime_config.get_all(),
    }
