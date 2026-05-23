# -*- coding: utf-8 -*-
"""
数据库连接模块

本模块提供SQLAlchemy数据库连接管理：
1. 数据库连接池配置
2. 会话管理
3. 基础模型定义

使用示例：
    from core.database import get_db, Base

    @app.get("/users")
    def get_users(db: Session = Depends(get_db)):
        return db.query(User).all()
"""

from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker, declarative_base
from sqlalchemy.pool import QueuePool

from core.config import settings

# 创建数据库引擎
engine = create_engine(
    settings.database.url,
    poolclass=QueuePool,
    pool_size=settings.database.pool_size,
    max_overflow=settings.database.max_overflow,
    pool_recycle=settings.database.pool_recycle,
    echo=settings.database.echo,
    pool_pre_ping=True,
)

# 创建会话工厂
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False
)

# 创建基类
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    获取数据库会话的依赖注入函数

    用于FastAPI的Depends注入。

    Args:
        无

    Yields:
        Session: 数据库会话对象

    示例:
        @app.get("/users")
        def get_users(db: Session = Depends(get_db)):
            return db.query(User).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_context() -> Generator[Session, None, None]:
    """
    获取数据库会话的上下文管理器

    用于非FastAPI场景（如定时任务、脚本等）。

    Yields:
        Session: 数据库会话对象

    示例:
        with get_db_context() as db:
            db.query(User).all()
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def init_db() -> None:
    """
    初始化数据库

    创建所有表结构（如果不存在）。
    """
    # 导入所有模型以确保它们被注册
    from app.models import document, chunk, qa, feedback  # noqa: F401

    # 创建所有表
    Base.metadata.create_all(bind=engine)


def close_db() -> None:
    """
    关闭数据库连接池
    """
    engine.dispose()


# 设置SQL日志（仅在调试模式启用）
if settings.database.echo:
    @event.listens_for(engine, "before_cursor_execute")
    def receive_before_cursor_execute(conn, cursor, statement, params, context, executemany):
        """记录SQL语句"""
        import logging
        logger = logging.getLogger("sql")
        logger.debug(f"SQL: {statement}")
        logger.debug(f"Params: {params}")
