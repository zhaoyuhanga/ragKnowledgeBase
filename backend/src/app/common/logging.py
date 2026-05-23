# -*- coding: utf-8 -*-
"""
日志配置模块

本模块提供JSON格式的日志配置，满足规范要求的日志格式：
- JSON格式输出
- 包含traceId、method、uri、costMs等字段
- 支持中文消息
- 支持审计日志

日志格式：
{
    "time": "2026-05-21T12:00:00.123+08:00",
    "level": "INFO",
    "traceId": "202605211200000001",
    "userId": 1001,
    "method": "POST",
    "uri": "/api/v1/students",
    "requestParams": {},
    "responseCode": 200,
    "costMs": 156,
    "clientIp": "192.168.1.100",
    "message": "学生创建成功",
    "errorStack": null
}

使用示例：
    from app.common.logging import logger

    logger.info("用户登录成功", extra={
        "userId": 1001,
        "method": "POST",
        "uri": "/api/v1/login"
    })
"""

import json
import logging
import logging.handlers
import os
import sys
import time as time_module
import uuid
from datetime import datetime, timedelta, timezone, time as datetime_time
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Dict, Optional

from pythonjsonlogger import jsonlogger

from core.config import settings

# 北京时间时区 (UTC+8)
BEIJING_TZ = timezone(timedelta(hours=8))


class BeijingTimeFormatter(logging.Formatter):
    """
    使用北京时间格式的日志格式化器
    """

    def formatTime(self, record: logging.LogRecord, datefmt: str = None) -> str:
        """
        重写时间格式化方法，使用北京时间

        Args:
            record: 日志记录对象
            datefmt: 时间格式字符串

        Returns:
            格式化后的时间字符串，格式：YYYY-MM-DD HH:MM:SS,SSS
        """
        ct = datetime.fromtimestamp(record.created, tz=BEIJING_TZ)
        if datefmt:
            s = ct.strftime(datefmt)
        else:
            # 格式：YYYY-MM-DD HH:MM:SS,SSS
            s = f"{ct.strftime('%Y-%m-%d %H:%M:%S')},{record.msecs:03.0f}"
        return s


class RAGJsonFormatter(jsonlogger.JsonFormatter):
    """
    RAG系统专用JSON日志格式化器

    确保日志输出符合规范要求的JSON格式，包含所有必需字段。
    时间格式：YYYY-MM-DD HH:MM:SS,SSS（北京时间）
    """

    DEFAULT_FIELDS = {
        "traceId": "",
        "userId": None,
        "method": "",
        "uri": "",
        "requestParams": {},
        "responseCode": None,
        "costMs": None,
        "clientIp": "",
        "errorStack": None
    }

    def add_fields(self, log_record: Dict[str, Any], record: logging.LogRecord, message_dict: Dict[str, Any]) -> None:
        """
        添加日志字段

        Args:
            log_record: 日志记录字典
            record: 日志记录对象
            message_dict: 消息字典
        """
        super().add_fields(log_record, record, message_dict)

        # 设置时间（使用北京时间，格式：YYYY-MM-DD HH:MM:SS,SSS）
        ct = datetime.fromtimestamp(record.created, tz=BEIJING_TZ)
        log_record["time"] = f"{ct.strftime('%Y-%m-%d %H:%M:%S')},{record.msecs:03.0f}"

        # 设置日志级别
        log_record["level"] = record.levelname

        # 设置默认字段（如果不存在）
        for field, default_value in self.DEFAULT_FIELDS.items():
            if field not in log_record:
                log_record[field] = default_value

        # 确保message字段存在
        if "message" not in log_record:
            log_record["message"] = record.getMessage()

        # 处理异常信息
        if record.exc_info:
            log_record["errorStack"] = self.formatException(record.exc_info)


class LevelFilter(logging.Filter):
    """
    日志级别过滤器

    根据日志级别过滤日志记录。
    """

    def __init__(self, min_level: int):
        """
        初始化过滤器

        Args:
            min_level: 最小日志级别
        """
        super().__init__()
        self.min_level = min_level

    def filter(self, record: logging.LogRecord) -> bool:
        """过滤日志记录"""
        return record.levelno >= self.min_level


def _get_log_filename_with_date(log_path: str, level: str) -> str:
    """
    根据级别和当前日期生成日志文件名

    Args:
        log_path: 原日志文件路径
        level: 日志级别 (info/error)

    Returns:
        带日期的日志文件路径 (例如: app.2026-05-23.info.log)
    """
    log_path_obj = Path(log_path)
    filename = log_path_obj.stem  # 不带扩展名的文件名
    ext = log_path_obj.suffix    # 扩展名 (.log)
    base_dir = log_path_obj.parent

    # 获取当前日期
    current_date = datetime.now(BEIJING_TZ).strftime("%Y-%m-%d")

    # 新文件名: app.2026-05-23.info.log
    return str(base_dir / f"{filename}.{current_date}.{level}{ext}")


def _create_timed_json_handler(log_path: str, level: str, min_level: int) -> logging.Handler:
    """
    创建按日期分割的JSON格式日志处理器

    Args:
        log_path: 日志文件路径
        level: 日志级别标识 (info/error)
        min_level: 最小日志级别

    Returns:
        日志处理器
    """
    formatter = RAGJsonFormatter(
        fmt="%(time)s %(level)s %(traceId)s %(message)s"
    )

    # 生成带日期的日志文件路径
    file_path = _get_log_filename_with_date(log_path, level)
    _ensure_log_dir(file_path)

    # 创建自定义文件名生成器（用于旋转时）
    def namer(filename: str) -> str:
        # 从当前日期生成新文件名
        current_date = datetime.now(BEIJING_TZ).strftime("%Y-%m-%d")
        base_path = Path(filename)
        name = base_path.stem
        ext = base_path.suffix
        parent = base_path.parent

        parts = name.rsplit(".", 2)
        if len(parts) >= 2:
            # app.2026-05-23.info -> app.2026-05-24.info
            base_name = parts[0]
            level_part = parts[-1]
            return str(parent / f"{base_name}.{current_date}.{level_part}{ext}")

        return str(parent / f"{name}.{current_date}{ext}")

    def rotator(source: str, dest: str) -> None:
        """重写旋转后的文件名"""
        pass

    # 使用 TimedRotatingFileHandler 按天分割
    handler = logging.handlers.TimedRotatingFileHandler(
        filename=file_path,
        when="midnight",           # 每天午夜分割
        interval=1,                 # 间隔1天
        backupCount=30,            # 保留30天日志
        encoding="utf-8",
        atTime=datetime_time(0, 0, 0)  # 北京时间0点分割
    )
    handler.setFormatter(formatter)
    handler.setLevel(min_level)

    # 设置自定义文件名生成器
    handler.namer = namer
    handler.rotator = rotator

    return handler


def _ensure_log_dir(log_path: str) -> None:
    """
    确保日志目录存在

    Args:
        log_path: 日志文件路径
    """
    log_dir = Path(log_path).parent
    log_dir.mkdir(parents=True, exist_ok=True)


def _create_timed_json_handler(log_path: str, level: str, min_level: int) -> logging.Handler:
    """
    创建按日期分割的JSON格式日志处理器

    Args:
        log_path: 日志文件路径
        level: 日志级别标识 (info/error)
        min_level: 最小日志级别

    Returns:
        日志处理器
    """
    formatter = RAGJsonFormatter(
        fmt="%(time)s %(level)s %(traceId)s %(message)s"
    )

    # 生成带级别的日志文件路径
    file_path = _get_log_filename_with_date(log_path, level)
    _ensure_log_dir(file_path)

    # 使用 TimedRotatingFileHandler 按天分割
    handler = logging.handlers.TimedRotatingFileHandler(
        filename=file_path,
        when="midnight",           # 每天午夜分割
        interval=1,                 # 间隔1天
        backupCount=30,            # 保留30天日志
        encoding="utf-8",
        atTime=datetime_time(0, 0, 0)  # 北京时间0点分割
    )
    handler.setFormatter(formatter)
    handler.setLevel(min_level)

    return handler


def _create_json_handler(log_path: Optional[str] = None, level: str = "INFO") -> logging.Handler:
    """
    创建JSON格式的日志处理器（保留原接口兼容）

    Args:
        log_path: 日志文件路径
        level: 日志级别

    Returns:
        日志处理器
    """
    formatter = RAGJsonFormatter(
        fmt="%(time)s %(level)s %(traceId)s %(message)s"
    )

    # 如果指定了文件路径，创建文件处理器
    if log_path:
        _ensure_log_dir(log_path)
        handler = logging.handlers.TimedRotatingFileHandler(
            filename=log_path,
            when="midnight",
            interval=1,
            backupCount=30,
            encoding="utf-8",
            atTime=datetime.time(0, 0, 0)
        )
        handler.setFormatter(formatter)
    else:
        # 否则创建控制台处理器
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(formatter)

    handler.setLevel(getattr(logging, level.upper(), logging.INFO))
    return handler


def setup_logging() -> None:
    """
    配置应用程序日志

    根据配置文件设置日志级别、格式和处理器。
    日志按日期分割，INFO和ERROR分别写入不同文件。
    """
    # 获取日志配置
    log_level = settings.logging.level
    log_format = settings.logging.format
    log_file_path = settings.logging.file.path

    # 创建根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    # 清除现有处理器
    root_logger.handlers.clear()

    if log_format == "json":
        # JSON格式日志
        if settings.logging.file.enabled:
            # INFO级别日志处理器（包含DEBUG, INFO, WARNING）
            info_handler = _create_timed_json_handler(log_file_path, "info", logging.INFO)
            root_logger.addHandler(info_handler)

            # ERROR级别日志处理器（包含ERROR, CRITICAL）
            error_handler = _create_timed_json_handler(log_file_path, "error", logging.ERROR)
            root_logger.addHandler(error_handler)

        if settings.logging.console.enabled:
            console_handler = _create_json_handler(level=log_level)
            root_logger.addHandler(console_handler)
    else:
        # 普通格式日志
        if settings.logging.file.enabled:
            # INFO级别日志
            info_file_path = _get_log_filename_with_date(log_file_path, "info")
            _ensure_log_dir(info_file_path)
            info_handler = logging.handlers.TimedRotatingFileHandler(
                filename=info_file_path,
                when="midnight",
                interval=1,
                backupCount=30,
                encoding="utf-8",
                atTime=datetime_time(0, 0, 0)
            )
            info_handler.setFormatter(
                BeijingTimeFormatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
            )
            info_handler.setLevel(logging.INFO)
            root_logger.addHandler(info_handler)

            # ERROR级别日志
            error_file_path = _get_log_filename_with_date(log_file_path, "error")
            error_handler = logging.handlers.TimedRotatingFileHandler(
                filename=error_file_path,
                when="midnight",
                interval=1,
                backupCount=30,
                encoding="utf-8",
                atTime=datetime_time(0, 0, 0)
            )
            error_handler.setFormatter(
                BeijingTimeFormatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
            )
            error_handler.setLevel(logging.ERROR)
            root_logger.addHandler(error_handler)

        if settings.logging.console.enabled:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(
                BeijingTimeFormatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
            )
            root_logger.addHandler(console_handler)

    # 设置第三方库日志级别
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)


class RequestLogger:
    """
    请求日志记录器

    用于记录HTTP请求的详细信息。
    """

    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        初始化请求日志记录器

        Args:
            logger: 日志记录器实例
        """
        self.logger = logger or logging.getLogger("rag.request")

    def log_request(
        self,
        trace_id: str,
        method: str,
        uri: str,
        client_ip: str,
        request_params: Optional[Dict[str, Any]] = None,
        user_id: Optional[int] = None,
        response_code: Optional[int] = None,
        cost_ms: Optional[int] = None,
        message: str = "",
        error_stack: Optional[str] = None
    ) -> None:
        """
        记录请求日志

        Args:
            trace_id: 追踪ID
            method: HTTP方法
            uri: 请求路径
            client_ip: 客户端IP
            request_params: 请求参数
            user_id: 用户ID
            response_code: 响应码
            cost_ms: 耗时（毫秒）
            message: 日志消息
            error_stack: 错误堆栈
        """
        log_data = {
            "traceId": trace_id,
            "method": method,
            "uri": uri,
            "clientIp": client_ip,
            "requestParams": request_params or {},
            "message": message
        }

        if user_id is not None:
            log_data["userId"] = user_id
        if response_code is not None:
            log_data["responseCode"] = response_code
        if cost_ms is not None:
            log_data["costMs"] = cost_ms
        if error_stack:
            log_data["errorStack"] = error_stack

        # 根据响应码确定日志级别
        if response_code is not None and response_code >= 500:
            self.logger.error("请求处理失败", extra=log_data)
        elif response_code is not None and response_code >= 400:
            self.logger.warning("请求参数错误", extra=log_data)
        else:
            self.logger.info(message or "请求处理成功", extra=log_data)


def get_trace_id() -> str:
    """
    生成追踪ID

    格式：日期时间+序号，例如 202605211200000001

    Returns:
        追踪ID字符串
    """
    now = datetime.now(BEIJING_TZ)
    date_part = now.strftime("%Y%m%d%H%M")
    # 使用UUID生成唯一序号
    unique_part = str(uuid.uuid4().int)[:6]
    return f"{date_part}{unique_part}"


# 创建全局请求日志记录器
request_logger = RequestLogger()

# 创建全局logger
logger = logging.getLogger("rag")


def log_request_info(
    message: str,
    trace_id: Optional[str] = None,
    user_id: Optional[int] = None,
    method: Optional[str] = None,
    uri: Optional[str] = None,
    **kwargs
) -> None:
    """
    记录INFO级别日志

    Args:
        message: 日志消息
        trace_id: 追踪ID
        user_id: 用户ID
        method: HTTP方法
        uri: 请求路径
        **kwargs: 其他日志字段
    """
    extra = {"traceId": trace_id or "", "userId": user_id, "method": method or "", "uri": uri or ""}
    extra.update(kwargs)
    logger.info(message, extra=extra)


def log_request_error(
    message: str,
    error: Optional[Exception] = None,
    trace_id: Optional[str] = None,
    user_id: Optional[int] = None,
    method: Optional[str] = None,
    uri: Optional[str] = None,
    **kwargs
) -> None:
    """
    记录ERROR级别日志

    Args:
        message: 日志消息
        error: 异常对象
        trace_id: 追踪ID
        user_id: 用户ID
        method: HTTP方法
        uri: 请求路径
        **kwargs: 其他日志字段
    """
    extra = {
        "traceId": trace_id or "",
        "userId": user_id,
        "method": method or "",
        "uri": uri or "",
        "errorStack": str(error) if error else None
    }
    extra.update(kwargs)
    logger.error(message, extra=extra)
