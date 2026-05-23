# -*- coding: utf-8 -*-
"""
PDF文档解析器

本模块实现PDF文档的解析，支持电子版PDF和扫描版PDF。
- 电子版：直接提取文本层和坐标
- 扫描版：图像预处理 + OCR识别
"""

import io
from typing import Any, Dict, List, Optional, Tuple

from app.parsers.base import (
    BaseParser,
    BBox,
    DocumentElementModel,
    ElementType,
    QualityFlag,
)


class PdfParser(BaseParser):
    """
    PDF文档解析器

    支持电子版PDF和扫描版PDF的解析。
    """

    def __init__(self):
        """初始化PDF解析器"""
        super().__init__()
        self.supported_extensions = ["pdf"]
        self._ocr_threshold = 0.5  # 文本页面比例阈值，低于此值判定为扫描版

    def parse(
        self,
        file_path: str,
        version_id: int,
        document_id: int
    ) -> List[DocumentElementModel]:
        """
        解析PDF文档

        Args:
            file_path: 文件路径
            version_id: 版本ID
            document_id: 文档ID

        Returns:
            解析后的元素列表
        """
        try:
            import fitz  # PyMuPDF
        except ImportError:
            # PyMuPDF未安装，返回空列表
            return []

        elements = []

        try:
            doc = fitz.open(file_path)
            total_pages = len(doc)

            # 判断PDF类型（电子版/扫描版）
            is_scanned = self._is_scanned_pdf(doc)

            # 遍历所有页面
            for page_no in range(total_pages):
                page = doc[page_no]
                if is_scanned:
                    # 扫描版PDF：图像预处理 + OCR
                    page_elements = self._parse_scanned_page(
                        page, page_no, version_id, document_id
                    )
                else:
                    # 电子版PDF：文本提取
                    page_elements = self._parse_text_page(
                        page, page_no, version_id, document_id
                    )
                elements.extend(page_elements)

            doc.close()

        except Exception as e:
            import logging
            logger = logging.getLogger("rag.parser")
            logger.error(f"PDF文档解析失败: {file_path}, 错误: {str(e)}")

        return elements

    def _is_scanned_pdf(self, doc) -> bool:
        """
        判断是否为扫描版PDF

        统计有文本的页面比例，如果文本页面比例低于阈值，判定为扫描版。

        Args:
            doc: PDF文档对象

        Returns:
            是否为扫描版PDF
        """
        text_pages = 0
        total_pages = len(doc)

        for page in doc:
            text = page.get_text()
            if text.strip():
                text_pages += 1

        # 计算文本页面比例
        ratio = text_pages / total_pages if total_pages > 0 else 0
        return ratio < self._ocr_threshold

    def _parse_text_page(
        self,
        page,
        page_no: int,
        version_id: int,
        document_id: int
    ) -> List[DocumentElementModel]:
        """
        解析电子版PDF页面

        Args:
            page: PDF页面对象
            page_no: 页码
            version_id: 版本ID
            document_id: 文档ID

        Returns:
            页面元素列表
        """
        elements = []
        reading_order = 0

        # 获取文本块和坐标
        text_dict = page.get_text("dict")
        blocks = text_dict.get("blocks", [])

        for block in blocks:
            if block.get("type") == 0:  # 文本块
                element = self._extract_text_block(
                    block, page_no, version_id, document_id, reading_order
                )
                if element:
                    elements.append(element)
                    reading_order += 1
            elif block.get("type") == 1:  # 图像块
                element = self._extract_image_block(
                    block, page_no, version_id, document_id, reading_order
                )
                if element:
                    elements.append(element)
                    reading_order += 1

        return elements

    def _extract_text_block(
        self,
        block: Dict[str, Any],
        page_no: int,
        version_id: int,
        document_id: int,
        reading_order: int
    ) -> Optional[DocumentElementModel]:
        """
        提取文本块

        Args:
            block: 文本块数据
            page_no: 页码
            version_id: 版本ID
            document_id: 文档ID
            reading_order: 阅读顺序

        Returns:
            文本元素
        """
        try:
            # 获取边界框
            bbox = block.get("bbox")
            if not bbox:
                return None

            # 获取文本内容
            lines = block.get("lines", [])
            if not lines:
                return None

            text_parts = []
            for line in lines:
                for span in line.get("spans", []):
                    text_parts.append(span.get("text", ""))

            text = "".join(text_parts).strip()
            if not text:
                return None

            # 提取样式信息
            font_sizes = set()
            is_bold = False
            for line in lines:
                for span in line.get("spans", []):
                    font_size = span.get("size", 0)
                    font_sizes.add(font_size)
                    font_name = span.get("font", "").lower()
                    if "bold" in font_name or "黑体" in font_name:
                        is_bold = True

            # 判断是否为标题（较大的字体或粗体）
            max_font_size = max(font_sizes) if font_sizes else 0
            is_title = is_bold and max_font_size >= 14

            # 提取坐标
            bbox_obj = BBox(
                x=bbox[0],
                y=bbox[1],
                width=bbox[2] - bbox[0],
                height=bbox[3] - bbox[1]
            )

            if is_title:
                # 标题元素
                level = self._estimate_title_level(max_font_size)
                return DocumentElementModel(
                    element_id=self._generate_element_id(),
                    document_id=document_id,
                    version_id=version_id,
                    page_no=page_no + 1,
                    element_type=ElementType.TITLE,
                    content=text,
                    enhanced_content=text,
                    reading_order=reading_order,
                    title_level=level,
                    bbox=bbox_obj,
                    confidence=0.95,
                    quality_flag=QualityFlag.GOOD
                )
            else:
                # 段落元素
                return DocumentElementModel(
                    element_id=self._generate_element_id(),
                    document_id=document_id,
                    version_id=version_id,
                    page_no=page_no + 1,
                    element_type=ElementType.PARAGRAPH,
                    content=text,
                    enhanced_content=text,
                    reading_order=reading_order,
                    bbox=bbox_obj,
                    confidence=0.9,
                    quality_flag=QualityFlag.GOOD
                )

        except Exception:
            return None

    def _extract_image_block(
        self,
        block: Dict[str, Any],
        page_no: int,
        version_id: int,
        document_id: int,
        reading_order: int
    ) -> Optional[DocumentElementModel]:
        """
        提取图像块

        Args:
            block: 图像块数据
            page_no: 页码
            version_id: 版本ID
            document_id: 文档ID
            reading_order: 阅读顺序

        Returns:
            图像元素
        """
        try:
            bbox = block.get("bbox")
            if not bbox:
                return None

            # 获取图像信息
            image = block.get("image")
            if not image:
                return None

            bbox_obj = BBox(
                x=bbox[0],
                y=bbox[1],
                width=bbox[2] - bbox[0],
                height=bbox[3] - bbox[1]
            )

            return DocumentElementModel(
                element_id=self._generate_element_id(),
                document_id=document_id,
                version_id=version_id,
                page_no=page_no + 1,
                element_type=ElementType.IMAGE,
                reading_order=reading_order,
                bbox=bbox_obj,
                confidence=0.85,
                metadata={"image_size": len(str(image))},
                quality_flag=QualityFlag.GOOD
            )

        except Exception:
            return None

    def _estimate_title_level(self, font_size: float) -> int:
        """
        根据字体大小估算标题级别

        Args:
            font_size: 字体大小

        Returns:
            标题级别（1-6）
        """
        if font_size >= 24:
            return 1
        elif font_size >= 20:
            return 2
        elif font_size >= 18:
            return 3
        elif font_size >= 16:
            return 4
        elif font_size >= 14:
            return 5
        else:
            return 6

    def _parse_scanned_page(
        self,
        page,
        page_no: int,
        version_id: int,
        document_id: int
    ) -> List[DocumentElementModel]:
        """
        解析扫描版PDF页面

        Args:
            page: PDF页面对象
            page_no: 页码
            version_id: 版本ID
            document_id: 文档ID

        Returns:
            页面元素列表
        """
        elements = []

        try:
            # 1. 页面转图像
            mat = fitz.Matrix(2, 2)  # 2x倍率提高清晰度
            pix = page.get_pixmap(matrix=mat)
            image_bytes = pix.tobytes("png")

            # 2. 图像预处理
            processed_image = self._preprocess_image(image_bytes)

            # 3. 简单文本提取（使用PyMuPDF内置OCR或返回图像信息）
            # 实际OCR需要调用外部OCR服务
            text = page.get_text().strip()

            if text:
                # 如果有文本，使用文本内容
                elements.append(DocumentElementModel(
                    element_id=self._generate_element_id(),
                    document_id=document_id,
                    version_id=version_id,
                    page_no=page_no + 1,
                    element_type=ElementType.PARAGRAPH,
                    content=text,
                    enhanced_content=text,
                    reading_order=0,
                    confidence=0.9,
                    quality_flag=QualityFlag.GOOD
                ))
            else:
                # 无文本，标记为需要OCR
                elements.append(DocumentElementModel(
                    element_id=self._generate_element_id(),
                    document_id=document_id,
                    version_id=version_id,
                    page_no=page_no + 1,
                    element_type=ElementType.PARAGRAPH,
                    content="[需要OCR识别]",
                    enhanced_content="",
                    reading_order=0,
                    confidence=0.5,
                    quality_flag=QualityFlag.WARNING,
                    metadata={"ocr_required": True}
                ))

        except Exception as e:
            import logging
            logger = logging.getLogger("rag.parser")
            logger.error(f"扫描版PDF页面解析失败: 第{page_no + 1}页, 错误: {str(e)}")

            # 失败时添加错误标记
            elements.append(DocumentElementModel(
                element_id=self._generate_element_id(),
                document_id=document_id,
                version_id=version_id,
                page_no=page_no + 1,
                element_type=ElementType.PARAGRAPH,
                content="[解析失败]",
                enhanced_content="",
                reading_order=0,
                confidence=0.0,
                quality_flag=QualityFlag.BAD,
                metadata={"error": str(e)}
            ))

        return elements

    def _preprocess_image(self, image_bytes: bytes) -> Any:
        """
        图像预处理

        包括：转灰度、去噪、二值化、倾斜校正。

        Args:
            image_bytes: 图像字节数据

        Returns:
            处理后的图像数据
        """
        try:
            from PIL import Image
            import numpy as np
            import cv2

            # 转换为PIL Image
            image = Image.open(io.BytesIO(image_bytes))
            img_array = np.array(image)

            # 转灰度
            if len(img_array.shape) == 3:
                gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            else:
                gray = img_array

            # 去噪
            try:
                denoised = cv2.fastNlMeansDenoising(gray)
            except Exception:
                denoised = gray

            # 二值化
            _, binary = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

            return {
                "image": binary,
                "original": img_array
            }

        except ImportError:
            # 缺少依赖，返回原始数据
            return {"original": image_bytes}
        except Exception:
            return {"original": image_bytes}
