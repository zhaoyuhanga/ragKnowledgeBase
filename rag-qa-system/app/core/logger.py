"""
RAG 问答系统 - 日志模块
统一日志配置，支持控制台和文件输出
"""

import sys
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

from loguru import logger

from app.config import settings


class LogManager:
    """
    日志管理器
    统一管理应用日志，支持多输出目标
    """
    
    _instance: Optional["LogManager"] = None
    _initialized: bool = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if LogManager._initialized:
            return
        self._setup_logging()
        LogManager._initialized = True
    
    def _setup_logging(self):
        """
        配置日志系统
        
        日志记录级别：
        - DEBUG: 详细调试信息
        - INFO: 一般信息
        - WARNING: 警告信息
        - ERROR: 错误信息
        - CRITICAL: 严重错误
        """
        # 移除默认的 handler
        logger.remove()
        
        # 设置日志级别
        log_level = settings.log_level.upper()
        
        # 配置控制台输出（处理 Windows 编码问题）
        if settings.log_console:
            logger.add(
                sys.stdout,
                level=log_level,
                format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | <level>{message}</level>",
                colorize=True,
                backtrace=True,
                diagnose=True,
                enqueue=True  # 多线程安全，避免编码问题
            )
        
        # 配置文件输出
        log_file_path = Path(settings.log_file_path)
        log_file_path.parent.mkdir(parents=True, exist_ok=True)
        
        if settings.log_format == "json":
            logger.add(
                settings.log_file_path,
                level=log_level,
                format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}",
                rotation=settings.log_file_max_size,
                retention=settings.log_file_backup_count,
                compression="zip",
                serialize=True  # JSON 格式
            )
        else:
            logger.add(
                settings.log_file_path,
                level=log_level,
                format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
                rotation=settings.log_file_max_size,
                retention=settings.log_file_backup_count,
                compression="zip"
            )
    
    def get_logger(self, name: str = None):
        """
        获取日志记录器
        
        Args:
            name: 日志记录器名称，通常使用模块名
            
        Returns:
            配置好的 logger 实例
        """
        if name:
            return logger.bind(name=name)
        return logger


# 全局日志管理器
log_manager = LogManager()


def get_logger(name: str = None) -> logger:
    """
    获取日志记录器的便捷函数
    
    Args:
        name: 日志记录器名称
        
    Returns:
        配置好的 logger 实例
        
    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("这是一条信息日志")
        >>> logger.error("这是一条错误日志", exc_info=True)
    """
    return log_manager.get_logger(name)


# 便捷的模块级日志记录器
app_logger = get_logger("app")


class OperationLogger:
    """
    操作日志记录器
    用于记录业务操作，便于审计和分析
    """
    
    def __init__(self, module: str):
        """
        初始化操作日志记录器
        
        Args:
            module: 模块名称，如 "document", "qa", "knowledge"
        """
        self.module = module
        self.logger = get_logger(f"app.{module}")
    
    def log_operation(
        self,
        operation: str,
        status: str,
        details: dict = None,
        user_id: str = None,
        duration_ms: float = None
    ):
        """
        记录操作日志
        
        Args:
            operation: 操作名称
            status: 操作状态 (success/failed/start/end)
            details: 操作详情（字典）
            user_id: 用户 ID
            duration_ms: 操作耗时（毫秒）
        """
        log_data = {
            "module": self.module,
            "operation": operation,
            "status": status,
            "timestamp": datetime.now().isoformat(),
        }
        
        if details:
            log_data["details"] = details
        if user_id:
            log_data["user_id"] = user_id
        if duration_ms is not None:
            log_data["duration_ms"] = duration_ms
        
        if status == "success":
            self.logger.info(f"操作成功: {operation}", extra=log_data)
        elif status == "failed":
            self.logger.error(f"操作失败: {operation}", extra=log_data)
        elif status == "start":
            self.logger.debug(f"操作开始: {operation}", extra=log_data)
        elif status == "end":
            self.logger.debug(f"操作结束: {operation}", extra=log_data)
        else:
            self.logger.info(f"操作状态: {operation} - {status}", extra=log_data)
    
    def log_upload(self, filename: str, file_size: int, status: str, error: str = None, duration_ms: float = None):
        """记录文件上传操作"""
        self.log_operation(
            operation="document_upload",
            status=status,
            details={
                "filename": filename,
                "file_size": file_size,
                "error": error
            },
            duration_ms=duration_ms
        )
    
    def log_indexing(self, document_id: int, chunk_count: int, status: str, error: str = None, duration_ms: float = None):
        """记录文档索引操作"""
        self.log_operation(
            operation="document_indexing",
            status=status,
            details={
                "document_id": document_id,
                "chunk_count": chunk_count,
                "error": error
            },
            duration_ms=duration_ms
        )
    
    def log_query(self, question: str, answer_length: int, sources_count: int, 
                  cache_hit: bool, status: str, duration_ms: float):
        """记录问答查询操作"""
        # 脱敏处理，避免记录完整问题
        question_preview = question[:50] + "..." if len(question) > 50 else question
        self.log_operation(
            operation="qa_query",
            status=status,
            details={
                "question_preview": question_preview,
                "answer_length": answer_length,
                "sources_count": sources_count,
                "cache_hit": cache_hit
            },
            duration_ms=duration_ms
        )


# 预创建各模块的操作日志记录器
document_logger = OperationLogger("document")
knowledge_logger = OperationLogger("knowledge")
qa_logger = OperationLogger("qa")
system_logger = OperationLogger("system")
