"""
RAG 问答系统 - FastAPI 应用入口
主应用配置文件
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.api.v1 import api_router
from app.core.database import init_db, check_db_connection, SessionLocal
from app.core.logger import get_logger
from app.core.runtime_config import runtime_config

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理
    启动时初始化组件，关闭时清理资源
    """
    # 启动时执行
    logger.info("=" * 50)
    logger.info("RAG 问答系统启动中...")
    logger.info("=" * 50)
    
    # 初始化数据库
    try:
        init_db()
        logger.info("数据库初始化完成")
    except Exception as e:
        logger.error(f"数据库初始化失败: {str(e)}")

    # 从数据库加载运行时配置（仅包含运行时可调参数）
    try:
        db = SessionLocal()
        try:
            runtime_config.load_from_db(db)
            logger.info("运行时配置加载完成")
        finally:
            db.close()
    except Exception as e:
        logger.warning(f"运行时配置加载失败: {str(e)}")
    
    logger.info("=" * 50)
    logger.info("RAG 问答系统启动完成")
    logger.info("=" * 50)
    
    yield
    
    # 关闭时执行
    logger.info("RAG 问答系统正在关闭...")
    # 清理资源（如有需要）
    logger.info("RAG 问答系统已关闭")


# 创建 FastAPI 应用
app = FastAPI(
    title="RAG 问答系统 API",
    description="""
## RAG 问答系统

基于检索增强生成（RAG）技术的本地问答系统。

### 核心功能

- **文档管理**: 上传、解析、存储 PDF/Markdown/TXT/DOCX 文档
- **知识库构建**: 文本切分、向量化、存储到 Milvus
- **智能问答**: 基于向量检索和 LLM 生成准确回答
- **缓存管理**: Redis 缓存热点问答，降低 API 调用成本

### 技术栈

- FastAPI: 高性能 Web 框架
- MySQL 8.0: 元数据存储
- Milvus: 向量数据库
- Redis: 缓存层
- DeepSeek API: 大语言模型
- sentence-transformers: 本地 Embedding
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)


# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods_list,
    allow_headers=settings.cors_allow_headers.split(","),
)


# 请求日志中间件
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    请求日志中间件
    记录每个请求的路径、方法、耗时等信息
    """
    start_time = time.time()
    
    # 获取请求信息
    method = request.method
    path = request.url.path
    client_ip = request.client.host if request.client else "unknown"
    
    # 处理请求
    try:
        response = await call_next(request)
    except Exception as e:
        logger.error(f"请求处理异常: {method} {path} - {str(e)}")
        raise
    
    # 计算耗时
    elapsed = (time.time() - start_time) * 1000
    
    # 记录日志
    status_code = response.status_code
    log_level = "info" if status_code < 400 else "warning" if status_code < 500 else "error"
    log_func = getattr(logger, log_level)
    
    log_func(
        f"{method} {path} - {status_code} - {elapsed:.2f}ms - {client_ip}"
    )
    
    # 添加响应头
    response.headers["X-Process-Time"] = str(elapsed)
    
    return response


# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    全局异常处理器
    捕获所有未处理的异常并返回统一格式的错误响应
    """
    logger.error(f"未处理的异常: {str(exc)}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "服务器内部错误",
            "code": 500,
            "error": str(exc) if settings.debug else "Internal Server Error",
        }
    )


# 注册 API 路由
app.include_router(
    api_router,
    prefix=settings.api_v1_prefix,
)


# 根路径
@app.get("/", tags=["首页"])
async def root():
    """
    根路径
    返回系统基本信息
    """
    return {
        "name": "RAG 问答系统",
        "version": "1.0.0",
        "description": "基于检索增强生成（RAG）技术的本地问答系统",
        "docs": "/docs",
        "redoc": "/redoc",
    }


# 健康检查路径（简化版）
@app.get("/health", tags=["系统"])
async def health():
    """
    简化健康检查
    """
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
