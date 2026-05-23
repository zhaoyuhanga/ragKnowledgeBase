# -*- coding: utf-8 -*-
"""
文档模块测试

测试文档上传、列表、详情、删除等功能。
"""

import io
import pytest
from unittest.mock import Mock, patch

from fastapi.testclient import TestClient

from app.main import app


class TestDocumentUpload:
    """文档上传测试类"""

    def setup_method(self):
        """测试前置设置"""
        self.client = TestClient(app)

    def test_upload_success(self):
        """测试上传成功"""
        # 创建测试文件
        file_content = b"%PDF-1.4 test content"
        file = ("file", ("test.pdf", io.BytesIO(file_content), "application/pdf"))

        # 模拟文件上传
        with patch("app.services.storage_service.FileStorageService.validate_file") as mock_validate:
            mock_validate.return_value = "pdf"

            with patch("app.services.storage_service.FileStorageService.calculate_hash") as mock_hash:
                mock_hash.return_value = "abc123"

                with patch("app.services.version_service.DocumentVersionService.check_file_duplicate_with_db") as mock_duplicate:
                    mock_duplicate.return_value = None  # 不是重复文件

                    with patch("app.services.storage_service.FileStorageService.save_file") as mock_save:
                        mock_save.return_value = Mock(
                            original_name="test.pdf",
                            stored_name="test.pdf",
                            file_path="/data/test.pdf",
                            file_size=len(file_content),
                            file_hash="abc123",
                            doc_type="pdf",
                            mime_type="application/pdf"
                        )

                        with patch("core.database.SessionLocal") as mock_db:
                            mock_session = Mock()
                            mock_db.return_value = mock_session

                            response = self.client.post(
                                "/api/v1/documents/upload",
                                files={"file": file}
                            )

                            # 验证响应
                            assert response.status_code == 200
                            data = response.json()
                            assert data["code"] == 0
                            assert "data" in data

    def test_upload_invalid_type(self):
        """测试不支持的文件类型"""
        file_content = b"test content"
        file = ("file", ("test.xyz", io.BytesIO(file_content), "text/plain"))

        response = self.client.post(
            "/api/v1/documents/upload",
            files={"file": file}
        )

        # 验证响应（应该返回错误）
        assert response.status_code == 200
        data = response.json()
        assert data["code"] != 0


class TestDocumentList:
    """文档列表测试类"""

    def setup_method(self):
        """测试前置设置"""
        self.client = TestClient(app)

    def test_list_documents(self):
        """测试获取文档列表"""
        with patch("app.services.document_service.DocumentService.list_documents") as mock_list:
            mock_list.return_value = {
                "items": [
                    {
                        "id": 1,
                        "name": "测试文档.pdf",
                        "doc_type": "pdf",
                        "status": 0,
                        "status_name": "待解析",
                        "total_versions": 1,
                        "created_at": "2026-05-22T10:00:00"
                    }
                ],
                "total": 1
            }

            response = self.client.get("/api/v1/documents")

            # 验证响应
            assert response.status_code == 200
            data = response.json()
            assert data["code"] == 0
            assert "data" in data
            assert "items" in data["data"]
            assert data["data"]["total"] == 1

    def test_list_documents_with_filters(self):
        """测试带筛选条件的文档列表"""
        with patch("app.services.document_service.DocumentService.list_documents") as mock_list:
            mock_list.return_value = {
                "items": [],
                "total": 0
            }

            response = self.client.get(
                "/api/v1/documents",
                params={
                    "business_id": "biz001",
                    "status": 0,
                    "keyword": "测试"
                }
            )

            # 验证响应
            assert response.status_code == 200
            data = response.json()
            assert data["code"] == 0


class TestDocumentDetail:
    """文档详情测试类"""

    def setup_method(self):
        """测试前置设置"""
        self.client = TestClient(app)

    def test_get_document(self):
        """测试获取文档详情"""
        with patch("app.services.document_service.DocumentService.get_document") as mock_get:
            mock_get.return_value = {
                "id": 1,
                "name": "测试文档.pdf",
                "doc_type": "pdf",
                "status": 0,
                "status_name": "待解析",
                "total_versions": 1,
                "versions": []
            }

            response = self.client.get("/api/v1/documents/1")

            # 验证响应
            assert response.status_code == 200
            data = response.json()
            assert data["code"] == 0
            assert data["data"]["id"] == 1


class TestDocumentVersion:
    """文档版本测试类"""

    def setup_method(self):
        """测试前置设置"""
        self.client = TestClient(app)

    def test_list_versions(self):
        """测试获取版本列表"""
        with patch("app.services.document_service.DocumentService.list_versions") as mock_list:
            mock_list.return_value = [
                {
                    "id": 1,
                    "version": 1,
                    "file_name": "test.pdf",
                    "status": 0
                }
            ]

            response = self.client.get("/api/v1/documents/1/versions")

            # 验证响应
            assert response.status_code == 200
            data = response.json()
            assert data["code"] == 0
            assert "items" in data["data"]

    def test_get_version(self):
        """测试获取版本详情"""
        with patch("app.services.document_service.DocumentService.get_version") as mock_get:
            mock_get.return_value = {
                "id": 1,
                "version": 1,
                "file_name": "test.pdf",
                "file_size": 1024,
                "status": 0
            }

            response = self.client.get("/api/v1/documents/1/versions/1")

            # 验证响应
            assert response.status_code == 200
            data = response.json()
            assert data["code"] == 0
            assert data["data"]["id"] == 1


class TestImportTask:
    """导入任务测试类"""

    def setup_method(self):
        """测试前置设置"""
        self.client = TestClient(app)

    def test_get_task(self):
        """测试获取任务详情"""
        with patch("app.services.document_service.ImportTaskService.get_task_by_id") as mock_get:
            mock_task = Mock()
            mock_task.id = 1
            mock_task.task_id = "task-123"
            mock_task.document_id = 1
            mock_task.version_id = 1
            mock_task.task_type = "upload"
            mock_task.task_status = "completed"
            mock_task.priority = 5
            mock_task.progress = 100
            mock_task.retry_count = 0
            mock_task.max_retry = 3
            mock_task.error_type = None
            mock_task.error_message = None
            mock_task.started_at = None
            mock_task.completed_at = None
            mock_task.cost_seconds = None
            mock_task.created_at = None
            mock_get.return_value = mock_task

            response = self.client.get("/api/v1/import-tasks/task-123")

            # 验证响应
            assert response.status_code == 200
            data = response.json()
            assert data["code"] == 0
            assert data["data"]["task_id"] == "task-123"

    def test_list_tasks(self):
        """测试获取任务列表"""
        with patch("core.database.SessionLocal") as mock_db:
            mock_session = Mock()
            mock_db.return_value = mock_session

            # 模拟查询结果为空
            mock_query = Mock()
            mock_query.filter.return_value = mock_query
            mock_query.count.return_value = 0
            mock_query.order_by.return_value = mock_query
            mock_query.offset.return_value = mock_query
            mock_query.limit.return_value = mock_query
            mock_query.all.return_value = []
            mock_session.query.return_value = mock_query

            response = self.client.get("/api/v1/import-tasks")

            # 验证响应
            assert response.status_code == 200
            data = response.json()
            assert data["code"] == 0
