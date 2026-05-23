# -*- coding: utf-8 -*-
"""
解析相关数据模型

本模块定义解析相关的数据库模型：
- DocumentElement: 文档解析元素表
- ParseQualityLog: 解析质量日志表
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, DateTime, Integer, String, Text, BigInteger, Index, JSON, Float
from sqlalchemy.orm import relationship

from core.database import Base


class DocumentElement(Base):
    """
    文档解析元素表

    存储文档解析后的结构化元素，包括标题、段落、表格、图片等。
    """
    __tablename__ = "document_elements"

    # 主键ID
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="元素主键ID")

    # 文档ID
    document_id = Column(BigInteger, nullable=False, comment="文档ID")

    # 版本ID
    version_id = Column(BigInteger, nullable=False, comment="版本ID")

    # 元素唯一ID
    element_id = Column(String(64), nullable=False, unique=True, comment="元素唯一ID")

    # 页码（Word可为空）
    page_no = Column(Integer, nullable=True, comment="页码")

    # 起始页（跨页元素）
    page_start = Column(Integer, nullable=True, comment="起始页")

    # 结束页
    page_end = Column(Integer, nullable=True, comment="结束页")

    # 元素类型：title/paragraph/table/image/chart/list/header/footer/code
    element_type = Column(String(20), nullable=False, comment="元素类型：title/paragraph/table/image/chart/list/header/footer/code")

    # 原始文本内容
    content = Column(Text, nullable=True, comment="原始文本内容")

    # 增强文本内容
    enhanced_content = Column(Text, nullable=True, comment="增强文本内容")

    # 阅读顺序
    reading_order = Column(Integer, default=0, comment="阅读顺序")

    # 标题层级（1-6）
    title_level = Column(Integer, nullable=True, comment="标题层级（1-6）")

    # 标题层级路径
    title_path = Column(String(500), nullable=True, comment="标题层级路径")

    # 父级路径
    parent_path = Column(String(500), nullable=True, comment="父级路径")

    # 元素坐标 JSON {x, y, width, height}
    bbox = Column(JSON, nullable=True, comment="元素坐标")

    # 识别置信度（0-1）
    confidence = Column(Float, default=1.0, comment="识别置信度（0-1）")

    # 是否跨页合并
    is_merged = Column(Integer, default=0, comment="是否跨页合并")

    # 表格结构信息
    table_structure = Column(JSON, nullable=True, comment="表格结构信息")

    # 图片描述信息
    image_description = Column(JSON, nullable=True, comment="图片描述信息")

    # 元数据
    element_metadata = Column(JSON, nullable=True, comment="元数据")

    # 质量标记：good/warning/bad
    quality_flag = Column(String(20), default="good", comment="质量标记：good/warning/bad")

    # 创建时间
    created_at = Column(DateTime, default=datetime.now, nullable=False, comment="创建时间")

    # 索引定义
    __table_args__ = (
        Index("idx_document_elements_document_version", "document_id", "version_id"),
        Index("idx_document_elements_page_no", "page_no"),
        Index("idx_document_elements_element_type", "element_type"),
        Index("idx_document_elements_reading_order", "reading_order"),
        Index("idx_document_elements_quality_flag", "quality_flag"),
    )

    def __repr__(self) -> str:
        """返回元素对象的字符串表示"""
        return f"<DocumentElement(id={self.id}, element_id={self.element_id}, type={self.element_type})>"


class ParseQualityLog(Base):
    """
    解析质量日志表

    存储文档解析过程中的质量检查日志，包括OCR识别、置信度、版面问题等。
    """
    __tablename__ = "parse_quality_logs"

    # 主键ID
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="日志主键ID")

    # 文档ID
    document_id = Column(BigInteger, nullable=False, comment="文档ID")

    # 版本ID
    version_id = Column(BigInteger, nullable=False, comment="版本ID")

    # 页码
    page_no = Column(Integer, nullable=True, comment="页码")

    # 元素ID（关联element_id）
    element_id = Column(String(64), nullable=True, comment="元素ID")

    # 检查类型：ocr/low_confidence/layout/encoding/table/image
    check_type = Column(String(50), nullable=False, comment="检查类型：ocr/low_confidence/layout/encoding/table/image")

    # 质量标记：good/warning/bad
    quality_flag = Column(String(20), nullable=False, comment="质量标记：good/warning/bad")

    # 置信度
    confidence = Column(Float, nullable=True, comment="置信度")

    # 问题描述
    issue_description = Column(Text, nullable=True, comment="问题描述")

    # 修复建议
    suggestion = Column(Text, nullable=True, comment="修复建议")

    # 是否已解决：0-否 1-是
    resolved = Column(Integer, default=0, nullable=False, comment="是否已解决：0-否 1-是")

    # 解决时间
    resolved_at = Column(DateTime, nullable=True, comment="解决时间")

    # 解决人ID
    resolved_by = Column(BigInteger, nullable=True, comment="解决人ID")

    # 创建时间
    created_at = Column(DateTime, default=datetime.now, nullable=False, comment="创建时间")

    # 索引定义
    __table_args__ = (
        Index("idx_parse_quality_document_version", "document_id", "version_id"),
        Index("idx_parse_quality_page_no", "page_no"),
        Index("idx_parse_quality_quality_flag", "quality_flag"),
        Index("idx_parse_quality_resolved", "resolved"),
    )

    def __repr__(self) -> str:
        """返回日志对象的字符串表示"""
        return f"<ParseQualityLog(id={self.id}, document_id={self.document_id}, check_type={self.check_type})>"
