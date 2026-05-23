# -*- coding: utf-8 -*-
"""
反馈服务

本模块提供反馈相关的业务逻辑处理，包括：
- 用户反馈提交
- 反馈分析与问题分类
- 检索问题检测
- 生成问题检测
- 优化规则管理
- 反馈统计
- 审核管理
- 清洗规则优化

注意：路由层只做参数校验和响应封装，所有业务逻辑在此层实现。
"""

import json
import re
from typing import Any, Dict, List, Optional

from app.common.exception import BusinessException, ErrorCode
from app.common.logging import logger
from app.models.feedback import FeedbackAnalysis, OptimizationRule
from app.models.qa import QALog
from app.schemas.qa import (
    FeedbackSubmitRequest,
    QALogDetail,
    QALogQueryRequest,
    FeedbackStatistics,
    OptimizationRuleRequest,
    OptimizationRuleModel,
    FeedbackAnalysisResult,
    FeedbackSubmitResponse,
)


class FeedbackService:
    """
    反馈服务

    提供用户反馈提交、反馈分析、优化规则管理等业务逻辑。
    """

    def __init__(self):
        """初始化反馈服务"""
        self._db = None
        self._analyzer = None
        self._engine = None
        self._optimizer = None
        self._audit_service = None

    def _get_db(self):
        """获取数据库会话"""
        from core.database import SessionLocal
        if self._db is None:
            self._db = SessionLocal()
        return self._db

    def _get_analyzer(self):
        """获取反馈分析器"""
        if self._analyzer is None:
            from app.services.feedback_analyzer import get_feedback_analyzer
            self._analyzer = get_feedback_analyzer()
        return self._analyzer

    def _get_engine(self):
        """获取优化规则引擎"""
        if self._engine is None:
            from app.services.optimization_engine import get_optimization_engine
            self._engine = get_optimization_engine()
        return self._engine

    def _get_optimizer(self):
        """获取清洗规则优化器"""
        if self._optimizer is None:
            from app.services.cleaning_optimizer import get_cleaning_rule_optimizer
            self._optimizer = get_cleaning_rule_optimizer()
        return self._optimizer

    def _get_audit_service(self):
        """获取审核服务"""
        if self._audit_service is None:
            from app.services.rule_audit_service import get_rule_audit_service
            self._audit_service = get_rule_audit_service()
        return self._audit_service

    def submit_feedback(self, request) -> Dict[str, Any]:
        """
        提交用户反馈

        Args:
            request: 反馈提交请求

        Returns:
            反馈提交响应
        """
        from app.schemas.qa import FeedbackSubmitRequest, FeedbackSubmitResponse

        db = self._get_db()
        try:
            qa_log = db.query(QALog).filter(QALog.id == request.qa_id).first()

            if not qa_log:
                raise BusinessException(
                    code=ErrorCode.DATA_NOT_FOUND[0],
                    message=f"问答记录不存在，ID: {request.qa_id}"
                )

            # 获取租户ID
            tenant_id = qa_log.tenant_id or 1

            # 更新QA日志的反馈信息
            qa_log.feedback = "helpful" if request.feedback == 1 else "not_helpful"
            qa_log.quality_score = request.quality_score
            qa_log.feedback_remark = request.feedback_reason

            db.commit()

            logger.info(
                "反馈提交成功",
                extra={
                    "qa_id": request.qa_id,
                    "feedback": request.feedback,
                    "quality_score": request.quality_score
                }
            )

            analysis_id = None

            # 负面反馈时进行自动分析
            if request.feedback == 0:
                # 使用新的分析器进行分析
                analysis_result = self._analyze_feedback_with_new_analyzer(
                    db, qa_log, request, tenant_id
                )
                if analysis_result:
                    analysis_id = analysis_result

            return {
                "success": True,
                "message": "反馈提交成功",
                "analysis_id": analysis_id
            }

        except BusinessException:
            db.rollback()
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"反馈提交失败: {str(e)}")
            raise BusinessException(
                code=ErrorCode.OPERATION_FAILED[0],
                message=f"反馈提交失败: {str(e)}"
            )

    def _analyze_feedback_with_new_analyzer(
        self,
        db,
        qa_log: QALog,
        request,
        tenant_id: int
    ) -> Optional[int]:
        """
        使用新的分析器分析负面反馈

        Args:
            db: 数据库会话
            qa_log: 问答日志
            request: 反馈请求
            tenant_id: 租户ID

        Returns:
            分析记录ID
        """
        try:
            # 获取分析器
            analyzer = self._get_analyzer()

            # 执行分析
            analysis_result = analyzer.analyze(
                qa_log=qa_log,
                feedback_type=request.feedback,
                feedback_reason=request.feedback_reason,
                quality_score=request.quality_score
            )

            # 提取涉及的文档和Chunk
            involved_chunks = analysis_result.involved_chunks
            involved_documents = analysis_result.involved_documents

            # 获取检索指标
            retrieval_metadata = analysis_result.retrieval_metadata

            # 获取建议
            suggestions = [
                {
                    "type": s.suggestion_type,
                    "priority": s.priority,
                    "description": s.description,
                    "action_type": s.action_type,
                    "action_config": s.action_config
                }
                for s in analysis_result.suggestions
            ]

            # 创建分析记录
            analysis = FeedbackAnalysis(
                tenant_id=tenant_id,
                qa_log_id=qa_log.id,
                feedback_type="not_helpful" if request.feedback == 0 else "helpful",
                issue_type=analysis_result.issue_classification.issue_type,
                issue_category=analysis_result.issue_classification.issue_category,
                issue_description=request.feedback_reason or "用户反馈不满意",
                involved_chunks=json.dumps(involved_chunks, ensure_ascii=False) if involved_chunks else None,
                involved_documents=json.dumps(involved_documents, ensure_ascii=False) if involved_documents else None,
                retrieval_score=analysis_result.issue_classification.confidence * 5,
                retrieval_avg_score=retrieval_metadata.get("retrieval_avg_score"),
                retrieval_result_count=retrieval_metadata.get("retrieval_result_count"),
                retrieval_timeout=retrieval_metadata.get("retrieval_timeout", 0),
                suggestions=json.dumps(suggestions, ensure_ascii=False) if suggestions else None,
                suggestion_type=analysis_result.suggestions[0].suggestion_type if analysis_result.suggestions else None,
                root_cause=analysis_result.root_cause.root_cause_description,
                root_cause_type=analysis_result.root_cause.root_cause_type,
                handled_status=0,
            )

            db.add(analysis)
            db.commit()
            db.refresh(analysis)

            logger.info(
                "负面反馈分析完成（新版分析器）",
                extra={
                    "qa_id": qa_log.id,
                    "analysis_id": analysis.id,
                    "issue_type": analysis_result.issue_classification.issue_type,
                    "issue_category": analysis_result.issue_classification.issue_category
                }
            )

            # 检查是否触发了优化规则
            self._check_optimization_rules(db, analysis)

            return analysis.id

        except Exception as e:
            logger.error(f"分析反馈失败: {str(e)}")
            return None

    def _check_optimization_rules(self, db, analysis: FeedbackAnalysis) -> None:
        """检查是否触发了优化规则"""
        try:
            engine = self._get_engine()

            # 获取适用的规则
            rules = engine.get_applicable_rules(
                tenant_id=analysis.tenant_id,
                rule_type=analysis.issue_type
            )

            # 检查触发条件
            matched_rules = engine.check_trigger(analysis, rules)

            if matched_rules:
                logger.info(
                    f"检测到{len(matched_rules)}条匹配的优化规则",
                    extra={"analysis_id": analysis.id, "matched_count": len(matched_rules)}
                )

                # 可以在这里执行规则或生成通知
                for match in matched_rules:
                    logger.info(
                        "触发优化规则",
                        extra={
                            "rule_id": match.rule_id,
                            "rule_name": match.rule_name,
                            "confidence": match.confidence
                        }
                    )

        except Exception as e:
            logger.error(f"检查优化规则失败: {str(e)}")

    def _analyze_negative_feedback(
        self,
        db,
        qa_log: QALog,
        request: FeedbackSubmitRequest
    ) -> int:
        """
        分析负面反馈

        Args:
            db: 数据库会话
            qa_log: 问答日志
            request: 反馈请求

        Returns:
            分析记录ID
        """
        issue_type, issue_category, suggestions, suggestion_type = self._classify_issue(
            qa_log, request
        )

        references_data = []
        if qa_log.references:
            try:
                references_data = json.loads(qa_log.references) if isinstance(qa_log.references, str) else qa_log.references
            except (json.JSONDecodeError, TypeError):
                references_data = []

        involved_chunks = [ref.get("chunk_id") for ref in references_data if ref.get("chunk_id")]

        retrieval_score = self._calculate_retrieval_score(qa_log)
        generation_score = request.quality_score or 3

        analysis = FeedbackAnalysis(
            qa_log_id=qa_log.id,
            issue_type=issue_type,
            issue_category=issue_category,
            issue_description=request.feedback_reason or "用户反馈不满意",
            involved_chunks=json.dumps(involved_chunks, ensure_ascii=False) if involved_chunks else None,
            retrieval_score=retrieval_score,
            generation_score=generation_score,
            suggestions=json.dumps(suggestions, ensure_ascii=False) if suggestions else None,
            suggestion_type=suggestion_type,
            handled_status=0,
        )

        db.add(analysis)
        db.commit()
        db.refresh(analysis)

        logger.info(
            "负面反馈分析完成",
            extra={
                "qa_id": qa_log.id,
                "analysis_id": analysis.id,
                "issue_type": issue_type,
                "issue_category": issue_category
            }
        )

        return analysis.id

    def _classify_issue(
        self,
        qa_log: QALog,
        request: FeedbackSubmitRequest
    ) -> tuple:
        """
        分类问题类型

        Args:
            qa_log: 问答日志
            request: 反馈请求

        Returns:
            (issue_type, issue_category, suggestions, suggestion_type)
        """
        issue_type = "retrieval"
        issue_category = "retrieval_inaccurate"
        suggestions = []
        suggestion_type = "optimize_retrieval"

        if self._is_retrieval_issue(qa_log):
            suggestions = self._suggest_retrieval_improvements(qa_log)
            suggestion_type = "optimize_retrieval"
        elif self._is_generation_issue(qa_log):
            issue_type = "generation"
            issue_category = "answer_incorrect"
            suggestions = self._suggest_generation_improvements(qa_log)
            suggestion_type = "optimize_prompt"
        else:
            issue_type = "both"
            issue_category = "unclear"
            suggestions = ["建议检查检索和生成两个阶段的问题"]
            suggestion_type = "general"

        return issue_type, issue_category, suggestions, suggestion_type

    def _is_retrieval_issue(self, qa_log: QALog) -> bool:
        """
        判断是否为检索问题

        Args:
            qa_log: 问答日志

        Returns:
            是否为检索问题
        """
        if not qa_log.references or qa_log.references == "[]":
            return True

        try:
            references = json.loads(qa_log.references) if isinstance(qa_log.references, str) else qa_log.references
            if not references:
                return True

            total_score = sum(ref.get("score", 0) for ref in references)
            avg_score = total_score / len(references) if references else 0

            if avg_score < 0.3:
                return True

            if qa_log.retrieval_time_ms and qa_log.retrieval_time_ms > 5000:
                return True

        except (json.JSONDecodeError, TypeError):
            return True

        return False

    def _is_generation_issue(self, qa_log: QALog) -> bool:
        """
        判断是否为生成问题

        Args:
            qa_log: 问答日志

        Returns:
            是否为生成问题
        """
        if not qa_log.answer:
            return True

        answer_lower = qa_log.answer.lower()
        if any(phrase in answer_lower for phrase in ["无法", "不知道", "没有找到", "不清楚", "抱歉"]):
            if self._has_valid_references(qa_log):
                return True

        if len(qa_log.answer) < 10 and self._has_valid_references(qa_log):
            return True

        return False

    def _has_valid_references(self, qa_log: QALog) -> bool:
        """检查是否有有效的引用"""
        if not qa_log.references or qa_log.references == "[]":
            return False

        try:
            references = json.loads(qa_log.references) if isinstance(qa_log.references, str) else qa_log.references
            return len(references) > 0
        except (json.JSONDecodeError, TypeError):
            return False

    def _calculate_retrieval_score(self, qa_log: QALog) -> int:
        """
        计算检索质量评分

        Args:
            qa_log: 问答日志

        Returns:
            检索质量评分（1-5）
        """
        if not qa_log.references or qa_log.references == "[]":
            return 1

        try:
            references = json.loads(qa_log.references) if isinstance(qa_log.references, str) else qa_log.references
            if not references:
                return 1

            total_score = sum(ref.get("score", 0) for ref in references)
            avg_score = total_score / len(references)

            if avg_score >= 0.7:
                return 5
            elif avg_score >= 0.5:
                return 4
            elif avg_score >= 0.3:
                return 3
            elif avg_score >= 0.1:
                return 2
            else:
                return 1

        except (json.JSONDecodeError, TypeError):
            return 1

    def _suggest_retrieval_improvements(self, qa_log: QALog) -> List[str]:
        """
        生成检索改进建议

        Args:
            qa_log: 问答日志

        Returns:
            改进建议列表
        """
        suggestions = []

        if not qa_log.references or qa_log.references == "[]":
            suggestions.append("检索结果为空，建议优化检索关键词或检查文档库")
            suggestions.append("可能需要增加相关文档的导入")
        else:
            suggestions.append("检索相关性偏低，建议优化向量模型或关键词权重")
            suggestions.append("考虑调整混合检索的融合参数")

        suggestions.append("检查相关文档的切分是否合理")

        return suggestions

    def _suggest_generation_improvements(self, qa_log: QALog) -> List[str]:
        """
        生成改进建议

        Args:
            qa_log: 问答日志

        Returns:
            改进建议列表
        """
        suggestions = []

        suggestions.append("检查Prompt模板是否准确引导模型生成答案")
        suggestions.append("考虑增加上下文信息或调整上下文组装策略")

        if self._is_retrieval_issue(qa_log):
            suggestions.append("虽然可能是检索问题导致的生成问题，但建议同时检查生成阶段")

        return suggestions

    def get_qa_log_detail(self, qa_id: int) -> QALogDetail:
        """
        获取问答日志详情

        Args:
            qa_id: 问答日志ID

        Returns:
            问答日志详情
        """
        db = self._get_db()
        try:
            qa_log = db.query(QALog).filter(QALog.id == qa_id).first()

            if not qa_log:
                raise BusinessException(
                    code=ErrorCode.DATA_NOT_FOUND[0],
                    message=f"问答记录不存在，ID: {qa_id}"
                )

            references_data = None
            if qa_log.references:
                try:
                    references_data = json.loads(qa_log.references) if isinstance(qa_log.references, str) else qa_log.references
                except (json.JSONDecodeError, TypeError):
                    references_data = []

            analysis = None
            analysis_record = db.query(FeedbackAnalysis).filter(
                FeedbackAnalysis.qa_log_id == qa_id
            ).first()

            if analysis_record:
                suggestions_list = None
                if analysis_record.suggestions:
                    try:
                        suggestions_list = json.loads(analysis_record.suggestions) if isinstance(analysis_record.suggestions, str) else analysis_record.suggestions
                    except (json.JSONDecodeError, TypeError):
                        suggestions_list = []

                analysis = FeedbackAnalysisResult(
                    id=analysis_record.id,
                    qa_log_id=analysis_record.qa_log_id,
                    issue_type=analysis_record.issue_type,
                    issue_category=analysis_record.issue_category,
                    issue_description=analysis_record.issue_description,
                    suggestions=suggestions_list,
                    suggestion_type=analysis_record.suggestion_type,
                    handled_status=analysis_record.handled_status or 0,
                    created_at=analysis_record.created_at
                )

            return QALogDetail(
                id=qa_log.id,
                user_id=qa_log.user_id,
                session_id=qa_log.session_id,
                question=qa_log.question,
                answer=qa_log.answer,
                references=references_data,
                feedback=qa_log.feedback,
                feedback_reason=qa_log.feedback_remark,
                quality_score=qa_log.quality_score,
                retrieval_time_ms=qa_log.retrieval_time_ms,
                generation_time_ms=qa_log.generation_time_ms,
                total_time_ms=qa_log.total_time_ms,
                created_at=qa_log.created_at,
                analysis=analysis
            )

        finally:
            db.close()
            self._db = None

    def query_qa_logs(self, request: QALogQueryRequest) -> Dict[str, Any]:
        """
        查询问答日志列表

        Args:
            request: 查询请求

        Returns:
            包含items和total的字典
        """
        db = self._get_db()
        try:
            query = db.query(QALog).filter(QALog.tenant_id == request.tenant_id)

            if request.user_id:
                query = query.filter(QALog.user_id == request.user_id)

            if request.session_id:
                query = query.filter(QALog.session_id == request.session_id)

            if request.start_date:
                from datetime import datetime
                query = query.filter(QALog.created_at >= datetime.fromisoformat(request.start_date))

            if request.end_date:
                from datetime import datetime
                end_date = datetime.fromisoformat(request.end_date)
                query = query.filter(QALog.created_at <= end_date.replace(hour=23, minute=59, second=59))

            if request.has_feedback is not None:
                if request.has_feedback:
                    query = query.filter(QALog.feedback.isnot(None))
                else:
                    query = query.filter(QALog.feedback.is_(None))

            if request.feedback_value is not None:
                feedback_str = "helpful" if request.feedback_value == 1 else "not_helpful"
                query = query.filter(QALog.feedback == feedback_str)

            if request.min_score is not None:
                query = query.filter(QALog.quality_score >= request.min_score)

            if request.max_score is not None:
                query = query.filter(QALog.quality_score <= request.max_score)

            if request.keyword:
                keyword_pattern = f"%{request.keyword}%"
                query = query.filter(
                    (QALog.question.like(keyword_pattern)) |
                    (QALog.answer.like(keyword_pattern))
                )

            total = query.count()

            offset = (request.page_no - 1) * request.page_size
            items = query.order_by(QALog.created_at.desc()).offset(offset).limit(request.page_size).all()

            result_items = []
            for item in items:
                result_items.append({
                    "id": item.id,
                    "user_id": item.user_id,
                    "session_id": item.session_id,
                    "question": item.question,
                    "answer": item.answer[:100] + "..." if item.answer and len(item.answer) > 100 else item.answer,
                    "feedback": item.feedback,
                    "quality_score": item.quality_score,
                    "created_at": item.created_at
                })

            return {
                "items": result_items,
                "total": total
            }

        finally:
            db.close()
            self._db = None

    def get_feedback_statistics(
        self,
        tenant_id: int,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> FeedbackStatistics:
        """
        获取反馈统计信息

        Args:
            tenant_id: 租户ID
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            反馈统计信息
        """
        db = self._get_db()
        try:
            from sqlalchemy import func

            query = db.query(QALog).filter(QALog.tenant_id == tenant_id)

            if start_date:
                from datetime import datetime
                query = query.filter(QALog.created_at >= datetime.fromisoformat(start_date))
            if end_date:
                from datetime import datetime
                end_dt = datetime.fromisoformat(end_date)
                query = query.filter(QALog.created_at <= end_dt.replace(hour=23, minute=59, second=59))

            total_count = query.count()

            positive_count = query.filter(QALog.feedback == "helpful").count()
            negative_count = query.filter(QALog.feedback == "not_helpful").count()

            positive_rate = (positive_count / total_count * 100) if total_count > 0 else 0.0

            avg_score = db.query(func.avg(QALog.quality_score)).filter(
                QALog.tenant_id == tenant_id,
                QALog.quality_score.isnot(None)
            ).scalar() or 0.0

            retrieval_issue_count = db.query(FeedbackAnalysis).join(
                QALog, FeedbackAnalysis.qa_log_id == QALog.id
            ).filter(
                QALog.tenant_id == tenant_id,
                FeedbackAnalysis.issue_type == "retrieval"
            ).count()

            generation_issue_count = db.query(FeedbackAnalysis).join(
                QALog, FeedbackAnalysis.qa_log_id == QALog.id
            ).filter(
                QALog.tenant_id == tenant_id,
                FeedbackAnalysis.issue_type == "generation"
            ).count()

            pending_analysis_count = db.query(FeedbackAnalysis).join(
                QALog, FeedbackAnalysis.qa_log_id == QALog.id
            ).filter(
                QALog.tenant_id == tenant_id,
                FeedbackAnalysis.handled_status == 0
            ).count()

            handled_count = db.query(FeedbackAnalysis).join(
                QALog, FeedbackAnalysis.qa_log_id == QALog.id
            ).filter(
                QALog.tenant_id == tenant_id,
                FeedbackAnalysis.handled_status.in_([1, 2])
            ).count()

            top_issues = self._get_top_issues(db, tenant_id, limit=5)

            return FeedbackStatistics(
                total_count=total_count,
                positive_count=positive_count,
                negative_count=negative_count,
                positive_rate=round(positive_rate, 2),
                avg_quality_score=round(float(avg_score), 2),
                top_issues=top_issues,
                retrieval_issue_count=retrieval_issue_count,
                generation_issue_count=generation_issue_count,
                pending_analysis_count=pending_analysis_count,
                handled_count=handled_count
            )

        finally:
            db.close()
            self._db = None

    def _get_top_issues(
        self,
        db,
        tenant_id: int,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """获取高频问题类型"""
        from sqlalchemy import func

        results = db.query(
            FeedbackAnalysis.issue_category,
            func.count(FeedbackAnalysis.id).label("count")
        ).join(
            QALog, FeedbackAnalysis.qa_log_id == QALog.id
        ).filter(
            QALog.tenant_id == tenant_id,
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
                "percentage": round(r.count / total * 100, 2)
            }
            for r in results
        ]

    def get_optimization_rules(
        self,
        rule_type: Optional[str] = None,
        enabled: Optional[bool] = None,
        page_no: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """
        获取优化规则列表

        Args:
            rule_type: 规则类型
            enabled: 是否启用
            page_no: 页码
            page_size: 每页数量

        Returns:
            包含items和total的字典
        """
        db = self._get_db()
        try:
            query = db.query(OptimizationRule)

            if rule_type:
                query = query.filter(OptimizationRule.rule_type == rule_type)

            if enabled is not None:
                query = query.filter(OptimizationRule.enabled == (1 if enabled else 0))

            total = query.count()

            offset = (page_no - 1) * page_size
            items = query.order_by(OptimizationRule.priority.asc(), OptimizationRule.created_at.desc()).offset(offset).limit(page_size).all()

            result_items = []
            for item in items:
                rule_config = None
                if item.rule_config:
                    try:
                        rule_config = json.loads(item.rule_config) if isinstance(item.rule_config, str) else item.rule_config
                    except (json.JSONDecodeError, TypeError):
                        rule_config = {}

                trigger_condition = None
                if item.trigger_condition:
                    try:
                        trigger_condition = json.loads(item.trigger_condition) if isinstance(item.trigger_condition, str) else item.trigger_condition
                    except (json.JSONDecodeError, TypeError):
                        trigger_condition = {}

                applicable_scope = None
                if item.applicable_scope:
                    try:
                        applicable_scope = json.loads(item.applicable_scope) if isinstance(item.applicable_scope, str) else item.applicable_scope
                    except (json.JSONDecodeError, TypeError):
                        applicable_scope = {}

                result_items.append(OptimizationRuleModel(
                    id=item.id,
                    rule_name=item.rule_name,
                    rule_type=item.rule_type,
                    rule_config=rule_config,
                    trigger_condition=trigger_condition,
                    priority=item.priority or 2,
                    enabled=bool(item.enabled),
                    description=item.description,
                    applicable_scope=applicable_scope,
                    expected_effect=item.expected_effect,
                    actual_effect=item.actual_effect,
                    creator_id=item.creator_id,
                    created_at=item.created_at,
                    updated_at=item.updated_at
                ))

            return {
                "items": result_items,
                "total": total
            }

        finally:
            db.close()
            self._db = None

    def create_optimization_rule(
        self,
        request: OptimizationRuleRequest,
        creator_id: Optional[int] = None
    ) -> OptimizationRuleModel:
        """
        创建优化规则

        Args:
            request: 规则请求
            creator_id: 创建人ID

        Returns:
            创建的优化规则
        """
        db = self._get_db()
        try:
            rule = OptimizationRule(
                rule_name=request.rule_name,
                rule_type=request.rule_type,
                rule_config=json.dumps(request.rule_config, ensure_ascii=False) if request.rule_config else None,
                trigger_condition=json.dumps(request.trigger_condition, ensure_ascii=False) if request.trigger_condition else None,
                priority=request.priority,
                enabled=1 if request.enabled else 0,
                description=request.description,
                applicable_scope=json.dumps(request.applicable_scope, ensure_ascii=False) if request.applicable_scope else None,
                expected_effect=request.expected_effect,
                creator_id=creator_id,
            )

            db.add(rule)
            db.commit()
            db.refresh(rule)

            logger.info(
                "优化规则创建成功",
                extra={"rule_id": rule.id, "rule_name": rule.rule_name}
            )

            return OptimizationRuleModel(
                id=rule.id,
                rule_name=rule.rule_name,
                rule_type=rule.rule_type,
                rule_config=request.rule_config,
                trigger_condition=request.trigger_condition,
                priority=rule.priority or 2,
                enabled=bool(rule.enabled),
                description=rule.description,
                applicable_scope=request.applicable_scope,
                expected_effect=rule.expected_effect,
                actual_effect=rule.actual_effect,
                creator_id=rule.creator_id,
                created_at=rule.created_at,
                updated_at=rule.updated_at
            )

        except Exception as e:
            db.rollback()
            logger.error(f"创建优化规则失败: {str(e)}")
            raise BusinessException(
                code=ErrorCode.OPERATION_FAILED[0],
                message=f"创建优化规则失败: {str(e)}"
            )

        finally:
            db.close()
            self._db = None

    def update_optimization_rule(
        self,
        rule_id: int,
        request: OptimizationRuleRequest,
        updater_id: Optional[int] = None
    ) -> OptimizationRuleModel:
        """
        更新优化规则

        Args:
            rule_id: 规则ID
            request: 规则请求
            updater_id: 更新人ID

        Returns:
            更新的优化规则
        """
        db = self._get_db()
        try:
            rule = db.query(OptimizationRule).filter(OptimizationRule.id == rule_id).first()

            if not rule:
                raise BusinessException(
                    code=ErrorCode.DATA_NOT_FOUND[0],
                    message=f"优化规则不存在，ID: {rule_id}"
                )

            rule.rule_name = request.rule_name
            rule.rule_type = request.rule_type
            rule.rule_config = json.dumps(request.rule_config, ensure_ascii=False) if request.rule_config else None
            rule.trigger_condition = json.dumps(request.trigger_condition, ensure_ascii=False) if request.trigger_condition else None
            rule.priority = request.priority
            rule.enabled = 1 if request.enabled else 0
            rule.description = request.description
            rule.applicable_scope = json.dumps(request.applicable_scope, ensure_ascii=False) if request.applicable_scope else None
            rule.expected_effect = request.expected_effect
            rule.updater_id = updater_id

            db.commit()
            db.refresh(rule)

            logger.info(
                "优化规则更新成功",
                extra={"rule_id": rule.id, "rule_name": rule.rule_name}
            )

            rule_config = None
            if rule.rule_config:
                try:
                    rule_config = json.loads(rule.rule_config) if isinstance(rule.rule_config, str) else rule.rule_config
                except (json.JSONDecodeError, TypeError):
                    rule_config = {}

            trigger_condition = None
            if rule.trigger_condition:
                try:
                    trigger_condition = json.loads(rule.trigger_condition) if isinstance(rule.trigger_condition, str) else rule.trigger_condition
                except (json.JSONDecodeError, TypeError):
                    trigger_condition = {}

            applicable_scope = None
            if rule.applicable_scope:
                try:
                    applicable_scope = json.loads(rule.applicable_scope) if isinstance(rule.applicable_scope, str) else rule.applicable_scope
                except (json.JSONDecodeError, TypeError):
                    applicable_scope = {}

            return OptimizationRuleModel(
                id=rule.id,
                rule_name=rule.rule_name,
                rule_type=rule.rule_type,
                rule_config=rule_config,
                trigger_condition=trigger_condition,
                priority=rule.priority or 2,
                enabled=bool(rule.enabled),
                description=rule.description,
                applicable_scope=applicable_scope,
                expected_effect=rule.expected_effect,
                actual_effect=rule.actual_effect,
                creator_id=rule.creator_id,
                created_at=rule.created_at,
                updated_at=rule.updated_at
            )

        except BusinessException:
            db.rollback()
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"更新优化规则失败: {str(e)}")
            raise BusinessException(
                code=ErrorCode.OPERATION_FAILED[0],
                message=f"更新优化规则失败: {str(e)}"
            )

        finally:
            db.close()
            self._db = None

    def delete_optimization_rule(self, rule_id: int) -> bool:
        """
        删除优化规则

        Args:
            rule_id: 规则ID

        Returns:
            是否成功
        """
        db = self._get_db()
        try:
            rule = db.query(OptimizationRule).filter(OptimizationRule.id == rule_id).first()

            if not rule:
                raise BusinessException(
                    code=ErrorCode.DATA_NOT_FOUND[0],
                    message=f"优化规则不存在，ID: {rule_id}"
                )

            db.delete(rule)
            db.commit()

            logger.info(
                "优化规则删除成功",
                extra={"rule_id": rule_id}
            )

            return True

        except BusinessException:
            db.rollback()
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"删除优化规则失败: {str(e)}")
            raise BusinessException(
                code=ErrorCode.OPERATION_FAILED[0],
                message=f"删除优化规则失败: {str(e)}"
            )

        finally:
            db.close()
            self._db = None

    def handle_feedback_analysis(
        self,
        analysis_id: int,
        handler_id: int,
        status: int,
        remark: Optional[str] = None
    ) -> bool:
        """
        处理反馈分析

        Args:
            analysis_id: 分析ID
            handler_id: 处理人ID
            status: 处理状态（1-已处理 2-已忽略）
            remark: 处理备注

        Returns:
            是否成功
        """
        db = self._get_db()
        try:
            from datetime import datetime

            analysis = db.query(FeedbackAnalysis).filter(FeedbackAnalysis.id == analysis_id).first()

            if not analysis:
                raise BusinessException(
                    code=ErrorCode.DATA_NOT_FOUND[0],
                    message=f"反馈分析记录不存在，ID: {analysis_id}"
                )

            analysis.handled_status = status
            analysis.handler_id = handler_id
            analysis.handled_at = datetime.now()
            analysis.handler_remark = remark

            db.commit()

            logger.info(
                "反馈分析处理完成",
                extra={
                    "analysis_id": analysis_id,
                    "handler_id": handler_id,
                    "status": status
                }
            )

            return True

        except BusinessException:
            db.rollback()
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"处理反馈分析失败: {str(e)}")
            raise BusinessException(
                code=ErrorCode.OPERATION_FAILED[0],
                message=f"处理反馈分析失败: {str(e)}"
            )

        finally:
            db.close()
            self._db = None

    # ================================================
    # 清洗规则优化相关方法
    # ================================================

    def get_cleaning_optimization_suggestions(
        self,
        tenant_id: int = 1,
        time_window_days: int = 7,
        min_occurrence: int = 3
    ) -> List[Dict[str, Any]]:
        """
        获取清洗规则优化建议

        Args:
            tenant_id: 租户ID
            time_window_days: 分析时间窗口（天）
            min_occurrence: 最小出现次数

        Returns:
            优化建议列表
        """
        optimizer = self._get_optimizer()
        suggestions = optimizer.analyze_and_suggest(
            tenant_id=tenant_id,
            time_window_days=time_window_days,
            min_occurrence=min_occurrence
        )

        return [
            {
                "optimization_type": s.optimization_type,
                "rule_name": s.rule_name,
                "rule_type": s.rule_type,
                "rule_config": s.rule_config,
                "priority": s.priority,
                "reason": s.reason,
                "problem_pattern": s.problem_pattern
            }
            for s in suggestions
        ]

    def get_high_frequency_patterns(
        self,
        tenant_id: int = 1,
        time_window_days: int = 7,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        获取高频问题模式

        Args:
            tenant_id: 租户ID
            time_window_days: 时间窗口
            limit: 返回数量

        Returns:
            高频问题模式列表
        """
        optimizer = self._get_optimizer()
        return optimizer.get_high_frequency_patterns(
            tenant_id=tenant_id,
            time_window_days=time_window_days,
            limit=limit
        )

    def apply_cleaning_optimization(
        self,
        optimization_data: Dict[str, Any],
        operator_id: int
    ) -> bool:
        """
        应用清洗规则优化

        Args:
            optimization_data: 优化数据
            operator_id: 操作人ID

        Returns:
            是否成功
        """
        from app.services.cleaning_optimizer import RuleOptimization

        optimization = RuleOptimization(
            optimization_id=None,
            optimization_type=optimization_data.get("optimization_type", "add"),
            target_rule_id=optimization_data.get("target_rule_id"),
            rule_name=optimization_data.get("rule_name", "未命名规则"),
            rule_type=optimization_data.get("rule_type", "cleaning"),
            rule_config=optimization_data.get("rule_config", {}),
            priority=optimization_data.get("priority", 2),
            reason=optimization_data.get("reason", ""),
            problem_pattern=optimization_data.get("problem_pattern", ""),
            status=0
        )

        optimizer = self._get_optimizer()
        return optimizer.apply_optimization(optimization, operator_id)

    # ================================================
    # 审核相关方法
    # ================================================

    def submit_rule_for_review(
        self,
        rule_id: int,
        operator_id: int,
        operator_name: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> bool:
        """
        提交规则审核

        Args:
            rule_id: 规则ID
            operator_id: 操作人ID
            operator_name: 操作人姓名
            ip_address: IP地址

        Returns:
            是否成功
        """
        audit_service = self._get_audit_service()
        return audit_service.submit_for_review(
            rule_id=rule_id,
            operator_id=operator_id,
            operator_name=operator_name,
            ip_address=ip_address
        )

    def approve_rule(
        self,
        rule_id: int,
        reviewer_id: int,
        reviewer_name: Optional[str] = None,
        comment: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> bool:
        """
        审核通过规则

        Args:
            rule_id: 规则ID
            reviewer_id: 审核人ID
            reviewer_name: 审核人姓名
            comment: 审核意见
            ip_address: IP地址

        Returns:
            是否成功
        """
        audit_service = self._get_audit_service()
        return audit_service.approve_rule(
            rule_id=rule_id,
            reviewer_id=reviewer_id,
            reviewer_name=reviewer_name,
            comment=comment,
            ip_address=ip_address
        )

    def reject_rule(
        self,
        rule_id: int,
        reviewer_id: int,
        reviewer_name: Optional[str] = None,
        comment: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> bool:
        """
        审核拒绝规则

        Args:
            rule_id: 规则ID
            reviewer_id: 审核人ID
            reviewer_name: 审核人姓名
            comment: 拒绝原因
            ip_address: IP地址

        Returns:
            是否成功
        """
        audit_service = self._get_audit_service()
        return audit_service.reject_rule(
            rule_id=rule_id,
            reviewer_id=reviewer_id,
            reviewer_name=reviewer_name,
            comment=comment,
            ip_address=ip_address
        )

    def enable_rule(
        self,
        rule_id: int,
        operator_id: int,
        operator_name: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> bool:
        """
        启用规则

        Args:
            rule_id: 规则ID
            operator_id: 操作人ID
            operator_name: 操作人姓名
            ip_address: IP地址

        Returns:
            是否成功
        """
        audit_service = self._get_audit_service()
        return audit_service.enable_rule(
            rule_id=rule_id,
            operator_id=operator_id,
            operator_name=operator_name,
            ip_address=ip_address
        )

    def disable_rule(
        self,
        rule_id: int,
        operator_id: int,
        operator_name: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> bool:
        """
        禁用规则

        Args:
            rule_id: 规则ID
            operator_id: 操作人ID
            operator_name: 操作人姓名
            ip_address: IP地址

        Returns:
            是否成功
        """
        audit_service = self._get_audit_service()
        return audit_service.disable_rule(
            rule_id=rule_id,
            operator_id=operator_id,
            operator_name=operator_name,
            ip_address=ip_address
        )

    def get_audit_logs(
        self,
        rule_id: Optional[int] = None,
        operator_id: Optional[int] = None,
        action: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        page_no: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """
        获取审核日志

        Args:
            rule_id: 规则ID
            operator_id: 操作人ID
            action: 操作类型
            start_date: 开始日期
            end_date: 结束日期
            page_no: 页码
            page_size: 每页数量

        Returns:
            审核日志列表
        """
        audit_service = self._get_audit_service()
        items, total = audit_service.get_audit_logs(
            rule_id=rule_id,
            operator_id=operator_id,
            action=action,
            start_date=start_date,
            end_date=end_date,
            page_no=page_no,
            page_size=page_size
        )

        return {
            "items": items,
            "total": total
        }

    def get_pending_approvals(
        self,
        tenant_id: int = 1,
        page_no: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """
        获取待审核规则

        Args:
            tenant_id: 租户ID
            page_no: 页码
            page_size: 每页数量

        Returns:
            待审核规则列表
        """
        audit_service = self._get_audit_service()
        items, total = audit_service.get_pending_approvals(
            tenant_id=tenant_id,
            page_no=page_no,
            page_size=page_size
        )

        return {
            "items": items,
            "total": total
        }

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
        engine = self._get_engine()
        return engine.evaluate_rule_effect(
            rule_id=rule_id,
            time_window_hours=time_window_hours
        )


# 全局服务实例
_feedback_service: Optional[FeedbackService] = None


def get_feedback_service() -> FeedbackService:
    """获取反馈服务实例"""
    global _feedback_service
    if _feedback_service is None:
        _feedback_service = FeedbackService()
    return _feedback_service
