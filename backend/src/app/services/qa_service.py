# -*- coding: utf-8 -*-
"""
问答服务

本模块提供问答相关的业务逻辑处理，包括：
- 检索相关文档
- 重排序处理
- 上下文组装
- LLM生成答案
- 引用绑定

注意：路由层只做参数校验和响应封装，所有业务逻辑在此层实现。
"""

import time
import uuid
import json
from typing import Any, Dict, List, Optional

import httpx

from app.common.exception import BusinessException, ErrorCode
from app.common.logging import logger
from app.models.qa import QALog
from app.schemas.qa import (
    FeedbackRequest,
    FeedbackResponse,
    HistoryItem,
    QARequest,
    QAResult,
    QAResponse,
    SessionInfo,
    QAStatistics,
)
from core.config import settings


class QAService:
    """
    问答服务

    提供问答生成、历史查询、反馈提交等业务逻辑。
    """

    def __init__(self):
        """初始化问答服务"""
        self._retrieval_service = None
        self._rerank_service = None
        self._context_assembler = None
        self._prompt_builder = None
        self._llm_service = None

    @property
    def retrieval_service(self):
        """获取检索服务"""
        if self._retrieval_service is None:
            from app.services.retrieval_service import RetrievalService
            self._retrieval_service = RetrievalService()
        return self._retrieval_service

    @property
    def rerank_service(self):
        """获取重排序服务"""
        if self._rerank_service is None:
            from app.services.rerank_service import get_rerank_service
            self._rerank_service = get_rerank_service()
        return self._rerank_service

    @property
    def context_assembler(self):
        """获取上下文组装器"""
        if self._context_assembler is None:
            from app.services.context_service import get_context_assembler
            self._context_assembler = get_context_assembler()
        return self._context_assembler

    @property
    def prompt_builder(self):
        """获取Prompt构造器"""
        if self._prompt_builder is None:
            from app.services.context_service import get_prompt_builder
            self._prompt_builder = get_prompt_builder()
        return self._prompt_builder

    @property
    def llm_service(self):
        """获取LLM服务"""
        if self._llm_service is None:
            self._llm_service = LLMService()
        return self._llm_service

    def ask_question(self, request: QARequest) -> QAResponse:
        """
        问答接口

        根据用户问题，生成答案。

        Args:
            request: 问答请求

        Returns:
            问答响应
        """
        total_start_time = time.time()

        try:
            # 生成会话ID
            session_id = request.session_id
            if not session_id:
                session_id = str(uuid.uuid4())

            # ========== 1. 检索阶段 ==========
            retrieval_start_time = time.time()
            from app.schemas.retrieval import RetrievalRequest
            retrieval_response = self.retrieval_service.hybrid_search(
                RetrievalRequest(
                    query=request.question,
                    top_k=request.top_k or 20,
                    doc_ids=request.doc_ids,
                    enable_rewrite=True,
                    fusion_method="rrf",
                )
            )
            retrieval_time_ms = int((time.time() - retrieval_start_time) * 1000)

            # ========== 2. 重排序阶段（可选） ==========
            rerank_start_time = time.time()
            reranked_results = retrieval_response.results

            if request.use_rerank and retrieval_response.results:
                # 转换为候选格式
                candidates = []
                for result in retrieval_response.results:
                    candidates.append({
                        "chunk_id": result.chunk.chunk_id,
                        "document_id": result.chunk.document_id,
                        "version_id": result.chunk.version_id,
                        "title_path": result.chunk.title_path,
                        "page_start": result.chunk.page_start,
                        "page_end": result.chunk.page_end,
                        "content": result.chunk.content,
                        "chunk_type": result.chunk.chunk_type,
                        "score": result.fusion_score,
                    })

                # 执行重排序
                reranked = self.rerank_service.rerank_with_expansion(
                    query=request.question,
                    candidates=candidates,
                    top_k=request.rerank_top_k or 10,
                    expand_adjacent=True,
                    expand_tables=True,
                )

                # 更新检索结果
                reranked_results = self._convert_rerank_to_results(reranked)
            rerank_time_ms = int((time.time() - rerank_start_time) * 1000)

            # ========== 3. 上下文组装阶段 ==========
            context_start_time = time.time()
            assembled_context = self.context_assembler.assemble(
                reranked_results,
                max_tokens=request.max_context_tokens or 4000,
            )
            context_time_ms = int((time.time() - context_start_time) * 1000)

            # ========== 4. LLM生成答案 ==========
            generation_start_time = time.time()
            system_prompt, user_prompt = self.prompt_builder.build(
                question=request.question,
                context=assembled_context,
            )

            answer = self.llm_service.generate(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=request.temperature or 0.7,
            )
            generation_time_ms = int((time.time() - generation_start_time) * 1000)

            # ========== 5. 保存问答日志 ==========
            total_time_ms = int((time.time() - total_start_time) * 1000)
            qa_id = self._save_qa_log(
                question=request.question,
                answer=answer,
                references=reranked_results,
                session_id=session_id,
                user_id=request.user_id,
                tenant_id=request.tenant_id,
                retrieval_time_ms=retrieval_time_ms,
                rerank_time_ms=rerank_time_ms,
                context_time_ms=context_time_ms,
                generation_time_ms=generation_time_ms,
                total_time_ms=total_time_ms,
            )

            # ========== 6. 构建响应 ==========
            result = QAResult(
                qa_id=qa_id,
                question=request.question,
                answer=answer,
                references=reranked_results,
                session_id=session_id,
                total_time_ms=total_time_ms,
                retrieval_time_ms=retrieval_time_ms,
                rerank_time_ms=rerank_time_ms,
                context_time_ms=context_time_ms,
                generation_time_ms=generation_time_ms,
            )

            logger.info(
                "问答生成成功",
                extra={
                    "qa_id": qa_id,
                    "session_id": session_id,
                    "question": request.question[:50],
                    "retrieval_time_ms": retrieval_time_ms,
                    "rerank_time_ms": rerank_time_ms,
                    "context_time_ms": context_time_ms,
                    "generation_time_ms": generation_time_ms,
                    "total_time_ms": total_time_ms,
                }
            )

            return QAResponse(result=result)

        except Exception as e:
            logger.error(f"问答生成失败: {str(e)}")
            raise BusinessException(
                code=ErrorCode.OPERATION_FAILED[0],
                message=f"问答生成失败: {str(e)}"
            )

    def ask_question_stream(
        self,
        question: str,
        session_id: str,
        user_id: Optional[int] = None,
        tenant_id: int = 1,
        use_rerank: bool = True,
        top_k: int = 20,
        rerank_top_k: int = 10,
        max_context_tokens: int = 4000,
        temperature: float = 0.7,
        doc_ids: Optional[List[int]] = None,
    ) -> Dict[str, Any]:
        """
        流式问答接口

        根据用户问题，流式生成答案。
        注意：此方法会调用两次LLM（一次保存日志，一次流式输出）

        Args:
            question: 用户问题
            session_id: 会话ID
            user_id: 用户ID
            tenant_id: 租户ID
            use_rerank: 是否使用重排
            top_k: 检索TopK
            rerank_top_k: 重排后TopK
            max_context_tokens: 最大上下文Token数
            temperature: 温度参数
            doc_ids: 限定文档ID列表

        Returns:
            包含qa_id和answer_stream的字典
        """
        total_start_time = time.time()

        try:
            # ========== 1. 检索阶段 ==========
            retrieval_start_time = time.time()
            from app.schemas.retrieval import RetrievalRequest
            retrieval_response = self.retrieval_service.hybrid_search(
                RetrievalRequest(
                    query=question,
                    top_k=top_k,
                    doc_ids=doc_ids,
                    enable_rewrite=True,
                    fusion_method="rrf",
                )
            )
            retrieval_time_ms = int((time.time() - retrieval_start_time) * 1000)

            # ========== 2. 重排序阶段 ==========
            rerank_start_time = time.time()
            reranked_results = retrieval_response.results

            if use_rerank and retrieval_response.results:
                candidates = []
                for result in retrieval_response.results:
                    candidates.append({
                        "chunk_id": result.chunk.chunk_id,
                        "document_id": result.chunk.document_id,
                        "version_id": result.chunk.version_id,
                        "title_path": result.chunk.title_path,
                        "page_start": result.chunk.page_start,
                        "page_end": result.chunk.page_end,
                        "content": result.chunk.content,
                        "chunk_type": result.chunk.chunk_type,
                        "score": result.fusion_score,
                    })

                reranked = self.rerank_service.rerank_with_expansion(
                    query=question,
                    candidates=candidates,
                    top_k=rerank_top_k,
                    expand_adjacent=True,
                    expand_tables=True,
                )
                reranked_results = self._convert_rerank_to_results(reranked)
            rerank_time_ms = int((time.time() - rerank_start_time) * 1000)

            # ========== 3. 上下文组装阶段 ==========
            context_start_time = time.time()
            assembled_context = self.context_assembler.assemble(
                reranked_results,
                max_tokens=max_context_tokens,
            )
            context_time_ms = int((time.time() - context_start_time) * 1000)

            # ========== 4. 构建Prompt ==========
            system_prompt, user_prompt = self.prompt_builder.build(
                question=question,
                context=assembled_context,
            )

            # ========== 5. 流式LLM生成 ==========
            # 返回生成器供流式输出
            answer_stream = self.llm_service.generate_stream(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=temperature,
            )

            # 计算生成耗时（估算）
            generation_time_ms = 0
            total_time_ms = int((time.time() - total_start_time) * 1000)

            logger.info(
                "流式问答准备完成",
                extra={
                    "session_id": session_id,
                    "question": question[:50],
                    "retrieval_time_ms": retrieval_time_ms,
                    "rerank_time_ms": rerank_time_ms,
                    "context_time_ms": context_time_ms,
                }
            )

            return {
                "question": question,
                "system_prompt": system_prompt,
                "user_prompt": user_prompt,
                "temperature": temperature,
                "answer_stream": answer_stream,
                "references": reranked_results,
                "session_id": session_id,
                "user_id": user_id,
                "tenant_id": tenant_id,
                "retrieval_time_ms": retrieval_time_ms,
                "rerank_time_ms": rerank_time_ms,
                "context_time_ms": context_time_ms,
                "generation_time_ms": generation_time_ms,
                "total_time_ms": total_time_ms,
            }

        except Exception as e:
            logger.error(f"流式问答生成失败: {str(e)}")
            raise BusinessException(
                code=ErrorCode.OPERATION_FAILED[0],
                message=f"流式问答生成失败: {str(e)}"
            )

    def _convert_rerank_to_results(self, reranked: List) -> List:
        """将重排序结果转换为检索结果"""
        from app.schemas.retrieval import ChunkReference, RetrievalResult

        results = []
        for item in reranked:
            if hasattr(item, 'chunk_id'):
                chunk_ref = ChunkReference(
                    chunk_id=item.chunk_id,
                    document_id=item.document_id,
                    version_id=item.version_id,
                    title_path=item.title_path,
                    page_start=item.page_start,
                    page_end=item.page_end,
                    content=item.content,
                    score=item.rerank_score,
                    chunk_type=item.chunk_type,
                )

                result = RetrievalResult(
                    chunk=chunk_ref,
                    vector_score=None,
                    keyword_score=None,
                    fusion_score=item.rerank_score,
                )
                results.append(result)

        return results

    def _save_qa_log(
        self,
        question: str,
        answer: str,
        references: List,
        session_id: str,
        user_id: Optional[int],
        tenant_id: int,
        retrieval_time_ms: int,
        rerank_time_ms: int,
        context_time_ms: int,
        generation_time_ms: int,
        total_time_ms: int
    ) -> int:
        """
        保存问答日志

        Args:
            question: 用户问题
            answer: 生成的答案
            references: 引用来源
            session_id: 会话ID
            user_id: 用户ID
            tenant_id: 租户ID
            retrieval_time_ms: 检索耗时
            rerank_time_ms: 重排序耗时
            context_time_ms: 上下文组装耗时
            generation_time_ms: 生成耗时
            total_time_ms: 总耗时

        Returns:
            问答记录ID
        """
        from core.database import SessionLocal

        db = SessionLocal()
        try:
            # 将引用转换为JSON格式
            references_data = []
            for i, ref in enumerate(references[:10]):  # 最多保存10个引用
                chunk = ref.chunk if hasattr(ref, 'chunk') else ref
                references_data.append({
                    "index": i + 1,
                    "chunk_id": chunk.chunk_id,
                    "document_id": chunk.document_id,
                    "title_path": chunk.title_path,
                    "page_start": chunk.page_start,
                    "page_end": chunk.page_end,
                    "content_preview": chunk.content[:200] if chunk.content else "",
                    "score": getattr(ref, 'fusion_score', 0) or getattr(ref, 'rerank_score', 0) or 0
                })

            qa_log = QALog(
                user_id=user_id,
                tenant_id=tenant_id,
                session_id=session_id,
                question=question,
                answer=answer,
                references=json.dumps(references_data, ensure_ascii=False),
                retrieval_time_ms=retrieval_time_ms,
                rerank_time_ms=rerank_time_ms,
                context_time_ms=context_time_ms,
                generation_time_ms=generation_time_ms,
                total_time_ms=total_time_ms
            )
            db.add(qa_log)
            db.commit()
            db.refresh(qa_log)

            return qa_log.id
        except Exception as e:
            db.rollback()
            logger.error(f"保存问答日志失败: {str(e)}")
            raise
        finally:
            db.close()

    def get_history(
        self,
        session_id: str,
        page_no: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """
        查询会话历史

        Args:
            session_id: 会话ID
            page_no: 页码
            page_size: 每页数量

        Returns:
            包含items和total的字典
        """
        from core.database import SessionLocal

        db = SessionLocal()
        try:
            query = db.query(QALog).filter(QALog.session_id == session_id)

            # 获取总数
            total = query.count()

            # 分页查询
            offset = (page_no - 1) * page_size
            items = query.order_by(QALog.created_at.desc()).offset(offset).limit(page_size).all()

            result_items = []
            for item in items:
                result_items.append(HistoryItem(
                    id=item.id,
                    question=item.question,
                    answer=item.answer,
                    quality_score=item.quality_score,
                    feedback=item.feedback,
                    created_at=item.created_at
                ))

            return {
                "items": result_items,
                "total": total
            }
        finally:
            db.close()

    def submit_feedback(
        self,
        qa_id: int,
        feedback: FeedbackRequest
    ) -> FeedbackResponse:
        """
        提交反馈

        Args:
            qa_id: 问答记录ID
            feedback: 反馈内容

        Returns:
            反馈响应
        """
        from core.database import SessionLocal

        db = SessionLocal()
        try:
            qa_log = db.query(QALog).filter(QALog.id == qa_id).first()

            if not qa_log:
                raise BusinessException(
                    code=ErrorCode.DATA_NOT_FOUND[0],
                    message=f"问答记录不存在，ID: {qa_id}"
                )

            qa_log.feedback = feedback.feedback
            qa_log.quality_score = feedback.quality_score
            qa_log.feedback_remark = feedback.remark
            db.commit()

            logger.info(
                "反馈提交成功",
                extra={"qa_id": qa_id, "feedback": feedback.feedback}
            )

            return FeedbackResponse(
                qa_id=qa_id,
                feedback=feedback.feedback,
                quality_score=feedback.quality_score,
                remark=feedback.remark
            )
        except BusinessException:
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"反馈提交失败: {str(e)}")
            raise BusinessException(
                code=ErrorCode.OPERATION_FAILED[0],
                message=f"反馈提交失败: {str(e)}"
            )
        finally:
            db.close()

    def list_sessions(
        self,
        user_id: Optional[int],
        tenant_id: int,
        page_no: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """
        查询会话列表

        Args:
            user_id: 用户ID
            tenant_id: 租户ID
            page_no: 页码
            page_size: 每页数量

        Returns:
            包含items和total的字典
        """
        from core.database import SessionLocal
        from sqlalchemy import func

        db = SessionLocal()
        try:
            # 查询会话列表
            query = db.query(
                QALog.session_id,
                QALog.user_id,
                func.count(QALog.id).label("question_count"),
                func.max(QALog.created_at).label("last_answer_time")
            ).filter(QALog.tenant_id == tenant_id)

            if user_id:
                query = query.filter(QALog.user_id == user_id)

            query = query.group_by(QALog.session_id, QALog.user_id)

            # 获取总数
            total = query.count()

            # 分页查询
            offset = (page_no - 1) * page_size
            results = query.order_by(func.max(QALog.created_at).desc()).offset(offset).limit(page_size).all()

            # 获取每个会话的最后问题
            result_items = []
            for r in results:
                last_qa = db.query(QALog).filter(
                    QALog.session_id == r.session_id
                ).order_by(QALog.created_at.desc()).first()

                result_items.append(SessionInfo(
                    session_id=r.session_id,
                    user_id=r.user_id,
                    question_count=r.question_count,
                    last_question=last_qa.question if last_qa else None,
                    last_answer_time=r.last_answer_time,
                    created_at=r.last_answer_time
                ))

            return {
                "items": result_items,
                "total": total
            }
        finally:
            db.close()

    def get_statistics(
        self,
        tenant_id: int,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> QAStatistics:
        """
        获取问答统计信息

        Args:
            tenant_id: 租户ID
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            统计信息
        """
        from core.database import SessionLocal
        from sqlalchemy import func
        from datetime import datetime

        db = SessionLocal()
        try:
            query = db.query(QALog).filter(QALog.tenant_id == tenant_id)

            if start_date:
                query = query.filter(QALog.created_at >= datetime.fromisoformat(start_date))
            if end_date:
                query = query.filter(QALog.created_at <= datetime.fromisoformat(end_date))

            total_count = query.count()

            # 平均评分
            avg_score = db.query(func.avg(QALog.quality_score)).filter(
                QALog.tenant_id == tenant_id,
                QALog.quality_score.isnot(None)
            ).scalar() or 0.0

            # 反馈统计
            helpful_count = query.filter(QALog.feedback == "helpful").count()
            not_helpful_count = query.filter(QALog.feedback == "not_helpful").count()

            # 平均耗时
            avg_retrieval_time = db.query(func.avg(QALog.retrieval_time_ms)).filter(
                QALog.tenant_id == tenant_id
            ).scalar() or 0.0

            avg_generation_time = db.query(func.avg(QALog.generation_time_ms)).filter(
                QALog.tenant_id == tenant_id
            ).scalar() or 0.0

            return QAStatistics(
                total_count=total_count,
                avg_quality_score=round(float(avg_score), 2),
                helpful_count=helpful_count,
                not_helpful_count=not_helpful_count,
                avg_retrieval_time_ms=round(float(avg_retrieval_time), 2),
                avg_generation_time_ms=round(float(avg_generation_time), 2),
            )

        finally:
            db.close()


class LLMService:
    """
    LLM服务

    提供大语言模型调用功能，支持多种Provider：
    - DeepSeek
    - OpenAI
    - Zhipu (智谱)
    - Qwen (通义千问)
    """

    def __init__(self):
        """初始化服务"""
        self._config = settings.llm
        self._model_name = self._config.model_name
        self._api_key = self._config.api_key
        self._base_url = self._config.base_url
        self._max_tokens = self._config.max_tokens
        self._temperature = self._config.temperature
        self._timeout = self._config.timeout
        self._initialized = False

    def _initialize(self) -> None:
        """初始化服务"""
        if self._initialized:
            return

        logger.info(
            f"初始化LLM服务",
            extra={
                "provider": self._config.provider,
                "model": self._model_name,
                "base_url": self._base_url
            }
        )
        self._initialized = True

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = None,
        max_tokens: int = None
    ) -> str:
        """
        生成文本（一次性返回完整结果）

        Args:
            system_prompt: 系统提示
            user_prompt: 用户提示
            temperature: 温度参数
            max_tokens: 最大token数

        Returns:
            生成的完整文本
        """
        self._initialize()

        temp = temperature if temperature is not None else (self._temperature or 0.7)
        tokens = max_tokens if max_tokens is not None else self._max_tokens

        provider = self._config.provider.lower()

        if provider == "deepseek":
            return self._call_deepseek(system_prompt, user_prompt, temp, tokens)
        elif provider == "openai":
            return self._call_openai(system_prompt, user_prompt, temp, tokens)
        elif provider == "zhipu":
            return self._call_zhipu(system_prompt, user_prompt, temp, tokens)
        elif provider == "qwen":
            return self._call_qwen(system_prompt, user_prompt, temp, tokens)
        else:
            raise BusinessException(
                code=ErrorCode.OPERATION_FAILED[0],
                message=f"不支持的LLM Provider: {provider}"
            )

    def generate_stream(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = None,
        max_tokens: int = None
    ):
        """
        流式生成文本

        Args:
            system_prompt: 系统提示
            user_prompt: 用户提示
            temperature: 温度参数
            max_tokens: 最大token数

        Yields:
            生成的文本片段
        """
        self._initialize()

        temp = temperature if temperature is not None else (self._temperature or 0.7)
        tokens = max_tokens if max_tokens is not None else self._max_tokens

        provider = self._config.provider.lower()

        if provider == "deepseek":
            yield from self._call_deepseek_stream(system_prompt, user_prompt, temp, tokens)
        elif provider == "openai":
            yield from self._call_openai_stream(system_prompt, user_prompt, temp, tokens)
        elif provider == "zhipu":
            yield from self._call_zhipu_stream(system_prompt, user_prompt, temp, tokens)
        elif provider == "qwen":
            yield from self._call_qwen_stream(system_prompt, user_prompt, temp, tokens)
        else:
            raise BusinessException(
                code=ErrorCode.OPERATION_FAILED[0],
                message=f"不支持的LLM Provider: {provider}"
            )

    def _call_deepseek(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
        max_tokens: int
    ) -> str:
        """调用DeepSeek API"""
        url = f"{self._base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self._model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        logger.info(f"调用DeepSeek API: {url}", extra={"model": self._model_name})

        with httpx.Client(timeout=self._timeout) as client:
            response = client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            result = response.json()

        content = result["choices"][0]["message"]["content"]
        usage = result.get("usage", {})

        logger.info(
            "DeepSeek API调用成功",
            extra={
                "model": self._model_name,
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
                "total_tokens": usage.get("total_tokens", 0)
            }
        )

        return content

    def _call_openai(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
        max_tokens: int
    ) -> str:
        """调用OpenAI API"""
        url = f"{self._base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self._model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        with httpx.Client(timeout=self._timeout) as client:
            response = client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            result = response.json()

        return result["choices"][0]["message"]["content"]

    def _call_zhipu(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
        max_tokens: int
    ) -> str:
        """调用智谱AI API"""
        url = f"{self._base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self._model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        with httpx.Client(timeout=self._timeout) as client:
            response = client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            result = response.json()

        return result["choices"][0]["message"]["content"]

    def _call_qwen(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
        max_tokens: int
    ) -> str:
        """调用通义千问API"""
        url = f"{self._base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self._model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        with httpx.Client(timeout=self._timeout) as client:
            response = client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            result = response.json()

        return result["choices"][0]["message"]["content"]

    def _call_deepseek_stream(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
        max_tokens: int
    ):
        """调用DeepSeek API流式生成"""
        url = f"{self._base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self._model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True
        }

        logger.info(f"调用DeepSeek API(流式): {url}", extra={"model": self._model_name})

        with httpx.Client(timeout=self._timeout) as client:
            with client.stream("POST", url, json=payload, headers=headers) as response:
                response.raise_for_status()
                full_content = ""
                for line in response.iter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        if data == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data)
                            delta = chunk.get("choices", [{}])[0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                full_content += content
                                yield content
                        except json.JSONDecodeError:
                            continue

        usage = {"model": self._model_name, "complete": True}
        logger.info("DeepSeek流式生成完成", extra=usage)

    def _call_openai_stream(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
        max_tokens: int
    ):
        """调用OpenAI API流式生成"""
        yield from self._call_deepseek_stream(system_prompt, user_prompt, temperature, max_tokens)

    def _call_zhipu_stream(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
        max_tokens: int
    ):
        """调用智谱AI API流式生成"""
        yield from self._call_deepseek_stream(system_prompt, user_prompt, temperature, max_tokens)

    def _call_qwen_stream(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
        max_tokens: int
    ):
        """调用通义千问API流式生成"""
        yield from self._call_deepseek_stream(system_prompt, user_prompt, temperature, max_tokens)


# 全局服务实例
_qa_service: Optional[QAService] = None


def get_qa_service() -> QAService:
    """获取问答服务实例"""
    global _qa_service
    if _qa_service is None:
        _qa_service = QAService()
    return _qa_service
