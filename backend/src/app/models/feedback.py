# -*- coding: utf-8 -*-
"""
反馈分析数据模型

本模块定义反馈分析相关的数据模型：
- FeedbackAnalysis: 反馈分析表
- OptimizationRule: 优化规则表
- RuleAuditLog: 规则审核日志表
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, DateTime, BigInteger, String, Text, Index

from core.database import Base


class FeedbackAnalysis(Base):
    """
    反馈分析表

    存储用户反馈的分析结果，包括问题分类、改进建议等。
    支持多种反馈类型：点赞、点踩、具体问题等。
    """

    # 反馈类型常量
    FEEDBACK_TYPE_HELPFUL = "helpful"
    FEEDBACK_TYPE_NOT_HELPFUL = "not_helpful"
    FEEDBACK_TYPE_ACCURATE = "accurate"
    FEEDBACK_TYPE_INACCURATE = "inaccurate"
    FEEDBACK_TYPE_CANT_ANSWER = "cant_answer"
    FEEDBACK_TYPE_INCOMPLETE = "incomplete"
    FEEDBACK_TYPE_IRRELEVANT = "irrelevant"

    # 问题类型常量
    ISSUE_TYPE_RETRIEVAL = "retrieval"
    ISSUE_TYPE_GENERATION = "generation"
    ISSUE_TYPE_BOTH = "both"
    ISSUE_TYPE_UNKNOWN = "unknown"

    # 问题分类常量
    ISSUE_CATEGORY_RETRIEVAL_INACCURATE = "retrieval_inaccurate"
    ISSUE_CATEGORY_RETRIEVAL_EMPTY = "retrieval_empty"
    ISSUE_CATEGORY_RETRIEVAL_IRRELEVANT = "retrieval_irrelevant"
    ISSUE_CATEGORY_RETRIEVAL_TIMEOUT = "retrieval_timeout"
    ISSUE_CATEGORY_ANSWER_INCORRECT = "answer_incorrect"
    ISSUE_CATEGORY_ANSWER_INCOMPLETE = "answer_incomplete"
    ISSUE_CATEGORY_ANSWER_CANT_ANSWER = "answer_cant_answer"
    ISSUE_CATEGORY_ANSWER_IRRELEVANT = "answer_irrelevant"
    ISSUE_CATEGORY_PROMPT_INEFFECTIVE = "prompt_ineffective"
    ISSUE_CATEGORY_CONTEXT_INSUFFICIENT = "context_insufficient"

    __tablename__ = "feedback_analysis"

    # 主键ID
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="主键ID")

    # 租户ID
    tenant_id = Column(BigInteger, default=1, nullable=False, index=True, comment="租户ID")

    # 问答日志ID（关联qa_logs表）
    qa_log_id = Column(BigInteger, nullable=False, index=True, comment="问答日志ID")

    # 反馈类型：helpful/not_helpful/accurate/inaccurate/cant_answer/incomplete/irrelevant
    feedback_type = Column(String(50), nullable=True, comment="反馈类型")

    # 问题类型：retrieval、generation、both、unknown
    issue_type = Column(String(50), nullable=True, comment="问题类型")

    # 问题分类：检索不准确、答案错误、答案不完整、无法回答、无引用等
    issue_category = Column(String(100), nullable=True, comment="问题分类")

    # 问题描述
    issue_description = Column(Text, nullable=True, comment="问题描述")

    # 涉及Chunk ID列表（JSON格式）
    involved_chunks = Column(Text, nullable=True, comment="涉及Chunk ID列表")

    # 涉及文档ID列表（JSON格式）
    involved_documents = Column(Text, nullable=True, comment="涉及文档ID列表")

    # 检索质量评分（1-5）
    retrieval_score = Column(BigInteger, nullable=True, comment="检索质量评分")

    # 生成质量评分（1-5）
    generation_score = Column(BigInteger, nullable=True, comment="生成质量评分")

    # 检索平均分
    retrieval_avg_score = Column(BigInteger, nullable=True, comment="检索平均分")

    # 检索结果数量
    retrieval_result_count = Column(BigInteger, nullable=True, comment="检索结果数量")

    # 检索超时标识
    retrieval_timeout = Column(BigInteger, nullable=True, comment="检索是否超时")

    # 改进建议列表（JSON格式）
    suggestions = Column(Text, nullable=True, comment="改进建议列表")

    # 建议类型：增加训练数据、优化检索策略、调整Prompt、改进清洗规则、调整切分参数
    suggestion_type = Column(String(100), nullable=True, comment="建议类型")

    # 根本原因分析
    root_cause = Column(Text, nullable=True, comment="根本原因分析")

    # 根本原因类型
    root_cause_type = Column(String(50), nullable=True, comment="根本原因类型")

    # 是否已处理：0-未处理 1-已处理 2-已忽略
    handled_status = Column(BigInteger, default=0, comment="处理状态")

    # 处理人ID
    handler_id = Column(BigInteger, nullable=True, comment="处理人ID")

    # 处理时间
    handled_at = Column(DateTime, nullable=True, comment="处理时间")

    # 处理备注
    handler_remark = Column(Text, nullable=True, comment="处理备注")

    # 创建时间
    created_at = Column(DateTime, default=datetime.now, nullable=False, comment="创建时间")

    # 索引定义
    __table_args__ = (
        Index("idx_feedback_analysis_qa_log_id", "qa_log_id"),
        Index("idx_feedback_analysis_issue_type", "issue_type"),
        Index("idx_feedback_analysis_handled_status", "handled_status"),
        Index("idx_feedback_analysis_feedback_type", "feedback_type"),
        Index("idx_feedback_analysis_tenant_id", "tenant_id"),
        Index("idx_feedback_analysis_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        """返回反馈分析对象的字符串表示"""
        return f"<FeedbackAnalysis(id={self.id}, qa_log_id={self.qa_log_id}, issue_type={self.issue_type})>"


class OptimizationRule(Base):
    """
    优化规则表

    存储基于反馈分析产生的优化规则。
    """

    # 规则类型常量
    RULE_TYPE_CLEANING = "cleaning"
    RULE_TYPE_CHUNKING = "chunking"
    RULE_TYPE_RETRIEVAL = "retrieval"
    RULE_TYPE_RERANK = "rerank"
    RULE_TYPE_PROMPT = "prompt"

    # 规则状态常量
    STATUS_DRAFT = 0
    STATUS_PENDING_APPROVAL = 1
    STATUS_APPROVED = 2
    STATUS_REJECTED = 3
    STATUS_ENABLED = 4
    STATUS_DISABLED = 5

    __tablename__ = "optimization_rules"

    # 主键ID
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="主键ID")

    # 租户ID
    tenant_id = Column(BigInteger, default=1, nullable=False, index=True, comment="租户ID")

    # 规则名称
    rule_name = Column(String(200), nullable=False, comment="规则名称")

    # 规则类型：cleaning、chunking、retrieval、rerank、prompt
    rule_type = Column(String(50), nullable=False, comment="规则类型")

    # 规则状态：0-草稿 1-待审核 2-已审核 3-已拒绝 4-已启用 5-已禁用
    status = Column(BigInteger, default=0, comment="规则状态")

    # 规则配置（JSON格式）
    rule_config = Column(Text, nullable=True, comment="规则配置")

    # 触发条件（JSON格式）
    trigger_condition = Column(Text, nullable=True, comment="触发条件")

    # 优先级：1-高 2-中 3-低
    priority = Column(BigInteger, default=2, comment="优先级")

    # 启用状态：0-禁用 1-启用
    enabled = Column(BigInteger, default=1, comment="启用状态")

    # 规则描述
    description = Column(Text, nullable=True, comment="规则描述")

    # 应用范围（JSON格式）：文档类型、业务线等
    applicable_scope = Column(Text, nullable=True, comment="应用范围")

    # 预期效果
    expected_effect = Column(Text, nullable=True, comment="预期效果")

    # 实际效果评估
    actual_effect = Column(Text, nullable=True, comment="实际效果评估")

    # 审核信息
    approved_by = Column(BigInteger, nullable=True, comment="审核人ID")
    approved_at = Column(DateTime, nullable=True, comment="审核时间")
    approval_comment = Column(Text, nullable=True, comment="审核意见")

    # 创建人ID
    creator_id = Column(BigInteger, nullable=True, comment="创建人ID")

    # 最后修改人ID
    updater_id = Column(BigInteger, nullable=True, comment="最后修改人ID")

    # 创建时间
    created_at = Column(DateTime, default=datetime.now, nullable=False, comment="创建时间")

    # 更新时间
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False, comment="更新时间")

    # 来源分析ID（关联到触发该规则的反馈分析）
    source_analysis_id = Column(BigInteger, nullable=True, comment="来源分析ID")

    # 索引定义
    __table_args__ = (
        Index("idx_optimization_rules_rule_type", "rule_type"),
        Index("idx_optimization_rules_enabled", "enabled"),
        Index("idx_optimization_rules_priority", "priority"),
        Index("idx_optimization_rules_status", "status"),
        Index("idx_optimization_rules_tenant_id", "tenant_id"),
    )

    def __repr__(self) -> str:
        """返回优化规则对象的字符串表示"""
        return f"<OptimizationRule(id={self.id}, rule_name={self.rule_name}, rule_type={self.rule_type})>"


class RuleAuditLog(Base):
    """
    规则审核日志表

    记录优化规则的审核历史。
    """

    # 审核操作常量
    ACTION_CREATE = "create"
    ACTION_UPDATE = "update"
    ACTION_DELETE = "delete"
    ACTION_ENABLE = "enable"
    ACTION_DISABLE = "disable"
    ACTION_SUBMIT_REVIEW = "submit_review"
    ACTION_APPROVE = "approve"
    ACTION_REJECT = "reject"

    __tablename__ = "rule_audit_logs"

    # 主键ID
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="主键ID")

    # 租户ID
    tenant_id = Column(BigInteger, default=1, nullable=False, index=True, comment="租户ID")

    # 规则ID
    rule_id = Column(BigInteger, nullable=False, index=True, comment="规则ID")

    # 操作类型：create/update/delete/enable/disable/submit_review/approve/reject
    action = Column(String(50), nullable=False, comment="操作类型")

    # 操作人ID
    operator_id = Column(BigInteger, nullable=True, comment="操作人ID")

    # 操作人姓名
    operator_name = Column(String(100), nullable=True, comment="操作人姓名")

    # 操作前状态
    before_status = Column(BigInteger, nullable=True, comment="操作前状态")

    # 操作后状态
    after_status = Column(BigInteger, nullable=True, comment="操作后状态")

    # 操作前配置（JSON）
    before_config = Column(Text, nullable=True, comment="操作前配置")

    # 操作后配置（JSON）
    after_config = Column(Text, nullable=True, comment="操作后配置")

    # 审核意见
    comment = Column(Text, nullable=True, comment="审核意见")

    # IP地址
    ip_address = Column(String(50), nullable=True, comment="IP地址")

    # 创建时间
    created_at = Column(DateTime, default=datetime.now, nullable=False, comment="创建时间")

    # 索引定义
    __table_args__ = (
        Index("idx_rule_audit_rule_id", "rule_id"),
        Index("idx_rule_audit_operator_id", "operator_id"),
        Index("idx_rule_audit_action", "action"),
        Index("idx_rule_audit_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        """返回审核日志对象的字符串表示"""
        return f"<RuleAuditLog(id={self.id}, rule_id={self.rule_id}, action={self.action})>"


class CleaningRuleOptimization(Base):
    """
    清洗规则优化记录表

    记录基于反馈分析产生的清洗规则优化建议。
    """

    # 优化类型常量
    OPTIMIZE_TYPE_ADD = "add"
    OPTIMIZE_TYPE_MODIFY = "modify"
    OPTIMIZE_TYPE_DELETE = "delete"
    OPTIMIZE_TYPE_DISABLE = "disable"

    # 状态常量
    STATUS_PENDING = 0
    STATUS_APPROVED = 1
    STATUS_REJECTED = 2
    STATUS_APPLIED = 3

    __tablename__ = "cleaning_rule_optimizations"

    # 主键ID
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="主键ID")

    # 租户ID
    tenant_id = Column(BigInteger, default=1, nullable=False, index=True, comment="租户ID")

    # 来源分析ID（关联feedback_analysis表）
    source_analysis_id = Column(BigInteger, nullable=True, index=True, comment="来源分析ID")

    # 涉及文档ID
    document_id = Column(BigInteger, nullable=True, comment="涉及文档ID")

    # 涉及Chunk ID
    chunk_id = Column(BigInteger, nullable=True, comment="涉及Chunk ID")

    # 优化类型：add/modify/delete/disable
    optimize_type = Column(String(50), nullable=False, comment="优化类型")

    # 规则名称（新增时）
    rule_name = Column(String(100), nullable=True, comment="规则名称")

    # 规则类型（新增时）
    rule_type = Column(String(50), nullable=True, comment="规则类型")

    # 规则配置（JSON格式）
    rule_config = Column(Text, nullable=True, comment="规则配置")

    # 目标规则ID（修改/删除时）
    target_rule_id = Column(BigInteger, nullable=True, comment="目标规则ID")

    # 问题模式（JSON格式，匹配该模式时触发）
    problem_pattern = Column(Text, nullable=True, comment="问题模式")

    # 优先级
    priority = Column(BigInteger, default=2, comment="优先级")

    # 状态：0-待处理 1-已审核 2-已拒绝 3-已应用
    status = Column(BigInteger, default=0, comment="状态")

    # 审核信息
    reviewed_by = Column(BigInteger, nullable=True, comment="审核人ID")
    reviewed_at = Column(DateTime, nullable=True, comment="审核时间")
    review_comment = Column(Text, nullable=True, comment="审核意见")

    # 应用信息
    applied_by = Column(BigInteger, nullable=True, comment="应用人ID")
    applied_at = Column(DateTime, nullable=True, comment="应用时间")

    # 创建人ID
    creator_id = Column(BigInteger, nullable=True, comment="创建人ID")

    # 创建时间
    created_at = Column(DateTime, default=datetime.now, nullable=False, comment="创建时间")

    # 索引定义
    __table_args__ = (
        Index("idx_cleaning_opt_source_analysis_id", "source_analysis_id"),
        Index("idx_cleaning_opt_status", "status"),
        Index("idx_cleaning_opt_document_id", "document_id"),
        Index("idx_cleaning_opt_priority", "priority"),
    )

    def __repr__(self) -> str:
        """返回清洗规则优化记录对象的字符串表示"""
        return f"<CleaningRuleOptimization(id={self.id}, optimize_type={self.optimize_type})>"
