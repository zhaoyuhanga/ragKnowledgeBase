# -*- coding: utf-8 -*-
"""
清洗规则持续优化服务

本模块实现基于反馈的清洗规则自动优化：
- 问题模式识别
- 规则优化建议生成
- 规则自动调整
- 高频问题统计
"""

import json
import re
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from app.common.logging import logger


@dataclass
class ProblemPattern:
    """问题模式"""
    pattern_id: str  # 模式ID
    pattern_type: str  # 模式类型
    pattern_content: str  # 模式内容（正则表达式或关键词）
    description: str  # 模式描述
    occurrence_count: int  # 发生次数
    severity: int  # 严重程度（1-3）
    affected_documents: List[int] = field(default_factory=list)  # 影响的文档
    affected_chunks: List[int] = field(default_factory=list)  # 影响的Chunk


@dataclass
class RuleOptimization:
    """规则优化建议"""
    optimization_id: Optional[int]  # 优化记录ID
    optimization_type: str  # 优化类型：add/modify/delete/disable
    target_rule_id: Optional[int]  # 目标规则ID（修改/删除时）
    rule_name: str  # 规则名称
    rule_type: str  # 规则类型
    rule_config: Dict[str, Any]  # 规则配置
    priority: int  # 优先级
    reason: str  # 优化原因
    problem_pattern: str  # 对应的问题模式
    status: int  # 状态：0-待处理 1-已审核 2-已拒绝 3-已应用


class CleaningRuleOptimizer:
    """
    清洗规则持续优化服务

    根据用户反馈自动分析问题模式，生成清洗规则优化建议。
    """

    # 问题模式检测规则
    PROBLEM_PATTERNS = {
        "乱码文本": {
            "type": "regex",
            "pattern": r"[\ufffd]{2,}|[\x80-\xff]{3,}",
            "description": "检测到乱码文本，可能需要编码修复",
            "severity": 2
        },
        "页眉残留": {
            "type": "keyword",
            "keywords": ["第页", "Page", "Pages"],
            "description": "页眉清洗不彻底",
            "severity": 1
        },
        "页脚残留": {
            "type": "keyword",
            "keywords": ["©", "版权所有", "未经授权", "Confidential"],
            "description": "页脚清洗不彻底",
            "severity": 1
        },
        "水印残留": {
            "type": "keyword",
            "keywords": ["草稿", "内部资料", "机密", "Draft", "Sample"],
            "description": "水印清洗不彻底",
            "severity": 1
        },
        "广告噪声": {
            "type": "keyword",
            "keywords": ["立即购买", "点击查看", "扫码关注", "推广", "订阅"],
            "description": "广告推广信息未清除",
            "severity": 2
        },
        "控制字符": {
            "type": "regex",
            "pattern": r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]",
            "description": "检测到控制字符",
            "severity": 2
        },
        "零宽字符": {
            "type": "regex",
            "pattern": r"[\u200b-\u200f\ufeff]",
            "description": "检测到零宽字符",
            "severity": 1
        },
        "多余空白": {
            "type": "regex",
            "pattern": r"\s{3,}",
            "description": "检测到多余空白字符",
            "severity": 1
        },
        "编号残留": {
            "type": "keyword",
            "keywords": ["[1]", "[2]", "（1）", "（2）", "1.", "2."],
            "description": "编号格式不一致",
            "severity": 1
        },
        "签名残留": {
            "type": "keyword",
            "keywords": ["签名：", "签字：", "审核：", "日期："],
            "description": "文档签名信息残留",
            "severity": 1
        }
    }

    def __init__(self):
        """初始化优化器"""
        self._db = None

    def analyze_and_suggest(
        self,
        tenant_id: int,
        time_window_days: int = 7,
        min_occurrence: int = 3
    ) -> List[RuleOptimization]:
        """
        分析问题并生成优化建议

        Args:
            tenant_id: 租户ID
            time_window_days: 分析时间窗口（天）
            min_occurrence: 最小出现次数

        Returns:
            优化建议列表
        """
        logger.info(
            "开始分析清洗规则优化建议",
            extra={"tenant_id": tenant_id, "time_window_days": time_window_days}
        )

        # 1. 获取分析数据
        analyses = self._get_analyses(tenant_id, time_window_days)

        if not analyses:
            logger.info("没有反馈数据，跳过分析")
            return []

        # 2. 识别问题模式
        patterns = self._identify_problem_patterns(analyses)

        # 3. 筛选高频问题模式
        frequent_patterns = [p for p in patterns if p.occurrence_count >= min_occurrence]

        # 4. 生成优化建议
        suggestions = self._generate_optimization_suggestions(frequent_patterns)

        logger.info(
            f"清洗规则优化分析完成，生成{len(suggestions)}条建议",
            extra={"tenant_id": tenant_id, "suggestion_count": len(suggestions)}
        )

        return suggestions

    def _get_analyses(
        self,
        tenant_id: int,
        time_window_days: int
    ) -> List[Any]:
        """获取分析数据"""
        from core.database import SessionLocal
        from app.models.feedback import FeedbackAnalysis, OptimizationRule
        from app.models.qa import QALog

        db = SessionLocal()
        try:
            time_threshold = datetime.now() - timedelta(days=time_window_days)

            # 获取检索问题相关的分析记录
            analyses = db.query(FeedbackAnalysis).join(
                QALog, FeedbackAnalysis.qa_log_id == QALog.id
            ).filter(
                QALog.tenant_id == tenant_id,
                FeedbackAnalysis.created_at >= time_threshold,
                FeedbackAnalysis.issue_type.in_(["retrieval", "both"])
            ).all()

            return analyses

        finally:
            db.close()

    def _identify_problem_patterns(
        self,
        analyses: List[Any]
    ) -> List[ProblemPattern]:
        """
        识别问题模式

        Args:
            analyses: 分析记录列表

        Returns:
            问题模式列表
        """
        patterns_found = {}

        for analysis in analyses:
            # 获取涉及的Chunk内容进行模式检测
            if not analysis.involved_chunks:
                continue

            try:
                chunk_ids = json.loads(analysis.involved_chunks) if isinstance(analysis.involved_chunks, str) else analysis.involved_chunks
                doc_ids = json.loads(analysis.involved_documents) if analysis.involved_documents and isinstance(analysis.involved_documents, str) else []

                # 获取Chunk内容进行检测
                chunk_contents = self._get_chunk_contents(chunk_ids)

                # 检测每个模式
                for pattern_name, pattern_config in self.PROBLEM_PATTERNS.items():
                    for content in chunk_contents:
                        if self._match_pattern(content, pattern_config):
                            if pattern_name not in patterns_found:
                                patterns_found[pattern_name] = ProblemPattern(
                                    pattern_id=pattern_name,
                                    pattern_type=pattern_config["type"],
                                    pattern_content=pattern_config.get("pattern", str(pattern_config.get("keywords"))),
                                    description=pattern_config["description"],
                                    occurrence_count=0,
                                    severity=pattern_config["severity"],
                                    affected_documents=[],
                                    affected_chunks=[]
                                )

                            patterns_found[pattern_name].occurrence_count += 1
                            patterns_found[pattern_name].affected_chunks.extend(chunk_ids)
                            patterns_found[pattern_name].affected_documents.extend(doc_ids)

            except Exception as e:
                logger.warning(f"分析Chunk内容时出错: {str(e)}")
                continue

        # 去重
        for pattern in patterns_found.values():
            pattern.affected_chunks = list(set(pattern.affected_chunks))
            pattern.affected_documents = list(set(pattern.affected_documents))

        return list(patterns_found.values())

    def _match_pattern(
        self,
        content: str,
        pattern_config: Dict[str, Any]
    ) -> bool:
        """匹配问题模式"""
        pattern_type = pattern_config.get("type")

        if pattern_type == "regex":
            pattern = pattern_config.get("pattern")
            if pattern and re.search(pattern, content):
                return True

        elif pattern_type == "keyword":
            keywords = pattern_config.get("keywords", [])
            for keyword in keywords:
                if keyword in content:
                    return True

        return False

    def _get_chunk_contents(
        self,
        chunk_ids: List[int]
    ) -> List[str]:
        """获取Chunk内容"""
        from core.database import SessionLocal
        from app.models.chunk import DocumentChunk

        if not chunk_ids:
            return []

        db = SessionLocal()
        try:
            chunks = db.query(DocumentChunk).filter(
                DocumentChunk.id.in_(chunk_ids)
            ).all()

            return [chunk.content for chunk in chunks if chunk.content]

        finally:
            db.close()

    def _generate_optimization_suggestions(
        self,
        patterns: List[ProblemPattern]
    ) -> List[RuleOptimization]:
        """生成优化建议"""
        suggestions = []

        for pattern in patterns:
            # 根据问题模式生成对应规则
            optimization = self._create_optimization_from_pattern(pattern)
            if optimization:
                suggestions.append(optimization)

        # 按严重程度和出现次数排序
        suggestions.sort(key=lambda x: (x.priority, -x.rule_config.get("occurrence_count", 0)))

        return suggestions

    def _create_optimization_from_pattern(
        self,
        pattern: ProblemPattern
    ) -> Optional[RuleOptimization]:
        """根据问题模式创建优化建议"""
        # 根据模式名称选择优化类型和规则配置
        if "乱码" in pattern.pattern_id:
            return RuleOptimization(
                optimization_id=None,
                optimization_type="modify",
                target_rule_id=None,
                rule_name="编码修复增强",
                rule_type="cleaning",
                rule_config={
                    "action": "regex_replace",
                    "patterns": [r"[\ufffd]+", r"[\x80-\xff]{3,}"],
                    "replacement": "",
                    "occurrence_count": pattern.occurrence_count
                },
                priority=3 - pattern.severity,  # 严重程度越高，优先级越高
                reason=pattern.description,
                problem_pattern=pattern.pattern_id,
                status=0
            )

        elif "页眉" in pattern.pattern_id:
            return RuleOptimization(
                optimization_id=None,
                optimization_type="add",
                target_rule_id=None,
                rule_name="增强页眉清洗",
                rule_type="cleaning",
                rule_config={
                    "action": "regex_delete",
                    "patterns": [r"第\s*\d+\s*页", r"Page\s+\d+", r"Pages?\s+\d+"],
                    "priority": 10,
                    "scope": "all",
                    "occurrence_count": pattern.occurrence_count
                },
                priority=3 - pattern.severity,
                reason=pattern.description,
                problem_pattern=pattern.pattern_id,
                status=0
            )

        elif "页脚" in pattern.pattern_id:
            return RuleOptimization(
                optimization_id=None,
                optimization_type="add",
                target_rule_id=None,
                rule_name="增强页脚清洗",
                rule_type="cleaning",
                rule_config={
                    "action": "regex_delete",
                    "patterns": [r"©\s*\d{4}", r"版权所有", r"未经授权", r"Confidential"],
                    "priority": 11,
                    "scope": "all",
                    "occurrence_count": pattern.occurrence_count
                },
                priority=3 - pattern.severity,
                reason=pattern.description,
                problem_pattern=pattern.pattern_id,
                status=0
            )

        elif "水印" in pattern.pattern_id:
            return RuleOptimization(
                optimization_id=None,
                optimization_type="add",
                target_rule_id=None,
                rule_name="增强水印清洗",
                rule_type="cleaning",
                rule_config={
                    "action": "regex_delete",
                    "patterns": [r"^草稿$", r"^内部资料$", r"^机密$", r"^Draft$", r"^Sample$"],
                    "priority": 12,
                    "scope": "all",
                    "occurrence_count": pattern.occurrence_count
                },
                priority=3 - pattern.severity,
                reason=pattern.description,
                problem_pattern=pattern.pattern_id,
                status=0
            )

        elif "广告" in pattern.pattern_id:
            return RuleOptimization(
                optimization_id=None,
                optimization_type="add",
                target_rule_id=None,
                rule_name="增强广告清洗",
                rule_type="cleaning",
                rule_config={
                    "action": "regex_delete",
                    "patterns": [r"立即购买", r"点击查看", r"扫码.*关注", r"推广", r"订阅", r"优惠.*截止"],
                    "priority": 30,
                    "scope": "all",
                    "occurrence_count": pattern.occurrence_count
                },
                priority=3 - pattern.severity,
                reason=pattern.description,
                problem_pattern=pattern.pattern_id,
                status=0
            )

        elif "控制字符" in pattern.pattern_id:
            return RuleOptimization(
                optimization_id=None,
                optimization_type="modify",
                target_rule_id=None,
                rule_name="控制字符清理增强",
                rule_type="cleaning",
                rule_config={
                    "action": "regex_replace",
                    "pattern": r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]",
                    "replacement": "",
                    "priority": 5,
                    "scope": "all",
                    "occurrence_count": pattern.occurrence_count
                },
                priority=3 - pattern.severity,
                reason=pattern.description,
                problem_pattern=pattern.pattern_id,
                status=0
            )

        elif "零宽字符" in pattern.pattern_id:
            return RuleOptimization(
                optimization_id=None,
                optimization_type="add",
                target_rule_id=None,
                rule_name="零宽字符清理",
                rule_type="cleaning",
                rule_config={
                    "action": "regex_replace",
                    "pattern": r"[\u200b-\u200f\ufeff]",
                    "replacement": "",
                    "priority": 6,
                    "scope": "all",
                    "occurrence_count": pattern.occurrence_count
                },
                priority=3 - pattern.severity,
                reason=pattern.description,
                problem_pattern=pattern.pattern_id,
                status=0
            )

        elif "多余空白" in pattern.pattern_id:
            return RuleOptimization(
                optimization_id=None,
                optimization_type="modify",
                target_rule_id=None,
                rule_name="空白归一化增强",
                rule_type="cleaning",
                rule_config={
                    "action": "regex_replace",
                    "pattern": r"\s{3,}",
                    "replacement": " ",
                    "priority": 20,
                    "scope": "all",
                    "occurrence_count": pattern.occurrence_count
                },
                priority=3 - pattern.severity,
                reason=pattern.description,
                problem_pattern=pattern.pattern_id,
                status=0
            )

        return None

    def get_high_frequency_patterns(
        self,
        tenant_id: int,
        time_window_days: int = 7,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        获取高频问题模式

        Args:
            tenant_id: 租户ID
            time_window_days: 时间窗口
            limit: 返回数量限制

        Returns:
            高频问题模式列表
        """
        # 简单统计：按问题分类计数
        from core.database import SessionLocal
        from app.models.feedback import FeedbackAnalysis
        from app.models.qa import QALog
        from sqlalchemy import func

        db = SessionLocal()
        try:
            time_threshold = datetime.now() - timedelta(days=time_window_days)

            results = db.query(
                FeedbackAnalysis.issue_category,
                func.count(FeedbackAnalysis.id).label("count")
            ).join(
                QALog, FeedbackAnalysis.qa_log_id == QALog.id
            ).filter(
                QALog.tenant_id == tenant_id,
                FeedbackAnalysis.created_at >= time_threshold,
                FeedbackAnalysis.issue_category.isnot(None)
            ).group_by(
                FeedbackAnalysis.issue_category
            ).order_by(
                func.count(FeedbackAnalysis.id).desc()
            ).limit(limit).all()

            total = sum(r.count for r in results) or 1

            return [
                {
                    "category": r.issue_category,
                    "count": r.count,
                    "percentage": round(r.count / total * 100, 2),
                    "suggestion": self._get_suggestion_for_category(r.issue_category)
                }
                for r in results
            ]

        finally:
            db.close()

    def _get_suggestion_for_category(
        self,
        category: Optional[str]
    ) -> str:
        """获取问题分类的建议"""
        suggestions_map = {
            "retrieval_empty": "建议检查相关文档是否已导入，或优化检索关键词",
            "retrieval_inaccurate": "建议优化检索参数或调整向量模型",
            "retrieval_irrelevant": "建议优化查询改写或调整混合检索权重",
            "retrieval_timeout": "建议检查系统性能或增加缓存",
            "answer_cant_answer": "建议检查上下文是否包含相关信息，或优化Prompt",
            "answer_incorrect": "建议检查LLM配置或优化Prompt模板",
            "answer_incomplete": "建议要求生成更详细的答案",
            "answer_irrelevant": "建议优化Prompt引导或调整上下文组装策略",
        }

        return suggestions_map.get(category, "建议人工审核以确定具体改进方向")

    def apply_optimization(
        self,
        optimization: RuleOptimization,
        operator_id: int
    ) -> bool:
        """
        应用优化建议

        Args:
            optimization: 优化建议
            operator_id: 操作人ID

        Returns:
            是否成功
        """
        from core.database import SessionLocal
        from app.models.cleaning import CleaningRule
        from app.models.feedback import CleaningRuleOptimization

        db = SessionLocal()
        try:
            # 创建清洗规则优化记录
            cleaning_opt = CleaningRuleOptimization(
                tenant_id=1,  # TODO: 从上下文获取
                source_analysis_id=None,
                optimize_type=optimization.optimization_type,
                rule_name=optimization.rule_name,
                rule_type=optimization.rule_type,
                rule_config=json.dumps(optimization.rule_config, ensure_ascii=False),
                priority=optimization.priority,
                status=CleaningRuleOptimization.STATUS_APPLIED,
                applied_by=operator_id,
                applied_at=datetime.now(),
                creator_id=operator_id
            )
            db.add(cleaning_opt)

            # 如果是新增或修改规则，创建或更新清洗规则
            if optimization.optimization_type in ["add", "modify"]:
                self._create_or_update_cleaning_rule(
                    db, optimization, operator_id
                )

            # 更新优化记录状态
            cleaning_opt.status = CleaningRuleOptimization.STATUS_APPLIED
            cleaning_opt.applied_at = datetime.now()
            cleaning_opt.applied_by = operator_id

            db.commit()

            logger.info(
                f"清洗规则优化已应用: {optimization.rule_name}",
                extra={
                    "optimization_type": optimization.optimization_type,
                    "operator_id": operator_id
                }
            )

            return True

        except Exception as e:
            db.rollback()
            logger.error(f"应用清洗规则优化失败: {str(e)}")
            return False

        finally:
            db.close()

    def _create_or_update_cleaning_rule(
        self,
        db,
        optimization: RuleOptimization,
        operator_id: int
    ) -> Optional[int]:
        """创建或更新清洗规则"""
        from app.models.cleaning import CleaningRule

        config = optimization.rule_config
        action = config.get("action", "regex_delete")
        patterns = config.get("patterns", [])
        pattern = config.get("pattern", "")
        replacement = config.get("replacement", "")

        # 根据action类型选择规则类型
        if action == "regex_delete":
            rule_type = "regex_delete"
        elif action == "regex_replace":
            rule_type = "regex_replace"
        else:
            rule_type = action

        # 创建规则
        rule = CleaningRule(
            name=optimization.rule_name,
            rule_type=rule_type,
            rule_config={
                "patterns": patterns,
                "pattern": pattern,
                "replacement": replacement,
                "is_enabled": 1
            },
            priority=config.get("priority", 100),
            is_enabled=1,
            scope=config.get("scope", "all"),
            description=optimization.reason,
            creator_id=operator_id,
            creator_name=f"自动优化-{optimization.problem_pattern}"
        )

        db.add(rule)
        db.flush()

        logger.info(
            f"创建清洗规则: {optimization.rule_name}",
            extra={"rule_id": rule.id, "rule_type": rule_type}
        )

        return rule.id


# 全局服务实例
_cleaning_optimizer: Optional[CleaningRuleOptimizer] = None


def get_cleaning_rule_optimizer() -> CleaningRuleOptimizer:
    """获取清洗规则优化器实例"""
    global _cleaning_optimizer
    if _cleaning_optimizer is None:
        _cleaning_optimizer = CleaningRuleOptimizer()
    return _cleaning_optimizer
