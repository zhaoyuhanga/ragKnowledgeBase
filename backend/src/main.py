# -*- coding: utf-8 -*-
"""
FastAPI应用入口

本模块是应用程序的入口点，负责：
1. 初始化FastAPI应用
2. 配置中间件
3. 注册路由
4. 配置Swagger文档
5. 启动应用

使用示例：
    # 开发环境启动 (在 backend 目录运行)
    uvicorn src.main:app --reload --host 127.0.0.1 --port 8011

    # 生产环境启动
    uvicorn src.main:app --host 0.0.0.0 --port 8011 --workers 4
"""

import multiprocessing
import os
import sys

# Windows multiprocessing 需要在导入任何模块之前调用
multiprocessing.freeze_support()

# 添加项目根目录到 Python 路径
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)  # backend 目录
sys.path.insert(0, project_root)

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import api_router
from app.common.logging import logger, setup_logging
from app.common.middleware import setup_middleware
from core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理

    在应用启动时初始化资源，在应用关闭时释放资源。
    """
    # 应用启动时
    logger.info(
        f"{settings.app.name} 启动中...",
        extra={
            "environment": settings.app.env,
            "version": settings.app.version
        }
    )

    # 初始化数据库
    try:
        from core.database import init_db
        init_db()
        logger.info("数据库初始化完成")
    except Exception as e:
        logger.error(f"数据库初始化失败: {str(e)}")

    # 初始化Milvus（可选，不影响主服务启动）
    try:
        from core.milvus import init_milvus
        init_milvus()
        logger.info("Milvus初始化完成")
    except Exception as e:
        logger.warning(f"Milvus初始化失败（不影响主服务）: {str(e)}")

    # 初始化RabbitMQ（可选，不影响主服务启动）
    try:
        from core.mq import init_mq
        init_mq()
        logger.info("RabbitMQ初始化完成")
    except Exception as e:
        logger.warning(f"RabbitMQ初始化失败（不影响主服务）: {str(e)}")

    # 初始化Redis（可选，不影响主服务启动）
    try:
        from core.cache import get_redis_client
        get_redis_client()
        logger.info("Redis初始化完成")
    except Exception as e:
        logger.warning(f"Redis初始化失败（不影响主服务）: {str(e)}")

    logger.info(
        f"{settings.app.name} 启动完成",
        extra={
            "host": settings.server.host,
            "port": settings.server.port
        }
    )

    yield

    # 应用关闭时
    logger.info(f"{settings.app.name} 关闭中...")

    # 关闭数据库连接
    try:
        from core.database import close_db
        close_db()
    except Exception as e:
        logger.error(f"关闭数据库连接失败: {str(e)}")

    # 关闭Milvus连接
    try:
        from core.milvus import close_milvus_client
        close_milvus_client()
    except Exception as e:
        logger.error(f"关闭Milvus连接失败: {str(e)}")

    # 关闭RabbitMQ连接
    try:
        from core.mq import close_mq_client
        close_mq_client()
    except Exception as e:
        logger.error(f"关闭RabbitMQ连接失败: {str(e)}")

    # 关闭Redis连接
    try:
        from core.cache import close_redis_client
        close_redis_client()
    except Exception as e:
        logger.error(f"关闭Redis连接失败: {str(e)}")

    logger.info(f"{settings.app.name} 已关闭")


def create_app() -> FastAPI:
    """
    创建FastAPI应用实例

    Returns:
        FastAPI应用实例
    """
    # 初始化日志
    setup_logging()

    # 创建应用实例
    app = FastAPI(
        title=settings.api.title,
        description=settings.api.description,
        version=settings.api.version,
        docs_url=settings.api.docs_url if settings.app.debug else None,
        redoc_url=settings.api.redoc_url if settings.app.debug else None,
        openapi_url="/openapi.json" if settings.app.debug else None,
        lifespan=lifespan
    )

    # 配置中间件
    setup_middleware(app)

    # 注册路由
    app.include_router(api_router, prefix=settings.api.prefix)

    return app


# 创建应用实例
app = create_app()


if __name__ == "__main__":
    import argparse
    import os
    import uvicorn

    # Windows multiprocessing 需要这个
    multiprocessing.freeze_support()

    # 确保子进程的 sys.path 正确
    script_dir = os.path.dirname(os.path.abspath(__file__))  # backend/src
    project_root = os.path.dirname(script_dir)  # backend
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    parser = argparse.ArgumentParser(description="RAG知识库系统启动器")
    parser.add_argument(
        "--mode",
        type=str,
        default="api",
        choices=["api", "worker", "all"],
        help="启动模式: api(仅API), worker(仅Worker), all(API+Worker)"
    )
    parser.add_argument(
        "--worker-type",
        type=str,
        default="all",
        help="Worker类型: all/parse/clean/chunk/embedding/index"
    )
    args = parser.parse_args()

    if args.mode in ["worker", "all"]:
        from app.services.run_worker import run_worker

        worker_process = multiprocessing.Process(
            target=run_worker,
            args=(args.worker_type,),
            name="RAG-Worker"
        )
        worker_process.start()
        print(f"[启动] Worker服务 ({args.worker_type}) - PID: {worker_process.pid}")

    if args.mode in ["api", "all"]:
        uvicorn.run(
            "main:app",
            host=settings.server.host,
            port=settings.server.port,
            reload=settings.server.reload,
            workers=settings.server.workers if not settings.server.reload else 1,
            log_level=settings.logging.level.lower()
        )
