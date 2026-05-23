# -*- coding: utf-8 -*-
"""
文档版本服务

本模块提供文档版本相关的业务逻辑：
1. 版本创建
2. 版本查询
3. 版本状态更新
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.common.exception import BusinessException, ErrorCode
from app.common.logging import logger
from app.models.document import Document, DocumentVersion
from core.database import SessionLocal


class DocumentVersionService:
    """
    文档版本服务

    提供文档版本的增删改查等业务逻辑。
    """

    def create_version(
        self,
        db: Session,
        document_id: int,
        file_info: Dict[str, Any],
        uploader_id: Optional[int] = None,
        uploader_name: Optional[str] = None
    ) -> DocumentVersion:
        """
        创建新版本

        Args:
            db: 数据库会话
            document_id: 文档ID
            file_info: 文件信息字典，包含：
                - file_name: 原始文件名
                - file_size: 文件大小
                - file_hash: 文件哈希
                - file_path: 存储路径
                - mime_type: MIME类型
            uploader_id: 上传人ID
            uploader_name: 上传人姓名

        Returns:
            DocumentVersion: 创建的版本对象

        Raises:
            BusinessException: 文档不存在时抛出
        """
        # 验证文档是否存在
        document = db.query(Document).filter(
            Document.id == document_id,
            Document.is_deleted == 0
        ).first()

        if not document:
            raise BusinessException(
                code=ErrorCode.DATA_NOT_FOUND[0],
                message=f"文档不存在，ID: {document_id}"
            )

        # 获取当前最大版本号
        max_version = db.query(DocumentVersion).filter(
            DocumentVersion.document_id == document_id
        ).order_by(desc(DocumentVersion.version)).first()

        new_version = (max_version.version + 1) if max_version else 1

        # 创建版本记录
        version = DocumentVersion(
            document_id=document_id,
            version=new_version,
            file_name=file_info.get("file_name", ""),
            file_size=file_info.get("file_size", 0),
            file_hash=file_info.get("file_hash", ""),
            file_path=file_info.get("file_path", ""),
            mime_type=file_info.get("mime_type", ""),
            storage_type="local",
            status=0,  # 待解析
            parse_status="pending",
            parse_progress=0,
            uploader_id=uploader_id,
            uploader_name=uploader_name,
            uploaded_at=datetime.now()
        )

        db.add(version)

        # 更新文档的当前版本
        document.current_version_id = version.id
        document.total_versions += 1

        db.commit()
        db.refresh(version)

        logger.info(
            f"文档版本创建成功",
            extra={
                "document_id": document_id,
                "version_id": version.id,
                "version": new_version,
                "file_name": file_info.get("file_name", "")
            }
        )

        return version

    def get_version(self, version_id: int) -> Optional[DocumentVersion]:
        """
        获取版本详情

        Args:
            version_id: 版本ID

        Returns:
            DocumentVersion: 版本对象，不存在返回None
        """
        db = SessionLocal()
        try:
            version = db.query(DocumentVersion).filter(
                DocumentVersion.id == version_id
            ).first()

            return version
        finally:
            db.close()

    def get_version_by_id(self, db: Session, version_id: int) -> Optional[DocumentVersion]:
        """
        获取版本详情（带会话）

        Args:
            db: 数据库会话
            version_id: 版本ID

        Returns:
            DocumentVersion: 版本对象
        """
        return db.query(DocumentVersion).filter(
            DocumentVersion.id == version_id
        ).first()

    def list_versions(
        self,
        document_id: int,
        include_inactive: bool = False
    ) -> List[DocumentVersion]:
        """
        获取版本列表

        Args:
            document_id: 文档ID
            include_inactive: 是否包含非激活版本

        Returns:
            版本列表
        """
        db = SessionLocal()
        try:
            query = db.query(DocumentVersion).filter(
                DocumentVersion.document_id == document_id
            )

            # 按版本号降序排列
            versions = query.order_by(desc(DocumentVersion.version)).all()

            return versions
        finally:
            db.close()

    def list_versions_with_db(
        self,
        db: Session,
        document_id: int
    ) -> List[DocumentVersion]:
        """
        获取版本列表（带会话）

        Args:
            db: 数据库会话
            document_id: 文档ID

        Returns:
            版本列表
        """
        return db.query(DocumentVersion).filter(
            DocumentVersion.document_id == document_id
        ).order_by(desc(DocumentVersion.version)).all()

    def update_version_status(
        self,
        version_id: int,
        status: int,
        **kwargs
    ) -> bool:
        """
        更新版本状态

        Args:
            version_id: 版本ID
            status: 新状态
            **kwargs: 其他可更新字段

        Returns:
            是否更新成功
        """
        db = SessionLocal()
        try:
            version = db.query(DocumentVersion).filter(
                DocumentVersion.id == version_id
            ).first()

            if not version:
                raise BusinessException(
                    code=ErrorCode.DATA_NOT_FOUND[0],
                    message=f"版本不存在，ID: {version_id}"
                )

            version.status = status

            # 更新可选字段
            if "parse_status" in kwargs:
                version.parse_status = kwargs["parse_status"]
            if "parse_progress" in kwargs:
                version.parse_progress = kwargs["parse_progress"]
            if "parse_confidence" in kwargs:
                version.parse_confidence = kwargs["parse_confidence"]
            if "total_pages" in kwargs:
                version.total_pages = kwargs["total_pages"]
            if "total_elements" in kwargs:
                version.total_elements = kwargs["total_elements"]
            if "parsed_at" in kwargs:
                version.parsed_at = kwargs["parsed_at"]
            if "error_message" in kwargs:
                version.error_message = kwargs["error_message"]

            db.commit()

            logger.info(
                f"版本状态更新成功",
                extra={
                    "version_id": version_id,
                    "status": status
                }
            )

            return True
        except BusinessException:
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"版本状态更新失败: {str(e)}")
            raise BusinessException(
                code=ErrorCode.OPERATION_FAILED[0],
                message=f"版本状态更新失败: {str(e)}"
            )
        finally:
            db.close()

    def check_file_duplicate(self, file_hash: str) -> Optional[DocumentVersion]:
        """
        检查文件是否重复

        Args:
            file_hash: 文件哈希

        Returns:
            已存在的版本对象，如果不存在返回None
        """
        db = SessionLocal()
        try:
            # 查找相同哈希的版本
            version = db.query(DocumentVersion).filter(
                DocumentVersion.file_hash == file_hash
            ).order_by(desc(DocumentVersion.version)).first()

            return version
        finally:
            db.close()

    def check_file_duplicate_with_db(
        self,
        db: Session,
        file_hash: str
    ) -> Optional[DocumentVersion]:
        """
        检查文件是否重复（带会话）

        Args:
            db: 数据库会话
            file_hash: 文件哈希

        Returns:
            已存在的版本对象
        """
        return db.query(DocumentVersion).filter(
            DocumentVersion.file_hash == file_hash
        ).order_by(desc(DocumentVersion.version)).first()

    def get_version_count(self, document_id: int) -> int:
        """
        获取文档的版本数量

        Args:
            document_id: 文档ID

        Returns:
            版本数量
        """
        db = SessionLocal()
        try:
            count = db.query(DocumentVersion).filter(
                DocumentVersion.document_id == document_id
            ).count()
            return count
        finally:
            db.close()


# 全局服务实例
_version_service: Optional[DocumentVersionService] = None


def get_version_service() -> DocumentVersionService:
    """
    获取文档版本服务实例

    Returns:
        DocumentVersionService: 文档版本服务实例
    """
    global _version_service
    if _version_service is None:
        _version_service = DocumentVersionService()
    return _version_service
