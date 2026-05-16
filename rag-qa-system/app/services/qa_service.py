"""
RAG 问答系统 - 问答服务模块
问答检索、生成和缓存管理
"""

import time
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime

from sqlalchemy.orm import Session

from app.config import settings
from app.models.document import DocumentChunk, QALog
from app.services.embedding_service import embedding_service, get_embedding_service
from app.core.vectorstore import vector_store, get_vector_store
from app.core.cache import redis_cache, get_redis_cache
from app.core.llm import llm_client, get_llm_client, DEFAULT_SYSTEM_PROMPT
from app.core.runtime_config import runtime_config
from app.core.logger import get_logger, qa_logger

logger = get_logger(__name__)


class QAService:
    """
    问答服务
    处理用户问答请求，包括检索、生成和缓存
    """

    def __init__(self):
        self.embedding_service = get_embedding_service()
        self.vector_store = get_vector_store()
        self.cache = get_redis_cache()
        self.llm = get_llm_client()

    async def ask(
        self,
        question: str,
        db: Session,
        session_id: str = None,
        top_k: int = None,
        temperature: float = 0.3
    ) -> Dict[str, Any]:
        """
        处理问答请求

        Args:
            question: 用户问题
            db: 数据库会话
            session_id: 会话 ID（用于多轮对话）
            top_k: 检索的文档数量
            temperature: 生成温度参数

        Returns:
            包含回答、来源等信息的字典
        """
        start_time = time.time()

        # 检查缓存
        cached = self.cache.get_qa_cache(question)
        if cached:
            elapsed = (time.time() - start_time) * 1000
            qa_logger.log_query(
                question,
                len(cached.get("answer", "")),
                len(cached.get("sources", [])),
                True,
                "cached",
                elapsed
            )
            return {
                "answer": cached["answer"],
                "sources": cached["sources"],
                "cache_hit": True,
                "response_time_ms": int(elapsed),
            }

        try:
            # 1. 向量化问题
            logger.info(f"正在处理问题: {question[:50]}...")
            query_embedding = self.embedding_service.encode_single(question)

            # 2. 检索相关文档（使用运行时配置）
            k = top_k or runtime_config.retrieval_top_k
            search_results = self.vector_store.search_vectors(
                query_embedding=query_embedding,
                n_results=k,
                where=None
            )

            # 3. 提取检索结果
            retrieved_chunks = self._parse_search_results(search_results, db)

            if not retrieved_chunks:
                elapsed = (time.time() - start_time) * 1000
                return {
                    "answer": "抱歉，知识库中没有找到与您问题相关的内容。请尝试上传更多文档或调整问题表述。",
                    "sources": [],
                    "cache_hit": False,
                    "response_time_ms": int(elapsed),
                }

            # 4. 生成回答
            context_texts = [chunk["content"] for chunk in retrieved_chunks]

            # Build conversation history for multi-turn dialogue
            conversation_history = []
            if session_id:
                history_logs, _ = self.get_qa_history(db, session_id=session_id, limit=5)
                if history_logs:
                    for log in reversed(history_logs):
                        conversation_history.append({"role": "user", "content": log.question})
                        if log.answer:
                            conversation_history.append({"role": "assistant", "content": log.answer})

            answer = self.llm.generate_with_context(
                question=question,
                context=context_texts,
                history=conversation_history if conversation_history else None,
                system_prompt=DEFAULT_SYSTEM_PROMPT,
                temperature=temperature
            )

            # 5. 记录日志
            elapsed = (time.time() - start_time) * 1000
            qa_logger.log_query(
                question,
                len(answer),
                len(retrieved_chunks),
                False,
                "success",
                elapsed
            )

            # 6. 保存问答日志
            qa_log = QALog(
                question=question,
                answer=answer,
                referenced_chunks=[chunk["vector_id"] for chunk in retrieved_chunks],
                response_time_ms=int(elapsed),
                cache_hit=False,
                session_id=session_id,
            )
            db.add(qa_log)
            db.commit()

            # 7. 缓存结果
            sources = [
                {
                    "chunk_id": chunk.get("chunk_id"),
                    "vector_id": chunk["vector_id"],
                    "document_id": chunk["document_id"],
                    "filename": chunk["filename"],
                    "content": chunk["content"][:200] + "..." if len(chunk["content"]) > 200 else chunk["content"],
                    "similarity": chunk["similarity"],
                }
                for chunk in retrieved_chunks
            ]

            self.cache.set_qa_cache(question, answer, sources)

            return {
                "answer": answer,
                "sources": sources,
                "cache_hit": False,
                "response_time_ms": int(elapsed),
            }

        except Exception as e:
            elapsed = (time.time() - start_time) * 1000
            logger.error(f"问答处理失败: {str(e)}")
            qa_logger.log_query(question, 0, 0, False, "error", elapsed)

            return {
                "answer": f"处理您的问题时出现错误: {str(e)}",
                "sources": [],
                "cache_hit": False,
                "response_time_ms": int(elapsed),
                "error": str(e),
            }

    def _parse_search_results(
        self,
        results: Dict[str, Any],
        db: Session
    ) -> List[Dict[str, Any]]:
        """
        解析向量检索结果

        Args:
            results: Milvus 检索结果
            db: 数据库会话

        Returns:
            包含文档块详情的列表
        """
        chunks = []

        ids = results.get("ids", [[]])[0]
        distances = results.get("distances", [[]])[0]
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]

        for i, (vector_id, distance, document, metadata) in enumerate(zip(ids, distances, documents, metadatas)):
            # 计算相似度
            # Milvus IP 度量时，distance 即为相似度（归一化向量）
            similarity = distance
            
            # 过滤低于阈值的检索结果
            if similarity < runtime_config.similarity_threshold:
                continue
            
            chunks.append({
                "vector_id": vector_id,
                "document_id": metadata.get("document_id"),
                "chunk_index": metadata.get("chunk_index"),
                "filename": metadata.get("filename"),
                "file_type": metadata.get("file_type"),
                "content": document,
                "char_count": metadata.get("char_count", len(document)),
                "similarity": round(similarity, 4),
            })

        return chunks

    def get_qa_history(
        self,
        db: Session,
        session_id: str = None,
        skip: int = 0,
        limit: int = 20
    ) -> Tuple[List[QALog], int]:
        """
        获取问答历史

        Args:
            db: 数据库会话
            session_id: 会话 ID（可选）
            skip: 跳过的记录数
            limit: 返回的记录数

        Returns:
            (问答记录列表, 总数)
        """
        query = db.query(QALog)

        if session_id:
            query = query.filter(QALog.session_id == session_id)

        total = query.count()
        logs = query.order_by(QALog.created_at.desc()).offset(skip).limit(limit).all()

        return logs, total

    def clear_cache(self) -> int:
        """
        清空问答缓存

        Returns:
            删除的缓存数量
        """
        count = self.cache.clear_pattern("qa:*")
        logger.info(f"已清空 {count} 条问答缓存")
        return count


# 创建全局问答服务实例
qa_service = QAService()


def get_qa_service() -> QAService:
    """获取问答服务实例"""
    return qa_service
