# -*- coding: utf-8 -*-
"""
文档数据模型

本模块定义文档相关的数据库模型：
- Document: 文档主表
- DocumentVersion: 文档版本表
- ImportTask: 导入任务表
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, BigInteger, Index, JSON
from sqlalchemy.orm import relationship

from core.database import Base


class Document(Base):
    """
    文档主表

    存储文档的基本信息，包括文档名称、类型、状态、业务归属等。
    """
    __tablename__ = "documents"

    # 主键ID
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="文档主键ID")

    # 文档名称
    name = Column(String(255), nullable=False, comment="文档名称")

    # 文档类型：docx/doc/pdf/txt/md/html/xlsx/png/jpg/jpeg
    doc_type = Column(String(50), nullable=False, comment="文档类型")

    # 业务归属ID
    business_id = Column(String(100), nullable=True, comment="业务归属ID")

    # 业务归属名称
    business_name = Column(String(100), nullable=True, comment="业务归属名称")

    # 当前版本ID
    current_version_id = Column(BigInteger, nullable=True, comment="当前版本ID")

    # 版本总数
    total_versions = Column(Integer, default=1, nullable=False, comment="版本总数")

    # 状态：0-待解析 1-解析中 2-已解析 3-解析失败 9-已删除
    status = Column(Integer, default=0, nullable=False, comment="状态：0-待解析 1-解析中 2-已解析 3-解析失败 9-已删除")

    # 总页数
    total_pages = Column(Integer, default=0, comment="总页数")

    # 总 Chunk 数
    total_chunks = Column(Integer, default=0, comment="总 Chunk 数")

    # 创建人ID
    creator_id = Column(BigInteger, nullable=True, comment="创建人ID")

    # 创建人姓名
    creator_name = Column(String(100), nullable=True, comment="创建人姓名")

    # 创建时间
    created_at = Column(DateTime, default=datetime.now, nullable=False, comment="创建时间")

    # 更新时间
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False, comment="更新时间")

    # 是否删除：0-否 1-是
    is_deleted = Column(Integer, default=0, nullable=False, comment="是否删除：0-否 1-是")

    # 关系定义
    versions = relationship("DocumentVersion", back_populates="document", lazy="dynamic")

    # 索引定义
    __table_args__ = (
        Index("idx_documents_business_id", "business_id"),
        Index("idx_documents_status", "status"),
        Index("idx_documents_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        """返回文档对象的字符串表示"""
        return f"<Document(id={self.id}, name={self.name}, status={self.status})>"

    @property
    def status_name(self) -> str:
        """获取状态名称"""
        status_map = {
            0: "待解析",
            1: "解析中",
            2: "已解析",
            3: "解析失败",
            9: "已删除"
        }
        return status_map.get(self.status, "未知")


class DocumentVersion(Base):
    """
    文档版本表

    存储文档的版本信息，包括文件哈希、存储路径、上传信息、解析状态等。
    """
    __tablename__ = "document_versions"

    # 主键ID
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="版本主键ID")

    # 文档ID
    document_id = Column(BigInteger, ForeignKey("documents.id"), nullable=False, index=True, comment="文档ID")

    # 版本号
    version = Column(Integer, nullable=False, comment="版本号")

    # 文件哈希
    file_hash = Column(String(64), nullable=False, comment="文件MD5哈希值")

    # 原始文件名
    file_name = Column(String(255), nullable=False, comment="原始文件名")

    # 文件大小（字节）
    file_size = Column(BigInteger, nullable=False, comment="文件大小（字节）")

    # 文件存储路径
    file_path = Column(String(500), nullable=False, comment="文件存储路径")

    # MIME类型
    mime_type = Column(String(100), nullable=True, comment="MIME类型")

    # 存储类型：local/oss/s3
    storage_type = Column(String(20), default="local", nullable=False, comment="存储类型：local/oss/s3")

    # 状态：0-待解析 1-解析中 2-已解析 3-解析失败
    status = Column(Integer, default=0, nullable=False, comment="状态：0-待解析 1-解析中 2-已解析 3-解析失败")

    # 解析状态：pending/processing/completed/failed
    parse_status = Column(String(20), nullable=True, comment="解析状态：pending/processing/completed/failed")

    # 解析进度（百分比）
    parse_progress = Column(Integer, default=0, comment="解析进度（百分比）")

    # 解析置信度
    parse_confidence = Column(String(10), nullable=True, comment="解析置信度")

    # 总页数
    total_pages = Column(Integer, default=0, comment="总页数")

    # 解析元素总数
    total_elements = Column(Integer, default=0, comment="解析元素总数")

    # 上传人ID
    uploader_id = Column(BigInteger, nullable=True, comment="上传人ID")

    # 上传人姓名
    uploader_name = Column(String(100), nullable=True, comment="上传人姓名")

    # 上传时间
    uploaded_at = Column(DateTime, default=datetime.now, nullable=False, comment="上传时间")

    # 解析完成时间
    parsed_at = Column(DateTime, nullable=True, comment="解析完成时间")

    # 错误信息
    error_message = Column(Text, nullable=True, comment="错误信息")

    # 创建时间
    created_at = Column(DateTime, default=datetime.now, nullable=False, comment="创建时间")

    # 更新时间
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False, comment="更新时间")

    # 关系定义
    document = relationship("Document", back_populates="versions")

    # 索引定义
    __table_args__ = (
        Index("idx_document_versions_document_id", "document_id"),
        Index("idx_document_versions_file_hash", "file_hash"),
        Index("idx_document_versions_status", "status"),
        Index("idx_document_versions_uploaded_at", "uploaded_at"),
    )

    def __repr__(self) -> str:
        """返回版本对象的字符串表示"""
        return f"<DocumentVersion(id={self.id}, document_id={self.document_id}, version={self.version})>"

    @property
    def status_name(self) -> str:
        """获取状态名称"""
        status_map = {
            0: "待解析",
            1: "解析中",
            2: "已解析",
            3: "解析失败"
        }
        return status_map.get(self.status, "未知")


class ImportTask(Base):
    """
    导入任务表

    存储导入任务的跟踪信息，包括任务状态、进度、错误信息等。
    """
    __tablename__ = "import_tasks"

    # 主键ID
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="任务主键ID")

    # 任务唯一ID（UUID）
    task_id = Column(String(64), nullable=False, unique=True, comment="任务唯一ID（UUID）")

    # 关联文档ID
    document_id = Column(BigInteger, nullable=True, comment="关联文档ID")

    # 关联版本ID
    version_id = Column(BigInteger, nullable=True, comment="关联版本ID")

    # 任务类型：upload/parse/clean/chunk/embed
    task_type = Column(String(20), nullable=False, comment="任务类型：upload/parse/clean/chunk/embed")

    # 任务状态：pending/running/completed/failed/retry
    task_status = Column(String(20), default="pending", nullable=False, comment="任务状态：pending/running/completed/failed/retry")

    # 优先级：1-最高 5-普通
    priority = Column(Integer, default=5, nullable=False, comment="优先级：1-最高 5-普通")

    # 进度（百分比）
    progress = Column(Integer, default=0, nullable=False, comment="进度（百分比）")

    # 重试次数
    retry_count = Column(Integer, default=0, nullable=False, comment="重试次数")

    # 最大重试次数
    max_retry = Column(Integer, default=3, nullable=False, comment="最大重试次数")

    # 错误类型
    error_type = Column(String(50), nullable=True, comment="错误类型")

    # 错误信息
    error_message = Column(Text, nullable=True, comment="错误信息")

    # 错误详情
    error_detail = Column(Text, nullable=True, comment="错误详情")

    # 开始时间
    started_at = Column(DateTime, nullable=True, comment="开始时间")

    # 完成时间
    completed_at = Column(DateTime, nullable=True, comment="完成时间")

    # 耗时（秒）
    cost_seconds = Column(Integer, nullable=True, comment="耗时（秒）")

    # 任务参数（JSON）
    payload = Column(JSON, nullable=True, comment="任务参数")

    # 任务结果（JSON）
    result = Column(JSON, nullable=True, comment="任务结果")

    # 创建人ID
    creator_id = Column(BigInteger, nullable=True, comment="创建人ID")

    # 创建时间
    created_at = Column(DateTime, default=datetime.now, nullable=False, comment="创建时间")

    # 更新时间
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False, comment="更新时间")

    # 索引定义
    __table_args__ = (
        Index("idx_import_tasks_document_id", "document_id"),
        Index("idx_import_tasks_version_id", "version_id"),
        Index("idx_import_tasks_task_status", "task_status"),
        Index("idx_import_tasks_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        """返回任务对象的字符串表示"""
        return f"<ImportTask(id={self.id}, task_id={self.task_id}, task_type={self.task_type}, task_status={self.task_status})>"

    @property
    def status_name(self) -> str:
        """获取状态名称"""
        status_map = {
            "pending": "待处理",
            "running": "进行中",
            "completed": "已完成",
            "failed": "失败",
            "retry": "重试中"
        }
        return status_map.get(self.task_status, "未知")
