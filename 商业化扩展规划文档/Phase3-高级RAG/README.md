# Phase 3：高级 RAG

**版本：** V1.0  
**日期：** 2026-05-17  
**预计周期：** 4-5 周  
**优先级：** P1

---

## 一、阶段概述

### 1.1 阶段目标

构建行业领先的检索与问答质量，实现混合检索、查询处理管道、Prompt 工程平台和答案质量评估能力。

### 1.2 核心功能

| 模块 | 功能点 | 优先级 | 工作量 |
|------|--------|--------|--------|
| 混合检索 | 向量+关键词+混合融合 | P0 | 5 天 |
| 查询处理 | 意图识别/查询改写/扩展 | P0 | 4 天 |
| 重排序 | Cross-Encoder 重排序 | P1 | 2 天 |
| Prompt 平台 | 模板管理/变量配置 | P1 | 2 天 |
| 质量评估 | 答案评估/反馈收集 | P2 | 3 天 |

### 1.3 技术架构

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          Phase 3 架构                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│                          用户问题输入                                       │
│                                 │                                           │
│                                 ▼                                           │
│   ┌──────────────────────────────────────────────────────────────────┐    │
│   │                      查询处理管道                                    │    │
│   │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐           │    │
│   │  │意图识别 │→│查询改写 │→│查询扩展 │→│问题分解 │           │    │
│   │  └─────────┘  └─────────┘  └─────────┘  └─────────┘           │    │
│   └──────────────────────────────────────────────────────────────────┘    │
│                                 │                                           │
│                                 ▼                                           │
│   ┌──────────────────────────────────────────────────────────────────┐    │
│   │                        混合检索层                                    │    │
│   │                                                                  │    │
│   │  ┌───────────────┐           ┌───────────────┐                  │    │
│   │  │  Dense检索    │           │  Sparse检索   │                  │    │
│   │  │ (向量检索)    │           │  (BM25/关键词)│                  │    │
│   │  │  Milvus      │           │ Elasticsearch │                  │    │
│   │  └───────┬───────┘           └───────┬───────┘                  │    │
│   │          │                           │                            │    │
│   │          └─────────┬─────────────────┘                            │    │
│   │                    ▼                                              │    │
│   │          ┌─────────────────┐                                    │    │
│   │          │  融合策略 (RRF) │                                    │    │
│   │          └────────┬────────┘                                    │    │
│   │                   │                                              │    │
│   └───────────────────┼──────────────────────────────────────────────┘    │
│                       ▼                                                │
│   ┌──────────────────────────────────────────────────────────────────┐    │
│   │                       重排序层                                     │    │
│   │                                                                  │    │
│   │          ┌─────────────────┐                                    │    │
│   │          │  Cross-Encoder  │                                    │    │
│   │          │    Reranker     │                                    │    │
│   │          └────────┬────────┘                                    │    │
│   │                   │                                              │    │
│   └───────────────────┼──────────────────────────────────────────────┘    │
│                       ▼                                                │
│   ┌──────────────────────────────────────────────────────────────────┐    │
│   │                       生成层                                       │    │
│   │                                                                  │    │
│   │          ┌─────────────────┐                                    │    │
│   │          │   LLM 生成       │                                    │    │
│   │          │  (DeepSeek API)  │                                    │    │
│   │          └────────┬────────┘                                    │    │
│   │                   │                                              │    │
│   └───────────────────┼──────────────────────────────────────────────┘    │
│                       ▼                                                │
│                  最终答案输出                                            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 二、功能需求详述

### 2.1 混合检索系统

#### 2.1.1 检索架构

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           混合检索架构                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│                         查询: "RAG技术原理"                                 │
│                                 │                                           │
│           ┌─────────────────────┼─────────────────────┐                  │
│           │                     │                     │                    │
│           ▼                     ▼                     ▼                    │
│    ┌─────────────┐      ┌─────────────┐      ┌─────────────┐          │
│    │  Dense向量  │      │  Sparse向量  │      │   BM25     │          │
│    │  检索       │      │  (ColBERT)  │      │  关键词检索 │          │
│    └──────┬──────┘      └──────┬──────┘      └──────┬──────┘          │
│           │                     │                     │                    │
│           │  Top-50           │  Top-50           │  Top-50           │
│           │  相似度分          │  相似度分          │  BM25分            │
│           └─────────┬─────────┘         │           └─────────┬─────────┘
│                     │                   │                     │           │
│                     └───────────────────┼─────────────────────┘           │
│                                         │                                 │
│                                         ▼                                 │
│                               ┌─────────────────┐                       │
│                               │  融合策略 (RRF) │                       │
│                               │  Reciprocal     │                       │
│                               │  Rank Fusion    │                       │
│                               └────────┬────────┘                       │
│                                        │                                 │
│                                        │  Top-20                         │
│                                        ▼                                 │
│                               ┌─────────────────┐                       │
│                               │  Cross-Encoder  │                       │
│                               │     Reranker   │                       │
│                               └────────┬────────┘                       │
│                                        │                                 │
│                                        │  Top-10                         │
│                                        ▼                                 │
│                               ┌─────────────────┐                       │
│                               │    答案生成     │                       │
│                               └─────────────────┘                       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### 2.1.2 检索配置

```yaml
# 检索配置模型
retrieval:
  # 检索模式
  mode: "hybrid"  # dense | sparse | keyword | hybrid
  
  # 向量检索配置
  dense:
    enabled: true
    top_k: 50
    min_similarity: 0.3
    
  # 稀疏向量检索配置
  sparse:
    enabled: true
    top_k: 50
    encoder: "colbert"  # colbert | splade
    
  # 关键词检索配置
  keyword:
    enabled: true
    top_k: 50
    algorithm: "bm25"
    k1: 1.5
    b: 0.75
    
  # 融合配置
  fusion:
    method: "rrf"  # rrf | weighted | convex
    weights:
      dense: 0.4
      sparse: 0.3
      keyword: 0.3
    rrf_k: 60  # RRF 参数
    
  # 重排序配置
  rerank:
    enabled: true
    model: "BAAI/bge-reranker-base"
    top_n: 10
    batch_size: 32
    
  # MMR 配置
  mmr:
    enabled: false
    diversity: 0.5
    max_segments: 5
```

#### 2.1.3 需求规格

| 需求ID | 需求描述 | 验收条件 | 验证方法 |
|--------|----------|----------|----------|
| HR-001 | 向量检索 | 支持向量相似度检索 | 检索结果正确 |
| HR-002 | 关键词检索 | 支持 BM25 检索 | 检索结果正确 |
| HR-003 | 稀疏向量检索 | 支持 SPLADE/ColBERT | 检索结果正确 |
| HR-004 | 混合融合 | 支持 RRF 融合 | 结果优于单一检索 |
| HR-005 | 权重配置 | 支持调整融合权重 | 权重生效 |
| HR-006 | Top-K 配置 | 支持配置检索数量 | 数量正确 |
| HR-007 | 相似度阈值 | 支持设置阈值 | 过滤生效 |
| HR-008 | 召回率 | Top-20 召回率 ≥ 85% | 测试集验证 |

### 2.2 查询处理管道

#### 2.2.1 查询处理流程

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         查询处理流程                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  输入: "RAG和LangChain有什么关系？它们能一起用吗？"                         │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │ 1. 意图识别                                                          │  │
│  │    输入: 用户问题                                                     │  │
│  │    输出: { intent: "qa", confidence: 0.95, sub_type: "comparison" }  │  │
│  │                                                                      │  │
│  │    意图类型:                                                         │  │
│  │    - qa: 知识问答                                                    │  │
│  │    - chat: 闲聊                                                     │  │
│  │    - command: 命令                                                  │  │
│  │    - clarification: 澄清                                             │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                    │                                       │
│                                    ▼                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │ 2. 查询改写                                                          │  │
│  │    输入: "RAG和LangChain有什么关系？它们能一起用吗？"                  │  │
│  │    输出: [                                                            │  │
│  │      "RAG技术原理",                                                   │  │
│  │      "LangChain框架介绍",                                             │  │
│  │      "RAG与LangChain集成"                                            │  │
│  │    ]                                                                 │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                    │                                       │
│                                    ▼                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │ 3. 查询扩展 (可选)                                                    │  │
│  │    输入: "RAG技术原理"                                                │  │
│  │    输出: {                                                            │  │
│  │      original: "RAG技术原理",                                         │  │
│  │      expanded: [                                                      │  │
│  │        "Retrieval Augmented Generation",                               │  │
│  │        "RAG检索增强生成原理",                                          │  │
│  │        "RAG工作流程"                                                  │  │
│  │      ]                                                                │  │
│  │    }                                                                 │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                    │                                       │
│                                    ▼                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │ 4. 问题分解 (复杂问题)                                                │  │
│  │    输入: "RAG和LangChain有什么关系？它们能一起用吗？"                  │  │
│  │    输出: [                                                            │  │
│  │      "RAG是什么？",                                                   │  │
│  │      "LangChain是什么？",                                             │  │
│  │      "RAG和LangChain如何集成？",                                       │  │
│  │    ]                                                                 │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                    │                                       │
│                                    ▼                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │ 5. 检索执行                                                          │  │
│  │    对每个子问题执行混合检索                                            │  │
│  │    结果合并去重                                                       │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### 2.2.2 意图识别模型

```python
class IntentType(Enum):
    QA = "qa"                    # 知识问答
    CHAT = "chat"                # 闲聊
    COMMAND = "command"           # 命令
    CLARIFICATION = "clarification"  # 澄清请求
    UNKNOWN = "unknown"          # 未知

class IntentResult:
    intent: IntentType
    confidence: float             # 置信度 0-1
    sub_type: Optional[str]      # 子类型
    entities: List[Entity]       # 识别的实体
    
# 意图识别示例
{
    "question": "RAG和LangChain有什么关系？",
    "intent": "qa",
    "confidence": 0.95,
    "sub_type": "comparison",
    "entities": [
        {"type": "technology", "value": "RAG"},
        {"type": "technology", "value": "LangChain"}
    ]
}
```

#### 2.2.3 查询改写策略

```python
# 查询改写策略
query_rewrite_strategies = {
    # 同义词替换
    "synonym": {
        "enabled": True,
        "thesaurus": "built-in",  # 内置 + 自定义
    },
    
    # 拼写纠正
    "spell_check": {
        "enabled": True,
        "language": "zh-CN",
    },
    
    # 句式转换
    "paraphrase": {
        "enabled": True,
        "num_variants": 3,
        "model": "paraphrase-multilingual",
    },
    
    # 术语标准化
    "normalization": {
        "enabled": True,
        "abbreviations": {
            "RAG": "Retrieval Augmented Generation",
            "LLM": "Large Language Model",
        }
    }
}
```

#### 2.2.4 需求规格

| 需求ID | 需求描述 | 验收条件 | 验证方法 |
|--------|----------|----------|----------|
| QP-001 | 意图识别 | 准确识别问答意图 | 准确率 ≥ 90% |
| QP-002 | 闲聊处理 | 正确处理闲聊问题 | 响应合理 |
| QP-003 | 查询改写 | 改写提升检索效果 | 召回率提升 |
| QP-004 | 同义词扩展 | 同义词检索生效 | 测试验证 |
| QP-005 | 问题分解 | 复杂问题正确分解 | 子问题完整 |
| QP-006 | 检索合并 | 多子问题结果合并 | 去重正确 |
| QP-007 | 配置开关 | 各功能可独立开关 | 配置生效 |
| QP-008 | 性能要求 | 处理延迟 ≤ 200ms | 性能测试 |

### 2.3 重排序 (Rerank)

#### 2.3.1 重排序流程

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Cross-Encoder 重排序                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  初始检索结果 (Top-20)                                                      │
│  ┌────────────────────────────────────────────────────────────────────┐   │
│  │  Doc 1: "RAG是一种检索增强生成技术..."         相似度: 0.85       │   │
│  │  Doc 2: "LangChain是一个LLM应用框架..."      相似度: 0.82       │   │
│  │  Doc 3: "RAG工作流程包含检索和生成..."         相似度: 0.78       │   │
│  │  ...                                                                │   │
│  └────────────────────────────────────────────────────────────────────┘   │
│                                    │                                       │
│                                    ▼                                       │
│  ┌────────────────────────────────────────────────────────────────────┐   │
│  │                    Cross-Encoder 评分                                │   │
│  │                                                                      │   │
│  │  Query: "RAG和LangChain有什么关系？"                                │   │
│  │                                                                      │   │
│  │  Cross-Encoder( Query, Doc ) → Relevance Score                     │   │
│  │                                                                      │   │
│  │  Doc 1: 0.92  (直接讨论RAG)                                       │   │
│  │  Doc 3: 0.88  (RAG工作流程)                                        │   │
│  │  Doc 2: 0.85  (讨论LangChain)                                      │   │
│  │  Doc 5: 0.72  (提到两者)                                            │   │
│  └────────────────────────────────────────────────────────────────────┘   │
│                                    │                                       │
│                                    ▼                                       │
│  ┌────────────────────────────────────────────────────────────────────┐   │
│  │                    最终排序结果 (Top-10)                             │   │
│  │                                                                      │   │
│  │  1. RAG是一种检索增强生成技术...                                     │   │
│  │  2. RAG工作流程包含检索和生成...                                     │   │
│  │  3. LangChain是一个LLM应用框架...                                   │   │
│  │  ...                                                                │   │
│  └────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### 2.3.2 重排序模型配置

```yaml
reranker:
  # 模型选择
  model: "BAAI/bge-reranker-base"
  # 备选模型:
  # - BAAI/bge-reranker-large
  # - cross-encoder/ms-marco-MiniLM-L-6-v2
  # - cross-encoder/ms-marco-MiniLM-L-12-v2
  
  # 推理配置
  max_length: 512
  batch_size: 32
  device: "cuda"  # cuda, cpu, mps
  
  # 评分配置
  normalize: true  # 归一化评分
  score_threshold: 0.3  # 最低评分阈值
  
  # 缓存配置
  cache_enabled: true
  cache_ttl: 3600  # 秒
```

#### 2.3.3 需求规格

| 需求ID | 需求描述 | 验收条件 | 验证方法 |
|--------|----------|----------|----------|
| RR-001 | 重排序功能 | 支持 Cross-Encoder 重排 | 结果质量提升 |
| RR-002 | 模型配置 | 支持切换重排模型 | 模型切换成功 |
| RR-003 | 阈值配置 | 支持设置评分阈值 | 过滤生效 |
| RR-004 | Top-N 配置 | 支持配置返回数量 | 数量正确 |
| RR-005 | 性能要求 | 重排延迟 ≤ 500ms | 性能测试 |
| RR-006 | 缓存支持 | 支持结果缓存 | 缓存命中 |

### 2.4 Prompt 工程平台

#### 2.4.1 Prompt 模板结构

```python
class PromptTemplate:
    id: str
    name: str
    description: str
    template_type: str  # system, user, assistant
    
    # 模板内容
    content: str = """
    【角色定义】
    你是一个{{ profession }}助手，专为{{ domain }}领域提供专业解答。
    
    【知识库信息】
    - 知识库名称: {{ kb_name }}
    - 领域: {{ domain }}
    - 文档数量: {{ doc_count }}
    
    【回答规则】
    {{ #if requires_citation }}
    1. 必须引用参考文档，使用格式: [文档X]
    2. 引用必须准确对应原文
    {{ /if }}
    
    {{ #if max_length }}
    3. 回答长度不超过 {{ max_length }} 字
    {{ /if }}
    
    【上下文】
    {{ context }}
    
    【问题】
    {{ question }}
    """
    
    # 变量定义
    variables: List[TemplateVariable] = [
        Variable(name="profession", type="string", required=True),
        Variable(name="domain", type="string", required=True),
        Variable(name="requires_citation", type="boolean", default=False),
        Variable(name="max_length", type="integer", required=False),
    ]
    
    # 版本管理
    version: int
    is_active: bool
    created_by: str
    created_at: datetime
    updated_at: datetime
```

#### 2.4.2 Prompt 模板管理

| 功能 | 说明 |
|------|------|
| 模板创建 | 创建新的 Prompt 模板 |
| 模板编辑 | 可视化编辑模板内容 |
| 变量配置 | 定义和管理模板变量 |
| 版本管理 | 模板版本历史 |
| A/B 测试 | 对比不同模板效果 |
| 预览测试 | 使用示例数据预览 |

#### 2.4.3 需求规格

| 需求ID | 需求描述 | 验收条件 | 验证方法 |
|--------|----------|----------|----------|
| PP-001 | 模板创建 | 创建 Prompt 模板 | 创建成功 |
| PP-002 | 变量管理 | 支持变量定义和使用 | 变量生效 |
| PP-003 | 模板预览 | 预览渲染结果 | 预览正确 |
| PP-004 | 版本管理 | 模板版本历史 | 版本可回滚 |
| PP-005 | 知识库绑定 | 模板关联知识库 | 关联生效 |
| PP-006 | 默认模板 | 设置默认 Prompt | 默认生效 |
| PP-007 | 模板测试 | 测试模板效果 | 效果对比 |

### 2.5 答案质量评估

#### 2.5.1 质量评估指标

```python
class AnswerQualityMetrics:
    # 相关性指标
    relevance: RelevanceMetrics = {
        "score": float,              # 0-1 综合相关性
        "question_alignment": float, # 问题对齐度
        "context_utilization": float, # 上下文利用率
    }
    
    # 忠实度指标
    faithfulness: FaithfulnessMetrics = {
        "score": float,               # 0-1 忠实度
        "grounded_ratio": float,     # 基于文档的比例
        "factual_accuracy": float,   # 事实准确性
        "hallucination_detected": bool, # 是否检测到幻觉
        "unsupported_claims": List[str], # 不支持的声明
    }
    
    # 质量指标
    quality: QualityMetrics = {
        "completeness": float,  # 回答完整性
        "conciseness": float,   # 回答简洁性
        "readability": float,    # 可读性评分
        "coherence": float,     # 连贯性评分
    }
    
    # 引用指标
    citation: CitationMetrics = {
        "has_citation": bool,       # 是否有引用
        "citation_recall": float,   # 引用召回率
        "citation_precision": float, # 引用准确率
    }
    
    # 综合评分
    overall_score: float  # 0-100
```

#### 2.5.2 评估方法

| 评估类型 | 方法 | 说明 |
|----------|------|------|
| **自动评估** | LLM-as-Judge | 使用大模型评估答案质量 |
| **自动评估** | RAGAS 指标 | 综合多个指标评估 |
| **自动评估** | 幻觉检测 | 检测答案中的幻觉 |
| **人工评估** | 用户反馈 | 用户点赞/点踩/评分 |
| **人工评估** | 专家评审 | 专业人员进行评审 |

#### 2.5.3 需求规格

| 需求ID | 需求描述 | 验收条件 | 验证方法 |
|--------|----------|----------|----------|
| QA-001 | 质量评分 | 生成质量评分 | 评分合理 |
| QA-002 | 多维评估 | 多维度评估指标 | 各维度准确 |
| QA-003 | 幻觉检测 | 检测答案幻觉 | 有效检测 |
| QA-004 | 引用评估 | 评估引用准确性 | 评估正确 |
| QA-005 | 用户反馈 | 收集用户反馈 | 反馈收集成功 |
| QA-006 | 反馈统计 | 统计反馈数据 | 统计准确 |
| QA-007 | 质量报告 | 生成质量报告 | 报告完整 |
| QA-008 | 改进建议 | 基于评估给出建议 | 建议合理 |

---

## 三、接口设计

### 3.1 检索接口

```
POST   /api/v1/search/vector            # 向量检索
  Body: {
    query: string,
    knowledge_base_id: string,
    top_k: number (default: 20)
  }
  Response: {
    results: Array<{id, content, score, metadata}>,
    query_time_ms: number
  }

POST   /api/v1/search/hybrid            # 混合检索
  Body: {
    query: string,
    knowledge_base_id: string,
    config: RetrievalConfig,
    top_k: number (default: 20)
  }
  Response: {
    results: Array<{id, content, score, metadata}>,
    scores: {dense, sparse, keyword},
    query_time_ms: number
  }

POST   /api/v1/search/rerank            # 重排序检索
  Body: {
    query: string,
    documents: Array<{id, content}>,
    top_n: number (default: 10),
    model: string (optional)
  }
  Response: {
    results: Array<{id, content, rerank_score, original_score}>,
    rerank_time_ms: number
  }
```

### 3.2 查询处理接口

```
POST   /api/v1/query/intent             # 意图识别
  Body: { query: string }
  Response: {
    intent: string,
    confidence: number,
    sub_type: string,
    entities: Array<{type, value}>
  }

POST   /api/v1/query/rewrite            # 查询改写
  Body: {
    query: string,
    strategies: Array<string> (optional)
  }
  Response: {
    original: string,
    rewritten: Array<string>
  }

POST   /api/v1/query/expand             # 查询扩展
  Body: { query: string }
  Response: {
    original: string,
    expanded: Array<string>
  }

POST   /api/v1/query/decompose          # 问题分解
  Body: { query: string }
  Response: {
    original: string,
    sub_questions: Array<string>
  }
```

### 3.3 Prompt 模板接口

```
GET    /api/v1/prompts/templates       # 模板列表
POST   /api/v1/prompts/templates       # 创建模板
GET    /api/v1/prompts/templates/{id} # 模板详情
PUT    /api/v1/prompts/templates/{id} # 更新模板
DELETE /api/v1/prompts/templates/{id} # 删除模板
POST   /api/v1/prompts/templates/{id}/preview # 预览
POST   /api/v1/prompts/templates/{id}/duplicate # 复制模板
GET    /api/v1/prompts/templates/{id}/versions # 版本历史
POST   /api/v1/prompts/templates/{id}/rollback # 回滚版本

GET    /api/v1/prompts/variables       # 变量列表
POST   /api/v1/prompts/variables       # 创建变量
```

### 3.4 质量评估接口

```
POST   /api/v1/qa/evaluate             # 评估答案质量
  Body: {
    question: string,
    answer: string,
    context: Array<string>,
    metrics: Array<string> (optional)
  }
  Response: {
    relevance: number,
    faithfulness: number,
    quality: number,
    citation: {has_citation, recall, precision},
    overall_score: number,
    details: {...}
  }

POST   /api/v1/qa/{log_id}/feedback   # 提交反馈
  Body: {
    rating: number (1-5),
    thumbs_up: boolean,
    thumbs_down: boolean,
    corrections: string (optional),
    preferred_answer: string (optional)
  }

GET    /api/v1/qa/feedback/stats       # 反馈统计
GET    /api/v1/qa/quality/report       # 质量报告
```

---

## 四、非功能需求

### 4.1 性能需求

| 指标 | 目标值 | 说明 |
|------|--------|------|
| 混合检索延迟 | ≤ 300ms | Top-20 检索 |
| 重排序延迟 | ≤ 500ms | Top-20 重排 |
| 查询处理延迟 | ≤ 200ms | 意图识别+改写 |
| 质量评估延迟 | ≤ 1s | 单条评估 |
| 吞吐量 | ≥ 50 QPS | 检索服务 |

### 4.2 质量需求

| 指标 | 目标值 | 说明 |
|------|--------|------|
| Top-20 召回率 | ≥ 85% | 标准测试集 |
| 意图识别准确率 | ≥ 90% | 问答意图 |
| 答案质量评分 | ≥ 80 分 | 综合评分 |
| 幻觉检测率 | ≥ 85% | 有效检测 |

---

## 五、验收清单

### 5.1 混合检索验收

| 序号 | 验收项 | 验收条件 | 验证方法 | 状态 |
|------|--------|----------|----------|------|
| 1 | 向量检索 | 检索结果正确 | 功能测试 | ⬜ |
| 2 | 关键词检索 | 检索结果正确 | 功能测试 | ⬜ |
| 3 | 混合融合 | 结果优于单一检索 | 对比测试 | ⬜ |
| 4 | 权重配置 | 权重生效 | 配置测试 | ⬜ |
| 5 | 阈值过滤 | 过滤生效 | 配置测试 | ⬜ |
| 6 | 召回率 | ≥ 85% | 测试集验证 | ⬜ |

### 5.2 查询处理验收

| 序号 | 验收项 | 验收条件 | 验证方法 | 状态 |
|------|--------|----------|----------|------|
| 1 | 意图识别 | 准确率 ≥ 90% | 测试集验证 | ⬜ |
| 2 | 闲聊处理 | 响应合理 | 功能测试 | ⬜ |
| 3 | 查询改写 | 提升召回率 | 对比测试 | ⬜ |
| 4 | 问题分解 | 子问题完整 | 功能测试 | ⬜ |
| 5 | 结果合并 | 去重正确 | 功能测试 | ⬜ |
| 6 | 处理延迟 | ≤ 200ms | 性能测试 | ⬜ |

### 5.3 重排序验收

| 序号 | 验收项 | 验收条件 | 验证方法 | 状态 |
|------|--------|----------|----------|------|
| 1 | 重排功能 | 质量提升 | 对比测试 | ⬜ |
| 2 | 模型切换 | 切换成功 | 功能测试 | ⬜ |
| 3 | 阈值过滤 | 过滤生效 | 功能测试 | ⬜ |
| 4 | 延迟要求 | ≤ 500ms | 性能测试 | ⬜ |
| 5 | 缓存支持 | 缓存生效 | 功能测试 | ⬜ |

### 5.4 Prompt 平台验收

| 序号 | 验收项 | 验收条件 | 验证方法 | 状态 |
|------|--------|----------|----------|------|
| 1 | 模板创建 | 创建成功 | 功能测试 | ⬜ |
| 2 | 变量管理 | 变量生效 | 功能测试 | ⬜ |
| 3 | 模板预览 | 预览正确 | 功能测试 | ⬜ |
| 4 | 版本管理 | 版本可回滚 | 功能测试 | ⬜ |
| 5 | 知识库绑定 | 关联生效 | 功能测试 | ⬜ |

### 5.5 质量评估验收

| 序号 | 验收项 | 验收条件 | 验证方法 | 状态 |
|------|--------|----------|----------|------|
| 1 | 质量评分 | 评分合理 | 专家评审 | ⬜ |
| 2 | 多维评估 | 各维度准确 | 专家评审 | ⬜ |
| 3 | 幻觉检测 | 有效检测 | 测试集验证 | ⬜ |
| 4 | 用户反馈 | 收集成功 | 功能测试 | ⬜ |
| 5 | 质量报告 | 报告完整 | 功能测试 | ⬜ |

---

## 六、风险与应对

| 风险 | 影响 | 可能性 | 应对措施 |
|------|------|--------|----------|
| 重排性能瓶颈 | 高 | 中 | GPU 优化/批处理 |
| 意图识别准确率不足 | 中 | 中 | 领域微调/规则补充 |
| 幻觉检测漏检 | 高 | 中 | 多模型ensemble |
| 召回率不达标 | 中 | 中 | 多路召回优化 |

---

## 七、版本历史

| 版本 | 日期 | 修改内容 | 作者 |
|------|------|----------|------|
| V1.0 | 2026-05-17 | 初始版本 | - |
