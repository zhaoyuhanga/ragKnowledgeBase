# -*- coding: utf-8 -*-
"""
文件存储服务

本模块提供文件存储相关的业务逻辑：
1. 文件保存和删除
2. 文件哈希计算
3. 文件类型识别
4. 存储路径管理
"""

import hashlib
import os
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

from app.common.exception import BusinessException, ErrorCode
from app.common.logging import logger
from core.config import settings


# 支持的文件类型映射
FILE_TYPE_MAP = {
    # Word 文档
    "doc": "doc",
    "docx": "docx",
    # PDF
    "pdf": "pdf",
    # 文本
    "txt": "txt",
    "md": "md",
    "markdown": "md",
    "html": "html",
    "htm": "html",
    # 表格
    "xlsx": "xlsx",
    "xls": "xls",
    "csv": "csv",
    # 图片
    "png": "png",
    "jpg": "jpg",
    "jpeg": "jpeg",
    "gif": "gif",
    "bmp": "bmp",
    "tiff": "tiff",
}

# 支持的文件类型列表
SUPPORTED_TYPES = list(set(FILE_TYPE_MAP.values()))

# MIME 类型映射
MIME_TYPE_MAP = {
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "doc": "application/msword",
    "pdf": "application/pdf",
    "txt": "text/plain",
    "md": "text/markdown",
    "html": "text/html",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "xls": "application/vnd.ms-excel",
    "csv": "text/csv",
    "png": "image/png",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "gif": "image/gif",
    "bmp": "image/bmp",
    "tiff": "image/tiff",
}


@dataclass
class FileInfo:
    """文件信息数据类"""
    original_name: str  # 原始文件名
    stored_name: str    # 存储文件名
    file_path: str      # 文件路径
    file_size: int     # 文件大小
    file_hash: str     # 文件哈希
    doc_type: str      # 文档类型
    mime_type: str     # MIME类型


class FileStorageService:
    """
    文件存储服务

    提供文件存储相关的业务逻辑，包括文件保存、删除、哈希计算、类型识别等。
    """

    def __init__(self):
        """初始化文件存储服务"""
        import os as _os
        # 使用 src 目录作为基准，确保路径在不同工作目录下都能正确解析
        _src_dir = _os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
        _base_path_from_config = settings.document.storage.base_path
        
        # 如果是相对路径，基于 src 目录解析
        if not _os.path.isabs(_base_path_from_config):
            self._base_path = Path(_src_dir) / _base_path_from_config
        else:
            self._base_path = Path(_base_path_from_config)
        
        self._temp_path = Path(settings.document.storage.temp_path)
        self._max_size = settings.document.upload.max_size
        self._allowed_extensions = set(SUPPORTED_TYPES)

    def _ensure_directory(self, directory: Path) -> None:
        """
        确保目录存在

        Args:
            directory: 目录路径
        """
        directory.mkdir(parents=True, exist_ok=True)

    def _get_file_type(self, file_name: str) -> str:
        """
        根据文件名获取文件类型

        Args:
            file_name: 文件名

        Returns:
            文件类型（小写）
        """
        if "." not in file_name:
            return ""

        ext = file_name.rsplit(".", 1)[-1].lower()
        return FILE_TYPE_MAP.get(ext, ext)

    def identify_file_type(self, file_name: str, file_data: bytes) -> str:
        """
        识别文件类型

        优先根据文件扩展名识别，如果无法识别则尝试根据文件头判断。

        Args:
            file_name: 文件名
            file_data: 文件数据

        Returns:
            文件类型

        Raises:
            BusinessException: 文件类型不支持时抛出
        """
        # 首先根据扩展名判断
        doc_type = self._get_file_type(file_name)

        if doc_type in self._allowed_extensions:
            return doc_type

        # 尝试根据文件头判断（MIME magic bytes）
        if len(file_data) >= 4:
            # PDF
            if file_data[:4] == b'%PDF':
                return 'pdf'
            # PNG
            if file_data[:8] == b'\x89PNG\r\n\x1a\n':
                return 'png'
            # JPEG
            if file_data[:2] == b'\xff\xd8':
                return 'jpg'
            # GIF
            if file_data[:6] in (b'GIF87a', b'GIF89a'):
                return 'gif'
            # BMP
            if file_data[:2] == b'BM':
                return 'bmp'

        # 无法识别文件类型
        raise BusinessException(
            code=ErrorCode.FILE_TYPE_NOT_SUPPORT[0],
            message=f"不支持的文件类型: {doc_type or '未知'}，支持的类型: {', '.join(sorted(SUPPORTED_TYPES))}"
        )

    def validate_file(self, file_name: str, file_size: int) -> str:
        """
        验证文件

        Args:
            file_name: 文件名
            file_size: 文件大小

        Returns:
            文件类型

        Raises:
            BusinessException: 文件验证失败时抛出
        """
        # 获取文件类型
        doc_type = self._get_file_type(file_name)

        # 检查文件类型是否支持
        if doc_type not in self._allowed_extensions:
            raise BusinessException(
                code=ErrorCode.FILE_TYPE_NOT_SUPPORT[0],
                message=f"不支持的文件类型: {doc_type}，支持的类型: {', '.join(sorted(SUPPORTED_TYPES))}"
            )

        # 检查文件大小
        if file_size > self._max_size:
            max_mb = self._max_size / (1024 * 1024)
            raise BusinessException(
                code=ErrorCode.FILE_SIZE_TOO_LARGE[0],
                message=f"文件大小超出限制，最大支持 {max_mb:.0f}MB"
            )

        return doc_type

    def calculate_hash(self, file_data: bytes) -> str:
        """
        计算文件哈希（MD5）

        Args:
            file_data: 文件数据

        Returns:
            MD5哈希值
        """
        md5_hash = hashlib.md5(file_data)
        return md5_hash.hexdigest()

    def save_file(
        self,
        file_data: bytes,
        original_name: str,
        doc_type: str,
        business_id: Optional[str] = None
    ) -> FileInfo:
        """
        保存文件

        Args:
            file_data: 文件数据
            original_name: 原始文件名
            doc_type: 文档类型
            business_id: 业务归属ID

        Returns:
            FileInfo: 文件信息

        Raises:
            BusinessException: 文件保存失败时抛出
        """
        try:
            # 计算文件哈希
            file_hash = self.calculate_hash(file_data)

            # 计算文件大小
            file_size = len(file_data)

            # 获取MIME类型
            mime_type = MIME_TYPE_MAP.get(doc_type, "application/octet-stream")

            # 生成存储文件名
            stored_name = f"{uuid.uuid4().hex}_{file_hash[:8]}_{original_name}"

            # 确定存储目录
            if business_id:
                storage_dir = self._base_path / business_id
            else:
                storage_dir = self._base_path / "default"

            self._ensure_directory(storage_dir)

            # 完整存储路径
            storage_path = storage_dir / stored_name

            # 保存文件
            with open(storage_path, "wb") as f:
                f.write(file_data)

            logger.info(
                f"文件保存成功",
                extra={
                    "original_name": original_name,
                    "stored_name": stored_name,
                    "file_size": file_size,
                    "file_hash": file_hash,
                    "storage_path": str(storage_path)
                }
            )

            return FileInfo(
                original_name=original_name,
                stored_name=stored_name,
                file_path=str(storage_path),
                file_size=file_size,
                file_hash=file_hash,
                doc_type=doc_type,
                mime_type=mime_type
            )

        except BusinessException:
            raise
        except Exception as e:
            logger.error(f"文件保存失败: {str(e)}")
            raise BusinessException(
                code=ErrorCode.FILE_UPLOAD_FAILED[0],
                message=f"文件保存失败: {str(e)}"
            )

    def delete_file(self, file_path: str) -> bool:
        """
        删除文件

        Args:
            file_path: 文件路径

        Returns:
            是否删除成功
        """
        try:
            path = Path(file_path)
            if path.exists():
                path.unlink()
                logger.info(f"文件删除成功: {file_path}")
                return True
            else:
                logger.warning(f"文件不存在，无需删除: {file_path}")
                return False
        except Exception as e:
            logger.error(f"文件删除失败: {str(e)}")
            return False

    def get_file_path(self, relative_path: str) -> str:
        """
        获取文件完整路径

        Args:
            relative_path: 相对路径

        Returns:
            完整路径
        """
        return str(self._base_path / relative_path)

    def file_exists(self, file_path: str) -> bool:
        """
        检查文件是否存在

        Args:
            file_path: 文件路径

        Returns:
            是否存在
        """
        return Path(file_path).exists()

    def get_file_content(self, file_path: str) -> bytes:
        """
        获取文件内容

        Args:
            file_path: 文件路径

        Returns:
            文件内容

        Raises:
            BusinessException: 文件读取失败时抛出
        """
        try:
            with open(file_path, "rb") as f:
                return f.read()
        except Exception as e:
            logger.error(f"文件读取失败: {str(e)}")
            raise BusinessException(
                code=ErrorCode.FILE_NOT_FOUND[0],
                message=f"文件读取失败: {str(e)}"
            )


# 全局服务实例
_storage_service: Optional[FileStorageService] = None


def get_storage_service() -> FileStorageService:
    """
    获取文件存储服务实例

    Returns:
        FileStorageService: 文件存储服务实例
    """
    global _storage_service
    if _storage_service is None:
        _storage_service = FileStorageService()
    return _storage_service
