"""
RAG 问答系统 - 文档服务模块
文档上传、解析、存储和管理
"""

import os
import uuid
import time
from pathlib import Path
from typing import List, Optional, Tuple

from sqlalchemy.orm import Session

from app.config import settings
from app.models.document import Document, DocumentChunk
from app.utils.file_parser import FileParser, file_parser
from app.utils.text_splitter import TextSplitter, text_splitter
from app.services.embedding_service import embedding_service, get_embedding_service
from app.core.vectorstore import vector_store, get_vector_store
from app.core.database import get_db_session
from app.core.logger import get_logger, document_logger
from app.core.runtime_config import runtime_config

logger = get_logger(__name__)


def safe_filename(filename: str) -> str:
    """安全处理文件名"""
    safe_name = "".join(c if c.isalnum() or c in ".-_ " else "_" for c in filename)
    return safe_name


class DocumentService:
    """文档服务"""

    def __init__(
        self,
        parser: FileParser = None,
        splitter: TextSplitter = None,
    ):
        self.parser = parser or file_parser
        self.splitter = splitter or text_splitter
        self.embedding_service = get_embedding_service()
        self.vector_store = get_vector_store()

    async def upload_document(
        self,
        file_content: bytes,
        filename: str,
        db: Session
    ) -> Document:
        """上传并处理文档"""
        start_time = time.time()

        file_type = self.parser.get_file_type(filename)
        if not file_type:
            raise ValueError(f"不支持的文件类型: {filename}")

        safe_original_name = safe_filename(filename)
        unique_filename = f"{uuid.uuid4().hex}_{safe_original_name}"
        file_path = os.path.join(settings.upload_dir, unique_filename)

        os.makedirs(settings.upload_dir, exist_ok=True)

        with open(file_path, "wb") as f:
            f.write(file_content)

        file_size = len(file_content)
        document_logger.log_upload(filename, file_size, "uploaded")

        content_hash = self.parser.calculate_hash(file_path)

        document = Document(
            filename=filename,
            file_path=file_path,
            file_type=file_type,
            file_size=file_size,
            content_hash=content_hash,
            status=0,
        )

        db.add(document)
        db.commit()
        db.refresh(document)

        logger.info(f"文档上传成功: {filename}, ID: {document.id}")

        await self._process_document_async(document.id, file_path, file_type, db)

        elapsed = (time.time() - start_time) * 1000
        document_logger.log_upload(filename, file_size, "completed", duration_ms=elapsed)

        return document

    async def _process_document_async(
        self,
        document_id: int,
        file_path: str,
        file_type: str,
        db: Session
    ):
        """异步处理文档"""
        start_time = time.time()

        try:
            logger.info(f"正在解析文档: {file_path}")
            content, _ = self.parser.parse_file(file_path, file_type)

            if not content or not content.strip():
                raise ValueError("文档内容为空")

            logger.info(f"正在切分文档文本...")
            splitter = TextSplitter(
                chunk_size=runtime_config.chunk_size,
                chunk_overlap=runtime_config.chunk_overlap,
                min_chunk_size=runtime_config.chunk_min_size,
            )
            chunks = splitter.split_text(content)

            if not chunks:
                raise ValueError("文档切分后无有效内容")

            logger.info(f"正在向量化 {len(chunks)} 个文本块...")
            embeddings = self.embedding_service.encode(chunks)

            vector_ids = [f"{document_id}_{i}_{uuid.uuid4().hex[:8]}" for i in range(len(chunks))]

            metadatas = [
                {
                    "document_id": document_id,
                    "chunk_index": i,
                    "filename": Path(file_path).name,
                    "file_type": file_type,
                    "char_count": len(chunk),
                }
                for i, chunk in enumerate(chunks)
            ]

            self.vector_store.add_vectors(
                documents=chunks,
                embeddings=embeddings,
                ids=vector_ids,
                metadatas=metadatas
            )

            for i, (chunk, vector_id, metadata) in enumerate(zip(chunks, vector_ids, metadatas)):
                chunk_record = DocumentChunk(
                    document_id=document_id,
                    chunk_index=i,
                    content=chunk,
                    char_count=len(chunk),
                    vector_id=vector_id,
                )
                db.add(chunk_record)

            document = db.query(Document).filter(Document.id == document_id).first()
            document.status = 1
            document.chunk_count = len(chunks)

            db.commit()

            elapsed = (time.time() - start_time) * 1000
            document_logger.log_indexing(document_id, len(chunks), "completed", duration_ms=elapsed)
            logger.info(f"文档处理完成: {document_id}, 耗时: {elapsed:.2f}ms")

        except Exception as e:
            logger.error(f"文档处理失败: {document_id}, {str(e)}")

            document = db.query(Document).filter(Document.id == document_id).first()
            if document:
                document.status = 2
                document.error_message = str(e)
                db.commit()

            document_logger.log_indexing(document_id, 0, "failed", error=str(e))
            raise

    def get_document(self, document_id: int, db: Session) -> Optional[Document]:
        """获取文档详情"""
        return db.query(Document).filter(Document.id == document_id).first()

    def get_document_list(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 20,
        status: int = None,
        source_type: str = None,
        llm_model: str = None,
        llm_provider: str = None,
        generated_at_start=None,
        generated_at_end=None,
        question_keyword: str = None
    ) -> Tuple[List[Document], int]:
        """获取文档列表
        
        Args:
            db: 数据库会话
            skip: 跳过数量
            limit: 返回数量
            status: 状态过滤
            source_type: 来源类型过滤: local | ai_generated
            llm_model: LLM模型过滤
            llm_provider: LLM提供商过滤
            generated_at_start: 生成时间开始
            generated_at_end: 生成时间结束
            question_keyword: 原始问题关键词
        """
        query = db.query(Document)

        if status is not None:
            query = query.filter(Document.status == status)
        
        if source_type:
            query = query.filter(Document.source_type == source_type)
        
        if llm_model:
            query = query.filter(Document.llm_model == llm_model)
        
        if llm_provider:
            query = query.filter(Document.llm_provider == llm_provider)
        
        if generated_at_start:
            query = query.filter(Document.generated_at >= generated_at_start)
        
        if generated_at_end:
            query = query.filter(Document.generated_at <= generated_at_end)
        
        if question_keyword:
            query = query.filter(Document.generated_from_question.like(f"%{question_keyword}%"))

        total = query.count()
        documents = query.order_by(Document.created_at.desc()).offset(skip).limit(limit).all()

        return documents, total

    def delete_document(self, document_id: int, db: Session) -> bool:
        """删除文档"""
        document = db.query(Document).filter(Document.id == document_id).first()

        if not document:
            return False

        try:
            self.vector_store.delete_by_document_id(document_id)

            if os.path.exists(document.file_path):
                os.remove(document.file_path)

            db.delete(document)
            db.commit()

            logger.info(f"文档删除成功: {document_id}")
            return True

        except Exception as e:
            logger.error(f"删除文档失败: {document_id}, {str(e)}")
            db.rollback()
            raise

    def get_document_content(self, document_id: int, db: Session) -> Optional[str]:
        """获取文档内容预览"""
        chunks = db.query(DocumentChunk).filter(
            DocumentChunk.document_id == document_id
        ).order_by(DocumentChunk.chunk_index).all()

        if not chunks:
            return None

        return "\n\n".join([chunk.content for chunk in chunks])

    def get_document_chunks(
        self,
        document_id: int,
        db: Session
    ) -> List[DocumentChunk]:
        """获取文档的所有块"""
        return db.query(DocumentChunk).filter(
            DocumentChunk.document_id == document_id
        ).order_by(DocumentChunk.chunk_index).all()


# 创建全局文档服务实例
document_service = DocumentService()


def get_document_service() -> DocumentService:
    """获取文档服务实例"""
    return document_service
