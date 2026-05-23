# -*- coding: utf-8 -*-
"""
文档服务

本模块提供文档相关的业务逻辑处理：
1. 文档CRUD操作
2. 单文件上传
3. 批量上传
4. 文件Hash去重
5. 导入任务管理

注意：路由层只做参数校验和响应封装，所有业务逻辑在此层实现。
"""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import UploadFile
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.common.exception import BusinessException, ErrorCode
from app.common.logging import logger
from app.models.document import Document, DocumentVersion, ImportTask
from app.models.chunk import DocumentChunk, ChunkKeywordIndex
from app.models.qa import QALog
from app.models.feedback import FeedbackAnalysis, OptimizationRule
from app.services.storage_service import get_storage_service, FileStorageService
from app.services.version_service import get_version_service, DocumentVersionService
from core.config import settings
from core.database import SessionLocal
from core.milvus import get_milvus_client


class ImportTaskService:
    """
    导入任务服务

    提供导入任务的创建、查询等业务逻辑。
    """

    def create_task(
        self,
        db: Session,
        document_id: Optional[int] = None,
        version_id: Optional[int] = None,
        task_type: str = "upload",
        creator_id: Optional[int] = None,
        payload: Optional[Dict[str, Any]] = None
    ) -> ImportTask:
        """
        创建导入任务

        Args:
            db: 数据库会话
            document_id: 文档ID
            version_id: 版本ID
            task_type: 任务类型
            creator_id: 创建人ID
            payload: 任务参数

        Returns:
            ImportTask: 创建的任务对象
        """
        task = ImportTask(
            task_id=str(uuid.uuid4()),
            document_id=document_id,
            version_id=version_id,
            task_type=task_type,
            task_status="pending",
            priority=5,
            progress=0,
            retry_count=0,
            max_retry=3,
            creator_id=creator_id,
            payload=payload
        )
        db.add(task)
        db.flush()

        logger.info(
            f"导入任务创建成功",
            extra={
                "task_id": task.task_id,
                "document_id": document_id,
                "version_id": version_id,
                "task_type": task_type
            }
        )

        return task

    def get_task_by_id(self, task_id: str) -> Optional[ImportTask]:
        """
        根据任务ID获取任务

        Args:
            task_id: 任务ID

        Returns:
            ImportTask: 任务对象
        """
        db = SessionLocal()
        try:
            task = db.query(ImportTask).filter(
                ImportTask.task_id == task_id
            ).first()
            return task
        finally:
            db.close()

    def update_task_status(
        self,
        task_id: str,
        task_status: str,
        progress: Optional[int] = None,
        error_type: Optional[str] = None,
        error_message: Optional[str] = None,
        result: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        更新任务状态

        Args:
            task_id: 任务ID
            task_status: 新状态
            progress: 进度
            error_type: 错误类型
            error_message: 错误信息
            result: 任务结果

        Returns:
            是否更新成功
        """
        db = SessionLocal()
        try:
            task = db.query(ImportTask).filter(
                ImportTask.task_id == task_id
            ).first()

            if not task:
                return False

            task.task_status = task_status
            if progress is not None:
                task.progress = progress
            if error_type is not None:
                task.error_type = error_type
            if error_message is not None:
                task.error_message = error_message
            if result is not None:
                task.result = result

            # 设置开始时间和完成时间
            if task_status == "running" and task.started_at is None:
                task.started_at = datetime.now()
            if task_status in ("completed", "failed"):
                task.completed_at = datetime.now()
                if task.started_at:
                    task.cost_seconds = int(
                        (task.completed_at - task.started_at).total_seconds()
                    )

            db.commit()
            return True
        except Exception as e:
            db.rollback()
            logger.error(f"更新任务状态失败: {str(e)}")
            return False
        finally:
            db.close()


class DocumentService:
    """
    文档服务

    提供文档的增删改查、上传、导入任务等业务逻辑。
    """

    def __init__(self):
        """初始化文档服务"""
        self._storage_service: Optional[FileStorageService] = None
        self._version_service: Optional[DocumentVersionService] = None
        self._import_task_service: Optional[ImportTaskService] = None

    @property
    def storage_service(self) -> FileStorageService:
        """获取存储服务"""
        if self._storage_service is None:
            self._storage_service = get_storage_service()
        return self._storage_service

    @property
    def version_service(self) -> DocumentVersionService:
        """获取版本服务"""
        if self._version_service is None:
            self._version_service = get_version_service()
        return self._version_service

    @property
    def import_task_service(self) -> ImportTaskService:
        """获取导入任务服务"""
        if self._import_task_service is None:
            self._import_task_service = ImportTaskService()
        return self._import_task_service

    def upload_document(
        self,
        file: UploadFile,
        business_id: Optional[str] = None,
        business_name: Optional[str] = None,
        creator_id: Optional[int] = None,
        creator_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        上传单个文档

        Args:
            file: 上传的文件
            business_id: 业务归属ID
            business_name: 业务归属名称
            creator_id: 创建人ID
            creator_name: 创建人姓名

        Returns:
            上传结果
        """
        db = SessionLocal()
        try:
            # ========== 阶段1：读取文件内容 ==========
            logger.info(
                f"开始上传文档",
                extra={
                    "file_name": file.filename,
                    "business_id": business_id,
                    "creator_id": creator_id
                }
            )
            
            try:
                file_content = file.file.read()
                file_size = len(file_content)
                logger.debug(
                    f"文件内容读取完成",
                    extra={
                        "file_name": file.filename,
                        "file_size": file_size
                    }
                )
            except Exception as e:
                logger.error(
                    f"读取文件内容失败",
                    extra={
                        "file_name": file.filename,
                        "error_type": type(e).__name__,
                        "error_message": str(e)
                    }
                )
                raise BusinessException(
                    code=ErrorCode.FILE_UPLOAD_FAILED[0],
                    message=f"读取文件内容失败: {str(e)}"
                )

            # ========== 阶段2：验证并识别文件类型 ==========
            try:
                doc_type = self.storage_service.validate_file(file.filename, file_size)
                logger.debug(
                    f"文件类型识别成功",
                    extra={
                        "file_name": file.filename,
                        "doc_type": doc_type
                    }
                )
            except Exception as e:
                logger.error(
                    f"文件类型验证失败",
                    extra={
                        "file_name": file.filename,
                        "file_size": file_size,
                        "error_type": type(e).__name__,
                        "error_message": str(e)
                    }
                )
                raise BusinessException(
                    code=ErrorCode.FILE_UPLOAD_FAILED[0],
                    message=f"不支持的文件类型: {str(e)}"
                )

            # ========== 阶段3：计算文件哈希 ==========
            try:
                file_hash = self.storage_service.calculate_hash(file_content)
                logger.debug(
                    f"文件哈希计算完成",
                    extra={
                        "file_name": file.filename,
                        "file_hash": file_hash[:16] + "..."
                    }
                )
            except Exception as e:
                logger.error(
                    f"计算文件哈希失败",
                    extra={
                        "file_name": file.filename,
                        "error_type": type(e).__name__,
                        "error_message": str(e)
                    }
                )
                raise BusinessException(
                    code=ErrorCode.FILE_UPLOAD_FAILED[0],
                    message=f"计算文件哈希失败: {str(e)}"
                )

            # ========== 阶段4：检查文件是否重复 ==========
            try:
                existing_version = self.version_service.check_file_duplicate_with_db(db, file_hash)
                if existing_version:
                    logger.info(
                        f"检测到重复文件",
                        extra={
                            "file_name": file.filename,
                            "file_hash": file_hash[:16] + "...",
                            "existing_version_id": existing_version.id,
                            "existing_document_id": existing_version.document_id
                        }
                    )

                    return {
                        "document_id": existing_version.document_id,
                        "version_id": existing_version.id,
                        "task_id": None,
                        "name": file.filename,
                        "doc_type": doc_type,
                        "file_size": file_size,
                        "file_hash": file_hash,
                        "is_duplicate": True,
                        "status": "completed",
                        "message": "文档已存在，关联到已有版本"
                    }
            except Exception as e:
                logger.error(
                    f"检查文件重复失败",
                    extra={
                        "file_name": file.filename,
                        "file_hash": file_hash[:16] + "...",
                        "error_type": type(e).__name__,
                        "error_message": str(e)
                    }
                )
                raise BusinessException(
                    code=ErrorCode.DATABASE_ERROR[0],
                    message=f"检查文件重复失败: {str(e)}"
                )

            # ========== 阶段5：保存文件 ==========
            try:
                file_info = self.storage_service.save_file(
                    file_data=file_content,
                    original_name=file.filename,
                    doc_type=doc_type,
                    business_id=business_id
                )
                logger.debug(
                    f"文件保存成功",
                    extra={
                        "file_name": file.filename,
                        "saved_path": file_info.file_path
                    }
                )
            except Exception as e:
                logger.error(
                    f"保存文件失败",
                    extra={
                        "file_name": file.filename,
                        "doc_type": doc_type,
                        "error_type": type(e).__name__,
                        "error_message": str(e)
                    }
                )
                raise BusinessException(
                    code=ErrorCode.FILE_UPLOAD_FAILED[0],
                    message=f"保存文件失败: {str(e)}"
                )

            # ========== 阶段6：创建导入任务 ==========
            try:
                task = self.import_task_service.create_task(
                    db=db,
                    task_type="upload",
                    creator_id=creator_id,
                    payload={
                        "file_name": file.filename,
                        "doc_type": doc_type,
                        "file_size": file_size
                    }
                )
                logger.debug(
                    f"导入任务创建成功",
                    extra={
                        "task_id": task.task_id
                    }
                )
            except Exception as e:
                logger.error(
                    f"创建导入任务失败",
                    extra={
                        "file_name": file.filename,
                        "error_type": type(e).__name__,
                        "error_message": str(e)
                    }
                )
                raise BusinessException(
                    code=ErrorCode.DATABASE_ERROR[0],
                    message=f"创建导入任务失败: {str(e)}"
                )

            # ========== 阶段7：创建文档记录 ==========
            try:
                document = Document(
                    name=file.filename,
                    doc_type=doc_type,
                    business_id=business_id,
                    business_name=business_name,
                    status=0,  # 待解析
                    creator_id=creator_id,
                    creator_name=creator_name
                )
                db.add(document)
                db.flush()
                
                logger.debug(
                    f"文档记录创建成功",
                    extra={
                        "document_id": document.id,
                        "file_name": file.filename
                    }
                )
            except Exception as e:
                logger.error(
                    f"创建文档记录失败",
                    extra={
                        "file_name": file.filename,
                        "error_type": type(e).__name__,
                        "error_message": str(e)
                    }
                )
                raise BusinessException(
                    code=ErrorCode.DATABASE_ERROR[0],
                    message=f"创建文档记录失败: {str(e)}"
                )

            # ========== 阶段8：创建版本记录 ==========
            try:
                version_data = {
                    "file_name": file.filename,
                    "file_size": file_size,
                    "file_hash": file_hash,
                    "file_path": file_info.file_path,
                    "doc_type": doc_type,
                    "mime_type": file_info.mime_type
                }
                version = self.version_service.create_version(
                    db=db,
                    document_id=document.id,
                    file_info=version_data,
                    uploader_id=creator_id,
                    uploader_name=creator_name
                )
                
                logger.debug(
                    f"版本记录创建成功",
                    extra={
                        "document_id": document.id,
                        "version_id": version.id,
                        "file_path": file_info.file_path
                    }
                )
            except Exception as e:
                logger.error(
                    f"创建版本记录失败",
                    extra={
                        "document_id": document.id,
                        "file_name": file.filename,
                        "error_type": type(e).__name__,
                        "error_message": str(e)
                    }
                )
                raise BusinessException(
                    code=ErrorCode.DATABASE_ERROR[0],
                    message=f"创建版本记录失败: {str(e)}"
                )

            # 更新导入任务
            task.document_id = document.id
            task.version_id = version.id
            task.task_status = "completed"
            task.completed_at = datetime.now()
            task.result = {
                "document_id": document.id,
                "version_id": version.id
            }

            # 更新文档的当前版本ID
            document.current_version_id = version.id

            # ========== 阶段9：发布解析任务到消息队列 ==========
            from app.services.queue_consumer import get_queue_publisher
            parse_task_published = False
            parse_task_id = None
            
            logger.info(
                f"准备发布解析任务到消息队列",
                extra={
                    "document_id": document.id,
                    "version_id": version.id,
                    "file_name": file.filename,
                    "file_path": file_info.file_path,
                    "doc_type": doc_type
                }
            )
            
            try:
                publisher = get_queue_publisher()
                parse_task_id = f"{task.task_id}_parse"
                parse_task = {
                    "task_id": parse_task_id,
                    "task_type": "parse",
                    "document_id": document.id,
                    "version_id": version.id,
                    "priority": task.priority,
                    "retry_count": 0,
                    "max_retry": 3,
                    "payload": {
                        "file_name": file.filename,
                        "file_path": file_info.file_path,
                        "doc_type": doc_type,
                        "file_size": file_size
                    }
                }
                publisher.publish_parse_task(parse_task)
                parse_task_published = True
                
                logger.info(
                    f"解析任务发布成功",
                    extra={
                        "document_id": document.id,
                        "version_id": version.id,
                        "task_id": parse_task_id,
                        "file_name": file.filename,
                        "routing_key": "rag.parse.start"
                    }
                )
            except Exception as e:
                logger.error(
                    f"解析任务发布失败",
                    extra={
                        "document_id": document.id,
                        "version_id": version.id,
                        "task_id": parse_task_id,
                        "file_name": file.filename,
                        "file_path": file_info.file_path,
                        "doc_type": doc_type,
                        "error_type": type(e).__name__,
                        "error_class": e.__class__.__name__,
                        "error_message": str(e),
                        "error_module": type(e).__module__
                    }
                )

            # 如果解析任务发布失败，确保文档状态为待手动解析
            if not parse_task_published:
                document.status = 0  # 待手动解析
                logger.warning(
                    f"解析任务发布失败，文档状态设置为待手动解析",
                    extra={
                        "document_id": document.id,
                        "version_id": version.id
                    }
                )

            db.commit()

            # 根据解析任务发布状态设置返回信息
            if parse_task_published:
                result_status = "pending"
                result_message = "文档上传成功，正在自动解析"
            else:
                result_status = "manual_required"
                result_message = "文档上传成功，但解析任务发布失败，需要手动触发解析"

            logger.info(
                f"文档上传成功",
                extra={
                    "document_id": document.id,
                    "version_id": version.id,
                    "task_id": task.task_id,
                    "file_name": file.filename,
                    "doc_type": doc_type,
                    "file_size": file_size,
                    "file_hash": file_hash[:16] + "...",
                    "parse_task_published": parse_task_published,
                    "status": result_status
                }
            )

            return {
                "document_id": document.id,
                "version_id": version.id,
                "task_id": task.task_id,
                "name": file.filename,
                "doc_type": doc_type,
                "file_size": file_size,
                "file_hash": file_hash,
                "is_duplicate": False,
                "status": result_status,
                "parse_task_published": parse_task_published,
                "message": result_message
            }

        except BusinessException:
            db.rollback()
            raise
        except Exception as e:
            db.rollback()
            logger.error(
                f"文档上传失败",
                extra={
                    "file_name": file.filename if 'file' in locals() else "unknown",
                    "error_type": type(e).__name__,
                    "error_class": e.__class__.__name__,
                    "error_message": str(e),
                    "error_module": type(e).__module__
                }
            )
            raise BusinessException(
                code=ErrorCode.FILE_UPLOAD_FAILED[0],
                message=f"文档上传失败: {str(e)}"
            )
        finally:
            db.close()

    def batch_upload(
        self,
        files: List[UploadFile],
        business_id: Optional[str] = None,
        creator_id: Optional[int] = None,
        creator_name: Optional[str] = None,
        max_batch_size: int = 20
    ) -> Dict[str, Any]:
        """
        批量上传文档

        Args:
            files: 上传的文件列表
            business_id: 业务归属ID
            creator_id: 创建人ID
            creator_name: 创建人姓名
            max_batch_size: 最大批量大小

        Returns:
            批量上传结果
        """
        # 检查批量大小
        if len(files) > max_batch_size:
            raise BusinessException(
                code=ErrorCode.PARAM_INVALID[0],
                message=f"批量上传文件数量不能超过 {max_batch_size} 个"
            )

        results = {
            "total": len(files),
            "success": 0,
            "failed": 0,
            "duplicates": 0,
            "documents": [],
            "failed_files": []
        }

        for file in files:
            try:
                result = self.upload_document(
                    file=file,
                    business_id=business_id,
                    creator_id=creator_id,
                    creator_name=creator_name
                )

                results["success"] += 1
                if result.get("is_duplicate"):
                    results["duplicates"] += 1

                results["documents"].append({
                    "document_id": result["document_id"],
                    "version_id": result["version_id"],
                    "name": result["name"],
                    "is_duplicate": result["is_duplicate"],
                    "status": result["status"]
                })

            except BusinessException as e:
                results["failed"] += 1
                results["failed_files"].append({
                    "name": file.filename,
                    "error": e.message
                })
                logger.warning(
                    f"文件上传失败: {file.filename}",
                    extra={"error": e.message}
                )

        logger.info(
            f"批量上传完成",
            extra={
                "total": results["total"],
                "success": results["success"],
                "failed": results["failed"],
                "duplicates": results["duplicates"]
            }
        )

        return results

    def list_documents(
        self,
        page_no: int = 1,
        page_size: int = 20,
        business_id: Optional[str] = None,
        status: Optional[int] = None,
        keyword: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        查询文档列表

        Args:
            page_no: 页码
            page_size: 每页数量
            business_id: 业务归属ID
            status: 状态筛选
            keyword: 名称关键词搜索
            start_date: 创建开始日期
            end_date: 创建结束日期

        Returns:
            包含items和total的字典
        """
        db = SessionLocal()
        try:
            query = db.query(Document).filter(Document.is_deleted == 0)

            # 添加筛选条件
            if business_id:
                query = query.filter(Document.business_id == business_id)
            if status is not None:
                query = query.filter(Document.status == status)
            if keyword:
                query = query.filter(Document.name.like(f"%{keyword}%"))
            if start_date:
                query = query.filter(Document.created_at >= start_date)
            if end_date:
                query = query.filter(Document.created_at <= end_date)

            # 获取总数
            total = query.count()

            # 分页查询
            offset = (page_no - 1) * page_size
            items = query.order_by(desc(Document.updated_at)).offset(offset).limit(page_size).all()

            # 转换为字典
            result_items = []
            for doc in items:
                result_items.append({
                    "id": doc.id,
                    "name": doc.name,
                    "doc_type": doc.doc_type,
                    "business_id": doc.business_id,
                    "business_name": doc.business_name,
                    "current_version_id": doc.current_version_id,
                    "total_versions": doc.total_versions,
                    "status": doc.status,
                    "status_name": doc.status_name,
                    "total_pages": doc.total_pages,
                    "total_chunks": doc.total_chunks,
                    "creator_name": doc.creator_name,
                    "created_at": doc.created_at.isoformat() if doc.created_at else None
                })

            return {
                "items": result_items,
                "total": total
            }
        finally:
            db.close()

    def get_document(self, document_id: int) -> Dict[str, Any]:
        """
        获取文档详情

        Args:
            document_id: 文档ID

        Returns:
            文档详情字典

        Raises:
            BusinessException: 文档不存在时抛出
        """
        db = SessionLocal()
        try:
            document = db.query(Document).filter(
                Document.id == document_id,
                Document.is_deleted == 0
            ).first()

            if not document:
                raise BusinessException(
                    code=ErrorCode.DATA_NOT_FOUND[0],
                    message=f"文档不存在，ID: {document_id}"
                )

            # 获取版本列表
            versions = self.version_service.list_versions_with_db(db, document_id)

            version_list = [{
                "id": v.id,
                "version": v.version,
                "file_name": v.file_name,
                "file_size": v.file_size,
                "status": v.status,
                "parse_progress": v.parse_progress,
                "total_pages": v.total_pages,
                "uploader_name": v.uploader_name,
                "uploaded_at": v.uploaded_at.isoformat() if v.uploaded_at else None,
                "parsed_at": v.parsed_at.isoformat() if v.parsed_at else None
            } for v in versions]

            return {
                "id": document.id,
                "name": document.name,
                "doc_type": document.doc_type,
                "business_id": document.business_id,
                "business_name": document.business_name,
                "current_version_id": document.current_version_id,
                "total_versions": document.total_versions,
                "status": document.status,
                "status_name": document.status_name,
                "total_pages": document.total_pages,
                "total_chunks": document.total_chunks,
                "creator_id": document.creator_id,
                "creator_name": document.creator_name,
                "created_at": document.created_at.isoformat() if document.created_at else None,
                "updated_at": document.updated_at.isoformat() if document.updated_at else None,
                "versions": version_list
            }
        finally:
            db.close()

    def delete_document(self, document_id: int) -> bool:
        """
        删除文档（软删除）

        Args:
            document_id: 文档ID

        Returns:
            是否删除成功

        Raises:
            BusinessException: 文档不存在时抛出
        """
        db = SessionLocal()
        try:
            document = db.query(Document).filter(
                Document.id == document_id,
                Document.is_deleted == 0
            ).first()

            if not document:
                raise BusinessException(
                    code=ErrorCode.DATA_NOT_FOUND[0],
                    message=f"文档不存在，ID: {document_id}"
                )

            # 软删除
            document.is_deleted = 1
            document.status = 9  # 已删除
            db.commit()

            logger.info(
                f"文档删除成功",
                extra={"document_id": document_id}
            )

            return True
        except BusinessException:
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"文档删除失败: {str(e)}")
            raise BusinessException(
                code=ErrorCode.OPERATION_FAILED[0],
                message=f"文档删除失败: {str(e)}"
            )
        finally:
            db.close()

    def list_versions(self, document_id: int) -> List[Dict[str, Any]]:
        """
        获取版本列表

        Args:
            document_id: 文档ID

        Returns:
            版本列表

        Raises:
            BusinessException: 文档不存在时抛出
        """
        db = SessionLocal()
        try:
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

            # 获取版本列表
            versions = self.version_service.list_versions_with_db(db, document_id)

            return [{
                "id": v.id,
                "version": v.version,
                "file_name": v.file_name,
                "file_size": v.file_size,
                "file_hash": v.file_hash,
                "status": v.status,
                "parse_status": v.parse_status,
                "parse_progress": v.parse_progress,
                "total_pages": v.total_pages,
                "uploader_name": v.uploader_name,
                "uploaded_at": v.uploaded_at.isoformat() if v.uploaded_at else None,
                "parsed_at": v.parsed_at.isoformat() if v.parsed_at else None
            } for v in versions]
        finally:
            db.close()

    def get_version(self, document_id: int, version_id: int) -> Dict[str, Any]:
        """
        获取版本详情

        Args:
            document_id: 文档ID
            version_id: 版本ID

        Returns:
            版本详情

        Raises:
            BusinessException: 文档或版本不存在时抛出
        """
        db = SessionLocal()
        try:
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

            # 获取版本详情
            version = db.query(DocumentVersion).filter(
                DocumentVersion.id == version_id,
                DocumentVersion.document_id == document_id
            ).first()

            if not version:
                raise BusinessException(
                    code=ErrorCode.DATA_NOT_FOUND[0],
                    message=f"版本不存在，ID: {version_id}"
                )

            return {
                "id": version.id,
                "document_id": version.document_id,
                "version": version.version,
                "file_name": version.file_name,
                "file_size": version.file_size,
                "file_hash": version.file_hash,
                "file_path": version.file_path,
                "mime_type": version.mime_type,
                "storage_type": version.storage_type,
                "status": version.status,
                "parse_status": version.parse_status,
                "parse_progress": version.parse_progress,
                "parse_confidence": version.parse_confidence,
                "total_pages": version.total_pages,
                "total_elements": version.total_elements,
                "uploader_id": version.uploader_id,
                "uploader_name": version.uploader_name,
                "uploaded_at": version.uploaded_at.isoformat() if version.uploaded_at else None,
                "parsed_at": version.parsed_at.isoformat() if version.parsed_at else None,
                "error_message": version.error_message,
                "created_at": version.created_at.isoformat() if version.created_at else None
            }
        finally:
            db.close()

    def update_document_status(
        self,
        document_id: int,
        status: int,
        total_pages: Optional[int] = None,
        total_chunks: Optional[int] = None
    ) -> bool:
        """
        更新文档状态

        Args:
            document_id: 文档ID
            status: 新状态
            total_pages: 总页数
            total_chunks: 总Chunk数

        Returns:
            是否更新成功
        """
        db = SessionLocal()
        try:
            document = db.query(Document).filter(
                Document.id == document_id,
                Document.is_deleted == 0
            ).first()

            if not document:
                raise BusinessException(
                    code=ErrorCode.DATA_NOT_FOUND[0],
                    message=f"文档不存在，ID: {document_id}"
                )

            document.status = status
            if total_pages is not None:
                document.total_pages = total_pages
            if total_chunks is not None:
                document.total_chunks = total_chunks

            db.commit()

            logger.info(
                f"文档状态更新成功",
                extra={
                    "document_id": document_id,
                    "status": status
                }
            )

            return True
        except BusinessException:
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"文档状态更新失败: {str(e)}")
            raise BusinessException(
                code=ErrorCode.OPERATION_FAILED[0],
                message=f"文档状态更新失败: {str(e)}"
            )
        finally:
            db.close()

    def initialize_system(self) -> Dict[str, Any]:
        """
        初始化系统

        清空所有数据库表和向量数据库，回到初始状态。
        此操作会删除所有文档、版本、Chunk、关键词索引等数据。

        Returns:
            初始化结果统计

        Raises:
            BusinessException: 初始化失败时抛出
        """
        db = SessionLocal()
        try:
            result = {
                "documents_deleted": 0,
                "versions_deleted": 0,
                "chunks_deleted": 0,
                "keyword_indexes_deleted": 0,
                "tasks_deleted": 0,
                "qa_logs_deleted": 0,
                "feedback_analysis_deleted": 0,
                "optimization_rules_deleted": 0,
                "milvus_entities_deleted": 0,
                "files_deleted": 0,
                "errors": []
            }

            # 1. 获取所有文档的文件路径，用于后续删除文件
            all_versions = db.query(DocumentVersion).all()
            file_paths = [v.file_path for v in all_versions if v.file_path]
            result["files_deleted"] = len(file_paths)

            # 2. 清空关键词索引表
            try:
                keyword_count = db.query(ChunkKeywordIndex).count()
                db.query(ChunkKeywordIndex).delete()
                result["keyword_indexes_deleted"] = keyword_count
                logger.info(f"关键词索引表已清空，删除 {keyword_count} 条记录")
            except Exception as e:
                error_msg = f"清空关键词索引表失败: {str(e)}"
                logger.error(error_msg)
                result["errors"].append(error_msg)

            # 3. 清空Chunk表
            try:
                chunk_count = db.query(DocumentChunk).count()
                db.query(DocumentChunk).delete()
                result["chunks_deleted"] = chunk_count
                logger.info(f"Chunk表已清空，删除 {chunk_count} 条记录")
            except Exception as e:
                error_msg = f"清空Chunk表失败: {str(e)}"
                logger.error(error_msg)
                result["errors"].append(error_msg)

            # 4. 清空版本表
            try:
                version_count = db.query(DocumentVersion).count()
                db.query(DocumentVersion).delete()
                result["versions_deleted"] = version_count
                logger.info(f"版本表已清空，删除 {version_count} 条记录")
            except Exception as e:
                error_msg = f"清空版本表失败: {str(e)}"
                logger.error(error_msg)
                result["errors"].append(error_msg)

            # 5. 清空文档表
            try:
                doc_count = db.query(Document).count()
                db.query(Document).delete()
                result["documents_deleted"] = doc_count
                logger.info(f"文档表已清空，删除 {doc_count} 条记录")
            except Exception as e:
                error_msg = f"清空文档表失败: {str(e)}"
                logger.error(error_msg)
                result["errors"].append(error_msg)

            # 6. 清空导入任务表
            try:
                task_count = db.query(ImportTask).count()
                db.query(ImportTask).delete()
                result["tasks_deleted"] = task_count
                logger.info(f"导入任务表已清空，删除 {task_count} 条记录")
            except Exception as e:
                error_msg = f"清空导入任务表失败: {str(e)}"
                logger.error(error_msg)
                result["errors"].append(error_msg)

            # 7. 清空问答日志表
            try:
                qa_count = db.query(QALog).count()
                db.query(QALog).delete()
                result["qa_logs_deleted"] = qa_count
                logger.info(f"问答日志表已清空，删除 {qa_count} 条记录")
            except Exception as e:
                error_msg = f"清空问答日志表失败: {str(e)}"
                logger.error(error_msg)
                result["errors"].append(error_msg)

            # 8. 清空反馈分析表
            try:
                feedback_count = db.query(FeedbackAnalysis).count()
                db.query(FeedbackAnalysis).delete()
                result["feedback_analysis_deleted"] = feedback_count
                logger.info(f"反馈分析表已清空，删除 {feedback_count} 条记录")
            except Exception as e:
                error_msg = f"清空反馈分析表失败: {str(e)}"
                logger.error(error_msg)
                result["errors"].append(error_msg)

            # 9. 清空优化规则表
            try:
                rules_count = db.query(OptimizationRule).count()
                db.query(OptimizationRule).delete()
                result["optimization_rules_deleted"] = rules_count
                logger.info(f"优化规则表已清空，删除 {rules_count} 条记录")
            except Exception as e:
                error_msg = f"清空优化规则表失败: {str(e)}"
                logger.error(error_msg)
                result["errors"].append(error_msg)

            # 提交所有数据库更改
            db.commit()

            # 10. 删除物理文件
            from pathlib import Path
            for file_path in file_paths:
                try:
                    path = Path(file_path)
                    if path.exists():
                        path.unlink()
                except Exception as e:
                    logger.warning(f"删除文件失败: {file_path}, 错误: {str(e)}")

            # 11. 清空Milvus向量数据库
            try:
                milvus_client = get_milvus_client()
                collection_name = "document_chunks"

                # 检查集合是否存在
                from pymilvus import utility
                if utility.has_collection(collection_name, using=milvus_client._alias):
                    # 获取集合并删除所有数据
                    collection = milvus_client.get_collection(collection_name)

                    # 使用drop方式更彻底
                    milvus_client.drop_collection(collection_name)
                    logger.info(f"Milvus集合 {collection_name} 已删除")

                    # 重新创建集合
                    milvus_client.create_collection(
                        collection_name=collection_name,
                        dimension=settings.embedding.dimension,
                        description="RAG知识库文档块向量集合"
                    )
                    logger.info(f"Milvus集合 {collection_name} 已重新创建")

                    result["milvus_entities_deleted"] = "all (collection dropped and recreated)"
            except Exception as e:
                error_msg = f"清空Milvus向量数据库失败: {str(e)}"
                logger.error(error_msg)
                result["errors"].append(error_msg)

            # 12. 清空上传文件目录（只清空default目录）
            try:
                storage_path = Path(settings.document.storage.base_path)
                default_path = storage_path / "default"
                if default_path.exists():
                    import shutil
                    for item in default_path.iterdir():
                        if item.is_file():
                            item.unlink()
                        elif item.is_dir():
                            shutil.rmtree(item)
                    logger.info(f"上传文件目录已清空: {default_path}")
            except Exception as e:
                logger.warning(f"清空上传目录失败: {str(e)}")

            logger.info(
                f"系统初始化完成",
                extra={
                    "result": result
                }
            )

            return result

        except Exception as e:
            db.rollback()
            logger.error(f"系统初始化失败: {str(e)}")
            raise BusinessException(
                code=ErrorCode.OPERATION_FAILED[0],
                message=f"系统初始化失败: {str(e)}"
            )
        finally:
            db.close()
