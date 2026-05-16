# Milvus 向量数据库面试题集

> 本文档包含 30 道 Milvus 向量数据库相关的高频面试题，涵盖向量检索原理、索引机制、ANN 算法、集合操作等核心概念。所有答案均为中文，代码附有详细中文解释。

---

## 目录

1. [向量数据库基础](#1-向量数据库基础)
2. [Milvus 核心概念](#2-milvus-核心概念)
3. [索引与算法](#3-索引与算法)
4. [集合与分区](#4-集合与分区)
5. [搜索与查询](#5-搜索与查询)
6. [数据管理](#6-数据管理)
7. [性能优化](#7-性能优化)
8. [部署与运维](#8-部署与运维)

---

## 1. 向量数据库基础

### Q1: 什么是向量数据库？它与传统数据库有什么区别？

**参考答案：**

**向量数据库定义：**
向量数据库是一种专门用于存储和检索高维向量（Embedding）的数据库，能够在大规模数据中快速找到与查询向量最相似的项。

**核心区别对比：**

| 特性 | 向量数据库 | 传统关系型数据库 |
|------|-----------|-----------------|
| **存储内容** | 高维浮点数向量 | 结构化数据（行/列） |
| **查询方式** | 相似度检索（KNN/ANN） | 精确匹配（WHERE 条件） |
| **索引类型** | ANN 近似索引 | B-Tree、Hash 等 |
| **距离度量** | 余弦、欧氏、内积 | 等于、大于、小于 |
| **适用场景** | AI 检索、推荐系统 | 事务处理、业务系统 |
| **数据规模** | 十亿级向量 | 千万级记录 |

**向量数据库工作流程：**

```python
# 1. 向量存储
#    将文本通过 Embedding 模型转换为向量后存储
vector_db.add(
    ids=["doc1", "doc2", "doc3"],
    embeddings=[[0.1, 0.2, ...], [0.3, 0.4, ...], ...],
    documents=["文档内容1", "文档内容2", "文档内容3"]
)

# 2. 向量检索
#    将查询文本转换为向量，在数据库中找最相似的向量
results = vector_db.query(
    query_vector=[0.15, 0.25, ...],  # 查询向量
    n_results=5  # 返回最相似的 5 个
)

# 3. 结果返回
#    返回相似向量及其关联的原始数据
print(results)  # [{id: "doc1", distance: 0.01, document: "文档内容1"}, ...]
```

**为什么需要向量数据库：**
1. **语义搜索**：通过语义理解找相关内容，而非关键词匹配
2. **大规模检索**：十亿级向量秒级检索
3. **AI 原生**：与大模型、Embedding 模型天然配合

---

### Q2: 什么是向量 Embedding？它是如何生成的？

**参考答案：**

**向量 Embedding 定义：**
Embedding 是将文本、图像、音频等非结构化数据转换为固定维度数值向量的过程，使得语义相似的内容在向量空间中距离相近。

**Embedding 生成流程：**

```python
from sentence_transformers import SentenceTransformer

# 1. 加载预训练模型
#    项目中使用 all-MiniLM-L6-v2，输出 384 维向量
model = SentenceTransformer("all-MiniLM-L6-v2")

# 2. 单条文本向量化
text = "RAG 是一种检索增强生成技术"
embedding = model.encode(text)
# 输出: array([0.123, -0.456, 0.789, ...], dtype=float32)
# 向量维度: 384

# 3. 批量向量化
texts = ["文本1", "文本2", "文本3"]
embeddings = model.encode(texts, batch_size=32)
# 输出: array([[...], [...], [...]], dtype=float32)

# 4. 归一化向量
#    归一化后向量长度为 1，便于计算余弦相似度
embedding_normalized = model.encode(text, normalize_embeddings=True)
```

**向量空间示意：**

```
                    文科相关
                       ↑
                       |
        [历史]     [语文]     [地理]
           \        |        /
            \       |       /
             \      |      /
              \     |     /
   理工相关 ←————————+————————→ 文科相关
              /     |     \
             /      |      \
            /       |       \
        [数学]    [物理]    [化学]
                       |
                       ↓
                    基础学科
```

---

### Q3: 什么是向量相似度？有哪些计算方法？

**参考答案：**

**向量相似度定义：**
向量相似度衡量两个向量在向量空间中的"接近程度"，值越大表示越相似。

**常用相似度计算方法：**

| 方法 | 公式 | 取值范围 | 适用场景 |
|------|------|----------|----------|
| **余弦相似度** | cos(θ) = A·B/(\|A\|\|B\|) | [-1, 1] | 文档、文本检索 |
| **欧氏距离** | √Σ(Aᵢ-Bᵢ)² | [0, +∞) | 图像、推荐系统 |
| **内积** | A·B = ΣAᵢBᵢ | (-∞, +∞) | 归一化向量 |

**项目中的相似度计算：**

```python
import numpy as np

def calculate_similarity(vec1, vec2, metric="cosine"):
    """计算向量相似度"""
    vec1 = np.array(vec1)
    vec2 = np.array(vec2)
    
    if metric == "cosine":
        # 余弦相似度
        dot_product = np.dot(vec1, vec2)
        norm_product = np.linalg.norm(vec1) * np.linalg.norm(vec2)
        return dot_product / (norm_product + 1e-9)
    
    elif metric == "euclidean":
        # 欧氏距离（距离越小越相似）
        return np.linalg.norm(vec1 - vec2)
    
    elif metric == "ip":  # 内积
        return np.dot(vec1, vec2)

# Milvus 中的距离转换
# Milvus 返回的是距离（distance），需要转换
# - L2 距离: similarity = 1 / (1 + distance)
# - IP 内积: similarity = distance（已是相似度）
# - COSINE: similarity = distance（已是相似度）
```

**实际应用示例：**

```python
# 查询向量与文档向量相似度计算
query_embedding = [0.1, 0.2, 0.3]
doc_embeddings = [
    [0.1, 0.2, 0.3],  # 相同方向，相似度高
    [0.5, 0.5, 0.5],  # 不同方向，相似度低
    [-0.1, -0.2, -0.3] # 相反方向，相似度为负
]

for i, doc_vec in enumerate(doc_embeddings):
    similarity = calculate_similarity(query_embedding, doc_vec, "cosine")
    print(f"文档{i+1} 相似度: {similarity:.4f}")
# 输出:
# 文档1 相似度: 1.0000（完全相同）
# 文档2 相似度: 0.964
# 文档3 相似度: -1.0000（完全相反）
```

---

### Q4: 什么是 ANN（近似最近邻）算法？为什么需要 ANN？

**参考答案：**

**精确最近邻 vs 近似最近邻：**

| 方法 | 全称 | 时间复杂度 | 准确率 | 适用规模 |
|------|------|------------|--------|----------|
| **KNN** | 精确最近邻 | O(N) | 100% | < 1万 |
| **ANN** | 近似最近邻 | O(log N) | 95-99% | 亿级 |

**为什么需要 ANN：**
精确搜索在十亿级向量中需要计算数十亿次距离，耗时数小时。ANN 通过牺牲少量精度换取大幅速度提升。

**常见 ANN 算法：**

| 算法 | 全称 | 特点 | 代表数据库 |
|------|------|------|-----------|
| **HNSW** | Hierarchical Navigable Small World | 图索引，高精度 | Milvus, Faiss |
| **IVF** | Inverted File Index | 聚类索引 | Faiss, Milvus |
| **PQ** | Product Quantization | 压缩向量 | Faiss |
| **LSH** | Locality-Sensitive Hashing | 哈希索引 | - |

**HNSW 算法原理：**

```python
# HNSW 层次结构示意
"""
Layer 2 (稀疏):    A ──────── E ──────── K
                    │         │         │
Layer 1 (中等):  A ─ B ─ C ─ E ─ F ─ G ─ K ─ L
                    │   │   │ │   │   │ │
Layer 0 (密集): A B C D E F G H I J K L M N O
                    
搜索过程:
1. 从顶层开始，在稀疏层做跳跃式搜索
2. 找到当前层的最近邻后，下降到下一层
3. 在密集层进行精确搜索
"""
```

**Milvus 中的 ANN 配置：**

```python
# 创建集合时指定索引
from pymilvus import Collection, FieldSchema, CollectionSchema, DataType

# 索引参数配置
index_params = {
    "metric_type": "IP",        # 距离度量类型: L2, IP, COSINE
    "index_type": "HNSW",       # 索引类型
    "params": {
        "M": 16,                 # HNSW 参数：每层连接数
        "efConstruction": 200   # HNSW 参数：构建时的搜索范围
    }
}

collection.create_index(
    field_name="embedding",  # 向量字段名
    index_params=index_params
)
```

---

### Q5: Milvus 是什么？它有哪些核心特点？

**参考答案：**

**Milvus 简介：**
Milvus 是一个开源的向量数据库，专为 AI 应用设计，支持存储、检索十亿级向量数据。

**核心特点：**

| 特点 | 说明 |
|------|------|
| **高性能** | 单节点支持十亿级向量，毫秒级查询 |
| **多索引支持** | HNSW、IVF、ANNOY、DISKANN 等 |
| **多距离度量** | L2 距离、内积（IP）、余弦相似度 |
| **混合查询** | 支持标量字段过滤 |
| **分布式架构** | 支持集群部署，水平扩展 |
| **云原生** | K8s 原生，支持公私混合部署 |
| **多语言 SDK** | Python、Go、Java、RESTful API |

**Milvus 架构：**

```
┌─────────────────────────────────────────────────────────────┐
│                         SDK Layer                           │
│              Python / Go / Java / REST API                  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      Access Layer                           │
│              负载均衡 │ 认证 │ 读写分离                      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      Coordinator                           │
│     Root Coord │ Data Coord │ Query Coord │ Index Coord    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                         Workers                            │
│    Data Node │ Query Node │ Index Node │ Proxy Node        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                       Storage Layer                         │
│          Object Storage │ Meta Storage │ Message Queue     │
│              (MinIO/S3)   │   (etcd)     │   (Pulsar)     │
└─────────────────────────────────────────────────────────────┘
```

**项目中的 Milvus 使用：**

```python
# rag-qa-system/app/core/vectorstore.py
from pymilvus import connections, Collection

# 1. 连接 Milvus
connections.connect(
    alias="default",
    host=settings.milvus_host,
    port=settings.milvus_port,
    user=settings.milvus_user,
    password=settings.milvus_password
)

# 2. 获取集合
collection = Collection("knowledge_base")

# 3. 搜索向量
results = collection.search(
    data=[query_embedding],
    anns_field="embedding",
    param={"metric_type": "IP", "params": {"nprobe": 16}},
    limit=5,
    output_fields=["id", "document_id", "content"]
)
```

---

## 2. Milvus 核心概念

### Q6: Milvus 中的 Collection（集合）和 Partition（分区）是什么？

**参考答案：**

**Collection 概念：**
Collection 是 Milvus 中存储向量数据的顶层容器，类似于关系型数据库中的表。

**Collection 特点：**
| 特性 | 说明 |
|------|------|
| 动态Schema | 支持动态添加字段 |
| 多向量字段 | 一个 Collection 可有多个向量字段 |
| 主键 | 必须是字符串类型 |
| 向量维度 | 必须是正整数 |

**创建 Collection：**

```python
from pymilvus import Collection, FieldSchema, CollectionSchema, DataType

# 定义字段
fields = [
    FieldSchema(name="id", dtype=DataType.VARCHAR, max_length=256, is_primary=True),
    FieldSchema(name="document_id", dtype=DataType.INT64),  # 文档ID
    FieldSchema(name="chunk_index", dtype=DataType.INT64),  # 块索引
    FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=65535),  # 内容
    FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=384)  # 向量
]

# 创建 Collection
schema = CollectionSchema(
    fields=fields,
    description="RAG 知识库向量集合"
)

collection = Collection(
    name="knowledge_base",
    schema=schema
)
```

**Partition 概念：**
Partition 是 Collection 的逻辑分区，用于数据隔离和查询加速。

**分区使用场景：**

```python
# 1. 创建分区
collection.create_partition("partition_name", description="分区描述")

# 2. 插入数据到指定分区
collection.insert(
    data=[...],
    partition_name="partition_name"
)

# 3. 只在特定分区搜索
collection.search(
    data=[query_vector],
    partition_names=["partition_name"],  # 只搜索该分区
    ...
)

# 项目中的分区策略
# 按文档类型分区
collection.create_partition("pdf_docs", description="PDF 文档")
collection.create_partition("docx_docs", description="Word 文档")
```

**分区优势：**

| 优势 | 说明 |
|------|------|
| 查询加速 | 只搜索相关分区，减少数据量 |
| 数据隔离 | 不同类型数据物理隔离 |
| 批量删除 | 按分区删除，不影响其他数据 |
| 备份恢复 | 可按分区独立备份 |

---

### Q7: Milvus 中的 Field（字段）和 Schema（模式）是什么？

**参考答案：**

**Field 类型：**

| 类型 | Milvus 类型 | 说明 |
|------|-------------|------|
| 主键 | VARCHAR | 唯一标识，必填 |
| 整型 | INT8/16/32/64 | 64位整数最常用 |
| 浮点 | FLOAT/DOUBLE | 64位浮点 |
| 布尔 | BOOL | True/False |
| 字符串 | VARCHAR | 可变长度字符串 |
| JSON | JSON | JSON 格式数据 |
| 向量 | FLOAT_VECTOR/BINARY_VECTOR | 向量字段 |

**完整 Schema 定义：**

```python
from pymilvus import FieldSchema, CollectionSchema, DataType

fields = [
    # 主键字段 - 必须是第一个字段
    FieldSchema(
        name="id",
        dtype=DataType.VARCHAR,
        max_length=256,  # VARCHAR 需要指定最大长度
        is_primary=True,  # 主键字段
        auto_id=False     # 手动指定 ID
    ),
    
    # 标量字段
    FieldSchema(
        name="document_id",
        dtype=DataType.INT64,  # 64 位整数
        description="文档 ID"
    ),
    
    FieldSchema(
        name="chunk_index",
        dtype=DataType.INT32,  # 32 位整数
        default_value=0        # 默认值
    ),
    
    FieldSchema(
        name="content",
        dtype=DataType.VARCHAR,
        max_length=65535        # 内容可能很长
    ),
    
    FieldSchema(
        name="tags",
        dtype=DataType.JSON,   # JSON 数组
        description="标签列表"
    ),
    
    # 向量字段
    FieldSchema(
        name="embedding",
        dtype=DataType.FLOAT_VECTOR,
        dim=384,              # 向量维度
        description="文本向量"
    )
]

schema = CollectionSchema(
    fields=fields,
    description="RAG 知识库集合",
    enable_dynamic_field=True  # 允许动态添加字段
)
```

**动态字段：**

```python
# 启用动态字段后，可以插入未定义的字段
collection.insert({
    "id": "doc_1",
    "document_id": 1,
    "embedding": [0.1, 0.2, ...],
    # 动态字段
    "custom_field": "custom_value",
    "score": 95.5
})
```

---

### Q8: Milvus 中的 Shard（分片）是什么？如何配置？

**参考答案：**

**Shard 概念：**
Shard 是 Milvus 集群中的数据分片机制，用于水平扩展写入能力。

**工作原理：**

```
写入请求
    │
    ▼
┌─────────────────────────────────────────┐
│           Proxy Node                    │
│    (接收请求，路由到 Shard)              │
└─────────────────────────────────────────┘
    │
    ├──▶ Shard 1 ──▶ Data Node 1 ──▶ Segment 1
    │
    ├──▶ Shard 2 ──▶ Data Node 2 ──▶ Segment 2
    │
    └──▶ Shard 3 ──▶ Data Node 3 ──▶ Segment 3
```

**创建 Collection 时指定 Shard 数：**

```python
# 单节点 Milvus（默认 1 个 Shard）
collection = Collection(
    name="test",
    schema=schema
)

# 集群 Milvus（可指定多个 Shard）
collection = Collection(
    name="test",
    schema=schema,
    num_shards=2  # 写入时路由到 2 个分片
)
```

**Shard 路由机制：**

```python
# Milvus 根据主键 hash 决定写入哪个 Shard
# 这保证了数据的均匀分布

# 对于字符串主键，Milvus 使用 MD5 哈希
# 对于数值主键，直接使用数值

# 示例：插入数据时自动路由
collection.insert([
    ["id1", "id2", "id3"],           # 主键
    [1, 2, 3],                         # document_id
    [[0.1,...], [0.2,...], [0.3,...]] # embeddings
])
# Milvus 内部会计算 hash(id) % num_shards 来决定分片
```

**Shards vs Partitions：**

| 特性 | Shard | Partition |
|------|-------|-----------|
| 作用层级 | 写入分布 | 查询优化 |
| 配置时机 | 创建 Collection | 随时创建 |
| 数量建议 | 2-10 | 按业务需求 |
| 影响范围 | 写入性能 | 查询性能 |
| 删除 | 不可单独删除 | 可单独删除 |

---

### Q9: Milvus 中的 Segment（段）是什么？

**参考答案：**

**Segment 概念：**
Segment 是 Milvus 存储向量的基本单元，每个 Segment 存储一批向量数据及其索引。

**Segment 类型：**

| 类型 | 说明 | 存储位置 |
|------|------|----------|
| **Growing Segment** | 新增数据的可增长段 | 内存 + 磁盘 |
| **Sealed Segment** | 已封存的只读段 | 磁盘 |

**数据流动：**

```
写入数据 ──▶ Growing Segment ──▶ Sealed Segment ──▶ 构建索引
                              (实时)                    │
                              (累积)                    ▼
                                                  完成索引
                                                  (可查询)
```

**Segment 配置：**

```python
# Milvus 配置文件（milvus.yaml）
dataCoord:
  segment:
    # 单个 Segment 最大大小（MB）
    maxSize: 512  # 默认 512MB
    
    # Growing Segment 触发封存的大小
    sealProportion: 0.25  # 达到 maxSize 的 25% 时封存
    
    # 最大 Segment 数量
    maxIdleSegmentCount: 50
```

**查看 Segment 状态：**

```python
# 获取 Collection 统计信息
collection.flush()  # 先刷新确保数据可见

# 查看实体数量
print(f"实体数量: {collection.num_entities}")

# 查看 Segment 信息（通过 Milvus Attu UI 或 Python API）
stats = collection.get_stats()
print(stats)
```

---

### Q10: Milvus 支持哪些数据类型？向量字段有什么限制？

**参考答案：**

**标量字段类型：**

| Python 类型 | Milvus 类型 | 说明 |
|-------------|-------------|------|
| str | VARCHAR | 可变长度字符串，需指定 max_length |
| int | INT64 | 64 位有符号整数 |
| float | Float/Double | 单精度/双精度浮点 |
| bool | BOOL | 布尔值 True/False |
| dict | JSON | JSON 格式数据 |
| list | JSON | JSON 数组 |

**向量字段类型：**

| 类型 | Milvus 类型 | 维度范围 | 存储需求 |
|------|-------------|----------|----------|
| 浮点向量 | FLOAT_VECTOR | 1-32768 | 4字节 × 维度 |
| 二进制向量 | BINARY_VECTOR | 8 的倍数 | 1字节 × (维度/8) |

**向量维度限制：**

```python
# Milvus 向量维度必须是正整数
FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=384)

# 不同 Embedding 模型的维度
models = {
    "all-MiniLM-L6-v2": 384,      # 项目使用
    "all-mpnet-base-v2": 768,
    "BAAI/bge-large-zh-v1.5": 1024,
    "text-embedding-ada-002": 1536,
    "text-embedding-3-small": 1536,
    "text-embedding-3-large": 3072
}

# 确保 Milvus 集合维度与模型输出维度一致
collection = Collection("knowledge_base")
# 如果维度不匹配，会导致插入失败
```

**类型转换示例：**

```python
import numpy as np

# NumPy 数组转列表
embedding_np = np.array([0.1, 0.2, 0.3])
embedding_list = embedding_np.tolist()

# Python 列表
embedding_list = [0.1, 0.2, 0.3]

# 确保是 float 类型
embedding_float = [float(x) for x in embedding_list]
```

---

## 3. 索引与算法

### Q11: Milvus 支持哪些索引类型？各有什么特点？

**参考答案：**

**索引类型对比：**

| 索引类型 | 适用度量 | 特点 | 适用场景 |
|----------|----------|------|----------|
| **FLAT** | 全部 | 暴力搜索，无压缩 | 小数据集、精确搜索 |
| **IVF_FLAT** | L2/IP | 聚类索引 | 中等规模 |
| **IVF_SQ8** | L2 | 标量量化压缩 | 减少存储 |
| **IVF_PQ** | L2/IP | 产品量化压缩 | 大规模减少存储 |
| **HNSW** | L2/IP/COSINE | 图索引，高精度 | 高性能需求 |
| **ANNOY** | L2/IP/COSINE | 树索引 | 磁盘友好 |
| **DISKANN** | L2/IP | 磁盘索引 | 超大规模 |

**HNSW 索引（推荐）：**

```python
# HNSW 配置
index_params = {
    "metric_type": "IP",           # 距离度量
    "index_type": "HNSW",           # 索引类型
    "params": {
        "M": 16,                    # 每层最大连接数
        "efConstruction": 200       # 构建时搜索范围
    }
}

# M 参数影响：
# - M ↑: 精度 ↑, 内存 ↑, 构建时间 ↑
# - 建议值: 8-64

# efConstruction 参数影响：
# - efConstruction ↑: 精度 ↑, 构建时间 ↑
# - 建议值: 64-512
```

**IVF_FLAT 索引：**

```python
# IVF_FLAT 配置
index_params = {
    "metric_type": "L2",
    "index_type": "IVF_FLAT",
    "params": {
        "nlist": 1024  # 聚类中心数量
    }
}

# 查询参数
search_params = {
    "metric_type": "L2",
    "params": {
        "nprobe": 16  # 查询时探测的聚类数
    }
}

# nlist 和 nprobe 的关系：
# - nlist: 1024-4096
# - nprobe: 1-4096, 通常 nlist 的 1-10%
```

**FLAT 索引（无索引）：**

```python
# 适用于小数据集或需要精确结果的情况
index_params = {
    "metric_type": "IP",
    "index_type": "FLAT"  # 无压缩，无索引
}

# search_params 可以为空
search_params = {
    "metric_type": "IP",
    "params": {}
}
```

---

### Q12: HNSW 算法的工作原理是什么？

**参考答案：**

**HNSW（分层可导航小世界图）原理：**

HNSW 是一种基于图的近似最近邻搜索算法，通过构建多层图结构实现高效的相似度搜索。

**多层结构：**

```
Layer 2:    A ────────────────────── K
             │                       │
Layer 1:  A ─ B ──────── E ────── K
             │       │   │       │
Layer 0:  A B C D E F G H I J K L M
           │   │   │   │   │   │
          最近邻集合
```

**搜索过程：**

```python
def hnsw_search(query_vector, search_params):
    """
    HNSW 搜索算法步骤：
    1. 从顶层入口点开始
    2. 在当前层贪心搜索最近邻
    3. 下降到下一层，以当前最近邻为入口点
    4. 重复直到最底层
    """
    
    # 1. 选择入口点（通常从顶层随机节点开始）
    current_node = entry_point
    
    # 2. 从顶层开始贪心搜索
    for layer in reversed(range(num_layers)):
        # 在当前层搜索最近邻
        for _ in range(search_params["ef"]):
            # 比较当前节点的所有邻居
            # 选择距离 query_vector 最近的
            neighbors = get_neighbors(current_node, layer)
            best = min(neighbors, key=lambda n: distance(query_vector, n))
            
            if distance(query_vector, best) < distance(query_vector, current_node):
                current_node = best
        
        # 3. 下降到下一层
        if layer > 0:
            current_node = get_closest_from_layer(current_node, layer - 1)
    
    # 4. 在最底层精确搜索
    return greedy_search_bottom_layer(query_vector, current_node, ef=search_params["ef"])
```

**HNSW 参数详解：**

| 参数 | 说明 | 影响 | 建议值 |
|------|------|------|--------|
| **M** | 每层最大连接数 | M↑ = 精度↑内存↑构建↑ | 8-64 |
| **efConstruction** | 构建时搜索范围 | ef↑ = 精度↑构建↑ | 64-512 |
| **efSearch** | 查询时搜索范围 | ef↑ = 精度↑速度↓ | 16-512 |
| **num_layers** | 层数（自动） | 通常 log(N) | 自动 |

**项目中的 HNSW 配置：**

```python
# rag-qa-system/app/core/vectorstore.py
index_params = {
    "metric_type": settings.milvus_metric_type,  # "IP" 内积
    "index_type": settings.milvus_index_type,    # "HNSW"
    "params": {
        "nlist": settings.milvus_nlist            # IVF 参数
    }
}

# 项目配置文件
# MILVUS_METRIC_TYPE = "IP"
# MILVUS_INDEX_TYPE = "HNSW"
# MILVUS_NLIST = 1024
```

---

### Q13: 什么是 IVF（倒排索引）？它如何工作？

**参考答案：**

**IVF（Inverted File Index）原理：**

IVF 是一种基于聚类的索引方法，将向量空间划分为多个聚类，搜索时只搜索相关聚类。

**工作流程：**

```
┌─────────────────────────────────────────────────┐
│                  向量空间                        │
│                                                 │
│      ● ● ●      ┌─────────┐      ● ● ●        │
│    ●    ●      │ Cluster1 │       ● ●          │
│  ●  ●  ●  ●   │  (中心C1) │     ●    ●  ●     │
│    ● ●        └─────────┘        ●  ●         │
│                     │                          │
│        ┌────────────┼────────────┐            │
│        ▼            ▼            ▼            │
│    ┌─────────┐ ┌─────────┐ ┌─────────┐      │
│    │ Cluster2│ │ Cluster3│ │ Cluster4│      │
│    │  (中心C2)│ │  (中心C3)│ │  (中心C4)│      │
│    └────┬────┘ └────┬────┘ └────┬────┘      │
│         │           │           │            │
│         ▼           ▼           ▼            │
│      [向量列表]  [向量列表]  [向量列表]        │
│                                                 │
└─────────────────────────────────────────────────┘
```

**搜索过程：**

```python
def ivf_search(query_vector, search_params):
    """
    IVF 搜索步骤：
    1. 计算 query 与所有聚类中心的距离
    2. 选择最近的 N 个聚类（nprobe）
    3. 在选中的聚类中搜索最近邻
    """
    
    nprobe = search_params["nprobe"]
    
    # 1. 计算到聚类中心的距离
    distances = []
    for center in cluster_centers:
        d = distance(query_vector, center)
        distances.append((center, d))
    
    # 2. 选择最近的 nprobe 个聚类
    nearest_clusters = sorted(distances, key=lambda x: x[1])[:nprobe]
    
    # 3. 在选中的聚类中搜索
    candidates = []
    for center, _ in nearest_clusters:
        candidates.extend(cluster_members[center])
    
    # 4. 计算精确距离，返回 Top-K
    results = sorted(
        [(c, distance(query_vector, c)) for c in candidates],
        key=lambda x: x[1]
    )[:k]
    
    return results
```

**IVF 变种：**

| 变种 | 特点 | 压缩比 | 精度损失 |
|------|------|--------|----------|
| IVF_FLAT | 不压缩 | 1x | 无 |
| IVF_SQ8 | 标量量化（8bit） | ~4x | 低 |
| IVF_SQ16 | 标量量化（16bit） | ~2x | 极低 |
| IVF_PQ | 产品量化 | ~10-50x | 中等 |

---

### Q14: 什么是向量量化（PQ）？它如何压缩向量？

**参考答案：**

**PQ（Product Quantization）原理：**

PQ 将高维向量分解为多个低维子向量，分别进行聚类量化，从而大幅减少存储空间。

**量化过程：**

```python
# 原始向量: [0.1, 0.2, 0.3, 0.4, 0.5, 0.6]  # 6维

# PQ 过程：
# 1. 分割：将向量分成 m=3 个子向量，每个子向量 2 维
sub_vector_1 = [0.1, 0.2]
sub_vector_2 = [0.3, 0.4]
sub_vector_3 = [0.5, 0.6]

# 2. 聚类：每个子空间用 k=256 个中心点量化
#    子空间1: 0.1 → 中心点 10 (假设值)
#    子空间2: 0.3 → 中心点 45
#    子空间3: 0.5 → 中心点 200

# 3. 编码：用中心点索引代替原始向量
#    原始: [0.1, 0.2, 0.3, 0.4, 0.5, 0.6]
#    编码: [10, 45, 200]  # 3个字节

# 存储对比：
# - 原始: 6个浮点数 × 4字节 = 24字节
# - PQ:   3个字节 + 聚类表 = ~3字节
# 压缩比: 8:1
```

**PQ 参数配置：**

```python
# PQ 索引配置
index_params = {
    "metric_type": "L2",
    "index_type": "IVF_PQ",
    "params": {
        "nlist": 1024,  # 聚类中心数
        "m": 16,        # 子向量数
        "nbits": 8      # 每个中心点用 8bit 表示（256 个中心）
    }
}

# 参数关系：
# - 向量维度 dim 必须能被 m 整除
# - dim = m × sub_dim
# - m 越大，压缩比越高，但精度可能下降
```

**距离计算（SDC 方法）：**

```python
# 查询时使用对称距离计算（SDC）
def pq_distance(query, encoded_vector, codebook):
    """
    query: 原始查询向量
    encoded_vector: PQ 编码后的向量 [c1, c2, ..., cm]
    codebook: 聚类中心点表
    """
    distance = 0
    sub_dim = len(query) // len(encoded_vector)
    
    for i, code in enumerate(encoded_vector):
        # 取查询向量的对应子向量
        query_sub = query[i * sub_dim : (i + 1) * sub_dim]
        
        # 取码本中对应的中心点
        center = codebook[i][code]  # 第 i 个子空间的第 code 个中心点
        
        # 累加距离
        distance += sum((a - b) ** 2 for a, b in zip(query_sub, center))
    
    return distance
```

---

### Q15: 如何选择合适的索引类型？

**参考答案：**

**索引选择决策树：**

```
数据规模和精度要求
        │
        ├─ 小数据量 (< 100万) + 高精度要求
        │       │
        │       └─▶ FLAT (暴力搜索，100% 精度)
        │
        ├─ 中等规模 (100万-1000万)
        │       │
        │       ├─ 内存充足 + 高精度
        │       │       │
        │       │       └─▶ HNSW
        │       │
        │       ├─ 内存有限 + 需要过滤
        │       │       │
        │       │       └─▶ IVF_FLAT
        │       │
        │       └─ 需要精确匹配
        │               │
        │               └─▶ IVF_FLAT + nprobe=全部
        │
        └─ 大规模 (> 1000万)
                │
                ├─ 内存极度有限
                │       │
                │       └─▶ IVF_PQ / DISKANN
                │
                └─ 追求均衡
                        │
                        └─▶ HNSW + 适量 nlist
```

**场景推荐：**

| 场景 | 推荐索引 | 配置 |
|------|----------|------|
| RAG 问答 | HNSW | M=16, efConstruction=200 |
| 图像检索 | IVF_PQ | nlist=4096, m=16, nbits=8 |
| 推荐系统 | HNSW/IVF_FLAT | M=32 或 nlist=4096, nprobe=64 |
| 人脸识别 | HNSW | M=32, efConstruction=256 |
| 日志分析 | IVF_FLAT | nlist=1024, nprobe=16 |

**项目中的选择：**

```python
# rag-qa-system 项目选择 HNSW 的原因：
# 1. 知识库规模：中等（百万级向量）
# 2. 精度要求：RAG 场景需要较高精度
# 3. 响应速度：HNSW 提供毫秒级查询
# 4. 内存：单机部署，HNSW 内存可控

index_params = {
    "metric_type": "IP",      # 内积（向量已归一化时等价于余弦）
    "index_type": "HNSW",
    "params": {
        "M": 16,               # 每层连接数
        "efConstruction": 200  # 构建精度
    }
}

# 查询参数
search_params = {
    "metric_type": "IP",
    "params": {
        "ef": 64  # 查询精度
    }
}
```

---

## 4. 集合与分区

### Q16: 如何创建、删除和管理 Collection？

**参考答案：**

**创建 Collection：**

```python
from pymilvus import Collection, CollectionSchema, FieldSchema, DataType, utility

# 1. 定义字段
fields = [
    FieldSchema(name="id", dtype=DataType.VARCHAR, max_length=256, is_primary=True),
    FieldSchema(name="document_id", dtype=DataType.INT64),
    FieldSchema(name="chunk_index", dtype=DataType.INT64),
    FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=65535),
    FieldSchema(name="filename", dtype=DataType.VARCHAR, max_length=512),
    FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=384)
]

# 2. 创建 Schema
schema = CollectionSchema(fields, description="RAG 知识库")

# 3. 创建 Collection
collection = Collection(
    name="knowledge_base",
    schema=schema,
    description="RAG 知识库集合",
    num_shards=2  # 可选：分片数
)

print(f"Collection 创建成功: {collection.name}")
```

**检查 Collection 是否存在：**

```python
# 检查 Collection 是否存在
if utility.has_collection("knowledge_base"):
    print("Collection 已存在")
    collection = Collection("knowledge_base")
else:
    print("Collection 不存在，需要创建")
```

**删除 Collection：**

```python
from pymilvus import utility

# 删除 Collection（会删除所有数据）
if utility.has_collection("knowledge_base"):
    utility.drop_collection("knowledge_base")
    print("Collection 已删除")

# 删除后重建
collection = Collection(
    name="knowledge_base",
    schema=schema
)
```

**Collection 基本操作：**

```python
collection = Collection("knowledge_base")

# 刷新数据（确保数据可见）
collection.flush()

# 获取实体数量
count = collection.num_entities
print(f"实体数量: {count}")

# 获取 Collection 统计信息
stats = collection.get_stats()
print(f"统计信息: {stats}")

# 释放 Collection（释放内存）
collection.release()

# 重新加载
collection.load()
```

**项目中的 Collection 管理：**

```python
# rag-qa-system/app/core/vectorstore.py
class VectorStore:
    def _ensure_collection(self):
        """确保 Collection 存在"""
        collection_name = settings.milvus_collection_name
        
        if utility.has_collection(collection_name):
            # 加载已有 Collection
            VectorStore._collection = Collection(collection_name)
            VectorStore._collection.load()
        else:
            # 创建新 Collection
            self._create_collection(collection_name)
    
    def reset(self) -> bool:
        """重置向量数据库"""
        if utility.has_collection(settings.milvus_collection_name):
            utility.drop_collection(settings.milvus_collection_name)
        self._create_collection(settings.milvus_collection_name)
```

---

### Q17: 如何管理 Milvus 中的分区（Partition）？

**参考答案：**

**创建分区：**

```python
collection = Collection("knowledge_base")

# 创建分区
collection.create_partition(
    partition_name="pdf_docs",
    description="PDF 文档分区"
)

# 创建多个分区
collection.create_partition("docx_docs", "Word 文档分区")
collection.create_partition("md_docs", "Markdown 文档分区")
```

**列出分区：**

```python
# 获取所有分区
partitions = collection.partitions

print(f"分区数量: {len(partitions)}")
for p in partitions:
    print(f"分区名: {p.name}, 描述: {p.description}, 实体数: {p.num_entities}")
```

**在分区中插入数据：**

```python
# 插入到指定分区
data = [
    ["doc_pdf_1", "doc_pdf_2"],
    [1, 1],
    [0, 1],
    ["PDF内容1", "PDF内容2"],
    ["file1.pdf", "file2.pdf"],
    [[0.1, 0.2, ...], [0.3, 0.4, ...]]  # 向量
]

collection.insert(data, partition_name="pdf_docs")

# 刷新使数据可见
collection.flush()
```

**在分区中搜索：**

```python
# 只搜索指定分区
results = collection.search(
    data=[query_vector],
    anns_field="embedding",
    param={"metric_type": "IP", "params": {"ef": 64}},
    limit=10,
    partition_names=["pdf_docs"]  # 只搜索 PDF 分区
)

# 搜索多个分区
results = collection.search(
    data=[query_vector],
    anns_field="embedding",
    param={"metric_type": "IP", "params": {"ef": 64}},
    limit=10,
    partition_names=["pdf_docs", "docx_docs"]
)
```

**删除分区：**

```python
# 删除分区（会删除分区中所有数据）
collection.drop_partition(partition_name="pdf_docs")

# 删除前确认
if collection.has_partition("pdf_docs"):
    collection.drop_partition("pdf_docs")
```

**分区使用场景：**

```python
# 场景1：按文档类型分区
# 适用于不同类型文档需要不同处理的场景
collection.create_partition("technical_docs", "技术文档")
collection.create_partition("business_docs", "业务文档")

# 场景2：按时间分区
# 适用于数据量持续增长，需要定期清理的场景
collection.create_partition("2024_q1")
collection.create_partition("2024_q2")

# 场景3：按用户/租户分区
# 适用于多租户系统
collection.create_partition("tenant_001")
collection.create_partition("tenant_002")
```

---

### Q18: 如何导入和导出 Milvus 数据？

**参考答案：**

**Bulk Insert（批量导入）：**

```python
from pymilvus import Collection, BulkInsertState
import json

# 1. 准备数据文件（JSON 格式）
# 每行一条记录
data_records = []
for i in range(1000):
    data_records.append({
        "id": f"doc_{i}",
        "document_id": i // 100,
        "chunk_index": i % 100,
        "content": f"文档内容 {i}",
        "embedding": [0.1 * j for j in range(384)]  # 示例向量
    })

# 写入 JSONL 文件
with open("bulk_data.jsonl", "w") as f:
    for record in data_records:
        f.write(json.dumps(record) + "\n")

# 2. 执行批量导入
collection = Collection("knowledge_base")

# 使用 Milvus 的 Bulk Insert API
tasks = collection.bulk_insert(
    collection_name="knowledge_base",
    partition_name=None,
    files=["bulk_data.jsonl"]
)

# 3. 检查导入状态
for task_id in tasks:
    state = collection.get_bulk_insert_state(task_id)
    print(f"任务ID: {task_id}, 状态: {state.state}")
```

**Python SDK 批量插入：**

```python
import numpy as np

collection = Collection("knowledge_base")

# 准备数据
batch_size = 1000
total_records = 10000

for batch_start in range(0, total_records, batch_size):
    batch_end = min(batch_start + batch_size, total_records)
    
    # 生成批次数据
    ids = [f"doc_{i}" for i in range(batch_start, batch_end)]
    doc_ids = [i // 100 for i in range(batch_start, batch_end)]
    chunk_indices = [i % 100 for i in range(batch_start, batch_end)]
    contents = [f"文档内容 {i}" for i in range(batch_start, batch_end)]
    filenames = [f"file_{i % 10}.pdf" for i in range(batch_start, batch_end)]
    embeddings = np.random.rand(batch_end - batch_start, 384).tolist()
    
    # 插入批次
    data = [ids, doc_ids, chunk_indices, contents, filenames, embeddings]
    collection.insert(data)
    
    print(f"已插入 {batch_end}/{total_records} 条记录")

# 刷新数据
collection.flush()
```

**导出数据：**

```python
# 通过查询导出所有数据
collection = Collection("knowledge_base")

# 查询所有数据
results = collection.query(
    expr="document_id >= 0",  # 查询条件
    output_fields=["id", "document_id", "content", "embedding"]
)

# 导出到文件
with open("exported_data.json", "w") as f:
    json.dump(results, f, ensure_ascii=False)

print(f"导出记录数: {len(results)}")
```

---

### Q19: Milvus 中如何处理数据的upsert（更新或插入）？

**参考答案：**

**Milvus 不支持直接 upsert，需要手动实现：**

```python
from pymilvus import Collection, utility

collection = Collection("knowledge_base")

def upsert_document(doc_id: str, data: dict):
    """Upsert 操作：更新已存在的数据，否则插入"""
    
    # 1. 检查记录是否存在
    existing = collection.query(
        expr=f'id == "{doc_id}"',
        output_fields=["id"]
    )
    
    if existing:
        # 2. 如果存在，更新数据
        # Milvus 不直接支持更新，需要删除后重新插入
        collection.delete(f'id == "{doc_id}"')
        print(f"已删除旧记录: {doc_id}")
    
    # 3. 插入新数据
    insert_data = [
        [doc_id],
        [data["document_id"]],
        [data["chunk_index"]],
        [data["content"]],
        [data.get("filename", "")],
        [data["embedding"]]
    ]
    collection.insert(insert_data)
    
    # 4. 刷新
    collection.flush()
    print(f"Upsert 完成: {doc_id}")

# 使用示例
upsert_document("doc_1", {
    "document_id": 1,
    "chunk_index": 0,
    "content": "更新后的内容",
    "embedding": [0.1, 0.2, ...]
})
```

**原子性 upsert 实现：**

```python
from pymilvus.exceptions import MilvusException

def atomic_upsert(collection_name: str, doc_id: str, data: dict):
    """
    原子性 Upsert：
    1. 先尝试删除
    2. 再插入新数据
    """
    try:
        collection = Collection(collection_name)
        
        # 删除操作
        collection.delete(f'id == "{doc_id}"')
        
        # 插入操作
        insert_data = prepare_insert_data(doc_id, data)
        collection.insert(insert_data)
        
        # 刷新
        collection.flush()
        
        return True
        
    except MilvusException as e:
        print(f"Upsert 失败: {e}")
        # 可能需要回滚逻辑
        return False
```

**条件更新：**

```python
# 更新满足条件的记录
# Milvus 支持根据主键或表达式删除

# 删除满足条件的记录
collection.delete("document_id in [1, 2, 3]")

# 批量删除
ids_to_delete = ["doc_1", "doc_2", "doc_3"]
for doc_id in ids_to_delete:
    collection.delete(f'id == "{doc_id}"')
```

---

### Q20: 如何监控 Milvus 集合的状态和统计信息？

**参考答案：**

**基本统计信息：**

```python
from pymilvus import Collection, utility

collection = Collection("knowledge_base")

# 刷新数据（确保统计准确）
collection.flush()

# 获取实体数量
count = collection.num_entities
print(f"总实体数: {count}")

# 获取分区统计
for partition in collection.partitions:
    partition.load()  # 加载分区以获取统计
    print(f"分区 {partition.name}: {partition.num_entities} 条")
```

**索引信息：**

```python
# 获取集合的索引信息
index_info = collection.index().params
print(f"索引类型: {index_info}")

# 获取索引构建进度（对于大集合）
# Milvus 不直接提供进度 API，需要通过状态判断
describe_index = collection.indexes
print(f"索引字段: {[idx.field_name for idx in describe_index]}")
```

**健康检查：**

```python
def check_milvus_health():
    """检查 Milvus 健康状态"""
    try:
        # 检查连接
        connections.connect(
            alias="default",
            host=settings.milvus_host,
            port=settings.milvus_port
        )
        
        # 检查集合
        collection = Collection("knowledge_base")
        collection.load()
        
        # 获取状态
        stats = collection.get_stats()
        
        return {
            "status": "healthy",
            "collection": collection.name,
            "entities": collection.num_entities,
            "stats": stats
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }

# 使用
health = check_milvus_health()
print(f"健康状态: {health['status']}")
```

**使用 Milvus Attu（可视化工具）：**

```bash
# 通过 Docker 运行 Attu
docker run -d \
    --name attu \
    -p 8000:3000 \
    -e MILVUS_URL=http://localhost:19530 \
    zilliz/attu:latest
```

---

## 5. 搜索与查询

### Q21: Milvus 中的向量搜索（search）如何使用？

**参考答案：**

**基本搜索语法：**

```python
collection = Collection("knowledge_base")

# 加载集合到内存（搜索前必须加载）
collection.load()

# 1. 单向量搜索
results = collection.search(
    data=[[0.1, 0.2, 0.3, ...]],  # 查询向量，包装在列表中
    anns_field="embedding",        # 要搜索的向量字段
    param={                        # 搜索参数
        "metric_type": "IP",      # 距离度量
        "params": {"ef": 64}      # HNSW 参数
    },
    limit=10,                      # 返回前 10 个结果
    output_fields=["id", "document_id", "content"]  # 返回的字段
)

# 处理结果
for result in results[0]:  # results 是列表的列表
    print(f"ID: {result.id}")
    print(f"Distance: {result.distance}")
    print(f"Document ID: {result.entity.get('document_id')}")
    print(f"Content: {result.entity.get('content')}")
```

**多向量批量搜索：**

```python
# 2. 多向量搜索（一次搜索多个查询向量）
query_vectors = [
    [0.1, 0.2, 0.3, ...],  # 查询1
    [0.4, 0.5, 0.6, ...],  # 查询2
    [0.7, 0.8, 0.9, ...]   # 查询3
]

results = collection.search(
    data=query_vectors,  # 多个查询向量
    anns_field="embedding",
    param={"metric_type": "IP", "params": {"ef": 64}},
    limit=5,
    output_fields=["id", "content"]
)

# results 是列表的列表
for i, query_results in enumerate(results):
    print(f"\n=== 查询 {i+1} 的结果 ===")
    for result in query_results:
        print(f"ID: {result.id}, Distance: {result.distance}")
```

**带过滤条件的搜索：**

```python
# 3. 带标量字段过滤的搜索
results = collection.search(
    data=[query_vector],
    anns_field="embedding",
    param={"metric_type": "IP", "params": {"ef": 64}},
    limit=10,
    expr="document_id == 1",  # 过滤条件
    output_fields=["id", "document_id", "content"]
)

# 复杂的过滤表达式
# =="document_id > 5"
# =="document_id in [1, 2, 3]"
# =="content like '%关键词%'"
# =="document_id == 1 and chunk_index > 5"
```

**项目中的搜索实现：**

```python
# rag-qa-system/app/core/vectorstore.py
def search_vectors(
    self,
    query_embedding: List[float],
    n_results: int = None,
    where: Dict[str, Any] = None
) -> Dict[str, Any]:
    """检索最相似的向量"""
    
    if n_results is None:
        n_results = runtime_config.retrieval_top_k
    
    # 构建搜索参数
    search_params = {
        "metric_type": settings.milvus_metric_type,
        "params": {"nprobe": 16}  # IVF 参数
    }
    
    # 处理过滤条件
    expr = None
    if where:
        if "document_id" in where:
            if isinstance(where["document_id"], dict):
                if "$in" in where["document_id"]:
                    doc_ids = where["document_id"]["$in"]
                    expr = f"document_id in {doc_ids}"
                elif "$eq" in where["document_id"]:
                    expr = f"document_id == {where['document_id']['$eq']}"
            else:
                expr = f"document_id == {where['document_id']}"
    
    # 执行搜索
    results = self.collection.search(
        data=[query_embedding],
        anns_field="embedding",
        param=search_params,
        limit=n_results,
        expr=expr,
        output_fields=["id", "document_id", "chunk_index", "content", "filename"]
    )
    
    # 处理结果...
    return processed_results
```

---

### Q22: Milvus 中的过滤查询（query）如何使用？

**参考答案：**

**基本查询语法：**

```python
collection = Collection("knowledge_base")
collection.load()

# 1. 查询所有数据
all_results = collection.query(
    expr="id >= 0",  # 永真条件
    output_fields=["id", "document_id", "content"]
)

# 2. 条件查询
results = collection.query(
    expr="document_id == 1",  # 等于条件
    output_fields=["id", "content"]
)

# 3. 范围查询
results = collection.query(
    expr="document_id > 5 and document_id < 10",  # 范围条件
    output_fields=["id", "document_id", "content"]
)
```

**支持的运算符：**

| 运算符 | 说明 | 示例 |
|--------|------|------|
| == | 等于 | `document_id == 1` |
| != | 不等于 | `document_id != 0` |
| > | 大于 | `chunk_index > 0` |
| >= | 大于等于 | `chunk_index >= 1` |
| < | 小于 | `chunk_index < 100` |
| <= | 小于等于 | `chunk_index <= 50` |
| in | 包含 | `document_id in [1, 2, 3]` |
| and | 逻辑与 | `a > 1 and b < 10` |
| or | 逻辑或 | `a == 1 or a == 2` |
| not | 逻辑非 | `not (a == 1)` |
| like | 模糊匹配 | `content like '%关键词%'` |

**字符串查询：**

```python
# 4. 字符串匹配
results = collection.query(
    expr='filename like "%.pdf%"',  # 文件名包含 .pdf
    output_fields=["id", "filename"]
)

# 5. JSON 字段查询
# 假设 tags 是 JSON 字段 ["技术", "Python"]
results = collection.query(
    expr='JSON_CONTAINS(tags, "\"Python\"")',  # 包含 Python 标签
    output_fields=["id", "tags"]
)
```

**分页查询：**

```python
# 6. 分页查询
offset = 0
limit = 20

results = collection.query(
    expr="document_id == 1",
    output_fields=["id", "chunk_index", "content"],
    limit=limit,
    offset=offset
)

# 分页获取
def paginate_query(expr, page, page_size):
    offset = (page - 1) * page_size
    return collection.query(
        expr=expr,
        output_fields=["id", "content"],
        limit=page_size,
        offset=offset
    )
```

**返回字段控制：**

```python
# 7. 指定返回字段（默认返回所有字段）
# 不返回向量字段可减少数据传输
results = collection.query(
    expr="document_id == 1",
    output_fields=["id", "document_id", "chunk_index", "content", "filename"]
    # 不包含 "embedding"，减少内存和网络开销
)
```

---

### Q23: Milvus 中如何计算距离？

**参考答案：**

**距离度量类型：**

| 度量类型 | 说明 | 公式 | 适用场景 |
|----------|------|------|----------|
| **L2** | 欧氏距离 | √Σ(aᵢ-bᵢ)² | 图像、通用 |
| **IP** | 内积 | Σaᵢbᵢ | 归一化向量、推荐 |
| **COSINE** | 余弦相似度 | cos(θ) = A·B/(\|A\|\|B\|) | 文本、语义相似度 |

**距离与相似度转换：**

```python
import numpy as np

def convert_distance_to_similarity(distance: float, metric_type: str) -> float:
    """将距离转换为相似度"""
    if metric_type == "L2":
        # L2 距离越小越相似
        # 转换为 0-1 的相似度
        # 注意：需要知道最大可能距离来归一化
        return 1 / (1 + distance)
    
    elif metric_type == "IP":
        # 内积越大越相似
        # 对于归一化向量，IP 等于余弦相似度
        return (distance + 1) / 2  # 假设 IP 范围是 [-1, 1]
    
    elif metric_type == "COSINE":
        # 余弦相似度范围 [-1, 1]
        return (distance + 1) / 2  # 转换到 [0, 1]
    
    return distance

# 项目中的转换
# 项目使用 IP（内积），向量已归一化
# similarity = distance（对于归一化向量，内积 = 余弦相似度）
```

**向量归一化：**

```python
# 为什么要归一化？
# 归一化后，向量的 L2 范数为 1
# 此时：
# - L2 距离与余弦距离的关系: L2_dist = sqrt(2 - 2*cos_sim)
# - 内积等价于余弦相似度

from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")

# 归一化向量
embedding = model.encode("文本", normalize_embeddings=True)

# 归一化后，L2 范数为 1
norm = np.linalg.norm(embedding)
print(f"向量范数: {norm}")  # 输出: 1.0

# 此时 IP = 余弦相似度
ip = np.dot(embedding1, embedding2)  # = 余弦相似度
```

**搜索时指定度量类型：**

```python
# 创建集合时指定度量类型
fields = [
    FieldSchema(name="id", dtype=DataType.VARCHAR, max_length=256, is_primary=True),
    FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=384)
]

schema = CollectionSchema(fields)

# 度量类型在索引中指定
index_params = {
    "metric_type": "IP",  # 或 "L2" 或 "COSINE"
    "index_type": "HNSW",
    "params": {"M": 16, "efConstruction": 200}
}

collection.create_index(field_name="embedding", index_params=index_params)

# 搜索时也要指定相同的度量类型
search_params = {
    "metric_type": "IP",  # 必须与索引一致
    "params": {"ef": 64}
}

results = collection.search(
    data=[query_vector],
    anns_field="embedding",
    param=search_params,
    limit=10
)
```

---

### Q24: 什么是 Range Search（范围搜索）？

**参考答案：**

**范围搜索概念：**
Range Search 返回与查询向量距离在指定范围内的所有向量，而不是固定数量的 Top-K。

**Range Search 实现：**

```python
# Milvus 原生不支持 Range Search，需要手动实现
collection = Collection("knowledge_base")
collection.load()

def range_search(
    collection,
    query_vector: list,
    anns_field: str,
    radius: float,       # 搜索半径
    range_filter: float, # 过滤范围（通常 >= radius）
    limit: int = 100
):
    """
    范围搜索：
    返回与 query_vector 距离 <= radius 的所有向量
    """
    results = collection.search(
        data=[query_vector],
        anns_field=anns_field,
        param={
            "metric_type": "IP",  # 或 L2
            "params": {"ef": 64}
        },
        limit=limit,
        output_fields=["id", "content"]
    )
    
    # 过滤出在指定范围内的结果
    filtered = []
    for result in results[0]:
        distance = result.distance
        # IP: 距离越大越相似；L2: 距离越小越相似
        # 根据度量类型调整过滤逻辑
        if is_within_range(distance, radius, "IP"):
            filtered.append(result)
    
    return filtered

def is_within_range(distance: float, radius: float, metric_type: str) -> bool:
    """判断距离是否在范围内"""
    if metric_type == "IP":
        # 内积：值越大越相似，radius 是相似度阈值
        return distance >= radius
    elif metric_type == "L2":
        # 欧氏距离：值越小越相似，radius 是距离阈值
        return distance <= radius
    return False

# 使用示例：找出相似度 >= 0.8 的所有文档
high_similarity_docs = range_search(
    collection=collection,
    query_vector=query_embedding,
    anns_field="embedding",
    radius=0.8,  # 相似度阈值
    range_filter=1.0,
    limit=1000  # 设置足够大的 limit
)
```

**项目中的应用：**

```python
# 项目中通过相似度阈值过滤
def _filter_by_threshold(self, results: Dict[str, Any], threshold: float) -> Dict[str, Any]:
    """根据相似度阈值过滤结果"""
    
    distances = results.get("distances", [[]])[0]
    
    # 保留距离 >= 阈值的结果
    valid_indices = [
        i for i, dist in enumerate(distances)
        if dist >= threshold  # IP 距离：越大越相似
    ]
    
    if not valid_indices:
        return {"ids": [[]], "distances": [[]], "documents": [[]], "metadatas": [[]]}
    
    # 过滤结果...
    return filtered_results
```

---

### Q25: 什么是 MMR（最大边际相关性）？如何实现？

**参考答案：**

**MMR 概念：**
MMR（Maximal Marginal Relevance）是一种多样性排序算法，在保证相关性的同时增加结果的多样性。

**为什么需要 MMR：**

```
不使用 MMR 的结果：
[文档1: Python入门] → [文档2: Python进阶] → [文档3: Python高级] → [文档4: Python框架]
问题：都是 Python 相关，内容高度重复

使用 MMR 的结果：
[文档1: Python入门] → [文档5: Django框架] → [文档2: Python进阶] → [文档6: Flask框架]
优势：既有 Python 核心知识，也有框架应用
```

**MMR 公式：**

```
MMR = argmax( relevance - λ * diversity )

其中：
- relevance = 与查询的相似度
- diversity = 与已选中结果的最大相似度
- λ = 多样性权重 (0-1)
```

**MMR 实现：**

```python
import numpy as np

def mmr_rerank(
    results: list,           # 初始搜索结果
    query_vector: list,     # 查询向量
    lambda_mult: float = 0.5,  # 多样性权重
    fetch_k: int = None    # 候选数量
) -> list:
    """
    MMR 重排序：
    在相关性和多样性之间取得平衡
    """
    if not results:
        return results
    
    fetch_k = fetch_k or len(results)
    selected = []
    candidates = results[:fetch_k]
    
    # 逐个选择
    while len(selected) < len(results):
        mmr_score = -float('inf')
        mmr_item = None
        
        for candidate in candidates:
            if candidate in selected:
                continue
            
            # 相关性：候选与查询的相似度
            relevance = candidate.distance
            
            # 多样性：候选与已选结果的最大相似度
            diversity = 0.0
            if selected:
                max_sim = 0
                for sel in selected:
                    # 计算已选结果与候选的相似度
                    sel_vec = get_embedding(sel)
                    cand_vec = get_embedding(candidate)
                    sim = cosine_similarity(sel_vec, cand_vec)
                    max_sim = max(max_sim, sim)
                diversity = max_sim
            
            # MMR 分数
            score = relevance - lambda_mult * diversity
            
            if score > mmr_score:
                mmr_score = score
                mmr_item = candidate
        
        if mmr_item:
            selected.append(mmr_item)
            candidates.remove(mmr_item)
        else:
            break
    
    return selected
```

**项目中的 MMR 实现：**

```python
# rag-qa-system/app/core/vectorstore.py
def _mmr_rerank(
    self,
    results: list,
    fetch_k: int = None,
    lambda_mult: float = None
) -> list:
    """
    Max Marginal Relevance 重排序
    """
    if not results:
        return results
    
    fetch_k = fetch_k or min(len(results), 100)
    lambda_mult = lambda_mult if lambda_mult is not None else runtime_config.mmr_diversity
    
    selected = []
    candidates = results[:fetch_k]
    
    while len(selected) < len(results):
        mmr_score = -float('inf')
        mmr_item = None
        
        for i, candidate in enumerate(candidates):
            if candidate in selected:
                continue
            
            rel = candidate.distance  # 相关性
            
            # 计算多样性
            div = 0.0
            if selected:
                cand_vec = self._get_hit_embedding(candidate)
                if cand_vec is not None:
                    cand_vec = np.array(cand_vec)
                    for sel in selected:
                        sel_vec = self._get_hit_embedding(sel)
                        if sel_vec is not None:
                            sel_vec = np.array(sel_vec)
                            # 计算余弦相似度
                            sim = float(np.dot(sel_vec, cand_vec) / 
                                      (np.linalg.norm(sel_vec) * np.linalg.norm(cand_vec) + 1e-9))
                            div = max(div, sim)
            
            # MMR 分数
            score = rel - lambda_mult * div
            
            if score > mmr_score:
                mmr_score = score
                mmr_item = candidate
        
        if mmr_item:
            selected.append(mmr_item)
            candidates.remove(mmr_item)
        else:
            break
        
        if len(selected) >= len(results):
            break
    
    return selected
```

---

## 6. 数据管理

### Q26: 如何删除 Milvus 中的数据？

**参考答案：**

**删除满足条件的实体：**

```python
collection = Collection("knowledge_base")

# 1. 按主键删除
collection.delete('id == "doc_123"')

# 2. 按条件删除
collection.delete('document_id == 1')  # 删除文档 ID 为 1 的所有块
collection.delete('document_id in [1, 2, 3]')  # 删除多个文档

# 3. 按范围删除
collection.delete('chunk_index > 100')  # 删除块索引大于 100 的

# 刷新使删除生效
collection.flush()
```

**批量删除：**

```python
# 删除多个文档的所有块
def delete_document_chunks(collection, document_id: int):
    """删除指定文档的所有块"""
    collection.delete(f'document_id == {document_id}')
    collection.flush()
    print(f"已删除文档 {document_id} 的所有块")

# 删除多个文档
def delete_documents(collection, document_ids: list):
    """批量删除多个文档"""
    for doc_id in document_ids:
        collection.delete(f'document_id == {doc_id}')
    collection.flush()
    print(f"已删除 {len(document_ids)} 个文档")
```

**删除分区：**

```python
# 删除整个分区（分区中的所有数据都会被删除）
collection.drop_partition(partition_name="temp_docs")
```

**清空集合：**

```python
# 删除所有数据
def clear_collection(collection):
    """清空 Collection 中的所有数据"""
    # 方法1：删除后再重建（更彻底）
    collection_name = collection.name
    collection.release()  # 释放内存
    from pymilvus import utility
    utility.drop_collection(collection_name)
    
    # 重新创建 Collection
    # ... (需要重新定义 schema)
    
    # 方法2：逐批删除（适用于大集合）
    while True:
        # 查询一批 ID
        results = collection.query(
            expr="id >= 0",
            output_fields=["id"],
            limit=1000
        )
        
        if not results:
            break
        
        # 删除这批
        for r in results:
            collection.delete(f'id == "{r["id"]}"')
        collection.flush()
    
    print("Collection 已清空")
```

---

### Q27: Milvus 中如何处理数据一致性？

**参考答案：**

**Milvus 数据一致性模型：**

| 级别 | 说明 | 适用场景 |
|------|------|----------|
| **Eventually** | 最终一致 | 大规模导入 |
| **Session** | 会话一致 | 实时读写 |
| **Strong** | 强一致 | 金融、订单 |

**会话一致性实现：**

```python
# 插入后立即查询，确保数据可见
collection.insert(data)
collection.flush()  # 刷新确保数据可见

# 查询时指定一致性级别（Milvus SDK 暂不支持，需在服务端配置）
# 或者使用等待策略

def insert_and_query(collection, data):
    """插入后等待数据可见"""
    # 插入
    collection.insert(data)
    
    # 等待刷新
    collection.flush()
    
    # 或者使用 timeout 参数
    # collection.flush(timeout=30)
    
    # 查询
    results = collection.query(expr=f'id == "{data[0][0]}"')
    return results
```

**并发控制：**

```python
import threading
from queue import Queue

class MilvusManager:
    """Milvus 操作管理器（线程安全）"""
    
    def __init__(self, collection_name):
        self.collection = Collection(collection_name)
        self.lock = threading.Lock()
    
    def safe_insert(self, data):
        """线程安全的插入"""
        with self.lock:
            self.collection.insert(data)
            self.collection.flush()
    
    def safe_delete(self, expr):
        """线程安全的删除"""
        with self.lock:
            self.collection.delete(expr)
            self.collection.flush()
    
    def safe_search(self, query_vector, limit=10):
        """线程安全的搜索"""
        with self.lock:
            return self.collection.search(
                data=[query_vector],
                anns_field="embedding",
                param={"metric_type": "IP", "params": {"ef": 64}},
                limit=limit
            )
```

**事务支持：**

```python
# Milvus 不支持跨集合事务，单集合内的事务也是有限的
# 最佳实践：批量操作 + 最终一致

def batch_upsert(collection, operations: list):
    """
    批量 Upsert（原子性有限）
    """
    delete_exprs = []
    insert_data = [[], [], [], [], [], []]
    
    for op in operations:
        if op["type"] == "delete":
            delete_exprs.append(f'id == "{op["id"]}"')
        elif op["type"] == "insert":
            # 收集插入数据
            pass
    
    # 先执行删除
    for expr in delete_exprs:
        collection.delete(expr)
    
    # 再执行插入
    if insert_data[0]:
        collection.insert(insert_data)
    
    # 最后刷新
    collection.flush()
```

---

### Q28: Milvus 中如何处理向量的增删改查？

**参考答案：**

**插入（Insert）：**

```python
collection = Collection("knowledge_base")

# 单条插入
data = [
    ["doc_1"],                           # 主键
    [1],                                 # document_id
    [0],                                 # chunk_index
    ["这是文档内容"],                     # content
    ["test.pdf"],                        # filename
    [[0.1, 0.2, 0.3, ...] * 96]         # embedding (384维)
]
collection.insert(data)

# 批量插入
batch_data = [
    ["doc_1", "doc_2", "doc_3"],       # 3个主键
    [1, 1, 1],                          # document_id
    [0, 1, 2],                          # chunk_index
    ["内容1", "内容2", "内容3"],
    ["file.pdf", "file.pdf", "file.pdf"],
    [vec1, vec2, vec3]                  # 3个向量
]
collection.insert(batch_data)

# 刷新
collection.flush()
```

**查询（Query）：**

```python
# 按主键查询
result = collection.query(
    expr='id == "doc_1"',
    output_fields=["*"]  # 返回所有字段
)

# 按条件查询
results = collection.query(
    expr="document_id == 1",
    output_fields=["id", "content", "chunk_index"]
)
```

**更新（Update）：**

```python
# Milvus 不直接支持 Update，需要删除后重新插入
def update_entity(collection, doc_id, new_data):
    # 1. 删除旧记录
    collection.delete(f'id == "{doc_id}"')
    
    # 2. 插入新记录
    collection.insert(prepare_data(doc_id, new_data))
    
    # 3. 刷新
    collection.flush()
```

**删除（Delete）：**

```python
# 按主键删除
collection.delete('id == "doc_1"')

# 按条件删除
collection.delete('document_id == 1')  # 删除该文档所有块
collection.delete('chunk_index >= 100')  # 删除末尾块

# 刷新
collection.flush()
```

**项目中的 CRUD 操作：**

```python
# rag-qa-system/app/core/vectorstore.py
class VectorStore:
    def add_vectors(self, documents, embeddings, ids, metadatas):
        """添加向量"""
        data = [
            ids,
            [m.get("document_id", 0) for m in metadatas],
            [m.get("chunk_index", 0) for m in metadatas],
            documents,
            [m.get("filename", "") for m in metadatas],
            embeddings
        ]
        self.collection.insert(data)
        self.collection.flush()
    
    def delete_by_document_id(self, document_id: int):
        """根据文档 ID 删除"""
        expr = f"document_id == {document_id}"
        self.collection.delete(expr)
        self.collection.flush()
    
    def search_vectors(self, query_embedding, n_results, where):
        """搜索向量"""
        # ... 搜索逻辑
        pass
    
    def reset(self):
        """重置集合"""
        # 删除并重建
        pass
```

---

## 7. 性能优化

### Q29: 如何优化 Milvus 的搜索性能？

**参考答案：**

**1. 合理选择索引类型：**

```python
# HNSW 配置优化
search_params = {
    "metric_type": "IP",
    "index_type": "HNSW",
    "params": {
        "ef": 64  # 查询时搜索范围，越大越精确但越慢
    }
}

# 平衡策略
# - 精确优先：ef=256-512
# - 均衡：ef=64-128
# - 速度优先：ef=16-32
```

**2. 预加载集合到内存：**

```python
# 搜索前加载集合
collection = Collection("knowledge_base")
collection.load()  # 加载到内存

# 检查加载状态
if not collection.is_empty:
    print(f"集合已加载，实体数: {collection.num_entities}")
```

**3. 限制返回字段：**

```python
# 只返回必要的字段，避免返回大字段
results = collection.search(
    data=[query_vector],
    anns_field="embedding",
    param=search_params,
    limit=10,
    output_fields=["id", "document_id", "content"]  # 不返回 embedding 字段
)
```

**4. 使用分区缩小搜索范围：**

```python
# 按业务类型分区
collection.create_partition("technical", "技术文档")
collection.create_partition("business", "业务文档")

# 只搜索相关分区
results = collection.search(
    data=[query_vector],
    anns_field="embedding",
    param=search_params,
    limit=10,
    partition_names=["technical"]  # 只搜索技术文档分区
)
```

**5. 批量搜索优化：**

```python
# 多个查询向量一起搜索比多次单独搜索更快
query_vectors = [[...], [...], [...]]  # 多个查询

results = collection.search(
    data=query_vectors,  # 一次传入多个向量
    anns_field="embedding",
    param=search_params,
    limit=10
)
```

**6. 连接池复用：**

```python
# 复用连接而不是每次请求创建新连接
from pymilvus import connections

class VectorStore:
    _instance = None
    _connection = None
    _collection = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            # 建立连接（只执行一次）
            connections.connect(
                alias="default",
                host=settings.milvus_host,
                port=settings.milvus_port
            )
        return cls._instance
```

**7. 缓存热点数据：**

```python
# Redis 缓存热门查询结果
redis_cache = RedisCache()

def search_with_cache(query_vector, question):
    # 生成缓存键
    cache_key = f"search:{hashlib.md5(str(query_vector).encode()).hexdigest()}"
    
    # 尝试获取缓存
    cached = redis_cache.get(cache_key)
    if cached:
        return cached
    
    # 未命中，执行搜索
    results = collection.search(...)
    
    # 存入缓存
    redis_cache.set(cache_key, results, ttl=3600)
    
    return results
```

---

### Q30: Milvus 的内存管理有哪些要点？

**参考答案：**

**内存占用分析：**

| 组件 | 内存占用 | 说明 |
|------|----------|------|
| **向量数据** | dim × 4字节 × 数量 | FLOAT_VECTOR 格式 |
| **索引数据** | 索引大小 × 系数 | HNSW 约 1.2-2 倍数据大小 |
| **缓冲区** | 配置文件指定 | 预分配内存池 |

**计算示例：**

```python
# 假设 100 万条 384 维向量

# 1. 向量数据大小
vector_size_mb = 1000000 * 384 * 4 / (1024 * 1024)  # ≈ 1464 MB

# 2. HNSW 索引大小（估算）
hnsw_overhead = 1.5  # HNSW 通常是原始数据的 1.5-2 倍
index_size_mb = vector_size_mb * hnsw_overhead  # ≈ 2200 MB

# 3. 总内存需求
total_mb = vector_size_mb + index_size_mb  # ≈ 3664 MB

print(f"向量数据: {vector_size_mb:.0f} MB")
print(f"索引数据: {index_size_mb:.0f} MB")
print(f"总内存需求: {total_mb:.0f} MB")
```

**内存配置优化：**

```yaml
# milvus.yaml 配置
dataCoord:
  segment:
    maxSize: 512  # 单个 Segment 最大大小(MB)

queryCoord:
  # 查询节点内存限制
  memoryLimitPerNode: 16GB  # 单节点内存限制

# 确保系统有足够内存
# 公式：向量大小 × 2.5（数据 + 索引 + 缓冲区）
```

**内存释放：**

```python
# 释放集合占用的内存
collection = Collection("knowledge_base")

# 释放（从内存中卸载）
collection.release()

# 重新加载
collection.load()

# 清理未使用的资源
import gc
gc.collect()  # Python 垃圾回收
```

**监控内存使用：**

```python
import psutil

def monitor_milvus_memory():
    """监控 Milvus 进程内存"""
    milvus_process = None
    
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        if 'milvus' in proc.info['name'].lower():
            milvus_process = proc
            break
    
    if milvus_process:
        mem_info = milvus_process.memory_info()
        print(f"Milvus 进程内存: {mem_info.rss / (1024**3):.2f} GB")
```

**减少内存占用的策略：**

| 策略 | 效果 | 说明 |
|------|------|------|
| 使用 PQ 索引 | 减少 80% | 有精度损失 |
| 减小向量维度 | 线性减少 | 384→128 |
| 分区存储 | 按需加载 | 减少并发占用 |
| 数据分层 | 热数据内存 | 冷数据磁盘 |

---

## 附录：面试重点总结

### 核心知识点

| 类别 | 重点内容 |
|------|----------|
| **向量基础** | Embedding、相似度计算、ANN vs KNN |
| **索引算法** | HNSW、IVF、PQ 的原理和选择 |
| **数据操作** | Collection、分区、CRUD |
| **搜索查询** | search、query、过滤、范围搜索 |
| **MMR** | 多样性重排序原理和实现 |
| **性能优化** | 索引配置、内存管理、缓存 |

### 常见追问

1. **HNSW 和 IVF 各自适用场景？**
   - HNSW：需要高精度的在线查询
   - IVF：大规模数据、需要过滤条件的场景

2. **如何选择向量维度？**
   - 根据 Embedding 模型输出维度
   - 维度越高精度越高，但内存和计算成本增加

3. **Milvus 如何保证数据一致性？**
   - 写入后需要 flush
   - 不支持跨集合事务
   - 推荐使用 Session 一致性级别

---

*本文档共 30 道面试题，覆盖 Milvus 向量数据库的核心技术点*
