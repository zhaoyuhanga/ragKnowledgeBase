# -*- coding: utf-8 -*-
"""
上下文组装服务

本模块提供上下文组装功能：
- 按标题路径和页码重组上下文
- Token预算裁剪
- 来源引用绑定
"""

import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from app.common.logging import logger
from core.config import settings


@dataclass
class ContextChunk:
    """上下文Chunk"""
    chunk_id: int
    document_id: int
    version_id: int
    title_path: Optional[str]
    page_start: Optional[int]
    page_end: Optional[int]
    content: str
    chunk_type: str
    rerank_score: float
    quality_score: float
    source_info: Dict[str, str]


@dataclass
class AssembledContext:
    """组装后的上下文"""
    chunks: List[ContextChunk]
    total_tokens: int
    total_content: str
    references: List[Dict[str, Any]]
    metadata: Dict[str, Any]


class ContextAssembler:
    """
    上下文组装器

    负责将重排序后的Chunks组装成最终上下文。
    """

    def __init__(self):
        """初始化组装器"""
        self._max_tokens = settings.chunk.target_tokens * 20  # 上下文总token限制

    def assemble(
        self,
        reranked_results: List[Any],
        max_tokens: Optional[int] = None,
        include_metadata: bool = True
    ) -> AssembledContext:
        """
        组装上下文

        Args:
            reranked_results: 重排序后的结果
            max_tokens: 最大token数量限制
            include_metadata: 是否包含元数据

        Returns:
            组装后的上下文
        """
        start_time = time.time()

        if not reranked_results:
            return AssembledContext(
                chunks=[],
                total_tokens=0,
                total_content="",
                references=[],
                metadata={}
            )

        # 计算token限制
        if max_tokens is None:
            max_tokens = self._max_tokens

        # 1. 构建上下文Chunk列表
        context_chunks = []
        for result in reranked_results:
            if isinstance(result, dict):
                chunk = ContextChunk(
                    chunk_id=result.get("chunk_id", 0),
                    document_id=result.get("document_id", 0),
                    version_id=result.get("version_id", 0),
                    title_path=result.get("title_path"),
                    page_start=result.get("page_start"),
                    page_end=result.get("page_end"),
                    content=result.get("content", ""),
                    chunk_type=result.get("chunk_type", "paragraph"),
                    rerank_score=result.get("rerank_score", result.get("score", 0)),
                    quality_score=result.get("quality_score", 0),
                    source_info={}
                )
            else:
                # 处理RetrievalResult对象或类似结构
                # RetrievalResult有chunk属性(ChunkReference)，其他对象可能有直接属性
                if hasattr(result, 'chunk'):
                    # RetrievalResult对象结构
                    chunk_ref = result.chunk
                    chunk = ContextChunk(
                        chunk_id=chunk_ref.chunk_id,
                        document_id=chunk_ref.document_id,
                        version_id=chunk_ref.version_id,
                        title_path=chunk_ref.title_path,
                        page_start=chunk_ref.page_start,
                        page_end=chunk_ref.page_end,
                        content=chunk_ref.content,
                        chunk_type=chunk_ref.chunk_type,
                        rerank_score=getattr(result, "rerank_score", getattr(result, "fusion_score", 0)),
                        quality_score=getattr(result, "quality_score", 0),
                        source_info={}
                    )
                else:
                    # RerankResult或其他直接属性结构
                    chunk = ContextChunk(
                        chunk_id=result.chunk_id,
                        document_id=result.document_id,
                        version_id=result.version_id,
                        title_path=result.title_path,
                        page_start=result.page_start,
                        page_end=result.page_end,
                        content=result.content,
                        chunk_type=result.chunk_type,
                        rerank_score=getattr(result, "rerank_score", getattr(result, "score", 0)),
                        quality_score=getattr(result, "quality_score", 0),
                        source_info={}
                    )

            # 添加来源信息
            if include_metadata:
                chunk.source_info = self._build_source_info(chunk)

            context_chunks.append(chunk)

        # 2. 按标题路径和页码分组排序
        context_chunks = self._group_and_sort(context_chunks)

        # 3. Token预算裁剪
        total_tokens = 0
        selected_chunks = []
        for chunk in context_chunks:
            chunk_tokens = self._estimate_tokens(chunk.content)

            if total_tokens + chunk_tokens <= max_tokens:
                selected_chunks.append(chunk)
                total_tokens += chunk_tokens
            else:
                # 检查是否还有空间容纳更小的内容
                if not selected_chunks:
                    # 如果第一个chunk就超限，截断它
                    truncated_content = self._truncate_to_tokens(chunk.content, max_tokens)
                    chunk.content = truncated_content
                    selected_chunks.append(chunk)
                    total_tokens = self._estimate_tokens(truncated_content)
                break

        # 4. 构建完整内容
        total_content = self._build_content(selected_chunks)

        # 5. 构建引用列表
        references = self._build_references(selected_chunks)

        # 6. 构建元数据
        metadata = {
            "chunk_count": len(selected_chunks),
            "total_tokens": total_tokens,
            "document_count": len(set(c.document_id for c in selected_chunks)),
            "version_count": len(set(c.version_id for c in selected_chunks)),
            "page_range": self._get_page_range(selected_chunks),
        }

        assembly_time_ms = int((time.time() - start_time) * 1000)

        logger.info(
            "上下文组装完成",
            extra={
                "input_count": len(reranked_results),
                "output_count": len(selected_chunks),
                "total_tokens": total_tokens,
                "assembly_time_ms": assembly_time_ms
            }
        )

        return AssembledContext(
            chunks=selected_chunks,
            total_tokens=total_tokens,
            total_content=total_content,
            references=references,
            metadata=metadata
        )

    def _group_and_sort(self, chunks: List[ContextChunk]) -> List[ContextChunk]:
        """
        按标题路径和页码分组排序

        Args:
            chunks: Chunk列表

        Returns:
            排序后的Chunk列表
        """
        if not chunks:
            return []

        # 按(文档ID, 版本ID, 标题路径, 起始页码)分组
        grouped: Dict[Tuple, List[ContextChunk]] = {}

        for chunk in chunks:
            key = (
                chunk.document_id,
                chunk.version_id,
                chunk.title_path or "",
                chunk.page_start or 0
            )
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(chunk)

        # 按组内分数排序，取最高分
        sorted_chunks = []
        for key, group in grouped.items():
            # 按rerank_score降序排序
            group.sort(key=lambda x: x.rerank_score, reverse=True)
            sorted_chunks.append(group[0])

        # 整体按文档、版本、页码排序
        sorted_chunks.sort(key=lambda x: (
            x.document_id,
            x.version_id,
            x.title_path or "",
            x.page_start or 0,
            -x.rerank_score  # 同位置按分数降序
        ))

        return sorted_chunks

    def _build_source_info(self, chunk: ContextChunk) -> Dict[str, str]:
        """
        构建来源信息

        Args:
            chunk: 上下文Chunk

        Returns:
            来源信息字典
        """
        source_info = {
            "source": f"文档ID:{chunk.document_id}",
            "location": "",
        }

        # 添加标题路径
        if chunk.title_path:
            source_info["source"] = f"{source_info['source']} / {chunk.title_path}"

        # 添加页码
        if chunk.page_start:
            if chunk.page_end and chunk.page_end != chunk.page_start:
                source_info["location"] = f"第{chunk.page_start}-{chunk.page_end}页"
            else:
                source_info["location"] = f"第{chunk.page_start}页"

        # 添加类型
        type_map = {
            "paragraph": "段落",
            "table": "表格",
            "image": "图片",
            "chart": "图表",
            "code": "代码",
            "list": "列表"
        }
        source_info["type"] = type_map.get(chunk.chunk_type, chunk.chunk_type)

        return source_info

    def _estimate_tokens(self, text: str) -> int:
        """
        估算token数量

        简单的估算方法：中文按字符数计算，英文按空格分隔的词数计算。

        Args:
            text: 文本内容

        Returns:
            估算的token数量
        """
        if not text:
            return 0

        # 中文按字符计算
        chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
        # 英文按词计算
        english_words = len([w for w in text.split() if w.isascii()])
        # 其他字符
        other_chars = len(text) - chinese_chars - sum(1 for w in text.split() if w.isascii())

        # 估算：中文每个字符约1个token，英文每个词约1.3个token
        return int(chinese_chars + english_words * 1.3 + other_chars * 0.5)

    def _truncate_to_tokens(self, text: str, max_tokens: int) -> str:
        """
        截断文本到指定token数

        Args:
            text: 文本内容
            max_tokens: 最大token数

        Returns:
            截断后的文本
        """
        if not text:
            return ""

        tokens = 0
        result = []
        for char in text:
            result.append(char)
            if '\u4e00' <= char <= '\u9fff':
                tokens += 1
            elif char.isascii() and char.strip():
                tokens += 1.3
            else:
                tokens += 0.5

            if tokens >= max_tokens:
                break

        return "".join(result)

    def _build_content(self, chunks: List[ContextChunk]) -> str:
        """
        构建完整上下文内容

        Args:
            chunks: 上下文Chunk列表

        Returns:
            完整的上下文文本
        """
        if not chunks:
            return ""

        parts = []
        for i, chunk in enumerate(chunks):
            # 添加来源标记
            source_label = f"[来源{i+1}] "
            if chunk.title_path:
                source_label += f"{chunk.title_path} "
            if chunk.page_start:
                if chunk.page_end and chunk.page_end != chunk.page_start:
                    source_label += f"(页{chunk.page_start}-{chunk.page_end})"
                else:
                    source_label += f"(页{chunk.page_start})"

            # 段落分隔
            if i > 0:
                parts.append("\n\n")

            parts.append(f"{source_label}\n{chunk.content}")

        return "".join(parts)

    def _build_references(self, chunks: List[ContextChunk]) -> List[Dict[str, Any]]:
        """
        构建引用列表

        Args:
            chunks: 上下文Chunk列表

        Returns:
            引用列表
        """
        references = []

        for i, chunk in enumerate(chunks):
            reference = {
                "index": i + 1,
                "chunk_id": chunk.chunk_id,
                "document_id": chunk.document_id,
                "version_id": chunk.version_id,
                "title_path": chunk.title_path,
                "page_start": chunk.page_start,
                "page_end": chunk.page_end,
                "content_preview": chunk.content[:200] + "..." if len(chunk.content) > 200 else chunk.content,
                "chunk_type": chunk.chunk_type,
                "rerank_score": chunk.rerank_score,
                "quality_score": chunk.quality_score,
            }
            references.append(reference)

        return references

    def _get_page_range(self, chunks: List[ContextChunk]) -> Dict[str, Any]:
        """
        获取页码范围

        Args:
            chunks: 上下文Chunk列表

        Returns:
            页码范围信息
        """
        pages = []
        for chunk in chunks:
            if chunk.page_start:
                pages.append(chunk.page_start)
            if chunk.page_end:
                pages.append(chunk.page_end)

        if not pages:
            return {"start": None, "end": None, "total_pages": 0}

        return {
            "start": min(pages),
            "end": max(pages),
            "total_pages": len(set(pages))
        }


class PromptBuilder:
    """
    Prompt构造器

    负责构造问答Prompt。
    """

    def __init__(self):
        """初始化构造器"""
        self._system_prompt = self._get_default_system_prompt()
        self._user_prompt_template = self._get_default_user_prompt_template()

    def _get_default_system_prompt(self) -> str:
        """获取默认系统提示"""
        return """你是一个专业的知识库问答助手，擅长从文档中提取信息并准确回答用户问题。

## 回答原则
1. **基于事实**：只根据提供的上下文内容回答，不要编造信息
2. **诚实守信**：如果上下文中没有相关信息，诚实地回答"抱歉，我没有找到相关信息"
3. **准确简洁**：回答要准确、简洁、有条理，避免冗余
4. **结构清晰**：使用合理的段落和层次结构组织答案
5. **引用来源**：标注信息来源，如：[来源1]

## 回答格式
- 优先使用简洁的段落形式
- 涉及数据或统计时，引用具体的上下文来源
- 表格内容用结构化方式呈现
- 代码内容使用代码块格式

## 注意事项
- 如果多个来源信息有冲突，说明不同来源的观点
- 对于模糊或部分匹配的问题，说明匹配程度
- 保持回答的专业性和客观性"""

    def _get_default_user_prompt_template(self) -> str:
        """获取默认用户提示模板"""
        return """请根据以下上下文内容回答问题。

问题：{question}

上下文：
{context}

请根据以上上下文回答问题。如果上下文中没有相关信息，请如实说明。"""

    def build(self, question: str, context: AssembledContext) -> Tuple[str, str]:
        """
        构造Prompt

        Args:
            question: 用户问题
            context: 组装后的上下文

        Returns:
            (system_prompt, user_prompt)
        """
        # 格式化上下文
        context_text = context.total_content

        # 格式化用户Prompt
        user_prompt = self._user_prompt_template.format(
            question=question,
            context=context_text or "（无相关上下文）"
        )

        return self._system_prompt, user_prompt

    def build_with_sources(
        self,
        question: str,
        context: AssembledContext,
        include_stats: bool = True
    ) -> Tuple[str, str, Dict[str, Any]]:
        """
        构造带统计信息的Prompt

        Args:
            question: 用户问题
            context: 组装后的上下文
            include_stats: 是否包含统计信息

        Returns:
            (system_prompt, user_prompt, metadata)
        """
        system_prompt, user_prompt = self.build(question, context)

        metadata = {
            "chunk_count": context.metadata.get("chunk_count", 0),
            "total_tokens": context.metadata.get("total_tokens", 0),
            "document_count": context.metadata.get("document_count", 0),
            "references_count": len(context.references),
        }

        if include_stats:
            stats_text = f"""
【参考信息统计】
- 引用文档数：{metadata['document_count']}
- 引用Chunk数：{metadata['chunk_count']}
- 预估Token数：{metadata['total_tokens']}
"""
            user_prompt += stats_text

        return system_prompt, user_prompt, metadata

    def set_custom_system_prompt(self, prompt: str) -> None:
        """
        设置自定义系统提示

        Args:
            prompt: 自定义系统提示
        """
        self._system_prompt = prompt

    def set_custom_user_prompt_template(self, template: str) -> None:
        """
        设置自定义用户提示模板

        Args:
            template: 自定义用户提示模板，变量占位符使用{question}和{context}
        """
        self._user_prompt_template = template


# 全局实例
_context_assembler: Optional[ContextAssembler] = None
_prompt_builder: Optional[PromptBuilder] = None


def get_context_assembler() -> ContextAssembler:
    """获取上下文组装器实例"""
    global _context_assembler
    if _context_assembler is None:
        _context_assembler = ContextAssembler()
    return _context_assembler


def get_prompt_builder() -> PromptBuilder:
    """获取Prompt构造器实例"""
    global _prompt_builder
    if _prompt_builder is None:
        _prompt_builder = PromptBuilder()
    return _prompt_builder
