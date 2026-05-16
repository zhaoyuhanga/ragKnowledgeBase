"""
RAG 问答系统 - 知识库服务模块
知识库索引管理和统计
"""

import time
from datetime import datetime
from typing import Dict, Any, List

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.config import settings
from app.models.document import Document, DocumentChunk, QALog
from app.services.embedding_service import embedding_service, get_embedding_service
from app.core.vectorstore import vector_store, get_vector_store
from app.core.logger import get_logger, knowledge_logger
from app.core.runtime_config import runtime_config

logger = get_logger(__name__)


class KnowledgeService:
    """知识库服务"""

    def __init__(self):
        self.embedding_service = get_embedding_service()
        self.vector_store = get_vector_store()

    def get_stats(self, db: Session) -> Dict[str, Any]:
        """获取知识库统计信息"""
        try:
            total_documents = db.query(func.count(Document.id)).scalar() or 0
            processed_documents = db.query(func.count(Document.id)).filter(
                Document.status == 1
            ).scalar() or 0
            failed_documents = db.query(func.count(Document.id)).filter(
                Document.status == 2
            ).scalar() or 0

            total_chunks = db.query(func.count(DocumentChunk.id)).scalar() or 0

            collection_info = self.vector_store.get_collection_info()

            total_questions = db.query(func.count(QALog.id)).scalar() or 0
            cached_questions = db.query(func.count(QALog.id)).filter(
                QALog.cache_hit == True
            ).scalar() or 0

            avg_response_time = db.query(func.avg(QALog.response_time_ms)).filter(
                QALog.response_time_ms.isnot(None)
            ).scalar() or 0

            today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            today_queries = db.query(func.count(QALog.id)).filter(
                QALog.created_at >= today_start
            ).scalar() or 0

            return {
                "documents": {
                    "total": total_documents,
                    "processed": processed_documents,
                    "failed": failed_documents,
                    "processing": total_documents - processed_documents - failed_documents,
                },
                "chunks": {
                    "total": total_chunks,
                },
                "vectors": {
                    "count": collection_info.get("count", 0),
                    "collection_name": collection_info.get("name"),
                },
                "qa": {
                    "total_questions": total_questions,
                    "cached_questions": cached_questions,
                    "cache_rate": round(cached_questions / total_questions * 100, 2) if total_questions > 0 else 0,
                    "avg_response_time_ms": round(avg_response_time, 2),
                    "today_queries": today_queries,
                },
                "config": {
                    "chunk_size": runtime_config.chunk_size,
                    "chunk_overlap": runtime_config.chunk_overlap,
                    "retrieval_top_k": runtime_config.retrieval_top_k,
                    "similarity_threshold": runtime_config.similarity_threshold,
                    "embedding_model": settings.embedding_model,
                }
            }

        except Exception as e:
            logger.error(f"获取知识库统计失败: {str(e)}")
            raise

    async def rebuild_index(self, db: Session) -> Dict[str, Any]:
        """重建知识库索引"""
        start_time = time.time()
        knowledge_logger.log_operation("rebuild_index", "start")

        try:
            logger.info("正在清空向量数据库...")
            self.vector_store.reset()

            logger.info("正在清空文档块表...")
            db.query(DocumentChunk).delete()

            logger.info("正在重置文档状态...")
            db.query(Document).update({Document.status: 0, Document.chunk_count: 0})
            db.commit()

            documents = db.query(Document).filter(Document.status != 2).all()
            total_chunks = 0
            success_count = 0
            failed_count = 0

            for doc in documents:
                try:
                    chunks = await self._reindex_document(doc, db)
                    total_chunks += chunks
                    success_count += 1
                except Exception as e:
                    logger.error(f"重建文档 {doc.id} 失败: {str(e)}")
                    doc.status = 2
                    doc.error_message = str(e)
                    failed_count += 1

            db.commit()

            elapsed = (time.time() - start_time) * 1000

            result = {
                "success": True,
                "total_documents": len(documents),
                "success_count": success_count,
                "failed_count": failed_count,
                "total_chunks": total_chunks,
                "duration_ms": int(elapsed),
            }

            knowledge_logger.log_operation(
                "rebuild_index",
                "completed",
                details={
                    "total_documents": len(documents),
                    "success_count": success_count,
                    "failed_count": failed_count,
                    "total_chunks": total_chunks,
                },
                duration_ms=elapsed
            )

            logger.info(f"知识库重建完成: {result}")
            return result

        except Exception as e:
            elapsed = (time.time() - start_time) * 1000
            logger.error(f"知识库重建失败: {str(e)}")
            knowledge_logger.log_operation("rebuild_index", "failed", error=str(e), duration_ms=elapsed)
            raise

    async def _reindex_document(self, document: Document, db: Session) -> int:
        """重新索引单个文档"""
        from app.utils.file_parser import FileParser, file_parser
        from app.utils.text_splitter import TextSplitter, text_splitter
        import uuid

        try:
            parser = FileParser()
            content, _ = parser.parse_file(document.file_path, document.file_type)

            if not content:
                raise ValueError("文档内容为空")

            splitter = TextSplitter(
                chunk_size=runtime_config.chunk_size,
                chunk_overlap=runtime_config.chunk_overlap,
                min_chunk_size=runtime_config.chunk_min_size,
            )
            chunks = splitter.split_text(content)

            if not chunks:
                raise ValueError("文档切分后无有效内容")

            embeddings = self.embedding_service.encode(chunks)

            vector_ids = [f"{document.id}_{i}_{uuid.uuid4().hex[:8]}" for i in range(len(chunks))]

            metadatas = [
                {
                    "document_id": document.id,
                    "chunk_index": i,
                    "filename": document.filename,
                    "file_type": document.file_type,
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
                    document_id=document.id,
                    chunk_index=i,
                    content=chunk,
                    char_count=len(chunk),
                    vector_id=vector_id,
                )
                db.add(chunk_record)

            document.status = 1
            document.chunk_count = len(chunks)
            document.error_message = None

            return len(chunks)

        except Exception as e:
            logger.error(f"重新索引文档 {document.id} 失败: {str(e)}")
            raise

    def search_chunks(
        self,
        query: str,
        db: Session,
        top_k: int = None
    ) -> List[Dict[str, Any]]:
        """手动检索相关文本块（调试用）"""
        try:
            query_embedding = self.embedding_service.encode_single(query)

            k = top_k or runtime_config.retrieval_top_k
            results = self.vector_store.search_vectors(
                query_embedding=query_embedding,
                n_results=k
            )

            chunks = []
            ids = results.get("ids", [[]])[0]
            distances = results.get("distances", [[]])[0]
            documents = results.get("documents", [[]])[0]
            metadatas = results.get("metadatas", [[]])[0]

            for i, (vector_id, distance, document, metadata) in enumerate(zip(ids, distances, documents, metadatas)):
                similarity = distance

                chunks.append({
                    "vector_id": vector_id,
                    "document_id": metadata.get("document_id"),
                    "chunk_index": metadata.get("chunk_index"),
                    "filename": metadata.get("filename"),
                    "content": document,
                    "similarity": round(similarity, 4),
                })

            return chunks

        except Exception as e:
            logger.error(f"检索失败: {str(e)}")
            raise


# 创建全局知识库服务实例
knowledge_service = KnowledgeService()


def get_knowledge_service() -> KnowledgeService:
    """获取知识库服务实例"""
    return knowledge_service
