# -*- coding: utf-8 -*-
"""
健康检查路由

本模块提供系统健康检查接口。
"""

from fastapi import APIRouter, Request

from app.common.response import success_response
from app.common.logging import logger
from core.config import settings

router = APIRouter()


@router.get("")
async def health_check():
    """
    健康检查接口

    检查系统各组件的连接状态。

    Returns:
        健康状态信息
    """
    return success_response(
        data={
            "status": "healthy",
            "service": settings.app.name,
            "version": settings.app.version,
            "environment": settings.app.env
        }
    )


@router.get("/db")
async def health_check_db(request: Request):
    """
    数据库健康检查

    检查MySQL数据库连接状态。

    Returns:
        数据库连接状态
    """
    from core.database import engine

    try:
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return success_response(
            data={
                "status": "connected",
                "type": "mysql"
            }
        )
    except Exception as e:
        logger.error(f"数据库连接检查失败: {str(e)}")
        return success_response(
            data={
                "status": "disconnected",
                "type": "mysql",
                "error": str(e)
            }
        )


@router.get("/redis")
async def health_check_redis():
    """
    Redis健康检查

    检查Redis缓存连接状态。

    Returns:
        Redis连接状态
    """
    from core.cache import get_redis_client

    try:
        client = get_redis_client()
        is_connected = client.is_connected()
        return success_response(
            data={
                "status": "connected" if is_connected else "disconnected",
                "type": "redis"
            }
        )
    except Exception as e:
        logger.error(f"Redis连接检查失败: {str(e)}")
        return success_response(
            data={
                "status": "disconnected",
                "type": "redis",
                "error": str(e)
            }
        )


@router.get("/milvus")
async def health_check_milvus():
    """
    Milvus健康检查

    检查Milvus向量数据库连接状态。

    Returns:
        Milvus连接状态
    """
    from core.milvus import get_milvus_client

    try:
        client = get_milvus_client()
        is_connected = client.is_connected()
        return success_response(
            data={
                "status": "connected" if is_connected else "disconnected",
                "type": "milvus"
            }
        )
    except Exception as e:
        logger.error(f"Milvus连接检查失败: {str(e)}")
        return success_response(
            data={
                "status": "disconnected",
                "type": "milvus",
                "error": str(e)
            }
        )


@router.get("/rabbitmq")
async def health_check_rabbitmq():
    """
    RabbitMQ健康检查

    检查RabbitMQ消息队列连接状态。

    Returns:
        RabbitMQ连接状态
    """
    from core.mq import get_mq_client

    try:
        client = get_mq_client()
        is_connected = client.is_connected()
        return success_response(
            data={
                "status": "connected" if is_connected else "disconnected",
                "type": "rabbitmq"
            }
        )
    except Exception as e:
        logger.error(f"RabbitMQ连接检查失败: {str(e)}")
        return success_response(
            data={
                "status": "disconnected",
                "type": "rabbitmq",
                "error": str(e)
            }
        )
