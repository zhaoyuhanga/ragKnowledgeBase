# -*- coding: utf-8 -*-
"""
检索融合服务

本模块提供检索结果融合功能，包括：
- RRF融合算法
- 加权融合算法
- 权限过滤
- 业务过滤
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

from app.common.logging import logger
from core.config import settings


@dataclass
class RetrievalItem:
    """检索项"""
    chunk_id: int
    document_id: int
    version_id: int
    title_path: Optional[str] = None
    page_start: Optional[int] = None
    page_end: Optional[int] = None
    content: str = ""
    chunk_type: str = "paragraph"
    vector_score: float = 0.0
    keyword_score: float = 0.0
    fusion_score: float = 0.0
    rank_vector: int = 0
    rank_keyword: int = 0


@dataclass
class FilterCriteria:
    """过滤条件"""
    tenant_ids: Optional[List[int]] = None
    user_ids: Optional[List[int]] = None
    document_ids: Optional[Set[int]] = None
    version_ids: Optional[Set[int]] = None
    chunk_types: Optional[Set[str]] = None
    min_quality_score: Optional[float] = None
    active_versions_only: bool = True


@dataclass
class FusionConfig:
    """融合配置"""
    vector_top_k: int = 100
    keyword_top_k: int = 100
    rrf_k: int = 60
    fusion_top_k: int = 20
    vector_weight: float = 0.6
    keyword_weight: float = 0.4
    enable_rrf: bool = True


class FusionService:
    """
    检索融合服务

    提供检索结果的融合和过滤功能：
    - RRF（Reciprocal Rank Fusion）融合
    - 加权融合
    - 权限过滤
    - 业务过滤
    """

    def __init__(self, config: Optional[FusionConfig] = None):
        """
        初始化融合服务

        Args:
            config: 融合配置
        """
        self._config = config or self._load_config()
        self._cache: Dict[str, Any] = {}

    def _load_config(self) -> FusionConfig:
        """从配置加载融合参数"""
        return FusionConfig(
            vector_top_k=settings.retrieval.vector_top_k,
            keyword_top_k=settings.retrieval.keyword_top_k,
            rrf_k=settings.retrieval.rrf_k,
            fusion_top_k=settings.retrieval.fusion_top_k,
            vector_weight=settings.retrieval.vector_weight,
            keyword_weight=settings.retrieval.keyword_weight,
        )

    def rrf_fusion(
        self,
        vector_results: List[RetrievalItem],
        keyword_results: List[RetrievalItem],
        k: Optional[int] = None
    ) -> List[RetrievalItem]:
        """
        RRF融合

        使用Reciprocal Rank Fusion算法融合向量检索和关键词检索结果。

        RRF公式：score(d) = Σ(1 / (k + rank(d)))

        Args:
            vector_results: 向量检索结果
            keyword_results: 关键词检索结果
            k: RRF参数k

        Returns:
            融合后的结果列表
        """
        if k is None:
            k = self._config.rrf_k

        if not vector_results and not keyword_results:
            return []

        if not vector_results:
            return keyword_results[:self._config.fusion_top_k]

        if not keyword_results:
            return vector_results[:self._config.fusion_top_k]

        # 构建排名映射
        vector_ranks = {item.chunk_id: rank for rank, item in enumerate(vector_results)}
        keyword_ranks = {item.chunk_id: rank for rank, item in enumerate(keyword_results)}

        # 获取所有chunk_id
        all_chunk_ids = set(vector_ranks.keys()) | set(keyword_ranks.keys())

        # 计算RRF分数
        rrf_scores: Dict[int, float] = {}
        for chunk_id in all_chunk_ids:
            score = 0.0

            if chunk_id in vector_ranks:
                rank = vector_ranks[chunk_id]
                score += 1.0 / (k + rank + 1)

            if chunk_id in keyword_ranks:
                rank = keyword_ranks[chunk_id]
                score += 1.0 / (k + rank + 1)

            rrf_scores[chunk_id] = score

        # 构建结果映射
        all_items: Dict[int, RetrievalItem] = {}
        for item in vector_results:
            all_items[item.chunk_id] = item
        for item in keyword_results:
            if item.chunk_id in all_items:
                all_items[item.chunk_id].keyword_score = item.keyword_score
            else:
                all_items[item.chunk_id] = item

        # 按RRF分数排序
        fused_results = sorted(
            all_items.values(),
            key=lambda x: rrf_scores.get(x.chunk_id, 0),
            reverse=True
        )

        # 更新融合分数
        for item in fused_results:
            item.fusion_score = rrf_scores.get(item.chunk_id, 0)

        # 返回top_k
        return fused_results[:self._config.fusion_top_k]

    def weighted_fusion(
        self,
        vector_results: List[RetrievalItem],
        keyword_results: List[RetrievalItem],
        vector_weight: Optional[float] = None,
        keyword_weight: Optional[float] = None
    ) -> List[RetrievalItem]:
        """
        加权融合

        使用加权平均的方式融合向量检索和关键词检索结果。

        Args:
            vector_results: 向量检索结果
            keyword_results: 关键词检索结果
            vector_weight: 向量权重
            keyword_weight: 关键词权重

        Returns:
            融合后的结果列表
        """
        if vector_weight is None:
            vector_weight = self._config.vector_weight
        if keyword_weight is None:
            keyword_weight = self._config.keyword_weight

        if not vector_results and not keyword_results:
            return []

        if not vector_results:
            return keyword_results[:self._config.fusion_top_k]

        if not keyword_results:
            return vector_results[:self._config.fusion_top_k]

        # 归一化分数
        max_vector_score = max(item.vector_score for item in vector_results) if vector_results else 1.0
        max_keyword_score = max(item.keyword_score for item in keyword_results) if keyword_results else 1.0

        # 构建结果映射
        all_items: Dict[int, RetrievalItem] = {}
        for item in vector_results:
            item.vector_score = item.vector_score / max_vector_score if max_vector_score > 0 else 0
            all_items[item.chunk_id] = item

        for item in keyword_results:
            normalized_score = item.keyword_score / max_keyword_score if max_keyword_score > 0 else 0
            if item.chunk_id in all_items:
                all_items[item.chunk_id].keyword_score = normalized_score
            else:
                item.keyword_score = normalized_score
                all_items[item.chunk_id] = item

        # 计算加权分数
        for item in all_items.values():
            item.fusion_score = (
                vector_weight * item.vector_score +
                keyword_weight * item.keyword_score
            )

        # 按加权分数排序
        fused_results = sorted(
            all_items.values(),
            key=lambda x: x.fusion_score,
            reverse=True
        )

        return fused_results[:self._config.fusion_top_k]

    def rank_fusion(
        self,
        vector_results: List[RetrievalItem],
        keyword_results: List[RetrievalItem]
    ) -> List[RetrievalItem]:
        """
        排名融合（组合RRF和加权）

        综合使用RRF和加权融合的结果。

        Args:
            vector_results: 向量检索结果
            keyword_results: 关键词检索结果

        Returns:
            融合后的结果列表
        """
        # 获取两种融合结果
        rrf_results = self.rrf_fusion(vector_results, keyword_results)
        weighted_results = self.weighted_fusion(vector_results, keyword_results)

        if not rrf_results:
            return weighted_results
        if not weighted_results:
            return rrf_results

        # 为每种结果分配权重并重新排序
        rrf_scores = {item.chunk_id: item.fusion_score for item in rrf_results}
        weighted_scores = {item.chunk_id: item.fusion_score for item in weighted_results}

        # 获取所有chunk_id
        all_chunk_ids = set(rrf_scores.keys()) | set(weighted_scores.keys())

        # 综合分数
        combined_scores: Dict[int, float] = {}
        for chunk_id in all_chunk_ids:
            rrf_score = rrf_scores.get(chunk_id, 0)
            weighted_score = weighted_scores.get(chunk_id, 0)
            combined_scores[chunk_id] = 0.5 * rrf_score + 0.5 * weighted_score

        # 构建完整结果
        all_items: Dict[int, RetrievalItem] = {}
        for item in rrf_results:
            all_items[item.chunk_id] = item
        for item in weighted_results:
            if item.chunk_id not in all_items:
                all_items[item.chunk_id] = item

        # 按综合分数排序
        fused_results = sorted(
            all_items.values(),
            key=lambda x: combined_scores.get(x.chunk_id, 0),
            reverse=True
        )

        # 更新融合分数
        for item in fused_results:
            item.fusion_score = combined_scores.get(item.chunk_id, 0)

        return fused_results[:self._config.fusion_top_k]

    def filter_by_permissions(
        self,
        items: List[RetrievalItem],
        criteria: FilterCriteria
    ) -> List[RetrievalItem]:
        """
        权限过滤

        根据权限条件过滤检索结果。

        Args:
            items: 检索结果列表
            criteria: 过滤条件

        Returns:
            过滤后的结果列表
        """
        filtered = []

        for item in items:
            # 检查文档ID过滤
            if criteria.document_ids and item.document_id not in criteria.document_ids:
                continue

            # 检查版本ID过滤
            if criteria.version_ids and item.version_id not in criteria.version_ids:
                continue

            # 检查Chunk类型过滤
            if criteria.chunk_types and item.chunk_type not in criteria.chunk_types:
                continue

            # 检查质量评分
            # 注意：RetrievalItem没有quality_score字段，需要扩展

            filtered.append(item)

        logger.info(
            "权限过滤完成",
            extra={
                "input_count": len(items),
                "output_count": len(filtered),
                "filter_type": "permission"
            }
        )

        return filtered

    def filter_by_business(
        self,
        items: List[RetrievalItem],
        criteria: FilterCriteria
    ) -> List[RetrievalItem]:
        """
        业务过滤

        根据业务条件过滤检索结果。

        Args:
            items: 检索结果列表
            criteria: 过滤条件

        Returns:
            过滤后的结果列表
        """
        filtered = items

        # 只返回活跃版本
        if criteria.active_versions_only:
            # 这里需要查询数据库确认版本状态
            # 目前先保留所有结果
            pass

        logger.info(
            "业务过滤完成",
            extra={
                "input_count": len(items),
                "output_count": len(filtered),
                "filter_type": "business"
            }
        )

        return filtered

    def deduplicate(
        self,
        items: List[RetrievalItem],
        strategy: str = "higher_score"
    ) -> List[RetrievalItem]:
        """
        去重处理

        对检索结果进行去重处理。

        Args:
            items: 检索结果列表
            strategy: 去重策略（higher_score-保留高分, first-保留第一个）

        Returns:
            去重后的结果列表
        """
        if not items:
            return []

        seen: Dict[int, RetrievalItem] = {}

        for item in items:
            # 使用chunk_id作为唯一标识
            if item.chunk_id not in seen:
                seen[item.chunk_id] = item
            else:
                # 冲突时根据策略保留
                if strategy == "higher_score":
                    existing = seen[item.chunk_id]
                    if item.fusion_score > existing.fusion_score:
                        seen[item.chunk_id] = item

        result = list(seen.values())

        logger.info(
            "去重完成",
            extra={
                "input_count": len(items),
                "output_count": len(result),
                "strategy": strategy
            }
        )

        return result

    def apply_filters(
        self,
        items: List[RetrievalItem],
        criteria: FilterCriteria
    ) -> List[RetrievalItem]:
        """
        应用所有过滤条件

        按顺序应用权限过滤和业务过滤。

        Args:
            items: 检索结果列表
            criteria: 过滤条件

        Returns:
            过滤后的结果列表
        """
        # 1. 权限过滤
        filtered = self.filter_by_permissions(items, criteria)

        # 2. 业务过滤
        filtered = self.filter_by_business(filtered, criteria)

        # 3. 去重
        filtered = self.deduplicate(filtered)

        return filtered


# 全局服务实例
_fusion_service: Optional[FusionService] = None


def get_fusion_service(config: Optional[FusionConfig] = None) -> FusionService:
    """
    获取融合服务实例

    Args:
        config: 融合配置

    Returns:
        融合服务实例
    """
    global _fusion_service
    if _fusion_service is None or config is not None:
        _fusion_service = FusionService(config)
    return _fusion_service
