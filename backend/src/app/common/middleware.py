# -*- coding: utf-8 -*-
"""
中间件模块

本模块提供FastAPI应用的中间件：
- RequestLoggingMiddleware: 请求日志中间件
- ErrorHandlerMiddleware: 错误处理中间件
- CORSMiddleware: 跨域中间件

使用示例：
    from app.common.middleware import setup_middleware

    app = FastAPI()
    setup_middleware(app)
"""

import json
import time
import uuid
from datetime import datetime, timezone
from typing import Callable

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.common.exception import BusinessException
from app.common.logging import get_trace_id, log_request_error, log_request_info
from app.common.response import error_response
from core.config import settings


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    请求日志中间件

    在每个请求处理前后记录日志，包含：
    - 请求信息（方法、路径、参数等）
    - 响应信息（状态码、耗时等）
    - 追踪ID（用于关联请求链路）
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        处理请求

        Args:
            request: 请求对象
            call_next: 下一个处理函数

        Returns:
            响应对象
        """
        # 生成追踪ID
        trace_id = request.headers.get("X-Trace-Id") or get_trace_id()

        # 获取客户端IP
        client_ip = self._get_client_ip(request)

        # 获取用户ID（如果有）
        user_id = self._get_user_id(request)

        # 获取请求参数
        request_params = await self._get_request_params(request)

        # 记录请求开始时间
        start_time = time.time()

        # 处理请求
        try:
            response = await call_next(request)

            # 计算耗时
            cost_ms = int((time.time() - start_time) * 1000)

            # 记录成功日志
            log_request_info(
                message="请求处理成功",
                trace_id=trace_id,
                user_id=user_id,
                method=request.method,
                uri=str(request.url.path),
                response_code=response.status_code,
                cost_ms=cost_ms,
                client_ip=client_ip,
                request_params=request_params
            )

            # 在响应头中添加追踪ID
            response.headers["X-Trace-Id"] = trace_id

            return response

        except BusinessException as e:
            # 业务异常处理
            cost_ms = int((time.time() - start_time) * 1000)

            log_request_error(
                message=f"业务异常: {e.message}",
                error=e,
                trace_id=trace_id,
                user_id=user_id,
                method=request.method,
                uri=str(request.url.path),
                response_code=500,
                cost_ms=cost_ms,
                client_ip=client_ip,
                request_params=request_params
            )

            return JSONResponse(
                status_code=200,  # 使用200，因为错误信息在响应体中
                content=error_response(
                    code=e.code,
                    message=e.message,
                    data=e.data,
                    trace_id=trace_id
                ).model_dump(),
                headers={"X-Trace-Id": trace_id}
            )

        except Exception as e:
            # 其他异常处理
            cost_ms = int((time.time() - start_time) * 1000)

            log_request_error(
                message=f"系统异常: {str(e)}",
                error=e,
                trace_id=trace_id,
                user_id=user_id,
                method=request.method,
                uri=str(request.url.path),
                response_code=500,
                cost_ms=cost_ms,
                client_ip=client_ip,
                request_params=request_params
            )

            return JSONResponse(
                status_code=200,
                content=error_response(
                    code="SYS_1000",
                    message="系统错误，请稍后重试",
                    trace_id=trace_id
                ).model_dump(),
                headers={"X-Trace-Id": trace_id}
            )

    def _get_client_ip(self, request: Request) -> str:
        """
        获取客户端IP地址

        Args:
            request: 请求对象

        Returns:
            客户端IP地址
        """
        # 优先从X-Forwarded-For获取
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        # 其次从X-Real-IP获取
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        # 最后从客户端地址获取
        if request.client:
            return request.client.host

        return "unknown"

    def _get_user_id(self, request: Request) -> int | None:
        """
        从请求中获取用户ID

        Args:
            request: 请求对象

        Returns:
            用户ID，如果未登录则返回None
        """
        # 从Authorization头获取token
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:]
            # TODO: 从token中解析用户ID
            # 这里可以使用JWT解码或其他方式
            pass

        # 从请求状态中获取（由认证依赖注入设置）
        if hasattr(request.state, "user_id"):
            return request.state.user_id

        return None

    async def _get_request_params(self, request: Request) -> dict:
        """
        获取请求参数

        Args:
            request: 请求对象

        Returns:
            请求参数字典
        """
        params = {}

        # 获取路径参数
        if request.path_params:
            params["path"] = request.path_params

        # 获取查询参数
        if request.query_params:
            # 过滤敏感字段
            sensitive_fields = {"password", "token", "secret", "key"}
            for key, value in request.query_params.items():
                if key.lower() not in sensitive_fields:
                    params[key] = value

        # 获取请求体
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.body()
                if body:
                    data = json.loads(body)
                    # 过滤敏感字段
                    sensitive_fields = {"password", "token", "secret", "key"}
                    filtered_data = {
                        k: v for k, v in data.items()
                        if k.lower() not in sensitive_fields
                    }
                    params["body"] = filtered_data
            except Exception:
                pass

        return params


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """
    全局异常处理中间件

    捕获所有未处理的异常，统一返回规范格式的响应。
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        处理请求

        Args:
            request: 请求对象
            call_next: 下一个处理函数

        Returns:
            响应对象
        """
        try:
            response = await call_next(request)
            return response

        except Exception as e:
            # 生成追踪ID
            trace_id = request.headers.get("X-Trace-Id") or get_trace_id()

            # 记录错误日志
            log_request_error(
                message=f"未处理的异常: {str(e)}",
                error=e,
                trace_id=trace_id,
                method=request.method,
                uri=str(request.url.path)
            )

            return JSONResponse(
                status_code=200,
                content=error_response(
                    code="SYS_1000",
                    message="系统错误，请稍后重试",
                    trace_id=trace_id
                ).model_dump(),
                headers={"X-Trace-Id": trace_id}
            )


def setup_middleware(app: FastAPI) -> None:
    """
    配置中间件

    Args:
        app: FastAPI应用实例
    """
    # 添加请求日志中间件
    app.add_middleware(RequestLoggingMiddleware)

    # 添加CORS中间件
    if settings.cors.enabled:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors.allow_origins,
            allow_credentials=settings.cors.allow_credentials,
            allow_methods=settings.cors.allow_methods if settings.cors.allow_methods else ["*"],
            allow_headers=settings.cors.allow_headers if settings.cors.allow_headers else ["*"],
        )
