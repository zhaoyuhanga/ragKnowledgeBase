# -*- coding: utf-8 -*-
"""
清洗相关数据Schema

本模块定义清洗服务相关的数据模型：
- 清洗规则请求/响应模型
- 清洗日志响应模型
- 清洗结果模型
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ================================================
# 清洗规则相关模型
# ================================================

class CleaningRuleBase(BaseModel):
    """清洗规则基础模型"""
    name: str = Field(..., description="规则名称", min_length=1, max_length=100)
    rule_type: str = Field(..., description="规则类型")
    rule_config: Dict[str, Any] = Field(..., description="规则配置")
    priority: int = Field(default=100, description="优先级（数字越小越优先）")
    is_enabled: int = Field(default=1, description="是否启用：0-禁用 1-启用")
    scope: Optional[str] = Field(None, description="适用范围：all/pdf/docx/image/table")
    business_scope: Optional[str] = Field(None, description="业务范围筛选")
    description: Optional[str] = Field(None, description="规则说明")


class CleaningRuleCreate(CleaningRuleBase):
    """清洗规则创建模型"""
    creator_id: Optional[int] = Field(None, description="创建人ID")
    creator_name: Optional[str] = Field(None, description="创建人姓名")


class CleaningRuleUpdate(BaseModel):
    """清洗规则更新模型"""
    name: Optional[str] = Field(None, description="规则名称")
    rule_type: Optional[str] = Field(None, description="规则类型")
    rule_config: Optional[Dict[str, Any]] = Field(None, description="规则配置")
    priority: Optional[int] = Field(None, description="优先级")
    is_enabled: Optional[int] = Field(None, description="是否启用")
    scope: Optional[str] = Field(None, description="适用范围")
    business_scope: Optional[str] = Field(None, description="业务范围筛选")
    description: Optional[str] = Field(None, description="规则说明")


class CleaningRuleResponse(BaseModel):
    """清洗规则响应模型"""
    id: int = Field(..., description="规则ID")
    name: str = Field(..., description="规则名称")
    rule_type: str = Field(..., description="规则类型")
    rule_config: Dict[str, Any] = Field(..., description="规则配置")
    priority: int = Field(..., description="优先级")
    is_enabled: int = Field(..., description="是否启用")
    scope: Optional[str] = Field(None, description="适用范围")
    business_scope: Optional[str] = Field(None, description="业务范围筛选")
    description: Optional[str] = Field(None, description="规则说明")
    effect_count: int = Field(..., description="生效次数")
    creator_name: Optional[str] = Field(None, description="创建人姓名")
    created_at: Optional[str] = Field(None, description="创建时间")
    updated_at: Optional[str] = Field(None, description="更新时间")

    class Config:
        from_attributes = True


# ================================================
# 清洗日志相关模型
# ================================================

class CleaningLogResponse(BaseModel):
    """清洗日志响应模型"""
    id: int = Field(..., description="日志ID")
    document_id: int = Field(..., description="文档ID")
    version_id: int = Field(..., description="版本ID")
    element_id: Optional[str] = Field(None, description="元素ID")
    rule_id: Optional[int] = Field(None, description="规则ID")
    rule_name: Optional[str] = Field(None, description="规则名称")
    rule_type: Optional[str] = Field(None, description="规则类型")
    action: str = Field(..., description="操作")
    before_content: Optional[str] = Field(None, description="处理前内容摘要")
    after_content: Optional[str] = Field(None, description="处理后内容摘要")
    hit_count: int = Field(..., description="命中次数")
    created_at: Optional[str] = Field(None, description="创建时间")

    class Config:
        from_attributes = True


# ================================================
# 清洗结果相关模型
# ================================================

class CleanedElement(BaseModel):
    """清洗后的元素模型"""
    element_id: str = Field(..., description="元素ID")
    original_content: str = Field(..., description="原始内容")
    cleaned_content: str = Field(..., description="清洗后内容")
    quality_score: float = Field(..., description="质量评分（0-1）")
    quality_flag: str = Field(..., description="质量标记：good/warning/bad")
    applied_rules: List[str] = Field(default_factory=list, description="应用的规则名称列表")
    issues: List[str] = Field(default_factory=list, description="发现的问题列表")
    is_duplicate: bool = Field(default=False, description="是否重复内容")


class CleaningResult(BaseModel):
    """清洗结果模型"""
    document_id: int = Field(..., description="文档ID")
    version_id: int = Field(..., description="版本ID")
    total_elements: int = Field(..., description="处理元素总数")
    success_count: int = Field(..., description="成功数量")
    warning_count: int = Field(..., description="警告数量")
    bad_count: int = Field(..., description="不良数量")
    duplicate_count: int = Field(..., description="重复数量")
    elements: List[CleanedElement] = Field(default_factory=list, description="清洗后的元素列表")
    quality_summary: Dict[str, int] = Field(..., description="质量统计摘要")
    applied_rule_count: int = Field(..., description="应用的规则总数")
    processing_time_ms: int = Field(..., description="处理耗时（毫秒）")


# ================================================
# 清洗配置相关模型
# ================================================

class CleaningConfig(BaseModel):
    """清洗配置模型"""
    enable_encoding_fix: bool = Field(default=True, description="是否启用编码修复")
    enable_noise_removal: bool = Field(default=True, description="是否启用噪声过滤")
    enable_duplicate_detection: bool = Field(default=True, description="是否启用重复检测")
    enable_desensitization: bool = Field(default=True, description="是否启用脱敏")
    enable_quality_scoring: bool = Field(default=True, description="是否启用质量评分")
    quality_threshold: float = Field(default=0.5, description="质量评分阈值")
    duplicate_similarity_threshold: float = Field(default=0.85, description="重复相似度阈值")


class BatchCleaningRequest(BaseModel):
    """批量清洗请求模型"""
    document_ids: List[int] = Field(..., description="文档ID列表")
    config: Optional[CleaningConfig] = Field(None, description="清洗配置")
    rule_ids: Optional[List[int]] = Field(None, description="指定使用的规则ID列表")
