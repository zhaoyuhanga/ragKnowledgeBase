# -*- coding: utf-8 -*-
"""
图片解析器

本模块实现图片文档的解析，支持OCR文字识别和多模态描述生成。
"""

import io
from typing import Any, Dict, List, Optional

from app.parsers.base import (
    BaseParser,
    BBox,
    DocumentElementModel,
    ElementType,
    ImageDescription,
    QualityFlag,
)


class ImageParser(BaseParser):
    """
    图片解析器

    支持PNG、JPG、JPEG等图片格式的解析和OCR识别。
    集成视觉模型生成图片描述，包括图表识别和数据提取。
    """

    def __init__(self):
        """初始化图片解析器"""
        super().__init__()
        self.supported_extensions = ["png", "jpg", "jpeg", "gif", "bmp", "tiff"]
        self._ocr_enabled = True  # 是否启用OCR
        self._vision_client = None  # 视觉模型客户端（懒加载）

    def _get_vision_client(self):
        """获取视觉模型客户端（懒加载）"""
        if self._vision_client is None:
            from app.services.vision_client import get_vision_client
            self._vision_client = get_vision_client()
        return self._vision_client

    def parse(
        self,
        file_path: str,
        version_id: int,
        document_id: int
    ) -> List[DocumentElementModel]:
        """
        解析图片文档

        Args:
            file_path: 文件路径
            version_id: 版本ID
            document_id: 文档ID

        Returns:
            解析后的元素列表
        """
        elements = []

        try:
            # 1. 读取图片
            with open(file_path, "rb") as f:
                image_bytes = f.read()

            # 2. 图像预处理
            processed_image = self._preprocess_image(image_bytes)

            # 3. OCR文字识别
            ocr_text = ""
            ocr_confidence = 0.0
            if self._ocr_enabled:
                ocr_text, ocr_confidence = self._perform_ocr(processed_image)

            # 4. 多模态描述生成
            image_description = self._generate_description(image_bytes)

            # 5. 创建元素
            element = DocumentElementModel(
                element_id=self._generate_element_id(),
                document_id=document_id,
                version_id=version_id,
                page_no=1,
                element_type=ElementType.IMAGE,
                content=ocr_text,
                enhanced_content=image_description.description if image_description else "",
                reading_order=0,
                image_description=image_description,
                confidence=image_description.confidence if image_description else 0.85,
                metadata={
                    "image_size": len(image_bytes),
                    "ocr_confidence": ocr_confidence,
                    "image_format": file_path.split(".")[-1].lower()
                },
                quality_flag=self._get_quality_flag(ocr_confidence)
            )
            elements.append(element)

        except Exception as e:
            import logging
            logger = logging.getLogger("rag.parser")
            logger.error(f"图片解析失败: {file_path}, 错误: {str(e)}")

        return elements

    def _preprocess_image(self, image_bytes: bytes) -> Dict[str, Any]:
        """
        图像预处理

        包括：方向检测与矫正、去噪、增强等。

        Args:
            image_bytes: 图像字节数据

        Returns:
            处理后的图像数据
        """
        result = {"original": image_bytes}

        try:
            from PIL import Image
            import numpy as np
            import cv2

            # 读取图像
            image = Image.open(io.BytesIO(image_bytes))
            img_array = np.array(image)

            # 方向检测与矫正
            corrected = self._correct_orientation(img_array)
            result["corrected"] = corrected

            # 去噪增强
            enhanced = self._enhance_image(corrected)
            result["enhanced"] = enhanced

        except ImportError:
            # 缺少依赖
            pass
        except Exception:
            # 处理失败，使用原图
            pass

        return result

    def _correct_orientation(self, img_array: Any) -> Any:
        """
        方向检测与矫正

        Args:
            img_array: 图像数组

        Returns:
            矫正后的图像
        """
        try:
            import cv2
            import numpy as np

            # 转为灰度图
            if len(img_array.shape) == 3:
                gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            else:
                gray = img_array

            # 检测文本方向（简化实现）
            # 实际可使用文本检测模型

            return img_array

        except ImportError:
            return img_array
        except Exception:
            return img_array

    def _enhance_image(self, img_array: Any) -> Any:
        """
        图像增强

        Args:
            img_array: 图像数组

        Returns:
            增强后的图像
        """
        try:
            import cv2
            import numpy as np

            # 转为灰度
            if len(img_array.shape) == 3:
                gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            else:
                gray = img_array

            # 自适应对比度增强
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(gray)

            return enhanced

        except ImportError:
            return img_array
        except Exception:
            return img_array

    def _perform_ocr(self, processed_image: Dict[str, Any]) -> tuple:
        """
        执行OCR文字识别

        Args:
            processed_image: 预处理后的图像

        Returns:
            (识别的文本, 置信度)
        """
        try:
            # 优先使用增强后的图像
            image_data = processed_image.get("enhanced") or processed_image.get("corrected")
            if not image_data:
                image_data = processed_image.get("original")

            if isinstance(image_data, bytes):
                image_bytes = image_data
            else:
                # 如果是数组，转换为PIL Image再转bytes
                try:
                    from PIL import Image
                    import numpy as np
                    img = Image.fromarray(image_data)
                    buffer = io.BytesIO()
                    img.save(buffer, format="PNG")
                    image_bytes = buffer.getvalue()
                except Exception:
                    return "", 0.0

            # 尝试使用Tesseract OCR
            try:
                import pytesseract
                from PIL import Image

                image = Image.open(io.BytesIO(image_bytes))
                text = pytesseract.image_to_string(image, lang="chi_sim+eng")
                confidence = 0.85  # Tesseract不直接返回置信度，使用默认值

                return text.strip(), confidence

            except ImportError:
                # Tesseract未安装，尝试使用EasyOCR
                try:
                    import easyocr

                    reader = easyocr.Reader(["ch_sim", "en"])
                    results = reader.readtext(image_bytes)

                    text_parts = []
                    confidences = []
                    for bbox, text, conf in results:
                        text_parts.append(text)
                        confidences.append(conf)

                    full_text = " ".join(text_parts)
                    avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

                    return full_text.strip(), avg_confidence

                except ImportError:
                    # 所有OCR都不可用
                    return "", 0.0

        except Exception as e:
            import logging
            logger = logging.getLogger("rag.parser")
            logger.warning(f"OCR执行失败: {str(e)}")
            return "", 0.0

    def _generate_description(self, image_bytes: bytes) -> Optional[ImageDescription]:
        """
        生成图片描述

        调用视觉模型（如 Ollama qwen2.5-ocr）生成图片描述。
        支持图表类型识别和图表数据提取。

        Args:
            image_bytes: 图像字节数据

        Returns:
            图片描述对象
        """
        try:
            import logging
            logger = logging.getLogger("rag.parser")

            # 获取视觉模型客户端
            vision_client = self._get_vision_client()

            # 检查视觉模型是否启用
            from core.config import settings
            if not settings.vision.enabled:
                logger.info("视觉模型未启用，使用默认描述")
                return ImageDescription(
                    description="图片",
                    confidence=0.5
                )

            # 检查视觉模型服务健康状态
            if not vision_client.health_check():
                logger.warning("视觉模型服务不可用，使用默认描述")
                return ImageDescription(
                    description="图片",
                    confidence=0.5
                )

            # 调用视觉模型生成描述
            description = vision_client.describe(image_bytes)

            logger.info(
                f"图片描述生成成功: {description.description[:50]}...",
                extra={
                    "chart_type": description.chart_type,
                    "confidence": description.confidence
                }
            )

            return description

        except ImportError as e:
            import logging
            logger = logging.getLogger("rag.parser")
            logger.warning(f"视觉模型模块导入失败: {str(e)}")
            return ImageDescription(
                description="图片",
                confidence=0.5
            )
        except Exception as e:
            import logging
            logger = logging.getLogger("rag.parser")
            logger.warning(f"图片描述生成失败: {str(e)}")
            return ImageDescription(
                description="图片描述生成失败",
                confidence=0.3
            )

    def _get_quality_flag(self, confidence: float) -> QualityFlag:
        """
        根据置信度获取质量标记

        Args:
            confidence: 置信度

        Returns:
            质量标记
        """
        if confidence >= 0.8:
            return QualityFlag.GOOD
        elif confidence >= 0.5:
            return QualityFlag.WARNING
        else:
            return QualityFlag.BAD
