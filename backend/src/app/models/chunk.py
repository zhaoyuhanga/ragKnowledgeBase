# -*- coding: utf-8 -*-
"""
Chunk数据模型

本模块定义文档切分块的数据模型和关键词索引模型。
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, DateTime, Integer, String, Text, BigInteger, Index, Float, JSON

from core.database import Base


class DocumentChunk(Base):
    """
    文档Chunk表

    存储文档切分后的文本块信息。
    """
    __tablename__ = "document_chunks"

    # 主键ID
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="Chunk主键ID")

    # 文档ID
    document_id = Column(BigInteger, nullable=False, comment="文档ID")

    # 版本ID
    version_id = Column(BigInteger, nullable=False, comment="版本ID")

    # Chunk唯一ID
    chunk_id = Column(String(64), nullable=False, unique=True, comment="Chunk唯一ID")

    # Chunk索引
    chunk_index = Column(Integer, nullable=False, comment="Chunk索引")

    # Chunk原文
    content = Column(Text, nullable=False, comment="Chunk原文")

    # 增强文本
    enhanced_content = Column(Text, nullable=True, comment="增强文本")

    # 内容Hash
    content_hash = Column(String(64), nullable=False, comment="内容Hash")

    # Chunk类型：paragraph/table/image/chart/code/list
    chunk_type = Column(String(20), nullable=False, comment="Chunk类型")

    # 标题层级路径
    title_path = Column(String(500), nullable=True, comment="标题层级路径")

    # 章节路径
    chapter_path = Column(String(500), nullable=True, comment="章节路径")

    # 起始页码
    page_start = Column(Integer, nullable=True, comment="起始页码")

    # 结束页码
    page_end = Column(Integer, nullable=True, comment="结束页码")

    # Token数量
    token_count = Column(Integer, default=0, nullable=False, comment="Token数量")

    # 字符数量
    char_count = Column(Integer, default=0, nullable=False, comment="字符数量")

    # 来源元素ID列表
    element_ids = Column(JSON, nullable=True, comment="来源元素ID列表")

    # 质量评分
    quality_score = Column(Float, nullable=True, comment="质量评分")

    # 表格摘要（长表使用）
    table_summary = Column(Text, nullable=True, comment="表格摘要")

    # 表结构（表格使用）
    table_schema = Column(JSON, nullable=True, comment="表结构")

    # 图片描述（图片使用）
    image_description = Column(JSON, nullable=True, comment="图片描述")

    # 是否重复
    is_duplicate = Column(Integer, default=0, nullable=False, comment="是否重复")

    # 重复的Chunk ID
    duplicate_of = Column(BigInteger, nullable=True, comment="重复的Chunk ID")

    # 状态：0-待处理 1-已向量化 9-已删除
    status = Column(Integer, default=0, nullable=False, comment="状态")

    # 向量ID
    vector_id = Column(BigInteger, nullable=True, comment="向量ID")

    # 是否已建关键词索引
    keyword_indexed = Column(Integer, default=0, nullable=False, comment="是否已建关键词索引")

    # 创建时间
    created_at = Column(DateTime, default=datetime.now, nullable=False, comment="创建时间")

    # 更新时间
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False, comment="更新时间")

    # 索引定义
    __table_args__ = (
        Index("idx_chunks_document_version", "document_id", "version_id"),
        Index("idx_chunks_chunk_type", "chunk_type"),
        Index("idx_chunks_content_hash", "content_hash"),
        Index("idx_chunks_quality_score", "quality_score"),
        Index("idx_chunks_status", "status"),
        Index("idx_chunks_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        """返回Chunk对象的字符串表示"""
        return f"<DocumentChunk(id={self.id}, chunk_id={self.chunk_id}, chunk_type={self.chunk_type})>"


class ChunkKeywordIndex(Base):
    """
    Chunk关键词索引表

    存储文档Chunk的关键词倒排索引信息。
    """
    __tablename__ = "chunk_keyword_index"

    # 主键ID
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="主键ID")

    # Chunk ID
    chunk_id = Column(BigInteger, nullable=False, comment="Chunk ID")

    # 词项
    term = Column(String(128), nullable=False, comment="分词词项")

    # 字段：content/title/enhanced
    field = Column(String(20), nullable=False, default="content", comment="字段")

    # 词频
    tf = Column(Integer, nullable=False, default=1, comment="词频")

    # 逆文档频率
    idf = Column(Float, nullable=False, default=0.0, comment="逆文档频率")

    # 词项位置
    position = Column(Integer, nullable=True, comment="词项位置")

    # 权重
    weight = Column(Float, nullable=False, default=1.0, comment="权重")

    # 创建时间
    created_at = Column(DateTime, default=datetime.now, nullable=False, comment="创建时间")

    # 索引定义
    __table_args__ = (
        Index("idx_keyword_chunk_term_field", "chunk_id", "term", "field", unique=True),
        Index("idx_keyword_term", "term"),
        Index("idx_keyword_chunk_id", "chunk_id"),
    )

    def __repr__(self) -> str:
        """返回索引对象的字符串表示"""
        return f"<ChunkKeywordIndex(chunk_id={self.chunk_id}, term={self.term}, field={self.field})>"
