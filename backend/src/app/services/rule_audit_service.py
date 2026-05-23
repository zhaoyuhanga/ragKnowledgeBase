# -*- coding: utf-8 -*-
"""
规则审核服务

本模块提供规则审核功能：
- 规则创建审核
- 规则修改审核
- 规则删除审核
- 审核历史记录
"""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from app.common.logging import logger


class RuleAuditService:
    """
    规则审核服务

    管理优化规则的审核流程和审核日志。
    """

    # 审核操作类型
    ACTION_CREATE = "create"
    ACTION_UPDATE = "update"
    ACTION_DELETE = "delete"
    ACTION_ENABLE = "enable"
    ACTION_DISABLE = "disable"
    ACTION_SUBMIT_REVIEW = "submit_review"
    ACTION_APPROVE = "approve"
    ACTION_REJECT = "reject"

    # 规则状态
    STATUS_DRAFT = 0
    STATUS_PENDING_APPROVAL = 1
    STATUS_APPROVED = 2
    STATUS_REJECTED = 3
    STATUS_ENABLED = 4
    STATUS_DISABLED = 5

    def __init__(self):
        """初始化审核服务"""
        pass

    def submit_for_review(
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
        from core.database import SessionLocal
        from app.models.feedback import OptimizationRule, RuleAuditLog

        db = SessionLocal()
        try:
            rule = db.query(OptimizationRule).filter(
                OptimizationRule.id == rule_id
            ).first()

            if not rule:
                logger.warning(f"提交审核失败，规则不存在: {rule_id}")
                return False

            # 检查状态
            if rule.status not in [self.STATUS_DRAFT, self.STATUS_REJECTED]:
                logger.warning(
                    f"规则状态不允许提交审核: {rule_id}, 当前状态: {rule.status}"
                )
                return False

            before_status = rule.status

            # 更新规则状态
            rule.status = self.STATUS_PENDING_APPROVAL

            # 记录审核日志
            self._create_audit_log(
                db=db,
                rule_id=rule_id,
                action=self.ACTION_SUBMIT_REVIEW,
                operator_id=operator_id,
                operator_name=operator_name,
                before_status=before_status,
                after_status=self.STATUS_PENDING_APPROVAL,
                ip_address=ip_address
            )

            db.commit()

            logger.info(
                f"规则提交审核成功: {rule_id}",
                extra={
                    "rule_id": rule_id,
                    "operator_id": operator_id,
                    "rule_name": rule.rule_name
                }
            )

            return True

        except Exception as e:
            db.rollback()
            logger.error(f"提交审核失败: {str(e)}")
            return False

        finally:
            db.close()

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
        from core.database import SessionLocal
        from app.models.feedback import OptimizationRule, RuleAuditLog

        db = SessionLocal()
        try:
            rule = db.query(OptimizationRule).filter(
                OptimizationRule.id == rule_id
            ).first()

            if not rule:
                logger.warning(f"审核失败，规则不存在: {rule_id}")
                return False

            # 检查状态
            if rule.status != self.STATUS_PENDING_APPROVAL:
                logger.warning(
                    f"规则状态不允许审核: {rule_id}, 当前状态: {rule.status}"
                )
                return False

            before_status = rule.status

            # 更新规则状态
            rule.status = self.STATUS_APPROVED
            rule.approved_by = reviewer_id
            rule.approved_at = datetime.now()
            rule.approval_comment = comment

            # 记录审核日志
            self._create_audit_log(
                db=db,
                rule_id=rule_id,
                action=self.ACTION_APPROVE,
                operator_id=reviewer_id,
                operator_name=reviewer_name,
                before_status=before_status,
                after_status=self.STATUS_APPROVED,
                comment=comment,
                ip_address=ip_address
            )

            db.commit()

            logger.info(
                f"规则审核通过: {rule_id}",
                extra={
                    "rule_id": rule_id,
                    "reviewer_id": reviewer_id,
                    "rule_name": rule.rule_name
                }
            )

            return True

        except Exception as e:
            db.rollback()
            logger.error(f"审核失败: {str(e)}")
            return False

        finally:
            db.close()

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
        from core.database import SessionLocal
        from app.models.feedback import OptimizationRule, RuleAuditLog

        db = SessionLocal()
        try:
            rule = db.query(OptimizationRule).filter(
                OptimizationRule.id == rule_id
            ).first()

            if not rule:
                logger.warning(f"拒绝失败，规则不存在: {rule_id}")
                return False

            # 检查状态
            if rule.status != self.STATUS_PENDING_APPROVAL:
                logger.warning(
                    f"规则状态不允许拒绝: {rule_id}, 当前状态: {rule.status}"
                )
                return False

            before_status = rule.status

            # 更新规则状态
            rule.status = self.STATUS_REJECTED
            rule.approved_by = reviewer_id
            rule.approved_at = datetime.now()
            rule.approval_comment = comment

            # 记录审核日志
            self._create_audit_log(
                db=db,
                rule_id=rule_id,
                action=self.ACTION_REJECT,
                operator_id=reviewer_id,
                operator_name=reviewer_name,
                before_status=before_status,
                after_status=self.STATUS_REJECTED,
                comment=comment,
                ip_address=ip_address
            )

            db.commit()

            logger.info(
                f"规则审核拒绝: {rule_id}",
                extra={
                    "rule_id": rule_id,
                    "reviewer_id": reviewer_id,
                    "rule_name": rule.rule_name
                }
            )

            return True

        except Exception as e:
            db.rollback()
            logger.error(f"拒绝规则失败: {str(e)}")
            return False

        finally:
            db.close()

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
        from core.database import SessionLocal
        from app.models.feedback import OptimizationRule, RuleAuditLog

        db = SessionLocal()
        try:
            rule = db.query(OptimizationRule).filter(
                OptimizationRule.id == rule_id
            ).first()

            if not rule:
                logger.warning(f"启用失败，规则不存在: {rule_id}")
                return False

            # 检查状态：已审核的规则才能启用
            if rule.status != self.STATUS_APPROVED:
                logger.warning(
                    f"规则必须先审核通过才能启用: {rule_id}, 当前状态: {rule.status}"
                )
                return False

            before_status = rule.status
            rule.enabled = 1
            rule.status = self.STATUS_ENABLED

            # 记录审核日志
            self._create_audit_log(
                db=db,
                rule_id=rule_id,
                action=self.ACTION_ENABLE,
                operator_id=operator_id,
                operator_name=operator_name,
                before_status=before_status,
                after_status=self.STATUS_ENABLED,
                ip_address=ip_address
            )

            db.commit()

            logger.info(
                f"规则已启用: {rule_id}",
                extra={
                    "rule_id": rule_id,
                    "operator_id": operator_id,
                    "rule_name": rule.rule_name
                }
            )

            return True

        except Exception as e:
            db.rollback()
            logger.error(f"启用规则失败: {str(e)}")
            return False

        finally:
            db.close()

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
        from core.database import SessionLocal
        from app.models.feedback import OptimizationRule, RuleAuditLog

        db = SessionLocal()
        try:
            rule = db.query(OptimizationRule).filter(
                OptimizationRule.id == rule_id
            ).first()

            if not rule:
                logger.warning(f"禁用失败，规则不存在: {rule_id}")
                return False

            before_status = rule.status
            before_enabled = rule.enabled

            rule.enabled = 0
            rule.status = self.STATUS_DISABLED

            # 记录审核日志
            self._create_audit_log(
                db=db,
                rule_id=rule_id,
                action=self.ACTION_DISABLE,
                operator_id=operator_id,
                operator_name=operator_name,
                before_status=before_status,
                after_status=self.STATUS_DISABLED,
                ip_address=ip_address
            )

            db.commit()

            logger.info(
                f"规则已禁用: {rule_id}",
                extra={
                    "rule_id": rule_id,
                    "operator_id": operator_id,
                    "rule_name": rule.rule_name
                }
            )

            return True

        except Exception as e:
            db.rollback()
            logger.error(f"禁用规则失败: {str(e)}")
            return False

        finally:
            db.close()

    def get_audit_logs(
        self,
        rule_id: Optional[int] = None,
        operator_id: Optional[int] = None,
        action: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        page_no: int = 1,
        page_size: int = 20
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        获取审核日志列表

        Args:
            rule_id: 规则ID
            operator_id: 操作人ID
            action: 操作类型
            start_date: 开始日期
            end_date: 结束日期
            page_no: 页码
            page_size: 每页数量

        Returns:
            (日志列表, 总数)
        """
        from core.database import SessionLocal
        from app.models.feedback import RuleAuditLog
        from sqlalchemy import and_

        db = SessionLocal()
        try:
            query = db.query(RuleAuditLog)

            # 应用筛选条件
            conditions = []
            if rule_id:
                conditions.append(RuleAuditLog.rule_id == rule_id)
            if operator_id:
                conditions.append(RuleAuditLog.operator_id == operator_id)
            if action:
                conditions.append(RuleAuditLog.action == action)
            if start_date:
                conditions.append(RuleAuditLog.created_at >= datetime.fromisoformat(start_date))
            if end_date:
                end_dt = datetime.fromisoformat(end_date)
                conditions.append(RuleAuditLog.created_at <= end_dt.replace(hour=23, minute=59, second=59))

            if conditions:
                query = query.filter(and_(*conditions))

            # 获取总数
            total = query.count()

            # 分页查询
            offset = (page_no - 1) * page_size
            logs = query.order_by(RuleAuditLog.created_at.desc()).offset(offset).limit(page_size).all()

            # 转换结果
            items = []
            for log in logs:
                items.append({
                    "id": log.id,
                    "rule_id": log.rule_id,
                    "action": log.action,
                    "operator_id": log.operator_id,
                    "operator_name": log.operator_name,
                    "before_status": log.before_status,
                    "after_status": log.after_status,
                    "comment": log.comment,
                    "ip_address": log.ip_address,
                    "created_at": log.created_at.isoformat() if log.created_at else None
                })

            return items, total

        finally:
            db.close()

    def get_pending_approvals(
        self,
        tenant_id: int = 1,
        page_no: int = 1,
        page_size: int = 20
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        获取待审核规则列表

        Args:
            tenant_id: 租户ID
            page_no: 页码
            page_size: 每页数量

        Returns:
            (待审核规则列表, 总数)
        """
        from core.database import SessionLocal
        from app.models.feedback import OptimizationRule

        db = SessionLocal()
        try:
            query = db.query(OptimizationRule).filter(
                OptimizationRule.tenant_id == tenant_id,
                OptimizationRule.status == self.STATUS_PENDING_APPROVAL
            )

            total = query.count()

            offset = (page_no - 1) * page_size
            rules = query.order_by(OptimizationRule.updated_at.asc()).offset(offset).limit(page_size).all()

            items = []
            for rule in rules:
                items.append({
                    "id": rule.id,
                    "rule_name": rule.rule_name,
                    "rule_type": rule.rule_type,
                    "rule_config": rule.rule_config,
                    "trigger_condition": rule.trigger_condition,
                    "priority": rule.priority,
                    "description": rule.description,
                    "expected_effect": rule.expected_effect,
                    "creator_id": rule.creator_id,
                    "created_at": rule.created_at.isoformat() if rule.created_at else None,
                    "updated_at": rule.updated_at.isoformat() if rule.updated_at else None
                })

            return items, total

        finally:
            db.close()

    def _create_audit_log(
        self,
        db,
        rule_id: int,
        action: str,
        operator_id: int,
        operator_name: Optional[str] = None,
        before_status: Optional[int] = None,
        after_status: Optional[int] = None,
        before_config: Optional[str] = None,
        after_config: Optional[str] = None,
        comment: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> None:
        """创建审核日志记录"""
        from app.models.feedback import RuleAuditLog

        log = RuleAuditLog(
            tenant_id=1,  # TODO: 从上下文获取
            rule_id=rule_id,
            action=action,
            operator_id=operator_id,
            operator_name=operator_name,
            before_status=before_status,
            after_status=after_status,
            before_config=before_config,
            after_config=after_config,
            comment=comment,
            ip_address=ip_address
        )

        db.add(log)


# 全局服务实例
_rule_audit_service: Optional[RuleAuditService] = None


def get_rule_audit_service() -> RuleAuditService:
    """获取规则审核服务实例"""
    global _rule_audit_service
    if _rule_audit_service is None:
        _rule_audit_service = RuleAuditService()
    return _rule_audit_service
