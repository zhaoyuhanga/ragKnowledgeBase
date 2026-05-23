# -*- coding: utf-8 -*-
"""
异常模块测试

测试统一异常处理功能。
"""

import pytest


class TestException:
    """异常模块测试类"""

    def test_business_exception(self):
        """测试业务异常"""
        from app.common.exception import BusinessException, ErrorCode

        exception = BusinessException(
            code=ErrorCode.DATA_NOT_FOUND[0],
            message="数据不存在"
        )

        # 验证异常属性
        assert exception.code == "BIZ_2001"
        assert exception.message == "数据不存在"
        assert exception.data is None
        assert "[BIZ_2001] 数据不存在" in str(exception)

    def test_business_exception_with_data(self):
        """测试带数据的业务异常"""
        from app.common.exception import BusinessException

        exception = BusinessException(
            code="BIZ_2001",
            message="数据不存在",
            data={"id": 123}
        )

        # 验证异常数据
        assert exception.data == {"id": 123}

    def test_error_code_system(self):
        """测试系统错误码"""
        from app.common.exception import ErrorCode

        # 验证系统错误码
        assert ErrorCode.SYSTEM_ERROR[0] == "SYS_1000"
        assert ErrorCode.PARAM_INVALID[0] == "SYS_1001"
        assert ErrorCode.DATABASE_ERROR[0] == "SYS_1003"

    def test_error_code_business(self):
        """测试业务错误码"""
        from app.common.exception import ErrorCode

        # 验证业务错误码
        assert ErrorCode.DATA_NOT_FOUND[0] == "BIZ_2001"
        assert ErrorCode.DATA_DUPLICATE[0] == "BIZ_2002"
        assert ErrorCode.OPERATION_FAILED[0] == "BIZ_2004"

    def test_error_code_document(self):
        """测试文档错误码"""
        from app.common.exception import ErrorCode

        # 验证文档错误码
        assert ErrorCode.FILE_TYPE_NOT_SUPPORT[0] == "DOC_3001"
        assert ErrorCode.FILE_SIZE_TOO_LARGE[0] == "DOC_3002"
        assert ErrorCode.PARSE_FAILED[0] == "DOC_3005"

    def test_error_code_retrieval(self):
        """测试检索错误码"""
        from app.common.exception import ErrorCode

        # 验证检索错误码
        assert ErrorCode.EMBEDDING_FAILED[0] == "RET_4001"
        assert ErrorCode.RETRIEVAL_FAILED[0] == "RET_4002"
        assert ErrorCode.RERANK_FAILED[0] == "RET_4003"

    def test_error_code_auth(self):
        """测试认证错误码"""
        from app.common.exception import ErrorCode

        # 验证认证错误码
        assert ErrorCode.UNAUTHORIZED[0] == "AUTH_9000"
        assert ErrorCode.TOKEN_EXPIRED[0] == "AUTH_9001"
        assert ErrorCode.PERMISSION_DENIED[0] == "AUTH_9003"

    def test_exception_to_dict(self):
        """测试异常转字典"""
        from app.common.exception import BusinessException

        exception = BusinessException(
            code="TEST_001",
            message="测试异常",
            data={"key": "value"}
        )

        # 验证字典转换
        exception_dict = exception.to_dict()
        assert exception_dict["code"] == "TEST_001"
        assert exception_dict["message"] == "测试异常"
        assert exception_dict["data"] == {"key": "value"}

    def test_validation_exception(self):
        """测试参数校验异常"""
        from app.common.exception import ValidationException

        exception = ValidationException(message="参数不能为空")

        # 验证异常
        assert exception.code == "SYS_1001"
        assert exception.message == "参数不能为空"

    def test_unauthorized_exception(self):
        """测试未授权异常"""
        from app.common.exception import UnauthorizedException

        exception = UnauthorizedException()

        # 验证异常
        assert exception.code == "AUTH_9000"
        assert exception.message == "未授权"
