# -*- coding: utf-8 -*-
"""
清洗服务

本模块提供文档内容清洗的核心服务，包括：
- 编码修复与乱码检测
- 噪声过滤（页眉页脚、水印、广告）
- 重复段落识别
- 敏感信息脱敏
- 质量评分
"""

import hashlib
import re
import time
import unicodedata
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from typing import Any, Dict, List, Optional, Tuple

from app.common.exception import BusinessException, ErrorCode
from app.common.logging import logger
from app.models.cleaning import (
    CleaningLog,
    CleaningRule,
    DEFAULT_CLEANING_RULES,
)
from app.models.parse import DocumentElement
from app.schemas.cleaning import (
    CleanedElement,
    CleaningConfig,
    CleaningResult,
    CleaningRuleCreate,
    CleaningRuleResponse,
    CleaningRuleUpdate,
)
from core.database import SessionLocal


# ================================================
# 预定义脱敏模式
# ================================================

DESENSITIZATION_PATTERNS = {
    "手机号": (r"1[3-9]\d{9}", "138****1234"),
    "身份证号": (r"\d{17}[\dXx]", "310***********1234"),
    "邮箱": (r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", "user@example.com"),
    "银行卡号": (r"\d{16,19}", "622202***********1234"),
    "IP地址": (r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}", "192.168.***.***"),
}


# ================================================
# 乱码检测模式
# ================================================

GARBLED_PATTERNS = [
    r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]",  # 控制字符
    r"[\ufffd]{2,}",  # Unicode替换字符
    r"[\x80-\xff]{3,}",  # 可能的UTF-8编码问题
]


# ================================================
# 噪声模式
# ================================================

NOISE_PATTERNS = {
    "页眉页脚": [
        r"^第\s*\d+\s*页$",
        r"^Page\s+\d+$",
        r"^Pages?\s+\d+(\s*-\s*\d+)?$",
        r"^\d+/\d+$",
        r"^第\s*\d+\s*页\s*/\s*共\s*\d+\s*页$",
        r"^©\s*\d{4}",
        r"^版权所有",
        r"^未经授权",
        r"^Confidential$",
        r"^内部资料$",
        r"^机密$",
        r"^草稿$",
        r"^Draft$",
    ],
    "水印": [
        r"^草稿$",
        r"^内部资料$",
        r"^机密$",
        r"^Confidential$",
        r"^Draft$",
        r"^样本$",
        r"^Sample$",
    ],
    "广告推广": [
        r"立即购买",
        r"点击查看",
        r"扫码.*关注",
        r"推广",
        r"广告",
        r"订阅",
        r"优惠.*截止",
        r"限时.*抢购",
    ],
    "特殊符号": [
        r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]",  # 控制字符
        r"[\u200b-\u200f]",  # 零宽字符
        r"[\ufeff]",  # BOM字符
    ],
}


# ================================================
# 数据类定义
# ================================================

@dataclass
class CleaningRuleItem:
    """清洗规则项"""
    rule_id: int
    name: str
    rule_type: str
    config: Dict[str, Any]
    priority: int


@dataclass
class CleaningContext:
    """清洗上下文"""
    document_id: int
    version_id: int
    rules: List[CleaningRuleItem] = field(default_factory=list)
    seen_contents: List[str] = field(default_factory=list)  # 用于重复检测
    seen_hashes: List[str] = field(default_factory=list)


@dataclass
class CleaningReport:
    """清洗报告"""
    element_id: str
    original_content: str
    cleaned_content: str
    applied_rules: List[str] = field(default_factory=list)
    issues: List[str] = field(default_factory=list)
    quality_score: float = 1.0
    quality_flag: str = "good"
    is_duplicate: bool = False


# ================================================
# 清洗服务类
# ================================================

class CleanService:
    """
    文档清洗服务

    提供完整的文档内容清洗功能，包括编码修复、噪声过滤、重复检测、脱敏和质量评分。
    """

    def __init__(self):
        """初始化清洗服务"""
        self._rules_cache: Optional[List[CleaningRuleItem]] = None
        self._cache_time: float = 0
        self._cache_ttl: float = 300  # 缓存5分钟

    def get_cleaning_rules(
        self,
        scope: Optional[str] = None,
        rule_type: Optional[str] = None,
        enabled_only: bool = True
    ) -> List[CleaningRuleItem]:
        """
        获取清洗规则列表

        Args:
            scope: 适用范围筛选
            rule_type: 规则类型筛选
            enabled_only: 是否只返回启用的规则

        Returns:
            清洗规则列表
        """
        # 检查缓存
        current_time = time.time()
        if (self._rules_cache is not None and 
            current_time - self._cache_time < self._cache_ttl):
            rules = self._rules_cache
        else:
            # 从数据库加载规则
            rules = self._load_rules_from_db()
            self._rules_cache = rules
            self._cache_time = current_time

        # 应用筛选条件
        filtered_rules = []
        for rule in rules:
            if enabled_only and rule.config.get("is_enabled", 1) == 0:
                continue
            if scope and scope != "all" and rule.config.get("scope") not in [None, "all", scope]:
                continue
            if rule_type and rule.rule_type != rule_type:
                continue
            filtered_rules.append(rule)

        # 按优先级排序
        filtered_rules.sort(key=lambda r: r.priority)
        return filtered_rules

    def _load_rules_from_db(self) -> List[CleaningRuleItem]:
        """从数据库加载清洗规则"""
        rules = []
        db = SessionLocal()
        try:
            db_rules = db.query(CleaningRule).filter(
                CleaningRule.is_deleted == 0
            ).order_by(CleaningRule.priority).all()

            for rule in db_rules:
                rules.append(CleaningRuleItem(
                    rule_id=rule.id,
                    name=rule.name,
                    rule_type=rule.rule_type,
                    config=rule.rule_config or {},
                    priority=rule.priority
                ))

            logger.info(
                f"从数据库加载清洗规则: {len(rules)}条",
                extra={"total_rules": len(rules)}
            )

        except Exception as e:
            logger.error(f"加载清洗规则失败: {str(e)}")
            # 如果数据库加载失败，使用默认规则
            rules = self._get_default_rules()
        finally:
            db.close()

        return rules

    def _get_default_rules(self) -> List[CleaningRuleItem]:
        """获取默认清洗规则"""
        rules = []
        for i, rule_config in enumerate(DEFAULT_CLEANING_RULES):
            rules.append(CleaningRuleItem(
                rule_id=-i - 1,  # 使用负数表示默认规则
                name=rule_config["name"],
                rule_type=rule_config["rule_type"],
                config=rule_config,
                priority=rule_config.get("priority", 100)
            ))
        return rules

    def clean_document(
        self,
        document_id: int,
        version_id: int,
        elements: List[DocumentElement],
        config: Optional[CleaningConfig] = None
    ) -> CleaningResult:
        """
        清洗文档

        Args:
            document_id: 文档ID
            version_id: 版本ID
            elements: 待清洗的元素列表
            config: 清洗配置

        Returns:
            清洗结果
        """
        start_time = time.time()

        # 默认配置
        if config is None:
            config = CleaningConfig()

        # 创建清洗上下文
        context = CleaningContext(
            document_id=document_id,
            version_id=version_id
        )

        # 加载规则
        context.rules = self.get_cleaning_rules()

        # 清洗结果统计
        success_count = 0
        warning_count = 0
        bad_count = 0
        duplicate_count = 0
        cleaned_elements: List[CleanedElement] = []
        applied_rule_count = 0

        db = SessionLocal()
        try:
            for element in elements:
                # 跳过无内容的元素
                if not element.content or not element.content.strip():
                    continue

                # 执行清洗
                report = self._clean_element(element, context, config)

                # 统计
                if report.quality_flag == "good":
                    success_count += 1
                elif report.quality_flag == "warning":
                    warning_count += 1
                else:
                    bad_count += 1

                if report.is_duplicate:
                    duplicate_count += 1

                applied_rule_count += len(report.applied_rules)

                # 构建清洗后的元素
                cleaned_element = CleanedElement(
                    element_id=element.element_id,
                    original_content=report.original_content,
                    cleaned_content=report.cleaned_content,
                    quality_score=report.quality_score,
                    quality_flag=report.quality_flag,
                    applied_rules=report.applied_rules,
                    issues=report.issues,
                    is_duplicate=report.is_duplicate
                )
                cleaned_elements.append(cleaned_element)

                # 记录清洗日志
                self._save_cleaning_log(
                    db=db,
                    document_id=document_id,
                    version_id=version_id,
                    element_id=element.element_id,
                    report=report
                )

            db.commit()

        except Exception as e:
            db.rollback()
            logger.error(f"文档清洗失败: {str(e)}")
            raise BusinessException(
                code=ErrorCode.OPERATION_FAILED[0],
                message=f"文档清洗失败: {str(e)}"
            )
        finally:
            db.close()

        processing_time = int((time.time() - start_time) * 1000)

        logger.info(
            f"文档清洗完成",
            extra={
                "document_id": document_id,
                "version_id": version_id,
                "total_elements": len(elements),
                "success_count": success_count,
                "warning_count": warning_count,
                "bad_count": bad_count,
                "duplicate_count": duplicate_count,
                "processing_time_ms": processing_time
            }
        )

        return CleaningResult(
            document_id=document_id,
            version_id=version_id,
            total_elements=len(elements),
            success_count=success_count,
            warning_count=warning_count,
            bad_count=bad_count,
            duplicate_count=duplicate_count,
            elements=cleaned_elements,
            quality_summary={
                "good": success_count,
                "warning": warning_count,
                "bad": bad_count,
                "duplicate": duplicate_count
            },
            applied_rule_count=applied_rule_count,
            processing_time_ms=processing_time
        )

    def _clean_element(
        self,
        element: DocumentElement,
        context: CleaningContext,
        config: CleaningConfig
    ) -> CleaningReport:
        """
        清洗单个元素

        Args:
            element: 待清洗的元素
            context: 清洗上下文
            config: 清洗配置

        Returns:
            清洗报告
        """
        report = CleaningReport(
            element_id=element.element_id,
            original_content=element.content,
            cleaned_content=element.content
        )

        current_content = element.content

        # 1. 编码修复与乱码检测
        if config.enable_encoding_fix:
            current_content, encoding_issues = self._fix_encoding(current_content)
            if encoding_issues:
                report.issues.extend(encoding_issues)
                report.applied_rules.append("编码修复")

        # 2. 应用清洗规则（噪声过滤）
        if config.enable_noise_removal:
            current_content, applied_rules = self._apply_cleaning_rules(current_content, context)
            report.applied_rules.extend(applied_rules)

        # 3. 敏感信息脱敏
        if config.enable_desensitization:
            current_content, desensitized = self._desensitize(current_content)
            if desensitized:
                report.applied_rules.append("敏感信息脱敏")

        # 4. 重复检测
        if config.enable_duplicate_detection:
            is_duplicate, similarity = self._check_duplicate(current_content, context)
            if is_duplicate:
                report.is_duplicate = True
                report.issues.append(f"重复内容（相似度: {similarity:.2f}）")

        # 5. 质量评分
        if config.enable_quality_scoring:
            quality_score, quality_flag, quality_issues = self._score_quality(
                current_content,
                element.confidence if element.confidence else 1.0
            )
            report.quality_score = quality_score
            report.quality_flag = quality_flag
            report.issues.extend(quality_issues)

        report.cleaned_content = current_content.strip()

        # 更新上下文
        context.seen_contents.append(current_content)
        context.seen_hashes.append(self._compute_hash(current_content))

        return report

    def _fix_encoding(self, text: str) -> Tuple[str, List[str]]:
        """
        修复编码问题

        Args:
            text: 原始文本

        Returns:
            (修复后的文本, 发现的问题列表)
        """
        issues = []
        fixed_text = text

        # 检测并标记乱码
        has_garbled = False
        for pattern in GARBLED_PATTERNS:
            if re.search(pattern, fixed_text):
                has_garbled = True
                issues.append("检测到可能的乱码字符")
                break

        # 修复控制字符
        fixed_text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", fixed_text)

        # 修复Unicode替换字符
        fixed_text = re.sub(r"\ufffd+", "", fixed_text)

        # 归一化Unicode
        fixed_text = unicodedata.normalize("NFKC", fixed_text)

        # 修复多余空白
        fixed_text = re.sub(r"\s+", " ", fixed_text)

        if has_garbled:
            logger.warning(f"文本可能存在乱码", extra={"original_length": len(text)})

        return fixed_text, issues

    def _apply_cleaning_rules(
        self,
        text: str,
        context: CleaningContext
    ) -> Tuple[str, List[str]]:
        """
        应用清洗规则

        Args:
            text: 原始文本
            context: 清洗上下文

        Returns:
            (清洗后的文本, 应用的规则名称列表)
        """
        applied_rules = []
        current_text = text

        for rule_item in context.rules:
            if rule_item.rule_type == "regex_delete":
                # 正则删除
                patterns = rule_item.config.get("patterns", [])
                for pattern in patterns:
                    if re.search(pattern, current_text):
                        current_text = re.sub(pattern, "", current_text)
                        if rule_item.name not in applied_rules:
                            applied_rules.append(rule_item.name)

            elif rule_item.rule_type == "regex_replace":
                # 正则替换
                pattern = rule_item.config.get("pattern")
                replacement = rule_item.config.get("replacement", "")
                if pattern and re.search(pattern, current_text):
                    current_text = re.sub(pattern, replacement, current_text)
                    if rule_item.name not in applied_rules:
                        applied_rules.append(rule_item.name)

        return current_text, applied_rules

    def _desensitize(self, text: str) -> Tuple[str, bool]:
        """
        敏感信息脱敏

        Args:
            text: 原始文本

        Returns:
            (脱敏后的文本, 是否进行了脱敏)
        """
        desensitized = False
        result = text

        for name, (pattern, replacement) in DESENSITIZATION_PATTERNS.items():
            if re.search(pattern, result):
                result = re.sub(pattern, replacement, result)
                desensitized = True

        return result, desensitized

    def _check_duplicate(
        self,
        text: str,
        context: CleaningContext
    ) -> Tuple[bool, float]:
        """
        检查重复内容

        Args:
            text: 待检查文本
            context: 清洗上下文

        Returns:
            (是否重复, 相似度)
        """
        text_hash = self._compute_hash(text)

        # 精确匹配检查
        if text_hash in context.seen_hashes:
            return True, 1.0

        # 模糊匹配检查（相似度）
        for seen_text in context.seen_contents:
            similarity = SequenceMatcher(None, text, seen_text).ratio()
            if similarity >= 0.85:
                return True, similarity

        return False, 0.0

    def _compute_hash(self, text: str) -> str:
        """计算文本哈希"""
        normalized = text.lower().strip()
        return hashlib.md5(normalized.encode("utf-8")).hexdigest()

    def _score_quality(
        self,
        text: str,
        original_confidence: float
    ) -> Tuple[float, str, List[str]]:
        """
        质量评分

        Args:
            text: 清洗后的文本
            original_confidence: 原始置信度

        Returns:
            (质量评分, 质量标记, 问题列表)
        """
        issues = []
        score = original_confidence

        # 检查文本长度
        if len(text) < 10:
            issues.append("文本内容过短")
            score *= 0.8
        elif len(text) > 50000:
            issues.append("文本内容过长")
            score *= 0.9

        # 检查乱码比例
        garbled_ratio = self._calculate_garbled_ratio(text)
        if garbled_ratio > 0.1:
            issues.append(f"乱码比例过高: {garbled_ratio:.2%}")
            score *= (1 - garbled_ratio)

        # 检查有效字符比例
        valid_ratio = self._calculate_valid_ratio(text)
        if valid_ratio < 0.5:
            issues.append(f"有效字符比例过低: {valid_ratio:.2%}")
            score *= valid_ratio

        # 确保评分在合理范围内
        score = max(0.0, min(1.0, score))

        # 确定质量标记
        if score >= 0.7:
            quality_flag = "good"
        elif score >= 0.4:
            quality_flag = "warning"
        else:
            quality_flag = "bad"

        return score, quality_flag, issues

    def _calculate_garbled_ratio(self, text: str) -> float:
        """计算乱码比例"""
        if not text:
            return 0.0

        garbled_count = 0
        for char in text:
            # 检测乱码字符
            if ord(char) in [0xFFFD] or (0x80 <= ord(char) <= 0xFF and not self._is_valid_utf8_char(char)):
                garbled_count += 1

        return garbled_count / len(text)

    def _is_valid_utf8_char(self, char: str) -> bool:
        """检查字符是否为有效UTF-8字符"""
        try:
            char.encode("utf-8")
            return True
        except UnicodeEncodeError:
            return False

    def _calculate_valid_ratio(self, text: str) -> float:
        """计算有效字符比例"""
        if not text:
            return 0.0

        # 有效字符：字母、数字、中文、常用标点
        valid_pattern = re.compile(r"[\w\u4e00-\u9fa5\u3000-\u303f\uff00-\uffef]")
        valid_count = len(valid_pattern.findall(text))

        return valid_count / len(text)

    def _save_cleaning_log(
        self,
        db,
        document_id: int,
        version_id: int,
        element_id: str,
        report: CleaningReport
    ) -> None:
        """保存清洗日志"""
        if not report.applied_rules:
            return

        for rule_name in report.applied_rules:
            log = CleaningLog(
                document_id=document_id,
                version_id=version_id,
                element_id=element_id,
                action="clean",
                before_content=report.original_content[:200] if len(report.original_content) > 200 else report.original_content,
                after_content=report.cleaned_content[:200] if len(report.cleaned_content) > 200 else report.cleaned_content,
                hit_count=1
            )
            db.add(log)

    # ================================================
    # 规则管理方法
    # ================================================

    def create_rule(self, rule_data: CleaningRuleCreate) -> CleaningRuleResponse:
        """创建清洗规则"""
        db = SessionLocal()
        try:
            rule = CleaningRule(
                name=rule_data.name,
                rule_type=rule_data.rule_type,
                rule_config=rule_data.rule_config,
                priority=rule_data.priority,
                is_enabled=rule_data.is_enabled,
                scope=rule_data.scope,
                business_scope=rule_data.business_scope,
                description=rule_data.description,
                creator_id=rule_data.creator_id,
                creator_name=rule_data.creator_name
            )
            db.add(rule)
            db.commit()
            db.refresh(rule)

            # 清除缓存
            self._rules_cache = None

            logger.info(f"创建清洗规则成功: {rule.name}", extra={"rule_id": rule.id})

            return self._rule_to_response(rule)

        except Exception as e:
            db.rollback()
            logger.error(f"创建清洗规则失败: {str(e)}")
            raise BusinessException(
                code=ErrorCode.OPERATION_FAILED[0],
                message=f"创建清洗规则失败: {str(e)}"
            )
        finally:
            db.close()

    def update_rule(self, rule_id: int, rule_data: CleaningRuleUpdate) -> CleaningRuleResponse:
        """更新清洗规则"""
        db = SessionLocal()
        try:
            rule = db.query(CleaningRule).filter(CleaningRule.id == rule_id).first()
            if not rule:
                raise BusinessException(
                    code=ErrorCode.DATA_NOT_FOUND[0],
                    message=f"清洗规则不存在: {rule_id}"
                )

            # 更新字段
            update_data = rule_data.model_dump(exclude_unset=True)
            for key, value in update_data.items():
                if value is not None:
                    setattr(rule, key, value)

            db.commit()
            db.refresh(rule)

            # 清除缓存
            self._rules_cache = None

            logger.info(f"更新清洗规则成功: {rule.name}", extra={"rule_id": rule.id})

            return self._rule_to_response(rule)

        except BusinessException:
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"更新清洗规则失败: {str(e)}")
            raise BusinessException(
                code=ErrorCode.OPERATION_FAILED[0],
                message=f"更新清洗规则失败: {str(e)}"
            )
        finally:
            db.close()

    def delete_rule(self, rule_id: int) -> bool:
        """删除清洗规则"""
        db = SessionLocal()
        try:
            rule = db.query(CleaningRule).filter(CleaningRule.id == rule_id).first()
            if not rule:
                raise BusinessException(
                    code=ErrorCode.DATA_NOT_FOUND[0],
                    message=f"清洗规则不存在: {rule_id}"
                )

            rule.is_deleted = 1
            db.commit()

            # 清除缓存
            self._rules_cache = None

            logger.info(f"删除清洗规则成功", extra={"rule_id": rule_id})

            return True

        except BusinessException:
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"删除清洗规则失败: {str(e)}")
            raise BusinessException(
                code=ErrorCode.OPERATION_FAILED[0],
                message=f"删除清洗规则失败: {str(e)}"
            )
        finally:
            db.close()

    def list_rules(
        self,
        page: int = 1,
        page_size: int = 20,
        scope: Optional[str] = None,
        rule_type: Optional[str] = None,
        enabled_only: bool = False
    ) -> Tuple[List[CleaningRuleResponse], int]:
        """获取规则列表"""
        db = SessionLocal()
        try:
            query = db.query(CleaningRule).filter(CleaningRule.is_deleted == 0)

            if enabled_only:
                query = query.filter(CleaningRule.is_enabled == 1)
            if scope:
                query = query.filter(CleaningRule.scope == scope)
            if rule_type:
                query = query.filter(CleaningRule.rule_type == rule_type)

            total = query.count()
            rules = query.order_by(CleaningRule.priority).offset(
                (page - 1) * page_size
            ).limit(page_size).all()

            return [self._rule_to_response(r) for r in rules], total

        finally:
            db.close()

    def _rule_to_response(self, rule: CleaningRule) -> CleaningRuleResponse:
        """将规则模型转换为响应模型"""
        return CleaningRuleResponse(
            id=rule.id,
            name=rule.name,
            rule_type=rule.rule_type,
            rule_config=rule.rule_config or {},
            priority=rule.priority,
            is_enabled=rule.is_enabled,
            scope=rule.scope,
            business_scope=rule.business_scope,
            description=rule.description,
            effect_count=rule.effect_count,
            creator_name=rule.creator_name,
            created_at=rule.created_at.isoformat() if rule.created_at else None,
            updated_at=rule.updated_at.isoformat() if rule.updated_at else None
        )


# 全局服务实例
_clean_service: Optional[CleanService] = None


def get_clean_service() -> CleanService:
    """获取清洗服务实例"""
    global _clean_service
    if _clean_service is None:
        _clean_service = CleanService()
    return _clean_service
