# -*- coding: utf-8 -*-
"""
版面分析器（增强版）

本模块实现增强的文档版面分析，包括：
- 元素排序
- 页眉页脚识别
- 栏结构识别（真实实现）
- 标题层级识别
- 邻接关系建立
- 阅读顺序重排（支持多栏布局）
- 跨页合并
- 表格跨页检测与合并
- 低置信度标记

所有代码注释使用中文，所有日志输出中文。
"""

import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

from app.common.logging import logger
from app.parsers.base import (
    BBox,
    DocumentElementModel,
    ElementType,
    QualityFlag,
)


@dataclass
class ColumnInfo:
    """栏信息"""
    column_index: int  # 栏索引（从0开始）
    x_start: float  # 起始X坐标
    x_end: float  # 结束X坐标
    width: float  # 栏宽度
    elements: List[DocumentElementModel] = field(default_factory=list)  # 栏内元素


@dataclass
class TableSpanInfo:
    """表格跨页信息"""
    table_id: str  # 表格ID
    header_row: Optional[List[str]] = None  # 表头行
    pages: List[int] = field(default_factory=list)  # 跨页页码列表
    rows_per_page: Dict[int, List[List[str]]] = field(default_factory=dict)  # 每页的行
    is_complete: bool = False  # 是否完整


class LayoutAnalyzer:
    """
    版面分析器（增强版）

    对解析后的元素进行版面分析，还原文档结构。
    支持：
    - 真实的栏结构识别
    - 表格跨页检测与合并
    - 多栏布局阅读顺序还原
    """

    def __init__(self):
        """初始化版面分析器"""
        # 页眉页脚位置阈值（相对于页面高度的比例）
        self._header_threshold = 0.05  # 页面顶部5%
        self._footer_threshold = 0.95  # 页面底部5%

        # 栏检测参数
        self._column_gap_threshold = 20  # 栏间距阈值（像素）
        self._min_column_width_ratio = 0.15  # 最小栏宽比例（相对于页面宽度）
        self._max_columns = 4  # 最大栏数

        # 表格跨页检测参数
        self._table_header_keywords = ["名称", "项目", "序号", "编号", "日期", "金额", "类型", "状态"]
        self._max_gap_for_table_merge = 5  # 表格合并最大间距（像素）

        # 页面高度（用于页眉页脚判断，A4纸约842pt或800px）
        self._page_height = 800

    def analyze(self, elements: List[DocumentElementModel]) -> List[DocumentElementModel]:
        """
        版面分析主入口

        Args:
            elements: 原始元素列表

        Returns:
            分析后的元素列表
        """
        start_time = time.time()

        if not elements:
            return elements

        logger.info(
            f"开始版面分析，元素数量: {len(elements)}",
            extra={"element_count": len(elements)}
        )

        try:
            # 1. 按bbox初步排序
            sorted_elements = self._sort_by_bbox(elements)

            # 2. 识别页眉页脚
            sorted_elements = self._identify_headers_footers(sorted_elements)

            # 3. 识别栏结构
            column_info = self._identify_columns(sorted_elements)

            # 4. 检测表格跨页
            table_spans = self._detect_table_spans(sorted_elements)

            # 5. 多栏布局阅读顺序还原
            sorted_elements = self._reorder_multicolumn(sorted_elements, column_info)

            # 6. 合并跨页表格
            sorted_elements = self._merge_cross_page_tables(sorted_elements, table_spans)

            # 7. 建立标题路径
            sorted_elements = self._build_title_paths(sorted_elements)

            # 8. 建立元素邻接关系
            sorted_elements = self._build_adjacency(sorted_elements)

            # 9. 按阅读顺序重排
            sorted_elements = self._reorder_by_reading(sorted_elements)

            # 10. 跨页段落合并
            sorted_elements = self._merge_cross_page_paragraphs(sorted_elements)

            # 11. 低置信度片段标记
            sorted_elements = self._mark_low_confidence(sorted_elements)

            # 12. 重新编号
            for i, elem in enumerate(sorted_elements):
                elem.reading_order = i

            analysis_time_ms = int((time.time() - start_time) * 1000)

            logger.info(
                f"版面分析完成，耗时: {analysis_time_ms}ms",
                extra={
                    "element_count": len(sorted_elements),
                    "column_count": len(column_info) if column_info else 0,
                    "table_span_count": len(table_spans),
                    "analysis_time_ms": analysis_time_ms
                }
            )

            return sorted_elements

        except Exception as e:
            logger.error(f"版面分析失败: {str(e)}")
            return elements

    def _sort_by_bbox(
        self,
        elements: List[DocumentElementModel]
    ) -> List[DocumentElementModel]:
        """
        按坐标排序

        先按页码排序，再按Y坐标排序，最后按X坐标排序。

        Args:
            elements: 元素列表

        Returns:
            排序后的元素列表
        """
        def sort_key(element: DocumentElementModel) -> tuple:
            bbox = element.bbox
            page_no = element.page_no or 0
            y = bbox.y if bbox else 0
            x = bbox.x if bbox else 0
            return (page_no, y, x)

        return sorted(elements, key=sort_key)

    def _identify_headers_footers(
        self,
        elements: List[DocumentElementModel]
    ) -> List[DocumentElementModel]:
        """
        识别页眉页脚

        根据元素位置判断是否为页眉或页脚。

        Args:
            elements: 元素列表

        Returns:
            处理后的元素列表
        """
        # 按页码分组
        page_elements: Dict[int, List[DocumentElementModel]] = defaultdict(list)
        for element in elements:
            page_no = element.page_no or 1
            page_elements[page_no].append(element)

        # 处理每一页
        for page_no, page_list in page_elements.items():
            if not page_list:
                continue

            # 估算页面高度（取最大Y值）
            page_height = max(
                (elem.bbox.y + elem.bbox.height if elem.bbox else 100)
                for elem in page_list
            )
            if page_height > 0:
                self._page_height = page_height

            for element in page_list:
                bbox = element.bbox
                if not bbox:
                    continue

                # 判断是否为页眉（页面顶部区域）
                header_threshold_y = self._page_height * self._header_threshold
                if bbox.y < header_threshold_y:
                    element.element_type = ElementType.HEADER

                # 判断是否为页脚（页面底部区域）
                footer_threshold_y = self._page_height * self._footer_threshold
                if bbox.y > footer_threshold_y:
                    element.element_type = ElementType.FOOTER

        return elements

    def _identify_columns(
        self,
        elements: List[DocumentElementModel]
    ) -> List[ColumnInfo]:
        """
        识别栏结构

        通过分析元素X坐标分布，识别单栏、双栏或多栏布局。

        算法步骤：
        1. 收集所有元素的X坐标和宽度
        2. 寻找X坐标的聚类（使用间隙检测算法）
        3. 识别栏边界
        4. 验证栏结构

        Args:
            elements: 元素列表

        Returns:
            栏信息列表
        """
        if not elements:
            return []

        # 收集有效的文本元素（用于栏分析）
        text_elements = [
            elem for elem in elements
            if elem.bbox and elem.element_type in (
                ElementType.PARAGRAPH,
                ElementType.TITLE
            )
        ]

        if not text_elements:
            return []

        # 提取元素的边界
        boundaries: List[float] = []
        for elem in text_elements:
            boundaries.append(elem.bbox.x)
            boundaries.append(elem.bbox.x + elem.bbox.width)

        if not boundaries:
            return []

        # 使用间隙检测算法识别栏边界
        boundaries.sort()
        gaps: List[Tuple[float, float]] = []  # (gap_start, gap_end)

        for i in range(len(boundaries) - 1):
            gap_start = boundaries[i]
            gap_end = boundaries[i + 1]
            gap_width = gap_end - gap_start

            # 如果间隙足够大，认为是栏间距
            if gap_width >= self._column_gap_threshold:
                gaps.append((gap_start, gap_end))

        if not gaps:
            # 单栏布局
            logger.info("检测到单栏布局")
            return []

        # 合并相邻的大间隙
        merged_gaps = self._merge_adjacent_gaps(gaps)

        if not merged_gaps:
            return []

        # 计算栏
        column_boundaries = [0.0]  # 起始位置
        for gap_start, gap_end in merged_gaps:
            column_boundaries.append(gap_start)
            column_boundaries.append(gap_end)
        column_boundaries.append(max(boundaries))  # 结束位置

        # 构建栏信息
        column_info: List[ColumnInfo] = []
        page_width = max(boundaries)

        for i in range(0, len(column_boundaries) - 1, 2):
            x_start = column_boundaries[i]
            x_end = column_boundaries[i + 1]
            width = x_end - x_start

            # 检查栏宽是否合理（不能太小）
            if width >= page_width * self._min_column_width_ratio:
                column = ColumnInfo(
                    column_index=i // 2,
                    x_start=x_start,
                    x_end=x_end,
                    width=width
                )
                column_info.append(column)

        # 如果识别出的栏数过多或过少，可能识别错误
        if len(column_info) > self._max_columns:
            logger.warning(
                f"识别到的栏数({len(column_info)})过多，可能识别错误",
                extra={"column_count": len(column_info)}
            )
            return []

        if len(column_info) < 2:
            logger.info("识别为单栏布局")
            return []

        logger.info(
            f"识别到{len(column_info)}栏布局",
            extra={
                "column_count": len(column_info),
                "column_widths": [c.width for c in column_info]
            }
        )

        return column_info

    def _merge_adjacent_gaps(
        self,
        gaps: List[Tuple[float, float]]
    ) -> List[Tuple[float, float]]:
        """
        合并相邻的间隙

        如果两个间隙之间的距离小于阈值，则合并。

        Args:
            gaps: 间隙列表

        Returns:
            合并后的间隙列表
        """
        if not gaps:
            return []

        merged: List[Tuple[float, float]] = []
        current_start, current_end = gaps[0]

        for gap_start, gap_end in gaps[1:]:
            # 如果间隙重叠或相邻
            if gap_start <= current_end + self._column_gap_threshold:
                current_end = max(current_end, gap_end)
            else:
                merged.append((current_start, current_end))
                current_start, current_end = gap_start, gap_end

        merged.append((current_start, current_end))
        return merged

    def _detect_table_spans(
        self,
        elements: List[DocumentElementModel]
    ) -> Dict[str, TableSpanInfo]:
        """
        检测表格跨页

        识别跨页的表格并记录其结构信息。

        Args:
            elements: 元素列表

        Returns:
            表格跨页信息字典
        """
        table_spans: Dict[str, TableSpanInfo] = {}

        # 按页码分组表格元素
        page_tables: Dict[int, List[DocumentElementModel]] = defaultdict(list)
        for elem in elements:
            if elem.element_type == ElementType.TABLE and elem.bbox:
                page_tables[elem.page_no or 1].append(elem)

        # 分析每个表格的跨页情况
        processed_table_ids: Set[str] = set()

        for page_no in sorted(page_tables.keys()):
            tables = page_tables[page_no]

            for table_elem in tables:
                table_id = table_elem.element_id

                if table_id in processed_table_ids:
                    continue

                # 创建或获取表格跨页信息
                if table_id not in table_spans:
                    table_spans[table_id] = TableSpanInfo(table_id=table_id)

                span_info = table_spans[table_id]
                span_info.pages.append(page_no)

                # 提取表头（第一行）
                if span_info.header_row is None and table_elem.table_structure:
                    structure = table_elem.table_structure
                    if structure.headers and len(structure.headers) > 0:
                        span_info.header_row = structure.headers[0]

                processed_table_ids.add(table_id)

        # 分析表格是否完整（检测可能的跨页）
        for table_id, span_info in table_spans.items():
            # 如果表格跨越多页，标记为可能不完整
            if len(span_info.pages) > 1:
                # 检查最后一页是否有表头
                last_page = span_info.pages[-1]
                page_table = page_tables.get(last_page, [])

                has_header_on_last_page = False
                for table in page_table:
                    if table.table_structure and table.table_structure.headers:
                        has_header_on_last_page = True
                        break

                # 如果最后一页没有表头，说明表格跨页了
                if not has_header_on_last_page:
                    span_info.is_complete = False
                    logger.info(
                        f"检测到表格跨页: {table_id}",
                        extra={
                            "table_id": table_id,
                            "pages": span_info.pages
                        }
                    )

        return table_spans

    def _reorder_multicolumn(
        self,
        elements: List[DocumentElementModel],
        column_info: List[ColumnInfo]
    ) -> List[DocumentElementModel]:
        """
        多栏布局阅读顺序还原

        在多栏布局中，需要按从左到右、从上到下的顺序阅读。
        算法：
        1. 将元素分配到各栏
        2. 在栏内按Y坐标排序
        3. 按栏顺序合并

        Args:
            elements: 元素列表
            column_info: 栏信息列表

        Returns:
            重排后的元素列表
        """
        if not column_info:
            # 单栏布局，无需特殊处理
            return elements

        # 按页码分组
        page_elements: Dict[int, List[DocumentElementModel]] = defaultdict(list)
        for elem in elements:
            page_elements[elem.page_no or 1].append(elem)

        reordered: List[DocumentElementModel] = []

        for page_no in sorted(page_elements.keys()):
            page_elems = page_elements[page_no]

            # 跳过页眉页脚
            main_content = [
                e for e in page_elems
                if e.element_type not in (ElementType.HEADER, ElementType.FOOTER)
            ]

            # 将元素分配到栏
            columns: Dict[int, List[DocumentElementModel]] = defaultdict(list)
            unassigned: List[DocumentElementModel] = []

            for elem in main_content:
                if not elem.bbox:
                    unassigned.append(elem)
                    continue

                assigned = False
                for col in column_info:
                    if col.x_start <= elem.bbox.x < col.x_end:
                        columns[col.column_index].append(elem)
                        assigned = True
                        break

                if not assigned:
                    # 尝试扩展栏范围
                    for col in column_info:
                        if elem.bbox.x < col.x_end and elem.bbox.x + elem.bbox.width > col.x_start:
                            columns[col.column_index].append(elem)
                            assigned = True
                            break

                    if not assigned:
                        unassigned.append(elem)

            # 在栏内按Y坐标排序
            for col_idx in columns:
                columns[col_idx].sort(key=lambda e: e.bbox.y if e.bbox else 0)

            # 按栏顺序合并
            for col_idx in sorted(columns.keys()):
                reordered.extend(columns[col_idx])

            # 添加未分配的元素
            reordered.extend(unassigned)

        # 添加页眉页脚（保持原位置）
        headers_footers = [e for e in elements if e.element_type in (ElementType.HEADER, ElementType.FOOTER)]
        reordered.extend(headers_footers)

        return reordered

    def _merge_cross_page_tables(
        self,
        elements: List[DocumentElementModel],
        table_spans: Dict[str, TableSpanInfo]
    ) -> List[DocumentElementModel]:
        """
        合并跨页表格

        将跨页的表格内容合并为一个完整元素。

        Args:
            elements: 元素列表
            table_spans: 表格跨页信息

        Returns:
            处理后的元素列表
        """
        if not table_spans:
            return elements

        # 识别需要合并的表格
        tables_to_merge: Set[str] = set()
        for table_id, span_info in table_spans.items():
            if not span_info.is_complete and len(span_info.pages) > 1:
                tables_to_merge.add(table_id)

        if not tables_to_merge:
            return elements

        # 按表格顺序重排
        merged_elements: List[DocumentElementModel] = []
        current_table: Optional[DocumentElementModel] = None
        current_table_pages: List[int] = []

        for elem in elements:
            if elem.element_type == ElementType.TABLE:
                table_id = elem.element_id

                if table_id in tables_to_merge:
                    span_info = table_spans.get(table_id)

                    if span_info and len(span_info.pages) > 1:
                        # 这是跨页表格的第一部分
                        if current_table is not None:
                            merged_elements.append(current_table)

                        current_table = elem
                        current_table_pages = [elem.page_no or 1]

                        logger.info(
                            f"开始合并跨页表格: {table_id}",
                            extra={
                                "table_id": table_id,
                                "total_pages": len(span_info.pages)
                            }
                        )
                    else:
                        # 普通表格或跨页表格的结束部分
                        if current_table is not None:
                            merged_elements.append(current_table)
                            current_table = None
                            current_table_pages = []
                        merged_elements.append(elem)
                else:
                    if current_table is not None:
                        merged_elements.append(current_table)
                        current_table = None
                        current_table_pages = []
                    merged_elements.append(elem)
            else:
                # 非表格元素
                if current_table is not None:
                    # 检查是否应该合并到当前表格
                    elem_page = elem.page_no or 1
                    last_table_page = current_table_pages[-1] if current_table_pages else 1

                    if elem_page == last_table_page + 1 or elem_page == last_table_page:
                        # 检查是否紧跟在表格后面
                        current_table_pages.append(elem_page)

                        # 合并内容
                        if current_table.table_structure and elem.table_structure:
                            # 追加行
                            if elem.table_structure.rows:
                                current_table.table_structure.rows.extend(elem.table_structure.rows)
                        elif elem.table_structure:
                            current_table.table_structure = elem.table_structure

                        # 标记为合并的
                        current_table.is_merged = True
                        current_table.metadata = current_table.metadata or {}
                        current_table.metadata["merged_from"] = table_spans.get(
                            current_table.element_id, TableSpanInfo(table_id=current_table.element_id)
                        ).pages
                        continue

                merged_elements.append(elem)

        # 处理最后一个表格
        if current_table is not None:
            merged_elements.append(current_table)
            logger.info(
                "跨页表格合并完成",
                extra={"total_tables_merged": len(tables_to_merge)}
            )

        return merged_elements

    def _build_title_paths(
        self,
        elements: List[DocumentElementModel]
    ) -> List[DocumentElementModel]:
        """
        建立标题路径

        为每个元素添加所属的标题路径。

        Args:
            elements: 元素列表

        Returns:
            处理后的元素列表
        """
        title_stack: List[DocumentElementModel] = []  # 标题栈

        for element in elements:
            if element.element_type == ElementType.TITLE:
                # 更新标题栈
                level = element.title_level or 1

                # 移除低级标题
                title_stack = [t for t in title_stack if (t.title_level or 1) < level]

                # 添加当前标题
                title_stack.append(element)

                # 构建标题路径
                path_parts = [t.content[:50] for t in title_stack]
                element.title_path = " > ".join(path_parts)
                element.parent_path = title_stack[-2].title_path if len(title_stack) > 1 else ""

            elif title_stack:
                # 非标题元素，继承父标题路径
                element.title_path = title_stack[-1].title_path
                element.parent_path = title_stack[-1].title_path

        return elements

    def _build_adjacency(
        self,
        elements: List[DocumentElementModel]
    ) -> List[DocumentElementModel]:
        """
        建立元素邻接关系

        为每个元素标记前一个和后一个相邻元素。

        Args:
            elements: 元素列表

        Returns:
            处理后的元素列表
        """
        for i, element in enumerate(elements):
            if i > 0:
                element.metadata = element.metadata or {}
                element.metadata["prev_element_id"] = elements[i - 1].element_id

            if i < len(elements) - 1:
                element.metadata = element.metadata or {}
                element.metadata["next_element_id"] = elements[i + 1].element_id

        return elements

    def _reorder_by_reading(
        self,
        elements: List[DocumentElementModel]
    ) -> List[DocumentElementModel]:
        """
        按阅读顺序重排

        确保元素按正确的阅读顺序排列。

        Args:
            elements: 元素列表

        Returns:
            重排后的元素列表
        """
        # 重新设置阅读顺序
        for i, element in enumerate(elements):
            element.reading_order = i

        return elements

    def _merge_cross_page_paragraphs(
        self,
        elements: List[DocumentElementModel]
    ) -> List[DocumentElementModel]:
        """
        跨页段落合并

        将被分页切断的段落合并。

        Args:
            elements: 元素列表

        Returns:
            合并后的元素列表
        """
        if not elements:
            return elements

        merged: List[DocumentElementModel] = []
        current_paragraph: Optional[DocumentElementModel] = None

        for element in elements:
            # 跳过页眉页脚
            if element.element_type in (ElementType.HEADER, ElementType.FOOTER):
                if current_paragraph:
                    merged.append(current_paragraph)
                    current_paragraph = None
                merged.append(element)
                continue

            # 处理段落
            if element.element_type == ElementType.PARAGRAPH:
                if current_paragraph is None:
                    current_paragraph = element
                else:
                    # 检查是否可以合并
                    if self._can_merge_paragraphs(current_paragraph, element):
                        # 合并到当前段落
                        current_paragraph.content += " " + element.content
                        current_paragraph.page_end = element.page_no
                        current_paragraph.is_merged = True
                        # 更新元数据
                        current_paragraph.metadata = current_paragraph.metadata or {}
                        current_paragraph.metadata["merged_elements"] = (
                            current_paragraph.metadata.get("merged_elements", []) + [element.element_id]
                        )
                    else:
                        # 不能合并，保存当前段落，开始新段落
                        merged.append(current_paragraph)
                        current_paragraph = element
            else:
                # 非段落元素
                if current_paragraph:
                    merged.append(current_paragraph)
                    current_paragraph = None
                merged.append(element)

        # 处理最后一个段落
        if current_paragraph:
            merged.append(current_paragraph)

        # 重新设置阅读顺序
        for i, element in enumerate(merged):
            element.reading_order = i

        return merged

    def _can_merge_paragraphs(
        self,
        current: DocumentElementModel,
        next_elem: DocumentElementModel
    ) -> bool:
        """
        判断两个段落是否可以合并

        合并条件：
        1. 两个段落类型相同
        2. 页码连续
        3. 当前段落没有明确结束标记

        Args:
            current: 当前段落
            next_elem: 下一个元素

        Returns:
            是否可以合并
        """
        # 类型必须相同
        if current.element_type != next_elem.element_type:
            return False

        # 必须是段落类型
        if current.element_type != ElementType.PARAGRAPH:
            return False

        # 页码检查（允许跨1页）
        current_page = current.page_no or 1
        next_page = next_elem.page_no or 1

        if next_page > current_page + 1:
            return False  # 跨了太多页

        # 检查内容是否完整（以标点符号结尾的不合并）
        if current.content and current.content[-1] in "。！？；：.,!?;:":
            return False

        return True

    def _mark_low_confidence(
        self,
        elements: List[DocumentElementModel]
    ) -> List[DocumentElementModel]:
        """
        标记低置信度元素

        根据置信度设置质量标记。

        Args:
            elements: 元素列表

        Returns:
            处理后的元素列表
        """
        for element in elements:
            confidence = element.confidence

            if confidence >= 0.8:
                element.quality_flag = QualityFlag.GOOD
            elif confidence >= 0.5:
                element.quality_flag = QualityFlag.WARNING
            else:
                element.quality_flag = QualityFlag.BAD

        return elements

    def get_quality_summary(
        self,
        elements: List[DocumentElementModel]
    ) -> Dict[str, int]:
        """
        获取质量汇总

        Args:
            elements: 元素列表

        Returns:
            质量汇总字典
        """
        summary = {
            "good": 0,
            "warning": 0,
            "bad": 0,
            "total": len(elements)
        }

        for element in elements:
            flag = element.quality_flag.value if isinstance(element.quality_flag, QualityFlag) else element.quality_flag
            if flag in summary:
                summary[flag] += 1

        return summary

    def get_layout_info(
        self,
        elements: List[DocumentElementModel]
    ) -> Dict[str, Any]:
        """
        获取版面信息

        返回当前文档的版面特征信息。

        Args:
            elements: 元素列表

        Returns:
            版面信息字典
        """
        column_info = self._identify_columns(elements)
        table_spans = self._detect_table_spans(elements)

        return {
            "is_multicolumn": len(column_info) > 1,
            "column_count": len(column_info),
            "columns": [
                {
                    "index": col.column_index,
                    "width": col.width,
                    "x_start": col.x_start,
                    "x_end": col.x_end
                }
                for col in column_info
            ],
            "table_spans": [
                {
                    "table_id": span.table_id,
                    "pages": span.pages,
                    "is_complete": span.is_complete
                }
                for span in table_spans.values()
            ],
            "quality_summary": self.get_quality_summary(elements)
        }
