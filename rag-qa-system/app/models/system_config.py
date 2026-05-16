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

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    key = Column(String(100), nullable=False, unique=True, index=True, comment="配置键名")
    value = Column(Text, nullable=True, comment="配置值")
    value_type = Column(String(20), default="string", nullable=False, comment="配置类型")
    group = Column(String(50), nullable=True, index=True, comment="配置分组")
    name = Column(String(100), nullable=True, comment="配置名称")
    description = Column(Text, nullable=True, comment="配置描述")
    editable = Column(Boolean, default=True, nullable=False, comment="是否可编辑")
    sensitive = Column(Boolean, default=False, nullable=False, comment="是否敏感配置")
    sort_order = Column(Integer, default=0, nullable=False, comment="排序顺序")
    created_at = Column(DateTime, default=datetime.now, nullable=False, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False, comment="更新时间")

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


# 只保留从 .env 无法获得的运行时可调配置
DEFAULT_CONFIGS = [
    # 检索配置
    {"key": "RETRIEVAL_TOP_K", "value": "5", "value_type": "number", "group": "retrieval", "name": "检索数量", "description": "检索返回的最相关文档数量", "sort_order": 1},
    {"key": "SIMILARITY_THRESHOLD", "value": "0.2", "value_type": "number", "group": "retrieval", "name": "相似度阈值", "description": "相似度阈值（低于此值的检索结果将被过滤）", "sort_order": 2},
    {"key": "ENABLE_MMR", "value": "false", "value_type": "boolean", "group": "retrieval", "name": "启用 MMR", "description": "是否启用多路召回（Max Marginal Relevance）", "sort_order": 3},
    {"key": "MMR_DIVERSITY", "value": "0.5", "value_type": "number", "group": "retrieval", "name": "MMR 多样性", "description": "MMR diversity 参数（仅在启用 MMR 时生效）", "sort_order": 4},

    # 文本切分配置
    {"key": "CHUNK_SIZE", "value": "500", "value_type": "number", "group": "chunking", "name": "文本块大小", "description": "文本块最大字符数", "sort_order": 10},
    {"key": "CHUNK_OVERLAP", "value": "50", "value_type": "number", "group": "chunking", "name": "文本块重叠", "description": "文本块重叠字符数", "sort_order": 11},
    {"key": "CHUNK_MIN_SIZE", "value": "50", "value_type": "number", "group": "chunking", "name": "最小块大小", "description": "最小块字符数（过滤过短块）", "sort_order": 12},

    # 访问令牌过期时间
    {"key": "ACCESS_TOKEN_EXPIRE_MINUTES", "value": "30", "value_type": "number", "group": "app", "name": "访问令牌过期时间", "description": "访问令牌过期时间（分钟）", "sort_order": 20},
]

CONFIG_GROUP_NAMES = {
    "retrieval": "检索配置",
    "chunking": "文本切分配置",
    "app": "应用配置",
}
