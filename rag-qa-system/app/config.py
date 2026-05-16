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
    
    # ============ MySQL 数据库配置 ============
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
    embedding_model: str = Field(default="sentence-transformers/all-MiniLM-L6-v2", description="Embedding 模型名称")
    embedding_device: str = Field(default="cpu", description="运行设备: cpu | cuda | mps")
    embedding_dimension: int = Field(default=384, description="向量维度")
    embedding_batch_size: int = Field(default=32, description="批量处理大小")
    
    # ============ 文本切分配置 ============
    chunk_size: int = Field(default=500, description="文本块最大字符数")
    chunk_overlap: int = Field(default=50, description="文本块重叠字符数")
    chunk_min_size: int = Field(default=50, description="最小块字符数")
    
    # ============ 向量检索配置 ============
    retrieval_top_k: int = Field(default=5, description="检索返回数量")
    similarity_threshold: float = Field(default=0.2, description="相似度阈值")
    enable_mmr: bool = Field(default=False, description="启用 MMR")
    mmr_diversity: float = Field(default=0.5, description="MMR diversity 参数")
    
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
    log_file_path: str = Field(default="./logs/rag_qa.log", description="日志文件路径")
    log_file_max_size: int = Field(default=10485760, description="日志文件最大大小（字节）")
    log_file_backup_count: int = Field(default=5, description="日志文件保留数量")
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
