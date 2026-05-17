"""
RAG 问答系统 - 配置测试模块
测试配置加载和管理功能
"""

import pytest
from app.config import Settings


class TestSettings:
    """配置测试类"""
    
    def test_default_values(self):
        """测试配置加载"""
        settings = Settings()

        assert settings.app_env == "development"
        assert settings.app_port == 8088
        assert settings.debug == True
        assert settings.mysql_host == "localhost"
        assert settings.redis_host == "localhost"
        assert settings.embedding_provider == "ollama"
        assert settings.reranker_enabled == False
    
    def test_mysql_url(self):
        """测试 MySQL URL 生成"""
        settings = Settings()
        
        url = settings.mysql_url
        assert "mysql+pymysql://" in url
        assert settings.mysql_host in url
    
    def test_async_mysql_url(self):
        """测试异步 MySQL URL 生成"""
        settings = Settings()
        
        url = settings.async_mysql_url
        assert "mysql+aiomysql://" in url
    
    def test_allowed_extensions_list(self):
        """测试允许扩展名列表"""
        settings = Settings()
        
        extensions = settings.allowed_extensions_list
        assert "pdf" in extensions
        assert "md" in extensions
        assert "txt" in extensions
    
    def test_cors_origins_list(self):
        """测试 CORS 来源列表"""
        settings = Settings()
        
        origins = settings.cors_origins_list
        assert len(origins) > 0
    
    def test_redis_key_prefix(self):
        """测试 Redis 键前缀"""
        settings = Settings()

        assert settings.redis_key_prefix.endswith(":")
