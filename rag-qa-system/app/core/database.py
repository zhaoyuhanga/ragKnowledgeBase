"""
RAG 问答系统 - 数据库连接模块
MySQL 数据库连接和会话管理
"""

from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from sqlalchemy.pool import QueuePool

from app.config import settings
from app.core.logger import get_logger

logger = get_logger(__name__)

# 创建基础模型类
Base = declarative_base()

# 创建同步引擎
engine = create_engine(
    settings.mysql_url + "?charset=utf8mb4&collation=utf8mb4_unicode_ci",
    poolclass=QueuePool,
    pool_size=settings.mysql_pool_size,
    max_overflow=settings.mysql_max_overflow,
    pool_pre_ping=True,  # 连接前测试
    pool_recycle=3600,  # 一小时后回收连接
    echo=settings.debug,  # 调试模式输出 SQL
)

# 创建 pymysql 连接参数
from sqlalchemy import event

@event.listens_for(engine, "connect")
def set_pymysql_charset(dbapi_conn, connection_record):
    """设置 pymysql 连接的字符集"""
    dbapi_conn.set_character_set('utf8mb4')

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    获取数据库会话的依赖函数
    
    Yields:
        数据库会话对象
        
    Example:
        @app.get("/items")
        def get_items(db: Session = Depends(get_db)):
            return db.query(Item).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """
    获取数据库会话的上下文管理器
    
    Yields:
        数据库会话对象
        
    Example:
        with get_db_session() as db:
            db.add(document)
            db.commit()
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"数据库操作失败: {str(e)}")
        raise
    finally:
        db.close()


def init_db():
    """
    初始化数据库
    创建所有表结构
    """
    logger.info("正在初始化数据库...")
    try:
        # 导入所有模型以确保它们被注册
        from app.models import document
        
        # 创建所有表
        Base.metadata.create_all(bind=engine)
        logger.info("数据库初始化完成")
    except Exception as e:
        logger.error(f"数据库初始化失败: {str(e)}")
        raise


def drop_db():
    """
    删除所有数据库表
    警告：此操作会删除所有数据，请谨慎使用
    """
    logger.warning("正在删除所有数据库表...")
    try:
        Base.metadata.drop_all(bind=engine)
        logger.warning("数据库表删除完成")
    except Exception as e:
        logger.error(f"删除数据库表失败: {str(e)}")
        raise


def check_db_connection() -> bool:
    """
    检查数据库连接是否正常
    
    Returns:
        连接是否正常
    """
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("数据库连接正常")
        return True
    except Exception as e:
        logger.error(f"数据库连接失败: {str(e)}")
        return False
