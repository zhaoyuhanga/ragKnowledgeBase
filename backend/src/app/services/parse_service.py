# -*- coding: utf-8 -*-
"""
解析服务

本模块提供文档解析的调度服务，包括：
- 解析任务创建和管理
- 解析器注册和选择
- 解析状态查询
- 解析结果保存
"""

import os
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.common.exception import BusinessException, ErrorCode
from app.common.logging import logger
from app.models.document import Document, DocumentVersion
from app.models.parse import DocumentElement, ParseQualityLog
from app.parsers.base import (
    ParserRegistry,
    get_parser_registry,
    register_parser,
)
from app.parsers.layout_analyzer import LayoutAnalyzer
from core.database import SessionLocal


class ParseService:
    """
    文档解析调度服务

    负责协调文档解析流程，包括解析器选择、解析执行、结果保存等。
    """

    def __init__(self):
        """初始化解析服务"""
        self._registry = get_parser_registry()
        self._analyzer = LayoutAnalyzer()
        self._register_parsers()

    def _register_parsers(self) -> None:
        """注册所有解析器"""
        from app.parsers.word_parser import WordParser
        from app.parsers.pdf_parser import PdfParser
        from app.parsers.image_parser import ImageParser
        from app.parsers.table_parser import TableParser
        from app.parsers.text_parser import TextParser

        # 注册解析器
        self._registry.register("docx", WordParser())
        self._registry.register("doc", WordParser())
        self._registry.register("pdf", PdfParser())
        self._registry.register("png", ImageParser())
        self._registry.register("jpg", ImageParser())
        self._registry.register("jpeg", ImageParser())
        self._registry.register("xlsx", TableParser())
        self._registry.register("xls", TableParser())
        self._registry.register("csv", TableParser())
        self._registry.register("txt", TextParser())
        self._registry.register("md", TextParser())
        self._registry.register("markdown", TextParser())
        self._registry.register("html", TextParser())
        self._registry.register("htm", TextParser())

    def parse_document(
        self,
        document_id: int,
        version_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        解析文档

        Args:
            document_id: 文档ID
            version_id: 版本ID，如果为None则使用最新版本

        Returns:
            解析结果
        """
        db = SessionLocal()
        try:
            # ========== 阶段1：获取文档信息 ==========
            logger.info(
                f"开始解析文档",
                extra={
                    "document_id": document_id,
                    "version_id": version_id
                }
            )
            
            try:
                document = db.query(Document).filter(
                    Document.id == document_id,
                    Document.is_deleted == 0
                ).first()

                if not document:
                    logger.error(
                        f"文档不存在",
                        extra={
                            "document_id": document_id
                        }
                    )
                    raise BusinessException(
                        code=ErrorCode.DATA_NOT_FOUND[0],
                        message=f"文档不存在，ID: {document_id}"
                    )
            except BusinessException:
                raise
            except Exception as e:
                logger.error(
                    f"查询文档信息失败",
                    extra={
                        "document_id": document_id,
                        "error_type": type(e).__name__,
                        "error_message": str(e)
                    }
                )
                raise BusinessException(
                    code=ErrorCode.DATABASE_ERROR[0],
                    message=f"查询文档信息失败: {str(e)}"
                )

            # ========== 阶段2：获取版本信息 ==========
            try:
                if version_id:
                    version = db.query(DocumentVersion).filter(
                        DocumentVersion.id == version_id,
                        DocumentVersion.document_id == document_id
                    ).first()
                else:
                    version = db.query(DocumentVersion).filter(
                        DocumentVersion.document_id == document_id
                    ).order_by(DocumentVersion.version.desc()).first()

                if not version:
                    logger.error(
                        f"文档版本不存在",
                        extra={
                            "document_id": document_id,
                            "version_id": version_id
                        }
                    )
                    raise BusinessException(
                        code=ErrorCode.DATA_NOT_FOUND[0],
                        message=f"文档版本不存在"
                    )
                    
                logger.debug(
                    f"版本信息获取成功",
                    extra={
                        "document_id": document_id,
                        "version_id": version.id,
                        "version_number": version.version,
                        "file_path": version.file_path
                    }
                )
            except BusinessException:
                raise
            except Exception as e:
                logger.error(
                    f"查询版本信息失败",
                    extra={
                        "document_id": document_id,
                        "version_id": version_id,
                        "error_type": type(e).__name__,
                        "error_message": str(e)
                    }
                )
                raise BusinessException(
                    code=ErrorCode.DATABASE_ERROR[0],
                    message=f"查询版本信息失败: {str(e)}"
                )

            # ========== 阶段3：检查文件是否存在 ==========
            try:
                if not os.path.exists(version.file_path):
                    logger.error(
                        f"文件不存在",
                        extra={
                            "document_id": document_id,
                            "version_id": version.id,
                            "file_path": version.file_path
                        }
                    )
                    raise BusinessException(
                        code=ErrorCode.FILE_NOT_FOUND[0],
                        message=f"文件不存在: {version.file_path}"
                    )
                    
                logger.debug(
                    f"文件存在检查通过",
                    extra={
                        "file_path": version.file_path
                    }
                )
            except BusinessException:
                raise
            except Exception as e:
                logger.error(
                    f"检查文件存在性失败",
                    extra={
                        "file_path": version.file_path,
                        "error_type": type(e).__name__,
                        "error_message": str(e)
                    }
                )
                raise BusinessException(
                    code=ErrorCode.FILE_NOT_FOUND[0],
                    message=f"检查文件存在性失败: {str(e)}"
                )

            # ========== 阶段4：获取解析器 ==========
            try:
                parser = self._registry.get_parser(version.file_path)
                if not parser:
                    logger.error(
                        f"不支持的文件类型",
                        extra={
                            "document_id": document_id,
                            "version_id": version.id,
                            "file_path": version.file_path
                        }
                    )
                    raise BusinessException(
                        code=ErrorCode.PARSE_FAILED[0],
                        message=f"不支持的文件类型: {version.file_path}"
                    )
                    
                logger.debug(
                    f"解析器获取成功",
                    extra={
                        "parser_type": parser.__class__.__name__,
                        "file_path": version.file_path
                    }
                )
            except BusinessException:
                raise
            except Exception as e:
                logger.error(
                    f"获取解析器失败",
                    extra={
                        "file_path": version.file_path,
                        "error_type": type(e).__name__,
                        "error_message": str(e)
                    }
                )
                raise BusinessException(
                    code=ErrorCode.PARSE_FAILED[0],
                    message=f"获取解析器失败: {str(e)}"
                )

            # ========== 阶段5：更新版本状态为解析中 ==========
            try:
                version.status = 1
                version.parse_status = "processing"
                version.parse_progress = 10  # 开始解析，进度10%
                db.commit()
                
                logger.info(
                    f"文档状态已更新为解析中",
                    extra={
                        "document_id": document_id,
                        "version_id": version.id
                    }
                )
            except Exception as e:
                logger.warning(
                    f"更新版本状态失败",
                    extra={
                        "document_id": document_id,
                        "version_id": version.id,
                        "error_type": type(e).__name__,
                        "error_message": str(e)
                    }
                )

            # 获取文件扩展名
            file_ext = os.path.splitext(version.file_path)[1].lower().lstrip(".")

            # ========== 阶段6：执行解析 ==========
            try:
                logger.info(
                    f"开始执行文档解析",
                    extra={
                        "document_id": document_id,
                        "version_id": version.id,
                        "file_path": version.file_path,
                        "file_ext": file_ext,
                        "parser_type": parser.__class__.__name__
                    }
                )
                
                elements = parser.parse(
                    file_path=version.file_path,
                    version_id=version.id,
                    document_id=document_id
                )
                
                logger.info(
                    f"文档解析完成，提取到元素",
                    extra={
                        "document_id": document_id,
                        "version_id": version.id,
                        "element_count": len(elements) if elements else 0
                    }
                )

            except Exception as e:
                # 解析失败
                version.status = 3  # 解析失败
                version.parse_status = "failed"
                version.error_message = str(e)
                document.status = 3  # 解析失败
                db.commit()

                logger.error(
                    f"文档解析执行失败",
                    extra={
                        "document_id": document_id,
                        "version_id": version.id,
                        "file_path": version.file_path,
                        "file_ext": file_ext,
                        "parser_type": parser.__class__.__name__,
                        "error_type": type(e).__name__,
                        "error_class": e.__class__.__name__,
                        "error_message": str(e),
                        "error_module": type(e).__module__
                    }
                )

                raise BusinessException(
                    code=ErrorCode.PARSE_FAILED[0],
                    message=f"文档解析失败: {str(e)}"
                )

            # ========== 阶段7：版面分析 ==========
            try:
                logger.debug(
                    f"开始版面分析",
                    extra={
                        "document_id": document_id,
                        "version_id": version.id,
                        "element_count": len(elements)
                    }
                )
                elements = self._analyzer.analyze(elements)
                
                logger.debug(
                    f"版面分析完成",
                    extra={
                        "document_id": document_id,
                        "version_id": version.id,
                        "element_count": len(elements)
                    }
                )
            except Exception as e:
                logger.warning(
                    f"版面分析失败",
                    extra={
                        "document_id": document_id,
                        "version_id": version.id,
                        "error_type": type(e).__name__,
                        "error_message": str(e)
                    }
                )

            # ========== 阶段8：保存元素 ==========
            try:
                logger.debug(
                    f"开始保存解析元素",
                    extra={
                        "document_id": document_id,
                        "version_id": version.id,
                        "element_count": len(elements)
                    }
                )
                # 保存元素前更新进度到50%
                version.parse_progress = 50
                db.commit()
                
                self._save_elements(db, elements, document_id, version.id)
                
                logger.debug(
                    f"解析元素保存完成",
                    extra={
                        "document_id": document_id,
                        "version_id": version.id,
                        "element_count": len(elements)
                    }
                )
            except Exception as e:
                logger.error(
                    f"保存解析元素失败",
                    extra={
                        "document_id": document_id,
                        "version_id": version.id,
                        "element_count": len(elements),
                        "error_type": type(e).__name__,
                        "error_message": str(e)
                    }
                )
                raise BusinessException(
                    code=ErrorCode.PARSE_FAILED[0],
                    message=f"保存解析元素失败: {str(e)}"
                )

            # ========== 阶段9：更新版本和文档状态 ==========
            try:
                version.status = 2  # 已解析
                version.parse_status = "completed"
                version.parse_progress = 100  # 解析进度100%
                version.total_pages = self._get_actual_page_count(version.file_path, file_ext)
                version.total_elements = len(elements)

                document.status = 2  # 已解析
                document.total_pages = version.total_pages
                document.total_chunks = version.total_elements

                db.commit()
                
                logger.info(
                    f"文档解析成功",
                    extra={
                        "document_id": document_id,
                        "version_id": version.id,
                        "total_elements": len(elements),
                        "total_pages": version.total_pages
                    }
                )

                return {
                    "document_id": document_id,
                    "version_id": version.id,
                    "status": "completed",
                    "total_elements": len(elements),
                    "total_pages": version.total_pages
                }

            except Exception as e:
                logger.error(
                    f"更新文档状态失败",
                    extra={
                        "document_id": document_id,
                        "version_id": version.id,
                        "error_type": type(e).__name__,
                        "error_message": str(e)
                    }
                )
                raise BusinessException(
                    code=ErrorCode.DATABASE_ERROR[0],
                    message=f"更新文档状态失败: {str(e)}"
                )

        except BusinessException:
            raise
        except Exception as e:
            logger.error(
                f"文档解析异常",
                extra={
                    "document_id": document_id,
                    "version_id": version_id,
                    "error_type": type(e).__name__,
                    "error_class": e.__class__.__name__,
                    "error_message": str(e),
                    "error_module": type(e).__module__
                }
            )
            raise BusinessException(
                code=ErrorCode.PARSE_FAILED[0],
                message=f"文档解析异常: {str(e)}"
            )
        finally:
            db.close()

    def _save_elements(
        self,
        db,
        elements: List[Any],
        document_id: int,
        version_id: int
    ) -> None:
        """
        保存解析元素到数据库

        Args:
            db: 数据库会话
            elements: 元素列表
            document_id: 文档ID
            version_id: 版本ID
        """
        for element in elements:
            # 转换元素为数据库模型
            element_dict = element.to_dict() if hasattr(element, "to_dict") else element

            db_element = DocumentElement(
                document_id=document_id,
                version_id=version_id,
                element_id=element_dict.get("element_id", ""),
                page_no=element_dict.get("page_no"),
                page_start=element_dict.get("page_start"),
                page_end=element_dict.get("page_end"),
                element_type=element_dict.get("element_type", "paragraph"),
                content=element_dict.get("content"),
                enhanced_content=element_dict.get("enhanced_content"),
                reading_order=element_dict.get("reading_order", 0),
                title_level=element_dict.get("title_level"),
                title_path=element_dict.get("title_path"),
                parent_path=element_dict.get("parent_path"),
                bbox=element_dict.get("bbox"),
                confidence=element_dict.get("confidence", 1.0),
                is_merged=1 if element_dict.get("is_merged") else 0,
                table_structure=element_dict.get("table_structure"),
                image_description=element_dict.get("image_description"),
                metadata=element_dict.get("metadata"),
                quality_flag=element_dict.get("quality_flag", "good")
            )
            db.add(db_element)

            # 记录质量日志（只记录低质量元素）
            quality_flag = element_dict.get("quality_flag", "good")
            if quality_flag != "good":
                log = ParseQualityLog(
                    document_id=document_id,
                    version_id=version_id,
                    page_no=element_dict.get("page_no"),
                    element_id=element_dict.get("element_id"),
                    check_type="low_confidence",
                    quality_flag=quality_flag,
                    confidence=element_dict.get("confidence"),
                    issue_description=f"元素置信度为 {element_dict.get('confidence', 0)}",
                    suggestion="请检查原始文档质量"
                )
                db.add(log)

    def _count_pages(self, elements: List[Any]) -> int:
        """
        统计页数

        Args:
            elements: 元素列表

        Returns:
            页数
        """
        page_nos = set()
        for element in elements:
            if hasattr(element, "page_no") and element.page_no:
                page_nos.add(element.page_no)
        return len(page_nos) if page_nos else 1

    def _get_actual_page_count(self, file_path: str, file_ext: str) -> int:
        """
        从文件直接获取实际页数

        Args:
            file_path: 文件路径
            file_ext: 文件扩展名

        Returns:
            实际页数
        """
        try:
            if file_ext.lower() == "pdf":
                import fitz
                doc = fitz.open(file_path)
                count = len(doc)
                doc.close()
                logger.debug(f"PDF文件页数: {count}", extra={"file_path": file_path})
                return count if count > 0 else 1
            elif file_ext.lower() in ["docx", "doc"]:
                from docx import Document
                doc = Document(file_path)
                # Word文档使用section数近似页数，或者返回1
                # 因为Word的真实页数需要渲染才能确定
                count = max(1, len(doc.sections))
                logger.debug(f"Word文档页数: {count}", extra={"file_path": file_path})
                return count
            elif file_ext.lower() in ["xlsx", "xls"]:
                import openpyxl
                wb = openpyxl.load_workbook(file_path, data_only=True)
                count = len(wb.sheetnames)
                wb.close()
                logger.debug(f"Excel工作表数: {count}", extra={"file_path": file_path})
                return count if count > 0 else 1
            elif file_ext.lower() == "csv":
                return 1
            else:
                return 1
        except Exception as e:
            logger.warning(
                f"获取文件页数失败",
                extra={
                    "file_path": file_path,
                    "file_ext": file_ext,
                    "error_type": type(e).__name__,
                    "error_message": str(e)
                }
            )
            return 1

    def get_parse_status(self, document_id: int) -> Dict[str, Any]:
        """
        获取解析状态

        Args:
            document_id: 文档ID

        Returns:
            解析状态
        """
        db = SessionLocal()
        try:
            # 获取文档信息
            document = db.query(Document).filter(
                Document.id == document_id,
                Document.is_deleted == 0
            ).first()

            if not document:
                raise BusinessException(
                    code=ErrorCode.DATA_NOT_FOUND[0],
                    message=f"文档不存在，ID: {document_id}"
                )

            # 获取最新版本
            version = db.query(DocumentVersion).filter(
                DocumentVersion.document_id == document_id
            ).order_by(DocumentVersion.version.desc()).first()

            if not version:
                return {
                    "document_id": document_id,
                    "version_id": None,
                    "status": document.status,
                    "status_name": self._get_status_name(document.status),
                    "parse_progress": 0,
                    "total_pages": 0,
                    "total_elements": 0,
                    "quality_summary": {"good": 0, "warning": 0, "bad": 0}
                }

            # 获取元素统计
            total_elements = db.query(DocumentElement).filter(
                DocumentElement.version_id == version.id
            ).count()

            quality_stats = {
                "good": db.query(DocumentElement).filter(
                    DocumentElement.version_id == version.id,
                    DocumentElement.quality_flag == "good"
                ).count(),
                "warning": db.query(DocumentElement).filter(
                    DocumentElement.version_id == version.id,
                    DocumentElement.quality_flag == "warning"
                ).count(),
                "bad": db.query(DocumentElement).filter(
                    DocumentElement.version_id == version.id,
                    DocumentElement.quality_flag == "bad"
                ).count()
            }

            # 计算解析进度
            parse_progress = 0
            if version.parse_status == "completed":
                parse_progress = 100
            elif version.parse_status == "processing":
                parse_progress = version.parse_progress or 50

            return {
                "document_id": document_id,
                "version_id": version.id,
                "status": document.status,
                "status_name": self._get_status_name(document.status),
                "parse_progress": parse_progress,
                "total_pages": version.total_pages or 0,
                "total_elements": total_elements,
                "quality_summary": quality_stats,
                "started_at": version.created_at.isoformat() if version.created_at else None,
                "completed_at": version.parsed_at.isoformat() if version.parsed_at else None
            }

        finally:
            db.close()

    def _get_status_name(self, status: int) -> str:
        """获取状态名称"""
        status_map = {
            0: "待解析",
            1: "解析中",
            2: "已解析",
            3: "解析失败",
            9: "已删除"
        }
        return status_map.get(status, "未知")

    def get_elements(
        self,
        document_id: int,
        page_no: Optional[int] = None,
        element_type: Optional[str] = None,
        quality_flag: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        获取解析元素列表

        Args:
            document_id: 文档ID
            page_no: 页码筛选
            element_type: 元素类型筛选
            quality_flag: 质量标记筛选

        Returns:
            元素列表
        """
        db = SessionLocal()
        try:
            query = db.query(DocumentElement).filter(
                DocumentElement.document_id == document_id
            )

            if page_no is not None:
                query = query.filter(DocumentElement.page_no == page_no)

            if element_type:
                query = query.filter(DocumentElement.element_type == element_type)

            if quality_flag:
                query = query.filter(DocumentElement.quality_flag == quality_flag)

            elements = query.order_by(
                DocumentElement.reading_order
            ).all()

            return [self._element_to_dict(e) for e in elements]

        finally:
            db.close()

    def _element_to_dict(self, element: DocumentElement) -> Dict[str, Any]:
        """将元素转换为字典"""
        return {
            "id": element.id,
            "element_id": element.element_id,
            "page_no": element.page_no,
            "page_start": element.page_start,
            "page_end": element.page_end,
            "element_type": element.element_type,
            "content": element.content,
            "enhanced_content": element.enhanced_content,
            "reading_order": element.reading_order,
            "title_level": element.title_level,
            "title_path": element.title_path,
            "bbox": element.bbox,
            "confidence": element.confidence,
            "is_merged": bool(element.is_merged),
            "table_structure": element.table_structure,
            "image_description": element.image_description,
            "metadata": element.element_metadata,
            "quality_flag": element.quality_flag,
            "created_at": element.created_at.isoformat() if element.created_at else None
        }


    def parse_document_sync(
        self,
        document_id: int,
        version_id: Optional[int] = None,
        enable_cleaning: bool = True,
        enable_chunking: bool = True,
        enable_embedding: bool = True
    ) -> Dict[str, Any]:
        """
        同步解析文档（完整流程）

        一次性完成解析、清洗、切分和向量化，适用于Worker未运行的场景。

        Args:
            document_id: 文档ID
            version_id: 版本ID，如果为None则使用最新版本
            enable_cleaning: 是否启用清洗
            enable_chunking: 是否启用切分
            enable_embedding: 是否启用向量化

        Returns:
            完整处理结果
        """
        from app.services.clean_service import get_clean_service
        from app.services.chunk_service import get_chunk_service
        from app.services.embedding_service import get_chunk_embedding_service
        from app.models.parse import DocumentElement

        logger.info(
            f"开始同步解析文档",
            extra={
                "document_id": document_id,
                "version_id": version_id,
                "enable_cleaning": enable_cleaning,
                "enable_chunking": enable_chunking,
                "enable_embedding": enable_embedding
            }
        )

        # 步骤1: 解析文档
        logger.info("步骤1: 解析文档...")
        try:
            parse_result = self.parse_document(document_id, version_id)
            actual_version_id = parse_result["version_id"]
        except Exception as e:
            logger.error(
                f"步骤1解析文档失败",
                extra={
                    "document_id": document_id,
                    "version_id": version_id,
                    "error_type": type(e).__name__,
                    "error_message": str(e)
                }
            )
            raise

        # 步骤2: 获取元素列表
        db = SessionLocal()
        try:
            elements = db.query(DocumentElement).filter(
                DocumentElement.version_id == actual_version_id
            ).order_by(DocumentElement.reading_order).all()
        except Exception as e:
            logger.error(
                f"查询解析元素失败",
                extra={
                    "version_id": actual_version_id,
                    "error_type": type(e).__name__,
                    "error_message": str(e)
                }
            )
            db.close()
            raise
        finally:
            pass

        if not elements:
            logger.warning(
                f"文档没有可处理的元素",
                extra={
                    "document_id": document_id,
                    "version_id": actual_version_id
                }
            )
            return {
                **parse_result,
                "stages": {
                    "parsing": {"status": "completed", "elements": 0},
                    "cleaning": {"status": "skipped", "reason": "no_elements"},
                    "chunking": {"status": "skipped", "reason": "no_elements"},
                    "embedding": {"status": "skipped", "reason": "no_elements"}
                }
            }

        logger.info(f"获取到 {len(elements)} 个解析元素")

        result = {
            **parse_result,
            "stages": {}
        }

        # 步骤3: 清洗文档
        if enable_cleaning:
            logger.info("步骤2: 清洗文档...")
            try:
                clean_service = get_clean_service()
                clean_result = clean_service.clean_document(
                    document_id=document_id,
                    version_id=actual_version_id,
                    elements=elements
                )
                result["stages"]["cleaning"] = {
                    "status": "completed",
                    "cleaned_count": clean_result.success_count,
                    "warning_count": clean_result.warning_count,
                    "bad_count": clean_result.bad_count
                }
                logger.info(
                    f"清洗完成",
                    extra={
                        "document_id": document_id,
                        "success_count": clean_result.success_count,
                        "warning_count": clean_result.warning_count,
                        "bad_count": clean_result.bad_count
                    }
                )
            except Exception as e:
                logger.error(
                    f"清洗文档失败",
                    extra={
                        "document_id": document_id,
                        "version_id": actual_version_id,
                        "error_type": type(e).__name__,
                        "error_message": str(e)
                    }
                )
                result["stages"]["cleaning"] = {
                    "status": "failed",
                    "error": str(e)
                }
        else:
            result["stages"]["cleaning"] = {"status": "skipped"}

        # 步骤4: 切分文档
        if enable_chunking:
            logger.info("步骤3: 切分文档...")
            try:
                chunk_service = get_chunk_service()
                chunk_result = chunk_service.chunk_document(
                    document_id=document_id,
                    version_id=actual_version_id,
                    elements=elements
                )

                # 保存chunks到数据库
                saved_ids = chunk_service.save_chunks(
                    document_id=document_id,
                    version_id=actual_version_id,
                    chunks=chunk_result.chunks
                )

                result["stages"]["chunking"] = {
                    "status": "completed",
                    "total_chunks": chunk_result.total_chunks,
                    "saved_chunks": len(saved_ids),
                    "strategy": chunk_result.strategy_used
                }
                result["total_chunks"] = chunk_result.total_chunks
                
                logger.info(
                    f"文档切分完成",
                    extra={
                        "document_id": document_id,
                        "total_chunks": chunk_result.total_chunks,
                        "saved_chunks": len(saved_ids),
                        "strategy": chunk_result.strategy_used
                    }
                )
            except Exception as e:
                logger.error(
                    f"切分文档失败",
                    extra={
                        "document_id": document_id,
                        "version_id": actual_version_id,
                        "element_count": len(elements),
                        "error_type": type(e).__name__,
                        "error_message": str(e)
                    }
                )
                result["stages"]["chunking"] = {
                    "status": "failed",
                    "error": str(e)
                }
        else:
            result["stages"]["chunking"] = {"status": "skipped"}

        # 步骤5: 向量化
        if enable_embedding:
            logger.info("步骤4: 向量化...")
            try:
                embedding_service = get_chunk_embedding_service()
                embedding_result = embedding_service.embed_document_chunks(
                    document_id=document_id,
                    version_id=actual_version_id
                )

                result["stages"]["embedding"] = {
                    "status": "completed",
                    "total_chunks": embedding_result.total_chunks,
                    "processed_chunks": embedding_result.processed_chunks,
                    "cached_count": embedding_result.cached_count,
                    "processing_time_ms": embedding_result.processing_time_ms
                }
                
                logger.info(
                    f"文档向量化完成",
                    extra={
                        "document_id": document_id,
                        "total_chunks": embedding_result.total_chunks,
                        "processed_chunks": embedding_result.processed_chunks,
                        "cached_count": embedding_result.cached_count,
                        "processing_time_ms": embedding_result.processing_time_ms
                    }
                )
            except Exception as e:
                logger.error(
                    f"向量化文档失败",
                    extra={
                        "document_id": document_id,
                        "version_id": actual_version_id,
                        "error_type": type(e).__name__,
                        "error_message": str(e)
                    }
                )
                result["stages"]["embedding"] = {
                    "status": "failed",
                    "error": str(e)
                }

                # 即使向量化失败，也标记文档状态
                db_inner = SessionLocal()
                try:
                    document = db_inner.query(Document).filter(Document.id == document_id).first()
                    if document:
                        document.status = 5  # 部分完成
                    db_inner.commit()
                except Exception as inner_e:
                    logger.warning(f"更新文档状态失败: {str(inner_e)}")
                    db_inner.rollback()
                finally:
                    db_inner.close()
        else:
            result["stages"]["embedding"] = {"status": "skipped"}

        # 更新文档状态为已完成
        try:
            document = db.query(Document).filter(Document.id == document_id).first()
            if document:
                document.status = 4  # 已完成
            db.commit()
        except Exception as e:
            logger.warning(
                f"更新文档状态失败",
                extra={
                    "document_id": document_id,
                    "error_type": type(e).__name__,
                    "error_message": str(e)
                }
            )
            db.rollback()
        finally:
            db.close()

        logger.info(
            f"同步解析流程完成",
            extra={
                "document_id": document_id,
                "version_id": actual_version_id,
                "stages": result.get("stages", {})
            }
        )

        return result


# 全局服务实例
_parse_service: Optional[ParseService] = None


def get_parse_service() -> ParseService:
    """获取解析服务实例"""
    global _parse_service
    if _parse_service is None:
        _parse_service = ParseService()
    return _parse_service
