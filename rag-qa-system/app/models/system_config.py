"""
RAG 问答系统 - 系统配置模型
存储系统运行参数，支持运行时修改
"""

from datetime import datetime
from sqlalchemy import Column, BigInteger, String, Text, DateTime, Integer, Boolean, Index

from app.core.database import Base


class SystemConfig(Base):
    """
    系统配置表
    存储系统运行参数，支持运行时修改
    """
    __tablename__ = "system_configs"

    # 主键，自增ID
    id = Column(BigInteger, primary_key=True, autoincrement=True)

    # 配置键名（唯一）
    key = Column(String(100), nullable=False, unique=True, index=True, comment="配置键名")

    # 配置值
    value = Column(Text, nullable=True, comment="配置值")

    # 配置类型: string, number, boolean, json
    value_type = Column(String(20), default="string", nullable=False, comment="配置类型")

    # 配置分组
    group = Column(String(50), nullable=True, index=True, comment="配置分组")

    # 配置名称（中文）
    name = Column(String(100), nullable=True, comment="配置名称")

    # 配置描述
    description = Column(Text, nullable=True, comment="配置描述")

    # 是否可编辑
    editable = Column(Boolean, default=True, nullable=False, comment="是否可编辑")

    # 是否敏感配置（如密码）
    sensitive = Column(Boolean, default=False, nullable=False, comment="是否敏感配置")

    # 排序顺序
    sort_order = Column(Integer, default=0, nullable=False, comment="排序顺序")

    # 创建时间
    created_at = Column(DateTime, default=datetime.now, nullable=False, comment="创建时间")

    # 更新时间
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False, comment="更新时间")

    # 索引
    __table_args__ = (
        Index("idx_config_group", "group"),
        Index("idx_config_key_group", "key", "group"),
    )

    def __repr__(self):
        return f"<SystemConfig(key='{self.key}', value_type='{self.value_type}')>"

    def get_typed_value(self):
        """获取类型转换后的值"""
        if self.value is None:
            return None

        if self.value_type == "number":
            try:
                return float(self.value) if '.' in self.value else int(self.value)
            except (ValueError, TypeError):
                return self.value
        elif self.value_type == "boolean":
            return self.value.lower() in ('true', '1', 'yes', 'on')
        elif self.value_type == "json":
            import json
            try:
                return json.loads(self.value)
            except json.JSONDecodeError:
                return self.value
        else:
            return self.value

    def set_typed_value(self, value):
        """设置类型转换后的值"""
        if value is None:
            self.value = None
        elif self.value_type == "number":
            self.value = str(value)
        elif self.value_type == "boolean":
            self.value = "true" if value else "false"
        elif self.value_type == "json":
            import json
            self.value = json.dumps(value)
        else:
            self.value = str(value)


# 默认配置项
DEFAULT_CONFIGS = [
    # 应用配置
    {"key": "APP_ENV", "value": "development", "value_type": "string", "group": "app", "name": "应用环境", "description": "应用环境: development | production", "sort_order": 1},
    {"key": "APP_HOST", "value": "0.0.0.0", "value_type": "string", "group": "app", "name": "应用主机", "description": "应用主机地址", "sort_order": 2},
    {"key": "APP_PORT", "value": "8088", "value_type": "number", "group": "app", "name": "应用端口", "description": "应用端口", "sort_order": 3},
    {"key": "DEBUG", "value": "true", "value_type": "boolean", "group": "app", "name": "调试模式", "description": "是否开启调试模式", "sort_order": 4},
    {"key": "SECRET_KEY", "value": "", "value_type": "string", "group": "app", "name": "密钥", "description": "用于 JWT 等加密场景，请使用随机字符串", "sensitive": True, "sort_order": 5},
    {"key": "ALGORITHM", "value": "HS256", "value_type": "string", "group": "app", "name": "JWT 算法", "description": "JWT 算法", "sort_order": 6},
    {"key": "ACCESS_TOKEN_EXPIRE_MINUTES", "value": "30", "value_type": "number", "group": "app", "name": "访问令牌过期时间", "description": "访问令牌过期时间（分钟）", "sort_order": 7},

    # 数据库配置
    {"key": "MYSQL_HOST", "value": "localhost", "value_type": "string", "group": "database", "name": "MySQL 主机", "description": "MySQL 数据库主机地址", "sort_order": 10},
    {"key": "MYSQL_PORT", "value": "3308", "value_type": "number", "group": "database", "name": "MySQL 端口", "description": "MySQL 数据库端口", "sort_order": 11},
    {"key": "MYSQL_DATABASE", "value": "rag_qa", "value_type": "string", "group": "database", "name": "MySQL 数据库名", "description": "MySQL 数据库名称", "sort_order": 12},
    {"key": "MYSQL_USER", "value": "root", "value_type": "string", "group": "database", "name": "MySQL 用户名", "description": "MySQL 数据库用户名", "sort_order": 13},
    {"key": "MYSQL_PASSWORD", "value": "", "value_type": "string", "group": "database", "name": "MySQL 密码", "description": "MySQL 数据库密码", "sensitive": True, "sort_order": 14},

    # Redis 配置
    {"key": "REDIS_HOST", "value": "localhost", "value_type": "string", "group": "cache", "name": "Redis 主机", "description": "Redis 服务器地址", "sort_order": 20},
    {"key": "REDIS_PORT", "value": "6379", "value_type": "number", "group": "cache", "name": "Redis 端口", "description": "Redis 服务器端口", "sort_order": 21},
    {"key": "REDIS_DB", "value": "0", "value_type": "number", "group": "cache", "name": "Redis 数据库", "description": "Redis 数据库编号", "sort_order": 22},
    {"key": "REDIS_PASSWORD", "value": "", "value_type": "string", "group": "cache", "name": "Redis 密码", "description": "Redis 访问密码", "sensitive": True, "sort_order": 23},
    {"key": "CACHE_DEFAULT_TTL", "value": "3600", "value_type": "number", "group": "cache", "name": "缓存默认过期时间", "description": "缓存默认过期时间（秒）", "sort_order": 24},

    # DeepSeek API 配置
    {"key": "DEEPSEEK_API_KEY", "value": "", "value_type": "string", "group": "llm", "name": "DeepSeek API 密钥", "description": "DeepSeek API 密钥，从 https://platform.deepseek.com/ 获取", "sensitive": True, "sort_order": 30},
    {"key": "DEEPSEEK_BASE_URL", "value": "https://api.deepseek.com", "value_type": "string", "group": "llm", "name": "DeepSeek API 地址", "description": "DeepSeek API 基础 URL", "sort_order": 31},
    {"key": "DEEPSEEK_MODEL", "value": "deepseek-chat", "value_type": "string", "group": "llm", "name": "DeepSeek 模型", "description": "使用的模型名称", "sort_order": 32},
    {"key": "DEEPSEEK_TIMEOUT", "value": "60", "value_type": "number", "group": "llm", "name": "API 请求超时", "description": "API 请求超时时间（秒）", "sort_order": 33},

    # Milvus 配置
    {"key": "MILVUS_HOST", "value": "localhost", "value_type": "string", "group": "vector", "name": "Milvus 主机", "description": "Milvus 服务地址", "sort_order": 40},
    {"key": "MILVUS_PORT", "value": "19530", "value_type": "number", "group": "vector", "name": "Milvus 端口", "description": "Milvus 服务端口", "sort_order": 41},
    {"key": "MILVUS_USER", "value": "", "value_type": "string", "group": "vector", "name": "Milvus 用户名", "description": "Milvus 用户名（可选）", "sort_order": 42},
    {"key": "MILVUS_PASSWORD", "value": "", "value_type": "string", "group": "vector", "name": "Milvus 密码", "description": "Milvus 密码（可选）", "sensitive": True, "sort_order": 43},
    {"key": "MILVUS_COLLECTION_NAME", "value": "knowledge_base", "value_type": "string", "group": "vector", "name": "Collection 名称", "description": "向量数据库 Collection 名称", "sort_order": 44},

    # Embedding 配置
    {"key": "EMBEDDING_MODEL", "value": "sentence-transformers/all-MiniLM-L6-v2", "value_type": "string", "group": "embedding", "name": "Embedding 模型", "description": "sentence-transformers 模型名称", "sort_order": 50},
    {"key": "EMBEDDING_DEVICE", "value": "cpu", "value_type": "string", "group": "embedding", "name": "Embedding 设备", "description": "运行设备: cpu | cuda | mps", "sort_order": 51},
    {"key": "EMBEDDING_DIMENSION", "value": "384", "value_type": "number", "group": "embedding", "name": "向量维度", "description": "向量维度（all-MiniLM-L6-v2 为 384）", "sort_order": 52},

    # 文本切分配置
    {"key": "CHUNK_SIZE", "value": "500", "value_type": "number", "group": "chunking", "name": "文本块大小", "description": "文本块最大字符数", "sort_order": 60},
    {"key": "CHUNK_OVERLAP", "value": "50", "value_type": "number", "group": "chunking", "name": "文本块重叠", "description": "文本块重叠字符数", "sort_order": 61},
    {"key": "CHUNK_MIN_SIZE", "value": "50", "value_type": "number", "group": "chunking", "name": "最小块大小", "description": "最小块字符数（过滤过短块）", "sort_order": 62},

    # 向量检索配置
    {"key": "RETRIEVAL_TOP_K", "value": "5", "value_type": "number", "group": "retrieval", "name": "检索数量", "description": "检索返回的最相关文档数量", "sort_order": 70},
    {"key": "SIMILARITY_THRESHOLD", "value": "0.2", "value_type": "number", "group": "retrieval", "name": "相似度阈值", "description": "相似度阈值（低于此值的检索结果将被过滤）", "sort_order": 71},
    {"key": "ENABLE_MMR", "value": "false", "value_type": "boolean", "group": "retrieval", "name": "启用 MMR", "description": "是否启用多路召回（Max Marginal Relevance）", "sort_order": 72},
    {"key": "MMR_DIVERSITY", "value": "0.5", "value_type": "number", "group": "retrieval", "name": "MMR 多样性", "description": "MMR diversity 参数（仅在启用 MMR 时生效）", "sort_order": 73},

    # 文件上传配置
    {"key": "UPLOAD_DIR", "value": "./data/documents", "value_type": "string", "group": "upload", "name": "文档存储目录", "description": "文档存储目录", "sort_order": 80},
    {"key": "MAX_FILE_SIZE", "value": "10485760", "value_type": "number", "group": "upload", "name": "最大文件大小", "description": "单文件最大大小（字节）", "sort_order": 81},

    # 日志配置
    {"key": "LOG_LEVEL", "value": "INFO", "value_type": "string", "group": "logging", "name": "日志级别", "description": "日志级别: DEBUG | INFO | WARNING | ERROR | CRITICAL", "sort_order": 90},
    {"key": "LOG_CONSOLE", "value": "true", "value_type": "boolean", "group": "logging", "name": "控制台日志", "description": "是否在控制台输出日志", "sort_order": 91},

    # CORS 配置
    {"key": "CORS_ORIGINS", "value": "http://localhost:3000,http://localhost:8080", "value_type": "string", "group": "cors", "name": "允许的来源", "description": "允许的来源（多个用逗号分隔）", "sort_order": 100},
]

# 配置分组名称映射
CONFIG_GROUP_NAMES = {
    "app": "应用配置",
    "database": "数据库配置",
    "cache": "缓存配置",
    "llm": "大模型配置",
    "vector": "向量数据库配置",
    "embedding": "Embedding 配置",
    "chunking": "文本切分配置",
    "retrieval": "检索配置",
    "upload": "文件上传配置",
    "logging": "日志配置",
    "cors": "跨域配置",
}
