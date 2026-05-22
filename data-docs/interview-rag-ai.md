# RAG 与 AI 技术面试题

## 目录

1. [RAG 检索增强生成](#1-rag-检索增强生成)
2. [向量数据库](#2-向量数据库)
3. [Embedding 向量化](#3-embedding-向量化)
4. [文本切分策略](#4-文本切分策略)
5. [Reranker 重排序](#5-reranker-重排序)
6. [LLM 大语言模型](#6-llm-大语言模型)
7. [混合检索与融合](#7-混合检索与融合)
8. [MMR 最大边际相关性](#8-mmr-最大边际相关性)

---

## 1. RAG 检索增强生成

### 问题 1：什么是 RAG？它解决什么问题？

**答案：**

**RAG 的定义：**

RAG（Retrieval-Augmented Generation，检索增强生成）是一种结合了信息检索和大语言模型的技术架构。它通过从外部知识库中检索相关文档，来增强 LLM 的回答能力。

**解决的问题：**

| 问题 | 传统 LLM | RAG |
|------|----------|-----|
| 知识时效性 | 训练数据截止日期之前的知识 | 可实时接入最新知识库 |
| 幻觉问题 | 可能生成不准确信息 | 基于检索到的真实文档生成 |
| 领域知识 | 缺乏垂直领域知识 | 可接入任何领域的文档 |
| 可解释性 | 答案来源不明确 | 可以引用具体文档来源 |
| 信息安全 | 无法控制敏感信息 | 可控的知识库访问 |

**RAG 工作流程：**

```
用户提问
    │
    ▼
┌────────────────────────────────────────────────────┐
│ 1. 检索阶段（Retrieval）                           │
│    - 用户问题向量化                                 │
│    - 在向量数据库中检索相似文档                     │
└────────────────────────────────────────────────────┘
    │
    ▼
┌────────────────────────────────────────────────────┐
│ 2. 增强阶段（Augmentation）                        │
│    - 将检索到的文档作为上下文                       │
│    - 构建 Prompt                                 │
└────────────────────────────────────────────────────┘
    │
    ▼
┌────────────────────────────────────────────────────┐
│ 3. 生成阶段（Generation）                           │
│    - LLM 基于上下文生成回答                         │
│    - 引用来源文档                                  │
└────────────────────────────────────────────────────┘
    │
    ▼
返回带来源的准确回答
```

**项目中应用：**

```python
# qa_service.py
async def ask(self, question: str, db: Session) -> Dict[str, Any]:
    # 1. 问题向量化
    query_embedding = self.embedding_service.encode_single(question)
    
    # 2. 向量检索
    search_results = self.vector_store.search_vectors(query_embedding)
    retrieved_chunks = self._parse_search_results(search_results)
    
    # 3. Rerank 重排序
    rerank_result = self.reranker.rerank(question, retrieved_chunks)
    final_chunks = [c.to_dict() for c in rerank_result.candidates]
    
    # 4. LLM 生成
    context_texts = [chunk["content"] for chunk in final_chunks]
    answer = self.llm.generate_with_context(
        question=question,
        context=context_texts
    )
    
    return {"answer": answer, "sources": final_chunks}
```

---

### 问题 2：RAG 系统中有哪些关键组件？

**答案：**

**RAG 系统组件架构：**

```
┌─────────────────────────────────────────────────────────────────┐
│                         RAG 系统架构                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    │
│  │  文档处理    │───▶│   向量化     │───▶│  向量存储    │    │
│  │  (Ingestion) │    │(Embedding)  │    │(VectorStore) │    │
│  └──────────────┘    └──────────────┘    └──────────────┘    │
│                                                │               │
│                                                ▼               │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    │
│  │   答案生成   │◀───│   上下文    │◀───│    检索     │    │
│  │ (Generation) │    │(Augment)    │    │ (Retrieval)  │    │
│  └──────────────┘    └──────────────┘    └──────────────┘    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**组件详解：**

**1. 文档处理（Document Processing）**

```python
# 文档处理流程
class DocumentProcessor:
    def process(self, file_path: str):
        # 1. 文件解析
        content = self.parser.parse(file_path)
        
        # 2. 文本切分
        chunks = self.chunker.split(content)
        
        # 3. 元数据提取
        metadata = {
            "filename": os.path.basename(file_path),
            "source": "user_upload",
            "created_at": datetime.now()
        }
        
        return chunks, metadata
```

**2. 向量化（Embedding）**

```python
# 向量化服务
class EmbeddingService:
    def encode(self, texts: List[str]) -> List[List[float]]:
        # 调用 embedding 模型
        embeddings = self.model.encode(texts)
        
        # L2 归一化
        embeddings = self.normalize(embeddings)
        
        return embeddings
```

**3. 向量存储（Vector Store）**

```python
# 向量数据库操作
class VectorStore:
    def add_vectors(self, chunks, embeddings):
        # 存储到 Milvus
        self.collection.insert(
            documents=chunks,
            embeddings=embeddings
        )
    
    def search(self, query_embedding, top_k=5):
        # ANN 近似最近邻检索
        results = self.collection.search(
            data=[query_embedding],
            anns_field="embedding",
            param={"metric_type": "IP"},
            limit=top_k
        )
        return results
```

**4. 检索（Retrieval）**

```python
# 检索策略
class RetrievalService:
    def retrieve(self, query: str, top_k=5):
        # 向量化查询
        query_emb = self.embedding.encode(query)
        
        # 向量检索
        results = self.vector_store.search(query_emb, top_k)
        
        # 可选：Rerank 重排序
        results = self.reranker.rerank(query, results)
        
        return results
```

**5. 上下文增强（Augmentation）**

```python
# 构建增强上下文
def build_context(query: str, retrieved_docs: List[str]) -> str:
    context = "根据以下参考文档回答问题：\n\n"
    
    for i, doc in enumerate(retrieved_docs):
        context += f"[文档 {i+1}]:\n{doc}\n\n"
    
    context += f"用户问题：{query}\n"
    context += "请根据参考文档回答问题。"
    
    return context
```

**6. 生成（Generation）**

```python
# LLM 生成
class LLMService:
    def generate(self, context: str) -> str:
        response = self.client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": context}
            ],
            temperature=0.3,
            stream=False
        )
        
        return response.choices[0].message.content
```

---

## 2. 向量数据库

### 问题 3：Milvus 向量数据库是如何工作的？

**答案：**

**Milvus 简介：**

Milvus 是一个开源的向量数据库，专为海量向量检索设计，支持十亿级别的向量规模。

**核心概念：**

| 概念 | 说明 |
|------|------|
| Collection | 类似 MySQL 的表，存储向量和元数据 |
| Partition | Collection 的分区，提高查询效率 |
| Field | 字段，向量字段和标量字段 |
| Index | 索引，加速向量检索 |
| Shard | 分片，水平扩展 |

**Collection Schema 设计：**

```python
# 创建 Collection
from pymilvus import FieldSchema, CollectionSchema, DataType

fields = [
    # 主键字段
    FieldSchema(name="id", dtype=DataType.VARCHAR, max_length=256, is_primary=True),
    
    # 文档元数据
    FieldSchema(name="document_id", dtype=DataType.INT64),
    FieldSchema(name="chunk_index", dtype=DataType.INT64),
    FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=65535),
    FieldSchema(name="filename", dtype=DataType.VARCHAR, max_length=512),
    
    # AI 生成相关
    FieldSchema(name="source_type", dtype=DataType.VARCHAR, max_length=20),
    
    # 向量字段
    FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=2560)
]

schema = CollectionSchema(
    fields=fields,
    description="知识库向量集合"
)
```

**索引类型：**

```python
# IVF_FLAT 索引（倒排索引 + 暴力搜索）
index_params = {
    "metric_type": "IP",      # 内积，适合归一化向量
    "index_type": "IVF_FLAT",
    "params": {"nlist": 1024}  # 聚类中心数量
}

# HNSW 索引（分层导航小世界图）
index_params = {
    "metric_type": "IP",
    "index_type": "HNSW",
    "params": {"M": 16, "efConstruction": 200}
}

# 创建索引
collection.create_index(
    field_name="embedding",
    index_params=index_params
)
```

**向量检索：**

```python
# 搜索参数
search_params = {
    "metric_type": "IP",      # 内积
    "params": {"nprobe": 16}  # 查询时探查的聚类数
}

# 执行检索
results = collection.search(
    data=[query_embedding],      # 查询向量
    anns_field="embedding",      # 向量字段
    param=search_params,         # 搜索参数
    limit=10,                   # 返回数量
    expr="source_type == 'local'",  # 过滤条件
    output_fields=["content", "filename"]  # 返回字段
)

# 处理结果
for hit in results[0]:
    print(f"ID: {hit.id}")
    print(f"Distance: {hit.distance}")
    print(f"Content: {hit.entity.content}")
```

**度量类型：**

| 类型 | 说明 | 适用场景 |
|------|------|----------|
| L2 | 欧氏距离 | 图像、通用 |
| IP | 内积 | 归一化向量 |
| COSINE | 余弦相似度 | 文本相似度 |

---

### 问题 4：向量索引算法有哪些？各自优缺点是什么？

**答案：**

**1. IVF（倒排索引）系列**

**IVF_FLAT：**

```python
# IVF_FLAT 原理
"""
1. 训练阶段：对所有向量进行 K-Means 聚类，得到 nlist 个聚类中心
2. 查询阶段：
   - 先找到最近的 N 个聚类中心
   - 在这些聚类中暴力搜索

优点：查询速度快，可控精度
缺点：需要训练，内存占用较高
"""

index_params = {
    "index_type": "IVF_FLAT",
    "params": {"nlist": 1024}  # 聚类数
}
```

**IVF_SQ8 / IVF_PQ：**

```python
# IVF_PQ：将向量压缩后存储
"""
1. PQ (Product Quantization)：将高维向量分段，每段独立聚类
2. 存储压缩后的中心 ID，而不是原始向量

优点：大幅降低内存占用
缺点：精度有所下降
"""

index_params = {
    "index_type": "IVF_PQ",
    "params": {"nlist": 1024, "m": 16, "nbits": 8}
}
```

**2. HNSW（分层导航小世界图）**

```python
# HNSW 原理
"""
1. 构建多层图，上层稀疏、下层稠密
2. 查询时从上层开始，快速定位大致区域
3. 下沉到最底层精确搜索

优点：查询速度极快，精度高
缺点：内存占用大，构建时间长
"""

index_params = {
    "index_type": "HNSW",
    "params": {
        "M": 16,              # 连接数
        "efConstruction": 200   # 构建时搜索范围
    }
}
```

**3. 对比总结：**

| 索引 | 查询速度 | 精度 | 内存占用 | 构建时间 | 适用场景 |
|------|----------|------|----------|----------|----------|
| FLAT | 慢 | 100% | 高 | 快 | 小规模数据 |
| IVF_FLAT | 中 | 可调 | 中 | 中 | 中等规模 |
| IVF_PQ | 快 | 90-95% | 低 | 中 | 大规模数据 |
| HNSW | 极快 | 95-99% | 高 | 慢 | 高性能场景 |

**项目中应用：**

```python
# vectorstore.py
index_params = {
    "metric_type": settings.milvus_metric_type,  # IP
    "index_type": settings.milvus_index_type,   # IVF_FLAT
    "params": {"nlist": settings.milvus_nlist}  # 1024
}
```

---

## 3. Embedding 向量化

### 问题 5：什么是 Embedding？为什么需要向量表示？

**答案：**

**Embedding 的定义：**

Embedding（嵌入）是将文本、图像等高维离散数据转换为低维连续向量的技术。语义相似的内容在向量空间中距离相近。

**为什么需要 Embedding：**

| 传统方法 | 问题 | Embedding 方案 |
|----------|------|----------------|
| 关键词匹配 | 无法理解语义 | 语义相似 → 向量相近 |
| TF-IDF | 维度高、稀疏 | 降维、密集表示 |
| 字符串相似度 | O(n²) 复杂度 | O(1) 检索复杂度 |

**Embedding 原理：**

```
文本："什么是 RAG"
    │
    ▼ Tokenize
["什", "么", "是", "RAG"]
    │
    ▼ Embedding Model
[0.123, -0.456, 0.789, ..., 0.234]  ← 2560 维向量
```

**常用 Embedding 模型：**

```python
# Ollama 调用示例
import httpx

response = httpx.post(
    "http://localhost:11434/api/embeddings",
    json={
        "model": "batiai/qwen3-embedding:4b-q6",
        "prompt": "什么是检索增强生成"
    }
)

embedding = response.json()["embedding"]  # 2560 维向量

# L2 归一化
import numpy as np
embedding = np.array(embedding)
embedding = embedding / np.linalg.norm(embedding)
```

**向量相似度计算：**

```python
import numpy as np

def cosine_similarity(a: List[float], b: List[float]) -> float:
    """余弦相似度"""
    a = np.array(a)
    b = np.array(b)
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def inner_product(a: List[float], b: List[float]) -> float:
    """内积（适用于归一化向量）"""
    a = np.array(a)
    b = np.array(b)
    return np.dot(a, b)
```

---

### 问题 6：Embedding 模型是如何训练的？

**答案：**

**训练目标：**

Embedding 模型的核心目标是让语义相似的文本在向量空间中距离相近。

**常用训练方法：**

**1. 对比学习（Contrastive Learning）：**

```python
"""
对比学习核心思想：
- 正样本对：语义相似的文本，距离近
- 负样本对：语义不同的文本，距离远

损失函数：Triplet Loss 或 InfoNCE
"""

# Triplet Loss
class TripletLoss(nn.Module):
    def forward(self, anchor, positive, negative):
        pos_dist = F.pairwise_distance(anchor, positive)
        neg_dist = F.pairwise_distance(anchor, negative)
        
        # 正样本距离小于负样本距离 + margin
        loss = F.relu(pos_dist - neg_dist + 0.2)
        return loss.mean()
```

**2. MNR（Mean Random Negative）：**

```python
"""
对于每个 query，正样本是匹配的 doc
随机采样负样本（同一 batch 中的其他 doc）

训练目标：query 与正样本的相似度 > query 与负样本的相似度
"""

def compute_loss(query_emb, pos_emb, neg_emb):
    pos_score = (query_emb * pos_emb).sum(dim=1)
    neg_score = (query_emb * neg_emb).sum(dim=1)
    
    loss = F.cross_entropy(
        torch.stack([pos_score, neg_score], dim=1),
        torch.zeros(len(query_emb)).long()
    )
    return loss
```

**预训练 + 微调范式：**

```python
"""
1. 预训练阶段：
   - 使用大规模无标注语料
   - 学习通用语义表示

2. 微调阶段：
   - 使用标注的 query-doc 对数据
   - 针对检索任务优化
"""

# 微调配置示例
finetune_config = {
    "batch_size": 32,
    "learning_rate": 2e-5,
    "epochs": 3,
    "warmup_steps": 100,
    "loss": "contrastive"  # 对比损失
}
```

---

## 4. 文本切分策略

### 问题 7：为什么文本切分很重要？有哪些切分策略？

**答案：**

**文本切分的重要性：**

1. **控制上下文长度**：LLM 有 token 限制，需要将长文档切分
2. **提高检索精度**：小块更容易精确匹配用户问题
3. **保留语义完整性**：避免在句子中间截断

**常见切分策略：**

**1. 固定长度切分（不推荐）：**

```python
def fixed_split(text: str, chunk_size: int = 500, overlap: int = 50):
    """简单但可能破坏语义"""
    chunks = []
    start = 0
    while start < len(text):
        chunks.append(text[start:start + chunk_size])
        start += chunk_size - overlap
    return chunks
```

**2. 递归字符切分：**

```python
def recursive_split(text: str, separators=["\n\n", "\n", "。", " ", ""]):
    """按分隔符层级递归切分"""
    if not text:
        return []
    
    for sep in separators:
        if sep in text:
            chunks = text.split(sep)
            return [s.strip() for s in chunks if s.strip()]
    
    return [text.strip()] if text.strip() else []
```

**3. 语义切分（项目使用）：**

```python
# semantic_chunker.py
class SemanticChunker:
    """基于文档结构的语义切分"""
    
    def split_text(self, text: str, document_id: int = 0):
        # 1. 解析文档结构
        sections = self._parse_document_structure(text)
        
        # 2. 按语义合并
        chunks = self._generate_chunks(sections)
        
        # 3. Token 约束检查
        chunks = self._enforce_token_limit(chunks)
        
        return chunks
```

**4. 语义切分流程：**

```python
# 解析 Markdown 结构
def _parse_document_structure(self, text: str):
    sections = []
    current_section = Section("root", "", 0)
    
    for line in text.split('\n'):
        # 检测标题
        if line.startswith('#'):
            level = len(line) - len(line.lstrip('#'))
            title = line.lstrip('#').strip()
            # 创建新章节
            sections.append(current_section)
            current_section = Section(...)
        
        # 检测代码块、列表、表格等
        # ...
    
    return sections

# Token 约束合并
def _merge_paragraphs(self, paragraphs, target_tokens=600, max_tokens=900):
    current = []
    current_tokens = 0
    
    for para in paragraphs:
        para_tokens = self._estimate_tokens(para)
        
        if current_tokens + para_tokens > max_tokens:
            yield '\n\n'.join(current)
            current = [para]
            current_tokens = para_tokens
        else:
            current.append(para)
            current_tokens += para_tokens
```

**Token 估算：**

```python
def estimate_tokens(self, text: str) -> int:
    """
    估算 token 数量
    中文：1 token ≈ 1 字符
    英文：1 token ≈ 4 字符
    """
    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
    other_chars = len(text) - chinese_chars
    return int(chinese_chars + other_chars * 0.25)
```

---

### 问题 8：什么是 Parent-Child Retrieval？

**答案：**

**Parent-Child Retrieval 概念：**

Parent-Child Retrieval 是一种分层检索策略，通过维护父子块之间的关系来平衡检索精度和上下文完整性。

**工作原理：**

```
┌─────────────────────────────────────────────────────────────┐
│                       原始文档                              │
│ "MySQL 索引是数据库性能优化的关键技术..."                    │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼ 切分
┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐
│  Child Chunk 1  │   │  Child Chunk 2  │   │  Child Chunk 3  │
│ "MySQL 索引..." │   │ "索引类型..."   │   │ "B+ Tree..."   │
│ (512 tokens)   │   │ (512 tokens)   │   │ (512 tokens)   │
└─────────────────┘   └─────────────────┘   └─────────────────┘
         │                     │                     │
         └─────────────────────┼─────────────────────┘
                               ▼
                    ┌─────────────────────┐
                    │   Parent Chunk       │
                    │ "MySQL 索引是数据库..." │
                    │ (整个段落，1500 tokens)│
                    └─────────────────────┘
```

**检索流程：**

```python
class ParentChildRetriever:
    def retrieve(self, query: str, top_k=5):
        # 1. 检索 Child Chunks（用于精确匹配）
        child_results = self.vector_store.search(
            query_embedding=embed(query),
            collection="child_chunks",
            top_k=top_k * 3  # 多召回一些
        )
        
        # 2. 获取 Parent Chunk IDs
        parent_ids = set()
        for result in child_results:
            parent_ids.add(result.parent_id)
        
        # 3. 检索 Parent Chunks（用于 LLM 上下文）
        parent_results = self.get_by_ids(parent_ids)
        
        # 4. 返回给 LLM
        return parent_results
```

**优势：**

| 特性 | Child Only | Parent-Child |
|------|------------|--------------|
| 检索精度 | 高 | 中 |
| 上下文完整性 | 低 | 高 |
| LLM 回答质量 | 较差 | 好 |
| 适用场景 | 简单问答 | 复杂理解 |

---

## 5. Reranker 重排序

### 问题 9：什么是 Cross-Encoder Reranker？与 Bi-Encoder 有什么区别？

**答案：**

**Bi-Encoder（双编码器）：**

```python
"""
Bi-Encoder 工作原理：
1. Query 和 Document 分别编码为向量
2. 在向量空间中计算相似度

优点：编码一次，可重复使用
缺点：无法建模 Query-Document 的交互关系
"""

query_embedding = bi_encoder.encode(query)
doc_embedding = bi_encoder.encode(document)

similarity = cosine_similarity(query_embedding, doc_embedding)
```

**Cross-Encoder（交叉编码器）：**

```python
"""
Cross-Encoder 工作原理：
1. 将 Query 和 Document 拼接
2. 一起通过 Transformer
3. 直接输出相似度分数

优点：建模 Query-Document 交互，精度高
缺点：每次查询都需要重新编码
"""

# Query-Document 拼接
input_text = f"{query} [SEP] {document}"

# 一起编码
score = cross_encoder.predict(input_text)  # 直接输出 0-1 的分数
```

**对比：**

| 特性 | Bi-Encoder | Cross-Encoder |
|------|------------|----------------|
| 编码方式 | Query 和 Doc 分别编码 | 拼接后一起编码 |
| 计算速度 | 快（向量检索） | 慢（需要逐个计算） |
| 精度 | 中等 | 高 |
| 适用场景 | 粗召回 | 精排序 |
| 典型模型 | Sentence-BERT | BERT、Qwen-Reranker |

**项目中的 Reranker：**

```python
# reranker_service.py
class RerankerService:
    def rerank(self, query: str, candidates: List[Dict]):
        """使用 Cross-Encoder 重排序"""
        
        # 1. 准备输入
        query_doc_pairs = [
            {"query": query, "document": c["content"]}
            for c in candidates
        ]
        
        # 2. 调用 Ollama Rerank API
        reranked_scores = self._call_rerank_api(query, documents)
        
        # 3. 按分数排序
        scored_candidates = list(zip(candidates, reranked_scores))
        scored_candidates.sort(key=lambda x: x[1], reverse=True)
        
        # 4. 返回 Top-K
        return scored_candidates[:self.top_k]
```

**为什么需要 Reranker：**

```
用户问题: "MySQL 索引失效的场景有哪些？"

Bi-Encoder 检索结果（按向量相似度）:
1. "MySQL 索引原理详解" (0.85)
2. "MySQL 索引分类" (0.82)
3. "索引失效的 10 种情况" (0.78)  ← 最相关！
4. "数据库性能优化" (0.75)

Cross-Encoder 重排后:
1. "索引失效的 10 种情况" (0.95)  ← 精确命中
2. "MySQL 索引原理详解" (0.88)
3. "MySQL 索引分类" (0.85)
4. "数据库性能优化" (0.72)
```

---

## 6. LLM 大语言模型

### 问题 10：LLM 的温度（Temperature）参数如何影响生成结果？

**答案：**

**Temperature 定义：**

Temperature 控制生成文本的随机性。值越低，输出越确定；值越高，输出越随机。

**数学原理：**

```python
import numpy as np

def softmax_with_temperature(logits: List[float], temperature: float) -> List[float]:
    """
    Temperature 影响 softmax 的平滑程度
    
    T → 0: 概率分布趋向 one-hot（最确定的输出）
    T = 1: 标准 softmax
    T → ∞: 概率分布趋向均匀（完全随机）
    """
    # 除以 temperature
    scaled_logits = [l / temperature for l in logits]
    
    # softmax
    exp_logits = [np.exp(l) for l in scaled_logits]
    sum_exp = sum(exp_logits)
    
    return [e / sum_exp for e in exp_logits]

# 示例
logits = [2.0, 1.0, 0.5]  # 原始 logits

print("T=0.1:", softmax_with_temperature(logits, 0.1))  # [0.99, 0.01, 0.00]
print("T=1.0:", softmax_with_temperature(logits, 1.0))  # [0.66, 0.24, 0.10]
print("T=2.0:", softmax_with_temperature(logits, 2.0))  # [0.42, 0.33, 0.25]
```

**不同场景的建议值：**

| Temperature | 特点 | 适用场景 |
|------------|------|----------|
| 0.0 - 0.3 | 确定性强，一致性好 | 问答、代码生成 |
| 0.3 - 0.7 | 平衡随机性 | 通用对话 |
| 0.7 - 1.0 | 创造性强 | 创意写作 |
| > 1.0 | 完全随机 | 不推荐 |

**项目中应用：**

```python
# llm.py
class LLMClient:
    def generate(self, prompt: str, temperature: float = 0.3):
        """
        RAG 场景建议 temperature = 0.3
        - 保证答案准确性
        - 减少幻觉
        - 保持一定的多样性
        """
        response = self.client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            temperature=temperature,
            max_tokens=2000
        )
        return response.choices[0].message.content
```

---

## 7. 混合检索与融合

### 问题 11：什么是 BM25？它和向量检索有什么区别？

**答案：**

**BM25 算法原理：**

BM25（Best Matching 25）是一种经典的文本检索算法，基于词袋模型和概率统计。

```python
def bm25_score(document: str, query: str, avgdl: float, 
                k1: float = 1.5, b: float = 0.75) -> float:
    """
    BM25 公式：
    score = Σ IDF(qi) * (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * |d|/avgdl))
    
    其中：
    - tf: 词项在文档中的频率
    - IDF: 逆文档频率
    - |d|: 文档长度
    - avgdl: 平均文档长度
    """
    from collections import Counter
    
    # 分词
    doc_terms = document.lower().split()
    query_terms = query.lower().split()
    
    # 计算 TF
    doc_tf = Counter(doc_terms)
    
    # 计算 IDF（简化版）
    idf = {term: 1.0 for term in query_terms}  # 实际应计算文档频率
    
    # 计算 BM25
    score = 0.0
    dl = len(doc_terms)
    
    for term in query_terms:
        tf = doc_tf.get(term, 0)
        if tf > 0:
            # BM25 公式
            numerator = tf * (k1 + 1)
            denominator = tf + k1 * (1 - b + b * dl / avgdl)
            score += idf[term] * numerator / (denominator + 1e-10)
    
    return score
```

**BM25 vs 向量检索：**

| 特性 | BM25 | 向量检索 |
|------|------|----------|
| 原理 | 词频统计 | 语义表示 |
| 语义理解 | 差 | 好 |
| 同义词处理 | 差 | 好 |
| 计算复杂度 | 低 | 中 |
| 可解释性 | 高 | 中 |
| 适用场景 | 关键词精确匹配 | 语义相似检索 |

**互补性：**

```python
# 混合检索示例
def hybrid_search(query: str, top_k: int = 10):
    # 1. 语义检索（Bi-Encoder）
    semantic_results = vector_store.search(embed(query), top_k=50)
    
    # 2. 关键词检索（BM25）
    bm25_results = bm25_search(query, top_k=50)
    
    # 3. RRF 融合
    fused_results = rrf_fusion(
        [semantic_results, bm25_results],
        k=60  # RRF 参数
    )
    
    return fused_results[:top_k]

# RRF (Reciprocal Rank Fusion)
def rrf_fusion(results_list: List[List], k: int = 60) -> List:
    """
    RRF = Σ 1 / (k + rank)
    
    优点：
    - 简单有效
    - 不需要训练
    - 可以融合任意数量的排序结果
    """
    from collections import defaultdict
    
    rrf_scores = defaultdict(float)
    
    for results in results_list:
        for rank, (doc_id, score) in enumerate(results):
            rrf_scores[doc_id] += 1.0 / (k + rank + 1)
    
    # 按 RRF 分数排序
    sorted_docs = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
    
    return sorted_docs
```

---

### 问题 12：什么是 RRF 融合？为什么要使用它？

**答案：**

**RRF 定义：**

RRF（Reciprocal Rank Fusion，倒数排名融合）是一种简单而有效的多排序结果融合算法。

**RRF 公式：**

```
RRF_score(doc) = Σ 1 / (k + rank(doc))

其中：
- k: RRF 参数（通常设为 60）
- rank(doc): 文档在某个排序结果中的排名
- Σ: 对所有排序结果求和
```

**示例：**

```python
# 假设有两个检索结果

# 语义检索结果（按相关性排序）
semantic_ranking = ["doc_A", "doc_B", "doc_C", "doc_D", "doc_E"]

# BM25 检索结果（按词频排序）
bm25_ranking = ["doc_C", "doc_A", "doc_D", "doc_E", "doc_B"]

# RRF 融合
k = 60
rrf_scores = {}

for rank, doc in enumerate(semantic_ranking):
    rrf_scores[doc] = rrf_scores.get(doc, 0) + 1 / (k + rank + 1)

for rank, doc in enumerate(bm25_ranking):
    rrf_scores[doc] = rrf_scores.get(doc, 0) + 1 / (k + rank + 1)

# 计算结果
# doc_A: 1/61 + 1/62 = 0.0326
# doc_B: 1/62 + 1/65 = 0.0319
# doc_C: 1/63 + 1/61 = 0.0323
# doc_D: 1/64 + 1/64 = 0.0312
# doc_E: 1/65 + 1/63 = 0.0315

# 最终排序: A > C > B > E > D
```

**RRF 的优势：**

| 特性 | 说明 |
|------|------|
| 简单 | 无需训练 |
| 鲁棒 | 对单个排序的错误不敏感 |
| 可扩展 | 可融合任意数量的排序结果 |
| 无参数 | k=60 通常效果不错 |

**项目中应用：**

```python
# sparse_service.py
@staticmethod
def rrf_fusion(results_list: List[List[Tuple[Any, float]]], k: int = 60) -> List[Tuple[Any, float]]:
    if not results_list:
        return []
    
    if len(results_list) == 1:
        return results_list[0]
    
    rrf_scores: Dict[Any, Dict[str, float]] = {}
    
    for results in results_list:
        for rank, (item, original_score) in enumerate(results):
            if item not in rrf_scores:
                rrf_scores[item] = {"rrf": 0.0, "original": original_score}
            rrf_scores[item]["rrf"] += 1.0 / (k + rank + 1)
    
    # 排序
    sorted_items = sorted(
        rrf_scores.items(),
        key=lambda x: x[1]["rrf"],
        reverse=True
    )
    
    return [(item, data["rrf"]) for item, data in sorted_items]
```

---

## 8. MMR 最大边际相关性

### 问题 13：什么是 MMR？它在 RAG 中起什么作用？

**答案：**

**MMR 定义：**

MMR（Maximal Marginal Relevance，最大边际相关性）是一种多样化排序算法，在保证相关性的同时增加结果的多样性。

**MMR 公式：**

```
MMR = argmax( λ × Relevance - (1-λ) × Max_Diversity )

其中：
- Relevance: 与查询的相关性（向量相似度）
- Max_Diversity: 与已选文档的最大相似度
- λ: 平衡参数（0-1 之间）
```

**MMR 工作原理：**

```python
def mmr_rerank(query_embedding: np.ndarray, 
                candidates: List[Dict], 
                lambda_mult: float = 0.7,
                fetch_k: int = 20,
                top_k: int = 5) -> List[Dict]:
    """
    MMR 重排序
    在相关性和多样性之间取得平衡
    """
    selected = []
    candidates = candidates[:fetch_k]  # 取前 fetch_k 个候选
    
    while len(selected) < top_k:
        best_score = -float('inf')
        best_doc = None
        best_idx = -1
        
        for i, doc in enumerate(candidates):
            if doc in selected:
                continue
            
            # 相关性分数
            relevance = doc['score']
            
            # 多样性分数（与已选文档的最大相似度）
            diversity = 0.0
            if selected:
                doc_emb = np.array(doc['embedding'])
                for sel_doc in selected:
                    sel_emb = np.array(sel_doc['embedding'])
                    sim = np.dot(doc_emb, sel_emb) / (
                        np.linalg.norm(doc_emb) * np.linalg.norm(sel_emb) + 1e-9
                    )
                    diversity = max(diversity, sim)
            
            # MMR 分数
            mmr_score = lambda_mult * relevance - (1 - lambda_mult) * diversity
            
            if mmr_score > best_score:
                best_score = mmr_score
                best_doc = doc
                best_idx = i
        
        if best_doc:
            selected.append(best_doc)
            candidates.pop(best_idx)
        else:
            break
    
    return selected
```

**MMR 效果示例：**

```
用户问题: "MySQL 索引优化"

Top-5 向量检索结果（按相似度）:
1. "MySQL 索引失效场景" (0.92) - 索引失效
2. "MySQL 索引失效原因" (0.91) - 索引失效
3. "MySQL 索引失效条件" (0.90) - 索引失效
4. "MySQL 索引分类" (0.88) - 索引分类
5. "MySQL 索引原理" (0.87) - 索引原理

问题：结果 1-3 高度重复，都在讲"索引失效"

应用 MMR（λ=0.7）后:
1. "MySQL 索引失效场景" (0.92) - 相关性高，添加到结果
2. "MySQL 索引分类" (0.88) - 与结果1相似度低，添加到结果
3. "MySQL 索引原理" (0.87) - 与结果1相似度低，添加到结果
4. "MySQL 索引优化技巧" (0.85) - 新主题，添加到结果
5. "MySQL 索引失效原因" (0.91) - 被过滤（与结果1相似度太高）

优点：结果覆盖多个主题，信息更全面
```

**项目中应用：**

```python
# vectorstore.py
def search_vectors(self, query_embedding, n_results):
    # ... 执行向量检索 ...
    
    # 应用 MMR
    if enable_mmr and n_results > 1:
        raw_limit = min(n_results * 3, 100)
        results = self.collection.search(...)
        
        # MMR 重排序
        reranked = self._mmr_rerank(results)
        
        return reranked[:n_results]
```

---

## 版本信息

- 文档版本: 1.0.0
- 更新日期: 2026-05-18
