# -*- coding: utf-8 -*-
"""
问答服务路由

本模块提供问答相关接口：
- 问答生成
- 问答流式生成
- 会话历史查询
- 反馈提交
- 反馈分析
- 日志查询
- 统计查询
- 优化规则管理

注意：路由层只做参数校验和响应封装，业务逻辑在services层。
"""

import json
import uuid
from typing import Optional, AsyncGenerator

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse

from app.common.response import success_response, page_response
from app.schemas.qa import (
    QARequest,
    QAResponse,
    FeedbackSubmitRequest,
    QALogQueryRequest,
    OptimizationRuleRequest,
    QAStatistics,
)
from app.services.feedback_service import FeedbackService, get_feedback_service
from app.services.qa_service import QAService

router = APIRouter()


def get_qa_service() -> QAService:
    """获取问答服务实例"""
    return QAService()


@router.post("")
async def ask_question(
    request: QARequest,
    service: QAService = Depends(get_qa_service)
):
    """
    问答接口

    根据用户问题，生成答案。

    Args:
        request: 问答请求参数
            - question: 用户问题
            - session_id: 会话ID（可选，自动生成）
            - use_rerank: 是否使用重排
            - top_k: 检索TopK
            - rerank_top_k: 重排后TopK
            - max_context_tokens: 最大上下文Token数

    Returns:
        问答结果，包含答案、引用和耗时信息
    """
    result = service.ask_question(request)
    return success_response(data=result)


@router.post("/stream")
async def ask_question_stream(
    request: QARequest,
    service: QAService = Depends(get_qa_service)
):
    """
    流式问答接口

    根据用户问题，流式生成答案。使用SSE实现流式输出。
    先调用完整API保存日志，再流式发送已保存的答案。

    Args:
        request: 问答请求参数

    Returns:
        流式响应（SSE格式）
    """
    # 生成会话ID
    session_id = request.session_id
    if not session_id:
        session_id = str(uuid.uuid4())

    async def event_generator() -> AsyncGenerator[str, None]:
        try:
            # 发送开始事件
            yield f"event: start\ndata: {json.dumps({'session_id': session_id}, ensure_ascii=False)}\n\n"

            # 调用完整的非流式问答（会保存日志）
            result = service.ask_question(request)
            qa_id = result.result.qa_id
            full_answer = result.result.answer

            # 发送元数据（包含引用等信息）
            yield f"event: metadata\ndata: {json.dumps({
                'qa_id': qa_id,
                'retrieval_time_ms': result.result.retrieval_time_ms,
                'rerank_time_ms': result.result.rerank_time_ms,
                'context_time_ms': result.result.context_time_ms,
                'generation_time_ms': result.result.generation_time_ms,
            }, ensure_ascii=False)}\n\n"

            # 流式发送答案（按字符/词组发送）
            # 简单的流式效果：将答案分块发送
            chunk_size = 10  # 每10个字符发送一次
            for i in range(0, len(full_answer), chunk_size):
                chunk = full_answer[i:i + chunk_size]
                yield f"event: content\ndata: {json.dumps({'content': chunk}, ensure_ascii=False)}\n\n"
                # 添加小延迟以产生流式效果
                import asyncio
                await asyncio.sleep(0.02)

            # 发送完成事件
            yield f"event: done\ndata: {json.dumps({'qa_id': qa_id}, ensure_ascii=False)}\n\n"

        except Exception as e:
            error_msg = str(e)
            yield f"event: error\ndata: {json.dumps({'error': error_msg}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@router.get("/history")
async def get_history(
    session_id: str = Query(..., description="会话ID"),
    page_no: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    service: QAService = Depends(get_qa_service)
):
    """
    查询会话历史

    获取指定会话的历史问答记录。

    Args:
        session_id: 会话ID
        page_no: 页码
        page_size: 每页数量

    Returns:
        分页后的历史记录
    """
    result = service.get_history(session_id, page_no, page_size)
    return page_response(
        items=result["items"],
        total=result["total"],
        page_no=page_no,
        page_size=page_size
    )


@router.post("/feedback", summary="提交用户反馈")
async def submit_feedback(
    request: FeedbackSubmitRequest,
    service: FeedbackService = Depends(get_feedback_service)
):
    """
    提交用户反馈

    提交用户对问答答案的反馈，系统会自动分析负面反馈并生成改进建议。

    Args:
        request: 反馈提交参数
            - qa_id: 问答记录ID
            - feedback: 反馈值（1-满意 0-不满意）
            - feedback_reason: 反馈原因
            - quality_score: 质量评分（1-5）

    Returns:
        提交结果，包含分析记录ID（仅负面反馈时）
    """
    result = service.submit_feedback(request)
    return success_response(data=result, message="反馈提交成功")


@router.get("/logs", summary="查询问答日志列表")
async def query_qa_logs(
    tenant_id: int = Query(1, description="租户ID"),
    user_id: Optional[int] = Query(None, description="用户ID"),
    session_id: Optional[str] = Query(None, description="会话ID"),
    start_date: Optional[str] = Query(None, description="开始日期 YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束日期 YYYY-MM-DD"),
    has_feedback: Optional[bool] = Query(None, description="是否有反馈"),
    feedback_value: Optional[int] = Query(None, description="反馈值：1-满意 0-不满意"),
    min_score: Optional[int] = Query(None, ge=1, le=5, description="最低评分"),
    max_score: Optional[int] = Query(None, ge=1, le=5, description="最高评分"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    page_no: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    service: FeedbackService = Depends(get_feedback_service)
):
    """
    查询问答日志列表

    支持多条件筛选查询问答历史记录。

    Args:
        tenant_id: 租户ID
        user_id: 用户ID
        session_id: 会话ID
        start_date: 开始日期
        end_date: 结束日期
        has_feedback: 是否有反馈
        feedback_value: 反馈值
        min_score: 最低评分
        max_score: 最高评分
        keyword: 关键词
        page_no: 页码
        page_size: 每页数量

    Returns:
        分页后的问答日志列表
    """
    request = QALogQueryRequest(
        tenant_id=tenant_id,
        user_id=user_id,
        session_id=session_id,
        start_date=start_date,
        end_date=end_date,
        has_feedback=has_feedback,
        feedback_value=feedback_value,
        min_score=min_score,
        max_score=max_score,
        keyword=keyword,
        page_no=page_no,
        page_size=page_size
    )
    result = service.query_qa_logs(request)
    return page_response(
        items=result["items"],
        total=result["total"],
        page_no=page_no,
        page_size=page_size
    )


@router.get("/logs/{qa_id}", summary="获取问答日志详情")
async def get_qa_log_detail(
    qa_id: int,
    service: FeedbackService = Depends(get_feedback_service)
):
    """
    获取问答日志详情

    获取指定问答记录的详细信息，包括反馈分析结果。

    Args:
        qa_id: 问答日志ID

    Returns:
        问答日志详情
    """
    result = service.get_qa_log_detail(qa_id)
    return success_response(data=result)


@router.get("/feedback/statistics", summary="获取反馈统计信息")
async def get_feedback_statistics(
    tenant_id: int = Query(1, description="租户ID"),
    start_date: Optional[str] = Query(None, description="开始日期 YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束日期 YYYY-MM-DD"),
    service: FeedbackService = Depends(get_feedback_service)
):
    """
    获取反馈统计信息

    获取指定时间范围内的反馈统计信息，包括正负面反馈比例、高频问题类型等。

    Args:
        tenant_id: 租户ID
        start_date: 开始日期
        end_date: 结束日期

    Returns:
        反馈统计信息
    """
    result = service.get_feedback_statistics(tenant_id, start_date, end_date)
    return success_response(data=result)


@router.get("/analysis", summary="查询反馈分析列表")
async def query_feedback_analysis(
    tenant_id: int = Query(1, description="租户ID"),
    issue_type: Optional[str] = Query(None, description="问题类型"),
    handled_status: Optional[int] = Query(None, description="处理状态"),
    page_no: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
):
    """
    查询反馈分析列表

    查询已生成的反馈分析记录。

    Args:
        tenant_id: 租户ID
        issue_type: 问题类型
        handled_status: 处理状态（0-未处理 1-已处理 2-已忽略）
        page_no: 页码
        page_size: 每页数量

    Returns:
        分页后的反馈分析列表
    """
    from core.database import SessionLocal
    from app.models.feedback import FeedbackAnalysis
    from app.models.qa import QALog
    from sqlalchemy import func

    db = SessionLocal()
    try:
        query = db.query(FeedbackAnalysis).join(
            QALog, FeedbackAnalysis.qa_log_id == QALog.id
        ).filter(QALog.tenant_id == tenant_id)

        if issue_type:
            query = query.filter(FeedbackAnalysis.issue_type == issue_type)

        if handled_status is not None:
            query = query.filter(FeedbackAnalysis.handled_status == handled_status)

        total = query.count()

        offset = (page_no - 1) * page_size
        items = query.order_by(FeedbackAnalysis.created_at.desc()).offset(offset).limit(page_size).all()

        result_items = []
        for item in items:
            suggestions_list = []
            if item.suggestions:
                try:
                    import json
                    suggestions_list = json.loads(item.suggestions) if isinstance(item.suggestions, str) else item.suggestions
                except (json.JSONDecodeError, TypeError):
                    suggestions_list = []

            result_items.append({
                "id": item.id,
                "qa_log_id": item.qa_log_id,
                "issue_type": item.issue_type,
                "issue_category": item.issue_category,
                "issue_description": item.issue_description,
                "suggestions": suggestions_list,
                "suggestion_type": item.suggestion_type,
                "handled_status": item.handled_status or 0,
                "created_at": item.created_at
            })

        return page_response(
            items=result_items,
            total=total,
            page_no=page_no,
            page_size=page_size
        )
    finally:
        db.close()


@router.post("/analysis/{analysis_id}/handle", summary="处理反馈分析")
async def handle_feedback_analysis(
    analysis_id: int,
    status: int = Query(..., ge=1, le=2, description="处理状态：1-已处理 2-已忽略"),
    handler_id: int = Query(..., description="处理人ID"),
    remark: Optional[str] = Query(None, description="处理备注"),
    service: FeedbackService = Depends(get_feedback_service)
):
    """
    处理反馈分析

    标记反馈分析记录的处理状态。

    Args:
        analysis_id: 分析记录ID
        status: 处理状态（1-已处理 2-已忽略）
        handler_id: 处理人ID
        remark: 处理备注

    Returns:
        操作结果
    """
    service.handle_feedback_analysis(analysis_id, handler_id, status, remark)
    return success_response(message="处理成功")


@router.get("/rules", summary="查询优化规则列表")
async def get_optimization_rules(
    rule_type: Optional[str] = Query(None, description="规则类型"),
    enabled: Optional[bool] = Query(None, description="是否启用"),
    page_no: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    service: FeedbackService = Depends(get_feedback_service)
):
    """
    查询优化规则列表

    获取系统中的优化规则配置。

    Args:
        rule_type: 规则类型（cleaning/chunking/retrieval/rerank）
        enabled: 是否启用
        page_no: 页码
        page_size: 每页数量

    Returns:
        分页后的优化规则列表
    """
    result = service.get_optimization_rules(rule_type, enabled, page_no, page_size)
    return page_response(
        items=result["items"],
        total=result["total"],
        page_no=page_no,
        page_size=page_size
    )


@router.post("/rules", summary="创建优化规则")
async def create_optimization_rule(
    request: OptimizationRuleRequest,
    creator_id: Optional[int] = Query(None, description="创建人ID"),
    service: FeedbackService = Depends(get_feedback_service)
):
    """
    创建优化规则

    创建新的优化规则，用于指导系统持续改进。

    Args:
        request: 规则配置
        creator_id: 创建人ID

    Returns:
        创建的规则
    """
    result = service.create_optimization_rule(request, creator_id)
    return success_response(data=result, message="规则创建成功")


@router.put("/rules/{rule_id}", summary="更新优化规则")
async def update_optimization_rule(
    rule_id: int,
    request: OptimizationRuleRequest,
    updater_id: Optional[int] = Query(None, description="更新人ID"),
    service: FeedbackService = Depends(get_feedback_service)
):
    """
    更新优化规则

    更新现有的优化规则配置。

    Args:
        rule_id: 规则ID
        request: 规则配置
        updater_id: 更新人ID

    Returns:
        更新的规则
    """
    result = service.update_optimization_rule(rule_id, request, updater_id)
    return success_response(data=result, message="规则更新成功")


@router.delete("/rules/{rule_id}", summary="删除优化规则")
async def delete_optimization_rule(
    rule_id: int,
    service: FeedbackService = Depends(get_feedback_service)
):
    """
    删除优化规则

    删除指定的优化规则。

    Args:
        rule_id: 规则ID

    Returns:
        操作结果
    """
    service.delete_optimization_rule(rule_id)
    return success_response(message="规则删除成功")


@router.get("/sessions", summary="查询会话列表")
async def list_sessions(
    user_id: Optional[int] = Query(None, description="用户ID"),
    tenant_id: int = Query(1, description="租户ID"),
    page_no: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    service: QAService = Depends(get_qa_service)
):
    """
    查询会话列表

    获取用户的会话列表。

    Args:
        user_id: 用户ID
        tenant_id: 租户ID
        page_no: 页码
        page_size: 每页数量

    Returns:
        分页后的会话列表
    """
    result = service.list_sessions(user_id, tenant_id, page_no, page_size)
    return page_response(
        items=result["items"],
        total=result["total"],
        page_no=page_no,
        page_size=page_size
    )


@router.get("/statistics", response_model=QAStatistics)
async def get_statistics(
    tenant_id: int = Query(1, description="租户ID"),
    start_date: Optional[str] = Query(None, description="开始日期 YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束日期 YYYY-MM-DD"),
    service: QAService = Depends(get_qa_service)
):
    """
    获取问答统计信息

    获取指定时间范围内的问答统计信息。

    Args:
        tenant_id: 租户ID
        start_date: 开始日期
        end_date: 结束日期

    Returns:
        统计信息
    """
    result = service.get_statistics(tenant_id, start_date, end_date)
    return success_response(data=result)


# ================================================
# 清洗规则优化相关接口
# ================================================

@router.get("/cleaning/suggestions", summary="获取清洗规则优化建议")
async def get_cleaning_optimization_suggestions(
    tenant_id: int = Query(1, description="租户ID"),
    time_window_days: int = Query(7, ge=1, le=30, description="分析时间窗口（天）"),
    min_occurrence: int = Query(3, ge=1, description="最小出现次数"),
    service: FeedbackService = Depends(get_feedback_service)
):
    """
    获取清洗规则优化建议

    基于反馈数据分析，生成清洗规则优化建议。

    Args:
        tenant_id: 租户ID
        time_window_days: 分析时间窗口（天）
        min_occurrence: 最小出现次数

    Returns:
        优化建议列表
    """
    result = service.get_cleaning_optimization_suggestions(
        tenant_id=tenant_id,
        time_window_days=time_window_days,
        min_occurrence=min_occurrence
    )
    return success_response(data={"items": result})


@router.get("/cleaning/patterns", summary="获取高频问题模式")
async def get_high_frequency_patterns(
    tenant_id: int = Query(1, description="租户ID"),
    time_window_days: int = Query(7, ge=1, le=30, description="时间窗口（天）"),
    limit: int = Query(10, ge=1, le=50, description="返回数量"),
    service: FeedbackService = Depends(get_feedback_service)
):
    """
    获取高频问题模式

    获取反馈中高频出现的问题类型统计。

    Args:
        tenant_id: 租户ID
        time_window_days: 时间窗口
        limit: 返回数量

    Returns:
        高频问题模式列表
    """
    result = service.get_high_frequency_patterns(
        tenant_id=tenant_id,
        time_window_days=time_window_days,
        limit=limit
    )
    return success_response(data={"items": result})


@router.post("/cleaning/apply", summary="应用清洗规则优化")
async def apply_cleaning_optimization(
    optimization_data: dict,
    operator_id: int = Query(..., description="操作人ID"),
    service: FeedbackService = Depends(get_feedback_service)
):
    """
    应用清洗规则优化

    将清洗规则优化建议应用到系统中。

    Args:
        optimization_data: 优化数据
        operator_id: 操作人ID

    Returns:
        操作结果
    """
    success = service.apply_cleaning_optimization(optimization_data, operator_id)
    if success:
        return success_response(message="清洗规则优化应用成功")
    else:
        return success_response(message="清洗规则优化应用失败", data={"success": False})


# ================================================
# 审核相关接口
# ================================================

@router.post("/rules/{rule_id}/submit", summary="提交规则审核")
async def submit_rule_for_review(
    rule_id: int,
    operator_id: int = Query(..., description="操作人ID"),
    operator_name: Optional[str] = Query(None, description="操作人姓名"),
    service: FeedbackService = Depends(get_feedback_service)
):
    """
    提交规则审核

    将规则提交给审核人员进行审核。

    Args:
        rule_id: 规则ID
        operator_id: 操作人ID
        operator_name: 操作人姓名

    Returns:
        操作结果
    """
    success = service.submit_rule_for_review(
        rule_id=rule_id,
        operator_id=operator_id,
        operator_name=operator_name
    )
    if success:
        return success_response(message="规则已提交审核")
    else:
        return success_response(message="规则提交审核失败", data={"success": False})


@router.post("/rules/{rule_id}/approve", summary="审核通过规则")
async def approve_rule(
    rule_id: int,
    reviewer_id: int = Query(..., description="审核人ID"),
    reviewer_name: Optional[str] = Query(None, description="审核人姓名"),
    comment: Optional[str] = Query(None, description="审核意见"),
    service: FeedbackService = Depends(get_feedback_service)
):
    """
    审核通过规则

    审核人员通过规则，规则将进入待启用状态。

    Args:
        rule_id: 规则ID
        reviewer_id: 审核人ID
        reviewer_name: 审核人姓名
        comment: 审核意见

    Returns:
        操作结果
    """
    success = service.approve_rule(
        rule_id=rule_id,
        reviewer_id=reviewer_id,
        reviewer_name=reviewer_name,
        comment=comment
    )
    if success:
        return success_response(message="规则审核通过")
    else:
        return success_response(message="规则审核失败", data={"success": False})


@router.post("/rules/{rule_id}/reject", summary="审核拒绝规则")
async def reject_rule(
    rule_id: int,
    reviewer_id: int = Query(..., description="审核人ID"),
    reviewer_name: Optional[str] = Query(None, description="审核人姓名"),
    comment: Optional[str] = Query(None, description="拒绝原因"),
    service: FeedbackService = Depends(get_feedback_service)
):
    """
    审核拒绝规则

    审核人员拒绝规则，规则将回到草稿状态。

    Args:
        rule_id: 规则ID
        reviewer_id: 审核人ID
        reviewer_name: 审核人姓名
        comment: 拒绝原因

    Returns:
        操作结果
    """
    success = service.reject_rule(
        rule_id=rule_id,
        reviewer_id=reviewer_id,
        reviewer_name=reviewer_name,
        comment=comment
    )
    if success:
        return success_response(message="规则已拒绝")
    else:
        return success_response(message="规则拒绝失败", data={"success": False})


@router.post("/rules/{rule_id}/enable", summary="启用规则")
async def enable_rule(
    rule_id: int,
    operator_id: int = Query(..., description="操作人ID"),
    operator_name: Optional[str] = Query(None, description="操作人姓名"),
    service: FeedbackService = Depends(get_feedback_service)
):
    """
    启用规则

    将已审核通过的规则启用，使其生效。

    Args:
        rule_id: 规则ID
        operator_id: 操作人ID
        operator_name: 操作人姓名

    Returns:
        操作结果
    """
    success = service.enable_rule(
        rule_id=rule_id,
        operator_id=operator_id,
        operator_name=operator_name
    )
    if success:
        return success_response(message="规则已启用")
    else:
        return success_response(message="规则启用失败", data={"success": False})


@router.post("/rules/{rule_id}/disable", summary="禁用规则")
async def disable_rule(
    rule_id: int,
    operator_id: int = Query(..., description="操作人ID"),
    operator_name: Optional[str] = Query(None, description="操作人姓名"),
    service: FeedbackService = Depends(get_feedback_service)
):
    """
    禁用规则

    禁用已启用的规则。

    Args:
        rule_id: 规则ID
        operator_id: 操作人ID
        operator_name: 操作人姓名

    Returns:
        操作结果
    """
    success = service.disable_rule(
        rule_id=rule_id,
        operator_id=operator_id,
        operator_name=operator_name
    )
    if success:
        return success_response(message="规则已禁用")
    else:
        return success_response(message="规则禁用失败", data={"success": False})


@router.get("/rules/audit/logs", summary="获取审核日志")
async def get_audit_logs(
    rule_id: Optional[int] = Query(None, description="规则ID"),
    operator_id: Optional[int] = Query(None, description="操作人ID"),
    action: Optional[str] = Query(None, description="操作类型"),
    start_date: Optional[str] = Query(None, description="开始日期 YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束日期 YYYY-MM-DD"),
    page_no: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    service: FeedbackService = Depends(get_feedback_service)
):
    """
    获取审核日志

    查询规则审核的操作日志。

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
    result = service.get_audit_logs(
        rule_id=rule_id,
        operator_id=operator_id,
        action=action,
        start_date=start_date,
        end_date=end_date,
        page_no=page_no,
        page_size=page_size
    )
    return page_response(
        items=result["items"],
        total=result["total"],
        page_no=page_no,
        page_size=page_size
    )


@router.get("/rules/pending", summary="获取待审核规则")
async def get_pending_approvals(
    tenant_id: int = Query(1, description="租户ID"),
    page_no: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    service: FeedbackService = Depends(get_feedback_service)
):
    """
    获取待审核规则

    查询所有待审核的规则列表。

    Args:
        tenant_id: 租户ID
        page_no: 页码
        page_size: 每页数量

    Returns:
        待审核规则列表
    """
    result = service.get_pending_approvals(
        tenant_id=tenant_id,
        page_no=page_no,
        page_size=page_size
    )
    return page_response(
        items=result["items"],
        total=result["total"],
        page_no=page_no,
        page_size=page_size
    )


@router.get("/rules/{rule_id}/effect", summary="评估规则效果")
async def evaluate_rule_effect(
    rule_id: int,
    time_window_hours: int = Query(24, ge=1, le=168, description="评估时间窗口（小时）"),
    service: FeedbackService = Depends(get_feedback_service)
):
    """
    评估规则效果

    评估规则应用后的效果。

    Args:
        rule_id: 规则ID
        time_window_hours: 评估时间窗口

    Returns:
        效果评估结果
    """
    result = service.evaluate_rule_effect(
        rule_id=rule_id,
        time_window_hours=time_window_hours
    )
    return success_response(data=result)
