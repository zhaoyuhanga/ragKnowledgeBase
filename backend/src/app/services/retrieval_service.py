# -*- coding: utf-8 -*-
"""
检索服务

本模块提供检索相关的业务逻辑处理，包括：
- 向量检索（基于Milvus）
- 关键词检索（基于MySQL BM25）
- 混合检索融合
- 查询改写

注意：路由层只做参数校验和响应封装，所有业务逻辑在此层实现。
"""

import time
from typing import Any, Dict, List, Optional

from app.common.exception import BusinessException, ErrorCode
from app.common.logging import logger
from app.schemas.retrieval import (
    ChunkReference,
    RetrievalRequest,
    RetrievalResponse,
    RetrievalResult,
    VectorSearchRequest,
    KeywordSearchRequest,
)
from app.services.fusion_service import (
    FusionService,
    RetrievalItem,
    FilterCriteria,
    FusionConfig,
    get_fusion_service,
)
from app.services.query_rewrite_service import QueryRewriteService, get_rewrite_service
from core.config import settings


class RetrievalService:
    """
    检索服务

    提供向量检索、关键词检索、混合检索等业务逻辑。
    集成增强的查询改写功能，支持：
    - 查询规范化
    - 多查询生成
    - 子查询分解
    - HyDE假设答案生成（可选）
    - 后退提示（可选）
    """

    def __init__(self):
        """初始化检索服务"""
        self._fusion_service: Optional[FusionService] = None
        self._rewrite_service: Optional[QueryRewriteService] = None

    @property
    def fusion_service(self) -> FusionService:
        """获取融合服务实例"""
        if self._fusion_service is None:
            config = FusionConfig(
                vector_top_k=settings.retrieval.vector_top_k,
                keyword_top_k=settings.retrieval.keyword_top_k,
                rrf_k=settings.retrieval.rrf_k,
                fusion_top_k=settings.retrieval.fusion_top_k,
                vector_weight=settings.retrieval.vector_weight,
                keyword_weight=settings.retrieval.keyword_weight,
            )
            self._fusion_service = get_fusion_service(config)
        return self._fusion_service

    @property
    def rewrite_service(self) -> QueryRewriteService:
        """获取查询改写服务实例"""
        if self._rewrite_service is None:
            self._rewrite_service = get_rewrite_service()
        return self._rewrite_service

    def hybrid_search(
        self,
        request: RetrievalRequest
    ) -> RetrievalResponse:
        """
        混合检索

        结合向量检索和关键词检索，返回融合后的结果。
        支持查询改写（规范化、多查询、子查询分解）。

        Args:
            request: 检索请求

        Returns:
            检索响应
        """
        start_time = time.time()
        trace_id = f"search_{int(time.time() * 1000)}"

        logger.info(
            "开始混合检索",
            extra={
                "traceId": trace_id,
                "method": "hybrid_search",
                "uri": "/api/v1/retrieval/hybrid",
                "query": request.query,
                "top_k": request.top_k,
                "enable_rewrite": request.enable_rewrite,
                "fusion_method": request.fusion_method
            }
        )

        try:
            rewrite_result = None
            rewrite_time_ms = 0

            # 1. 查询改写（可选）
            if request.enable_rewrite:
                rewrite_start = time.time()
                rewrite_result = self.rewrite_service.rewrite(
                    request.query,
                    enable_multi_query=True,
                    enable_subquery=True,
                    enable_hyde=False,  # HyDE默认关闭，性能开销较大
                    enable_background=False,  # 后退提示默认关闭
                )
                rewrite_time_ms = int((time.time() - rewrite_start) * 1000)

                logger.info(
                    "查询改写完成",
                    extra={
                        "traceId": trace_id,
                        "original_query": request.query,
                        "normalized_query": rewrite_result.normalized_query,
                        "multi_query_count": len(rewrite_result.multi_queries),
                        "subquery_count": len(rewrite_result.sub_queries),
                        "rewrite_time_ms": rewrite_time_ms
                    }
                )

            # 使用规范化后的查询或原始查询
            query = rewrite_result.normalized_query if rewrite_result else request.query

            # 2. 构建过滤条件
            criteria = FilterCriteria(
                document_ids=set(request.doc_ids) if request.doc_ids else None,
                active_versions_only=True,
            )

            # 3. 向量检索
            vector_start = time.time()
            vector_top_k = request.vector_top_k or settings.retrieval.vector_top_k

            # 如果启用了多查询，扩展向量检索
            all_queries = [query]
            if rewrite_result and rewrite_result.multi_queries:
                all_queries.extend(rewrite_result.multi_queries[:3])  # 最多使用3个多查询

            # 如果有HyDE答案，也纳入检索
            if rewrite_result and rewrite_result.hyde_answer:
                all_queries.append(rewrite_result.hyde_answer)

            vector_results = self._multi_query_vector_search(
                queries=all_queries,
                top_k=vector_top_k,
                doc_ids=request.doc_ids,
                trace_id=trace_id
            )
            vector_time_ms = int((time.time() - vector_start) * 1000)

            # 4. 关键词检索
            keyword_start = time.time()
            keyword_top_k = request.keyword_top_k or settings.retrieval.keyword_top_k

            # 收集所有关键词检索结果
            all_keyword_results = []
            for kw_query in all_queries:
                try:
                    kw_results = self.keyword_search(
                        query=kw_query,
                        top_k=keyword_top_k,
                        doc_ids=request.doc_ids,
                    )
                    all_keyword_results.extend(kw_results)
                except Exception as e:
                    logger.warning(f"关键词检索失败: {str(e)}")

            # 去重合并关键词结果
            keyword_results = self._merge_results(all_keyword_results)
            keyword_time_ms = int((time.time() - keyword_start) * 1000)

            # 5. 转换结果格式
            vector_items = self._convert_to_items(vector_results)
            keyword_items = self._convert_to_items(keyword_results)

            # 6. 结果融合
            fusion_start = time.time()
            if request.fusion_method == "rrf":
                fused_items = self.fusion_service.rrf_fusion(
                    vector_results=vector_items,
                    keyword_results=keyword_items,
                )
            elif request.fusion_method == "weighted":
                fused_items = self.fusion_service.weighted_fusion(
                    vector_results=vector_items,
                    keyword_results=keyword_items,
                )
            else:
                fused_items = self.fusion_service.rank_fusion(
                    vector_results=vector_items,
                    keyword_results=keyword_items,
                )
            fusion_time_ms = int((time.time() - fusion_start) * 1000)

            # 7. 应用过滤
            fused_items = self.fusion_service.apply_filters(fused_items, criteria)

            # 8. 转换为响应格式
            fused_results = self._convert_to_results(fused_items)

            # 限制返回数量
            fused_results = fused_results[:request.top_k]

            total_time_ms = int((time.time() - start_time) * 1000)

            logger.info(
                "混合检索完成",
                extra={
                    "traceId": trace_id,
                    "method": "hybrid_search",
                    "uri": "/api/v1/retrieval/hybrid",
                    "query": request.query,
                    "vector_count": len(vector_results),
                    "keyword_count": len(keyword_results),
                    "fused_count": len(fused_results),
                    "rewrite_time_ms": rewrite_time_ms,
                    "vector_time_ms": vector_time_ms,
                    "keyword_time_ms": keyword_time_ms,
                    "fusion_time_ms": fusion_time_ms,
                    "total_time_ms": total_time_ms,
                    "fusion_method": request.fusion_method,
                    "responseCode": 0
                }
            )

            return RetrievalResponse(
                query=request.query,
                total=len(fused_results),
                results=fused_results,
                retrieval_time_ms=total_time_ms,
            )

        except Exception as e:
            total_time_ms = int((time.time() - start_time) * 1000)
            logger.error(
                f"混合检索失败: {str(e)}",
                extra={
                    "traceId": trace_id,
                    "method": "hybrid_search",
                    "uri": "/api/v1/retrieval/hybrid",
                    "query": request.query,
                    "error": str(e),
                    "costMs": total_time_ms,
                    "responseCode": -1
                }
            )
            raise BusinessException(
                code=ErrorCode.RETRIEVAL_FAILED[0],
                message=f"检索失败: {str(e)}"
            )

    def _multi_query_vector_search(
        self,
        queries: List[str],
        top_k: int,
        doc_ids: Optional[List[int]],
        trace_id: str
    ) -> List[RetrievalResult]:
        """
        多查询向量检索

        对多个查询进行向量检索，然后合并结果。

        Args:
            queries: 查询列表
            top_k: 每个查询的检索数量
            doc_ids: 限定的文档ID列表
            trace_id: 追踪ID

        Returns:
            合并后的检索结果
        """
        all_results = []

        for query in queries:
            try:
                results = self.vector_search(
                    query=query,
                    top_k=top_k,
                    doc_ids=doc_ids,
                )
                all_results.extend(results)
            except Exception as e:
                logger.warning(f"多查询向量检索失败: {query}, 错误: {str(e)}")

        # 合并去重
        return self._merge_results(all_results)

    def _merge_results(
        self,
        results: List[RetrievalResult]
    ) -> List[RetrievalResult]:
        """
        合并去重检索结果

        Args:
            results: 检索结果列表

        Returns:
            去重后的结果
        """
        seen: Dict[int, RetrievalResult] = {}

        for result in results:
            chunk_id = result.chunk.chunk_id
            if chunk_id not in seen:
                seen[chunk_id] = result
            else:
                # 如果已存在，保留分数较高的
                existing = seen[chunk_id]
                if result.chunk.score > existing.chunk.score:
                    seen[chunk_id] = result

        return list(seen.values())

    def vector_search(
        self,
        query: str,
        top_k: int = 10,
        doc_ids: Optional[List[int]] = None
    ) -> List[RetrievalResult]:
        """
        向量检索

        基于Milvus向量数据库进行语义相似度检索。

        Args:
            query: 查询文本
            top_k: 返回数量
            doc_ids: 限定的文档ID列表

        Returns:
            检索结果列表
        """
        start_time = time.time()
        trace_id = f"vector_{int(time.time() * 1000)}"

        try:
            from app.repositories.milvus_repository import VectorSearchService, get_vector_search_service
            from app.services.embedding_service import get_embedding_service
            from app.models.chunk import DocumentChunk
            from core.database import SessionLocal

            # 1. 获取向量检索服务
            vector_service = get_vector_search_service()

            # 2. 执行向量检索
            try:
                milvus_results = vector_service.search_by_text(
                    query=query,
                    top_k=top_k,
                    document_ids=doc_ids,
                )
            except Exception as e:
                logger.warning(f"Milvus检索失败，使用备选方案: {str(e)}")
                milvus_results = []

            # 3. 如果Milvus检索失败或无结果，使用数据库备选检索
            if not milvus_results:
                db = SessionLocal()
                try:
                    # 获取向量化服务获取查询向量
                    embedding_service = get_embedding_service()
                    if embedding_service is None:
                        logger.warning("向量化服务不可用，跳过备选检索")
                    else:
                        try:
                            query_embedding, _ = embedding_service.encode_single(query)
                        except Exception as embed_err:
                            logger.warning(f"向量化查询失败: {str(embed_err)}")
                            embedding_service = None

                    # 从数据库查询已向量化且有向量的Chunks
                    query_obj = db.query(DocumentChunk).filter(
                        DocumentChunk.status == 1,
                        DocumentChunk.vector_id.isnot(None),
                    )

                    if doc_ids:
                        query_obj = query_obj.filter(DocumentChunk.document_id.in_(doc_ids))

                    chunks = query_obj.limit(top_k).all()

                    # 计算相似度并排序
                    results = []
                    for chunk in chunks:
                        # 这里使用简化的相似度计算
                        # 实际应该使用真实的向量相似度
                        score = self._calculate_similarity(query, chunk.content)
                        results.append((chunk, score))

                    results.sort(key=lambda x: x[1], reverse=True)
                    milvus_results = [
                        {
                            "chunk_id": chunk.id,
                            "document_id": chunk.document_id,
                            "version_id": chunk.version_id,
                            "title_path": chunk.title_path,
                            "page_start": chunk.page_start,
                            "page_end": chunk.page_end,
                            "chunk_type": chunk.chunk_type,
                            "quality_score": chunk.quality_score,
                            "distance": score,
                        }
                        for chunk, score in results[:top_k]
                    ]
                finally:
                    db.close()

            # 4. 转换为检索结果
            results = []
            for hit in milvus_results:
                chunk_ref = ChunkReference(
                    chunk_id=hit.get("chunk_id", 0),
                    document_id=hit.get("document_id", 0),
                    version_id=hit.get("version_id", 0),
                    title_path=hit.get("title_path"),
                    page_start=hit.get("page_start"),
                    page_end=hit.get("page_end"),
                    content="",  # 实际需要从数据库获取
                    score=hit.get("distance", 0.0),
                    chunk_type=hit.get("chunk_type", "paragraph"),
                )

                result = RetrievalResult(
                    chunk=chunk_ref,
                    vector_score=hit.get("distance", 0.0),
                    keyword_score=None,
                    fusion_score=hit.get("distance", 0.0),
                )
                results.append(result)

            # 5. 填充内容
            results = self._enrich_chunk_content(results)

            retrieval_time_ms = int((time.time() - start_time) * 1000)
            logger.info(
                "向量检索完成",
                extra={
                    "traceId": trace_id,
                    "method": "vector_search",
                    "query": query,
                    "result_count": len(results),
                    "costMs": retrieval_time_ms
                }
            )

            return results

        except Exception as e:
            logger.error(
                f"向量检索失败: {str(e)}",
                extra={
                    "traceId": trace_id,
                    "query": query,
                    "error": str(e)
                }
            )
            raise BusinessException(
                code=ErrorCode.RETRIEVAL_FAILED[0],
                message=f"向量检索失败: {str(e)}"
            )

    def keyword_search(
        self,
        query: str,
        top_k: int = 10,
        doc_ids: Optional[List[int]] = None
    ) -> List[RetrievalResult]:
        """
        关键词检索

        基于MySQL BM25进行关键词匹配检索。

        Args:
            query: 查询文本
            top_k: 返回数量
            doc_ids: 限定的文档ID列表

        Returns:
            检索结果列表
        """
        start_time = time.time()
        trace_id = f"keyword_{int(time.time() * 1000)}"

        try:
            from app.services.keyword_service import get_keyword_index_service
            from app.schemas.keyword import KeywordSearchRequest as KeywordReq

            # 1. 获取关键词索引服务
            keyword_service = get_keyword_index_service()

            # 2. 构建检索请求
            search_request = KeywordReq(
                query=query,
                top_k=top_k,
                document_ids=doc_ids,
            )

            # 3. 执行关键词检索
            try:
                keyword_response = keyword_service.search(search_request)
            except Exception as e:
                logger.warning(f"关键词检索失败: {str(e)}")
                keyword_response = None

            # 4. 转换为检索结果
            results = []
            if keyword_response and keyword_response.results:
                for hit in keyword_response.results:
                    chunk_ref = ChunkReference(
                        chunk_id=hit.chunk_id,
                        document_id=0,  # 需要从chunk查询
                        version_id=0,
                        title_path=hit.title_path,
                        page_start=hit.page_start,
                        page_end=hit.page_end,
                        content=hit.content,
                        score=hit.score,
                        chunk_type="paragraph",
                    )

                    result = RetrievalResult(
                        chunk=chunk_ref,
                        vector_score=None,
                        keyword_score=hit.score,
                        fusion_score=hit.score,
                    )
                    results.append(result)

            retrieval_time_ms = int((time.time() - start_time) * 1000)
            logger.info(
                "关键词检索完成",
                extra={
                    "traceId": trace_id,
                    "method": "keyword_search",
                    "query": query,
                    "result_count": len(results),
                    "costMs": retrieval_time_ms
                }
            )

            return results

        except Exception as e:
            logger.error(
                f"关键词检索失败: {str(e)}",
                extra={
                    "traceId": trace_id,
                    "query": query,
                    "error": str(e)
                }
            )
            raise BusinessException(
                code=ErrorCode.RETRIEVAL_FAILED[0],
                message=f"关键词检索失败: {str(e)}"
            )

    def _convert_to_items(self, results: List[RetrievalResult]) -> List[RetrievalItem]:
        """将检索结果转换为融合项"""
        items = []
        for result in results:
            item = RetrievalItem(
                chunk_id=result.chunk.chunk_id,
                document_id=result.chunk.document_id,
                version_id=result.chunk.version_id,
                title_path=result.chunk.title_path,
                page_start=result.chunk.page_start,
                page_end=result.chunk.page_end,
                content=result.chunk.content,
                chunk_type=result.chunk.chunk_type,
                vector_score=result.vector_score or 0.0,
                keyword_score=result.keyword_score or 0.0,
                fusion_score=result.fusion_score or 0.0,
            )
            items.append(item)
        return items

    def _convert_to_results(self, items: List[RetrievalItem]) -> List[RetrievalResult]:
        """将融合项转换为检索结果"""
        results = []
        for item in items:
            chunk_ref = ChunkReference(
                chunk_id=item.chunk_id,
                document_id=item.document_id,
                version_id=item.version_id,
                title_path=item.title_path,
                page_start=item.page_start,
                page_end=item.page_end,
                content=item.content,
                score=item.fusion_score,
                chunk_type=item.chunk_type,
            )

            result = RetrievalResult(
                chunk=chunk_ref,
                vector_score=item.vector_score,
                keyword_score=item.keyword_score,
                fusion_score=item.fusion_score,
            )
            results.append(result)
        return results

    def _enrich_chunk_content(self, results: List[RetrievalResult]) -> List[RetrievalResult]:
        """填充Chunk内容"""
        if not results:
            return results

        from app.models.chunk import DocumentChunk
        from core.database import SessionLocal

        chunk_ids = [r.chunk.chunk_id for r in results]
        db = SessionLocal()

        try:
            chunks = db.query(DocumentChunk).filter(
                DocumentChunk.id.in_(chunk_ids)
            ).all()

            chunk_map = {c.id: c for c in chunks}

            for result in results:
                chunk_id = result.chunk.chunk_id
                if chunk_id in chunk_map:
                    chunk = chunk_map[chunk_id]
                    result.chunk.document_id = chunk.document_id
                    result.chunk.version_id = chunk.version_id
                    result.chunk.content = chunk.content or chunk.enhanced_content or ""

        finally:
            db.close()

        return results

    def _calculate_similarity(self, query: str, content: str) -> float:
        """
        计算简单相似度

        使用词重叠计算查询和内容的相似度。
        实际应该使用向量相似度。

        Args:
            query: 查询文本
            content: 内容文本

        Returns:
            相似度分数
        """
        if not query or not content:
            return 0.0

        query_terms = set(query.lower().split())
        content_terms = set(content.lower().split())

        if not query_terms or not content_terms:
            return 0.0

        # Jaccard相似度
        intersection = len(query_terms & content_terms)
        union = len(query_terms | content_terms)

        return intersection / union if union > 0 else 0.0

    def get_suggestions(
        self,
        query: str,
        limit: int = 5
    ) -> List[str]:
        """
        获取检索建议

        Args:
            query: 查询文本
            limit: 返回数量

        Returns:
            建议列表
        """
        # TODO: 实现实际的建议逻辑
        # 可以基于查询历史、热门查询等生成建议
        return []


# 全局服务实例
_retrieval_service: Optional[RetrievalService] = None


def get_retrieval_service() -> RetrievalService:
    """获取检索服务实例"""
    global _retrieval_service
    if _retrieval_service is None:
        _retrieval_service = RetrievalService()
    return _retrieval_service
