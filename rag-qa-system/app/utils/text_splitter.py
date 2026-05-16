"""
RAG 问答系统 - 文本切分工具模块
支持多种文本切分策略
"""

from typing import List, Tuple, Optional
import re

from app.config import settings
from app.core.logger import get_logger

logger = get_logger(__name__)


class TextSplitter:
    """
    文本切分器
    将长文本切分为适合检索的文本块
    """
    
    def __init__(
        self,
        chunk_size: int = None,
        chunk_overlap: int = None,
        min_chunk_size: int = None,
        separator: str = "\n\n"
    ):
        """
        初始化文本切分器
        
        Args:
            chunk_size: 文本块最大字符数
            chunk_overlap: 文本块重叠字符数
            min_chunk_size: 最小块字符数
            separator: 分隔符
        """
        self.chunk_size = chunk_size or settings.chunk_size
        self.chunk_overlap = chunk_overlap or settings.chunk_overlap
        self.min_chunk_size = min_chunk_size or settings.chunk_min_size
        self.separator = separator
        
        # 验证参数
        if self.chunk_overlap >= self.chunk_size:
            logger.warning(f"chunk_overlap ({self.chunk_overlap}) >= chunk_size ({self.chunk_size})，已调整为 chunk_size/4")
            self.chunk_overlap = self.chunk_size // 4
    
    def split_text(self, text: str) -> List[str]:
        """
        切分文本
        
        Args:
            text: 待切分文本
            
        Returns:
            文本块列表
        """
        if not text or not text.strip():
            logger.warning("输入文本为空")
            return []
        
        # 预处理：规范化空白字符
        text = self._normalize_whitespace(text)
        
        # 使用分隔符分割
        chunks = self._split_by_separator(text)
        
        # 进一步切分过长的块
        final_chunks = []
        for chunk in chunks:
            if len(chunk) <= self.chunk_size:
                if len(chunk) >= self.min_chunk_size:
                    final_chunks.append(chunk)
            else:
                # 切分过长的块
                sub_chunks = self._split_long_chunk(chunk)
                final_chunks.extend(sub_chunks)
        
        # 过滤空块和过短块
        final_chunks = [
            chunk.strip() for chunk in final_chunks 
            if chunk.strip() and len(chunk.strip()) >= self.min_chunk_size
        ]
        
        logger.debug(f"文本切分完成: {len(final_chunks)} 个块")
        return final_chunks
    
    def _normalize_whitespace(self, text: str) -> str:
        """
        规范化空白字符
        
        Args:
            text: 原始文本
            
        Returns:
            规范化后的文本
        """
        # 将多个连续空白字符替换为单个空格
        text = re.sub(r'[ \t]+', ' ', text)
        # 将多个连续换行替换为两个换行
        text = re.sub(r'\n{3,}', '\n\n', text)
        # 去除首尾空白
        return text.strip()
    
    def _split_by_separator(self, text: str) -> List[str]:
        """
        使用分隔符分割文本
        
        Args:
            text: 待分割文本
            
        Returns:
            分割后的文本块列表
        """
        # 按段落分割（双换行）
        parts = text.split(self.separator)
        
        chunks = []
        current_chunk = ""
        
        for part in parts:
            part = part.strip()
            if not part:
                continue
            
            # 如果当前块加上这个部分不超过限制
            if len(current_chunk) + len(self.separator) + len(part) <= self.chunk_size:
                if current_chunk:
                    current_chunk += self.separator + part
                else:
                    current_chunk = part
            else:
                # 当前块已满，保存并开始新块
                if current_chunk:
                    chunks.append(current_chunk)
                
                # 如果单个部分就超过限制，需要进一步切分
                if len(part) > self.chunk_size:
                    # 先保存当前块
                    if current_chunk:
                        chunks.append(current_chunk)
                    # 切分长部分
                    chunks.extend(self._split_long_chunk(part))
                    current_chunk = ""
                else:
                    current_chunk = part
        
        # 保存最后一个块
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks
    
    def _split_long_chunk(self, chunk: str) -> List[str]:
        """
        切分过长的文本块
        
        Args:
            chunk: 过长的文本块
            
        Returns:
            切分后的子块列表
        """
        sub_chunks = []
        
        # 尝试按句子分割
        sentences = self._split_by_sentence(chunk)
        
        current_sub = ""
        for sentence in sentences:
            if len(current_sub) + len(sentence) <= self.chunk_size:
                current_sub += sentence if not current_sub else " " + sentence
            else:
                if current_sub:
                    sub_chunks.append(current_sub)
                
                # 如果单个句子就超过限制，按字符切分
                if len(sentence) > self.chunk_size:
                    sub_chunks.extend(self._split_by_chars(sentence))
                    current_sub = ""
                else:
                    current_sub = sentence
        
        if current_sub:
            sub_chunks.append(current_sub)
        
        return sub_chunks
    
    def _split_by_sentence(self, text: str) -> List[str]:
        """
        按句子分割文本
        
        Args:
            text: 待分割文本
            
        Returns:
            句子列表
        """
        # 中英文句子分割正则
        # 匹配常见句子结束符
        sentence_endings = r'[。！？.!?；;]'
        
        parts = re.split(sentence_endings, text)
        
        sentences = []
        for i, part in enumerate(parts):
            if i < len(parts) - 1:
                # 添加句子结束符
                part += text[text.find(part) + len(part)]
            if part.strip():
                sentences.append(part.strip())
        
        return sentences if sentences else [text]
    
    def _split_by_chars(self, text: str) -> List[str]:
        """
        按字符数切分文本（最后手段）
        
        Args:
            text: 待切分文本
            
        Returns:
            切分后的文本块列表
        """
        chunks = []
        
        for i in range(0, len(text), self.chunk_size - self.chunk_overlap):
            chunk = text[i:i + self.chunk_size]
            if len(chunk) >= self.min_chunk_size:
                chunks.append(chunk)
        
        return chunks
    
    def split_documents(
        self,
        documents: List[Tuple[str, dict]]
    ) -> List[Tuple[str, dict]]:
        """
        批量切分文档
        
        Args:
            documents: (文本, 元数据) 元组列表
            
        Returns:
            (文本块, 元数据) 元组列表
        """
        result = []
        
        for doc_text, metadata in documents:
            chunks = self.split_text(doc_text)
            
            for idx, chunk in enumerate(chunks):
                chunk_metadata = metadata.copy()
                chunk_metadata["chunk_index"] = idx
                chunk_metadata["char_count"] = len(chunk)
                result.append((chunk, chunk_metadata))
        
        logger.info(f"批量切分完成: {len(documents)} 个文档 -> {len(result)} 个块")
        return result


# 创建全局文本切分器实例
text_splitter = TextSplitter()


def get_text_splitter() -> TextSplitter:
    """获取文本切分器实例"""
    return text_splitter
