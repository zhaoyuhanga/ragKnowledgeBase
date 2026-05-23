# -*- coding: utf-8 -*-
"""
问答日志数据模型

本模块定义问答日志的数据模型。
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, DateTime, Integer, String, Text, BigInteger, Index, JSON

from core.database import Base


class QALog(Base):
    """
    问答日志表

    存储用户问答记录，包括问题、答案、引用来源等。
    """
    __tablename__ = "qa_logs"

    # 主键ID
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="主键ID")

    # 用户ID
    user_id = Column(BigInteger, nullable=True, index=True, comment="用户ID")

    # 租户ID
    tenant_id = Column(BigInteger, default=1, index=True, comment="租户ID")

    # 会话ID
    session_id = Column(String(64), nullable=True, index=True, comment="会话ID")

    # 用户问题
    question = Column(Text, nullable=False, comment="用户问题")

    # 生成的答案
    answer = Column(Text, nullable=True, comment="生成的答案")

    # 引用来源列表（JSON格式）
    references = Column(JSON, nullable=True, comment="引用来源列表")

    # 向量检索结果
    vector_results = Column(JSON, nullable=True, comment="向量检索结果")

    # 关键词检索结果
    keyword_results = Column(JSON, nullable=True, comment="关键词检索结果")

    # 融合检索结果
    fusion_results = Column(JSON, nullable=True, comment="融合检索结果")

    # 重排后结果
    reranked_results = Column(JSON, nullable=True, comment="重排后结果")

    # 检索耗时（毫秒）
    retrieval_time_ms = Column(Integer, nullable=True, comment="检索耗时(毫秒)")

    # 重排耗时（毫秒）
    rerank_time_ms = Column(Integer, nullable=True, comment="重排耗时(毫秒)")

    # 上下文组装耗时（毫秒）
    context_time_ms = Column(Integer, nullable=True, comment="上下文组装耗时(毫秒)")

    # 生成耗时（毫秒）
    generation_time_ms = Column(Integer, nullable=True, comment="生成耗时(毫秒)")

    # 总耗时（毫秒）
    total_time_ms = Column(Integer, nullable=True, comment="总耗时(毫秒)")

    # 答案质量评分
    quality_score = Column(Integer, nullable=True, comment="答案质量评分")

    # 用户反馈：helpful、not_helpful、null
    feedback = Column(String(50), nullable=True, comment="用户反馈")

    # 反馈备注
    feedback_remark = Column(Text, nullable=True, comment="反馈备注")

    # 创建时间
    created_at = Column(DateTime, default=datetime.now, nullable=False, comment="创建时间")

    # 索引定义
    __table_args__ = (
        Index("idx_qa_logs_user_id", "user_id"),
        Index("idx_qa_logs_tenant_id", "tenant_id"),
        Index("idx_qa_logs_session_id", "session_id"),
        Index("idx_qa_logs_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        """返回问答日志对象的字符串表示"""
        return f"<QALog(id={self.id}, user_id={self.user_id}, question={self.question[:50]})>"
