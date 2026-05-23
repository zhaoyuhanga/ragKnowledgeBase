# -*- coding: utf-8 -*-
"""
响应模块测试

测试统一响应格式功能。
"""

import pytest
from datetime import datetime, timezone


class TestResponse:
    """响应模块测试类"""

    def test_success_response(self):
        """测试成功响应创建"""
        from app.common.response import success_response

        response = success_response(
            data={"id": 1, "name": "测试"},
            message="获取成功"
        )

        # 验证响应格式
        assert response.code == 0
        assert response.message == "获取成功"
        assert response.data == {"id": 1, "name": "测试"}
        assert response.trace_id == ""
        assert response.timestamp != ""

    def test_success_response_default(self):
        """测试默认成功响应"""
        from app.common.response import success_response

        response = success_response()

        # 验证默认响应
        assert response.code == 0
        assert response.message == "success"
        assert response.data is None

    def test_error_response(self):
        """测试错误响应创建"""
        from app.common.response import error_response

        response = error_response(
            code="BIZ_2001",
            message="数据不存在",
            trace_id="202605221200000001"
        )

        # 验证响应格式
        assert response.code == "BIZ_2001"
        assert response.message == "数据不存在"
        assert response.trace_id == "202605221200000001"
        assert response.data is None

    def test_page_response(self):
        """测试分页响应创建"""
        from app.common.response import page_response

        items = [{"id": 1}, {"id": 2}, {"id": 3}]
        response = page_response(
            items=items,
            total=100,
            page_no=1,
            page_size=20
        )

        # 验证响应格式
        assert response.code == 0
        assert response.data.items == items
        assert response.data.total == 100
        assert response.data.page_no == 1
        assert response.data.page_size == 20
        assert response.data.pages == 5  # 100/20

    def test_page_response_empty(self):
        """测试空分页响应"""
        from app.common.response import page_response

        response = page_response(
            items=[],
            total=0,
            page_no=1,
            page_size=20
        )

        # 验证响应格式
        assert response.data.items == []
        assert response.data.total == 0
        assert response.data.pages == 0

    def test_response_timestamp_format(self):
        """测试时间戳格式"""
        from app.common.response import success_response

        response = success_response()

        # 验证时间戳是ISO格式
        assert "T" in response.timestamp
        assert "+" in response.timestamp or "Z" in response.timestamp
