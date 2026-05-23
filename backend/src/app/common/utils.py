# -*- coding: utf-8 -*-
"""
通用工具模块

本模块提供通用工具函数。
"""

import hashlib
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


def generate_uuid() -> str:
    """
    生成UUID

    Returns:
        UUID字符串
    """
    return str(uuid.uuid4())


def generate_trace_id() -> str:
    """
    生成追踪ID

    格式：日期时间+序号

    Returns:
        追踪ID字符串
    """
    now = datetime.now(timezone.utc)
    date_part = now.strftime("%Y%m%d%H%M")
    unique_part = str(uuid.uuid4().int)[:6]
    return f"{date_part}{unique_part}"


def compute_hash(text: str) -> str:
    """
    计算文本SHA256哈希

    Args:
        text: 文本内容

    Returns:
        SHA256哈希值
    """
    return hashlib.sha256(text.encode()).hexdigest()


def normalize_query(query: str) -> str:
    """
    标准化查询文本

    - 去除多余空格
    - 统一大小写
    - 去除首尾空白

    Args:
        query: 原始查询

    Returns:
        标准化后的查询
    """
    import re
    query = re.sub(r'\s+', ' ', query)
    query = query.lower().strip()
    return query


def paginate_list(items: List[Any], page_no: int, page_size: int) -> Dict[str, Any]:
    """
    分页列表

    Args:
        items: 完整列表
        page_no: 页码
        page_size: 每页数量

    Returns:
        包含items和pagination的字典
    """
    total = len(items)
    pages = (total + page_size - 1) // page_size if page_size > 0 else 0
    start = (page_no - 1) * page_size
    end = start + page_size

    return {
        "items": items[start:end],
        "total": total,
        "page_no": page_no,
        "page_size": page_size,
        "pages": pages
    }


def mask_sensitive_info(text: str, info_type: str = "phone") -> str:
    """
    脱敏敏感信息

    Args:
        text: 原始文本
        info_type: 信息类型 (phone/id_card/email)

    Returns:
        脱敏后的文本
    """
    if info_type == "phone":
        if len(text) >= 7:
            return text[:3] + "****" + text[-4:]
    elif info_type == "id_card":
        if len(text) >= 10:
            return text[:4] + "********" + text[-4:]
    elif info_type == "email":
        if "@" in text:
            parts = text.split("@")
            if len(parts[0]) > 2:
                return parts[0][:2] + "***@" + parts[1]
    return text
