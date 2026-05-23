# -*- coding: utf-8 -*-
"""
统一异常处理模块

本模块定义应用程序的异常体系，提供统一的异常处理机制。

异常分类：
- SYS_1xxx: 系统错误（1000-1999）
- BIZ_2xxx: 业务错误（2000-2999）
- DOC_3xxx: 文档错误（3000-3999）
- RET_4xxx: 检索错误（4000-4999）
- AUTH_9xxx: 认证错误（9000-9999）

使用示例：
    from app.common.exception import BusinessException, ErrorCode

    raise BusinessException(ErrorCode.DATA_NOT_FOUND, "用户不存在")
"""

from typing import Any, Optional


class ErrorCode:
    """错误码定义"""

    # ========== 系统错误 (SYS_1xxx) ==========
    SYSTEM_ERROR = ("SYS_1000", "系统错误")
    PARAM_INVALID = ("SYS_1001", "参数错误")
    INTERNAL_ERROR = ("SYS_1002", "内部错误")
    DATABASE_ERROR = ("SYS_1003", "数据库错误")
    SERVICE_UNAVAILABLE = ("SYS_1004", "服务不可用")
    TIMEOUT_ERROR = ("SYS_1005", "请求超时")

    # ========== 业务错误 (BIZ_2xxx) ==========
    DATA_NOT_FOUND = ("BIZ_2001", "数据不存在")
    DATA_DUPLICATE = ("BIZ_2002", "数据重复")
    DATA_INVALID = ("BIZ_2003", "数据无效")
    OPERATION_FAILED = ("BIZ_2004", "操作失败")
    RESOURCE_NOT_ENOUGH = ("BIZ_2005", "资源不足")

    # ========== 文档错误 (DOC_3xxx) ==========
    FILE_TYPE_NOT_SUPPORT = ("DOC_3001", "文件类型不支持")
    FILE_SIZE_TOO_LARGE = ("DOC_3002", "文件大小超出限制")
    FILE_UPLOAD_FAILED = ("DOC_3003", "文件上传失败")
    FILE_NOT_FOUND = ("DOC_3004", "文件不存在")
    PARSE_FAILED = ("DOC_3005", "文档解析失败")
    CHUNK_FAILED = ("DOC_3006", "文档切分失败")

    # ========== 检索错误 (RET_4xxx) ==========
    EMBEDDING_FAILED = ("RET_4001", "向量化失败")
    RETRIEVAL_FAILED = ("RET_4002", "检索失败")
    RERANK_FAILED = ("RET_4003", "重排失败")
    INDEX_NOT_FOUND = ("RET_4004", "索引不存在")

    # ========== 认证错误 (AUTH_9xxx) ==========
    UNAUTHORIZED = ("AUTH_9000", "未授权")
    TOKEN_EXPIRED = ("AUTH_9001", "登录已过期")
    TOKEN_INVALID = ("AUTH_9002", "令牌无效")
    PERMISSION_DENIED = ("AUTH_9003", "权限不足")
    USER_NOT_FOUND = ("AUTH_9004", "用户不存在")


class BusinessException(Exception):
    """
    业务异常基类

    所有业务异常都应继承此类，提供统一的异常处理。

    Attributes:
        code: 错误码
        message: 错误消息
        data: 附加数据
    """

    def __init__(
        self,
        code: str = "SYS_1000",
        message: str = "系统错误",
        data: Any = None
    ):
        """
        初始化业务异常

        Args:
            code: 错误码
            message: 错误消息
            data: 附加数据
        """
        self.code = code
        self.message = message
        self.data = data
        super().__init__(message)

    def __str__(self) -> str:
        """返回异常字符串表示"""
        return f"[{self.code}] {self.message}"

    def to_dict(self) -> dict:
        """
        转换为字典格式

        Returns:
            异常信息字典
        """
        return {
            "code": self.code,
            "message": self.message,
            "data": self.data
        }


class SystemException(BusinessException):
    """系统异常"""

    def __init__(
        self,
        code: str = "SYS_1000",
        message: str = "系统错误",
        data: Any = None
    ):
        super().__init__(code, message, data)


class DatabaseException(BusinessException):
    """数据库异常"""

    def __init__(
        self,
        message: str = "数据库错误",
        data: Any = None
    ):
        super().__init__("SYS_1003", message, data)


class ValidationException(BusinessException):
    """参数校验异常"""

    def __init__(
        self,
        message: str = "参数错误",
        data: Any = None
    ):
        super().__init__("SYS_1001", message, data)


class UnauthorizedException(BusinessException):
    """未授权异常"""

    def __init__(
        self,
        message: str = "未授权",
        data: Any = None
    ):
        super().__init__("AUTH_9000", message, data)


class PermissionDeniedException(BusinessException):
    """权限不足异常"""

    def __init__(
        self,
        message: str = "权限不足",
        data: Any = None
    ):
        super().__init__("AUTH_9003", message, data)


class DocumentException(BusinessException):
    """文档相关异常"""

    def __init__(
        self,
        code: str = "DOC_3001",
        message: str = "文档错误",
        data: Any = None
    ):
        super().__init__(code, message, data)


class RetrievalException(BusinessException):
    """检索相关异常"""

    def __init__(
        self,
        code: str = "RET_4002",
        message: str = "检索错误",
        data: Any = None
    ):
        super().__init__(code, message, data)


class ExternalServiceException(BusinessException):
    """外部服务调用异常"""

    def __init__(
        self,
        service_name: str,
        message: str = "外部服务调用失败",
        data: Any = None
    ):
        super().__init__(
            code="SYS_1004",
            message=f"{service_name}: {message}",
            data=data
        )


class FileException(DocumentException):
    """文件相关异常"""

    def __init__(
        self,
        code: str = "DOC_3001",
        message: str = "文件错误",
        data: Any = None
    ):
        super().__init__(code, message, data)
