# -*- coding: utf-8 -*-
"""
反馈自动分析器

本模块提供反馈自动分析功能，包括：
- 问题类型自动分类
- 根本原因分析
- 改进建议生成
- 触发条件匹配
"""

import json
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from app.common.logging import logger


@dataclass
class IssueClassification:
    """问题分类结果"""
    issue_type: str  # retrieval/generation/both/unknown
    issue_category: str  # 详细分类
    confidence: float  # 分类置信度
    reasoning: str  # 分类理由


@dataclass
class RootCauseAnalysis:
    """根本原因分析结果"""
    root_cause_type: str  # 数据问题/模型问题/配置问题/流程问题
    root_cause_description: str  # 原因描述
    evidence: List[str] = field(default_factory=list)  # 支撑证据
    related_factors: List[str] = field(default_factory=list)  # 相关因素


@dataclass
class ImprovementSuggestion:
    """改进建议"""
    suggestion_type: str  # 建议类型
    priority: int  # 优先级（1-高 3-低）
    description: str  # 建议描述
    action_type: str  # 操作类型
    action_config: Dict[str, Any] = field(default_factory=dict)  # 操作配置


@dataclass
class AnalysisResult:
    """完整分析结果"""
    issue_classification: IssueClassification
    root_cause: RootCauseAnalysis
    suggestions: List[ImprovementSuggestion]
    involved_chunks: List[int] = field(default_factory=list)
    involved_documents: List[int] = field(default_factory=list)
    retrieval_metadata: Dict[str, Any] = field(default_factory=dict)


class FeedbackAnalyzer:
    """
    反馈自动分析器

    分析用户反馈，识别问题类型，分析根本原因，并生成改进建议。
    """

    # 问题类型常量
    ISSUE_TYPE_RETRIEVAL = "retrieval"
    ISSUE_TYPE_GENERATION = "generation"
    ISSUE_TYPE_BOTH = "both"
    ISSUE_TYPE_UNKNOWN = "unknown"

    # 问题分类常量
    ISSUE_CATEGORIES = {
        "retrieval": {
            "empty": "retrieval_empty",
            "inaccurate": "retrieval_inaccurate",
            "irrelevant": "retrieval_irrelevant",
            "timeout": "retrieval_timeout",
            "low_score": "retrieval_low_score",
            "missing_context": "retrieval_missing_context",
        },
        "generation": {
            "incorrect": "answer_incorrect",
            "incomplete": "answer_incomplete",
            "cant_answer": "answer_cant_answer",
            "irrelevant": "answer_irrelevant",
            "too_short": "answer_too_short",
            "hallucination": "answer_hallucination",
            "unclear": "answer_unclear",
        },
        "prompt": {
            "ineffective": "prompt_ineffective",
            "confusing": "prompt_confusing",
            "missing_context": "prompt_missing_context",
        },
        "context": {
            "insufficient": "context_insufficient",
            "irrelevant": "context_irrelevant",
            "too_much": "context_too_much",
        }
    }

    # 根本原因类型
    ROOT_CAUSE_TYPES = {
        "data": "数据质量问题",
        "model": "模型能力问题",
        "config": "配置参数问题",
        "process": "流程处理问题",
        "user": "用户理解问题",
        "unknown": "未知原因",
    }

    # 关键词到问题分类的映射
    FEEDBACK_KEYWORDS = {
        "不准确": "retrieval_inaccurate",
        "错误": "answer_incorrect",
        "错了": "answer_incorrect",
        "胡说": "answer_hallucination",
        "没找到": "retrieval_empty",
        "找不到": "retrieval_empty",
        "没有": "retrieval_empty",
        "无法回答": "answer_cant_answer",
        "不知道": "answer_cant_answer",
        "不完整": "answer_incomplete",
        "太短": "answer_too_short",
        "长一点": "answer_too_short",
        "详细": "answer_incomplete",
        "无关": "retrieval_irrelevant",
        "跑题": "answer_irrelevant",
        "重复": "answer_irrelevant",
        "超时": "retrieval_timeout",
        "慢": "retrieval_timeout",
        "不清楚": "answer_unclear",
        "混乱": "answer_unclear",
    }

    # 否定回答关键词
    NEGATIVE_PHRASES = [
        "无法", "不能", "不会", "不知道", "不清楚",
        "没有找到", "没有相关", "很抱歉", "对不起",
        "无法回答", "无法提供", "无法确定"
    ]

    def __init__(self):
        """初始化分析器"""
        pass

    def analyze(
        self,
        qa_log: Any,
        feedback_type: int,
        feedback_reason: Optional[str] = None,
        quality_score: Optional[int] = None
    ) -> AnalysisResult:
        """
        分析反馈

        Args:
            qa_log: 问答日志对象
            feedback_type: 反馈类型（1-满意 0-不满意）
            feedback_reason: 反馈原因
            quality_score: 质量评分

        Returns:
            完整分析结果
        """
        logger.info(
            "开始分析反馈",
            extra={
                "qa_id": qa_log.id if hasattr(qa_log, "id") else None,
                "feedback_type": feedback_type,
                "feedback_reason": feedback_reason
            }
        )

        # 1. 问题分类
        issue_classification = self._classify_issue(
            qa_log, feedback_type, feedback_reason, quality_score
        )

        # 2. 根本原因分析
        root_cause = self._analyze_root_cause(
            qa_log, issue_classification
        )

        # 3. 生成改进建议
        suggestions = self._generate_suggestions(
            qa_log, issue_classification, root_cause
        )

        # 4. 提取涉及的文档和Chunk
        involved_chunks, involved_documents, retrieval_metadata = self._extract_involved(
            qa_log
        )

        # 5. 计算检索相关指标
        retrieval_info = self._analyze_retrieval_metrics(qa_log)

        result = AnalysisResult(
            issue_classification=issue_classification,
            root_cause=root_cause,
            suggestions=suggestions,
            involved_chunks=involved_chunks,
            involved_documents=involved_documents,
            retrieval_metadata={**retrieval_metadata, **retrieval_info}
        )

        logger.info(
            "反馈分析完成",
            extra={
                "issue_type": issue_classification.issue_type,
                "issue_category": issue_classification.issue_category,
                "suggestion_count": len(suggestions)
            }
        )

        return result

    def _classify_issue(
        self,
        qa_log: Any,
        feedback_type: int,
        feedback_reason: Optional[str] = None,
        quality_score: Optional[int] = None
    ) -> IssueClassification:
        """
        分类问题类型

        判断依据：
        1. 检索问题：无引用、低相关性分数、检索超时、检索为空
        2. 生成问题：有引用但无法回答、答案过短、答案错误
        3. 综合问题：上述两者都有
        """
        # 如果是正面反馈，不需要分类
        if feedback_type == 1:
            return IssueClassification(
                issue_type=self.ISSUE_TYPE_UNKNOWN,
                issue_category="helpful",
                confidence=1.0,
                reasoning="正面反馈，无需分析问题类型"
            )

        # 分析检索问题
        is_retrieval_issue, retrieval_reason = self._detect_retrieval_issue(qa_log)

        # 分析生成问题
        is_generation_issue, generation_reason = self._detect_generation_issue(qa_log)

        # 如果有用户反馈原因，进一步分析
        if feedback_reason:
            reason_category = self._analyze_feedback_reason(feedback_reason)
            if reason_category:
                if "retrieval" in reason_category:
                    is_retrieval_issue = True
                    retrieval_reason = f"用户反馈：{feedback_reason}"
                elif "answer" in reason_category or "prompt" in reason_category:
                    is_generation_issue = True
                    generation_reason = f"用户反馈：{feedback_reason}"

        # 综合判断
        if is_retrieval_issue and is_generation_issue:
            return IssueClassification(
                issue_type=self.ISSUE_TYPE_BOTH,
                issue_category="retrieval_and_generation",
                confidence=0.8,
                reasoning=f"检索问题：{retrieval_reason}；生成问题：{generation_reason}"
            )
        elif is_retrieval_issue:
            category = self._determine_retrieval_category(qa_log, retrieval_reason)
            return IssueClassification(
                issue_type=self.ISSUE_TYPE_RETRIEVAL,
                issue_category=category,
                confidence=0.9,
                reasoning=retrieval_reason
            )
        elif is_generation_issue:
            category = self._determine_generation_category(qa_log, generation_reason)
            return IssueClassification(
                issue_type=self.ISSUE_TYPE_GENERATION,
                issue_category=category,
                confidence=0.9,
                reasoning=generation_reason
            )
        else:
            # 无法明确判断，使用默认分类
            return IssueClassification(
                issue_type=self.ISSUE_TYPE_UNKNOWN,
                issue_category="unknown",
                confidence=0.5,
                reasoning="无法明确判断问题类型，需要人工审核"
            )

    def _detect_retrieval_issue(
        self,
        qa_log: Any
    ) -> Tuple[bool, str]:
        """
        检测检索问题

        Returns:
            (是否有问题, 问题描述)
        """
        # 检查是否有引用
        references = self._get_references(qa_log)

        if not references or len(references) == 0:
            return True, "检索结果为空，未找到相关文档"

        # 检查检索超时
        if hasattr(qa_log, "retrieval_time_ms") and qa_log.retrieval_time_ms:
            if qa_log.retrieval_time_ms > 5000:
                return True, f"检索超时，耗时{qa_log.retrieval_time_ms}毫秒"

        # 检查相关性分数
        scores = [ref.get("score", 0) for ref in references if ref.get("score")]
        if scores:
            avg_score = sum(scores) / len(scores)
            max_score = max(scores)

            if avg_score < 0.2:
                return True, f"检索相关性过低，平均分{avg_score:.2f}"
            if max_score < 0.3:
                return True, f"检索相关性过低，最高分{max_score:.2f}"

        return False, ""

    def _detect_generation_issue(
        self,
        qa_log: Any
    ) -> Tuple[bool, str]:
        """
        检测生成问题

        Returns:
            (是否有问题, 问题描述)
        """
        # 检查是否有答案
        if not qa_log.answer or not qa_log.answer.strip():
            return True, "未生成答案"

        answer = qa_log.answer.strip()
        answer_lower = answer.lower()

        # 检查是否是否定回答
        for phrase in self.NEGATIVE_PHRASES:
            if phrase in answer_lower:
                return True, f"答案包含否定表述：{phrase}"

        # 检查答案长度
        if len(answer) < 10:
            return True, f"答案过短，仅{len(answer)}个字符"

        # 检查是否有有效引用但仍然无法回答
        references = self._get_references(qa_log)
        if references and len(references) > 0:
            # 有引用但是否定回答，说明生成有问题
            for phrase in self.NEGATIVE_PHRASES:
                if phrase in answer_lower:
                    return True, f"有{len(references)}个相关引用，但仍然无法生成有效答案"

        return False, ""

    def _analyze_feedback_reason(self, reason: str) -> Optional[str]:
        """分析反馈原因中的关键词"""
        if not reason:
            return None

        reason_lower = reason.lower()
        for keyword, category in self.FEEDBACK_KEYWORDS.items():
            if keyword in reason_lower:
                return category

        return None

    def _determine_retrieval_category(
        self,
        qa_log: Any,
        reasoning: str
    ) -> str:
        """确定检索问题详细分类"""
        references = self._get_references(qa_log)

        if not references or len(references) == 0:
            return self.ISSUE_CATEGORIES["retrieval"]["empty"]

        if "超时" in reasoning:
            return self.ISSUE_CATEGORIES["retrieval"]["timeout"]

        if "过低" in reasoning:
            return self.ISSUE_CATEGORIES["retrieval"]["low_score"]

        if "无关" in reasoning:
            return self.ISSUE_CATEGORIES["retrieval"]["irrelevant"]

        return self.ISSUE_CATEGORIES["retrieval"]["inaccurate"]

    def _determine_generation_category(
        self,
        qa_log: Any,
        reasoning: str
    ) -> str:
        """确定生成问题详细分类"""
        answer = qa_log.answer or ""

        if "无法" in reasoning or "不知道" in reasoning:
            return self.ISSUE_CATEGORIES["generation"]["cant_answer"]
        if "过短" in reasoning:
            return self.ISSUE_CATEGORIES["generation"]["too_short"]
        if "错误" in reasoning or "错了" in reasoning:
            return self.ISSUE_CATEGORIES["generation"]["incorrect"]
        if "不完整" in reasoning or "详细" in reasoning:
            return self.ISSUE_CATEGORIES["generation"]["incomplete"]
        if "无关" in reasoning or "跑题" in reasoning:
            return self.ISSUE_CATEGORIES["generation"]["irrelevant"]
        if "胡说" in reasoning or "幻觉" in reasoning:
            return self.ISSUE_CATEGORIES["generation"]["hallucination"]
        if "不清楚" in reasoning or "混乱" in reasoning:
            return self.ISSUE_CATEGORIES["generation"]["unclear"]

        return self.ISSUE_CATEGORIES["generation"]["incorrect"]

    def _analyze_root_cause(
        self,
        qa_log: Any,
        classification: IssueClassification
    ) -> RootCauseAnalysis:
        """
        分析根本原因

        根据问题分类，分析可能的根本原因类型。
        """
        issue_type = classification.issue_type
        evidence = []
        related_factors = []

        # 根据问题类型分析原因
        if issue_type == self.ISSUE_TYPE_RETRIEVAL:
            evidence, related_factors = self._analyze_retrieval_root_cause(qa_log, classification)
            root_cause_type = "data" if "empty" in classification.issue_category else "config"
        elif issue_type == self.ISSUE_TYPE_GENERATION:
            evidence, related_factors = self._analyze_generation_root_cause(qa_log, classification)
            root_cause_type = "model"
        elif issue_type == self.ISSUE_TYPE_BOTH:
            evidence, related_factors = self._analyze_both_root_cause(qa_log, classification)
            root_cause_type = "process"
        else:
            root_cause_type = "unknown"
            evidence = ["无法确定具体原因"]
            related_factors = ["需要人工审核"]

        root_cause_description = self.ROOT_CAUSE_TYPES.get(root_cause_type, "未知原因")

        return RootCauseAnalysis(
            root_cause_type=root_cause_type,
            root_cause_description=root_cause_description,
            evidence=evidence,
            related_factors=related_factors
        )

    def _analyze_retrieval_root_cause(
        self,
        qa_log: Any,
        classification: IssueClassification
    ) -> Tuple[List[str], List[str]]:
        """分析检索问题的根本原因"""
        evidence = []
        factors = []

        references = self._get_references(qa_log)

        # 无引用情况
        if not references or len(references) == 0:
            evidence.append("检索结果为空")
            factors.append("文档库中可能缺少相关内容")
            factors.append("文档切分可能不合理，导致相关内容被分割")
            factors.append("查询改写可能偏离了原始意图")

            # 检查是否有相关文档
            if hasattr(qa_log, "question") and qa_log.question:
                factors.append(f"问题关键词：{qa_log.question[:50]}...")

        # 低分情况
        else:
            scores = [ref.get("score", 0) for ref in references if ref.get("score")]
            if scores:
                avg_score = sum(scores) / len(scores)
                evidence.append(f"检索平均相关性：{avg_score:.2f}")

                if avg_score < 0.3:
                    factors.append("检索向量模型可能不够准确")
                    factors.append("文档embedding可能需要更新")
                    factors.append("混合检索权重配置可能不合理")

        # 检索时间
        if hasattr(qa_log, "retrieval_time_ms") and qa_log.retrieval_time_ms:
            evidence.append(f"检索耗时：{qa_log.retrieval_time_ms}毫秒")
            if qa_log.retrieval_time_ms > 3000:
                factors.append("检索性能可能需要优化")

        return evidence, factors

    def _analyze_generation_root_cause(
        self,
        qa_log: Any,
        classification: IssueClassification
    ) -> Tuple[List[str], List[str]]:
        """分析生成问题的根本原因"""
        evidence = []
        factors = []

        # 检查答案内容
        if qa_log.answer:
            answer_lower = qa_log.answer.lower()
            evidence.append(f"答案长度：{len(qa_log.answer)}字符")

            for phrase in self.NEGATIVE_PHRASES:
                if phrase in answer_lower:
                    evidence.append(f"包含否定表述：{phrase}")
                    break

        # 检查引用
        references = self._get_references(qa_log)
        if references:
            evidence.append(f"引用数量：{len(references)}")
            if len(references) == 0:
                factors.append("缺少检索结果作为上下文")
        else:
            factors.append("缺少检索结果作为上下文")

        # 根据问题分类进一步分析
        category = classification.issue_category
        if "cant_answer" in category:
            factors.append("Prompt模板可能不够明确")
            factors.append("上下文组装策略可能不合理")
        elif "hallucination" in category:
            factors.append("LLM可能产生幻觉")
            factors.append("上下文中可能缺少明确答案")
        elif "incomplete" in category:
            factors.append("上下文信息可能不够完整")
            factors.append("Prompt可能没有引导生成详细答案")
        elif "irrelevant" in category:
            factors.append("上下文可能包含无关信息")
            factors.append("Prompt可能没有明确约束回答方向")

        return evidence, factors

    def _analyze_both_root_cause(
        self,
        qa_log: Any,
        classification: IssueClassification
    ) -> Tuple[List[str], List[str]]:
        """分析综合问题的根本原因"""
        evidence = []
        factors = []

        # 同时分析检索和生成
        retrieval_evidence, retrieval_factors = self._analyze_retrieval_root_cause(qa_log, classification)
        generation_evidence, generation_factors = self._analyze_generation_root_cause(qa_log, classification)

        evidence.extend(retrieval_evidence)
        evidence.extend(generation_evidence)
        factors.extend(retrieval_factors)
        factors.extend(generation_factors)

        factors.append("可能是检索-生成流程整体需要优化")

        return evidence, factors

    def _generate_suggestions(
        self,
        qa_log: Any,
        classification: IssueClassification,
        root_cause: RootCauseAnalysis
    ) -> List[ImprovementSuggestion]:
        """生成改进建议"""
        suggestions = []
        issue_type = classification.issue_type

        if issue_type == self.ISSUE_TYPE_RETRIEVAL:
            suggestions.extend(self._suggest_retrieval_improvements(qa_log, root_cause))
        elif issue_type == self.ISSUE_TYPE_GENERATION:
            suggestions.extend(self._suggest_generation_improvements(qa_log, root_cause))
        elif issue_type == self.ISSUE_TYPE_BOTH:
            suggestions.extend(self._suggest_both_improvements(qa_log, root_cause))
        else:
            suggestions.append(ImprovementSuggestion(
                suggestion_type="review",
                priority=2,
                description="需要人工审核以确定具体改进方向",
                action_type="manual_review",
                action_config={}
            ))

        return suggestions

    def _suggest_retrieval_improvements(
        self,
        qa_log: Any,
        root_cause: RootCauseAnalysis
    ) -> List[ImprovementSuggestion]:
        """生成检索改进建议"""
        suggestions = []
        category = ""

        references = self._get_references(qa_log)

        # 根据原因类型生成建议
        if "empty" in root_cause.related_factors or not references:
            suggestions.append(ImprovementSuggestion(
                suggestion_type="data",
                priority=1,
                description="建议增加相关文档或优化文档导入流程",
                action_type="suggest_document_import",
                action_config={"keywords": self._extract_keywords(qa_log.question)}
            ))
            suggestions.append(ImprovementSuggestion(
                suggestion_type="chunking",
                priority=1,
                description="建议检查相关文档的切分策略，可能需要调整chunk大小或overlap",
                action_type="adjust_chunking",
                action_config={"suggestion": "检查chunk边界是否合理"}
            ))

        if "embedding" in str(root_cause.related_factors) or any("过低" in f for f in root_cause.related_factors):
            suggestions.append(ImprovementSuggestion(
                suggestion_type="config",
                priority=2,
                description="建议优化向量检索参数，如调整top_k或检索阈值",
                action_type="adjust_retrieval_config",
                action_config={"min_score_threshold": 0.3}
            ))
            suggestions.append(ImprovementSuggestion(
                suggestion_type="model",
                priority=2,
                description="建议评估当前embedding模型的效果，考虑更换或微调",
                action_type="evaluate_embedding",
                action_config={}
            ))

        if "混合检索" in str(root_cause.related_factors):
            suggestions.append(ImprovementSuggestion(
                suggestion_type="config",
                priority=2,
                description="建议优化混合检索的权重配置",
                action_type="adjust_fusion_weight",
                action_config={"vector_weight": 0.7, "keyword_weight": 0.3}
            ))

        # 添加通用建议
        suggestions.append(ImprovementSuggestion(
            suggestion_type="query_rewrite",
            priority=3,
            description="建议检查查询改写策略，确保改写后的查询能准确反映用户意图",
            action_type="review_query_rewrite",
            action_config={}
        ))

        return suggestions

    def _suggest_generation_improvements(
        self,
        qa_log: Any,
        root_cause: RootCauseAnalysis
    ) -> List[ImprovementSuggestion]:
        """生成生成改进建议"""
        suggestions = []
        category = ""

        # 根据原因类型生成建议
        if "Prompt" in str(root_cause.related_factors):
            suggestions.append(ImprovementSuggestion(
                suggestion_type="prompt",
                priority=1,
                description="建议优化Prompt模板，明确引导LLM生成更准确的答案",
                action_type="optimize_prompt",
                action_config={"suggestion": "在Prompt中增加对答案格式和完整性的要求"}
            ))

        if "上下文" in str(root_cause.related_factors):
            suggestions.append(ImprovementSuggestion(
                suggestion_type="context",
                priority=1,
                description="建议优化上下文组装策略，确保关键信息完整",
                action_type="optimize_context",
                action_config={"suggestion": "增加相关上下文的优先级"}
            ))

        if "幻觉" in str(root_cause.related_factors):
            suggestions.append(ImprovementSuggestion(
                suggestion_type="prompt",
                priority=1,
                description="建议在Prompt中增加约束，减少LLM幻觉",
                action_type="add_constraint",
                action_config={"constraints": ["仅基于提供的上下文回答", "如上下文不足请明确说明"]}
            ))

        if "详细" in str(root_cause.related_factors):
            suggestions.append(ImprovementSuggestion(
                suggestion_type="prompt",
                priority=2,
                description="建议在Prompt中明确要求生成详细答案",
                action_type="enhance_prompt",
                action_config={"requirement": "要求包含具体细节和示例"}
            ))

        # 添加检索相关建议（因为生成依赖检索）
        references = self._get_references(qa_log)
        if not references or len(references) == 0:
            suggestions.append(ImprovementSuggestion(
                suggestion_type="retrieval",
                priority=2,
                description="检索结果为空，建议先解决检索问题",
                action_type="improve_retrieval",
                action_config={}
            ))

        return suggestions

    def _suggest_both_improvements(
        self,
        qa_log: Any,
        root_cause: RootCauseAnalysis
    ) -> List[ImprovementSuggestion]:
        """生成综合问题改进建议"""
        suggestions = []

        # 先添加检索建议
        suggestions.extend(self._suggest_retrieval_improvements(qa_log, root_cause))

        # 再添加生成建议
        suggestions.extend(self._suggest_generation_improvements(qa_log, root_cause))

        # 添加综合建议
        suggestions.append(ImprovementSuggestion(
            suggestion_type="process",
            priority=1,
            description="建议整体评估检索-生成流程，识别瓶颈环节",
            action_type="review_pipeline",
            action_config={}
        ))

        return suggestions

    def _extract_involved(
        self,
        qa_log: Any
    ) -> Tuple[List[int], List[int], Dict[str, Any]]:
        """提取涉及的文档和Chunk"""
        chunks = []
        documents = []
        metadata = {}

        references = self._get_references(qa_log)
        if references:
            for ref in references:
                chunk_id = ref.get("chunk_id")
                doc_id = ref.get("document_id") or ref.get("doc_id")

                if chunk_id and chunk_id not in chunks:
                    chunks.append(chunk_id)
                if doc_id and doc_id not in documents:
                    documents.append(doc_id)

                # 收集元数据
                if ref.get("score"):
                    metadata.setdefault("scores", []).append(ref.get("score"))
                if ref.get("source"):
                    metadata.setdefault("sources", []).append(ref.get("source"))

        return chunks, documents, metadata

    def _analyze_retrieval_metrics(self, qa_log: Any) -> Dict[str, Any]:
        """分析检索指标"""
        metrics = {}

        references = self._get_references(qa_log)
        if references:
            scores = [ref.get("score", 0) for ref in references if ref.get("score")]
            if scores:
                metrics["retrieval_avg_score"] = round(sum(scores) / len(scores), 4)
                metrics["retrieval_max_score"] = round(max(scores), 4)
                metrics["retrieval_result_count"] = len(references)

        if hasattr(qa_log, "retrieval_time_ms") and qa_log.retrieval_time_ms:
            metrics["retrieval_time_ms"] = qa_log.retrieval_time_ms
            metrics["retrieval_timeout"] = 1 if qa_log.retrieval_time_ms > 5000 else 0

        return metrics

    def _get_references(self, qa_log: Any) -> List[Dict[str, Any]]:
        """获取引用列表"""
        references = qa_log.references

        if not references:
            return []

        if isinstance(references, str):
            try:
                return json.loads(references)
            except (json.JSONDecodeError, TypeError):
                return []

        if isinstance(references, list):
            return references

        return []

    def _extract_keywords(self, text: Optional[str]) -> List[str]:
        """从文本中提取关键词（简单实现）"""
        if not text:
            return []

        # 简单分词
        keywords = re.findall(r"[\w\u4e00-\u9fa5]{2,}", text)

        # 去除停用词
        stopwords = {"的", "是", "在", "了", "和", "与", "对", "为", "有", "我", "你", "他", "她", "它", "这", "那", "什么", "如何", "怎么", "怎样", "为什么", "可以", "能够"}

        keywords = [k for k in keywords if k not in stopwords and len(k) > 1]

        return keywords[:10]  # 返回前10个关键词


# 全局分析器实例
_feedback_analyzer: Optional[FeedbackAnalyzer] = None


def get_feedback_analyzer() -> FeedbackAnalyzer:
    """获取反馈分析器实例"""
    global _feedback_analyzer
    if _feedback_analyzer is None:
        _feedback_analyzer = FeedbackAnalyzer()
    return _feedback_analyzer
