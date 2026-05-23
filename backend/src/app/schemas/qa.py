# -*- coding: utf-8 -*-
"""
问答数据模型

本模块定义问答相关的Pydantic数据模型。
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from app.schemas.retrieval import RetrievalResult


class QARequest(BaseModel):
    """问答请求模型"""
    question: str = Field(..., description="用户问题", min_length=1)
    session_id: Optional[str] = Field(None, description="会话ID")
    user_id: Optional[int] = Field(None, description="用户ID")
    tenant_id: int = Field(1, description="租户ID")
    use_rerank: bool = Field(True, description="是否使用重排")
    top_k: Optional[int] = Field(20, description="检索TopK")
    rerank_top_k: Optional[int] = Field(10, description="重排后TopK")
    max_context_tokens: Optional[int] = Field(4000, description="最大上下文Token数")
    temperature: Optional[float] = Field(0.7, ge=0.0, le=2.0, description="LLM温度参数")
    doc_ids: Optional[List[int]] = Field(None, description="限定文档ID列表")


class QAResult(BaseModel):
    """问答结果模型"""
    qa_id: int = Field(..., description="问答记录ID")
    question: str = Field(..., description="用户问题")
    answer: str = Field(..., description="生成的答案")
    references: List[RetrievalResult] = Field(..., description="引用来源")
    session_id: str = Field(..., description="会话ID")
    total_time_ms: int = Field(..., description="总耗时(毫秒)")
    retrieval_time_ms: int = Field(..., description="检索耗时(毫秒)")
    rerank_time_ms: int = Field(0, description="重排耗时(毫秒)")
    context_time_ms: int = Field(0, description="上下文组装耗时(毫秒)")
    generation_time_ms: int = Field(..., description="生成耗时(毫秒)")


class QAResponse(BaseModel):
    """问答响应模型"""
    result: QAResult = Field(..., description="问答结果")


class FeedbackRequest(BaseModel):
    """反馈请求模型"""
    feedback: str = Field(..., description="反馈内容: helpful/not_helpful")
    quality_score: Optional[int] = Field(None, ge=1, le=5, description="质量评分")
    remark: Optional[str] = Field(None, description="反馈备注")


class FeedbackResponse(BaseModel):
    """反馈响应模型"""
    qa_id: int = Field(..., description="问答记录ID")
    feedback: str = Field(..., description="反馈内容")
    quality_score: Optional[int] = Field(None, description="质量评分")
    remark: Optional[str] = Field(None, description="反馈备注")


class HistoryItem(BaseModel):
    """历史记录项模型"""
    id: int = Field(..., description="记录ID")
    question: str = Field(..., description="用户问题")
    answer: str = Field(..., description="生成的答案")
    quality_score: Optional[int] = Field(None, description="质量评分")
    feedback: Optional[str] = Field(None, description="用户反馈")
    created_at: datetime = Field(..., description="创建时间")

    class Config:
        from_attributes = True


class SessionInfo(BaseModel):
    """会话信息模型"""
    session_id: str = Field(..., description="会话ID")
    user_id: Optional[int] = Field(None, description="用户ID")
    question_count: int = Field(..., description="问题数量")
    last_question: Optional[str] = Field(None, description="最后问题")
    last_answer_time: Optional[datetime] = Field(None, description="最后回答时间")
    created_at: datetime = Field(..., description="创建时间")

    class Config:
        from_attributes = True


class QAStatistics(BaseModel):
    """问答统计模型"""
    total_count: int = Field(0, description="总问答数")
    avg_quality_score: float = Field(0.0, description="平均质量评分")
    helpful_count: int = Field(0, description="有帮助数量")
    not_helpful_count: int = Field(0, description="无帮助数量")
    avg_retrieval_time_ms: float = Field(0.0, description="平均检索耗时(毫秒)")
    avg_generation_time_ms: float = Field(0.0, description="平均生成耗时(毫秒)")


# ========== 反馈分析相关 Schema ==========

class FeedbackSubmitRequest(BaseModel):
    """反馈提交请求模型"""
    qa_id: int = Field(..., description="问答记录ID")
    feedback: int = Field(..., description="反馈值：1-满意 0-不满意")
    feedback_reason: Optional[str] = Field(None, description="反馈原因")
    quality_score: Optional[int] = Field(None, ge=1, le=5, description="质量评分")


class FeedbackSubmitResponse(BaseModel):
    """反馈提交响应模型"""
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="反馈消息")
    analysis_id: Optional[int] = Field(None, description="分析记录ID（仅负面反馈时）")


class FeedbackAnalysisResult(BaseModel):
    """反馈分析结果模型"""
    id: int = Field(..., description="分析ID")
    qa_log_id: int = Field(..., description="问答日志ID")
    issue_type: Optional[str] = Field(None, description="问题类型")
    issue_category: Optional[str] = Field(None, description="问题分类")
    issue_description: Optional[str] = Field(None, description="问题描述")
    suggestions: Optional[List[str]] = Field(None, description="改进建议列表")
    suggestion_type: Optional[str] = Field(None, description="建议类型")
    handled_status: int = Field(0, description="处理状态")
    created_at: datetime = Field(..., description="创建时间")

    class Config:
        from_attributes = True


class QALogDetail(BaseModel):
    """问答日志详情模型"""
    id: int = Field(..., description="日志ID")
    user_id: Optional[int] = Field(None, description="用户ID")
    session_id: Optional[str] = Field(None, description="会话ID")
    question: str = Field(..., description="用户问题")
    answer: Optional[str] = Field(None, description="生成的答案")
    references: Optional[List[Dict[str, Any]]] = Field(None, description="引用来源")
    feedback: Optional[str] = Field(None, description="用户反馈")
    feedback_reason: Optional[str] = Field(None, description="反馈原因")
    quality_score: Optional[int] = Field(None, description="质量评分")
    retrieval_time_ms: Optional[int] = Field(None, description="检索耗时")
    generation_time_ms: Optional[int] = Field(None, description="生成耗时")
    total_time_ms: Optional[int] = Field(None, description="总耗时")
    created_at: datetime = Field(..., description="创建时间")
    analysis: Optional[FeedbackAnalysisResult] = Field(None, description="分析结果")

    class Config:
        from_attributes = True


class QALogQueryRequest(BaseModel):
    """问答日志查询请求模型"""
    tenant_id: int = Field(1, description="租户ID")
    user_id: Optional[int] = Field(None, description="用户ID")
    session_id: Optional[str] = Field(None, description="会话ID")
    start_date: Optional[str] = Field(None, description="开始日期 YYYY-MM-DD")
    end_date: Optional[str] = Field(None, description="结束日期 YYYY-MM-DD")
    has_feedback: Optional[bool] = Field(None, description="是否有反馈")
    feedback_value: Optional[int] = Field(None, description="反馈值：1-满意 0-不满意")
    min_score: Optional[int] = Field(None, ge=1, le=5, description="最低评分")
    max_score: Optional[int] = Field(None, ge=1, le=5, description="最高评分")
    keyword: Optional[str] = Field(None, description="关键词搜索")
    page_no: int = Field(1, ge=1, description="页码")
    page_size: int = Field(20, ge=1, le=100, description="每页数量")


class OptimizationRuleModel(BaseModel):
    """优化规则模型"""
    id: int = Field(..., description="规则ID")
    rule_name: str = Field(..., description="规则名称")
    rule_type: str = Field(..., description="规则类型")
    rule_config: Optional[Dict[str, Any]] = Field(None, description="规则配置")
    trigger_condition: Optional[Dict[str, Any]] = Field(None, description="触发条件")
    priority: int = Field(2, description="优先级")
    enabled: bool = Field(True, description="是否启用")
    description: Optional[str] = Field(None, description="规则描述")
    applicable_scope: Optional[Dict[str, Any]] = Field(None, description="应用范围")
    expected_effect: Optional[str] = Field(None, description="预期效果")
    actual_effect: Optional[str] = Field(None, description="实际效果")
    creator_id: Optional[int] = Field(None, description="创建人ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True


class OptimizationRuleRequest(BaseModel):
    """优化规则请求模型"""
    rule_name: str = Field(..., description="规则名称", min_length=1, max_length=200)
    rule_type: str = Field(..., description="规则类型")
    rule_config: Optional[Dict[str, Any]] = Field(None, description="规则配置")
    trigger_condition: Optional[Dict[str, Any]] = Field(None, description="触发条件")
    priority: int = Field(2, ge=1, le=3, description="优先级：1-高 2-中 3-低")
    enabled: bool = Field(True, description="是否启用")
    description: Optional[str] = Field(None, description="规则描述")
    applicable_scope: Optional[Dict[str, Any]] = Field(None, description="应用范围")
    expected_effect: Optional[str] = Field(None, description="预期效果")


class FeedbackStatistics(BaseModel):
    """反馈统计模型"""
    total_count: int = Field(0, description="总反馈数")
    positive_count: int = Field(0, description="正面反馈数")
    negative_count: int = Field(0, description="负面反馈数")
    positive_rate: float = Field(0.0, description="正面反馈率")
    avg_quality_score: float = Field(0.0, description="平均质量评分")
    top_issues: List[Dict[str, Any]] = Field(default_factory=list, description="高频问题类型")
    retrieval_issue_count: int = Field(0, description="检索问题数")
    generation_issue_count: int = Field(0, description="生成问题数")
    pending_analysis_count: int = Field(0, description="待分析数")
    handled_count: int = Field(0, description="已处理数")


# ========== 扩展反馈分析 Schema ==========

class FeedbackAnalysisDetail(BaseModel):
    """反馈分析详情模型（扩展版）"""
    id: int = Field(..., description="分析ID")
    tenant_id: int = Field(..., description="租户ID")
    qa_log_id: int = Field(..., description="问答日志ID")
    feedback_type: Optional[str] = Field(None, description="反馈类型")
    issue_type: Optional[str] = Field(None, description="问题类型")
    issue_category: Optional[str] = Field(None, description="问题分类")
    issue_description: Optional[str] = Field(None, description="问题描述")
    involved_chunks: Optional[List[int]] = Field(None, description="涉及Chunk ID列表")
    involved_documents: Optional[List[int]] = Field(None, description="涉及文档ID列表")
    retrieval_score: Optional[int] = Field(None, description="检索质量评分")
    retrieval_avg_score: Optional[float] = Field(None, description="检索平均分")
    retrieval_result_count: Optional[int] = Field(None, description="检索结果数量")
    retrieval_timeout: Optional[int] = Field(None, description="检索是否超时")
    generation_score: Optional[int] = Field(None, description="生成质量评分")
    suggestions: Optional[List[Dict[str, Any]]] = Field(None, description="改进建议")
    suggestion_type: Optional[str] = Field(None, description="建议类型")
    root_cause: Optional[str] = Field(None, description="根本原因")
    root_cause_type: Optional[str] = Field(None, description="根本原因类型")
    handled_status: int = Field(0, description="处理状态")
    handler_id: Optional[int] = Field(None, description="处理人ID")
    handler_remark: Optional[str] = Field(None, description="处理备注")
    created_at: datetime = Field(..., description="创建时间")

    class Config:
        from_attributes = True


class IssueClassification(BaseModel):
    """问题分类结果模型"""
    issue_type: str = Field(..., description="问题类型")
    issue_category: str = Field(..., description="问题分类")
    confidence: float = Field(..., description="分类置信度")
    reasoning: str = Field(..., description="分类理由")


class RootCauseAnalysis(BaseModel):
    """根本原因分析模型"""
    root_cause_type: str = Field(..., description="原因类型")
    root_cause_description: str = Field(..., description="原因描述")
    evidence: List[str] = Field(default_factory=list, description="支撑证据")
    related_factors: List[str] = Field(default_factory=list, description="相关因素")


class ImprovementSuggestion(BaseModel):
    """改进建议模型"""
    suggestion_type: str = Field(..., description="建议类型")
    priority: int = Field(..., description="优先级")
    description: str = Field(..., description="建议描述")
    action_type: str = Field(..., description="操作类型")
    action_config: Dict[str, Any] = Field(default_factory=dict, description="操作配置")


class FullAnalysisResult(BaseModel):
    """完整分析结果模型"""
    issue_classification: IssueClassification = Field(..., description="问题分类")
    root_cause: RootCauseAnalysis = Field(..., description="根本原因")
    suggestions: List[ImprovementSuggestion] = Field(default_factory=list, description="改进建议")
    involved_chunks: List[int] = Field(default_factory=list, description="涉及Chunk")
    involved_documents: List[int] = Field(default_factory=list, description="涉及文档")
    retrieval_metadata: Dict[str, Any] = Field(default_factory=dict, description="检索元数据")


# ========== 清洗规则优化 Schema ==========

class CleaningOptimizationSuggestion(BaseModel):
    """清洗规则优化建议模型"""
    optimization_type: str = Field(..., description="优化类型")
    rule_name: str = Field(..., description="规则名称")
    rule_type: str = Field(..., description="规则类型")
    rule_config: Dict[str, Any] = Field(..., description="规则配置")
    priority: int = Field(..., description="优先级")
    reason: str = Field(..., description="优化原因")
    problem_pattern: str = Field(..., description="问题模式")


class ProblemPattern(BaseModel):
    """问题模式模型"""
    category: str = Field(..., description="问题分类")
    count: int = Field(..., description="出现次数")
    percentage: float = Field(..., description="占比")
    suggestion: str = Field(..., description="建议")


# ========== 审核相关 Schema ==========

class RuleAuditLog(BaseModel):
    """规则审核日志模型"""
    id: int = Field(..., description="日志ID")
    rule_id: int = Field(..., description="规则ID")
    action: str = Field(..., description="操作类型")
    operator_id: Optional[int] = Field(None, description="操作人ID")
    operator_name: Optional[str] = Field(None, description="操作人姓名")
    before_status: Optional[int] = Field(None, description="操作前状态")
    after_status: Optional[int] = Field(None, description="操作后状态")
    comment: Optional[str] = Field(None, description="审核意见")
    ip_address: Optional[str] = Field(None, description="IP地址")
    created_at: datetime = Field(..., description="创建时间")

    class Config:
        from_attributes = True


class PendingRule(BaseModel):
    """待审核规则模型"""
    id: int = Field(..., description="规则ID")
    rule_name: str = Field(..., description="规则名称")
    rule_type: str = Field(..., description="规则类型")
    rule_config: Optional[Dict[str, Any]] = Field(None, description="规则配置")
    trigger_condition: Optional[Dict[str, Any]] = Field(None, description="触发条件")
    priority: int = Field(..., description="优先级")
    description: Optional[str] = Field(None, description="规则描述")
    expected_effect: Optional[str] = Field(None, description="预期效果")
    creator_id: Optional[int] = Field(None, description="创建人ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True


class RuleEffectEvaluation(BaseModel):
    """规则效果评估模型"""
    rule_id: int = Field(..., description="规则ID")
    rule_name: str = Field(..., description="规则名称")
    rule_type: str = Field(..., description="规则类型")
    time_window_hours: int = Field(..., description="评估时间窗口")
    current_issue_count: int = Field(..., description="当前问题数量")
    previous_issue_count: int = Field(..., description="之前问题数量")
    change_rate: float = Field(..., description="变化率")
    trend: str = Field(..., description="趋势")
    evaluation_time: str = Field(..., description="评估时间")
