# -*- coding: utf-8 -*-
"""
清洗相关数据模型

本模块定义清洗服务相关的数据模型：
- CleaningRule: 清洗规则表
- CleaningLog: 清洗日志表
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, DateTime, Integer, String, Text, BigInteger, Index, JSON
from sqlalchemy.orm import relationship

from core.database import Base


class CleaningRule(Base):
    """
    清洗规则表

    存储文档清洗的规则配置，支持正则删除、正则替换、结构删除、质量控制、脱敏等类型。
    """
    __tablename__ = "cleaning_rules"

    # 主键ID
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="规则主键ID")

    # 规则名称
    name = Column(String(100), nullable=False, comment="规则名称")

    # 规则类型：regex_delete/regex_replace/struct_delete/quality_control/desensitization
    rule_type = Column(String(50), nullable=False, comment="规则类型")

    # 规则配置（JSON格式）
    rule_config = Column(JSON, nullable=False, comment="规则配置")

    # 优先级（数字越小越优先）
    priority = Column(Integer, default=100, nullable=False, comment="优先级")

    # 是否启用：0-禁用 1-启用
    is_enabled = Column(Integer, default=1, nullable=False, comment="是否启用")

    # 适用范围：all/pdf/docx/image/table
    scope = Column(String(100), nullable=True, comment="适用范围")

    # 业务范围筛选
    business_scope = Column(String(255), nullable=True, comment="业务范围筛选")

    # 规则说明
    description = Column(String(500), nullable=True, comment="规则说明")

    # 生效次数
    effect_count = Column(Integer, default=0, nullable=False, comment="生效次数")

    # 创建人ID
    creator_id = Column(BigInteger, nullable=True, comment="创建人ID")

    # 创建人姓名
    creator_name = Column(String(100), nullable=True, comment="创建人姓名")

    # 创建时间
    created_at = Column(DateTime, default=datetime.now, nullable=False, comment="创建时间")

    # 更新时间
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False, comment="更新时间")

    # 是否删除
    is_deleted = Column(Integer, default=0, nullable=False, comment="是否删除")

    # 索引定义
    __table_args__ = (
        Index("idx_cleaning_rule_type", "rule_type"),
        Index("idx_cleaning_is_enabled", "is_enabled"),
        Index("idx_cleaning_priority", "priority"),
    )

    def __repr__(self) -> str:
        """返回规则对象的字符串表示"""
        return f"<CleaningRule(id={self.id}, name={self.name}, type={self.rule_type})>"


class CleaningLog(Base):
    """
    清洗日志表

    记录文档清洗过程的日志信息，包括处理的元素、应用的规则、修改前后内容等。
    """
    __tablename__ = "cleaning_logs"

    # 主键ID
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="日志主键ID")

    # 文档ID
    document_id = Column(BigInteger, nullable=False, comment="文档ID")

    # 版本ID
    version_id = Column(BigInteger, nullable=False, comment="版本ID")

    # 元素ID
    element_id = Column(String(64), nullable=True, comment="元素ID")

    # 规则ID
    rule_id = Column(BigInteger, nullable=True, comment="规则ID")

    # 规则名称
    rule_name = Column(String(100), nullable=True, comment="规则名称")

    # 规则类型
    rule_type = Column(String(50), nullable=True, comment="规则类型")

    # 操作：delete/replace/mask/score
    action = Column(String(20), nullable=False, comment="操作")

    # 处理前内容摘要
    before_content = Column(Text, nullable=True, comment="处理前内容摘要")

    # 处理后内容摘要
    after_content = Column(Text, nullable=True, comment="处理后内容摘要")

    # 命中次数
    hit_count = Column(Integer, default=1, nullable=False, comment="命中次数")

    # 创建时间
    created_at = Column(DateTime, default=datetime.now, nullable=False, comment="创建时间")

    # 索引定义
    __table_args__ = (
        Index("idx_cleaning_document_version", "document_id", "version_id"),
        Index("idx_cleaning_rule_id", "rule_id"),
        Index("idx_cleaning_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        """返回日志对象的字符串表示"""
        return f"<CleaningLog(id={self.id}, document_id={self.document_id}, action={self.action})>"


# ================================================
# 预置清洗规则常量
# ================================================

DEFAULT_CLEANING_RULES = [
    {
        "name": "页眉清洗",
        "rule_type": "regex_delete",
        "rule_config": {
            "patterns": [
                r"^第\s*\d+\s*页$",
                r"^Page\s+\d+$",
                r"^\d+/\d+$",
                r"^[上下]篇$",
            ]
        },
        "priority": 10,
        "scope": "all",
        "description": "删除常见的页眉标记"
    },
    {
        "name": "页脚清洗",
        "rule_type": "regex_delete",
        "rule_config": {
            "patterns": [
                r"^©\s*\d{4}",
                r"^版权所有",
                r"^未经授权",
                r"^Confidential$",
            ]
        },
        "priority": 11,
        "scope": "all",
        "description": "删除常见的页脚标记"
    },
    {
        "name": "水印清洗",
        "rule_type": "regex_delete",
        "rule_config": {
            "patterns": [
                r"^草稿$",
                r"^内部资料$",
                r"^机密$",
                r"^Draft$",
            ]
        },
        "priority": 12,
        "scope": "all",
        "description": "删除水印文字"
    },
    {
        "name": "空白归一化",
        "rule_type": "regex_replace",
        "rule_config": {
            "pattern": r"\s+",
            "replacement": " "
        },
        "priority": 20,
        "scope": "all",
        "description": "将多个空白字符替换为单个空格"
    },
    {
        "name": "广告清洗",
        "rule_type": "regex_delete",
        "rule_config": {
            "patterns": [
                r"立即购买",
                r"点击查看",
                r"广告",
                r"推广",
                r"扫码.*关注",
            ]
        },
        "priority": 30,
        "scope": "all",
        "description": "删除广告和推广信息"
    },
    {
        "name": "特殊符号清理",
        "rule_type": "regex_replace",
        "rule_config": {
            "pattern": r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]",
            "replacement": ""
        },
        "priority": 5,
        "scope": "all",
        "description": "删除控制字符"
    },
]
