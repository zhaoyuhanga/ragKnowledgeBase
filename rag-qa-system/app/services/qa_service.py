"""
RAG 问答系统 - 问答服务模块
问答检索、生成和缓存管理
"""

import time
import json
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
    """问答服务"""

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
        """处理问答请求"""
        start_time = time.time()

        # 检查缓存
        cached = self.cache.get_qa_cache(question)
        if cached:
            elapsed = (time.time() - start_time) * 1000
            qa_log = QALog(
                question=question,
                answer=cached.get("answer", ""),
                referenced_chunks=[s.get("vector_id") for s in cached.get("sources", []) if s.get("vector_id")],
                response_time_ms=int(elapsed),
                cache_hit=True,
                session_id=session_id,
            )
            db.add(qa_log)
            db.commit()

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
            logger.info(f"正在处理问题: {question[:50]}...")
            query_embedding = self.embedding_service.encode_single(question)

            k = top_k or runtime_config.retrieval_top_k
            search_results = self.vector_store.search_vectors(
                query_embedding=query_embedding,
                n_results=k,
                where=None
            )

            retrieved_chunks = self._parse_search_results(search_results, db)

            if not retrieved_chunks:
                elapsed = (time.time() - start_time) * 1000
                return {
                    "answer": "抱歉，知识库中没有找到与您问题相关的内容。请尝试上传更多文档或调整问题表述。",
                    "sources": [],
                    "cache_hit": False,
                    "response_time_ms": int(elapsed),
                }

            context_texts = [chunk["content"] for chunk in retrieved_chunks]

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

            elapsed = (time.time() - start_time) * 1000
            qa_logger.log_query(
                question,
                len(answer),
                len(retrieved_chunks),
                False,
                "success",
                elapsed
            )

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
        """解析向量检索结果"""
        chunks = []

        ids = results.get("ids", [[]])[0]
        distances = results.get("distances", [[]])[0]
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]

        for i, (vector_id, distance, document, metadata) in enumerate(zip(ids, distances, documents, metadatas)):
            similarity = distance

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
        """获取问答历史"""
        query = db.query(QALog)

        if session_id:
            query = query.filter(QALog.session_id == session_id)

        total = query.count()
        logs = query.order_by(QALog.created_at.desc()).offset(skip).limit(limit).all()

        return logs, total

    async def ask_stream(
        self,
        question: str,
        db: Session,
        session_id: str = None,
        top_k: int = None,
        temperature: float = 0.3
    ):
        """
        流式处理问答请求，返回生成器

        Yields:
            SSE 格式的事件数据
        """
        start_time = time.time()

        try:
            # 检查缓存
            cached = self.cache.get_qa_cache(question)
            if cached:
                elapsed = (time.time() - start_time) * 1000
                cached_answer = cached.get("answer", "")
                cached_sources = cached.get("sources", [])

                # 保存到历史记录
                qa_log = QALog(
                    question=question,
                    answer=cached_answer,
                    referenced_chunks=[s.get("vector_id") for s in cached_sources if s.get("vector_id")],
                    response_time_ms=int(elapsed),
                    cache_hit=True,
                    session_id=session_id,
                )
                db.add(qa_log)
                db.commit()

                # 流式返回缓存结果
                yield f"data: {{\"type\":\"sources\",\"sources\":{json.dumps(cached_sources)}}}\n\n"
                for char in cached_answer:
                    yield f"data: {{\"type\":\"token\",\"content\":{json.dumps(char)}}}\n\n"
                yield f"data: {{\"type\":\"done\",\"answer\":{json.dumps(cached_answer)},\"sources\":{json.dumps(cached_sources)},\"response_time_ms\":{int(elapsed)},\"cache_hit\":true}}\n\n"
                yield "data: [DONE]\n\n"
                return

            logger.info(f"正在处理问题（流式）: {question[:50]}...")
            query_embedding = self.embedding_service.encode_single(question)

            k = top_k or runtime_config.retrieval_top_k
            search_results = self.vector_store.search_vectors(
                query_embedding=query_embedding,
                n_results=k,
                where=None
            )

            retrieved_chunks = self._parse_search_results(search_results, db)

            if not retrieved_chunks:
                yield "data: {\"type\":\"done\",\"answer\":\"抱歉，知识库中没有找到与您问题相关的内容。请尝试上传更多文档或调整问题表述。\",\"sources\":[],\"error\":null}\n\n"
                yield "data: [DONE]\n\n"
                return

            context_texts = [chunk["content"] for chunk in retrieved_chunks]

            conversation_history = []
            if session_id:
                history_logs, _ = self.get_qa_history(db, session_id=session_id, limit=5)
                if history_logs:
                    for log in reversed(history_logs):
                        conversation_history.append({"role": "user", "content": log.question})
                        if log.answer:
                            conversation_history.append({"role": "assistant", "content": log.answer})

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

            yield f"data: {{\"type\":\"sources\",\"sources\":{json.dumps(sources)}}}\n\n"

            full_answer = ""
            for token in self.llm.generate_with_context_stream(
                question=question,
                context=context_texts,
                history=conversation_history if conversation_history else None,
                system_prompt=DEFAULT_SYSTEM_PROMPT,
                temperature=temperature
            ):
                full_answer += token
                yield f"data: {{\"type\":\"token\",\"content\":{json.dumps(token)}}}\n\n"

            elapsed = (time.time() - start_time) * 1000

            qa_logger.log_query(
                question,
                len(full_answer),
                len(retrieved_chunks),
                False,
                "success",
                elapsed
            )

            qa_log = QALog(
                question=question,
                answer=full_answer,
                referenced_chunks=[chunk["vector_id"] for chunk in retrieved_chunks],
                response_time_ms=int(elapsed),
                cache_hit=False,
                session_id=session_id,
            )
            db.add(qa_log)
            db.commit()

            self.cache.set_qa_cache(question, full_answer, sources)

            yield f"data: {{\"type\":\"done\",\"answer\":{json.dumps(full_answer)},\"sources\":{json.dumps(sources)},\"response_time_ms\":{int(elapsed)},\"cache_hit\":false}}\n\n"
            yield "data: [DONE]\n\n"

        except Exception as e:
            elapsed = (time.time() - start_time) * 1000
            logger.error(f"流式问答处理失败: {str(e)}")
            yield f"data: {{\"type\":\"error\",\"error\":{json.dumps(str(e))}}}\n\n"
            yield "data: [DONE]\n\n"

    def clear_cache(self) -> int:
        """清空问答缓存"""
        count = self.cache.clear_pattern("qa:*")
        logger.info(f"已清空 {count} 条问答缓存")
        return count


# 创建全局问答服务实例
qa_service = QAService()


def get_qa_service() -> QAService:
    """获取问答服务实例"""
    return qa_service
