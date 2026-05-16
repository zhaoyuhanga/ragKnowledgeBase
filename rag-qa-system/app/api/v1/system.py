"""
RAG 问答系统 - 系统管理 API 模块
提供健康检查、统计信息、系统配置管理等接口
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.services.document_service import document_service
from app.services.knowledge_service import knowledge_service
from app.services.system_config_service import SystemConfigService
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
    description="检查系统各组件的运行状态，包括 MySQL、Redis、Milvus、LLM 和 Embedding 模型。",
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
    - `milvus`: Milvus 连接状态
    - `llm`: LLM API 连接状态
    - `embedding`: Embedding 模型状态
    - `version`: 服务版本
    
    **返回示例：**
    ```json
    {
        "status": "healthy",
        "mysql": true,
        "redis": true,
        "milvus": true,
        "llm": true,
        "embedding": true,
        "version": "1.0.0"
    }
    ```
    """
    # 检查各组件状态
    mysql_ok = check_db_connection()
    redis_ok = redis_cache.check_health()
    milvus_ok = vector_store.check_health()
    llm_ok = llm_client.check_connection()
    embedding_ok = embedding_service.check_health()
    
    # 计算整体状态
    critical_services = [mysql_ok, milvus_ok, embedding_ok]
    healthy_count = sum(critical_services)
    
    if all([mysql_ok, milvus_ok, embedding_ok]):
        status = "healthy"
    elif healthy_count >= 2:
        status = "degraded"
    else:
        status = "unhealthy"
    
    system_logger.log_operation("health_check", status, details={
        "mysql": mysql_ok,
        "redis": redis_ok,
        "milvus": milvus_ok,
        "llm": llm_ok,
        "embedding": embedding_ok,
    })
    
    return HealthCheckResponse(
        status=status,
        mysql=mysql_ok,
        redis=redis_ok,
        chromadb=False,  # 已废弃，保留兼容
        milvus=milvus_ok,
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
        "milvus_host": settings.milvus_host,
        "milvus_port": settings.milvus_port,
        "milvus_collection_name": settings.milvus_collection_name,
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


# ==================== 数据库配置管理接口 ====================

class ConfigItemUpdate(BaseModel):
    """配置项更新请求"""
    value: str


class ConfigItemCreate(BaseModel):
    """配置项创建请求"""
    key: str
    value: str
    value_type: str = "string"
    group: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    editable: bool = True
    sensitive: bool = False


class ConfigBatchUpdate(BaseModel):
    """批量配置更新请求"""
    configs: dict  # {key: value}


@router.get(
    "/configs",
    summary="获取所有系统配置",
    description="获取数据库中存储的所有系统配置，支持按分组筛选。",
)
def get_all_configs(
    group: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """
    获取所有系统配置

    **入参说明：**
    - `group`: 可选，按分组筛选

    **出参说明：**
    - 配置列表
    """
    service = SystemConfigService(db)

    # 如果没有配置，初始化默认配置
    if service.get_all_configs().__len__() == 0:
        count = service.initialize_default_configs()
        logger.info(f"Initialized {count} default configs")

    if group:
        configs = service.get_configs_by_group(group)
    else:
        configs = service.get_all_configs()

    return {
        "success": True,
        "message": "获取成功",
        "data": [
            {
                "key": c.key,
                "value": c.value if not c.sensitive else ("*" * 8) if c.value else "",
                "raw_value": c.value if not c.sensitive else None,
                "value_type": c.value_type,
                "group": c.group,
                "name": c.name,
                "description": c.description,
                "editable": c.editable,
                "sensitive": c.sensitive,
            }
            for c in configs
        ],
    }


@router.get(
    "/configs/groups",
    summary="获取配置分组",
    description="获取所有配置分组及其名称。",
)
def get_config_groups(db: Session = Depends(get_db)):
    """获取所有配置分组"""
    service = SystemConfigService(db)
    groups = service.get_grouped_configs()
    # get_groups_with_names() returns List[Dict], convert to dict for lookup
    groups_name_map = {g["key"]: g["name"] for g in service.get_groups_with_names()}

    return {
        "success": True,
        "message": "获取成功",
        "data": [
            {"key": key, "name": groups_name_map.get(key, key), "count": len(configs)}
            for key, configs in groups.items()
        ],
    }


@router.get(
    "/configs/grouped",
    summary="获取分组后的配置",
    description="获取按分组组织的系统配置。",
)
def get_grouped_configs(db: Session = Depends(get_db)):
    """获取分组后的配置"""
    service = SystemConfigService(db)

    # 如果没有配置，初始化默认配置
    if service.get_all_configs().__len__() == 0:
        count = service.initialize_default_configs()
        logger.info(f"Initialized {count} default configs")

    grouped = service.get_grouped_configs()

    return {
        "success": True,
        "message": "获取成功",
        "data": grouped,
    }


@router.get(
    "/configs/{config_key}",
    summary="获取单个配置",
    description="根据键名获取配置详情。",
)
def get_config(config_key: str, db: Session = Depends(get_db)):
    """获取单个配置"""
    service = SystemConfigService(db)
    config = service.get_config_by_key(config_key)

    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")

    return {
        "success": True,
        "message": "获取成功",
        "data": {
            "key": config.key,
            "value": config.value if not config.sensitive else ("*" * 8) if config.value else "",
            "raw_value": config.value if not config.sensitive else None,
            "value_type": config.value_type,
            "group": config.group,
            "name": config.name,
            "description": config.description,
            "editable": config.editable,
            "sensitive": config.sensitive,
        },
    }


@router.put(
    "/configs/{config_key}",
    summary="更新配置",
    description="更新配置值。",
)
def update_config(
    config_key: str,
    update_req: ConfigItemUpdate,
    db: Session = Depends(get_db),
):
    """更新配置"""
    service = SystemConfigService(db)

    # 先检查配置是否存在
    config = service.get_config_by_key(config_key)
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")

    if not config.editable:
        raise HTTPException(status_code=403, detail="该配置不可编辑")

    updated = service.update_config(config_key, update_req.value)
    if not updated:
        raise HTTPException(status_code=400, detail="更新失败")

    logger.info(f"Config updated: {config_key} = {update_req.value}")

    return {
        "success": True,
        "message": "更新成功",
        "data": {
            "key": updated.key,
            "value": updated.value if not updated.sensitive else ("*" * 8) if updated.value else "",
            "raw_value": updated.value if not updated.sensitive else None,
        },
    }


@router.post(
    "/configs/batch",
    summary="批量更新配置",
    description="批量更新多个配置项。",
)
def batch_update_configs(
    batch_req: ConfigBatchUpdate,
    db: Session = Depends(get_db),
):
    """批量更新配置"""
    service = SystemConfigService(db)
    results = service.update_configs_batch(batch_req.configs)

    success_count = sum(1 for v in results.values() if v)
    logger.info(f"Batch updated {success_count}/{len(batch_req.configs)} configs")

    return {
        "success": True,
        "message": f"成功更新 {success_count}/{len(batch_req.configs)} 项配置",
        "data": results,
    }


@router.post(
    "/configs/initialize",
    summary="初始化默认配置",
    description="初始化默认配置到数据库。",
)
def initialize_configs(db: Session = Depends(get_db)):
    """初始化默认配置"""
    service = SystemConfigService(db)
    count = service.initialize_default_configs()

    logger.info(f"Initialized {count} default configs")

    return {
        "success": True,
        "message": f"成功初始化 {count} 项默认配置",
        "data": {"count": count},
    }
