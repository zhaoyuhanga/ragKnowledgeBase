# -*- coding: utf-8 -*-
"""
解析器基类

本模块定义解析器基类和统一中间结构 DocumentElement。
"""

import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


# ================================================
# 枚举定义
# ================================================

class ElementType(str, Enum):
    """元素类型枚举"""
    TITLE = "title"           # 标题
    PARAGRAPH = "paragraph"   # 段落
    TABLE = "table"         # 表格
    IMAGE = "image"          # 图片
    CHART = "chart"          # 图表
    LIST = "list"           # 列表
    CODE = "code"           # 代码块
    HEADER = "header"        # 页眉
    FOOTER = "footer"      # 页脚


class QualityFlag(str, Enum):
    """质量标记枚举"""
    GOOD = "good"           # 良好
    WARNING = "warning"     # 警告
    BAD = "bad"             # 不良


# ================================================
# 数据模型定义
# ================================================

class BBox(BaseModel):
    """边界框模型"""
    x: float = 0.0          # 左上角X坐标
    y: float = 0.0          # 左上角Y坐标
    width: float = 0.0      # 宽度
    height: float = 0.0    # 高度

    def to_dict(self) -> Dict[str, float]:
        """转换为字典"""
        return self.model_dump()


class TableStructure(BaseModel):
    """表格结构模型"""
    headers: List[List[str]] = field(default_factory=list)  # 表头行列表
    rows: List[List[str]] = field(default_factory=list)     # 数据行列表
    merged_cells: List[Dict[str, Any]] = field(default_factory=list)  # 合并单元格
    row_count: int = 0      # 总行数
    col_count: int = 0       # 总列数
    caption: Optional[str] = None  # 表题

    def to_text(self) -> str:
        """转换为文本格式"""
        lines = []
        if self.headers:
            for row in self.headers:
                lines.append(" | ".join(row))
        for row in self.rows:
            lines.append(" | ".join(str(cell) for cell in row))
        return "\n".join(lines)


class ImageDescription(BaseModel):
    """图片描述模型"""
    description: str = ""    # 场景描述
    chart_type: Optional[str] = None  # 图表类型：折线图、柱状图、饼图等
    chart_data_summary: Optional[str] = None  # 图表数据摘要
    alt_text: Optional[str] = None  # 替代文本
    semantic_tags: List[str] = field(default_factory=list)  # 语义标签
    confidence: float = 0.9  # 置信度

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return self.model_dump()


@dataclass
class DocumentElementModel:
    """
    文档元素数据类

    统一中间结构，表示解析后的文档元素。
    """
    # 元素唯一ID
    element_id: str
    # 文档ID
    document_id: int
    # 版本ID
    version_id: int
    # 页码
    page_no: Optional[int] = None
    # 起始页（跨页元素）
    page_start: Optional[int] = None
    # 结束页
    page_end: Optional[int] = None
    # 元素类型
    element_type: ElementType = ElementType.PARAGRAPH
    # 原始内容
    content: str = ""
    # 增强内容
    enhanced_content: str = ""
    # 阅读顺序
    reading_order: int = 0
    # 标题层级（1-6）
    title_level: Optional[int] = None
    # 标题路径
    title_path: Optional[str] = None
    # 父级路径
    parent_path: Optional[str] = None
    # 边界框
    bbox: Optional[BBox] = None
    # 置信度
    confidence: float = 1.0
    # 是否跨页合并
    is_merged: bool = False
    # 表格结构
    table_structure: Optional[TableStructure] = None
    # 图片描述
    image_description: Optional[ImageDescription] = None
    # 元数据
    metadata: Dict[str, Any] = field(default_factory=dict)
    # 质量标记
    quality_flag: QualityFlag = QualityFlag.GOOD

    def generate_id(self) -> str:
        """生成元素唯一ID"""
        if not self.element_id:
            self.element_id = str(uuid.uuid4())
        return self.element_id

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = {
            "element_id": self.element_id,
            "document_id": self.document_id,
            "version_id": self.version_id,
            "page_no": self.page_no,
            "page_start": self.page_start,
            "page_end": self.page_end,
            "element_type": self.element_type.value if isinstance(self.element_type, ElementType) else self.element_type,
            "content": self.content,
            "enhanced_content": self.enhanced_content,
            "reading_order": self.reading_order,
            "title_level": self.title_level,
            "title_path": self.title_path,
            "parent_path": self.parent_path,
            "confidence": self.confidence,
            "is_merged": self.is_merged,
            "quality_flag": self.quality_flag.value if isinstance(self.quality_flag, QualityFlag) else self.quality_flag,
        }

        if self.bbox:
            result["bbox"] = self.bbox.to_dict()
        if self.table_structure:
            result["table_structure"] = self.table_structure.model_dump() if hasattr(self.table_structure, 'model_dump') else {}
        if self.image_description:
            result["image_description"] = self.image_description.to_dict()
        if self.metadata:
            result["metadata"] = self.metadata

        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DocumentElementModel":
        """从字典创建"""
        element_type = data.get("element_type")
        if isinstance(element_type, str):
            element_type = ElementType(element_type)

        quality_flag = data.get("quality_flag", "good")
        if isinstance(quality_flag, str):
            quality_flag = QualityFlag(quality_flag)

        bbox = data.get("bbox")
        if bbox:
            bbox = BBox(**bbox)

        table_structure = data.get("table_structure")
        if table_structure:
            table_structure = TableStructure(**table_structure)

        image_description = data.get("image_description")
        if image_description:
            image_description = ImageDescription(**image_description)

        return cls(
            element_id=data.get("element_id", str(uuid.uuid4())),
            document_id=data["document_id"],
            version_id=data["version_id"],
            page_no=data.get("page_no"),
            page_start=data.get("page_start"),
            page_end=data.get("page_end"),
            element_type=element_type,
            content=data.get("content", ""),
            enhanced_content=data.get("enhanced_content", ""),
            reading_order=data.get("reading_order", 0),
            title_level=data.get("title_level"),
            title_path=data.get("title_path"),
            parent_path=data.get("parent_path"),
            bbox=bbox,
            confidence=data.get("confidence", 1.0),
            is_merged=data.get("is_merged", False),
            table_structure=table_structure,
            image_description=image_description,
            metadata=data.get("metadata", {}),
            quality_flag=quality_flag
        )


# ================================================
# 解析器基类
# ================================================

class BaseParser(ABC):
    """
    解析器基类

    所有文档解析器必须继承此类并实现 parse 方法。
    支持插件化扩展，通过 register_parser 注册新的解析器。
    """

    def __init__(self):
        """初始化解析器"""
        self.supported_extensions: List[str] = []

    @abstractmethod
    def parse(self, file_path: str, version_id: int, document_id: int) -> List[DocumentElementModel]:
        """
        解析文档

        Args:
            file_path: 文件路径
            version_id: 版本ID
            document_id: 文档ID

        Returns:
            解析后的元素列表
        """
        pass

    def can_parse(self, file_path: str) -> bool:
        """
        检查此解析器是否能解析指定文件

        Args:
            file_path: 文件路径

        Returns:
            是否能解析
        """
        import os
        ext = os.path.splitext(file_path)[1].lower().lstrip(".")
        return ext in self.supported_extensions

    def _generate_element_id(self) -> str:
        """生成元素唯一ID"""
        return str(uuid.uuid4())

    def _create_title_element(
        self,
        text: str,
        level: int,
        document_id: int,
        version_id: int,
        reading_order: int,
        title_path: str = "",
        page_no: Optional[int] = 1
    ) -> DocumentElementModel:
        """
        创建标题元素

        Args:
            text: 标题文本
            level: 标题级别
            document_id: 文档ID
            version_id: 版本ID
            reading_order: 阅读顺序
            title_path: 标题路径
            page_no: 页码

        Returns:
            标题元素
        """
        return DocumentElementModel(
            element_id=self._generate_element_id(),
            document_id=document_id,
            version_id=version_id,
            page_no=page_no,
            element_type=ElementType.TITLE,
            content=text,
            enhanced_content=text,
            reading_order=reading_order,
            title_level=level,
            title_path=title_path,
            confidence=0.95
        )

    def _create_paragraph_element(
        self,
        text: str,
        document_id: int,
        version_id: int,
        reading_order: int,
        title_path: str = "",
        bbox: Optional[BBox] = None,
        page_no: Optional[int] = 1
    ) -> DocumentElementModel:
        """
        创建段落元素

        Args:
            text: 段落文本
            document_id: 文档ID
            version_id: 版本ID
            reading_order: 阅读顺序
            title_path: 标题路径
            bbox: 边界框
            page_no: 页码

        Returns:
            段落元素
        """
        return DocumentElementModel(
            element_id=self._generate_element_id(),
            document_id=document_id,
            version_id=version_id,
            page_no=page_no,
            element_type=ElementType.PARAGRAPH,
            content=text,
            enhanced_content=text,
            reading_order=reading_order,
            title_path=title_path,
            bbox=bbox,
            confidence=0.9
        )

    def _create_table_element(
        self,
        table_structure: TableStructure,
        document_id: int,
        version_id: int,
        reading_order: int,
        page_no: Optional[int] = None,
        caption: Optional[str] = None
    ) -> DocumentElementModel:
        """
        创建表格元素

        Args:
            table_structure: 表格结构
            document_id: 文档ID
            version_id: 版本ID
            reading_order: 阅读顺序
            page_no: 页码
            caption: 表题

        Returns:
            表格元素
        """
        if caption:
            table_structure.caption = caption

        return DocumentElementModel(
            element_id=self._generate_element_id(),
            document_id=document_id,
            version_id=version_id,
            page_no=page_no,
            element_type=ElementType.TABLE,
            content=table_structure.to_text(),
            reading_order=reading_order,
            table_structure=table_structure,
            confidence=0.95
        )

    def _create_image_element(
        self,
        document_id: int,
        version_id: int,
        reading_order: int,
        page_no: Optional[int] = None,
        image_description: Optional[ImageDescription] = None,
        bbox: Optional[BBox] = None
    ) -> DocumentElementModel:
        """
        创建图片元素

        Args:
            document_id: 文档ID
            version_id: 版本ID
            reading_order: 阅读顺序
            page_no: 页码
            image_description: 图片描述
            bbox: 边界框

        Returns:
            图片元素
        """
        return DocumentElementModel(
            element_id=self._generate_element_id(),
            document_id=document_id,
            version_id=version_id,
            page_no=page_no,
            element_type=ElementType.IMAGE,
            enhanced_content=image_description.description if image_description else "",
            reading_order=reading_order,
            image_description=image_description,
            bbox=bbox,
            confidence=image_description.confidence if image_description else 0.85
        )


# ================================================
# 解析器注册表
# ================================================

class ParserRegistry:
    """
    解析器注册表

    管理所有解析器的注册和获取。
    """

    def __init__(self):
        """初始化注册表"""
        self._parsers: Dict[str, BaseParser] = {}

    def register(self, extension: str, parser: BaseParser) -> None:
        """
        注册解析器

        Args:
            extension: 文件扩展名（如 "pdf", "docx"）
            parser: 解析器实例
        """
        self._parsers[extension.lower()] = parser

    def get_parser(self, file_path: str) -> Optional[BaseParser]:
        """
        获取指定文件的解析器

        Args:
            file_path: 文件路径

        Returns:
            解析器实例，如果没有则返回 None
        """
        import os
        ext = os.path.splitext(file_path)[1].lower().lstrip(".")
        return self._parsers.get(ext)

    def list_parsers(self) -> List[str]:
        """
        列出所有注册的解析器

        Returns:
            已注册的文件扩展名列表
        """
        return list(self._parsers.keys())


# 全局解析器注册表
_parser_registry = ParserRegistry()


def get_parser_registry() -> ParserRegistry:
    """获取解析器注册表"""
    return _parser_registry


def register_parser(extension: str, parser: BaseParser) -> None:
    """
    注册解析器的便捷函数

    Args:
        extension: 文件扩展名
        parser: 解析器实例
    """
    _parser_registry.register(extension, parser)
