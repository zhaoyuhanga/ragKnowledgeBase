# -*- coding: utf-8 -*-
"""
Pytest配置文件

本模块提供测试的 fixtures 和配置。
"""

import os
import sys
from pathlib import Path

import pytest

# 设置测试环境变量（在任何导入之前）
os.environ["APP_ENV"] = "local"
os.environ.setdefault("MYSQL_HOST", "localhost")
os.environ.setdefault("MYSQL_PORT", "3308")
os.environ.setdefault("MYSQL_USERNAME", "root")
os.environ.setdefault("MYSQL_PASSWORD", "root")
os.environ.setdefault("MYSQL_DATABASE", "rag_db_test")

# 将src目录添加到路径
backend_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(backend_path))


@pytest.fixture
def sample_document_data():
    """示例文档数据"""
    return {
        "name": "测试文档.pdf",
        "doc_type": "pdf",
        "tenant_id": 1
    }


@pytest.fixture
def sample_retrieval_request():
    """示例检索请求数据"""
    return {
        "query": "RAG是什么？",
        "top_k": 10,
        "tenant_id": 1
    }


@pytest.fixture
def sample_qa_request():
    """示例问答请求数据"""
    return {
        "question": "RAG技术有什么优势？",
        "tenant_id": 1,
        "use_rerank": True
    }
