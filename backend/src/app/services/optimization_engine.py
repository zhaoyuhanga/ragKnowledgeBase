# -*- coding: utf-8 -*-
"""
优化规则触发引擎

本模块实现优化规则的触发条件匹配和执行：
- 条件表达式解析
- 规则匹配检查
- 规则自动应用
- 规则效果评估
"""

import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from app.common.logging import logger


@dataclass
class TriggerCondition:
    """触发条件"""
    condition_type: str  # issue_category/occurrence_count/quality_score/time_range
    operator: str  # eq/ne/gt/gte/lt/lte/in/between/contains
    value: Any  # 比较值
    threshold: Optional[Any] = None  # 范围上限（用于between操作）


@dataclass
class RuleMatchResult:
    """规则匹配结果"""
    matched: bool  # 是否匹配
    rule_id: int  # 规则ID
    rule_name: str  # 规则名称
    confidence: float = 1.0  # 匹配置信度
    matched_conditions: List[str] = field(default_factory=list)  # 匹配的条件


@dataclass
class RuleExecutionResult:
    """规则执行结果"""
    success: bool  # 是否成功
    rule_id: int  # 规则ID
    execution_time_ms: int  # 执行耗时
    result_message: str  # 结果消息
    affected_items: int = 0  # 影响的条目数


class OptimizationRuleEngine:
    """
    优化规则触发引擎

    管理优化规则的触发条件匹配和自动执行。
    """

    # 支持的操作符
    OPERATORS = {
        "eq": lambda a, b: a == b,
        "ne": lambda a, b: a != b,
        "gt": lambda a, b: a > b,
        "gte": lambda a, b: a >= b,
        "lt": lambda a, b: a < b,
        "lte": lambda a, b: a <= b,
        "in": lambda a, b: a in b if isinstance(b, list) else a == b,
        "not_in": lambda a, b: a not in b if isinstance(b, list) else a != b,
        "contains": lambda a, b: b in a if isinstance(a, str) else False,
        "between": lambda a, b: b[0] <= a <= b[1] if isinstance(b, list) and len(b) == 2 else False,
    }

    def __init__(self):
        """初始化引擎"""
        self._rules_cache: List[Dict[str, Any]] = []
        self._cache_time: float = 0
        self._cache_ttl: float = 300  # 5分钟缓存

    def check_trigger(
        self,
        analysis: Any,
        rules: List[Any]
    ) -> List[RuleMatchResult]:
        """
        检查是否触发了优化规则

        Args:
            analysis: 反馈分析记录
            rules: 规则列表

        Returns:
            匹配成功的规则列表
        """
        matched_rules = []

        for rule in rules:
            # 跳过未启用的规则
            if hasattr(rule, "enabled") and rule.enabled == 0:
                continue

            # 跳过非pending状态的规则
            if hasattr(rule, "status") and rule.status not in [2, 4]:  # 非已审核或已启用
                continue

            result = self._match_rule(analysis, rule)
            if result.matched:
                matched_rules.append(result)
                logger.info(
                    "规则匹配成功",
                    extra={
                        "rule_id": rule.id,
                        "rule_name": rule.rule_name,
                        "confidence": result.confidence
                    }
                )

        return matched_rules

    def _match_rule(
        self,
        analysis: Any,
        rule: Any
    ) -> RuleMatchResult:
        """
        匹配单个规则

        Args:
            analysis: 反馈分析记录
            rule: 规则记录

        Returns:
            匹配结果
        """
        matched_conditions = []
        confidence = 1.0

        # 解析触发条件
        trigger_conditions = self._parse_trigger_condition(rule.trigger_condition)
        if not trigger_conditions:
            # 没有触发条件，检查是否需要触发
            return RuleMatchResult(
                matched=False,
                rule_id=rule.id,
                rule_name=rule.rule_name
            )

        # 检查每个条件
        for condition in trigger_conditions:
            if self._evaluate_condition(analysis, condition):
                matched_conditions.append(str(condition))
            else:
                # 任意条件不匹配则整体不匹配
                return RuleMatchResult(
                    matched=False,
                    rule_id=rule.id,
                    rule_name=rule.rule_name
                )

        return RuleMatchResult(
            matched=True,
            rule_id=rule.id,
            rule_name=rule.rule_name,
            confidence=confidence,
            matched_conditions=matched_conditions
        )

    def _parse_trigger_condition(
        self,
        condition_json: Optional[str]
    ) -> List[TriggerCondition]:
        """解析触发条件JSON"""
        if not condition_json:
            return []

        try:
            if isinstance(condition_json, str):
                condition_dict = json.loads(condition_json)
            else:
                condition_dict = condition_json

            conditions = []
            if isinstance(condition_dict, dict):
                for key, value in condition_dict.items():
                    condition = self._create_condition(key, value)
                    if condition:
                        conditions.append(condition)
            elif isinstance(condition_dict, list):
                for item in condition_dict:
                    if isinstance(item, dict):
                        for key, value in item.items():
                            condition = self._create_condition(key, value)
                            if condition:
                                conditions.append(condition)

            return conditions

        except (json.JSONDecodeError, TypeError) as e:
            logger.warning(f"解析触发条件失败: {str(e)}")
            return []

    def _create_condition(
        self,
        key: str,
        value: Any
    ) -> Optional[TriggerCondition]:
        """根据键值创建条件"""
        # 解析条件类型和操作符
        parts = key.split("__")
        if len(parts) == 2:
            condition_type, operator = parts
        else:
            condition_type = key
            operator = "eq"  # 默认等于

        # 解析阈值
        threshold = None
        if isinstance(value, dict):
            threshold = value.get("threshold")
            value = value.get("value", value)

        return TriggerCondition(
            condition_type=condition_type,
            operator=operator,
            value=value,
            threshold=threshold
        )

    def _evaluate_condition(
        self,
        analysis: Any,
        condition: TriggerCondition
    ) -> bool:
        """评估条件是否满足"""
        # 获取分析记录的属性值
        attr_value = self._get_attribute_value(analysis, condition.condition_type)
        if attr_value is None:
            return False

        # 获取比较操作
        operator_func = self.OPERATORS.get(condition.operator)
        if not operator_func:
            logger.warning(f"不支持的操作符: {condition.operator}")
            return False

        # 执行比较
        try:
            return operator_func(attr_value, condition.value)
        except (TypeError, ValueError):
            return False

    def _get_attribute_value(
        self,
        analysis: Any,
        attribute: str
    ) -> Any:
        """获取分析记录的属性值"""
        # 直接属性
        if hasattr(analysis, attribute):
            return getattr(analysis, attribute)

        # 映射关系
        attribute_mapping = {
            "issue_category": "issue_category",
            "issue_type": "issue_type",
            "retrieval_score": "retrieval_score",
            "generation_score": "generation_score",
            "retrieval_avg_score": "retrieval_avg_score",
            "retrieval_result_count": "retrieval_result_count",
            "retrieval_timeout": "retrieval_timeout",
            "feedback_type": "feedback_type",
        }

        mapped_attr = attribute_mapping.get(attribute)
        if mapped_attr and hasattr(analysis, mapped_attr):
            return getattr(analysis, mapped_attr)

        return None

    def check_occurrence_trigger(
        self,
        tenant_id: int,
        issue_category: str,
        min_occurrence: int = 10,
        time_window_hours: int = 24
    ) -> bool:
        """
        检查问题类型是否达到触发次数

        Args:
            tenant_id: 租户ID
            issue_category: 问题分类
            min_occurrence: 最小触发次数
            time_window_hours: 时间窗口（小时）

        Returns:
            是否达到触发条件
        """
        from core.database import SessionLocal
        from app.models.feedback import FeedbackAnalysis

        db = SessionLocal()
        try:
            time_threshold = datetime.now() - timedelta(hours=time_window_hours)

            count = db.query(FeedbackAnalysis).filter(
                FeedbackAnalysis.tenant_id == tenant_id,
                FeedbackAnalysis.issue_category == issue_category,
                FeedbackAnalysis.created_at >= time_threshold,
                FeedbackAnalysis.handled_status == 0  # 未处理
            ).count()

            triggered = count >= min_occurrence

            logger.info(
                "检查问题触发次数",
                extra={
                    "tenant_id": tenant_id,
                    "issue_category": issue_category,
                    "occurrence_count": count,
                    "min_occurrence": min_occurrence,
                    "triggered": triggered
                }
            )

            return triggered

        finally:
            db.close()

    def get_applicable_rules(
        self,
        tenant_id: int,
        rule_type: Optional[str] = None
    ) -> List[Any]:
        """
        获取适用的优化规则

        Args:
            tenant_id: 租户ID
            rule_type: 规则类型

        Returns:
            适用的规则列表
        """
        from core.database import SessionLocal
        from app.models.feedback import OptimizationRule

        db = SessionLocal()
        try:
            query = db.query(OptimizationRule).filter(
                OptimizationRule.tenant_id == tenant_id,
                OptimizationRule.status.in_([2, 4]),  # 已审核或已启用
                OptimizationRule.enabled == 1
            )

            if rule_type:
                query = query.filter(OptimizationRule.rule_type == rule_type)

            rules = query.order_by(OptimizationRule.priority.asc()).all()

            logger.info(
                f"获取适用规则: {len(rules)}条",
                extra={"tenant_id": tenant_id, "rule_type": rule_type}
            )

            return rules

        finally:
            db.close()

    def evaluate_rule_effect(
        self,
        rule_id: int,
        time_window_hours: int = 24
    ) -> Dict[str, Any]:
        """
        评估规则效果

        Args:
            rule_id: 规则ID
            time_window_hours: 评估时间窗口

        Returns:
            效果评估结果
        """
        from core.database import SessionLocal
        from app.models.feedback import FeedbackAnalysis, OptimizationRule

        db = SessionLocal()
        try:
            rule = db.query(OptimizationRule).filter(
                OptimizationRule.id == rule_id
            ).first()

            if not rule:
                return {"error": "规则不存在"}

            # 获取规则应用后的反馈数据
            time_threshold = datetime.now() - timedelta(hours=time_window_hours)

            # 统计应用后的相关问题数量
            issue_count = db.query(FeedbackAnalysis).filter(
                FeedbackAnalysis.tenant_id == rule.tenant_id,
                FeedbackAnalysis.created_at >= time_threshold
            )

            # 根据规则类型筛选
            if rule.rule_type == "retrieval":
                issue_count = issue_count.filter(
                    FeedbackAnalysis.issue_type.in_(["retrieval", "both"])
                )
            elif rule.rule_type == "generation":
                issue_count = issue_count.filter(
                    FeedbackAnalysis.issue_type.in_(["generation", "both"])
                )

            count = issue_count.count()

            # 计算趋势（如果有历史数据）
            prev_time_threshold = datetime.now() - timedelta(hours=time_window_hours * 2)
            prev_count_query = db.query(FeedbackAnalysis).filter(
                FeedbackAnalysis.tenant_id == rule.tenant_id,
                FeedbackAnalysis.created_at >= prev_time_threshold,
                FeedbackAnalysis.created_at < time_threshold
            )

            if rule.rule_type == "retrieval":
                prev_count_query = prev_count_query.filter(
                    FeedbackAnalysis.issue_type.in_(["retrieval", "both"])
                )
            elif rule.rule_type == "generation":
                prev_count_query = prev_count_query.filter(
                    FeedbackAnalysis.issue_type.in_(["generation", "both"])
                )

            prev_count = prev_count_query.count()

            # 计算变化率
            if prev_count > 0:
                change_rate = (count - prev_count) / prev_count * 100
            else:
                change_rate = 0 if count == 0 else -100

            effect_evaluation = {
                "rule_id": rule_id,
                "rule_name": rule.rule_name,
                "rule_type": rule.rule_type,
                "time_window_hours": time_window_hours,
                "current_issue_count": count,
                "previous_issue_count": prev_count,
                "change_rate": round(change_rate, 2),
                "trend": "improving" if change_rate < 0 else "worsening" if change_rate > 0 else "stable",
                "evaluation_time": datetime.now().isoformat()
            }

            logger.info(
                "规则效果评估完成",
                extra=effect_evaluation
            )

            return effect_evaluation

        finally:
            db.close()

    def generate_optimization_suggestion(
        self,
        analysis: Any,
        rules: List[Any]
    ) -> Optional[Dict[str, Any]]:
        """
        根据分析结果生成优化建议

        Args:
            analysis: 反馈分析记录
            rules: 当前规则列表

        Returns:
            优化建议，如果没有建议则返回None
        """
        # 检查是否已存在相关规则
        issue_category = analysis.issue_category if hasattr(analysis, "issue_category") else None
        issue_type = analysis.issue_type if hasattr(analysis, "issue_type") else None

        for rule in rules:
            # 检查触发条件是否匹配
            trigger_conditions = self._parse_trigger_condition(rule.trigger_condition)
            for condition in trigger_conditions:
                if condition.condition_type in ["issue_category", "issue_type"]:
                    if self._evaluate_condition(analysis, condition):
                        return None  # 已存在匹配规则

        # 生成新规则建议
        suggestion = {
            "suggestion_type": "new_rule",
            "issue_category": issue_category,
            "issue_type": issue_type,
            "rule_config": self._generate_rule_config(analysis),
            "trigger_condition": self._generate_trigger_condition(analysis),
            "priority": self._calculate_priority(analysis),
        }

        return suggestion

    def _generate_rule_config(
        self,
        analysis: Any
    ) -> Dict[str, Any]:
        """根据分析结果生成规则配置"""
        issue_type = analysis.issue_type if hasattr(analysis, "issue_type") else None

        if issue_type == "retrieval":
            retrieval_score = analysis.retrieval_score if hasattr(analysis, "retrieval_score") else 3
            return {
                "min_score_threshold": 0.3 if retrieval_score < 3 else 0.5,
                "top_k": 20,
                "fusion_weight": {"vector": 0.6, "keyword": 0.4}
            }
        elif issue_type == "generation":
            return {
                "prompt_template": "请基于以下上下文，详细回答用户问题...",
                "max_context_tokens": 4000,
                "temperature": 0.7
            }
        else:
            return {}

    def _generate_trigger_condition(
        self,
        analysis: Any
    ) -> Dict[str, Any]:
        """根据分析结果生成触发条件"""
        issue_category = analysis.issue_category if hasattr(analysis, "issue_category") else None

        return {
            "issue_category__eq": issue_category,
            "occurrence_count__gte": 10,
            "time_window_hours": 24
        }

    def _calculate_priority(
        self,
        analysis: Any
    ) -> int:
        """根据分析结果计算优先级"""
        issue_type = analysis.issue_type if hasattr(analysis, "issue_type") else None
        retrieval_score = analysis.retrieval_score if hasattr(analysis, "retrieval_score") else 3

        # 检索问题且分数很低，优先级高
        if issue_type == "retrieval" and retrieval_score <= 2:
            return 1
        # 生成问题，优先级中
        elif issue_type == "generation":
            return 2
        # 综合问题，优先级中
        elif issue_type == "both":
            return 2
        # 其他情况，优先级低
        else:
            return 3


# 全局引擎实例
_optimization_engine: Optional[OptimizationRuleEngine] = None


def get_optimization_engine() -> OptimizationRuleEngine:
    """获取优化规则引擎实例"""
    global _optimization_engine
    if _optimization_engine is None:
        _optimization_engine = OptimizationRuleEngine()
    return _optimization_engine
