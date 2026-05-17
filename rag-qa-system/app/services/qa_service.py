"""
RAG 问答系统 - 问答服务模块
问答检索、生成和缓存管理
"""

import time
import json
import asyncio
import hashlib
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

from sqlalchemy.orm import Session

from app.config import settings
from app.models.document import Document, DocumentChunk, QALog
from app.services.embedding_service import embedding_service, get_embedding_service
from app.core.vectorstore import vector_store, get_vector_store
from app.core.cache import redis_cache, get_redis_cache
from app.core.llm import llm_client, get_llm_client, DEFAULT_SYSTEM_PROMPT, AI_GENERATE_SYSTEM_PROMPT
from app.core.runtime_config import runtime_config
from app.core.logger import get_logger, qa_logger
from app.utils.text_splitter import get_text_splitter

logger = get_logger(__name__)

# 异步任务线程池
_executor = ThreadPoolExecutor(max_workers=4)


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
            # 从缓存来源判断 source_type
            cached_sources = cached.get("sources", [])
            source_type = "ai_generated" if any(s.get("source_type") == "ai_generated" for s in cached_sources) else "local"
            
            qa_log = QALog(
                question=question,
                answer=cached.get("answer", ""),
                referenced_chunks=[s.get("vector_id") for s in cached_sources if s.get("vector_id")],
                response_time_ms=int(elapsed),
                cache_hit=True,
                source_type=source_type,
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
                source_type="local",
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
        temperature: float = 0.3,
        search_mode: str = "local",
        enable_ai_extend: bool = True
    ):
        """
        流式处理问答请求，返回生成器

        Args:
            question: 用户问题
            db: 数据库会话
            session_id: 会话ID
            top_k: 检索数量
            temperature: 生成温度
            search_mode: 搜索模式: local(仅本地文档) | ai_generated(仅AI生成) | all(全部)
            enable_ai_extend: 是否启用AI扩展（检索为空时调用LLM生成）

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
                cached_sources = cached.get("sources", [])
                source_type = "ai_generated" if any(s.get("source_type") == "ai_generated" for s in cached_sources) else "local"
                
                qa_log = QALog(
                    question=question,
                    answer=cached_answer,
                    referenced_chunks=[s.get("vector_id") for s in cached_sources if s.get("vector_id")],
                    response_time_ms=int(elapsed),
                    cache_hit=True,
                    source_type=source_type,
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

            logger.info(f"正在处理问题（流式）: {question[:50]}..., search_mode={search_mode}")
            query_embedding = self.embedding_service.encode_single(question)

            k = top_k or runtime_config.retrieval_top_k
            
            # 如果是 AI 生成模式且启用 AI 扩展
            if search_mode == "ai_generated" and enable_ai_extend:
                # 先搜索本地文档
                local_search_results = self.vector_store.search_vectors(
                    query_embedding=query_embedding,
                    n_results=k,
                    where=None,
                    source_type="local"
                )
                local_chunks = self._parse_search_results(local_search_results, db)
                
                if local_chunks:
                    # 本地有结果，使用本地内容作为上下文
                    retrieved_chunks = local_chunks
                    logger.info(f"本地找到 {len(local_chunks)} 条相关文档，同时生成AI内容...")
                else:
                    # 本地无结果
                    retrieved_chunks = []
                    logger.info(f"本地未找到相关文档，将生成AI内容...")
                
                # AI 生成模式：始终生成内容并保存（无论是否有本地结果）
                yield "data: {\"type\":\"sources\",\"sources\":[]}\n\n"
                yield "data: {\"type\":\"ai_extend\",\"status\":\"generating\"}\n\n"
                
                # 获取对话历史
                conversation_history = []
                if session_id:
                    history_logs, _ = self.get_qa_history(db, session_id=session_id, limit=5)
                    if history_logs:
                        for log in reversed(history_logs):
                            conversation_history.append({"role": "user", "content": log.question})
                            if log.answer:
                                conversation_history.append({"role": "assistant", "content": log.answer})
                
                # 使用本地文档内容作为上下文生成（如果有的话）
                context_texts = [chunk["content"] for chunk in retrieved_chunks] if retrieved_chunks else []
                
                full_answer = ""
                for token in self.llm.generate_with_context_stream(
                    question=question,
                    context=context_texts,
                    history=conversation_history if conversation_history else None,
                    system_prompt=AI_GENERATE_SYSTEM_PROMPT,
                    temperature=temperature
                ):
                    full_answer += token
                    yield f"data: {{\"type\":\"token\",\"content\":{json.dumps(token)}}}\n\n"

                elapsed = (time.time() - start_time) * 1000
                
                # 检查回答是否有效（过滤"无法回答"等无效内容）
                invalid_patterns = [
                    "无法回答", "知识库中", "没有找到", "未包含", "没有相关",
                    "无法提供", "暂无", "不包含", "缺乏", "不涉及"
                ]
                is_invalid_answer = (
                    len(full_answer.strip()) < 10 or
                    any(pattern in full_answer for pattern in invalid_patterns)
                )
                
                # 构建来源信息
                sources = [
                    {
                        "chunk_id": chunk.get("chunk_id"),
                        "vector_id": chunk["vector_id"],
                        "document_id": chunk["document_id"],
                        "filename": chunk["filename"],
                        "content": chunk["content"][:200] + "..." if len(chunk["content"]) > 200 else chunk["content"],
                        "similarity": chunk["similarity"],
                        "source_type": "local",
                    }
                    for chunk in retrieved_chunks
                ]
                
                ai_doc_id = None
                
                # 只有有效回答才保存到向量数据库
                if not is_invalid_answer and len(full_answer.strip()) >= 10:
                    ai_doc_id = await _save_ai_generated_content_async(
                        db=db,
                        question=question,
                        answer=full_answer
                    )
                    if ai_doc_id:
                        sources.append({
                            "chunk_id": None,
                            "vector_id": None,
                            "document_id": ai_doc_id,
                            "filename": f"AI_Generated_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                            "content": full_answer[:200] + "..." if len(full_answer) > 200 else full_answer,
                            "similarity": 1.0,
                            "source_type": "ai_generated",
                        })
                else:
                    logger.info(f"AI 生成内容无效，跳过保存: len={len(full_answer)}")
                
                qa_logger.log_query(
                    question,
                    len(full_answer),
                    len(retrieved_chunks),
                    False,
                    "ai_generated",
                    elapsed
                )
                
                # 保存到历史记录
                # AI 生成模式，即使有本地文档上下文，来源类型也是 ai_generated
                qa_log = QALog(
                    question=question,
                    answer=full_answer,
                    referenced_chunks=[chunk["vector_id"] for chunk in retrieved_chunks] if retrieved_chunks else [],
                    response_time_ms=int(elapsed),
                    cache_hit=False,
                    source_type="ai_generated",
                    session_id=session_id,
                )
                db.add(qa_log)
                db.commit()
                
                # 保存到缓存
                self.cache.set_qa_cache(question, full_answer, sources)
                
                yield f"data: {{\"type\":\"done\",\"answer\":{json.dumps(full_answer)},\"sources\":{json.dumps(sources)},\"response_time_ms\":{int(elapsed)},\"cache_hit\":false,\"ai_extend\":true,\"ai_doc_id\":{ai_doc_id}}}\n\n"
                yield "data: [DONE]\n\n"
                return
            
            # 标准搜索逻辑（非 AI 生成模式）
            search_results = self.vector_store.search_vectors(
                query_embedding=query_embedding,
                n_results=k,
                where=None,
                source_type=search_mode if search_mode != "all" else None
            )
            retrieved_chunks = self._parse_search_results(search_results, db)

            if not retrieved_chunks:
                # 检索为空，检查是否启用 AI 扩展
                if enable_ai_extend:
                    # AI 扩展模式：直接调用 LLM 生成回答
                    yield "data: {\"type\":\"sources\",\"sources\":[]}\n\n"
                    yield "data: {\"type\":\"ai_extend\",\"status\":\"generating\"}\n\n"
                    
                    logger.info(f"本地检索为空，启用AI扩展生成...")
                    
                    conversation_history = []
                    if session_id:
                        history_logs, _ = self.get_qa_history(db, session_id=session_id, limit=5)
                        if history_logs:
                            for log in reversed(history_logs):
                                conversation_history.append({"role": "user", "content": log.question})
                                if log.answer:
                                    conversation_history.append({"role": "assistant", "content": log.answer})
                    
                    # 直接调用 LLM 流式生成（无上下文）
                    full_answer = ""
                    for token in self.llm.generate_with_context_stream(
                        question=question,
                        context=[],
                        history=conversation_history if conversation_history else None,
                        system_prompt=DEFAULT_SYSTEM_PROMPT,
                        temperature=temperature
                    ):
                        full_answer += token
                        yield f"data: {{\"type\":\"token\",\"content\":{json.dumps(token)}}}\n\n"

                    elapsed = (time.time() - start_time) * 1000
                    
                    # 检查回答是否有效
                    invalid_patterns = [
                        "无法回答", "知识库中", "没有找到", "未包含", "没有相关",
                        "无法提供", "暂无", "不包含", "缺乏", "不涉及"
                    ]
                    is_invalid_answer = (
                        len(full_answer.strip()) < 10 or
                        any(pattern in full_answer for pattern in invalid_patterns)
                    )
                    
                    # 只有有效回答才保存
                    ai_doc_id = None
                    if not is_invalid_answer and len(full_answer.strip()) >= 10:
                        ai_doc_id = await _save_ai_generated_content_async(
                            db=db,
                            question=question,
                            answer=full_answer
                        )
                    else:
                        logger.info(f"AI 生成内容无效，跳过保存: len={len(full_answer)}")
                    
                    qa_logger.log_query(
                        question,
                        len(full_answer),
                        0,
                        False,
                        "ai_extend",
                        elapsed
                    )
                    
                    # 保存到历史记录
                    # AI 扩展模式，来源类型是 ai_generated
                    qa_log = QALog(
                        question=question,
                        answer=full_answer,
                        referenced_chunks=[],
                        response_time_ms=int(elapsed),
                        cache_hit=False,
                        source_type="ai_generated",
                        session_id=session_id,
                    )
                    db.add(qa_log)
                    db.commit()
                    
                    # 保存到缓存
                    self.cache.set_qa_cache(question, full_answer, [])
                    
                    yield f"data: {{\"type\":\"done\",\"answer\":{json.dumps(full_answer)},\"sources\":[],\"response_time_ms\":{int(elapsed)},\"cache_hit\":false,\"ai_extend\":true,\"ai_doc_id\":{ai_doc_id}}}\n\n"
                    yield "data: [DONE]\n\n"
                    return
                else:
                    # 未启用 AI 扩展，直接返回无结果
                    yield "data: {\"type\":\"done\",\"answer\":\"抱歉，知识库中没有找到与您问题相关的内容，且AI扩展已禁用。\",\"sources\":[],\"error\":null}\n\n"
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
                source_type="local",
                session_id=session_id,
            )
            db.add(qa_log)
            db.commit()

            self.cache.set_qa_cache(question, full_answer, sources)

            yield f"data: {{\"type\":\"done\",\"answer\":{json.dumps(full_answer)},\"sources\":{json.dumps(sources)},\"response_time_ms\":{int(elapsed)},\"cache_hit\":false,\"ai_extend\":false}}\n\n"
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


async def _save_ai_generated_content_async(
    db: Session,
    question: str,
    answer: str
) -> int:
    """
    异步保存 AI 生成的内容到向量数据库
    
    Args:
        db: 数据库会话
        question: 原始问题
        answer: AI 生成的回答
        
    Returns:
        创建的文档ID
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        _executor,
        _save_ai_generated_content,
        db,
        question,
        answer
    )


def _save_ai_generated_content(
    db: Session,
    question: str,
    answer: str
) -> int:
    """
    保存 AI 生成的内容到向量数据库（同步方法）
    
    Args:
        db: 数据库会话
        question: 原始问题
        answer: AI 生成的回答
        
    Returns:
        创建的文档ID
    """
    from app.services.embedding_service import get_embedding_service
    from app.core.vectorstore import get_vector_store
    
    try:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        question_hash = hashlib.md5(question.encode()).hexdigest()[:8]
        filename = f"AI_Generated_{timestamp}_{question_hash}.txt"
        
        logger.info(f"开始保存AI生成内容: question_hash={question_hash}, answer_len={len(answer)}")
        
        # 1. 创建 Document 记录
        doc = Document(
            filename=filename,
            file_path=f"./uploads/{filename}",
            file_type="ai_generated",
            file_size=len(answer.encode('utf-8')),
            status=0,  # 初始状态：处理中
            chunk_count=0,
            source_type="ai_generated",
            generated_from_question=question,
            generated_at=datetime.now(),
            llm_model=settings.deepseek_model,
            llm_provider="deepseek",
        )
        db.add(doc)
        db.flush()
        
        logger.info(f"Document 创建成功: doc_id={doc.id}")
        
        # 2. 切分文本
        text_splitter = get_text_splitter()
        chunks = text_splitter.split_text(answer)
        logger.info(f"文本切分完成: {len(chunks)} 个 chunks")
        
        if not chunks:
            logger.warning("AI 生成内容为空，不创建 chunks")
            doc.status = 1  # 即使没有 chunks 也标记为完成
            db.commit()
            return doc.id
        
        # 3. 创建 DocumentChunk 记录
        embedding_service = get_embedding_service()
        vector_store = get_vector_store()
        
        for idx, chunk_text in enumerate(chunks):
            # 生成向量
            embedding = embedding_service.encode_single(chunk_text)
            vector_id = f"{doc.id}_{idx}_{question_hash}"
            
            # 创建 chunk 记录
            chunk_model = DocumentChunk(
                document_id=doc.id,
                chunk_index=idx,
                content=chunk_text,
                char_count=len(chunk_text),
                vector_id=vector_id,
                source_type="ai_generated",
                generated_from_question=question,
                generated_at=datetime.now(),
                llm_model=settings.deepseek_model,
                llm_provider="deepseek",
            )
            db.add(chunk_model)
            db.flush()
            
            # 4. 添加向量到 Milvus
            metadata = {
                "document_id": doc.id,
                "chunk_index": idx,
                "filename": filename,
                "source_type": "ai_generated",
                "generated_from_question": question,
                "generated_at": datetime.now().isoformat(),
                "llm_model": settings.deepseek_model,
                "llm_provider": "deepseek",
            }
            
            try:
                vector_store.add_vectors(
                    documents=[chunk_text],
                    embeddings=[embedding],
                    ids=[vector_id],
                    metadatas=[metadata]
                )
                logger.debug(f"向量添加成功: vector_id={vector_id}")
            except Exception as e:
                logger.error(f"向量添加失败: vector_id={vector_id}, error={str(e)}")
                # 继续处理，不中断
        
        # 5. 更新 Document 状态和 chunk_count
        doc.status = 1  # 已完成
        doc.chunk_count = len(chunks)
        db.commit()
        
        logger.info(f"AI 生成内容已入库: doc_id={doc.id}, chunks={len(chunks)}, model={settings.deepseek_model}")
        
        return doc.id
        
    except Exception as e:
        logger.error(f"保存AI生成内容失败: {str(e)}")
        try:
            db.rollback()
        except Exception:
            pass
        raise
