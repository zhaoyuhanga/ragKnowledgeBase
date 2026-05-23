# -*- coding: utf-8 -*-
"""
API路由测试

测试API路由功能。
"""

import pytest


class TestHealthAPI:
    """健康检查API测试类"""

    def test_health_check(self, client):
        """测试健康检查接口"""
        response = client.get("/api/v1/health")

        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["data"]["status"] == "healthy"
        assert "service" in data["data"]
        assert "version" in data["data"]

    def test_health_check_redis(self, client):
        """测试Redis健康检查"""
        response = client.get("/api/v1/health/redis")

        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert "code" in data
        assert "data" in data
        assert "status" in data["data"]
        assert "type" in data["data"]
        assert data["data"]["type"] == "redis"


class TestDocumentAPI:
    """文档管理API测试类"""

    def test_list_documents(self, client):
        """测试文档列表查询"""
        response = client.get("/api/v1/documents")

        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "data" in data
        assert "items" in data["data"]
        assert "total" in data["data"]
        assert "page_no" in data["data"]
        assert "page_size" in data["data"]

    def test_list_documents_with_params(self, client):
        """测试带参数的文档列表查询"""
        response = client.get(
            "/api/v1/documents",
            params={
                "page_no": 1,
                "page_size": 10,
                "name": "测试",
                "doc_type": "pdf"
            }
        )

        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0

    def test_get_document_not_found(self, client):
        """测试获取不存在的文档"""
        response = client.get("/api/v1/documents/999999")

        # 验证响应
        assert response.status_code == 200
        data = response.json()
        # 应该返回错误响应
        assert data["code"] != 0 or data["code"] == "BIZ_2001"


class TestRetrievalAPI:
    """检索API测试类"""

    def test_hybrid_search(self, client, sample_retrieval_request):
        """测试混合检索接口"""
        response = client.post(
            "/api/v1/retrieval/hybrid",
            json=sample_retrieval_request
        )

        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "data" in data
        assert "query" in data["data"]
        assert "results" in data["data"]

    def test_vector_search(self, client):
        """测试向量检索接口"""
        response = client.post(
            "/api/v1/retrieval/vector",
            params={
                "query": "RAG是什么？",
                "top_k": 10
            }
        )

        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0

    def test_keyword_search(self, client):
        """测试关键词检索接口"""
        response = client.post(
            "/api/v1/retrieval/keyword",
            params={
                "query": "RAG",
                "top_k": 10
            }
        )

        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0

    def test_suggestions(self, client):
        """测试检索建议接口"""
        response = client.get(
            "/api/v1/retrieval/suggest",
            params={
                "query": "RAG",
                "limit": 5
            }
        )

        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "data" in data


class TestQAAPI:
    """问答API测试类"""

    def test_ask_question(self, client, sample_qa_request):
        """测试问答接口"""
        response = client.post(
            "/api/v1/qa",
            json=sample_qa_request
        )

        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "data" in data
        assert "result" in data["data"]
        assert "question" in data["data"]["result"]
        assert "answer" in data["data"]["result"]

    def test_get_history(self, client):
        """测试获取会话历史"""
        response = client.get(
            "/api/v1/qa/history",
            params={
                "session_id": "test-session-id"
            }
        )

        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "data" in data
        assert "items" in data["data"]

    def test_feedback(self, client):
        """测试提交反馈接口"""
        feedback_data = {
            "feedback": "helpful",
            "quality_score": 5,
            "remark": "回答准确"
        }
        response = client.post(
            "/api/v1/qa/999999/feedback",
            json=feedback_data
        )

        # 验证响应（可能是错误，因为ID不存在）
        assert response.status_code == 200
        data = response.json()
        assert "code" in data
