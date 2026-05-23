# -*- coding: utf-8 -*-
"""
核心配置模块

本模块提供应用程序配置管理功能：
1. 从YAML文件加载多环境配置
2. 支持环境变量覆盖敏感信息
3. 提供类型安全的配置访问接口
4. 支持local/dev/prod三种环境

配置加载顺序：
1. 加载application-base.yml（基础配置）
2. 加载application-{ENV}.yml（环境配置）
3. 环境变量覆盖敏感信息

使用示例：
    from core.config import settings
    print(settings.database.host)
    print(settings.app.name)
"""

import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from pydantic import BaseModel, ConfigDict, Field


class ServerConfig(BaseModel):
    """服务器配置"""
    port: int = Field(default=8011, description="服务端口")
    host: str = Field(default="127.0.0.1", description="服务地址")
    reload: bool = Field(default=False, description="是否启用热重载")
    workers: int = Field(default=1, description="工作进程数")


class DatabaseConfig(BaseModel):
    """数据库配置"""
    host: str = Field(default="localhost", description="数据库主机")
    port: int = Field(default=3308, description="数据库端口")
    username: str = Field(default="root", description="数据库用户名")
    password: str = Field(default="", description="数据库密码")
    name: str = Field(default="rag_db", description="数据库名称")
    charset: str = Field(default="utf8mb4", description="字符集")
    pool_size: int = Field(default=5, description="连接池大小")
    max_overflow: int = Field(default=10, description="连接池最大溢出")
    pool_recycle: int = Field(default=3600, description="连接回收时间(秒)")
    echo: bool = Field(default=False, description="是否打印SQL语句")

    @property
    def url(self) -> str:
        """生成数据库连接URL"""
        return (
            f"mysql+pymysql://{self.username}:{self.password}@"
            f"{self.host}:{self.port}/{self.name}?charset={self.charset}"
        )


class RedisConfig(BaseModel):
    """Redis配置"""
    host: str = Field(default="localhost", description="Redis主机")
    port: int = Field(default=6379, description="Redis端口")
    password: str = Field(default="", description="Redis密码")
    db: int = Field(default=0, description="数据库编号")
    decode_responses: bool = Field(default=True, description="是否解码响应")
    socket_timeout: int = Field(default=5, description="Socket超时(秒)")
    socket_connect_timeout: int = Field(default=5, description="Socket连接超时(秒)")

    @property
    def url(self) -> str:
        """生成Redis连接URL"""
        if self.password:
            return f"redis://:{self.password}@{self.host}:{self.port}/{self.db}"
        return f"redis://{self.host}:{self.port}/{self.db}"


class MilvusConfig(BaseModel):
    """Milvus向量数据库配置"""
    host: str = Field(default="localhost", description="Milvus主机")
    port: int = Field(default=19530, description="Milvus端口")
    timeout: int = Field(default=30, description="超时时间(秒)")
    pool_size: int = Field(default=10, description="连接池大小")
    alias: str = Field(default="default", description="连接别名")


class RabbitMQExchangeConfig(BaseModel):
    """RabbitMQ交换机配置"""
    name: str = Field(default="rag_exchange", description="交换机名称")
    type: str = Field(default="topic", description="交换机类型")
    durable: bool = Field(default=True, description="是否持久化")


class RabbitMQQueueConfig(BaseModel):
    """RabbitMQ队列配置"""
    name: str = Field(description="队列名称")
    routing_key: str = Field(description="路由键")
    durable: bool = Field(default=True, description="是否持久化")


class RabbitMQDeadLetterConfig(BaseModel):
    """RabbitMQ死信队列配置"""
    exchange: str = Field(default="rag_dlx_exchange", description="死信交换机名称")
    queue: str = Field(default="rag_dlx_queue", description="死信队列名称")
    routing_key: str = Field(default="dlx", description="死信路由键")
    durable: bool = Field(default=True, description="是否持久化")


class RabbitMQConfig(BaseModel):
    """RabbitMQ消息队列配置"""
    host: str = Field(default="localhost", description="RabbitMQ主机")
    port: int = Field(default=5672, description="RabbitMQ端口")
    username: str = Field(default="guest", description="用户名")
    password: str = Field(default="guest", description="密码")
    virtual_host: str = Field(default="/", description="虚拟主机")
    heartbeat: int = Field(default=600, description="心跳间隔(秒)")
    connection_timeout: int = Field(default=30, description="连接超时(秒)")
    pool_size: int = Field(default=5, description="连接池大小")
    max_channels_per_connection: int = Field(default=100, description="每个连接最大信道数")
    exchange: RabbitMQExchangeConfig = Field(default_factory=RabbitMQExchangeConfig)
    queues: Dict[str, RabbitMQQueueConfig] = Field(default_factory=dict)
    dead_letter: RabbitMQDeadLetterConfig = Field(default_factory=RabbitMQDeadLetterConfig)


class AppConfig(BaseModel):
    """应用配置"""
    name: str = Field(default="RAG知识库系统", description="应用名称")
    version: str = Field(default="1.0.0", description="应用版本")
    debug: bool = Field(default=False, description="是否调试模式")
    env: str = Field(default="local", description="运行环境")
    description: str = Field(default="RAG知识库系统后端API服务", description="应用描述")


class LoggingFileConfig(BaseModel):
    """日志文件配置"""
    enabled: bool = Field(default=True, description="是否启用文件日志")
    path: str = Field(default="./logs/app.log", description="日志文件路径")
    max_bytes: int = Field(default=10485760, description="单个日志文件最大大小")
    backup_count: int = Field(default=5, description="保留的日志文件数量")


class LoggingConsoleConfig(BaseModel):
    """日志控制台配置"""
    enabled: bool = Field(default=True, description="是否启用控制台日志")


class LoggingConfig(BaseModel):
    """日志配置"""
    level: str = Field(default="INFO", description="日志级别")
    format: str = Field(default="json", description="日志格式")
    audit_enabled: bool = Field(default=True, description="是否启用审计日志")
    file: LoggingFileConfig = Field(default_factory=LoggingFileConfig)
    console: LoggingConsoleConfig = Field(default_factory=LoggingConsoleConfig)


class CorsConfig(BaseModel):
    """CORS跨域配置"""
    enabled: bool = Field(default=True, description="是否启用CORS")
    allow_origins: List[str] = Field(default_factory=list, description="允许的源")
    allow_methods: List[str] = Field(default_factory=list, description="允许的方法")
    allow_headers: List[str] = Field(default_factory=list, description="允许的头")
    allow_credentials: bool = Field(default=True, description="是否允许凭证")


class ApiConfig(BaseModel):
    """API文档配置"""
    title: str = Field(default="RAG知识库系统API", description="API标题")
    description: str = Field(default="基于FastAPI的RAG知识库系统后端接口", description="API描述")
    version: str = Field(default="1.0.0", description="API版本")
    prefix: str = Field(default="/api/v1", description="API前缀")
    docs_url: str = Field(default="/docs", description="Swagger文档URL")
    redoc_url: str = Field(default="/redoc", description="ReDoc文档URL")


class DocumentUploadConfig(BaseModel):
    """文档上传配置"""
    max_size: int = Field(default=104857600, description="最大文件大小(字节)")
    allowed_extensions: List[str] = Field(
        default_factory=lambda: ["pdf", "docx", "doc", "txt", "md", "html", "xlsx", "xls"],
        description="允许的文件扩展名"
    )


class DocumentStorageConfig(BaseModel):
    """文档存储配置"""
    base_path: str = Field(default="./data/uploads", description="基础存储路径")
    temp_path: str = Field(default="./data/temp", description="临时文件路径")


class DocumentParsingConfig(BaseModel):
    """文档解析配置"""
    ocr_enabled: bool = Field(default=True, description="是否启用OCR")
    ocr_language: str = Field(default="chn_sim", description="OCR语言")
    max_pages: int = Field(default=1000, description="最大页数")


class DocumentConfig(BaseModel):
    """文档处理配置"""
    upload: DocumentUploadConfig = Field(default_factory=DocumentUploadConfig)
    storage: DocumentStorageConfig = Field(default_factory=DocumentStorageConfig)
    parsing: DocumentParsingConfig = Field(default_factory=DocumentParsingConfig)


class ChunkConfig(BaseModel):
    """文档切分配置"""
    target_tokens: int = Field(default=600, description="目标Token数")
    max_tokens: int = Field(default=900, description="最大Token数")
    min_tokens: int = Field(default=120, description="最小Token数")
    overlap_tokens: int = Field(default=100, description="重叠Token数")
    semantic_threshold: float = Field(default=0.85, description="语义切分阈值")


class EmbeddingConfig(BaseModel):
    """向量化配置"""
    model_config = ConfigDict(protected_namespaces=())
    
    model_name: str = Field(default="Qwen3-Embedding", description="模型名称")
    dimension: int = Field(default=1024, description="向量维度")
    batch_size: int = Field(default=32, description="批处理大小")
    cache_enabled: bool = Field(default=True, description="是否启用缓存")
    cache_ttl: int = Field(default=86400, description="缓存TTL(秒)")
    
    # Ollama 相关配置
    use_ollama: bool = Field(default=True, description="是否使用 Ollama 向量化服务")
    ollama_host: str = Field(default="http://localhost:11434", description="Ollama 服务地址")
    ollama_timeout: int = Field(default=120, description="Ollama 请求超时时间(秒)")
    ollama_retry_times: int = Field(default=3, description="Ollama 重试次数")
    fallback_to_mock: bool = Field(default=True, description="Ollama 不可用时降级到 Mock")


class RetrievalConfig(BaseModel):
    """检索配置"""
    vector_top_k: int = Field(default=100, description="向量检索TopK")
    keyword_top_k: int = Field(default=100, description="关键词检索TopK")
    rrf_k: int = Field(default=60, description="RRF融合参数k")
    fusion_top_k: int = Field(default=20, description="融合后TopK")
    rerank_top_k: int = Field(default=10, description="重排后TopK")
    vector_weight: float = Field(default=0.6, description="向量权重")
    keyword_weight: float = Field(default=0.4, description="关键词权重")


class QueryRewriteConfig(BaseModel):
    """查询改写配置"""
    enable_normalize: bool = Field(default=True, description="是否启用规范化")
    enable_multi_query: bool = Field(default=True, description="是否启用多查询生成")
    enable_subquery: bool = Field(default=True, description="是否启用子查询分解")
    enable_hyde: bool = Field(default=False, description="是否启用HyDE")
    enable_background: bool = Field(default=False, description="是否启用后退提示")
    use_llm: bool = Field(default=False, description="是否使用LLM增强")
    max_queries: int = Field(default=5, ge=1, le=10, description="最大生成查询数量")
    remove_stopwords: bool = Field(default=True, description="是否移除停用词")


class JWTConfig(BaseModel):
    """JWT认证配置"""
    secret_key: str = Field(default="change-me-in-production", description="密钥")
    algorithm: str = Field(default="HS256", description="加密算法")
    access_token_expire_minutes: int = Field(default=120, description="访问令牌过期时间(分钟)")
    refresh_token_expire_days: int = Field(default=7, description="刷新令牌过期时间(天)")


class LLMConfig(BaseModel):
    """LLM大语言模型配置"""
    model_config = ConfigDict(protected_namespaces=())

    provider: str = Field(default="deepseek", description="LLM提供商: deepseek/openai/zhipu/qwen")
    api_key: str = Field(default="", description="API密钥")
    model_name: str = Field(default="deepseek-chat", description="模型名称")
    base_url: str = Field(default="https://api.deepseek.com", description="API地址")
    max_tokens: int = Field(default=4000, description="最大Token数")
    temperature: float = Field(default=0.7, description="温度参数")
    timeout: int = Field(default=120, description="请求超时(秒)")


class VisionConfig(BaseModel):
    """视觉模型配置"""
    model_config = ConfigDict(protected_namespaces=())

    model_name: str = Field(default="qwen2.5-ocr", description="视觉模型名称")
    ollama_host: str = Field(default="http://localhost:11434", description="Ollama 服务地址")
    timeout: int = Field(default=180, description="请求超时时间(秒)")
    retry_times: int = Field(default=3, description="重试次数")
    enabled: bool = Field(default=True, description="是否启用视觉描述生成")


class CacheConfig(BaseModel):
    """缓存配置"""
    embedding: Dict[str, Any] = Field(default_factory=lambda: {"ttl": 86400, "max_size": 10000})
    query: Dict[str, Any] = Field(default_factory=lambda: {"ttl": 3600, "max_size": 5000})


class Settings(BaseModel):
    """应用程序配置"""
    server: ServerConfig = Field(default_factory=ServerConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    redis: RedisConfig = Field(default_factory=RedisConfig)
    milvus: MilvusConfig = Field(default_factory=MilvusConfig)
    rabbitmq: RabbitMQConfig = Field(default_factory=RabbitMQConfig)
    app: AppConfig = Field(default_factory=AppConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    cors: CorsConfig = Field(default_factory=CorsConfig)
    api: ApiConfig = Field(default_factory=ApiConfig)
    document: DocumentConfig = Field(default_factory=DocumentConfig)
    chunk: ChunkConfig = Field(default_factory=ChunkConfig)
    embedding: EmbeddingConfig = Field(default_factory=EmbeddingConfig)
    retrieval: RetrievalConfig = Field(default_factory=RetrievalConfig)
    query_rewrite: QueryRewriteConfig = Field(default_factory=QueryRewriteConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    vision: VisionConfig = Field(default_factory=VisionConfig)
    jwt: JWTConfig = Field(default_factory=JWTConfig)
    cache: CacheConfig = Field(default_factory=CacheConfig)


def _resolve_env_vars(value: Any) -> Any:
    """
    递归解析环境变量引用

    支持格式：
    - ${ENV_VAR} - 必填环境变量
    - ${ENV_VAR:default} - 带默认值的环境变量
    """
    if isinstance(value, str):
        pattern = r'\$\{([^}:]+)(?::([^}]*))?\}'

        def replace_env_var(match):
            env_var = match.group(1)
            default_value = match.group(2)
            env_value = os.environ.get(env_var)

            if env_value is not None:
                return env_value
            elif default_value is not None:
                return default_value
            else:
                # 如果是必填环境变量且未设置，返回原字符串以便后续检查
                return match.group(0)

        resolved = re.sub(pattern, replace_env_var, value)

        # 检查是否有未解析的环境变量引用
        if '${' in resolved:
            # 尝试从环境变量获取
            unresolved_vars = re.findall(r'\$\{([^}]+)\}', resolved)
            for var in unresolved_vars:
                if var in os.environ:
                    resolved = resolved.replace(f'${{{var}}}', os.environ[var])

        return resolved
    elif isinstance(value, dict):
        return {k: _resolve_env_vars(v) for k, v in value.items()}
    elif isinstance(value, list):
        return [_resolve_env_vars(item) for item in value]
    else:
        return value


def _load_yaml_config(env: str = None) -> Dict[str, Any]:
    """
    加载YAML配置文件

    Args:
        env: 运行环境标识 (local/dev/prod)

    Returns:
        配置字典
    """
    # 确定环境
    if env is None:
        env = os.environ.get("APP_ENV", "local")

    # 获取配置文件路径
    config_dir = Path(__file__).parent.parent.parent / "resources"
    base_config_path = config_dir / "application.yml"
    env_config_path = config_dir / f"application-{env}.yml"

    config = {}

    # 加载基础配置（如果存在）
    if base_config_path.exists():
        with open(base_config_path, "r", encoding="utf-8") as f:
            base_config = yaml.safe_load(f)
            if base_config:
                config.update(base_config)

    # 加载环境配置
    if env_config_path.exists():
        with open(env_config_path, "r", encoding="utf-8") as f:
            env_config = yaml.safe_load(f)
            if env_config:
                # 深度合并配置
                for key, value in env_config.items():
                    if key in config and isinstance(config[key], dict) and isinstance(value, dict):
                        config[key].update(value)
                    else:
                        config[key] = value

    # 解析环境变量引用
    config = _resolve_env_vars(config)

    return config


# 全局配置实例
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """
    获取配置实例（单例模式）

    Returns:
        Settings配置实例
    """
    global _settings
    if _settings is None:
        _settings = Settings(**_load_yaml_config())
    return _settings


def reload_settings() -> Settings:
    """
    重新加载配置

    Returns:
        新的Settings配置实例
    """
    global _settings
    _settings = Settings(**_load_yaml_config())
    return _settings


# 创建全局配置实例
settings = get_settings()
