# -*- coding: utf-8 -*-
"""
查询改写服务（增强版）

本模块提供增强的查询改写功能，包括：
- QueryNormalizer: 查询规范化（去停用词、统一大小写、标点归一化）
- MultiQueryGenerator: 多查询生成（LLM驱动，扩展为3-5个相似查询）
- QueryDecomposer: 子查询分解（LLM驱动，复杂问题按意图拆分）
- HyDEGenerator: 假设答案生成接口
- BackwardHintGenerator: 后退提示接口

所有代码注释使用中文，所有日志输出中文。
"""

import re
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

from app.common.logging import logger


# ================================================
# 中文停用词表
# ================================================
CN_STOPWORDS: Set[str] = {
    # 常用虚词
    "的", "了", "在", "是", "我", "有", "和", "就", "不", "人",
    "都", "一", "一个", "上", "也", "很", "到", "说", "要", "去",
    "你", "会", "着", "没有", "看", "好", "自己", "这", "那",
    "里", "为", "之", "以", "而", "于", "并", "及", "等", "其",
    "但", "却", "或", "又", "还", "把", "被", "让", "给", "向",
    "从", "比", "如", "跟", "连", "只", "就是", "不是", "也是",
    "也是", "而且", "但是", "所以", "因为", "如果", "虽然", "即使",
    # 常见助词
    "啊", "呀", "吧", "呢", "吗", "哦", "嘛", "啦", "呀",
    # 常见量词（保留更有意义的）
    "个", "些", "种", "类",
}

# ================================================
# 英文停用词表
# ================================================
EN_STOPWORDS: Set[str] = {
    "the", "a", "an", "is", "are", "was", "were", "be", "been",
    "have", "has", "had", "do", "does", "did", "will", "would",
    "could", "should", "may", "might", "can", "must", "shall",
    "i", "you", "he", "she", "it", "we", "they", "me", "him",
    "her", "us", "them", "my", "your", "his", "its", "our",
    "their", "this", "that", "these", "those", "what", "which",
    "who", "whom", "whose", "where", "when", "why", "how",
    "and", "or", "but", "not", "no", "yes", "all", "any",
    "some", "none", "each", "every", "both", "few", "more",
    "most", "other", "such", "only", "own", "same", "so",
    "than", "too", "very", "just", "now",
}

# ================================================
# 所有停用词集合
# ================================================
ALL_STOPWORDS: Set[str] = CN_STOPWORDS | EN_STOPWORDS


# ================================================
# 中英文同义词映射
# ================================================
SYNONYM_MAP: Dict[str, List[str]] = {
    # 技术术语
    "系统": ["平台", "框架", "架构"],
    "查询": ["检索", "搜索", "查找"],
    "文档": ["文件", "资料", "文本"],
    "知识库": ["知识库系统", "知识平台"],
    "用户": ["使用者", "客户"],
    "数据": ["信息", "记录"],
    "配置": ["设置", "参数"],
    "服务": ["服务", "服务"],
    "接口": ["API", "端口"],
    # 疑问词
    "如何": ["怎么", "怎样", "如何"],
    "什么": ["哪个", "哪些", "什么"],
    "为什么": ["为何", "原因"],
    "多少": ["几", "数量"],
    # 动作词
    "实现": ["达成", "完成"],
    "使用": ["运用", "采用"],
    "支持": ["兼容", "支持"],
    "优化": ["改进", "提升"],
    "处理": ["加工", "操作"],
    "创建": ["新建", "建立"],
    "删除": ["移除", "去掉"],
    "更新": ["修改", "变更"],
    "获取": ["获得", "得到"],
}

# ================================================
# 中文到英文的映射
# ================================================
CN_TO_EN: Dict[str, str] = {
    "文档": "document",
    "知识库": "knowledge base",
    "检索": "retrieval",
    "问答": "Q&A",
    "系统": "system",
    "接口": "API",
    "数据库": "database",
    "服务器": "server",
    "配置": "configuration",
    "查询": "query",
    "搜索": "search",
    "用户": "user",
    "权限": "permission",
    "登录": "login",
    "注册": "register",
}


@dataclass
class NormalizeResult:
    """规范化结果"""
    original: str  # 原始查询
    normalized: str  # 规范化后的查询
    removed_stopwords: List[str] = field(default_factory=list)  # 被移除的停用词
    punctuation_normalized: int = 0  # 归一化的标点数量


@dataclass
class MultiQueryResult:
    """多查询生成结果"""
    original: str  # 原始查询
    queries: List[str] = field(default_factory=list)  # 生成的多个查询
    generation_time_ms: int = 0  # 生成耗时（毫秒）
    method: str = "rule"  # 生成方法：rule/llm


@dataclass
class DecomposeResult:
    """子查询分解结果"""
    original: str  # 原始查询
    sub_queries: List[str] = field(default_factory=list)  # 分解后的子查询
    intents: List[str] = field(default_factory=list)  # 识别出的意图
    generation_time_ms: int = 0  # 生成耗时（毫秒）


@dataclass
class HyDEResult:
    """HyDE假设答案结果"""
    query: str  # 原始查询
    hypothetical_answer: Optional[str] = None  # 假设答案
    generation_time_ms: int = 0  # 生成耗时（毫秒）
    success: bool = False  # 是否成功


@dataclass
class BackwardHintResult:
    """后退提示结果"""
    query: str  # 原始查询
    background_query: Optional[str] = None  # 宏观背景问题
    generation_time_ms: int = 0  # 生成耗时（毫秒）
    success: bool = False  # 是否成功


@dataclass
class RewriteResult:
    """完整查询改写结果"""
    original_query: str
    normalized_query: str
    multi_queries: List[str]
    sub_queries: List[str]
    hyde_answer: Optional[str]
    background_query: Optional[str]
    rewrite_time_ms: int = 0  # 总改写耗时
    # 详细统计
    removed_stopwords: List[str] = field(default_factory=list)
    normalization_details: Optional[NormalizeResult] = None
    multi_query_details: Optional[MultiQueryResult] = None
    decompose_details: Optional[DecomposeResult] = None
    hyde_details: Optional[HyDEResult] = None
    backward_details: Optional[BackwardHintResult] = None


class QueryNormalizer:
    """
    查询规范化器

    功能：
    - 去除多余空格
    - 标点归一化
    - 停用词移除
    - 统一大小写

    支持中文和英文。
    """

    def __init__(self, remove_stopwords: bool = True):
        """
        初始化规范化器

        Args:
            remove_stopwords: 是否移除停用词
        """
        self._remove_stopwords = remove_stopwords
        self._punctuation_pattern = re.compile(r'[^\w\s\u4e00-\u9fff]')  # 保留中文、英文、数字、下划线
        self._whitespace_pattern = re.compile(r'\s+')

    def normalize(self, query: str) -> NormalizeResult:
        """
        规范化查询

        Args:
            query: 原始查询

        Returns:
            规范化结果
        """
        start_time = time.time()

        if not query:
            return NormalizeResult(
                original=query,
                normalized="",
                removed_stopwords=[],
                punctuation_normalized=0
            )

        original = query
        removed_stopwords = []
        normalized = query

        # 1. 去除首尾空白
        normalized = normalized.strip()

        # 2. 合并多个空格
        normalized = self._whitespace_pattern.sub(' ', normalized)

        # 3. 标点归一化（将标点替换为空格）
        punctuation_count = len(self._punctuation_pattern.findall(normalized))
        normalized = self._punctuation_pattern.sub(' ', normalized)

        # 4. 再次合并空格
        normalized = self._whitespace_pattern.sub(' ', normalized)
        normalized = normalized.strip()

        # 5. 统一小写（英文部分）
        normalized = normalized.lower()

        # 6. 移除停用词
        if self._remove_stopwords:
            terms = normalized.split()
            filtered_terms = []
            for term in terms:
                if term not in ALL_STOPWORDS and len(term) > 0:
                    filtered_terms.append(term)
                else:
                    removed_stopwords.append(term)
            normalized = " ".join(filtered_terms)

        # 7. 最终去重空格
        normalized = self._whitespace_pattern.sub(' ', normalized)
        normalized = normalized.strip()

        processing_time_ms = int((time.time() - start_time) * 1000)

        logger.info(
            f"查询规范化完成，耗时: {processing_time_ms}ms",
            extra={
                "original": original,
                "normalized": normalized,
                "removed_count": len(removed_stopwords),
                "processing_time_ms": processing_time_ms
            }
        )

        return NormalizeResult(
            original=original,
            normalized=normalized,
            removed_stopwords=removed_stopwords,
            punctuation_normalized=punctuation_count
        )

    def quick_normalize(self, query: str) -> str:
        """
        快速规范化（仅返回规范化后的字符串）

        Args:
            query: 原始查询

        Returns:
            规范化后的查询
        """
        if not query:
            return ""

        result = self.normalize(query)
        return result.normalized


class MultiQueryGenerator:
    """
    多查询生成器

    将一个查询扩展为多个相似查询，提升召回覆盖率。

    支持两种模式：
    - 规则模式：基于同义词、问答形式转换等规则
    - LLM模式：使用LLM生成更丰富的查询变体
    """

    def __init__(self, use_llm: bool = False, llm_client: Any = None):
        """
        初始化生成器

        Args:
            use_llm: 是否使用LLM生成
            llm_client: LLM客户端实例
        """
        self._use_llm = use_llm
        self._llm_client = llm_client

    def generate(
        self,
        query: str,
        max_queries: int = 5
    ) -> MultiQueryResult:
        """
        生成多个查询

        Args:
            query: 规范化后的查询
            max_queries: 最大生成数量

        Returns:
            多查询生成结果
        """
        start_time = time.time()

        if not query:
            return MultiQueryResult(
                original=query,
                queries=[],
                generation_time_ms=0,
                method="rule"
            )

        queries = set()

        # 1. 保留原始查询
        queries.add(query)

        # 2. 规则生成
        rule_queries = self._generate_by_rules(query, max_queries)
        queries.update(rule_queries)

        # 3. 如果启用LLM，调用LLM生成
        if self._use_llm and self._llm_client:
            llm_queries = self._generate_by_llm(query, max_queries)
            queries.update(llm_queries)

        # 转换为列表并限制数量
        result_list = list(queries)[:max_queries]

        generation_time_ms = int((time.time() - start_time) * 1000)

        logger.info(
            f"多查询生成完成，共生成{len(result_list)}个查询，耗时: {generation_time_ms}ms",
            extra={
                "original": query,
                "query_count": len(result_list),
                "generation_time_ms": generation_time_ms,
                "method": "llm" if self._use_llm and self._llm_client else "rule"
            }
        )

        return MultiQueryResult(
            original=query,
            queries=result_list,
            generation_time_ms=generation_time_ms,
            method="llm" if self._use_llm and self._llm_client else "rule"
        )

    def _generate_by_rules(self, query: str, max_queries: int) -> List[str]:
        """
        基于规则生成查询变体

        Args:
            query: 查询文本
            max_queries: 最大数量

        Returns:
            查询列表
        """
        queries = []

        # 1. 去除停用词版本
        terms = query.split()
        filtered_terms = [t for t in terms if t not in ALL_STOPWORDS]
        if filtered_terms:
            filtered_query = " ".join(filtered_terms)
            if filtered_query != query:
                queries.append(filtered_query)

        # 2. 同义词扩展
        for term, synonyms in SYNONYM_MAP.items():
            if term in query:
                for syn in synonyms:
                    expanded = query.replace(term, syn)
                    if expanded != query:
                        queries.append(expanded)

        # 3. 中英文混合扩展
        for cn, en in CN_TO_EN.items():
            if cn in query and en not in query.lower():
                expanded = f"{query} {en}"
                queries.append(expanded)

        # 4. 问答形式转换
        question_forms = self._generate_question_forms(query)
        queries.extend(question_forms)

        # 5. 去重
        seen = set()
        unique_queries = []
        for q in queries:
            q_lower = q.lower()
            if q_lower not in seen:
                seen.add(q_lower)
                unique_queries.append(q)

        return unique_queries[:max_queries - 1]  # 保留一个位置给原始查询

    def _generate_by_llm(self, query: str, max_queries: int) -> List[str]:
        """
        使用LLM生成查询变体

        Args:
            query: 查询文本
            max_queries: 最大数量

        Returns:
            查询列表
        """
        try:
            prompt = f"""请为以下查询生成{max_queries - 1}个不同的相似查询变体。
要求：
1. 保持原意
2. 使用不同的表述方式
3. 可以包含同义词替换、句式转换等
4. 输出格式：每行一个查询

原始查询：{query}

相似查询变体："""

            response = self._llm_client.generate(prompt)
            lines = response.strip().split('\n')
            queries = [line.strip() for line in lines if line.strip()]
            return queries[:max_queries - 1]

        except Exception as e:
            logger.warning(f"LLM生成多查询失败: {str(e)}")
            return []

    def _generate_question_forms(self, query: str) -> List[str]:
        """
        生成问答形式变体

        Args:
            query: 查询文本

        Returns:
            问答形式列表
        """
        forms = []

        # 如果查询已经是疑问句，添加陈述句形式
        if any(kw in query for kw in ["如何", "怎么", "什么", "哪个", "多少", "why", "how", "what", "which"]):
            forms.append(f"关于{query}的说明")
            forms.append(f"{query}的相关信息")
        else:
            # 如果查询是陈述句，添加疑问句形式
            if query.endswith("方法") or query.endswith("方式"):
                forms.append(f"如何{query.replace('方法', '').replace('方式', '')}")
            if "是" in query:
                forms.append(f"什么是{query.split('是')[-1].strip() if '是' in query else query}")

        return forms


class QueryDecomposer:
    """
    子查询分解器

    将复杂问题按多个意图分别检索，然后合并证据。

    支持两种模式：
    - 规则模式：基于连接词、并列结构等规则
    - LLM模式：使用LLM识别复杂意图
    """

    def __init__(self, use_llm: bool = False, llm_client: Any = None):
        """
        初始化分解器

        Args:
            use_llm: 是否使用LLM分解
            llm_client: LLM客户端实例
        """
        self._use_llm = use_llm
        self._llm_client = llm_client
        self._separator_pattern = re.compile(r'[和与及或者或and or以及,]')

    def decompose(self, query: str) -> DecomposeResult:
        """
        分解查询

        Args:
            query: 规范化后的查询

        Returns:
            分解结果
        """
        start_time = time.time()

        if not query:
            return DecomposeResult(
                original=query,
                sub_queries=[],
                intents=[],
                generation_time_ms=0
            )

        sub_queries = []
        intents = []

        # 1. 规则分解
        rule_queries, rule_intents = self._decompose_by_rules(query)
        sub_queries.extend(rule_queries)
        intents.extend(rule_intents)

        # 2. 如果启用LLM且规则未分解，尝试LLM分解
        if not sub_queries and self._use_llm and self._llm_client:
            llm_queries, llm_intents = self._decompose_by_llm(query)
            sub_queries.extend(llm_queries)
            intents.extend(llm_intents)

        generation_time_ms = int((time.time() - start_time) * 1000)

        logger.info(
            f"子查询分解完成，耗时: {generation_time_ms}ms",
            extra={
                "original": query,
                "subquery_count": len(sub_queries),
                "intents": intents,
                "generation_time_ms": generation_time_ms
            }
        )

        return DecomposeResult(
            original=query,
            sub_queries=sub_queries,
            intents=intents,
            generation_time_ms=generation_time_ms
        )

    def _decompose_by_rules(self, query: str) -> tuple:
        """
        基于规则分解查询

        Args:
            query: 查询文本

        Returns:
            (子查询列表, 意图列表)
        """
        sub_queries = []
        intents = []

        # 检测连接词并分割
        separators = ["和", "与", "及", "或者", "或", "and", "or", "以及"]
        for sep in separators:
            if sep in query:
                parts = self._separator_pattern.split(query)
                if len(parts) > 1:
                    for i, part in enumerate(parts):
                        part = part.strip()
                        if part:
                            sub_queries.append(part)
                            intents.append(f"并列意图{i + 1}")
                    break

        # 检测并列结构（逗号分隔）
        if not sub_queries:
            comma_pattern = re.compile(r'[,，]')
            parts = comma_pattern.split(query)
            if len(parts) > 1:
                has_verbs = sum(1 for p in parts if any(v in p for v in ["是", "有", "如何", "什么", "怎么", "is", "are", "how", "what"]))
                if has_verbs >= 2:
                    for i, part in enumerate(parts):
                        part = part.strip()
                        if part:
                            sub_queries.append(part)
                            intents.append(f"并列意图{i + 1}")

        # 检测时间范围
        if not sub_queries:
            time_patterns = [
                (r'(\d{4})[年-](\d{1,2})[月-]', r'\1年\2月'),
                (r'(20\d{2})年', r'\1年'),
                (r'最近(\d+)(天|周|月|年)', r'最近\1\2内'),
            ]

            for pattern, replacement in time_patterns:
                if re.search(pattern, query):
                    time_match = re.search(pattern, query)
                    if time_match:
                        time_expr = time_match.group(0)
                        base_query = re.sub(pattern, '', query).strip()
                        if base_query:
                            sub_queries.append(base_query)
                            sub_queries.append(f"{base_query} {time_expr}")
                            intents.extend(["基础查询", "时间限定查询"])
                    break

        # 去重
        seen = set()
        unique_queries = []
        for q in sub_queries:
            if q not in seen:
                seen.add(q)
                unique_queries.append(q)

        return unique_queries, intents

    def _decompose_by_llm(self, query: str) -> tuple:
        """
        使用LLM分解查询

        Args:
            query: 查询文本

        Returns:
            (子查询列表, 意图列表)
        """
        try:
            prompt = f"""分析以下查询，如果它包含多个独立的子问题，请将其分解。

要求：
1. 识别查询中的多个独立意图
2. 每个子查询应该简洁明了
3. 输出格式：每行一个子查询，用"||"分隔意图说明

原始查询：{query}

分解结果："""

            response = self._llm_client.generate(prompt)
            lines = response.strip().split('\n')
            queries = []
            intents = []

            for line in lines:
                if '||' in line:
                    parts = line.split('||')
                    queries.append(parts[0].strip())
                    if len(parts) > 1:
                        intents.append(parts[1].strip())
                elif line.strip():
                    queries.append(line.strip())
                    intents.append("LLM识别意图")

            return queries, intents

        except Exception as e:
            logger.warning(f"LLM分解查询失败: {str(e)}")
            return [], []


class HyDEGenerator:
    """
    HyDE（假设答案生成器）

    使用LLM生成假设答案，然后用假设答案进行向量检索。
    这种方法可以帮助检索到语义相关但关键词不匹配的内容。

    注意：需要LLM服务支持。
    """

    def __init__(self, llm_client: Any = None):
        """
        初始化生成器

        Args:
            llm_client: LLM客户端实例
        """
        self._llm_client = llm_client

    def generate(self, query: str) -> HyDEResult:
        """
        生成假设答案

        Args:
            query: 用户查询

        Returns:
            假设答案结果
        """
        start_time = time.time()

        if not query:
            return HyDEResult(
                query=query,
                hypothetical_answer=None,
                generation_time_ms=0,
                success=False
            )

        if not self._llm_client:
            logger.info(
                "HyDE生成跳过：LLM客户端未配置",
                extra={"query": query}
            )
            return HyDEResult(
                query=query,
                hypothetical_answer=None,
                generation_time_ms=int((time.time() - start_time) * 1000),
                success=False
            )

        try:
            prompt = f"""请针对以下问题，生成一个假设性的答案。
这个答案可以是推断性的，用于帮助检索相关文档。
答案应该简洁、聚焦，长度控制在100字以内。

问题：{query}

假设答案："""

            answer = self._llm_client.generate(prompt)
            generation_time_ms = int((time.time() - start_time) * 1000)

            logger.info(
                f"HyDE假设答案生成完成，耗时: {generation_time_ms}ms",
                extra={
                    "query": query,
                    "answer_length": len(answer),
                    "generation_time_ms": generation_time_ms
                }
            )

            return HyDEResult(
                query=query,
                hypothetical_answer=answer.strip(),
                generation_time_ms=generation_time_ms,
                success=True
            )

        except Exception as e:
            generation_time_ms = int((time.time() - start_time) * 1000)
            logger.error(
                f"HyDE假设答案生成失败: {str(e)}",
                extra={
                    "query": query,
                    "error": str(e),
                    "generation_time_ms": generation_time_ms
                }
            )
            return HyDEResult(
                query=query,
                hypothetical_answer=None,
                generation_time_ms=generation_time_ms,
                success=False
            )


class BackwardHintGenerator:
    """
    后退提示生成器

    将具体问题抽象为宏观背景问题，先检索背景再回答原问题。
    这种方法可以帮助回答需要宏观理解的问题。

    注意：需要LLM服务支持。
    """

    def __init__(self, llm_client: Any = None):
        """
        初始化生成器

        Args:
            llm_client: LLM客户端实例
        """
        self._llm_client = llm_client

    def generate(self, query: str) -> BackwardHintResult:
        """
        生成后退提示

        Args:
            query: 用户查询

        Returns:
            后退提示结果
        """
        start_time = time.time()

        if not query:
            return BackwardHintResult(
                query=query,
                background_query=None,
                generation_time_ms=0,
                success=False
            )

        if not self._llm_client:
            logger.info(
                "后退提示生成跳过：LLM客户端未配置",
                extra={"query": query}
            )
            return BackwardHintResult(
                query=query,
                background_query=None,
                generation_time_ms=int((time.time() - start_time) * 1000),
                success=False
            )

        try:
            prompt = f"""请将以下问题抽象为一个更宏观的背景问题。
背景问题应该：
1. 概括原问题的领域和主题
2. 不包含具体的细节和限制
3. 用于帮助理解原问题的上下文

原问题：{query}

背景问题："""

            background = self._llm_client.generate(prompt)
            generation_time_ms = int((time.time() - start_time) * 1000)

            logger.info(
                f"后退提示生成完成，耗时: {generation_time_ms}ms",
                extra={
                    "original_query": query,
                    "background_query": background,
                    "generation_time_ms": generation_time_ms
                }
            )

            return BackwardHintResult(
                query=query,
                background_query=background.strip(),
                generation_time_ms=generation_time_ms,
                success=True
            )

        except Exception as e:
            generation_time_ms = int((time.time() - start_time) * 1000)
            logger.error(
                f"后退提示生成失败: {str(e)}",
                extra={
                    "query": query,
                    "error": str(e),
                    "generation_time_ms": generation_time_ms
                }
            )
            return BackwardHintResult(
                query=query,
                background_query=None,
                generation_time_ms=generation_time_ms,
                success=False
            )


class QueryRewriteService:
    """
    查询改写服务（增强版）

    整合所有查询改写组件，提供完整的查询改写功能。

    功能：
    - 查询规范化：去除停用词、统一大小写、标点归一化
    - 多查询生成：LLM驱动，扩展为3-5个相似查询
    - 子查询分解：LLM驱动，复杂问题按意图拆分
    - HyDE：生成假设答案用于向量检索
    - 后退提示：生成宏观背景问题

    配置开关：
    - enable_multi_query: 是否启用多查询生成
    - enable_subquery: 是否启用子查询分解
    - enable_hyde: 是否启用HyDE
    - enable_background: 是否启用后退提示
    - use_llm: 是否使用LLM增强生成
    """

    def __init__(
        self,
        remove_stopwords: bool = True,
        enable_multi_query: bool = True,
        enable_subquery: bool = True,
        enable_hyde: bool = False,
        enable_background: bool = False,
        use_llm: bool = False,
        llm_client: Any = None
    ):
        """
        初始化服务

        Args:
            remove_stopwords: 是否移除停用词
            enable_multi_query: 是否启用多查询生成
            enable_subquery: 是否启用子查询分解
            enable_hyde: 是否启用HyDE
            enable_background: 是否启用后退提示
            use_llm: 是否使用LLM增强生成
            llm_client: LLM客户端实例
        """
        self._normalizer = QueryNormalizer(remove_stopwords=remove_stopwords)
        self._multi_query_generator = MultiQueryGenerator(
            use_llm=use_llm,
            llm_client=llm_client
        )
        self._query_decomposer = QueryDecomposer(
            use_llm=use_llm,
            llm_client=llm_client
        )
        self._hyde_generator = HyDEGenerator(llm_client=llm_client)
        self._backward_generator = BackwardHintGenerator(llm_client=llm_client)

        self._enable_multi_query = enable_multi_query
        self._enable_subquery = enable_subquery
        self._enable_hyde = enable_hyde
        self._enable_background = enable_background

    def rewrite(
        self,
        query: str,
        enable_multi_query: Optional[bool] = None,
        enable_subquery: Optional[bool] = None,
        enable_hyde: Optional[bool] = None,
        enable_background: Optional[bool] = None,
        max_queries: int = 5
    ) -> RewriteResult:
        """
        执行查询改写

        Args:
            query: 原始查询
            enable_multi_query: 是否启用多查询生成（覆盖默认配置）
            enable_subquery: 是否启用子查询分解（覆盖默认配置）
            enable_hyde: 是否启用HyDE（覆盖默认配置）
            enable_background: 是否启用后退提示（覆盖默认配置）
            max_queries: 最大生成查询数量

        Returns:
            查询改写结果
        """
        start_time = time.time()

        try:
            # 1. 查询规范化
            normalize_result = self._normalizer.normalize(query)

            # 2. 多查询生成
            multi_query_details = None
            multi_queries = []
            if enable_multi_query if enable_multi_query is not None else self._enable_multi_query:
                multi_query_details = self._multi_query_generator.generate(
                    normalize_result.normalized,
                    max_queries=max_queries
                )
                multi_queries = multi_query_details.queries

            # 3. 子查询分解
            decompose_details = None
            sub_queries = []
            if enable_subquery if enable_subquery is not None else self._enable_subquery:
                decompose_details = self._query_decomposer.decompose(normalize_result.normalized)
                sub_queries = decompose_details.sub_queries

            # 4. HyDE假设答案
            hyde_details = None
            hyde_answer = None
            if enable_hyde if enable_hyde is not None else self._enable_hyde:
                hyde_details = self._hyde_generator.generate(query)
                hyde_answer = hyde_details.hypothetical_answer

            # 5. 后退提示
            backward_details = None
            background_query = None
            if enable_background if enable_background is not None else self._enable_background:
                backward_details = self._backward_generator.generate(query)
                background_query = backward_details.background_query

            total_time_ms = int((time.time() - start_time) * 1000)

            logger.info(
                f"查询改写完成，总耗时: {total_time_ms}ms",
                extra={
                    "original_query": query,
                    "normalized_query": normalize_result.normalized,
                    "multi_query_count": len(multi_queries),
                    "subquery_count": len(sub_queries),
                    "hyde_success": hyde_details.success if hyde_details else False,
                    "backward_success": backward_details.success if backward_details else False,
                    "total_time_ms": total_time_ms
                }
            )

            return RewriteResult(
                original_query=query,
                normalized_query=normalize_result.normalized,
                multi_queries=multi_queries,
                sub_queries=sub_queries,
                hyde_answer=hyde_answer,
                background_query=background_query,
                rewrite_time_ms=total_time_ms,
                removed_stopwords=normalize_result.removed_stopwords,
                normalization_details=normalize_result,
                multi_query_details=multi_query_details,
                decompose_details=decompose_details,
                hyde_details=hyde_details,
                backward_details=backward_details
            )

        except Exception as e:
            total_time_ms = int((time.time() - start_time) * 1000)
            logger.error(
                f"查询改写失败: {str(e)}，耗时: {total_time_ms}ms",
                extra={
                    "original_query": query,
                    "error": str(e),
                    "total_time_ms": total_time_ms
                }
            )
            # 出错时返回原始查询
            return RewriteResult(
                original_query=query,
                normalized_query=query,
                multi_queries=[query],
                sub_queries=[],
                hyde_answer=None,
                background_query=None,
                rewrite_time_ms=total_time_ms,
                removed_stopwords=[],
                normalization_details=None,
                multi_query_details=None,
                decompose_details=None,
                hyde_details=None,
                backward_details=None
            )

    def normalize_only(self, query: str) -> str:
        """
        仅执行规范化

        Args:
            query: 原始查询

        Returns:
            规范化后的查询
        """
        return self._normalizer.quick_normalize(query)

    def get_all_queries(
        self,
        query: str,
        max_queries: int = 5
    ) -> List[str]:
        """
        获取所有改写后的查询（包括原始查询的多个变体）

        Args:
            query: 原始查询
            max_queries: 最大数量

        Returns:
            查询列表
        """
        result = self.rewrite(query, max_queries=max_queries)

        # 合并所有查询
        all_queries = set()
        all_queries.add(query)  # 添加原始查询
        all_queries.update(result.multi_queries)  # 添加多查询
        all_queries.update(result.sub_queries)  # 添加子查询

        # 如果HyDE成功，添加假设答案
        if result.hyde_answer:
            all_queries.add(result.hyde_answer)

        # 如果后退提示成功，添加背景查询
        if result.background_query:
            all_queries.add(result.background_query)

        return list(all_queries)[:max_queries]


# ================================================
# 全局服务实例和工厂函数
# ================================================
_rewrite_service: Optional[QueryRewriteService] = None


def get_rewrite_service(
    enable_multi_query: bool = True,
    enable_subquery: bool = True,
    enable_hyde: bool = False,
    enable_background: bool = False,
    use_llm: bool = False,
    llm_client: Any = None
) -> QueryRewriteService:
    """
    获取查询改写服务实例

    Args:
        enable_multi_query: 是否启用多查询生成
        enable_subquery: 是否启用子查询分解
        enable_hyde: 是否启用HyDE
        enable_background: 是否启用后退提示
        use_llm: 是否使用LLM增强
        llm_client: LLM客户端实例

    Returns:
        QueryRewriteService实例
    """
    global _rewrite_service
    if _rewrite_service is None:
        _rewrite_service = QueryRewriteService(
            enable_multi_query=enable_multi_query,
            enable_subquery=enable_subquery,
            enable_hyde=enable_hyde,
            enable_background=enable_background,
            use_llm=use_llm,
            llm_client=llm_client
        )
    return _rewrite_service


def reset_rewrite_service() -> None:
    """重置服务实例（用于测试或配置变更后重新初始化）"""
    global _rewrite_service
    _rewrite_service = None
