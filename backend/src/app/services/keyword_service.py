# -*- coding: utf-8 -*-
"""
关键词索引服务

本模块提供关键词索引的构建和检索功能：
- 分词处理
- 倒排索引构建
- BM25评分
"""

import re
import time
from collections import Counter
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from app.common.exception import BusinessException, ErrorCode
from app.common.logging import logger
from app.schemas.keyword import (
    IndexStatistics,
    KeywordIndexResult,
    KeywordIndexResponse,
    KeywordMatch,
    KeywordSearchRequest,
    KeywordSearchResponse,
    KeywordSearchResult,
    TokenizerConfig,
)
from core.database import SessionLocal


# ================================================
# 中文分词器（简单实现）
# ================================================

class ChineseTokenizer:
    """
    简单中文分词器

    基于规则的分词，支持：
    - 英文单词提取
    - 数字提取
    - 简单中文bigram分词
    """

    def __init__(self, config: Optional[TokenizerConfig] = None):
        """初始化分词器"""
        self.config = config or TokenizerConfig()
        self.stopwords = set(self._get_default_stopwords())

    def _get_default_stopwords(self) -> List[str]:
        """获取默认停用词"""
        return [
            "的", "了", "在", "是", "我", "有", "和", "就", "不", "人",
            "都", "一", "一个", "上", "也", "很", "到", "说", "要", "去",
            "你", "会", "着", "没有", "看", "好", "自己", "这", "那",
            "里", "为", "之", "以", "而", "于", "并", "及", "等", "其",
            "the", "a", "an", "is", "are", "was", "were", "be", "been",
            "have", "has", "had", "do", "does", "did", "will", "would",
            "could", "should", "may", "might", "can"
        ]

    def tokenize(self, text: str) -> List[str]:
        """分词"""
        if not text:
            return []

        tokens = []

        # 提取英文单词
        english_pattern = re.compile(r'[a-zA-Z]+')
        english_words = english_pattern.findall(text.lower())
        tokens.extend([w for w in english_words if len(w) >= self.config.min_term_length])

        # 提取数字
        number_pattern = re.compile(r'\d+\.?\d*')
        numbers = number_pattern.findall(text)
        tokens.extend([n for n in numbers if len(n) >= self.config.min_term_length])

        # 简单中文bigram分词
        chinese_pattern = re.compile(r'[\u4e00-\u9fff]+')
        chinese_texts = chinese_pattern.findall(text)

        for chinese_text in chinese_texts:
            bigrams = self._generate_bigrams(chinese_text)
            tokens.extend([g for g in bigrams if g not in self.stopwords])

        return list(set(tokens))

    def _generate_bigrams(self, text: str) -> List[str]:
        """生成bigram"""
        if len(text) < 2:
            return [text] if text else []

        bigrams = []
        for i in range(len(text) - 1):
            bigram = text[i:i + 2]
            if len(bigram) >= self.config.min_term_length:
                bigrams.append(bigram)

        return bigrams


# ================================================
# BM25 评分器
# ================================================

@dataclass
class BM25Document:
    """BM25文档"""
    chunk_id: int
    content: str
    title_path: Optional[str]
    page_start: Optional[int]
    page_end: Optional[int]
    terms: List[str]
    term_freqs: Dict[str, int]


class BM25Scorer:
    """BM25评分器"""

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        """初始化评分器"""
        self.k1 = k1
        self.b = b
        self.avg_doc_len = 0
        self.doc_count = 0
        self.doc_freqs: Dict[str, int] = {}
        self.doc_lengths: Dict[int, int] = {}
        self.documents: Dict[int, BM25Document] = {}

    def add_document(self, doc: BM25Document) -> None:
        """添加文档"""
        self.documents[doc.chunk_id] = doc
        self.doc_lengths[doc.chunk_id] = len(doc.terms)
        self.doc_count += 1

        for term in set(doc.terms):
            self.doc_freqs[term] = self.doc_freqs.get(term, 0) + 1

        total_len = sum(self.doc_lengths.values())
        self.avg_doc_len = total_len / self.doc_count if self.doc_count > 0 else 0

    def calculate_idf(self, term: str) -> float:
        """计算IDF"""
        df = self.doc_freqs.get(term, 0)
        if df == 0:
            return 0
        return max(0, (self.doc_count - df + 0.5) / (df + 0.5))

    def score(self, query_terms: List[str], doc_id: int) -> float:
        """计算BM25评分"""
        if doc_id not in self.documents:
            return 0.0

        doc = self.documents[doc_id]
        doc_len = self.doc_lengths[doc_id]
        score = 0.0

        for term in query_terms:
            if term not in doc.term_freqs:
                continue

            tf = doc.term_freqs[term]
            idf = self.calculate_idf(term)

            numerator = tf * (self.k1 + 1)
            denominator = tf + self.k1 * (1 - self.b + self.b * doc_len / self.avg_doc_len)

            score += idf * numerator / denominator if denominator > 0 else 0

        return score


# ================================================
# 关键词索引服务
# ================================================

class KeywordIndexService:
    """关键词索引服务"""

    def __init__(self):
        """初始化服务"""
        self._tokenizer = ChineseTokenizer()
        self._scorer: Optional[BM25Scorer] = None

    def build_index(
        self,
        document_id: int,
        version_id: Optional[int] = None,
        chunk_ids: Optional[List[int]] = None
    ) -> KeywordIndexResponse:
        """构建关键词索引"""
        from app.models.chunk import ChunkKeywordIndex

        start_time = time.time()
        db = SessionLocal()

        try:
            from app.models.chunk import DocumentChunk

            # 查询Chunks
            query = db.query(DocumentChunk).filter(
                DocumentChunk.document_id == document_id,
                DocumentChunk.keyword_indexed != 1
            )

            if version_id:
                query = query.filter(DocumentChunk.version_id == version_id)

            if chunk_ids:
                query = query.filter(DocumentChunk.id.in_(chunk_ids))

            chunks = query.all()

            if not chunks:
                return KeywordIndexResponse(
                    document_id=document_id,
                    total_chunks=0,
                    indexed_chunks=0,
                    total_terms=0,
                    results=[],
                    processing_time_ms=int((time.time() - start_time) * 1000)
                )

            results = []
            total_terms = 0
            indexed_chunks = 0

            for chunk in chunks:
                content_text = chunk.enhanced_content or chunk.content or ""
                title_text = chunk.title_path or ""

                content_terms = self._tokenizer.tokenize(content_text)
                title_terms = self._tokenizer.tokenize(title_text)

                content_freqs = Counter(content_terms)
                title_freqs = Counter(title_terms)

                all_terms = list(set(content_terms + title_terms))

                if not all_terms:
                    continue

                indexed_chunks += 1
                total_terms += len(all_terms)

                for term in all_terms:
                    if term in content_freqs:
                        index_entry = ChunkKeywordIndex(
                            chunk_id=chunk.id,
                            term=term,
                            field="content",
                            tf=content_freqs[term],
                            idf=0.0,
                            position=content_terms.index(term) if term in content_terms else None,
                            weight=1.0
                        )
                        db.add(index_entry)

                    if term in title_freqs:
                        index_entry = ChunkKeywordIndex(
                            chunk_id=chunk.id,
                            term=term,
                            field="title",
                            tf=title_freqs[term],
                            idf=0.0,
                            position=title_terms.index(term) if term in title_terms else None,
                            weight=2.0
                        )
                        db.add(index_entry)

                chunk.keyword_indexed = 1

                results.append(KeywordIndexResult(
                    chunk_id=chunk.id,
                    terms=all_terms,
                    indexed_count=len(all_terms)
                ))

            self._calculate_idf_batch(db)
            db.commit()

            processing_time = int((time.time() - start_time) * 1000)

            logger.info(
                f"关键词索引构建完成",
                extra={
                    "document_id": document_id,
                    "indexed_chunks": indexed_chunks,
                    "total_terms": total_terms,
                    "processing_time_ms": processing_time
                }
            )

            return KeywordIndexResponse(
                document_id=document_id,
                total_chunks=len(chunks),
                indexed_chunks=indexed_chunks,
                total_terms=total_terms,
                results=results,
                processing_time_ms=processing_time
            )

        except Exception as e:
            db.rollback()
            logger.error(f"关键词索引构建失败: {str(e)}")
            raise BusinessException(
                code=ErrorCode.INTERNAL_ERROR[0],
                message=f"关键词索引构建失败: {str(e)}"
            )
        finally:
            db.close()

    def _calculate_idf_batch(self, db) -> None:
        """批量计算IDF"""
        from app.models.chunk import ChunkKeywordIndex

        term_df: Dict[str, set] = {}
        all_entries = db.query(ChunkKeywordIndex).all()

        for entry in all_entries:
            if entry.term not in term_df:
                term_df[entry.term] = set()
            term_df[entry.term].add(entry.chunk_id)

        total_docs = len(set(e.chunk_id for e in all_entries))

        for entry in all_entries:
            df = len(term_df.get(entry.term, set()))
            if df > 0:
                entry.idf = max(0, (total_docs - df + 0.5) / (df + 0.5))

    def search(self, request: KeywordSearchRequest) -> KeywordSearchResponse:
        """关键词检索"""
        from app.models.chunk import ChunkKeywordIndex

        start_time = time.time()
        db = SessionLocal()

        try:
            from app.models.chunk import DocumentChunk

            query_terms = self._tokenizer.tokenize(request.query)

            if not query_terms:
                return KeywordSearchResponse(
                    query=request.query,
                    top_k=request.top_k,
                    total_results=0,
                    results=[],
                    processing_time_ms=int((time.time() - start_time) * 1000)
                )

            query = db.query(ChunkKeywordIndex).filter(
                ChunkKeywordIndex.term.in_(query_terms)
            )

            entries = query.all()

            if not entries:
                return KeywordSearchResponse(
                    query=request.query,
                    top_k=request.top_k,
                    total_results=0,
                    results=[],
                    processing_time_ms=int((time.time() - start_time) * 1000)
                )

            chunk_term_freqs: Dict[int, Dict[str, KeywordMatch]] = {}
            chunk_ids = set()

            for entry in entries:
                if entry.chunk_id not in chunk_term_freqs:
                    chunk_term_freqs[entry.chunk_id] = {}

                term_key = f"{entry.term}_{entry.field}"
                if term_key not in chunk_term_freqs[entry.chunk_id]:
                    chunk_term_freqs[entry.chunk_id][term_key] = KeywordMatch(
                        chunk_id=entry.chunk_id,
                        term=entry.term,
                        field=entry.field,
                        tf=entry.tf,
                        position=entry.position,
                        weight=entry.weight
                    )
                chunk_ids.add(entry.chunk_id)

            chunk_query = db.query(DocumentChunk).filter(
                DocumentChunk.id.in_(chunk_ids)
            )

            if request.document_ids:
                chunk_query = chunk_query.filter(
                    DocumentChunk.document_id.in_(request.document_ids)
                )

            if request.chunk_types:
                chunk_query = chunk_query.filter(
                    DocumentChunk.chunk_type.in_(request.chunk_types)
                )

            if request.min_quality_score is not None:
                chunk_query = chunk_query.filter(
                    DocumentChunk.quality_score >= request.min_quality_score
                )

            chunks = {c.id: c for c in chunk_query.all()}

            scorer = BM25Scorer()
            for chunk_id in chunks.keys():
                if chunk_id in chunk_term_freqs:
                    term_freqs = {
                        key.split("_")[0]: match.tf
                        for key, match in chunk_term_freqs[chunk_id].items()
                    }
                    doc = BM25Document(
                        chunk_id=chunk_id,
                        content=chunks[chunk_id].content or "",
                        title_path=chunks[chunk_id].title_path,
                        page_start=chunks[chunk_id].page_start,
                        page_end=chunks[chunk_id].page_end,
                        terms=query_terms,
                        term_freqs=term_freqs
                    )
                    scorer.add_document(doc)

            scores = []
            for chunk_id in chunks.keys():
                score = scorer.score(query_terms, chunk_id)
                scores.append((chunk_id, score))

            scores.sort(key=lambda x: x[1], reverse=True)
            top_scores = scores[:request.top_k]

            results = []
            for chunk_id, score in top_scores:
                chunk = chunks[chunk_id]
                matches = [
                    match for key, match in chunk_term_freqs.get(chunk_id, {}).items()
                ]

                results.append(KeywordSearchResult(
                    chunk_id=chunk_id,
                    content=chunk.content[:500] if chunk.content else "",
                    title_path=chunk.title_path,
                    page_start=chunk.page_start,
                    page_end=chunk.page_end,
                    score=score,
                    matches=matches
                ))

            processing_time = int((time.time() - start_time) * 1000)

            return KeywordSearchResponse(
                query=request.query,
                top_k=request.top_k,
                total_results=len(results),
                results=results,
                processing_time_ms=processing_time
            )

        finally:
            db.close()

    def get_statistics(self) -> IndexStatistics:
        """获取索引统计信息"""
        from app.models.chunk import ChunkKeywordIndex

        db = SessionLocal()
        try:
            from app.models.chunk import DocumentChunk

            indexed_chunks = db.query(DocumentChunk).filter(
                DocumentChunk.keyword_indexed == 1
            ).count()

            total_terms = db.query(ChunkKeywordIndex).count()

            content_count = db.query(ChunkKeywordIndex).filter(
                ChunkKeywordIndex.field == "content"
            ).count()

            title_count = db.query(ChunkKeywordIndex).filter(
                ChunkKeywordIndex.field == "title"
            ).count()

            avg_terms = total_terms / indexed_chunks if indexed_chunks > 0 else 0

            return IndexStatistics(
                total_chunks=indexed_chunks,
                total_terms=total_terms,
                avg_terms_per_chunk=avg_terms,
                field_distribution={
                    "content": content_count,
                    "title": title_count
                }
            )

        finally:
            db.close()


# 全局服务实例
_keyword_index_service: Optional[KeywordIndexService] = None


def get_keyword_index_service() -> KeywordIndexService:
    """获取关键词索引服务实例"""
    global _keyword_index_service
    if _keyword_index_service is None:
        _keyword_index_service = KeywordIndexService()
    return _keyword_index_service
