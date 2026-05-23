# -*- coding: utf-8 -*-
"""
切分服务

本模块提供文档语义切分服务，包括：
- 按文档结构选择切分策略
- 语义切片（标题层级/段落边界）
- Token约束控制
- Overlap处理
- 图表与标题合并
"""

import hashlib
import re
import time
import tiktoken
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from app.common.exception import BusinessException, ErrorCode
from app.common.logging import logger
from app.models.chunk import DocumentChunk
from app.models.parse import DocumentElement
from app.parsers.base import ElementType
from app.schemas.chunk import (
    ChunkConfigRequest,
    ChunkElement,
    ChunkingResult,
    ChunkStatistics,
)
from app.schemas.cleaning import CleanedElement
from core.config import settings
from core.database import SessionLocal


# ================================================
# 枚举定义
# ================================================

class ChunkStrategy(str, Enum):
    """切分策略枚举"""
    TITLE_BASED = "title_based"       # 基于标题的切分
    SEMANTIC = "semantic"             # 语义切分
    MIXED = "mixed"                   # 混合切分


# ================================================
# 数据类定义
# ================================================

@dataclass
class TokenCounter:
    """Token计数器"""
    encoding: Any = None

    def __post_init__(self):
        """初始化编码器"""
        try:
            self.encoding = tiktoken.get_encoding("cl100k_base")
        except Exception:
            # 如果cl100k_base不可用，使用备用方案
            self.encoding = None

    def count(self, text: str) -> int:
        """
        计算Token数量

        Args:
            text: 待计数的文本

        Returns:
            Token数量
        """
        if not text:
            return 0

        if self.encoding:
            return len(self.encoding.encode(text))
        else:
            # 简单估算：中文约1.5字符/token，英文约4字符/token
            chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
            other_chars = len(text) - chinese_chars
            return int(chinese_chars / 1.5 + other_chars / 4)


@dataclass
class ChunkBuilder:
    """Chunk构建器"""
    chunk_index: int = 0
    content: str = ""
    enhanced_content: str = ""
    chunk_type: str = "paragraph"
    token_count: int = 0
    char_count: int = 0
    element_ids: List[str] = field(default_factory=list)
    title_path: Optional[str] = None
    chapter_path: Optional[str] = None
    page_start: Optional[int] = None
    page_end: Optional[int] = None
    table_summary: Optional[str] = None
    table_schema: Optional[Dict[str, Any]] = None
    image_description: Optional[Dict[str, Any]] = None
    quality_score: Optional[float] = None
    has_previous_overlap: bool = False
    has_next_overlap: bool = False
    overlap_with_previous: Optional[str] = None
    overlap_with_next: Optional[str] = None

    def add_element(self, element: Any, cleaned: Optional[CleanedElement] = None) -> None:
        """添加元素到chunk"""
        if self.content:
            self.content += "\n"
            self.char_count += 1

        self.content += element.content if hasattr(element, 'content') else str(element)
        self.char_count += len(element.content if hasattr(element, 'content') else str(element))
        self.element_ids.append(element.element_id if hasattr(element, 'element_id') else str(element))

        if self.page_start is None and hasattr(element, 'page_no') and element.page_no:
            self.page_start = element.page_no
        if hasattr(element, 'page_no') and element.page_no:
            self.page_end = element.page_no

        if hasattr(element, 'title_path') and element.title_path and not self.title_path:
            self.title_path = element.title_path

        if cleaned:
            self.enhanced_content += "\n" + cleaned.cleaned_content if self.enhanced_content else cleaned.cleaned_content
            if cleaned.quality_score and self.quality_score:
                self.quality_score = min(self.quality_score, cleaned.quality_score)
            elif cleaned.quality_score:
                self.quality_score = cleaned.quality_score

    def is_empty(self) -> bool:
        """检查是否为空"""
        return not self.content.strip()

    def get_content_hash(self) -> str:
        """计算内容哈希"""
        return hashlib.md5(self.content.encode("utf-8")).hexdigest()


# ================================================
# 切分服务类
# ================================================

class ChunkService:
    """
    文档切分服务

    提供完整的文档语义切分功能，支持多种切分策略和Token约束控制。
    """

    def __init__(self):
        """初始化切分服务"""
        self._token_counter = TokenCounter()
        self._config = settings.chunk

    def chunk_document(
        self,
        document_id: int,
        version_id: int,
        elements: List[DocumentElement],
        cleaned_elements: Optional[List[CleanedElement]] = None,
        config: Optional[ChunkConfigRequest] = None
    ) -> ChunkingResult:
        """
        切分文档

        Args:
            document_id: 文档ID
            version_id: 版本ID
            elements: 待切分的元素列表
            cleaned_elements: 清洗后的元素列表（可选）
            config: 切分配置

        Returns:
            切分结果
        """
        start_time = time.time()

        # 使用默认配置
        if config is None:
            config = ChunkConfigRequest(
                target_tokens=self._config.target_tokens,
                max_tokens=self._config.max_tokens,
                min_tokens=self._config.min_tokens,
                overlap_tokens=self._config.overlap_tokens,
                semantic_threshold=self._config.semantic_threshold
            )

        # 构建元素映射
        element_map = {e.element_id: e for e in elements}
        cleaned_map = {c.element_id: c for c in (cleaned_elements or [])}

        # 分析文档结构
        structure_analysis = self._analyze_structure(elements)

        # 选择切分策略
        strategy = self._select_strategy(structure_analysis, config)

        logger.info(
            f"开始文档切分",
            extra={
                "document_id": document_id,
                "version_id": version_id,
                "total_elements": len(elements),
                "strategy": strategy
            }
        )

        # 根据策略执行切分
        if strategy == ChunkStrategy.TITLE_BASED:
            chunks = self._split_by_title(elements, cleaned_map, config)
        elif strategy == ChunkStrategy.SEMANTIC:
            chunks = self._split_by_semantic(elements, cleaned_map, config)
        else:
            chunks = self._split_mixed(elements, cleaned_map, config)

        # 处理Overlap
        chunks = self._apply_overlap(chunks, config)

        # 构建Chunk元素列表
        chunk_elements = []
        for i, chunk_builder in enumerate(chunks):
            if chunk_builder.is_empty():
                continue

            # 计算Token数量
            token_count = self._token_counter.count(chunk_builder.content)

            # 检查Token约束
            if token_count > config.max_tokens:
                # 强制拆分超长chunk
                sub_chunks = self._split_long_chunk(chunk_builder, config)
                for j, sub_builder in enumerate(sub_chunks):
                    chunk_id = self._generate_chunk_id(document_id, version_id, i * 100 + j)
                    chunk_elements.append(self._build_chunk_element(
                        chunk_id=chunk_id,
                        index=i * 100 + j,
                        builder=sub_builder,
                        config=config
                    ))
            else:
                chunk_id = self._generate_chunk_id(document_id, version_id, i)
                chunk_elements.append(self._build_chunk_element(
                    chunk_id=chunk_id,
                    index=i,
                    builder=chunk_builder,
                    config=config
                ))

        processing_time = int((time.time() - start_time) * 1000)

        # 构建统计信息
        statistics = self._calculate_statistics(chunk_elements)

        logger.info(
            f"文档切分完成",
            extra={
                "document_id": document_id,
                "version_id": version_id,
                "total_chunks": len(chunk_elements),
                "processing_time_ms": processing_time
            }
        )

        return ChunkingResult(
            document_id=document_id,
            version_id=version_id,
            total_elements=len(elements),
            total_chunks=len(chunk_elements),
            strategy_used=strategy,
            config=config,
            chunks=chunk_elements,
            statistics=statistics,
            processing_time_ms=processing_time
        )

    def _analyze_structure(self, elements: List[DocumentElement]) -> Dict[str, Any]:
        """
        分析文档结构

        Args:
            elements: 元素列表

        Returns:
            结构分析结果
        """
        has_titles = False
        title_levels = {}
        has_tables = False
        has_images = False
        avg_paragraph_length = 0
        total_paragraphs = 0

        for element in elements:
            if element.element_type == ElementType.TITLE.value:
                has_titles = True
                level = element.title_level or 1
                title_levels[level] = title_levels.get(level, 0) + 1
            elif element.element_type == ElementType.PARAGRAPH.value:
                total_paragraphs += 1
                avg_paragraph_length += len(element.content or "")
            elif element.element_type == ElementType.TABLE.value:
                has_tables = True
            elif element.element_type == ElementType.IMAGE.value:
                has_images = True

        if total_paragraphs > 0:
            avg_paragraph_length /= total_paragraphs

        return {
            "has_titles": has_titles,
            "title_levels": title_levels,
            "has_tables": has_tables,
            "has_images": has_images,
            "avg_paragraph_length": avg_paragraph_length,
            "total_elements": len(elements)
        }

    def _select_strategy(
        self,
        analysis: Dict[str, Any],
        config: ChunkConfigRequest
    ) -> ChunkStrategy:
        """
        选择切分策略

        Args:
            analysis: 结构分析结果
            config: 切分配置

        Returns:
            切分策略
        """
        # 如果文档有明确的标题层级结构，优先使用基于标题的切分
        if analysis["has_titles"] and len(analysis["title_levels"]) > 1:
            return ChunkStrategy.TITLE_BASED

        # 如果文档有表格或图片，使用混合策略
        if analysis["has_tables"] or analysis["has_images"]:
            return ChunkStrategy.MIXED

        # 如果段落平均长度接近目标Token数，使用语义切分
        if 300 < analysis["avg_paragraph_length"] < 1500:
            return ChunkStrategy.SEMANTIC

        # 默认使用混合策略
        return ChunkStrategy.MIXED

    def _split_by_title(
        self,
        elements: List[DocumentElement],
        cleaned_map: Dict[str, CleanedElement],
        config: ChunkConfigRequest
    ) -> List[ChunkBuilder]:
        """
        基于标题的切分

        Args:
            elements: 元素列表
            cleaned_map: 清洗后元素映射
            config: 切分配置

        Returns:
            Chunk构建器列表
        """
        chunks: List[ChunkBuilder] = []
        current_chunk = ChunkBuilder()
        current_title_path = ""
        current_chapter_path = ""
        current_title_level = 0

        for element in elements:
            # 跳过无内容的元素
            if not element.content or not element.content.strip():
                continue

            cleaned = cleaned_map.get(element.element_id)

            # 处理标题元素
            if element.element_type == ElementType.TITLE.value:
                title_level = element.title_level or 1

                # 如果遇到同级或更高级标题，且当前chunk不为空，创建新chunk
                if title_level <= current_title_level and not current_chunk.is_empty():
                    chunks.append(current_chunk)
                    current_chunk = ChunkBuilder()

                # 更新当前标题路径
                if element.title_path:
                    current_title_path = element.title_path
                else:
                    # 构建标题路径
                    parts = current_title_path.split(" > ")
                    parts = parts[:title_level - 1] + [element.content]
                    current_title_path = " > ".join(parts)

                current_title_level = title_level
                current_chunk.title_path = current_title_path
                current_chunk.chapter_path = current_chapter_path

                # 标题作为独立chunk
                if config.split_by_title:
                    if not current_chunk.is_empty():
                        chunks.append(current_chunk)
                        current_chunk = ChunkBuilder()
                    current_chunk.add_element(element, cleaned)
                    current_chunk.title_path = current_title_path
                    current_chunk.chunk_type = "title"
                    chunks.append(current_chunk)
                    current_chunk = ChunkBuilder()
                    continue

            # 处理段落元素
            elif element.element_type == ElementType.PARAGRAPH.value:
                # 检查Token约束
                element_tokens = self._token_counter.count(element.content)
                current_tokens = self._token_counter.count(current_chunk.content)

                if current_tokens + element_tokens > config.target_tokens and not current_chunk.is_empty():
                    chunks.append(current_chunk)
                    current_chunk = ChunkBuilder()
                    current_chunk.title_path = current_title_path
                    current_chunk.chapter_path = current_chapter_path

                current_chunk.add_element(element, cleaned)

            # 处理表格元素 - 表格需要特殊处理
            elif element.element_type == ElementType.TABLE.value:
                # 先保存当前chunk
                if not current_chunk.is_empty():
                    chunks.append(current_chunk)
                    current_chunk = ChunkBuilder()
                    current_chunk.title_path = current_title_path
                    current_chunk.chapter_path = current_chapter_path

                # 表格作为独立chunk或按行块切分
                table_chunks = self._split_table(element, cleaned, config)
                for tc in table_chunks:
                    tc.title_path = current_title_path
                    tc.chapter_path = current_chapter_path
                    chunks.append(tc)

            # 处理图片元素
            elif element.element_type == ElementType.IMAGE.value:
                if not current_chunk.is_empty():
                    chunks.append(current_chunk)
                    current_chunk = ChunkBuilder()
                    current_chunk.title_path = current_title_path
                    current_chunk.chapter_path = current_chapter_path

                image_chunk = self._process_image_element(element, cleaned, config)
                image_chunk.title_path = current_title_path
                image_chunk.chapter_path = current_chapter_path
                chunks.append(image_chunk)

            # 其他类型元素
            else:
                current_chunk.add_element(element, cleaned)

        # 保存最后一个chunk
        if not current_chunk.is_empty():
            chunks.append(current_chunk)

        # 合并过短的chunk
        if config.merge_short_chunks:
            chunks = self._merge_short_chunks(chunks, config)

        return chunks

    def _split_by_semantic(
        self,
        elements: List[DocumentElement],
        cleaned_map: Dict[str, CleanedElement],
        config: ChunkConfigRequest
    ) -> List[ChunkBuilder]:
        """
        基于语义的切分

        Args:
            elements: 元素列表
            cleaned_map: 清洗后元素映射
            config: 切分配置

        Returns:
            Chunk构建器列表
        """
        chunks: List[ChunkBuilder] = []
        current_chunk = ChunkBuilder()

        for element in elements:
            if not element.content or not element.content.strip():
                continue

            cleaned = cleaned_map.get(element.element_id)

            # 计算当前chunk和新元素的token数
            current_tokens = self._token_counter.count(current_chunk.content)
            element_tokens = self._token_counter.count(element.content)

            # 如果加上新元素会超过最大限制
            if current_tokens + element_tokens > config.max_tokens:
                # 检查是否需要强制拆分
                if element_tokens > config.max_tokens:
                    # 先保存当前chunk
                    if not current_chunk.is_empty():
                        chunks.append(current_chunk)
                        current_chunk = ChunkBuilder()

                    # 拆分超长元素
                    sub_chunks = self._split_long_element(element, cleaned, config)
                    for i, sub in enumerate(sub_chunks[:-1]):
                        chunks.append(sub)
                    current_chunk = sub_chunks[-1] if sub_chunks else ChunkBuilder()
                else:
                    # 保存当前chunk，开始新的
                    chunks.append(current_chunk)
                    current_chunk = ChunkBuilder()
                    current_chunk.add_element(element, cleaned)
            elif current_tokens + element_tokens > config.target_tokens and not current_chunk.is_empty():
                # 达到目标大小时，尝试找语义边界
                if self._is_semantic_boundary(element, elements):
                    chunks.append(current_chunk)
                    current_chunk = ChunkBuilder()
                current_chunk.add_element(element, cleaned)
            else:
                current_chunk.add_element(element, cleaned)

        if not current_chunk.is_empty():
            chunks.append(current_chunk)

        # 合并过短chunk
        if config.merge_short_chunks:
            chunks = self._merge_short_chunks(chunks, config)

        return chunks

    def _split_mixed(
        self,
        elements: List[DocumentElement],
        cleaned_map: Dict[str, CleanedElement],
        config: ChunkConfigRequest
    ) -> List[ChunkBuilder]:
        """
        混合切分策略

        结合基于标题和语义切分的特点，先按标题结构组织，再进行语义切分。

        Args:
            elements: 元素列表
            cleaned_map: 清洗后元素映射
            config: 切分配置

        Returns:
            Chunk构建器列表
        """
        chunks: List[ChunkBuilder] = []
        current_chunk = ChunkBuilder()
        current_title_path = ""

        for element in elements:
            if not element.content or not element.content.strip():
                continue

            cleaned = cleaned_map.get(element.element_id)

            # 标题作为新的起点
            if element.element_type == ElementType.TITLE.value:
                if not current_chunk.is_empty():
                    # 合并过短chunk
                    if config.merge_short_chunks:
                        if current_chunk.token_count < config.min_tokens and chunks:
                            # 合并到前一个chunk
                            last_chunk = chunks[-1]
                            last_chunk.content += "\n" + current_chunk.content
                            last_chunk.char_count += current_chunk.char_count + 1
                            last_chunk.element_ids.extend(current_chunk.element_ids)
                            current_chunk = ChunkBuilder()
                            continue
                    chunks.append(current_chunk)
                current_chunk = ChunkBuilder()
                current_title_path = element.title_path or element.content
                current_chunk.title_path = current_title_path
                current_chunk.add_element(element, cleaned)
                current_chunk.chunk_type = "title"
                continue

            # 非段落元素作为独立chunk
            if element.element_type not in [ElementType.PARAGRAPH.value, ElementType.LIST.value]:
                if not current_chunk.is_empty():
                    chunks.append(current_chunk)
                current_chunk = ChunkBuilder()
                current_chunk.title_path = current_title_path
                current_chunk.add_element(element, cleaned)
                current_chunk.chunk_type = element.element_type
                chunks.append(current_chunk)
                current_chunk = ChunkBuilder()
                continue

            # 段落元素处理
            element_tokens = self._token_counter.count(element.content)

            # 如果超过最大限制
            if element_tokens > config.max_tokens:
                if not current_chunk.is_empty():
                    chunks.append(current_chunk)
                sub_chunks = self._split_long_element(element, cleaned, config)
                chunks.extend(sub_chunks[:-1])
                current_chunk = sub_chunks[-1] if sub_chunks else ChunkBuilder()
            elif self._token_counter.count(current_chunk.content) + element_tokens > config.max_tokens:
                chunks.append(current_chunk)
                current_chunk = ChunkBuilder()
                current_chunk.title_path = current_title_path
                current_chunk.add_element(element, cleaned)
            else:
                current_chunk.add_element(element, cleaned)

        if not current_chunk.is_empty():
            chunks.append(current_chunk)

        # 合并过短chunk
        if config.merge_short_chunks:
            chunks = self._merge_short_chunks(chunks, config)

        return chunks

    def _split_table(
        self,
        element: DocumentElement,
        cleaned: Optional[CleanedElement],
        config: ChunkConfigRequest
    ) -> List[ChunkBuilder]:
        """
        切分表格元素

        长表格按行块切分，每个块保留表头和表题。

        Args:
            element: 表格元素
            cleaned: 清洗后的元素
            config: 切分配置

        Returns:
            Chunk构建器列表
        """
        chunks = []
        chunk = ChunkBuilder()
        chunk.chunk_type = "table"
        chunk.quality_score = cleaned.quality_score if cleaned else None

        # 获取表格结构
        table_structure = element.table_structure
        if not table_structure:
            # 如果没有表格结构，将整个表格作为一个chunk
            chunk.add_element(element, cleaned)
            chunks.append(chunk)
            return chunks

        # 构建表头内容
        headers = table_structure.get("headers", [])
        caption = table_structure.get("caption", "")

        header_content = ""
        if caption:
            header_content = f"表格: {caption}\n"
        if headers:
            header_content += "表头: " + " | ".join(headers[0] if headers else []) + "\n"
            for row in headers[1:]:
                header_content += "  " + " | ".join(row) + "\n"

        header_tokens = self._token_counter.count(header_content)

        # 获取数据行
        rows = table_structure.get("rows", [])
        if not rows:
            chunk.add_element(element, cleaned)
            chunks.append(chunk)
            return chunks

        # 按行块切分
        current_rows: List[List[str]] = []
        current_tokens = header_tokens

        for row in rows:
            row_text = " | ".join(str(cell) for cell in row)
            row_tokens = self._token_counter.count(row_text)

            if current_tokens + row_tokens > config.target_tokens and current_rows:
                # 创建新chunk
                chunk = self._build_table_chunk(header_content, current_rows, element)
                chunks.append(chunk)

                # 重叠处理：保留最后一行
                current_rows = [current_rows[-1]] if len(current_rows) > 1 else []
                current_tokens = header_tokens + self._token_counter.count(
                    " | ".join(str(cell) for cell in current_rows[0]) if current_rows else ""
                )

            current_rows.append(row)
            current_tokens += row_tokens

        # 保存最后一块
        if current_rows:
            chunk = self._build_table_chunk(header_content, current_rows, element)
            chunks.append(chunk)

        return chunks

    def _build_table_chunk(
        self,
        header: str,
        rows: List[List[str]],
        element: DocumentElement
    ) -> ChunkBuilder:
        """构建表格chunk"""
        chunk = ChunkBuilder()
        chunk.chunk_type = "table"
        chunk.page_start = element.page_no
        chunk.page_end = element.page_no
        chunk.table_summary = header

        chunk.content = header
        chunk.char_count = len(header)

        for row in rows:
            row_text = " | ".join(str(cell) for cell in row)
            chunk.content += row_text + "\n"
            chunk.char_count += len(row_text) + 1

        chunk.element_ids = [element.element_id]

        return chunk

    def _process_image_element(
        self,
        element: DocumentElement,
        cleaned: Optional[CleanedElement],
        config: ChunkConfigRequest
    ) -> ChunkBuilder:
        """处理图片元素"""
        chunk = ChunkBuilder()
        chunk.chunk_type = "image"
        chunk.page_start = element.page_no
        chunk.page_end = element.page_no

        # 添加图片描述
        if element.image_description:
            chunk.image_description = element.image_description
            if hasattr(element.image_description, 'description'):
                chunk.content = element.image_description.description
            else:
                chunk.content = str(element.image_description)
        else:
            chunk.content = element.content or ""

        if cleaned:
            chunk.enhanced_content = cleaned.cleaned_content

        chunk.char_count = len(chunk.content)
        chunk.element_ids = [element.element_id]

        return chunk

    def _split_long_element(
        self,
        element: DocumentElement,
        cleaned: Optional[CleanedElement],
        config: ChunkConfigRequest
    ) -> List[ChunkBuilder]:
        """
        拆分超长元素

        Args:
            element: 超长元素
            cleaned: 清洗后的元素
            config: 切分配置

        Returns:
            子chunk列表
        """
        chunks = []
        text = element.content
        sentences = self._split_into_sentences(text)

        current_chunk = ChunkBuilder()
        for sentence in sentences:
            sentence_tokens = self._token_counter.count(sentence)

            if self._token_counter.count(current_chunk.content) + sentence_tokens > config.max_tokens:
                if not current_chunk.is_empty():
                    chunks.append(current_chunk)
                current_chunk = ChunkBuilder()

                # 如果单个句子就超过限制，按字符数拆分
                if sentence_tokens > config.max_tokens:
                    sub_chunks = self._split_by_char_count(sentence, config)
                    chunks.extend(sub_chunks[:-1])
                    current_chunk = sub_chunks[-1] if sub_chunks else ChunkBuilder()
                else:
                    current_chunk.content = sentence
                    current_chunk.char_count = len(sentence)
            else:
                if current_chunk.content:
                    current_chunk.content += sentence
                    current_chunk.char_count += len(sentence)
                else:
                    current_chunk.content = sentence
                    current_chunk.char_count = len(sentence)

            current_chunk.element_ids.append(element.element_id)

        if not current_chunk.is_empty():
            chunks.append(current_chunk)

        return chunks if chunks else [ChunkBuilder()]

    def _split_long_chunk(
        self,
        chunk: ChunkBuilder,
        config: ChunkConfigRequest
    ) -> List[ChunkBuilder]:
        """
        拆分超长chunk

        Args:
            chunk: 超长chunk
            config: 切分配置

        Returns:
            子chunk列表
        """
        chunks = []
        sentences = self._split_into_sentences(chunk.content)

        current = ChunkBuilder()
        for sentence in sentences:
            sentence_tokens = self._token_counter.count(sentence)

            if self._token_counter.count(current.content) + sentence_tokens > config.max_tokens:
                if not current.is_empty():
                    chunks.append(current)
                current = ChunkBuilder()

                if sentence_tokens > config.max_tokens:
                    sub = self._split_by_char_count(sentence, config)
                    chunks.extend(sub[:-1])
                    current = sub[-1] if sub else ChunkBuilder()
                else:
                    current.content = sentence
                    current.char_count = len(sentence)
            else:
                current.content = (current.content + sentence) if current.content else sentence
                current.char_count = len(current.content)

        if not current.is_empty():
            chunks.append(current)

        return chunks if chunks else [chunk]

    def _split_into_sentences(self, text: str) -> List[str]:
        """将文本拆分为句子"""
        # 按中英文句号、问号、感叹号分句
        sentences = re.split(r'([。！？\.\!\?])', text)
        result = []

        for i in range(0, len(sentences) - 1, 2):
            sentence = sentences[i] + sentences[i + 1]
            if sentence.strip():
                result.append(sentence)

        if len(sentences) % 2 == 1 and sentences[-1].strip():
            result.append(sentences[-1])

        return result if result else [text]

    def _split_by_char_count(
        self,
        text: str,
        config: ChunkConfigRequest
    ) -> List[ChunkBuilder]:
        """按字符数拆分"""
        # 估算每个chunk的字符数
        # 中文约1.5字符/token，英文约4字符/token
        chars_per_token = 2  # 平均值
        chunk_size = config.max_tokens * chars_per_token

        chunks = []
        for i in range(0, len(text), chunk_size):
            chunk = ChunkBuilder()
            chunk.content = text[i:i + chunk_size]
            chunk.char_count = len(chunk.content)
            chunks.append(chunk)

        return chunks

    def _is_semantic_boundary(
        self,
        element: DocumentElement,
        elements: List[DocumentElement]
    ) -> bool:
        """
        判断是否为语义边界

        Args:
            element: 当前元素
            elements: 元素列表

        Returns:
            是否为语义边界
        """
        # 检查元素内容是否包含段落分隔标记
        content = element.content or ""

        # 常见的段落分隔模式
        boundary_patterns = [
            r"^(第一|第二|第三|第四|第五|第六|第七|第八|第九|第十)\s*[、,.].*",
            r"^(一|二|三|四|五|六|七|八|九|十)\s*[、,.].*",
            r"^\d+[\.、].*",
            r"^第\d+\s*[章节段].*",
            r"^(但是|然而|不过|因此|所以|总之|综上所述)",
        ]

        for pattern in boundary_patterns:
            if re.match(pattern, content):
                return True

        return False

    def _apply_overlap(
        self,
        chunks: List[ChunkBuilder],
        config: ChunkConfigRequest
    ) -> List[ChunkBuilder]:
        """
        应用Overlap处理

        Args:
            chunks: chunk列表
            config: 切分配置

        Returns:
            处理后的chunk列表
        """
        if len(chunks) < 2 or config.overlap_tokens <= 0:
            return chunks

        overlap_chars = config.overlap_tokens * 2  # 估算字符数

        for i in range(1, len(chunks)):
            prev_chunk = chunks[i - 1]
            curr_chunk = chunks[i]

            # 获取前一个chunk的结尾部分作为重叠内容
            if len(prev_chunk.content) > overlap_chars:
                overlap_content = prev_chunk.content[-overlap_chars:]
                curr_chunk.overlap_with_previous = overlap_content
                curr_chunk.has_previous_overlap = True
                prev_chunk.has_next_overlap = True

        return chunks

    def _merge_short_chunks(
        self,
        chunks: List[ChunkBuilder],
        config: ChunkConfigRequest
    ) -> List[ChunkBuilder]:
        """
        合并过短的chunk

        Args:
            chunks: chunk列表
            config: 切分配置

        Returns:
            合并后的chunk列表
        """
        if not chunks:
            return chunks

        merged: List[ChunkBuilder] = []
        current = chunks[0]

        for i in range(1, len(chunks)):
            next_chunk = chunks[i]

            # 计算当前和下一个chunk的token数
            current_tokens = self._token_counter.count(current.content)
            next_tokens = self._token_counter.count(next_chunk.content)

            # 如果当前chunk过短，尝试合并
            if current_tokens < config.min_tokens:
                # 估算合并后的token数
                combined_tokens = current_tokens + next_tokens

                # 如果合并后不超过目标token数的1.5倍，合并
                if combined_tokens < config.target_tokens * 1.5:
                    current.content += "\n" + next_chunk.content
                    current.char_count += 1 + next_chunk.char_count
                    current.element_ids.extend(next_chunk.element_ids)

                    if not current.title_path and next_chunk.title_path:
                        current.title_path = next_chunk.title_path

                    if next_chunk.chunk_type != "paragraph":
                        current.chunk_type = next_chunk.chunk_type
                    continue

            # 不能合并，保存当前，开始新的
            merged.append(current)
            current = next_chunk

        # 保存最后一个
        if not current.is_empty():
            merged.append(current)

        return merged

    def _calculate_statistics(
        self,
        chunks: List[ChunkElement]
    ) -> Dict[str, Any]:
        """
        计算切分统计信息

        Args:
            chunks: chunk列表

        Returns:
            统计信息
        """
        if not chunks:
            return {
                "total_chunks": 0,
                "avg_tokens": 0,
                "min_tokens": 0,
                "max_tokens": 0,
                "avg_length": 0,
                "chunk_type_distribution": {},
                "quality_distribution": {}
            }

        total_tokens = sum(c.token_count for c in chunks)
        total_length = sum(c.char_count for c in chunks)
        min_tokens = min(c.token_count for c in chunks)
        max_tokens = max(c.token_count for c in chunks)

        # 类型分布
        type_dist = {}
        for c in chunks:
            t = c.chunk_type
            type_dist[t] = type_dist.get(t, 0) + 1

        # 质量分布
        quality_dist = {"good": 0, "warning": 0, "bad": 0}
        for c in chunks:
            if c.quality_score is not None:
                if c.quality_score >= 0.7:
                    quality_dist["good"] += 1
                elif c.quality_score >= 0.4:
                    quality_dist["warning"] += 1
                else:
                    quality_dist["bad"] += 1

        return {
            "total_chunks": len(chunks),
            "avg_tokens": total_tokens / len(chunks) if chunks else 0,
            "min_tokens": min_tokens,
            "max_tokens": max_tokens,
            "avg_length": total_length / len(chunks) if chunks else 0,
            "chunk_type_distribution": type_dist,
            "quality_distribution": quality_dist
        }

    def _generate_chunk_id(
        self,
        document_id: int,
        version_id: int,
        index: int
    ) -> str:
        """生成Chunk ID"""
        unique_str = f"{document_id}_{version_id}_{index}_{time.time()}"
        hash_str = hashlib.md5(unique_str.encode()).hexdigest()[:16]
        return f"chunk_{document_id}_{version_id}_{hash_str}"

    def _build_chunk_element(
        self,
        chunk_id: str,
        index: int,
        builder: ChunkBuilder,
        config: ChunkConfigRequest
    ) -> ChunkElement:
        """构建ChunkElement"""
        token_count = self._token_counter.count(builder.content)

        return ChunkElement(
            chunk_id=chunk_id,
            chunk_index=index,
            content=builder.content,
            enhanced_content=builder.enhanced_content or None,
            chunk_type=builder.chunk_type,
            token_count=token_count,
            char_count=builder.char_count,
            title_path=builder.title_path,
            chapter_path=builder.chapter_path,
            page_start=builder.page_start,
            page_end=builder.page_end,
            quality_score=builder.quality_score,
            element_ids=builder.element_ids,
            table_summary=builder.table_summary,
            table_schema=builder.table_schema,
            image_description=builder.image_description,
            has_previous_overlap=builder.has_previous_overlap,
            has_next_overlap=builder.has_next_overlap,
            overlap_with_previous=builder.overlap_with_previous,
            overlap_with_next=builder.overlap_with_next
        )

    # ================================================
    # 数据库操作方法
    # ================================================

    def save_chunks(
        self,
        document_id: int,
        version_id: int,
        chunks: List[ChunkElement]
    ) -> List[int]:
        """
        保存Chunks到数据库

        Args:
            document_id: 文档ID
            version_id: 版本ID
            chunks: chunk元素列表

        Returns:
            保存的chunk ID列表
        """
        db = SessionLocal()
        saved_ids = []

        try:
            for chunk in chunks:
                # 使用增强内容或原始内容
                content_to_use = chunk.enhanced_content or chunk.content
                # 跳过空内容
                if not content_to_use or not content_to_use.strip():
                    logger.warning(
                        f"跳过空内容的Chunk",
                        extra={"chunk_id": chunk.chunk_id, "document_id": document_id}
                    )
                    continue

                # 计算内容哈希
                content_hash = hashlib.md5(content_to_use.encode("utf-8")).hexdigest()

                # 如果 content 为空但 enhanced_content 有值，使用 enhanced_content 作为 content
                final_content = chunk.content if chunk.content else content_to_use

                db_chunk = DocumentChunk(
                    document_id=document_id,
                    version_id=version_id,
                    chunk_id=chunk.chunk_id,
                    chunk_index=chunk.chunk_index,
                    content=final_content,
                    enhanced_content=chunk.enhanced_content if chunk.enhanced_content else None,
                    content_hash=content_hash,
                    chunk_type=chunk.chunk_type,
                    title_path=chunk.title_path,
                    chapter_path=chunk.chapter_path,
                    page_start=chunk.page_start,
                    page_end=chunk.page_end,
                    token_count=chunk.token_count,
                    char_count=chunk.char_count,
                    element_ids=chunk.element_ids,
                    quality_score=chunk.quality_score,
                    table_summary=chunk.table_summary,
                    table_schema=chunk.table_schema,
                    image_description=chunk.image_description,
                    status=0  # 待向量化
                )
                db.add(db_chunk)
                db.flush()
                saved_ids.append(db_chunk.id)

            db.commit()

            logger.info(
                f"保存Chunks成功",
                extra={
                    "document_id": document_id,
                    "version_id": version_id,
                    "chunk_count": len(saved_ids)
                }
            )

        except Exception as e:
            db.rollback()
            logger.error(f"保存Chunks失败: {str(e)}")
            raise BusinessException(
                code=ErrorCode.OPERATION_FAILED[0],
                message=f"保存Chunks失败: {str(e)}"
            )
        finally:
            db.close()

        return saved_ids

    def get_chunks(
        self,
        document_id: int,
        version_id: Optional[int] = None,
        chunk_type: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        获取文档的Chunks

        Args:
            document_id: 文档ID
            version_id: 版本ID（可选）
            chunk_type: chunk类型筛选
            page: 页码
            page_size: 每页数量

        Returns:
            (chunk列表, 总数)
        """
        db = SessionLocal()
        try:
            query = db.query(DocumentChunk).filter(
                DocumentChunk.document_id == document_id,
                DocumentChunk.status != 9  # 未删除
            )

            if version_id:
                query = query.filter(DocumentChunk.version_id == version_id)

            if chunk_type:
                query = query.filter(DocumentChunk.chunk_type == chunk_type)

            total = query.count()
            chunks = query.order_by(DocumentChunk.chunk_index).offset(
                (page - 1) * page_size
            ).limit(page_size).all()

            return [self._chunk_to_dict(c) for c in chunks], total

        finally:
            db.close()

    def get_chunk_by_id(self, chunk_id: int) -> Optional[Dict[str, Any]]:
        """获取单个Chunk详情"""
        db = SessionLocal()
        try:
            chunk = db.query(DocumentChunk).filter(
                DocumentChunk.id == chunk_id
            ).first()

            return self._chunk_to_dict(chunk) if chunk else None

        finally:
            db.close()

    def _chunk_to_dict(self, chunk: DocumentChunk) -> Dict[str, Any]:
        """将Chunk模型转换为字典"""
        return {
            "id": chunk.id,
            "chunk_id": chunk.chunk_id,
            "document_id": chunk.document_id,
            "version_id": chunk.version_id,
            "chunk_index": chunk.chunk_index,
            "content": chunk.content,
            "enhanced_content": chunk.enhanced_content,
            "content_hash": chunk.content_hash,
            "chunk_type": chunk.chunk_type,
            "title_path": chunk.title_path,
            "chapter_path": chunk.chapter_path,
            "page_start": chunk.page_start,
            "page_end": chunk.page_end,
            "token_count": chunk.token_count,
            "char_count": chunk.char_count,
            "element_ids": chunk.element_ids,
            "quality_score": chunk.quality_score,
            "table_summary": chunk.table_summary,
            "table_schema": chunk.table_schema,
            "image_description": chunk.image_description,
            "is_duplicate": chunk.is_duplicate,
            "duplicate_of": chunk.duplicate_of,
            "status": chunk.status,
            "vector_id": chunk.vector_id,
            "keyword_indexed": chunk.keyword_indexed,
            "created_at": chunk.created_at.isoformat() if chunk.created_at else None,
            "updated_at": chunk.updated_at.isoformat() if chunk.updated_at else None
        }


# 全局服务实例
_chunk_service: Optional[ChunkService] = None


def get_chunk_service() -> ChunkService:
    """获取切分服务实例"""
    global _chunk_service
    if _chunk_service is None:
        _chunk_service = ChunkService()
    return _chunk_service
