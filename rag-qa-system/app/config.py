"""
RAG 问答系统 - 配置管理模块
配置文件读取、环境变量管理
"""

import os
from pathlib import Path
from typing import List, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    应用配置类
    使用 Pydantic Settings 进行配置管理，支持从 .env 文件读取
    """
    
    # ============ 应用配置 ============
    app_env: str = Field(default="development", description="应用环境: development | production")
    app_host: str = Field(default="0.0.0.0", description="应用主机地址")
    app_port: int = Field(default=8000, description="应用端口")
    debug: bool = Field(default=True, description="调试模式")
    api_v1_prefix: str = Field(default="/api/v1", description="API v1 前缀")
    secret_key: str = Field(default="your-secret-key-change-in-production", description="密钥")
    algorithm: str = Field(default="HS256", description="JWT 算法")
    access_token_expire_minutes: int = Field(default=30, description="访问令牌过期时间（分钟）")
    mysql_host: str = Field(default="localhost", description="MySQL 主机")
    mysql_port: int = Field(default=3306, description="MySQL 端口")
    mysql_database: str = Field(default="rag_qa", description="MySQL 数据库名")
    mysql_user: str = Field(default="root", description="MySQL 用户名")
    mysql_password: str = Field(default="", description="MySQL 密码")
    mysql_pool_size: int = Field(default=10, description="连接池大小")
    mysql_max_overflow: int = Field(default=20, description="连接池最大溢出")
    
    @property
    def mysql_url(self) -> str:
        """获取 MySQL 连接 URL"""
        return f"mysql+pymysql://{self.mysql_user}:{self.mysql_password}@{self.mysql_host}:{self.mysql_port}/{self.mysql_database}"
    
    @property
    def async_mysql_url(self) -> str:
        """获取异步 MySQL 连接 URL"""
        return f"mysql+aiomysql://{self.mysql_user}:{self.mysql_password}@{self.mysql_host}:{self.mysql_port}/{self.mysql_database}"
    
    # ============ Redis 缓存配置 ============
    redis_host: str = Field(default="localhost", description="Redis 主机")
    redis_port: int = Field(default=6379, description="Redis 端口")
    redis_db: int = Field(default=0, description="Redis 数据库号")
    redis_password: Optional[str] = Field(default=None, description="Redis 密码")
    redis_key_prefix: str = Field(default="rag_qa:", description="Redis 键前缀")
    cache_default_ttl: int = Field(default=3600, description="缓存默认过期时间（秒）")
    
    # ============ DeepSeek API 配置 ============
    deepseek_api_key: str = Field(default="", description="DeepSeek API 密钥")
    deepseek_base_url: str = Field(default="https://api.deepseek.com", description="DeepSeek API 基础 URL")
    deepseek_model: str = Field(default="deepseek-chat", description="DeepSeek 模型名称")
    deepseek_timeout: int = Field(default=60, description="API 请求超时时间（秒）")
    deepseek_max_retries: int = Field(default=3, description="最大重试次数")
    
    # ============ Milvus 向量数据库配置 ============
    milvus_host: str = Field(default="localhost", description="Milvus 主机")
    milvus_port: int = Field(default=19530, description="Milvus 端口")
    milvus_user: str = Field(default="", description="Milvus 用户名")
    milvus_password: str = Field(default="", description="Milvus 密码")
    milvus_collection_name: str = Field(default="knowledge_base", description="Collection 名称")
    milvus_index_type: str = Field(default="IVF_FLAT", description="索引类型")
    milvus_metric_type: str = Field(default="IP", description="度量类型 (L2/IP/COSINE)")
    milvus_nlist: int = Field(default=1024, description="nlist 参数")
    
    # ============ Embedding 模型配置 ============
    embedding_provider: str = Field(default="ollama", description="Embedding 提供者: ollama | sentence_transformers")
    embedding_model: str = Field(default="batiai/qwen3-embedding:4b-q6", description="Embedding 模型名称 (Ollama 模型名)")
    embedding_device: str = Field(default="cpu", description="运行设备: cpu | cuda | mps (仅 sentence_transformers 使用)")
    embedding_dimension: int = Field(default=2560, description="向量维度 (Ollama qwen3-embedding-4b 输出 2560)")
    embedding_batch_size: int = Field(default=32, description="批量处理大小")
    # Ollama 特有配置
    embedding_base_url: str = Field(default="http://localhost:11434", description="Ollama API 基础 URL")
    embedding_timeout: int = Field(default=60, description="Embedding 请求超时时间（秒）")
    embedding_max_retries: int = Field(default=3, description="Embedding 最大重试次数")

    # ============ Reranker 配置 ============
    reranker_enabled: bool = Field(default=False, description="是否启用 Reranker")
    reranker_model: str = Field(default="bantai/qwen3-reranker:1.5b-q4", description="Reranker 模型名称 (Ollama 模型名)")
    reranker_base_url: str = Field(default="http://localhost:11434", description="Reranker API 基础 URL")
    reranker_timeout: int = Field(default=30, description="Reranker 请求超时时间（秒）")
    reranker_max_retries: int = Field(default=2, description="Reranker 最大重试次数")
    reranker_recall_k: int = Field(default=50, description="Reranker 召回数量（rerank 前从 Milvus 召回的数量）")
    reranker_top_k: int = Field(default=10, description="Reranker 输出数量（rerank 后返回给 LLM 的数量）")

    # ============ Sparse/BM25 配置 ============
    sparse_enabled: bool = Field(default=False, description="是否启用 Sparse 检索")
    sparse_weight: float = Field(default=0.3, description="Sparse 检索权重（用于与 dense 检索结果融合）")
    bm25_k1: float = Field(default=1.5, description="BM25 参数 k1")
    bm25_b: float = Field(default=0.75, description="BM25 参数 b")
    rrf_k: int = Field(default=60, description="RRF 融合参数 k（用于 Reciprocal Rank Fusion）")

    # ============ SemanticChunker 配置 ============
    chunk_target_tokens: int = Field(default=600, description="Chunk 目标 token 数")
    chunk_max_tokens: int = Field(default=900, description="Chunk 最大 token 数")
    chunk_min_tokens: int = Field(default=120, description="Chunk 最小 token 数")
    chunk_overlap_tokens: int = Field(default=100, description="Chunk overlap token 数")
    chunk_version: str = Field(default="semantic-v1", description="Chunk 版本号")

    # ============ 文件上传配置 ============
    upload_dir: str = Field(default="./data/documents", description="文档存储目录")
    allowed_extensions: str = Field(default="pdf,md,txt,docx", description="允许的文件扩展名")
    max_file_size: int = Field(default=10485760, description="单文件最大大小（字节）")
    max_concurrent_uploads: int = Field(default=5, description="最大并发上传数")
    
    @property
    def allowed_extensions_list(self) -> List[str]:
        """获取允许的文件扩展名列表"""
        return [ext.strip() for ext in self.allowed_extensions.split(",")]
    
    # ============ 日志配置 ============
    log_level: str = Field(default="INFO", description="日志级别")
    log_format: str = Field(default="json", description="日志格式: json | console")
    log_file_path: str = Field(default="./logs/rag_qa.log", description="日志文件路径（实际文件名为 rag_qa.YYYY-MM-DD.log）")
    log_file_max_size: int = Field(default=10485760, description="日志文件最大大小（字节）")
    log_file_backup_count: int = Field(default=5, description="日志文件保留天数")
    log_console: bool = Field(default=True, description="是否在控制台输出日志")
    
    # ============ CORS 跨域配置 ============
    cors_origins: str = Field(default="http://localhost:3000,http://localhost:8080", description="允许的来源")
    cors_allow_credentials: bool = Field(default=True, description="允许凭据")
    cors_allow_methods: str = Field(default="GET,POST,PUT,DELETE,OPTIONS", description="允许的 HTTP 方法")
    cors_allow_headers: str = Field(default="*", description="允许的 HTTP 头")
    
    @property
    def cors_origins_list(self) -> List[str]:
        """获取 CORS 允许的来源列表"""
        return [origin.strip() for origin in self.cors_origins.split(",")]
    
    @property
    def cors_allow_methods_list(self) -> List[str]:
        """获取 CORS 允许的 HTTP 方法列表"""
        return [method.strip() for method in self.cors_allow_methods.split(",")]
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 确保必要的目录存在
        self._ensure_directories()
    
    def _ensure_directories(self):
        """确保必要的目录存在"""
        dirs = [
            self.upload_dir,
            os.path.dirname(self.log_file_path) if self.log_file_path else None,
        ]
        for dir_path in dirs:
            if dir_path:
                Path(dir_path).mkdir(parents=True, exist_ok=True)


# 全局配置实例
settings = Settings()


def get_settings() -> Settings:
    """获取配置实例（用于依赖注入）"""
    return settings
