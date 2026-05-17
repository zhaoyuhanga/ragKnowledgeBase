"""
RAG 问答系统 - 数据库模型
包含文档、文档块、问答日志等数据模型
"""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    Column, Integer, BigInteger, String, Text, DateTime, 
    Boolean, JSON, ForeignKey, Index, func
)
from sqlalchemy.orm import relationship, Mapped

from app.core.database import Base


class Document(Base):
    """
    文档表
    存储上传的文档元信息
    """
    __tablename__ = "documents"
    
    # 主键，自增ID
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    
    # 文件名
    filename = Column(String(255), nullable=False, comment="文件名")
    
    # 文件存储路径
    file_path = Column(String(512), nullable=False, comment="文件存储路径")
    
    # 文件类型 (pdf/md/txt/docx/ai_generated)
    file_type = Column(String(50), nullable=False, comment="文件类型")
    
    # 文件大小（字节）
    file_size = Column(BigInteger, nullable=False, comment="文件大小（字节）")
    
    # 文件内容哈希（用于去重）
    content_hash = Column(String(64), nullable=True, index=True, comment="文件内容哈希")
    
    # 处理状态 (0=处理中, 1=已完成, 2=失败)
    status = Column(Integer, default=0, nullable=False, comment="处理状态")
    
    # 切分块数量
    chunk_count = Column(Integer, default=0, nullable=False, comment="切分块数量")
    
    # 错误信息
    error_message = Column(Text, nullable=True, comment="错误信息")
    
    # ============ AI 生成相关字段 ============
    # 来源类型: local(本地导入) | ai_generated(AI生成)
    source_type = Column(String(20), default="local", nullable=False, comment="来源类型")
    
    # AI 生成时记录原始问题
    generated_from_question = Column(Text, nullable=True, comment="AI生成时的原始问题")
    
    # AI 生成时间
    generated_at = Column(DateTime, nullable=True, comment="AI生成时间")
    
    # 使用的LLM模型
    llm_model = Column(String(100), nullable=True, comment="LLM模型")
    
    # LLM提供商
    llm_provider = Column(String(50), nullable=True, comment="LLM提供商")
    
    # 创建时间
    created_at = Column(DateTime, default=datetime.now, nullable=False, comment="创建时间")
    
    # 更新时间
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False, comment="更新时间")
    
    # 关联的文档块
    chunks: Mapped[List["DocumentChunk"]] = relationship(
        "DocumentChunk", 
        back_populates="document",
        cascade="all, delete-orphan"
    )
    
    # 索引
    __table_args__ = (
        Index("idx_document_status", "status"),
        Index("idx_document_created", "created_at"),
        Index("idx_document_source_type", "source_type"),
        Index("idx_document_llm_model", "llm_model"),
    )
    
    def __repr__(self):
        return f"<Document(id={self.id}, filename='{self.filename}', source_type='{self.source_type}')>"


class DocumentChunk(Base):
    """
    文档块表
    存储文档切分后的文本块
    """
    __tablename__ = "document_chunks"
    
    # 主键，自增ID
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    
    # 外键，关联文档表
    document_id = Column(
        BigInteger, 
        ForeignKey("documents.id", ondelete="CASCADE"), 
        nullable=False,
        index=True,
        comment="文档ID"
    )
    
    # 块序号
    chunk_index = Column(Integer, nullable=False, comment="块序号")
    
    # 文本内容
    content = Column(Text, nullable=False, comment="文本内容")
    
    # 字符数量
    char_count = Column(Integer, nullable=False, comment="字符数量")
    
    # 向量数据库中的向量ID
    vector_id = Column(String(64), nullable=True, index=True, comment="向量ID")
    
    # 创建时间
    created_at = Column(DateTime, default=datetime.now, nullable=False, comment="创建时间")
    
    # ============ AI 生成相关字段 ============
    # 来源类型: local(本地导入) | ai_generated(AI生成)
    source_type = Column(String(20), default="local", nullable=False, comment="来源类型")
    
    # AI 生成时记录原始问题
    generated_from_question = Column(Text, nullable=True, comment="AI生成时的原始问题")
    
    # AI 生成时间
    generated_at = Column(DateTime, nullable=True, comment="AI生成时间")
    
    # 使用的LLM模型
    llm_model = Column(String(100), nullable=True, comment="LLM模型")
    
    # LLM提供商
    llm_provider = Column(String(50), nullable=True, comment="LLM提供商")
    
    # 关联的文档
    document: Mapped["Document"] = relationship("Document", back_populates="chunks")
    
    # 索引
    __table_args__ = (
        Index("idx_chunk_document_index", "document_id", "chunk_index"),
        Index("idx_chunk_source_type", "source_type"),
    )
    
    def __repr__(self):
        return f"<DocumentChunk(id={self.id}, document_id={self.document_id}, source_type='{self.source_type}')>"


class QALog(Base):
    """
    问答日志表
    存储用户问答记录
    """
    __tablename__ = "qa_logs"
    
    # 主键，自增ID
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    
    # 用户问题
    question = Column(Text, nullable=False, comment="用户问题")
    
    # 系统回答
    answer = Column(Text, nullable=True, comment="系统回答")
    
    # 引用的文档块ID列表 (JSON格式)
    referenced_chunks = Column(JSON, nullable=True, comment="引用的文档块ID列表")
    
    # 响应耗时（毫秒）
    response_time_ms = Column(Integer, nullable=True, comment="响应耗时（毫秒）")
    
    # 是否命中缓存
    cache_hit = Column(Boolean, default=False, nullable=False, comment="是否命中缓存")
    
    # 来源类型: local(本地文档) | ai_generated(AI生成)
    source_type = Column(String(32), default="local", nullable=False, comment="来源类型: local/ai_generated")
    
    # 会话ID（用于多轮对话）
    session_id = Column(String(64), nullable=True, index=True, comment="会话ID")
    
    # 创建时间
    created_at = Column(DateTime, default=datetime.now, nullable=False, index=True, comment="创建时间")
    
    # 索引
    __table_args__ = (
        Index("idx_qa_session", "session_id", "created_at"),
    )
    
    def __repr__(self):
        return f"<QALog(id={self.id}, cache_hit={self.cache_hit})>"


class SystemLog(Base):
    """
    系统日志表
    存储系统操作日志
    """
    __tablename__ = "system_logs"
    
    # 主键，自增ID
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    
    # 模块名称
    module = Column(String(50), nullable=False, index=True, comment="模块名称")
    
    # 操作名称
    operation = Column(String(100), nullable=False, comment="操作名称")
    
    # 操作状态
    status = Column(String(20), nullable=False, comment="操作状态")
    
    # 操作详情 (JSON格式)
    details = Column(JSON, nullable=True, comment="操作详情")
    
    # 用户ID
    user_id = Column(String(64), nullable=True, comment="用户ID")
    
    # 耗时（毫秒）
    duration_ms = Column(Integer, nullable=True, comment="耗时（毫秒）")
    
    # 错误信息
    error_message = Column(Text, nullable=True, comment="错误信息")
    
    # 创建时间
    created_at = Column(DateTime, default=datetime.now, nullable=False, index=True, comment="创建时间")
    
    # 索引
    __table_args__ = (
        Index("idx_system_log_module_time", "module", "created_at"),
    )
    
    def __repr__(self):
        return f"<SystemLog(id={self.id}, module='{self.module}', operation='{self.operation}')>"
