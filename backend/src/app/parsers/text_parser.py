# -*- coding: utf-8 -*-
"""
文本解析器

本模块实现纯文本文件的解析，支持TXT、MD、HTML等格式。
"""

from typing import List

from app.parsers.base import (
    BaseParser,
    DocumentElementModel,
    ElementType,
)


class TextParser(BaseParser):
    """
    文本解析器

    支持TXT、MD（Markdown）、HTML等纯文本格式的解析。
    """

    def __init__(self):
        """初始化文本解析器"""
        super().__init__()
        self.supported_extensions = ["txt", "md", "markdown", "html", "htm"]

    def parse(
        self,
        file_path: str,
        version_id: int,
        document_id: int
    ) -> List[DocumentElementModel]:
        """
        解析文本文件

        Args:
            file_path: 文件路径
            version_id: 版本ID
            document_id: 文档ID

        Returns:
            解析后的元素列表
        """
        import os
        elements = []
        ext = os.path.splitext(file_path)[1].lower().lstrip(".")

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            if ext in ["md", "markdown"]:
                elements = self._parse_markdown(content, version_id, document_id)
            elif ext in ["html", "htm"]:
                elements = self._parse_html(content, version_id, document_id)
            else:
                elements = self._parse_plain_text(content, version_id, document_id)

        except Exception as e:
            import logging
            logger = logging.getLogger("rag.parser")
            logger.error(f"文本文件解析失败: {file_path}, 错误: {str(e)}")

        return elements

    def _parse_plain_text(
        self,
        content: str,
        version_id: int,
        document_id: int
    ) -> List[DocumentElementModel]:
        """
        解析纯文本

        Args:
            content: 文本内容
            version_id: 版本ID
            document_id: 文档ID

        Returns:
            元素列表
        """
        lines = content.split("\n")
        elements = []

        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue

            elements.append(DocumentElementModel(
                element_id=self._generate_element_id(),
                document_id=document_id,
                version_id=version_id,
                page_no=1,
                element_type=ElementType.PARAGRAPH,
                content=line,
                enhanced_content=line,
                reading_order=i,
                confidence=0.95
            ))

        return elements

    def _parse_markdown(
        self,
        content: str,
        version_id: int,
        document_id: int
    ) -> List[DocumentElementModel]:
        """
        解析Markdown

        Args:
            content: Markdown内容
            version_id: 版本ID
            document_id: 文档ID

        Returns:
            元素列表
        """
        elements = []
        title_path: List[str] = []
        reading_order = 0
        lines = content.split("\n")

        i = 0
        while i < len(lines):
            line = lines[i].strip()

            if not line:
                i += 1
                continue

            # 检测标题
            if line.startswith("#"):
                # 解析标题级别
                level = 0
                for char in line:
                    if char == "#":
                        level += 1
                    else:
                        break

                title_text = line.lstrip("#").strip()

                # 更新标题路径
                title_path = title_path[:level - 1] + [title_text]

                elements.append(DocumentElementModel(
                    element_id=self._generate_element_id(),
                    document_id=document_id,
                    version_id=version_id,
                    page_no=1,
                    element_type=ElementType.TITLE,
                    content=title_text,
                    enhanced_content=title_text,
                    reading_order=reading_order,
                    title_level=level,
                    title_path=" > ".join(title_path),
                    confidence=0.95
                ))
                reading_order += 1

            # 检测代码块
            elif line.startswith("```"):
                code_lines = []
                i += 1
                while i < len(lines) and not lines[i].startswith("```"):
                    code_lines.append(lines[i])
                    i += 1

                if code_lines:
                    code_content = "\n".join(code_lines)
                    elements.append(DocumentElementModel(
                        element_id=self._generate_element_id(),
                        document_id=document_id,
                        version_id=version_id,
                        page_no=1,
                        element_type=ElementType.CODE,
                        content=code_content,
                        enhanced_content=code_content,
                        reading_order=reading_order,
                        title_path=" > ".join(title_path) if title_path else "",
                        confidence=0.95
                    ))
                    reading_order += 1

            # 检测列表
            elif line.startswith(("*", "-", "+")) or line[0].isdigit() and "." in line[:3]:
                list_text = line.lstrip("*-+0123456789. ").strip()

                elements.append(DocumentElementModel(
                    element_id=self._generate_element_id(),
                    document_id=document_id,
                    version_id=version_id,
                    page_no=1,
                    element_type=ElementType.LIST,
                    content=list_text,
                    enhanced_content=list_text,
                    reading_order=reading_order,
                    title_path=" > ".join(title_path) if title_path else "",
                    confidence=0.95
                ))
                reading_order += 1

            # 普通段落
            else:
                elements.append(DocumentElementModel(
                    element_id=self._generate_element_id(),
                    document_id=document_id,
                    version_id=version_id,
                    page_no=1,
                    element_type=ElementType.PARAGRAPH,
                    content=line,
                    enhanced_content=line,
                    reading_order=reading_order,
                    title_path=" > ".join(title_path) if title_path else "",
                    confidence=0.95
                ))
                reading_order += 1

            i += 1

        return elements

    def _parse_html(
        self,
        content: str,
        version_id: int,
        document_id: int
    ) -> List[DocumentElementModel]:
        """
        解析HTML

        Args:
            content: HTML内容
            version_id: 版本ID
            document_id: 文档ID

        Returns:
            元素列表
        """
        elements = []
        reading_order = 0

        try:
            from bs4 import BeautifulSoup

            soup = BeautifulSoup(content, "html.parser")

            # 提取标题
            for i, tag in enumerate(soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"])):
                level = int(tag.name[1])
                text = tag.get_text().strip()

                if text:
                    elements.append(DocumentElementModel(
                        element_id=self._generate_element_id(),
                        document_id=document_id,
                        version_id=version_id,
                        page_no=1,
                        element_type=ElementType.TITLE,
                        content=text,
                        enhanced_content=text,
                        reading_order=reading_order,
                        title_level=level,
                        confidence=0.95
                    ))
                    reading_order += 1

            # 提取段落
            for tag in soup.find_all("p"):
                text = tag.get_text().strip()

                if text:
                    elements.append(DocumentElementModel(
                        element_id=self._generate_element_id(),
                        document_id=document_id,
                        version_id=version_id,
                        page_no=1,
                        element_type=ElementType.PARAGRAPH,
                        content=text,
                        enhanced_content=text,
                        reading_order=reading_order,
                        confidence=0.95
                    ))
                    reading_order += 1

            # 提取列表
            for tag in soup.find_all(["ul", "ol"]):
                for li in tag.find_all("li"):
                    text = li.get_text().strip()

                    if text:
                        elements.append(DocumentElementModel(
                            element_id=self._generate_element_id(),
                            document_id=document_id,
                            version_id=version_id,
                            page_no=1,
                            element_type=ElementType.LIST,
                            content=text,
                            enhanced_content=text,
                            reading_order=reading_order,
                            confidence=0.95
                        ))
                        reading_order += 1

        except ImportError:
            # BeautifulSoup未安装，使用纯文本解析
            import re
            # 移除HTML标签
            text = re.sub(r"<[^>]+>", "", content)
            return self._parse_plain_text(text, version_id, document_id)
        except Exception as e:
            import logging
            logger = logging.getLogger("rag.parser")
            logger.error(f"HTML解析失败: {str(e)}")

        return elements
