"""
RAG 问答系统 - 系统管理 API 模块
提供健康检查、统计信息、系统配置管理等接口
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.services.knowledge_service import knowledge_service
from app.services.system_config_service import SystemConfigService
from app.core.database import check_db_connection
from app.core.vectorstore import vector_store
from app.core.cache import redis_cache
from app.core.llm import llm_client
from app.services.embedding_service import embedding_service
from app.schemas.common import HealthCheckResponse, DataResponse, StatsResponse
from app.core.logger import get_logger, system_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/system", tags=["系统管理"])


class ConfigUpdateRequest(BaseModel):
    """运行时配置更新请求"""
    retrieval_top_k: Optional[int] = None
    similarity_threshold: Optional[float] = None
    enable_mmr: Optional[bool] = None
    mmr_diversity: Optional[float] = None
    chunk_size: Optional[int] = None
    chunk_overlap: Optional[int] = None
    chunk_min_size: Optional[int] = None
    access_token_expire_minutes: Optional[int] = None


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
    mysql_ok = check_db_connection()
    redis_ok = redis_cache.check_health()
    milvus_ok = vector_store.check_health()
    llm_ok = llm_client.check_connection()
    embedding_ok = embedding_service.check_health()

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
        chromadb=False,
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
    """获取系统统计信息"""
    stats = knowledge_service.get_stats(db)

    return DataResponse(
        success=True,
        message="查询成功",
        data=stats,
    )


@router.get(
    "/config",
    summary="获取运行时配置",
    description="获取当前生效的运行时配置（来自数据库的运行时可调参数）。",
)
def get_runtime_config_summary():
    """获取运行时配置"""
    from app.core.runtime_config import runtime_config
    return {
        "success": True,
        "message": "获取成功",
        "data": runtime_config.get_all(),
    }


@router.post(
    "/config",
    summary="更新运行时配置",
    description="更新运行时配置（内存级别），支持动态修改检索、文本切分等参数。",
)
def update_runtime_config(config_req: ConfigUpdateRequest):
    """
    更新运行时配置

    **入参说明：**
    - `retrieval_top_k`: Top K 检索数 (1-50)
    - `similarity_threshold`: 相似度阈值 (0-1)
    - `enable_mmr`: 是否启用 MMR
    - `mmr_diversity`: MMR 多样性参数 (0-1)
    - `chunk_size`: 文档分块大小
    - `chunk_overlap`: 文档分块重叠
    - `chunk_min_size`: 最小块大小

    **出参说明：**
    - 更新后的配置信息
    """
    from app.core.runtime_config import runtime_config

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


# ==================== 数据库配置管理接口 ====================

class ConfigItemUpdate(BaseModel):
    """配置项更新请求"""
    value: str


@router.get(
    "/configs",
    summary="获取所有系统配置",
    description="获取数据库中存储的所有系统配置。",
)
def get_all_configs(
    group: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """获取所有系统配置"""
    service = SystemConfigService(db)

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
def update_db_config(
    config_key: str,
    update_req: ConfigItemUpdate,
    db: Session = Depends(get_db),
):
    """更新配置"""
    from app.core.runtime_config import runtime_config

    service = SystemConfigService(db)

    config = service.get_config_by_key(config_key)
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")

    if not config.editable:
        raise HTTPException(status_code=403, detail="该配置不可编辑")

    updated = service.update_config(config_key, update_req.value)
    if not updated:
        raise HTTPException(status_code=400, detail="更新失败")

    logger.info(f"Config updated: {config_key} = {update_req.value}")

    # 同步更新运行时配置
    runtime_config.update_from_db_key(config_key, updated.get_typed_value())

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
