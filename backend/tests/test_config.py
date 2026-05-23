# -*- coding: utf-8 -*-
"""
配置模块测试

测试核心配置模块的功能。
"""

import os
import pytest
from pathlib import Path


class TestConfig:
    """配置模块测试类"""

    def test_config_load_local(self):
        """测试本地环境配置加载"""
        # 设置环境变量
        os.environ["APP_ENV"] = "local"

        # 重新加载配置
        from core.config import reload_settings
        config = reload_settings()

        # 验证配置
        assert config.app.env == "local"
        assert config.server.port == 8011
        assert config.database.port == 3308

    def test_config_database_url(self):
        """测试数据库URL生成"""
        from core.config import settings

        url = settings.database.url

        # 验证URL格式
        assert "mysql+pymysql://" in url
        assert "localhost:3308" in url
        assert "charset=utf8mb4" in url

    def test_config_redis_url(self):
        """测试Redis URL生成"""
        from core.config import settings

        url = settings.redis.url

        # 验证URL格式
        assert "redis://" in url
        assert "localhost:6379" in url

    def test_config_milvus(self):
        """测试Milvus配置"""
        from core.config import settings

        # 验证Milvus配置
        assert settings.milvus.host == "localhost"
        assert settings.milvus.port == 19530

    def test_config_rabbitmq(self):
        """测试RabbitMQ配置"""
        from core.config import settings

        # 验证RabbitMQ配置
        assert settings.rabbitmq.host == "localhost"
        assert settings.rabbitmq.port == 5672
        assert settings.rabbitmq.exchange.name == "rag_exchange"

    def test_config_document(self):
        """测试文档配置"""
        from core.config import settings

        # 验证文档配置
        assert "pdf" in settings.document.upload.allowed_extensions
        assert "docx" in settings.document.upload.allowed_extensions
        assert settings.document.upload.max_size == 104857600  # 100MB

    def test_config_chunk(self):
        """测试切分配置"""
        from core.config import settings

        # 验证切分配置
        assert settings.chunk.target_tokens == 600
        assert settings.chunk.max_tokens == 900
        assert settings.chunk.overlap_tokens == 100

    def test_config_embedding(self):
        """测试向量化配置"""
        from core.config import settings

        # 验证向量化配置
        assert settings.embedding.model_name == "Qwen3-Embedding"
        assert settings.embedding.dimension == 1024
