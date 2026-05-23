# RAG 知识库系统 - 大厂RAG面试题

> 本文档包含30道来自大厂的真实RAG面试题，涵盖深度技术问题、系统设计、场景解决等方面。

---

## 第一部分：深度技术问题（共10题）

### Q1: 描述一下RAG的完整技术架构？

**题目类型**：系统设计类

**公司类型**：互联网大厂/AI公司

**问题描述**：请描述一个完整的RAG系统从文档导入到答案生成的完整技术架构，包括各组件的作用和数据流。

**答案要点**：

**完整架构图：**

```
┌─────────────────────────────────────────────────────────────────┐
│                        文档层                                     │
│         PDF解析  |  Word解析  |  OCR识别  |  表格解析          │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                      清洗与切分层                                │
│       文本清洗  |  语义切分  |  Chunk管理                    │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                      向量与索引层                                │
│      Embedding生成  |  向量存储  |  全文索引                  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                       检索与排序层                               │
│      混合检索  |  重排序  |  上下文组装                       │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                       生成层                                     │
│         Prompt工程  |  LLM生成  |  答案后处理                   │
└─────────────────────────────────────────────────────────────────┘
```

**关键组件详解：**

| 组件 | 技术选型 | 核心职责 |
|------|----------|----------|
| 文档解析 | PyMuPDF、python-docx | 结构化提取 |
| 文本清洗 | 正则、NLP工具 | 去噪标准化 |
| 语义切分 | 基于语义模型 | 保持完整性 |
| Embedding | Qwen3-Embedding | 向量化 |
| 向量存储 | Milvus | 高效检索 |
| 全文索引 | MySQL FULLTEXT | 关键词匹配 |
| 混合检索 | RRF融合 | 综合排序 |
| 重排序 | Cross-Encoder | 精细排序 |
| LLM | Qwen/Ollama | 答案生成 |

---

### Q2: RAG系统中如何处理文档的智能切分？

**题目类型**：深度技术类

**公司类型**：AI公司/企业服务

**问题描述**：文档切分是RAG效果的关键环节。请描述如何实现智能切分，保证语义完整性？

**答案要点**：

**切分策略：**

1. **基于结构的切分**
   - 识别文档标题层级（h1、h2、h3）
   - 按章节边界切分
   - 保持标题和内容的关联

2. **基于语义的切分**
   - 使用NLP模型判断句子边界
   - 检测段落间的语义连贯性
   - 在语义断点处切分

3. **基于规则的切分**
   - Token数量限制（通常600-900）
   - 重叠机制（Overlap 80-120 tokens）
   - 特殊内容保护（表格、代码块）

**实现代码框架：**

```python
class SmartChunker:
    def chunk(self, document):
        # 1. 识别文档结构
        structure = self.analyze_structure(document)
        
        # 2. 按结构分组
        sections = self.group_by_structure(structure)
        
        # 3. 语义切分
        chunks = []
        for section in sections:
            if self.count_tokens(section) <= MAX_TOKENS:
                chunks.append(section)
            else:
                sub_chunks = self.semantic_split(section)
                chunks.extend(sub_chunks)
        
        # 4. 添加Overlap
        chunks = self.add_overlap(chunks)
        
        return chunks
    
    def semantic_split(self, text):
        # 使用语义模型检测断点
        sentences = self.split_sentences(text)
        breakpoints = self.detect_breakpoints(sentences)
        return self.create_chunks(sentences, breakpoints)
```

**面试追问点：**
- 如何处理表格跨页问题？
- 如何保证列表项不被截断？
- 如何处理中英混合文档？

---

### Q3: 混合检索中向量检索和关键词检索如何融合？

**题目类型**：深度技术类

**公司类型**：搜索/AI公司

**问题描述**：混合检索是提升召回率的关键。请描述向量检索和关键词检索如何融合？

**答案要点**：

**融合策略对比：**

| 策略 | 公式 | 适用场景 | 效果 |
|------|------|----------|------|
| RRF | 1/(k+rank) | 通用场景 | 稳定 |
| 加权求和 | w1×v + w2×k | 偏重某通道 | 可调 |
| 分数归一化 | norm(v)×w1 + norm(k)×w2 | 分数差异大 | 平衡 |

**RRF实现：**

```python
def rrf_fusion(vector_results, keyword_results, k=60):
    """
    Reciprocal Rank Fusion
    """
    scores = defaultdict(float)
    
    # 向量检索结果打分
    for rank, doc in enumerate(vector_results):
        scores[doc.id] += 1 / (k + rank + 1)
    
    # 关键词检索结果打分
    for rank, doc in enumerate(keyword_results):
        scores[doc.id] += 1 / (k + rank + 1)
    
    # 按分数排序
    sorted_docs = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return [doc_id for doc_id, _ in sorted_docs]
```

**权重配置建议：**
- 语义问题：向量权重0.7
- 精确术语：关键词权重0.7
- 通用场景：各0.5

**面试追问点：**
- 如何处理结果重复问题？
- 如何根据Query类型动态调整权重？

---

### Q4: 如何优化RAG系统的检索召回率？

**题目类型**：优化类

**公司类型**：电商/AI公司

**问题描述**：用户反馈RAG系统召回不准确，如何系统性优化召回率？

**答案要点**：

**优化框架：**

```
召回率低 → 原因分析 → 针对性优化
    ↓
┌─────────────────────────────────┐
│ 原因1: Query表达与文档不匹配     │
│ 优化: 查询改写、多查询生成       │
├─────────────────────────────────┤
│ 原因2: 切分破坏语义完整性        │
│ 优化: 智能切分、增加Overlap      │
├─────────────────────────────────┤
│ 原因3: 检索策略单一             │
│ 优化: 混合检索、多路召回         │
├─────────────────────────────────┤
│ 原因4: 向量质量差               │
│ 优化: 更好的Embedding模型       │
└─────────────────────────────────┘
```

**具体措施：**

| 优化方向 | 具体方法 | 预期提升 |
|----------|----------|----------|
| Query改写 | 同义词扩展、口语化转正式 | +10-15% |
| 混合检索 | 向量+关键词RRF融合 | +5-10% |
| 智能切分 | 语义切分+Overlap | +5-10% |
| 重排序 | Cross-Encoder重排 | +5-8% |

**实验验证：**

```python
def evaluate_recall_improvement():
    test_queries = load_test_set()
    metrics = []
    
    for query in test_queries:
        # Baseline
        baseline = baseline_search(query)
        
        # 优化方案
        with_query_rewrite = search_with_rewrite(query)
        with_hybrid = search_with_hybrid(query)
        with_all = search_with_all_optimizations(query)
        
        metrics.append({
            'baseline': calculate_recall(baseline),
            'query_rewrite': calculate_recall(with_query_rewrite),
            'hybrid': calculate_recall(with_hybrid),
            'all': calculate_recall(with_all)
        })
    
    return aggregate_metrics(metrics)
```

---

### Q5: 描述一下RAG系统中Prompt工程的设计？

**题目类型**：深度技术类

**公司类型**：AI公司

**问题描述**：Prompt设计直接影响生成质量。请描述RAG系统中的Prompt工程设计。

**答案要点：**

**Prompt模板设计：**

```python
# RAG问答Prompt模板
QA_PROMPT = """
你是一个专业的知识库助手。请根据以下参考内容回答用户问题。

## 参考内容
{context}

## 要求
1. 只根据参考内容回答，不要编造信息
2. 如果参考内容不足以回答，请明确说明
3. 回答要准确、简洁、有条理
4. 在回答中标注参考来源

## 用户问题
{question}

## 回答
"""

# 带思维链的Prompt
COT_PROMPT = """
你是一个专业的知识库助手。请先思考再回答。

## 参考内容
{context}

## 用户问题
{question}

## 思考过程
请分析问题涉及的关键点：
1.
2.
3.

## 回答
"""
```

**Prompt优化策略：**

| 策略 | 方法 | 效果 |
|------|------|------|
| Few-shot | 添加示例 | 提升准确性 |
| Chain-of-Thought | 引导思考 | 提升逻辑性 |
| System Prompt | 设定角色/规则 | 提升一致性 |
| Context压缩 | 精简上下文 | 提升效率 |

**面试追问点：**
- 如何处理Context过长超出Token限制？
- 如何避免模型产生幻觉？

---

### Q6: RAG系统中如何实现文档的版本管理？

**题目类型**：系统设计类

**公司类型**：企业服务/知识管理

**问题描述**：企业文档经常更新，RAG系统如何管理文档版本？

**答案要点：**

**版本管理架构：**

```
文档更新
    ↓
文件Hash比对 → 版本检测
    ↓
┌─────────────────────────────────┐
│ 新版本 → 增量解析 → 增量索引    │
│ 旧版本 → 标记为inactive        │
└─────────────────────────────────┘
    ↓
检索时默认只查active版本
```

**数据模型设计：**

```sql
-- 文档表
CREATE TABLE documents (
    id VARCHAR(64) PRIMARY KEY,
    name VARCHAR(255),
    current_version_id VARCHAR(64)
);

-- 版本表
CREATE TABLE document_versions (
    id VARCHAR(64) PRIMARY KEY,
    document_id VARCHAR(64),
    version INT,
    file_hash VARCHAR(64),
    status ENUM('active', 'inactive', 'archived'),
    created_at TIMESTAMP
);

-- Chunk表关联版本
CREATE TABLE chunks (
    id VARCHAR(64) PRIMARY KEY,
    version_id VARCHAR(64),
    content TEXT,
    vector_id VARCHAR(64)
);
```

**增量更新策略：**

| 策略 | 适用场景 | 实现复杂度 |
|------|----------|------------|
| 全量重建 | 小文档集 | 低 |
| 版本Diff | 变化比例<30% | 中 |
| 向量Diff | 变化比例<10% | 高 |

**面试追问点：**
- 如何处理历史问答引用的旧版本？
- 如何平衡新旧版本的存储成本？

---

### Q7: RAG系统中如何实现权限控制？

**题目类型**：系统设计类

**公司类型**：企业服务/金融

**问题描述**：企业知识库需要权限控制，不同用户只能访问有权限的文档。如何实现？

**答案要点：**

**权限模型设计：**

```python
# 权限模型
class Permission:
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    ADMIN = "admin"

# 文档权限
class DocumentPermission:
    def __init__(self):
        self.acl = {}  # {doc_id: {user_id: [permissions]}}
    
    def check(self, user_id: str, doc_id: str, permission: str) -> bool:
        """检查用户对文档的权限"""
        user_perms = self.acl.get(doc_id, {}).get(user_id, [])
        return permission in user_perms
    
    def filter_docs(self, user_id: str, doc_ids: list) -> list:
        """过滤用户有权限访问的文档"""
        return [
            doc_id for doc_id in doc_ids
            if self.acl.get(doc_id, {}).get(user_id)
        ]
```

**检索时权限过滤：**

```python
async def search_with_permission(user_id: str, query: str):
    # 1. 执行检索
    results = await hybrid_search(query)
    
    # 2. 获取用户有权限的文档ID
    allowed_docs = await get_user_allowed_docs(user_id)
    
    # 3. 权限过滤
    filtered_results = [
        r for r in results
        if r.document_id in allowed_docs
    ]
    
    return filtered_results
```

**面试追问点：**
- 权限变更后缓存如何处理？
- 如何设计权限继承机制？

---

### Q8: 如何评估RAG系统的效果？

**题目类型**：指标设计类

**公司类型**：AI公司/研究机构

**问题描述**：RAG系统的效果如何量化评估？请设计完整的评估体系。

**答案要点：**

**评估指标体系：**

| 维度 | 指标 | 计算方式 | 权重 |
|------|------|----------|------|
| 检索 | Recall@K | 命中数/总相关数 | 25% |
| 检索 | MRR | 1/排名求和/N | 15% |
| 生成 | 答案准确率 | 正确/总数 | 30% |
| 生成 | 答案完整率 | 完整/总数 | 15% |
| 体验 | 响应时间 | P99延迟 | 10% |
| 体验 | 成功率 | 成功/总数 | 5% |

**评估数据集构建：**

```python
class RAGEvaluator:
    def __init__(self):
        self.test_set = self.load_test_set()
    
    def evaluate(self, rag_system):
        results = []
        
        for item in self.test_set:
            query = item['query']
            expected = item['expected_answer']
            
            # 执行RAG流程
            answer = rag_system.ask(query)
            
            # 评估
            retrieval_recall = self.evaluate_retrieval(
                rag_system.last_retrieved_docs,
                item['relevant_docs']
            )
            answer_accuracy = self.evaluate_answer(answer, expected)
            
            results.append({
                'query': query,
                'retrieval_recall': retrieval_recall,
                'answer_accuracy': answer_accuracy,
                'latency': rag_system.last_latency
            })
        
        return self.aggregate(results)
```

**面试追问点：**
- 如何构建高质量的Ground Truth？
- 如何处理开放域问题的评估？

---

### Q9: RAG系统中如何处理多模态内容（图片、表格）？

**题目类型**：深度技术类

**公司类型**：AI公司/文档处理

**问题描述**：企业文档包含大量图片和表格，RAG系统如何处理这些多模态内容？

**答案要点：**

**多模态处理策略：**

| 类型 | 处理方法 | 向量化 |
|------|----------|--------|
| 图片 | 多模态模型描述 | 图片Embedding |
| 表格 | 结构化提取+摘要 | 文本Embedding |
| 图表 | 提取数据+描述 | 文本Embedding |

**表格处理：**

```python
class TableProcessor:
    def process(self, table_element):
        # 1. 识别表头和内容
        headers = self.extract_headers(table_element)
        rows = self.extract_rows(table_element)
        
        # 2. 生成表格摘要
        summary = self.generate_summary(headers, rows)
        
        # 3. 构建增强文本
        enhanced = f"""
表格标题: {table_element.caption}
表格摘要: {summary}
表头: {', '.join(headers)}
数据: {self.serialize_rows(rows)}
"""
        
        return {
            'content': enhanced,
            'summary': summary,
            'headers': headers,
            'row_count': len(rows)
        }
```

**图片处理：**

```python
class ImageProcessor:
    def process(self, image_element):
        # 1. 图片描述生成
        description = self.vlm_describe(image_element)
        
        # 2. 提取关键信息
        key_info = self.extract_key_info(description)
        
        # 3. 构建检索文本
        retrieval_text = f"""
图片标题: {image_element.caption}
图片描述: {description}
关键信息: {key_info}
"""
        
        return {
            'content': retrieval_text,
            'description': description,
            'image_path': image_element.path
        }
```

**面试追问点：**
- 如何保证表格的上下文不丢失？
- 如何处理扫描版PDF中的图片？

---

### Q10: 如何设计RAG系统的缓存策略提升性能？

**题目类型**：性能优化类

**公司类型**：大型互联网

**问题描述**：RAG系统中哪些地方可以缓存？缓存策略如何设计？

**答案要点：**

**缓存分层架构：**

```
┌─────────────────────────────────────┐
│ L1: 本地内存缓存 (ms级)            │
│ - 热点Query向量                     │
│ - 热门文档摘要                      │
│ - 热点Chunk向量                     │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│ L2: Redis缓存 (ms级)               │
│ - Query向量                         │
│ - 检索结果                          │
│ - 会话状态                          │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│ L3: 向量库/数据库 (s级)            │
│ - Chunk向量                         │
│ - 文档元数据                        │
└─────────────────────────────────────┘
```

**缓存实现：**

```python
class RAGCache:
    def __init__(self, local_cache, redis_cache):
        self.local = local_cache
        self.redis = redis_cache
    
    async def get_query_vector(self, query: str):
        """查询向量缓存"""
        key = self.hash_query(query)
        
        # L1
        vector = self.local.get(key)
        if vector:
            return vector
        
        # L2
        vector = self.redis.get(key)
        if vector:
            self.local.set(key, vector)
            return vector
        
        return None
    
    async def get_search_results(self, query_vector, filters):
        """检索结果缓存"""
        cache_key = self.hash_search_params(query_vector, filters)
        
        results = self.redis.get(cache_key)
        if results:
            return results
        
        # 计算并缓存
        results = await self.do_search(query_vector, filters)
        self.redis.setex(cache_key, results, ttl=3600)
        
        return results
```

**缓存失效策略：**

| 事件 | 失效范围 | 策略 |
|------|----------|------|
| 文档更新 | 相关Query缓存 | 选择性清除 |
| Embedding模型更新 | 所有向量缓存 | 全量清除 |
| Chunk更新 | 相关检索结果 | 版本控制 |

---

## 第二部分：系统设计类（共10题）

### Q11: 设计一个企业级RAG知识库系统

**题目类型**：系统设计类

**公司类型**：咨询/企业服务

**问题描述**：某大型企业需要构建一个内部知识库系统，包含百万级文档，支持千人并发访问。请设计这个系统。

**答案要点：**

**系统架构设计：**

```
┌─────────────────────────────────────────────────────────────────┐
│                        接入层                                     │
│             API网关  |  负载均衡  |  CDN加速                      │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                       服务层                                     │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐         │
│  │ 文档服务 │ │ 检索服务 │ │ 问答服务 │ │ 管理服务 │         │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘         │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                       数据层                                     │
│  Milvus集群  |  MySQL集群  |  Redis集群  |  MinIO集群         │
└─────────────────────────────────────────────────────────────────┘
```

**容量规划：**

| 指标 | 数值 |
|------|------|
| 文档数量 | 100万 |
| 平均Chunk数/文档 | 50 |
| 向量总数 | 5000万 |
| 向量维度 | 1024 |
| 存储空间 | ~200GB |
| QPS | 1000 |

**高可用设计：**
- 服务层：无状态部署，水平扩展
- 数据层：多副本部署
- 缓存层：Redis集群

**面试追问点：**
- 如何支持多语言文档？
- 如何保证数据安全合规？

---

### Q12: 如何设计RAG系统的多租户隔离？

**题目类型**：系统设计类

**公司类型**：SaaS平台

**问题描述**：SaaS版RAG系统需要服务多个租户，租户间数据完全隔离。如何设计？

**答案要点：**

**隔离方案对比：**

| 方案 | 隔离程度 | 成本 | 适用场景 |
|------|----------|------|----------|
| 独立数据库 | 最高 | 高 | 数据敏感型 |
| 独立Schema | 高 | 中 | 中等隔离 |
| 表内租户ID | 中 | 低 | 普通场景 |

**推荐方案：混合隔离**

```python
class MultiTenantIsolation:
    def __init__(self):
        # 向量库：Collection隔离
        self.milvus_collections = {}  # tenant_id -> collection
    
    def get_collection(self, tenant_id: str):
        if tenant_id not in self.milvus_collections:
            # 动态创建Collection
            self.milvus_collections[tenant_id] = self.create_collection(tenant_id)
        return self.milvus_collections[tenant_id]
    
    def search(self, tenant_id: str, query_vector):
        collection = self.get_collection(tenant_id)
        return collection.search(query_vector)
```

**数据模型：**

```sql
-- MySQL: 表内隔离
CREATE TABLE chunks (
    id VARCHAR(64),
    tenant_id VARCHAR(64) NOT NULL,  -- 租户ID
    content TEXT,
    INDEX idx_tenant (tenant_id)
);

-- 检索时强制加租户条件
SELECT * FROM chunks 
WHERE tenant_id = ? AND content MATCH('...');
```

**面试追问点：**
- 租户资源配额如何管理？
- 如何处理租户数据迁移？

---

### Q13: 设计RAG系统的监控和可观测性体系

**题目类型**：系统设计类

**公司类型**：大型互联网

**问题描述**：RAG系统需要完善的监控体系。请设计监控指标和告警机制。

**答案要点：**

**监控四大支柱：**

| 支柱 | 内容 | 工具 |
|------|------|------|
| Metrics | 指标数据 | Prometheus |
| Logs | 日志记录 | ELK/Loki |
| Traces | 调用链路 | Jaeger |
| Health | 健康检查 | 自研 |

**核心指标体系：**

```yaml
# 业务指标
business:
  retrieval:
    recall_rate: 0.85  # 召回率
    avg_chunks_per_query: 12  # 平均召回数
  qa:
    answer_accuracy: 0.90  # 答案准确率
    satisfaction_score: 4.2  # 满意度(5分制)
  
# 技术指标
technical:
  api:
    qps: 1000
    p99_latency_ms: 300
    error_rate: 0.001
  retrieval:
    vector_search_ms: 50
    keyword_search_ms: 20
    rerank_ms: 100
  
# 资源指标
resources:
  milvus:
    memory_usage_gb: 64
    vector_count: 50000000
  mysql:
    connection_usage: 0.6
    query_p99_ms: 100
```

**告警配置：**

```yaml
alerts:
  - name: high_latency
    condition: "p99_latency > 1000ms"
    severity: warning
    channels: [dingtalk, email]
  
  - name: retrieval_failure
    condition: "error_rate > 0.01"
    severity: critical
    channels: [phone, sms]
  
  - name: resource_exhaustion
    condition: "memory_usage > 0.85"
    severity: warning
    channels: [dingtalk]
```

**面试追问点：**
- 如何设置合理的告警阈值？
- 如何避免告警疲劳？

---

### Q14: 如何设计RAG系统的A/B测试框架？

**题目类型**：系统设计类

**公司类型**：AI公司

**问题描述**：需要持续优化RAG系统效果。请设计一个A/B测试框架来验证优化效果。

**答案要点：**

**A/B测试架构：**

```python
class ABTestFramework:
    def __init__(self):
        self.experiments = {}
    
    def create_experiment(self, name, variants):
        """创建实验"""
        self.experiments[name] = {
            'variants': variants,
            'metrics': {k: [] for k in variants}
        }
    
    def assign_user(self, user_id, experiment_name):
        """用户分组"""
        bucket = hash(user_id) % 100
        cumulative = 0
        
        for variant, config in self.experiments[experiment_name]['variants'].items():
            cumulative += config['traffic']
            if bucket < cumulative:
                return variant
        
        return list(self.experiments[experiment_name]['variants'].keys())[0]
    
    def record(self, experiment_name, variant, metrics):
        """记录指标"""
        self.experiments[experiment_name]['metrics'][variant].append(metrics)
```

**实验示例：**

```yaml
experiments:
  - name: "retrieval_weight"
    variants:
      control:
        traffic: 50
        params:
          vector_weight: 0.5
          keyword_weight: 0.5
      treatment:
        traffic: 50
        params:
          vector_weight: 0.7
          keyword_weight: 0.3
    
    metrics:
      - recall_rate
      - answer_accuracy
      - user_satisfaction
    
    min_sample_size: 1000
    duration: 7d
```

**统计显著性检验：**

```python
def check_significance(control_metrics, treatment_metrics):
    """检验统计显著性"""
    from scipy import stats
    
    t_stat, p_value = stats.ttest_ind(
        control_metrics,
        treatment_metrics
    )
    
    return {
        'significant': p_value < 0.05,
        'p_value': p_value,
        'lift': (mean(treatment_metrics) - mean(control_metrics)) / mean(control_metrics)
    }
```

---

### Q15: 设计RAG系统的数据迁移方案

**题目类型**：系统设计类

**公司类型**：企业服务

**问题描述**：需要将现有系统迁移到新架构（如更换向量库）。如何设计数据迁移方案？

**答案要点：**

**迁移策略：**

```
Phase 1: 准备阶段
├── 新环境部署
├── 数据同步方案设计
└── 回滚方案准备

Phase 2: 双写阶段
├── 新系统写入
├── 旧系统写入
└── 数据一致性验证

Phase 3: 流量切换
├── 小流量测试
├── 逐步放量
└── 全量切换

Phase 4: 收尾
├── 旧系统数据迁移
├── 旧系统下线
└── 监控观察
```

**数据迁移实现：**

```python
class DataMigration:
    async def migrate_vectors(self, batch_size=1000):
        """向量数据迁移"""
        total = 0
        source = MilvusConnection('old')
        target = MilvusConnection('new')
        
        # 创建目标索引
        await target.create_index()
        
        # 分批迁移
        cursor = await source.query_chunks(batch_size)
        
        while True:
            batch = await cursor.fetch(batch_size)
            if not batch:
                break
            
            # 转换格式
            vectors = [self.transform(chunk) for chunk in batch]
            
            # 写入目标
            await target.insert(vectors)
            
            total += len(vectors)
            logger.info(f"已迁移 {total} 条")
        
        # 验证
        source_count = await source.count()
        target_count = await target.count()
        
        if source_count != target_count:
            raise MigrationError(f"数据量不一致: {source_count} vs {target_count}")
```

**回滚方案：**
- DNS切换回旧系统
- 保留旧系统30天
- 数据迁移回滚

---

### Q16: 如何设计RAG系统的灾备方案？

**题目类型**：系统设计类

**公司类型**：金融/大型企业

**问题描述**：作为核心业务系统，RAG需要完善的灾备方案。请设计。

**答案要点：**

**灾备架构：**

```
┌─────────────────────────────────────────────────────────┐
│                    主站点 (A区)                          │
│    Active ←实时复制→ Standby (B区)                     │
│                                                          │
│    RPO: 5分钟   RTO: 30分钟                            │
└─────────────────────────────────────────────────────────┘
```

**备份策略：**

| 层级 | 备份方式 | RPO | RTO |
|------|----------|-----|-----|
| 向量数据 | 增量备份+实时复制 | 5min | 15min |
| 关系数据 | 主从同步 | 5min | 10min |
| 文件存储 | 定时同步 | 1h | 1h |
| 配置数据 | 版本控制 | 实时 | 5min |

**切换流程：**

```python
async def disaster_recovery_switch():
    """灾备切换"""
    # 1. 确认主站点故障
    if await health_check('primary'):
        logger.info("主站点正常，无需切换")
        return
    
    # 2. 通知相关人员
    await notify("灾备切换开始")
    
    # 3. DNS切换
    await dns.switch('primary', 'disaster')
    
    # 4. 验证服务
    if await health_check('disaster'):
        logger.info("灾备站点启动成功")
    else:
        logger.error("灾备站点启动失败，启用紧急预案")
        await activate_cold_standby()
    
    # 5. 通知完成
    await notify("灾备切换完成")
```

**面试追问点：**
- 如何保证RPO达到5分钟？
- 切换过程中数据一致性如何保证？

---

### Q17: 设计RAG系统的自动化运维体系

**题目类型**：系统设计类

**公司类型**：大型互联网

**问题描述**：RAG系统需要自动化运维能力。请设计自动化运维体系。

**答案要点：**

**自动化运维框架：**

```
┌─────────────────────────────────────────────────────────────────┐
│                        自动化平台                                 │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐              │
│  │  CI/CD      │ │  监控告警   │ │  故障自愈  │              │
│  └─────────────┘ └─────────────┘ └─────────────┘              │
└─────────────────────────────────────────────────────────────────┘
```

**核心自动化能力：**

| 能力 | 功能 | 工具 |
|------|------|------|
| 持续交付 | 自动构建、测试、部署 | GitLab CI, ArgoCD |
| 配置管理 | 基础设施代码化 | Terraform, Ansible |
| 监控告警 | 自动发现问题 | Prometheus, Grafana |
| 故障自愈 | 自动恢复 | 自研+运维平台 |
| 容量管理 | 自动扩缩容 | K8s HPA |

**自动化场景：**

```yaml
# 自动化扩缩容
scaling:
  - trigger: "queue_depth > 1000"
    action: "scale_workers +2"
  
  - trigger: "queue_depth < 100"
    action: "scale_workers -1"
  
  - trigger: "p99_latency > 500ms"
    action: "scale_api +1"

# 自动化故障恢复
recovery:
  - trigger: "milvus_querynode_down"
    action: "restart_pod"
  
  - trigger: "mysql_connection_exhausted"
    action: "restart_api_pods"
```

---

### Q18: 如何设计RAG系统的安全防护？

**题目类型**：系统设计类

**公司类型**：金融/政务

**问题描述**：RAG系统涉及企业核心知识，需要完善的安全防护。请设计。

**答案要点：**

**安全防护层次：**

| 层级 | 措施 |
|------|------|
| 网络层 | VPC隔离、安全组、网络ACL |
| 传输层 | HTTPS、TLS 1.3 |
| 认证层 | OAuth2、JWT、API Key |
| 授权层 | RBAC、ABAC、细粒度权限 |
| 数据层 | 加密存储、脱敏、审计 |
| 应用层 | 输入验证、WAF、SQL注入防护 |

**权限模型：**

```python
class RBACPermission:
    def __init__(self):
        self.roles = {
            'admin': ['read', 'write', 'delete', 'manage'],
            'editor': ['read', 'write'],
            'viewer': ['read']
        }
    
    def check(self, user: User, resource: Document, action: str) -> bool:
        user_role = self.get_user_role(user)
        role_perms = self.roles.get(user_role, [])
        
        if action in role_perms:
            # 检查资源级别的ACL
            return resource.acl.get(user.id, action in role_perms)
        
        return False
```

**数据安全：**

```python
class DataSecurity:
    def sensitive_filter(self, content: str) -> str:
        """敏感信息过滤"""
        patterns = [
            (r'\d{11}', '[手机号]'),  # 手机号
            (r'\d{18}', '[身份证]'),  # 身份证
            (r'\w+@\w+\.\w+', '[邮箱]')  # 邮箱
        ]
        
        for pattern, replacement in patterns:
            content = re.sub(pattern, replacement, content)
        
        return content
```

---

### Q19: 设计RAG系统的成本优化方案

**题目类型**：系统设计类

**公司类型**：成本敏感型业务

**问题描述**：RAG系统成本较高。请设计成本优化方案。

**答案要点：**

**成本分解：**

| 成本项 | 占比 | 优化空间 |
|--------|------|----------|
| LLM API | 30% | 缓存、限流 |
| Embedding API | 25% | 缓存、批量 |
| 向量数据库 | 20% | PQ压缩、分片 |
| 计算资源 | 15% | 弹性伸缩 |
| 存储 | 10% | 冷热分层 |

**具体优化措施：**

```python
# 1. Embedding缓存
cache_config = {
    'embedding_cache': {
        'hit_rate_target': 0.6,
        'ttl': 86400,
        'max_size': 100000
    }
}

# 2. 向量压缩
index_config = {
    'type': 'IVF_PQ',
    'params': {
        'nlist': 1024,
        'm': 16,  # 压缩到1/4
        'nbits': 8
    }
}

# 3. 冷热分层
def move_cold_data():
    old_chunks = query("""
        SELECT * FROM chunks 
        WHERE last_access < '90 days ago'
        AND access_count < 10
    """)
    
    for chunk in old_chunks:
        move_to_glacier(chunk)
        update_storage_tier(chunk.id, 'glacier')
```

**成本预估模型：**

```python
def estimate_cost(vector_count, qps):
    """成本预估"""
    embedding_cost = qps * 30 * 0.0001  # Embedding API
    llm_cost = qps * 0.1 * 0.001  # LLM API
    milvus_cost = vector_count * 0.0001  # Milvus
    
    total = embedding_cost + llm_cost + milvus_cost
    return {
        'embedding': embedding_cost,
        'llm': llm_cost,
        'milvus': milvus_cost,
        'total': total
    }
```

---

### Q20: 如何设计RAG系统的弹性伸缩策略？

**题目类型**：系统设计类

**公司类型**：大型互联网

**问题描述**：RAG系统需要根据负载自动伸缩。请设计弹性伸缩策略。

**答案要点：**

**伸缩维度：**

| 维度 | 伸缩指标 | 范围 |
|------|----------|------|
| API服务 | CPU/请求队列 | 2-20实例 |
| Worker | 任务队列深度 | 3-30实例 |
| Milvus | 向量数量/QPS | 3-20节点 |
| Redis | 连接数/内存 | 3-9节点 |

**伸缩规则：**

```yaml
scaling_policies:
  api_service:
    type: "predictive"  # 预测伸缩
    metrics:
      - cpu_usage > 70%
      - request_queue > 100
    actions:
      scale_up: "+2"
      scale_down: "-1"
    cooldown: 5m
  
  worker_service:
    type: "reactive"  # 反应伸缩
    metrics:
      - queue_depth > 500
      - queue_depth < 50
    actions:
      scale_up: "+3"
      scale_down: "-2"
    cooldown: 3m
```

**K8s HPA配置：**

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: rag-api-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: rag-api
  minReplicas: 2
  maxReplicas: 20
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
```

---

## 第三部分：场景解决方案（共10题）

### Q21: 如何处理RAG系统中的过时信息问题？

**题目类型**：场景解决类

**公司类型**：咨询/新闻

**问题描述**：知识库中的信息可能过时，生成答案时可能引用过时内容。如何处理？

**答案要点：**

**解决方案：**

| 方法 | 说明 | 实现难度 |
|------|------|----------|
| 时间权重 | 新文档权重更高 | 低 |
| 版本标记 | 明确标注信息时效 | 中 |
| 自动过期 | 定期重新索引 | 中 |
| 用户确认 | 展示多个版本让用户选择 | 高 |

**实现代码：**

```python
def time_weighted_search(query, query_vector, time_decay=0.99):
    """时间加权检索"""
    # 1. 基础检索
    results = hybrid_search(query, query_vector)
    
    # 2. 计算时间权重
    now = datetime.now()
    for result in results:
        days_old = (now - result.create_time).days
        time_weight = time_decay ** days_old
        result.final_score = result.hybrid_score * time_weight
    
    # 3. 重新排序
    return sorted(results, key=lambda x: x.final_score, reverse=True)
```

**信息时效性标注：**

```python
def generate_answer_with_timeliness(query, results):
    """生成带时效性标注的答案"""
    # 检查结果时效性
    timeliness_notes = []
    
    for result in results:
        days_old = (datetime.now() - result.create_time).days
        
        if days_old > 365:
            timeliness_notes.append("【注意】此信息发布于1年前")
        elif days_old > 180:
            timeliness_notes.append("【注意】此信息发布于6个月前")
    
    # 生成答案
    answer = generate_with_context(query, results)
    
    # 添加时效性说明
    if timeliness_notes:
        answer += "\n\n" + "\n".join(set(timeliness_notes))
    
    return answer
```

---

### Q22: 如何处理RAG系统中的跨语言问答？

**题目类型**：场景解决类

**公司类型**：跨国企业

**问题描述**：用户用中文提问，但文档有中英文版本。如何实现跨语言问答？

**答案要点：**

**解决方案：**

```python
class CrossLingualRAG:
    def __init__(self):
        self.translator = Translator()
        self.embeddings = MultilingualEmbedding()
    
    async def ask(self, question: str, target_langs=['en']):
        # 1. 检测问题语言
        question_lang = detect_language(question)
        
        # 2. 跨语言检索
        all_results = []
        
        # 用原语言检索
        results = await self.search(question)
        all_results.extend(results)
        
        # 翻译后检索
        for lang in target_langs:
            translated = await self.translator.translate(question, lang)
            results = await self.search(translated)
            all_results.extend(results)
        
        # 3. 融合结果
        fused = self.fuse_results(all_results)
        
        # 4. 生成答案
        answer = await self.generate(question, fused)
        
        return answer
```

**翻译增强方案：**

```python
def translate_enhance(query, docs):
    """翻译增强"""
    # 翻译问题
    en_query = translate(query, 'en')
    
    # 翻译关键文档
    en_docs = []
    for doc in docs:
        if doc.lang != 'en':
            en_doc = translate(doc.content, 'en')
            en_docs.append(en_doc)
        else:
            en_docs.append(doc.content)
    
    # 用英文检索更多相关内容
    extra_results = await search(en_query, en_docs)
    
    return merge(docs, extra_results)
```

---

### Q23: 如何处理RAG系统中的长文档问答？

**题目类型**：场景解决类

**公司类型**：法律/金融

**问题描述**：用户问题涉及长文档（如合同、报告）中的多个部分。如何处理？

**答案要点：**

**解决思路：**

1. **文档结构理解**
```python
def understand_document_structure(doc):
    """理解文档结构"""
    sections = []
    
    for element in doc.elements:
        if element.type == 'heading':
            sections.append({
                'title': element.text,
                'level': element.level,
                'start_pos': element.position
            })
    
    return build_section_tree(sections)
```

2. **多段落检索**
```python
def retrieve_multiparts(query, doc, max_parts=5):
    """检索文档多个相关部分"""
    # 1. 找出相关章节
    related_sections = []
    for section in doc.sections:
        if query_match(query, section):
            related_sections.append(section)
    
    # 2. 按相关性排序
    sorted_sections = sorted(
        related_sections,
        key=lambda x: relevance_score(query, x)
    )
    
    # 3. 选择TopN
    return sorted_sections[:max_parts]
```

3. **上下文组装**
```python
def assemble_long_doc_context(sections):
    """组装长文档上下文"""
    context = "以下内容来自同一文档的不同部分：\n\n"
    
    for i, section in enumerate(sections):
        context += f"【第{i+1}部分 - {section.title}】\n"
        context += section.content + "\n\n"
    
    # 确保不超过Token限制
    if count_tokens(context) > MAX_CONTEXT_TOKENS:
        context = truncate_by_tokens(context, MAX_CONTEXT_TOKENS)
    
    return context
```

---

### Q24: 如何处理RAG系统中的模糊查询？

**题目类型**：场景解决类

**公司类型**：通用

**问题描述**：用户问题很模糊，如"告诉我关于RAG的事"。如何提供有用的回答？

**答案要点：**

**解决方案：**

```python
def handle_vague_query(query):
    """处理模糊查询"""
    # 1. 识别为模糊查询
    if is_vague(query):
        # 2. 返回引导
        return {
            'type': 'clarification',
            'message': '您的问题比较宽泛，请尝试以下方式：',
            'suggestions': [
                '如何部署RAG系统？',
                'RAG的检索流程是什么？',
                'RAG有哪些优化方法？'
            ]
        }
    
    # 3. 使用后退提示扩展
    step_back = generate_step_back(query)
    results = search(step_back)
    
    # 4. 返回概览
    return {
        'type': 'overview',
        'summary': generate_overview(results),
        'related_topics': extract_related_topics(results)
    }
```

**多意图识别：**

```python
def identify_intents(query):
    """识别可能的意图"""
    intents = []
    
    # 基于关键词识别
    if any(kw in query for kw in ['怎么', '如何', '怎样']):
        intents.append({
            'type': 'method',
            'question': f"如何{extract_topic(query)}？"
        })
    
    if any(kw in query for kw in ['是什么', '定义']):
        intents.append({
            'type': 'definition',
            'question': f"{extract_topic(query)}是什么？"
        })
    
    if any(kw in query for kw in ['为什么', '原因']):
        intents.append({
            'type': 'reason',
            'question': f"为什么{extract_topic(query)}？"
        })
    
    return intents
```

---

### Q25: 如何处理RAG系统中的矛盾信息？

**题目类型**：场景解决类

**公司类型**：咨询/专业服务

**问题描述**：不同文档对同一问题有不同说法，生成答案时如何处理？

**答案要点：**

**解决方案：**

```python
def handle_conflicting_info(query, results):
    """处理矛盾信息"""
    # 1. 检测矛盾
    conflicts = detect_conflicts(results)
    
    if conflicts:
        # 2. 按来源分组
        grouped = group_by_source(conflicts)
        
        # 3. 生成带标注的答案
        answer = "关于您的问题，不同来源给出了不同的说法：\n\n"
        
        for i, (source, content) in enumerate(grouped.items()):
            answer += f"**观点{i+1}（来源：{source}）**\n"
            answer += f"{content}\n\n"
        
        # 4. 添加分析
        answer += "**分析**：\n"
        answer += "这两个观点看起来矛盾，但实际上可能是由于：\n"
        answer += "1. 上下文或时间不同\n"
        answer += "2. 不同的应用场景\n"
        answer += "3. 不同的理解角度\n\n"
        
        answer += "建议您结合具体场景判断。"
        
        return answer
    
    return generate_normal_answer(query, results)
```

**冲突检测代码：**

```python
def detect_conflicts(results):
    """检测检索结果中的矛盾信息"""
    # 提取关键断言
    assertions = []
    for result in results:
        claims = extract_claims(result.content)
        assertions.extend(claims)
    
    # 检测矛盾
    conflicts = []
    for i, a in enumerate(assertions):
        for j, b in enumerate(assertions[i+1:], i+1):
            if are_contradicting(a, b):
                conflicts.append((a, b))
    
    return conflicts
```

---

### Q26: 如何处理RAG系统中的专业术语？

**题目类型**：场景解决类

**公司类型**：医疗/法律/金融

**问题描述**：用户问题包含专业术语，答案需要用通俗语言解释。如何处理？

**答案要点：**

**解决方案：**

```python
class LaymanExplainer:
    def __init__(self):
        self.glossary = load_glossary()
    
    def process_answer(self, answer, target_audience='general'):
        """处理专业术语"""
        processed = answer
        
        # 1. 识别专业术语
        terms = extract_technical_terms(answer)
        
        # 2. 替换为通俗解释
        for term in terms:
            if term in self.glossary:
                explanation = self.glossary[term]['layman']
                processed = processed.replace(
                    term,
                    f"{term}（{explanation}）"
                )
        
        # 3. 添加术语表
        if terms:
            processed += "\n\n**术语解释**：\n"
            for term in set(terms):
                if term in self.glossary:
                    processed += f"- **{term}**：{self.glossary[term]['layman']}\n"
        
        return processed
```

**术语表示例：**

```json
{
  "RAG": {
    "full_name": "Retrieval-Augmented Generation",
    "layman": "一种结合检索和生成的AI技术，让AI回答更准确",
    "level": "intermediate"
  },
  "Embedding": {
    "full_name": "词嵌入",
    "layman": "把文字转换成数字向量的技术，便于计算机比较文字的相似性",
    "level": "beginner"
  }
}
```

---

### Q27: 如何处理RAG系统中的敏感信息过滤？

**题目类型**：场景解决类

**公司类型**：金融/政务

**问题描述**：企业文档包含敏感信息，答案生成时如何过滤？

**答案要点：**

**解决方案：**

```python
class SensitiveInfoFilter:
    def __init__(self):
        self.patterns = {
            'phone': r'\d{11}',
            'id_card': r'\d{17}[\dXx]',
            'email': r'\w+@\w+\.\w+',
            'bank_account': r'\d{16,19}',
            'salary': r'\d{4,6}[元/月]?'
        }
        
        self.replacements = {
            'phone': '[手机号]',
            'id_card': '[身份证号]',
            'email': '[邮箱]',
            'bank_account': '[银行账号]',
            'salary': '[薪资信息]'
        }
    
    def filter(self, content: str) -> str:
        """过滤敏感信息"""
        filtered = content
        
        for pattern_name, pattern in self.patterns.items():
            filtered = re.sub(pattern, self.replacements[pattern_name], filtered)
        
        return filtered
```

**检索后处理：**

```python
def generate_with_filtering(query, retrieved_docs):
    """生成答案并过滤敏感信息"""
    # 1. 过滤检索结果中的敏感信息
    filtered_docs = []
    for doc in retrieved_docs:
        filtered_doc = {
            **doc,
            'content': sensitive_filter.filter(doc.content),
            'source': doc.source if not contains_sensitive(doc.source) else '[已脱敏]'
        }
        filtered_docs.append(filtered_doc)
    
    # 2. 生成答案
    answer = llm.generate(query, filtered_docs)
    
    # 3. 对答案再次过滤
    answer = sensitive_filter.filter(answer)
    
    return answer
```

---

### Q28: 如何处理RAG系统中的无答案情况？

**题目类型**：场景解决类

**公司类型**：通用

**问题描述**：用户问题在知识库中没有答案，系统如何友好地响应？

**答案要点：**

**解决方案：**

```python
def handle_no_answer(query, retrieval_results):
    """处理无答案情况"""
    # 1. 判断是否真的无答案
    if not retrieval_results:
        # 2. 分析原因
        reasons = analyze_no_answer(query)
        
        # 3. 提供替代方案
        response = "抱歉，知识库中暂时没有找到与您问题直接相关的内容。\n\n"
        
        if 'too_specific' in reasons:
            response += "**建议**：您的问题比较具体，可以尝试：\n"
            response += "- 扩大搜索范围\n"
            response += "- 使用更通用的关键词\n"
            response += f"- 相关话题：{suggest_related(query)}\n"
        
        elif 'out_of_scope' in reasons:
            response += "**说明**：您的问题可能超出了当前知识库的覆盖范围。\n"
            response += "- 这方面的内容可能还在整理中\n"
            response += "- 您可以联系客服获取帮助\n"
        
        elif 'terminology' in reasons:
            response += "**建议**：您使用的术语可能有多种含义。\n"
            response += f"- 您是指：{suggest_interpretations(query)}吗？\n"
        
        # 4. 提供其他帮助
        response += "\n**您可以尝试**：\n"
        response += "1. 换个方式提问\n"
        response += "2. 联系人工客服\n"
        response += "3. 提交您的问题，我们会尽快添加相关内容\n"
        
        return {
            'type': 'no_answer',
            'response': response,
            'suggestions': get_suggestions(query)
        }
```

**友好提示：**

```python
def friendly_no_answer_response(query):
    """友好的无答案响应"""
    # 基于Query特征提供建议
    suggestions = []
    
    # 如果Query太长，建议简化
    if len(query) > 50:
        suggestions.append("尝试用更简短的关键词搜索")
    
    # 如果包含缩写，建议展开
    abbreviations = extract_abbreviations(query)
    if abbreviations:
        suggestions.append(f"尝试展开缩写：{abbreviations}")
    
    return {
        'message': "我暂时没有找到相关内容，但这些建议可能有帮助：",
        'suggestions': suggestions,
        'alternatives': suggest_alternative_topics(query)
    }
```

---

### Q29: 如何设计RAG系统的人机协作流程？

**题目类型**：场景解决类

**公司类型**：客服/咨询

**问题描述**：当RAG无法给出满意答案时，如何无缝转人工处理？

**答案要点：**

**协作流程设计：**

```
┌─────────────────────────────────────────────────────────────────┐
│                      RAG回答                                      │
│                      ↓                                           │
│         ┌─────────────────────────┐                           │
│         │  答案置信度 ≥ 0.8?      │                           │
│         └─────────────────────────┘                           │
│              ↓ Yes              ↓ No                          │
│         返回RAG答案              进入人工流程                     │
│                              ↓                                 │
│         ┌─────────────────────────┐                           │
│         │  用户满意吗？           │                           │
│         └─────────────────────────┘                           │
│              ↓ No              ↓ Yes                         │
│         转人工客服              结束                          │
└─────────────────────────────────────────────────────────────────┘
```

**实现代码：**

```python
async def hybrid_qa_pipeline(query, user_id):
    """人机协作流程"""
    # 1. RAG尝试
    rag_result = await rag.ask(query)
    
    # 2. 检查置信度
    if rag_result.confidence >= CONFIDENCE_THRESHOLD:
        return {
            'answer': rag_result.answer,
            'source': 'rag',
            'confidence': rag_result.confidence,
            'feedback_requested': True
        }
    
    # 3. 置信度不足，尝试增强
    enhanced = await rag.enhance(query, rag_result)
    if enhanced.confidence >= CONFIDENCE_THRESHOLD:
        return enhanced
    
    # 4. 仍然不足，准备转人工
    human_handling = {
        'answer': rag_result.answer,
        'source': 'rag_fallback',
        'needs_human': True,
        'escalation_reason': enhanced.failure_reason,
        'context': {
            'query': query,
            'retrieved_docs': rag_result.documents,
            'conversation_history': get_history(user_id)
        }
    }
    
    # 5. 通知人工客服
    await notify_human_agent(human_handling)
    
    return human_handling
```

---

### Q30: 如何设计RAG系统的持续优化机制？

**题目类型**：场景解决类

**公司类型**：AI公司

**问题描述**：RAG系统上线后如何持续优化效果？请设计优化闭环。

**答案要点：**

**优化闭环架构：**

```
┌─────────────────────────────────────────────────────────────────┐
│                        数据闭环                                   │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐                   │
│  │ 用户反馈 │ → │ 分析问题 │ → │ 优化系统 │                   │
│  └─────────┘    └─────────┘    └─────────┘                   │
│       ↑                                           │             │
│       └───────────────────────┘                   │             │
│                       ↑                           │             │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐     │             │
│  │ 验证效果 │ ← │ AB测试   │ ← │ 离线优化 │ ────┘             │
│  └─────────┘    └─────────┘    └─────────┘                   │
└─────────────────────────────────────────────────────────────────┘
```

**反馈收集机制：**

```python
class FeedbackCollector:
    def record(self, user_id, query, answer, action, metadata):
        """收集用户反馈"""
        feedback = {
            'user_id': user_id,
            'query': query,
            'answer': answer,
            'action': action,  # click, bookmark, thumbs_up, thumbs_down
            'metadata': metadata,
            'timestamp': datetime.now()
        }
        
        # 存储反馈
        await self.store(feedback)
        
        # 触发分析
        if action == 'thumbs_down':
            await self.analyze_failure(query, answer)
    
    async def analyze_failure(self, query, answer):
        """分析失败原因"""
        # 1. 检查检索是否命中
        retrieved = await self.get_retrieved_docs(query)
        
        if not retrieved:
            self.log_issue('retrieval_miss', query)
        
        # 2. 检查答案质量
        issues = []
        if self.contains_hallucination(answer):
            issues.append('hallucination')
        if self.is_incomplete(answer):
            issues.append('incomplete')
        if self.is_irrelevant(answer, query):
            issues.append('irrelevant')
        
        if issues:
            self.log_issue('generation_failure', query, issues)
```

**持续优化策略：**

```python
class ContinuousOptimizer:
    def __init__(self):
        self.feedback_store = FeedbackStore()
    
    async def run_optimization_cycle(self):
        """执行优化周期"""
        # 1. 收集问题
        issues = self.feedback_store.get_high_impact_issues()
        
        for issue in issues:
            # 2. 分析根因
            root_cause = self.analyze_root_cause(issue)
            
            # 3. 生成优化方案
            solution = self.generate_solution(issue, root_cause)
            
            # 4. A/B测试
            if solution.ready_for_ab_test():
                experiment = self.create_experiment(solution)
                results = await self.run_ab_test(experiment)
                
                if results.significant_improvement():
                    self.deploy_solution(solution)
    
    async def run_ab_test(self, experiment):
        """运行A/B测试"""
        # 实现测试逻辑
        pass
```

---

## 附录：大厂RAG面试题总结

**面试重点考察点：**

| 类别 | 考察重点 |
|------|----------|
| 技术深度 | 检索原理、Embedding、切分策略 |
| 系统设计 | 架构设计、扩展性、高可用 |
| 场景解决 | 复杂场景的处理能力 |
| 优化经验 | 性能优化、效果优化 |
| 工程能力 | 代码实现、项目经验 |

**高频问题TOP10：**
1. RAG完整技术架构
2. 文档智能切分
3. 混合检索融合
4. 检索召回优化
5. Prompt工程设计
6. 效果评估体系
7. 缓存策略设计
8. 权限控制方案
9. 版本管理设计
10. 故障排查能力

---

*本文档共计30道面试题，涵盖大厂RAG面试的各个方面。*
