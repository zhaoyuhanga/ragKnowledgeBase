"""
RAG 问答系统 - API 依赖注入模块
定义通用的 API 依赖项
"""

from typing import Generator

from sqlalchemy.orm import Session

from app.core.database import SessionLocal


def get_db() -> Generator[Session, None, None]:
    """
    获取数据库会话的依赖函数
    
    Yields:
        数据库会话对象
        
    Note:
        使用 FastAPI 的 Depends 注入到路由函数中
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
