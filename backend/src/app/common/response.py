# -*- coding: utf-8 -*-
"""
统一响应模块

本模块提供统一的API响应格式，确保所有接口返回一致的响应结构。

响应格式：
- 成功响应：code=0, message="success", data=实际数据
- 失败响应：code=错误码, message=错误消息, data=null

使用示例：
    from app.common.response import success_response, error_response

    # 返回成功响应
    return success_response(data={"user_id": 1})

    # 返回错误响应
    return error_response(code="BIZ_2001", message="数据不存在")
"""

from datetime import datetime, timezone
from typing import Any, Generic, List, Optional, TypeVar

from pydantic import BaseModel, Field


# 定义泛型类型
T = TypeVar("T")


class BaseResponse(BaseModel):
    """响应基础模型"""
    code: int = Field(default=0, description="状态码，0表示成功")
    message: str = Field(default="success", description="响应消息")
    data: Any = Field(default=None, description="响应数据")
    trace_id: str = Field(default="", description="追踪ID")
    timestamp: str = Field(
        default="",
        description="ISO8601格式时间戳"
    )

    def __init__(self, **data):
        """初始化响应，自动设置时间戳"""
        if "timestamp" not in data or not data["timestamp"]:
            data["timestamp"] = datetime.now(timezone.utc).isoformat()
        super().__init__(**data)


class ErrorResponse(BaseModel):
    """错误响应模型"""
    code: str = Field(description="错误码")
    message: str = Field(description="错误消息")
    data: Any = Field(default=None, description="错误数据")
    trace_id: str = Field(default="", description="追踪ID")
    timestamp: str = Field(description="ISO8601格式时间戳")

    def __init__(self, **data):
        """初始化错误响应，自动设置时间戳"""
        if "timestamp" not in data or not data["timestamp"]:
            data["timestamp"] = datetime.now(timezone.utc).isoformat()
        super().__init__(**data)


class PageInfo(BaseModel):
    """分页信息"""
    items: List[Any] = Field(default_factory=list, description="数据列表")
    total: int = Field(default=0, description="总记录数")
    page_no: int = Field(default=1, description="当前页码")
    page_size: int = Field(default=20, description="每页大小")
    pages: int = Field(default=0, description="总页数")


class PageResponse(BaseModel):
    """分页响应模型"""
    code: int = Field(default=0, description="状态码")
    message: str = Field(default="success", description="响应消息")
    data: PageInfo = Field(description="分页数据")
    trace_id: str = Field(default="", description="追踪ID")
    timestamp: str = Field(description="ISO8601格式时间戳")

    def __init__(self, **data):
        """初始化分页响应，自动设置时间戳"""
        if "timestamp" not in data or not data["timestamp"]:
            data["timestamp"] = datetime.now(timezone.utc).isoformat()
        super().__init__(**data)


def success_response(
    data: Any = None,
    message: str = "success",
    trace_id: str = "",
    code: int = 0
) -> BaseModel:
    """
    创建成功响应

    Args:
        data: 响应数据
        message: 成功消息
        trace_id: 追踪ID
        code: 状态码，默认0表示成功

    Returns:
        BaseResponse: 统一响应对象

    示例:
        >>> success_response(data={"id": 1}, message="获取成功")
        >>> success_response(data=[1, 2, 3])
    """
    return BaseResponse(
        code=code,
        message=message,
        data=data,
        trace_id=trace_id
    )


def error_response(
    code: str = "SYS_1000",
    message: str = "系统错误",
    data: Any = None,
    trace_id: str = ""
) -> ErrorResponse:
    """
    创建错误响应

    Args:
        code: 错误码
        message: 错误消息
        data: 错误数据
        trace_id: 追踪ID

    Returns:
        ErrorResponse: 错误响应对象

    示例:
        >>> error_response(code="BIZ_2001", message="数据不存在")
        >>> error_response(code="AUTH_9001", message="登录已过期，请重新登录")
    """
    return ErrorResponse(
        code=code,
        message=message,
        data=data,
        trace_id=trace_id
    )


def page_response(
    items: List[Any],
    total: int,
    page_no: int = 1,
    page_size: int = 20,
    message: str = "success",
    trace_id: str = ""
) -> PageResponse:
    """
    创建分页响应

    Args:
        items: 数据列表
        total: 总记录数
        page_no: 当前页码
        page_size: 每页大小
        message: 成功消息
        trace_id: 追踪ID

    Returns:
        PageResponse: 分页响应对象

    示例:
        >>> page_response(items=[...], total=100, page_no=1, page_size=20)
    """
    pages = (total + page_size - 1) // page_size if page_size > 0 else 0
    return PageResponse(
        code=0,
        message=message,
        data=PageInfo(
            items=items,
            total=total,
            page_no=page_no,
            page_size=page_size,
            pages=pages
        ),
        trace_id=trace_id
    )
