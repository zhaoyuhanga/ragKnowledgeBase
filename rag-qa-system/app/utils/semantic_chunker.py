"""
RAG 问答系统 - 结构化语义切分器模块
生产级中文 RAG 文档切分方案：
结构优先 + 语义合并 + token 约束 + parent-child retrieval
"""

import re
import hashlib
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from enum import Enum

from app.core.logger import get_logger

logger = get_logger(__name__)


class BlockType(str, Enum):
    """块类型枚举"""
    TITLE = "title"
    PARAGRAPH = "paragraph"
    LIST = "list"
    TABLE = "table"
    CODE = "code"
    MIXED = "mixed"


@dataclass
class ChunkMetadata:
    """Chunk 元数据"""
    chunk_index: int
    document_id: int
    parent_section_id: str
    title_path: str
    section_level: int
    block_type: str
    page_no: Optional[int] = None
    token_count: int = 0
    char_count: int = 0
    content_hash: str = ""
    chunk_version: str = "semantic-v1"


@dataclass
class Chunk:
    """切分后的文本块"""
    content: str
    enhanced_content: str
    metadata: ChunkMetadata

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "content": self.content,
            "enhanced_content": self.enhanced_content,
            **self.metadata.__dict__
        }


class Section:
    """文档章节"""

    def __init__(
        self,
        section_id: str,
        title: str,
        level: int,
        parent_id: Optional[str] = None
    ):
        self.section_id = section_id
        self.title = title
        self.level = level
        self.parent_id = parent_id
        self.blocks: List[Dict[str, Any]] = []

    def add_block(self, block_type: str, content: str, raw_content: Optional[str] = None):
        """添加内容块"""
        self.blocks.append({
            "type": block_type,
            "content": content,
            "raw_content": raw_content or content
        })


class SemanticChunker:
    """
    结构化语义切分器

    特点：
    1. 优先按结构切分（标题、段落、列表、表格、代码块）
    2. 按 token 约束合并
    3. 支持 parent-child retrieval
    4. 自动生成 enhanced_content
    """

    def __init__(
        self,
        target_tokens: int = 600,
        max_tokens: int = 900,
        min_tokens: int = 120,
        overlap_tokens: int = 100,
        version: str = "semantic-v1"
    ):
        self.target_tokens = target_tokens
        self.max_tokens = max_tokens
        self.min_tokens = min_tokens
        self.overlap_tokens = overlap_tokens
        self.version = version

    def split_text(
        self,
        text: str,
        document_id: int = 0,
        page_no: Optional[int] = None
    ) -> List[Chunk]:
        """
        切分文本为结构化 chunks

        Args:
            text: 待切分文本
            document_id: 文档 ID
            page_no: 页码

        Returns:
            Chunk 列表
        """
        if not text or not text.strip():
            logger.warning("输入文本为空")
            return []

        # 解析文档结构
        sections = self._parse_document_structure(text)

        # 生成 chunks
        chunks = self._generate_chunks(
            sections,
            document_id,
            page_no
        )

        logger.info(f"文本切分完成: {len(chunks)} 个 chunks")
        return chunks

    def _parse_document_structure(self, text: str) -> List[Section]:
        """解析文档结构"""
        sections = []
        current_section = Section("root", "", 0)

        lines = text.split('\n')
        i = 0

        while i < len(lines):
            line = lines[i]

            # 跳过空行
            if not line.strip():
                i += 1
                continue

            # 检查 Markdown 标题
            heading_match = re.match(r'^(#{1,6})\s+(.+)$', line)
            if heading_match:
                level = len(heading_match.group(1))
                title = heading_match.group(2).strip()

                if current_section.blocks:
                    sections.append(current_section)

                new_section = Section(
                    section_id=f"s_{len(sections)}",
                    title=title,
                    level=level,
                    parent_id=current_section.section_id if current_section.level > 0 else None
                )
                current_section = new_section
                i += 1
                continue

            # 检查代码块
            if line.strip().startswith('```'):
                code_lines = []
                i += 1
                while i < len(lines) and not lines[i].strip().startswith('```'):
                    code_lines.append(lines[i])
                    i += 1
                code_content = '\n'.join(code_lines)
                current_section.add_block(BlockType.CODE, code_content)
                i += 1
                continue

            # 检查 Markdown 表格
            if '|' in line:
                table_lines = []
                while i < len(lines) and '|' in lines[i]:
                    table_lines.append(lines[i])
                    i += 1
                table_content = '\n'.join(table_lines)
                current_section.add_block(BlockType.TABLE, table_content)
                continue

            # 检查列表
            list_match = re.match(r'^(\s*)[-*+]\s+(.+)$', line)
            if not list_match:
                list_match = re.match(r'^(\s*)\d+\.\s+(.+)$', line)

            if list_match:
                list_items = []
                indent = len(list_match.group(1))
                while i < len(lines):
                    item_match = re.match(r'^(\s*)[-*+]\s+(.+)$', lines[i])
                    if not item_match:
                        item_match = re.match(r'^(\s*)\d+\.\s+(.+)$', lines[i])
                    if not item_match or len(item_match.group(1)) < indent:
                        break
                    list_items.append(item_match.group(2).strip())
                    i += 1
                list_content = '\n'.join(f"- {item}" for item in list_items)
                current_section.add_block(BlockType.LIST, list_content)
                continue

            # 普通段落
            para_lines = []
            while i < len(lines):
                if not lines[i].strip():
                    break
                if re.match(r'^(#{1,6})\s+', lines[i]):
                    break
                if lines[i].strip().startswith('```'):
                    break
                if '|' in lines[i] and i > 0:
                    break
                para_lines.append(lines[i])
                i += 1

            if para_lines:
                para_content = '\n'.join(para_lines)
                current_section.add_block(BlockType.PARAGRAPH, para_content)

        if current_section.blocks:
            sections.append(current_section)

        if not sections:
            sections.append(Section("s_0", "", 0))

        return sections

    def _generate_chunks(
        self,
        sections: List[Section],
        document_id: int,
        page_no: Optional[int]
    ) -> List[Chunk]:
        """生成 chunks"""
        chunks = []
        chunk_index = 0

        for section in sections:
            title_path = section.title

            paragraphs = []

            for block in section.blocks:
                block_type = block["type"]
                content = block["content"]

                if block_type == BlockType.CODE:
                    if paragraphs:
                        para_chunks = self._merge_paragraphs(
                            paragraphs, title_path, section,
                            document_id, chunk_index, page_no
                        )
                        chunks.extend(para_chunks)
                        chunk_index = chunks[-1].metadata.chunk_index + 1 if chunks else 0
                        paragraphs = []

                    chunk = self._create_chunk(
                        content=content,
                        block_type=BlockType.CODE,
                        section=section,
                        title_path=title_path,
                        document_id=document_id,
                        chunk_index=chunk_index,
                        page_no=page_no
                    )
                    chunks.append(chunk)
                    chunk_index += 1

                elif block_type == BlockType.TABLE:
                    if paragraphs:
                        para_chunks = self._merge_paragraphs(
                            paragraphs, title_path, section,
                            document_id, chunk_index, page_no
                        )
                        chunks.extend(para_chunks)
                        chunk_index = chunks[-1].metadata.chunk_index + 1 if chunks else 0
                        paragraphs = []

                    table_chunks = self._split_table(
                        content, title_path, section,
                        document_id, chunk_index, page_no
                    )
                    chunks.extend(table_chunks)
                    chunk_index = chunks[-1].metadata.chunk_index + 1 if chunks else 0

                elif block_type == BlockType.LIST:
                    if paragraphs:
                        para_chunks = self._merge_paragraphs(
                            paragraphs, title_path, section,
                            document_id, chunk_index, page_no
                        )
                        chunks.extend(para_chunks)
                        chunk_index = chunks[-1].metadata.chunk_index + 1 if chunks else 0
                        paragraphs = []

                    list_chunks = self._split_list(
                        content, title_path, section,
                        document_id, chunk_index, page_no
                    )
                    chunks.extend(list_chunks)
                    chunk_index = chunks[-1].metadata.chunk_index + 1 if chunks else 0

                else:
                    tokens = self._estimate_tokens(content)
                    if paragraphs and self._estimate_tokens('\n\n'.join(paragraphs)) + tokens > self.target_tokens:
                        para_chunks = self._merge_paragraphs(
                            paragraphs, title_path, section,
                            document_id, chunk_index, page_no
                        )
                        chunks.extend(para_chunks)
                        chunk_index = chunks[-1].metadata.chunk_index + 1 if chunks else 0
                        paragraphs = []

                    paragraphs.append(content)

            if paragraphs:
                para_chunks = self._merge_paragraphs(
                    paragraphs, title_path, section,
                    document_id, chunk_index, page_no
                )
                chunks.extend(para_chunks)

        return chunks

    def _merge_paragraphs(
        self,
        paragraphs: List[str],
        title_path: str,
        section: Section,
        document_id: int,
        chunk_index: int,
        page_no: Optional[int]
    ) -> List[Chunk]:
        """合并段落生成 chunks"""
        if not paragraphs:
            return []

        chunks = []
        current_paragraphs = []
        current_tokens = 0

        for para in paragraphs:
            para_tokens = self._estimate_tokens(para)

            if current_tokens + para_tokens > self.max_tokens and current_paragraphs:
                merged = '\n\n'.join(current_paragraphs)
                chunk = self._create_chunk(
                    content=merged,
                    block_type=BlockType.PARAGRAPH,
                    section=section,
                    title_path=title_path,
                    document_id=document_id,
                    chunk_index=chunk_index,
                    page_no=page_no
                )
                chunks.append(chunk)
                chunk_index += 1

                overlap_text = current_paragraphs[-1] if len(current_paragraphs) > 1 else current_paragraphs[0]
                overlap_tokens = self._estimate_tokens(overlap_text)
                if overlap_tokens <= self.overlap_tokens:
                    current_paragraphs = [overlap_text]
                    current_tokens = overlap_tokens
                else:
                    current_paragraphs = []
                    current_tokens = 0

            current_paragraphs.append(para)
            current_tokens += para_tokens

            if para_tokens > self.max_tokens:
                sub_chunks = self._split_long_paragraph(
                    para, title_path, section,
                    document_id, chunk_index, page_no
                )
                if len(sub_chunks) > 1:
                    merged = '\n\n'.join([c.content for c in sub_chunks[:-1]])
                    chunk = self._create_chunk(
                        content=merged,
                        block_type=BlockType.PARAGRAPH,
                        section=section,
                        title_path=title_path,
                        document_id=document_id,
                        chunk_index=chunk_index,
                        page_no=page_no
                    )
                    chunks.append(chunk)
                    chunk_index += 1
                    current_paragraphs = [sub_chunks[-1].content]
                    current_tokens = self._estimate_tokens(sub_chunks[-1].content)
                elif sub_chunks:
                    current_paragraphs = [sub_chunks[0].content]
                    current_tokens = self._estimate_tokens(sub_chunks[0].content)

        if current_paragraphs:
            merged = '\n\n'.join(current_paragraphs)
            chunk = self._create_chunk(
                content=merged,
                block_type=BlockType.PARAGRAPH,
                section=section,
                title_path=title_path,
                document_id=document_id,
                chunk_index=chunk_index,
                page_no=page_no
            )
            chunks.append(chunk)

        return chunks

    def _split_long_paragraph(
        self,
        text: str,
        title_path: str,
        section: Section,
        document_id: int,
        chunk_index: int,
        page_no: Optional[int]
    ) -> List[Chunk]:
        """拆分超长段落"""
        chunks = []

        sentences = re.split(r'([。！？；])', text)
        merged_sentences = []
        for i in range(0, len(sentences) - 1, 2):
            if i + 1 < len(sentences):
                merged_sentences.append(sentences[i] + sentences[i + 1])
            elif sentences[i].strip():
                merged_sentences.append(sentences[i])

        current_text = ""
        current_tokens = 0

        for sentence in merged_sentences:
            sentence_tokens = self._estimate_tokens(sentence)

            if current_tokens + sentence_tokens > self.max_tokens and current_text:
                chunk = self._create_chunk(
                    content=current_text,
                    block_type=BlockType.PARAGRAPH,
                    section=section,
                    title_path=title_path,
                    document_id=document_id,
                    chunk_index=chunk_index,
                    page_no=page_no
                )
                chunks.append(chunk)
                chunk_index += 1

                overlap_text = current_text[-100:] if len(current_text) > 100 else current_text
                current_text = overlap_text
                current_tokens = self._estimate_tokens(overlap_text)

            current_text += sentence
            current_tokens += sentence_tokens

        if current_text.strip():
            chunk = self._create_chunk(
                content=current_text,
                block_type=BlockType.PARAGRAPH,
                section=section,
                title_path=title_path,
                document_id=document_id,
                chunk_index=chunk_index,
                page_no=page_no
            )
            chunks.append(chunk)

        return chunks

    def _split_table(
        self,
        text: str,
        title_path: str,
        section: Section,
        document_id: int,
        chunk_index: int,
        page_no: Optional[int]
    ) -> List[Chunk]:
        """拆分超长表格"""
        lines = text.strip().split('\n')
        if not lines:
            return []

        chunks = []
        header = lines[0] if lines else ""
        header_tokens = self._estimate_tokens(header)
        max_data_tokens = self.max_tokens - header_tokens - 50

        current_rows = []
        current_tokens = 0

        for row in lines[1:]:
            row_tokens = self._estimate_tokens(row)

            if current_tokens + row_tokens > max_data_tokens and current_rows:
                table_content = header + '\n' + '\n'.join(current_rows)
                chunk = self._create_chunk(
                    content=table_content,
                    block_type=BlockType.TABLE,
                    section=section,
                    title_path=title_path,
                    document_id=document_id,
                    chunk_index=chunk_index,
                    page_no=page_no
                )
                chunks.append(chunk)
                chunk_index += 1

                current_rows = current_rows[-1:] if len(current_rows) > 1 else current_rows
                current_tokens = self._estimate_tokens('\n'.join(current_rows)) if current_rows else 0

            current_rows.append(row)
            current_tokens += row_tokens

        if current_rows:
            table_content = header + '\n' + '\n'.join(current_rows)
            chunk = self._create_chunk(
                content=table_content,
                block_type=BlockType.TABLE,
                section=section,
                title_path=title_path,
                document_id=document_id,
                chunk_index=chunk_index,
                page_no=page_no
            )
            chunks.append(chunk)

        return chunks

    def _split_list(
        self,
        text: str,
        title_path: str,
        section: Section,
        document_id: int,
        chunk_index: int,
        page_no: Optional[int]
    ) -> List[Chunk]:
        """拆分超长列表"""
        lines = text.strip().split('\n')
        if not lines:
            return []

        chunks = []
        current_items = []
        current_tokens = 0

        for item in lines:
            item_tokens = self._estimate_tokens(item)

            if current_tokens + item_tokens > self.max_tokens and current_items:
                list_content = '\n'.join(current_items)
                chunk = self._create_chunk(
                    content=list_content,
                    block_type=BlockType.LIST,
                    section=section,
                    title_path=title_path,
                    document_id=document_id,
                    chunk_index=chunk_index,
                    page_no=page_no
                )
                chunks.append(chunk)
                chunk_index += 1

                current_items = current_items[-1:] if len(current_items) > 1 else current_items
                current_tokens = self._estimate_tokens('\n'.join(current_items)) if current_items else 0

            current_items.append(item)
            current_tokens += item_tokens

        if current_items:
            list_content = '\n'.join(current_items)
            chunk = self._create_chunk(
                content=list_content,
                block_type=BlockType.LIST,
                section=section,
                title_path=title_path,
                document_id=document_id,
                chunk_index=chunk_index,
                page_no=page_no
            )
            chunks.append(chunk)

        return chunks

    def _create_chunk(
        self,
        content: str,
        block_type: str,
        section: Section,
        title_path: str,
        document_id: int,
        chunk_index: int,
        page_no: Optional[int]
    ) -> Chunk:
        """创建 chunk"""
        enhanced = self._generate_enhanced_content(content, title_path)
        token_count = self._estimate_tokens(content)
        char_count = len(content)
        content_hash = hashlib.md5(content.encode('utf-8')).hexdigest()

        metadata = ChunkMetadata(
            chunk_index=chunk_index,
            document_id=document_id,
            parent_section_id=section.section_id,
            title_path=title_path,
            section_level=section.level,
            block_type=block_type,
            page_no=page_no,
            token_count=token_count,
            char_count=char_count,
            content_hash=content_hash,
            chunk_version=self.version
        )

        return Chunk(
            content=content,
            enhanced_content=enhanced,
            metadata=metadata
        )

    def _generate_enhanced_content(self, content: str, title_path: str) -> str:
        """生成 enhanced_content（用于 embedding）"""
        parts = []
        if title_path:
            parts.append(f"[{title_path}]")
        parts.append(content)
        return " ".join(parts)

    def _estimate_tokens(self, text: str) -> int:
        """估算 token 数量"""
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        other_chars = len(text) - chinese_chars
        return int(chinese_chars + other_chars * 0.25)


# 全局实例
semantic_chunker = SemanticChunker()


def get_semantic_chunker() -> SemanticChunker:
    """获取切分器实例"""
    return semantic_chunker
