# -*- coding: utf-8 -*-
"""
解析器包

本模块包含所有文档解析器。
"""

from app.parsers.base import (
    BaseParser,
    ParserRegistry,
    ElementType,
    QualityFlag,
    DocumentElementModel,
    BBox,
    TableStructure,
    ImageDescription,
    get_parser_registry,
    register_parser
)
from app.parsers.word_parser import WordParser
from app.parsers.pdf_parser import PdfParser
from app.parsers.image_parser import ImageParser
from app.parsers.table_parser import TableParser
from app.parsers.text_parser import TextParser
from app.parsers.layout_analyzer import LayoutAnalyzer

__all__ = [
    "BaseParser",
    "ParserRegistry",
    "ElementType",
    "QualityFlag",
    "DocumentElementModel",
    "BBox",
    "TableStructure",
    "ImageDescription",
    "get_parser_registry",
    "register_parser",
    "WordParser",
    "PdfParser",
    "ImageParser",
    "TableParser",
    "TextParser",
    "LayoutAnalyzer"
]
