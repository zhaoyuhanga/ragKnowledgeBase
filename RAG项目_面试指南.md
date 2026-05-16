# RAG 问答系统 - 项目经验与面试指南

## 目录
1. [项目概述](#1-项目概述)
2. [核心技术问题](#2-核心技术问题)
3. [项目亮点面试题](#3-项目亮点面试题)
4. [系统设计问题](#4-系统设计问题)
5. [性能优化问题](#5-性能优化问题)
6. [项目经验总结](#6-项目经验总结)

---

## 1. 项目概述

### 1.1 项目简介

本项目是一个**基于 RAG（检索增强生成）技术的智能问答系统**，能够从用户上传的文档中检索相关内容，结合大语言模型生成准确的回答。

### 1.2 核心功能

| 功能 | 描述 |
|------|------|
| 文档上传 | 支持 PDF、DOCX、MD、TXT 等格式 |
| 智能问答 | 基于知识库内容回答用户问题 |
| 知识库管理 | 文档管理、索引重建、缓存清理 |
| 实时配置 | 支持动态调整检索参数 |
| 历史记录 | 保存问答历史，支持回溯 |

### 1.3 技术架构

```
┌─────────────────────────────────────────────────────────────┐
│                      前端 (Vue 3 + Element Plus)            │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼ HTTP/REST
┌─────────────────────────────────────────────────────────────┐
│                    后端 (FastAPI + Uvicorn)                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │  问答API  │  │ 文档API  │  │ 知识库API │  │ 系统API  │  │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘  │
│       │             │             │             │         │
│       └─────────────┴─────────────┴─────────────┘         │
│                           │                                │
│                    ┌──────▼──────┐                        │
│                    │   服务层     │                        │
│                    │ QA Service  │                        │
│                    │ Doc Service │                        │
│                    │ Knowledge Svc│                        │
│                    └──────┬──────┘                        │
└──────────────────────────│────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
┌───────────────┐  ┌───────────────┐  ┌───────────────┐
│     MySQL      │  │   ChromaDB    │  │     Redis     │
│   (元数据)     │  │   (向量库)    │  │    (缓存)     │
└───────────────┘  └───────────────┘  └───────────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │  DeepSeek API   │
                  │   (LLM 生成)    │
                  └─────────────────┘
```

### 1.4 技术栈清单

| 分类 | 技术 | 用途 |
|------|------|------|
| **后端框架** | FastAPI + Uvicorn | 异步 API 服务 |
| **数据库** | MySQL (SQLAlchemy) | 关系数据存储 |
| **向量库** | ChromaDB | 向量存储与检索 |
| **缓存** | Redis | 问答结果缓存 |
| **LLM** | DeepSeek API | 回答生成 |
| **Embedding** | sentence-transformers | 文本向量化 |
| **文档解析** | pypdf, python-docx | 文档内容提取 |
| **日志** | loguru | 结构化日志 |
| **前端** | Vue 3 + Element Plus | 用户界面 |

---

## 2. 核心技术问题

### Q1: 什么是 RAG？它的核心思想是什么？

**参考答案：**

**RAG（Retrieval-Augmented Generation，检索增强生成）** 是一种结合检索系统和生成模型的技术架构。

**核心思想**：
1. **检索阶段**：从知识库中检索与问题相关的文档片段
2. **增强阶段**：将检索到的内容作为上下文注入到 Prompt 中
3. **生成阶段**：让 LLM 基于检索内容生成准确回答

**为什么需要 RAG？**
- **知识时效性**：LLM 训练数据有截止日期，无法回答最新问题
- **幻觉问题**：LLM 可能产生不准确的"幻觉"内容
- **领域知识**：通用模型缺乏特定领域的专业知识
- **可溯源性**：可以追溯回答的来源文档

**项目中的应用**：
```python
# 1. 检索相关文档
search_results = vector_store.search_vectors(query_embedding, n_results=5)

# 2. 构建上下文
context_texts = [chunk["content"] for chunk in retrieved_chunks]
prompt = f"基于以下内容回答问题：\n{context}\n\n问题：{question}"

# 3. LLM 生成回答
answer = llm.generate_with_context(question, context_texts)
```

---

### Q2: ChromaDB 是如何实现向量检索的？原理是什么？

**参考答案：**

**ChromaDB 简介**：
ChromaDB 是一个开源的向量数据库，专为 AI 应用设计，支持本地持久化存储。

**核心原理**：

1. **向量存储**
   - 将文本通过 Embedding 模型转换为固定维度的向量（如 384 维）
   - 每个向量附带元数据（document_id, chunk_index 等）

2. **相似度计算**
   - ChromaDB 默认使用 **L2 距离（欧氏距离）**
   - 距离公式：`d = sqrt(sum((a_i - b_i)^2))`
   - 归一化相似度：`similarity = 1 - distance / 2`（L2 范围 [0,2]）

3. **ANN 近似最近邻**
   - 为加速检索，使用 HNSW（Hierarchical Navigable Small World）算法
   - 在精度和速度之间取得平衡

**项目中的使用**：
```python
# 添加向量
collection.add(
    ids=vector_ids,
    embeddings=embeddings,
    documents=texts,
    metadatas=metadatas
)

# 检索向量
results = collection.query(
    query_embeddings=[query_vector],
    n_results=5,
    where={"document_id": 1}  # 可选：元数据过滤
)
```

**为什么选择 ChromaDB？**
- 轻量级，易于部署
- 支持本地持久化
- 与 Python 生态集成良好
- 开源免费

---

### Q3: Embedding 模型是如何工作的？为什么选择 sentence-transformers？

**参考答案：**

**Embedding 原理**：

Embedding 模型将文本映射到高维向量空间，使得语义相似的文本在向量空间中距离相近。

**工作流程**：
1. **分词**：将文本分割成 tokens
2. **向量化**：通过神经网络将 tokens 转换为向量
3. **池化**：对 token 向量进行池化（如 mean pooling）得到句子向量
4. **归一化**：L2 归一化使向量长度统一

**本项目使用的模型**：
```python
model_name = "sentence-transformers/all-MiniLM-L6-v2"
# 输出向量维度：384
# 特点：轻量、快速、效果好
```

**为什么选择 all-MiniLM-L6-v2？**
| 特性 | 说明 |
|------|------|
| **轻量** | 仅 80MB，适合本地部署 |
| **快速** | CPU 友好，推理速度快 |
| **效果好** | 在 MTEB 基准上表现优秀 |
| **多语言** | 支持多语言语义相似度 |

**项目代码**：
```python
from sentence_transformers import SentenceTransformer

class EmbeddingService:
    def __init__(self):
        self.model = SentenceTransformer("all-MiniLM-L6-v2")

    def encode_single(self, text: str) -> List[float]:
        embedding = self.model.encode(text, normalize_embeddings=True)
        return embedding.tolist()

    def encode_batch(self, texts: List[str]) -> List[List[float]]:
        embeddings = self.model.encode(texts, batch_size=32)
        return embeddings.tolist()
```

---

### Q4: FastAPI 的异步机制是如何工作的？与 Django/Flask 有什么区别？

**参考答案：**

**FastAPI 异步原理**：

FastAPI 基于 Python 的 `asyncio` 和 Starlette 框架构建，使用 **async/await** 语法实现非阻塞 I/O。

**核心概念**：

1. **协程（Coroutine）**
   - 使用 `async def` 定义异步函数
   - 可暂停和恢复执行
   - 比线程更轻量

2. **事件循环（Event Loop）**
   - 管理协程的执行
   - 处理 I/O 事件
   - 单线程即可处理高并发

3. **异步 vs 同步对比**：
```python
# 同步方式 - 阻塞等待
def get_data_sync():
    response = requests.get(url)  # 阻塞
    return response.json()

# 异步方式 - 非阻塞
async def get_data_async():
    response = await httpx.AsyncClient().get(url)  # 非阻塞
    return response.json()
```

**FastAPI vs Django/Flask**：

| 特性 | FastAPI | Django | Flask |
|------|---------|--------|-------|
| **并发模型** | 异步（asyncio） | 同步（可加 async） | 同步 |
| **性能** | 极高 | 中等 | 中等 |
| **类型提示** | 原生支持 | 可选 | 需扩展 |
| **自动文档** | Swagger UI 内置 | DRF 可选 | 需扩展 |
| **学习曲线** | 中等 | 陡峭 | 平缓 |
| **适用场景** | I/O 密集型 API | 复杂 Web 应用 | 简单微服务 |

**项目中的异步使用**：
```python
@router.post("/ask")
async def ask_question(request: QAAskRequest, db: Session = Depends(get_db)):
    # 异步调用 LLM API
    result = await qa_service.ask(
        question=request.question,
        db=db,
        session_id=request.session_id
    )
    return result
```

---

### Q5: Redis 在项目中是如何使用的？为什么需要缓存？

**参考答案：**

**Redis 在项目中的使用**：

1. **问答结果缓存**
   ```python
   # 缓存键生成：使用问题 MD5 哈希
   cache_key = f"qa:{hashlib.md5(question.encode()).hexdigest()}"

   # 写入缓存
   cache.set_qa_cache(question, answer, sources)

   # 读取缓存
   cached = cache.get_qa_cache(question)
   if cached:
       return {"answer": cached["answer"], "cache_hit": True}
   ```

2. **缓存结构**
   ```python
   {
       "question": "...",
       "answer": "...",
       "sources": [...],
       "timestamp": "..."
   }
   ```

**为什么需要缓存？**

| 原因 | 说明 |
|------|------|
| **降低成本** | LLM API 按 token 计费，缓存避免重复调用 |
| **提升速度** | 缓存命中时响应时间从秒级降至毫秒级 |
| **减轻负载** | 减少对 LLM API 的并发压力 |
| **提升体验** | 用户无需等待重复问题的回答 |

**Redis 缓存策略**：
- TTL：3600 秒（1小时）
- 键前缀：`rag_qa:`
- 序列化：JSON 格式

---

### Q6: 文本是如何进行切分的？为什么需要切分？

**参考答案：**

**为什么需要文本切分？**

1. **LLM 上下文窗口限制**：大多数 LLM 有 token 数量限制（如 4K、16K）
2. **检索精度**：小块更容易准确匹配用户问题
3. **向量表示**：长文本会稀释语义焦点

**本项目的切分策略**：

```python
class TextSplitter:
    def __init__(self, chunk_size=500, chunk_overlap=50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def split(self, text: str) -> List[str]:
        # 1. 优先按段落分割
        paragraphs = text.split('\n\n')

        # 2. 合并小段落
        chunks = []
        current_chunk = []

        for para in paragraphs:
            if sum(len(p) for p in current_chunk) + len(para) <= self.chunk_size:
                current_chunk.append(para)
            else:
                if current_chunk:
                    chunks.append('\n\n'.join(current_chunk))
                # 重叠处理
                current_chunk = current_chunk[-1:] if len(current_chunk) > 1 else []
                current_chunk.append(para)

        if current_chunk:
            chunks.append('\n\n'.join(current_chunk))

        return chunks
```

**切分原则**：
| 原则 | 说明 |
|------|------|
| **保留语义** | 优先按段落边界切分 |
| **重叠保序** | 使用 overlap 确保上下文连续 |
| **大小限制** | chunk_size 限制每块长度 |
| **句子保护** | 尽量不在句子中间切分 |

---

### Q7: SQLAlchemy ORM 是如何工作的？它与原生 SQL 有什么区别？

**参考答案：**

**SQLAlchemy 核心概念**：

1. **ORM（对象关系映射）**
   - 将 Python 类映射到数据库表
   - 将类实例映射到数据库行
   - 将属性映射到表列

2. **核心组件**：
   ```python
   from sqlalchemy import Column, Integer, String
   from sqlalchemy.orm import declarative_base

   Base = declarative_base()

   class Document(Base):
       __tablename__ = "documents"

       id = Column(Integer, primary_key=True)
       filename = Column(String(255), nullable=False)
       status = Column(Integer, default=0)
   ```

**ORM vs 原生 SQL**：

| 方面 | SQLAlchemy ORM | 原生 SQL |
|------|---------------|----------|
| **代码风格** | Python 面向对象 | 字符串 SQL |
| **安全性** | 自动防 SQL 注入 | 需手动处理 |
| **可移植性** | 支持多数据库 | 需改写 |
| **性能** | 略有开销 | 最优 |
| **复杂度** | 学习曲线 | 简单直接 |

**项目中的使用**：
```python
# 查询
documents = db.query(Document).filter(
    Document.status == 1
).order_by(
    Document.created_at.desc()
).all()

# 添加
doc = Document(filename=filename, status=0)
db.add(doc)
db.commit()

# 更新
doc.status = 1
db.commit()

# 删除
db.delete(doc)
db.commit()
```

---

## 3. 项目亮点面试题

### Q8: 项目的架构设计有哪些亮点？

**参考答案：**

**1. 分层架构设计**
```
API Layer → Service Layer → Core Layer → Data Layer
```
- **关注点分离**：每层职责明确
- **易于测试**：可单独测试每层
- **便于扩展**：替换实现不影响其他层

**2. 单例模式管理全局组件**
```python
class EmbeddingService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.model = SentenceTransformer(...)
        return cls._instance
```
- 确保 Embedding 模型只加载一次
- 避免重复初始化开销

**3. 生命周期管理**
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动：初始化数据库、检查组件状态
    init_db()
    check_health()
    yield
    # 关闭：清理资源
    cleanup()
```
- 统一管理应用启动和关闭
- 避免资源泄漏

**4. 运行时配置热更新**
```python
class RuntimeConfigManager:
    _config = {"retrieval_top_k": 5, "similarity_threshold": 0.2}

    def update(self, config_dict):
        for key, value in config_dict.items():
            setattr(self, key, value)
```
- 无需重启服务即可修改配置
- 提升运维效率

**5. 操作日志审计**
```python
class OperationLogger:
    def log_operation(self, operation, status, details):
        log_data = {
            "operation": operation,
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "details": details
        }
        self.logger.info(f"操作日志", extra=log_data)
```
- 便于问题追溯
- 支持业务分析

---

### Q9: 项目中有哪些性能优化措施？

**参考答案：**

**1. Redis 缓存优化**
```python
# 缓存键设计：使用 MD5 哈希
cache_key = f"qa:{hashlib.md5(question.encode()).hexdigest()}"

# 设置过期时间
cache.setex(cache_key, ttl=3600, value=json.dumps(data))
```
- 避免重复调用 LLM API
- 降低响应时间（秒级 → 毫秒级）

**2. 批量向量化**
```python
# 批量编码而非逐个编码
embeddings = self.model.encode(texts, batch_size=32)
```
- 减少模型推理次数
- 提高 CPU 利用率

**3. 数据库连接池**
```python
engine = create_engine(
    url,
    poolclass=QueuePool,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,  # 检测连接有效性
    pool_recycle=3600     # 一小时后回收连接
)
```
- 复用数据库连接
- 避免频繁创建销毁连接

**4. 异步 I/O**
```python
async def ask_question(request: QAAskRequest):
    result = await qa_service.ask(...)  # 异步调用
```
- 充分利用 I/O 等待时间
- 支持高并发

**5. 向量检索优化**
```python
# 归一化向量加速检索
embedding = self.model.encode(text, normalize_embeddings=True)

# 相似度阈值过滤
if similarity < threshold:
    continue
```
- 减少返回数据量
- 提高检索质量

---

### Q10: 项目如何保证系统的稳定性？

**参考答案：**

**1. 健康检查机制**
```python
def health_check():
    mysql_ok = check_db_connection()
    redis_ok = redis_cache.check_health()
    chromadb_ok = vector_store.check_health()
    llm_ok = llm_client.check_connection()

    # 计算整体状态
    if all([mysql_ok, chromadb_ok]):
        return "healthy"
    elif healthy_count >= 2:
        return "degraded"
    else:
        return "unhealthy"
```

**2. 异常处理**
```python
try:
    result = await qa_service.ask(...)
    return {"success": True, "data": result}
except ValueError as e:
    return {"success": False, "error": str(e)}
except Exception as e:
    logger.error(f"处理失败: {e}")
    return {"success": False, "error": "系统错误"}
```

**3. 日志记录**
```python
# 操作日志
qa_logger.log_query(question, len(answer), sources_count, cache_hit, status, elapsed)

# 错误日志
logger.error(f"问答处理失败: {str(e)}", exc_info=True)
```

**4. 数据验证**
```python
class QAAskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=1000)
    top_k: int = Field(ge=1, le=20, default=5)
    temperature: float = Field(ge=0.0, le=2.0, default=0.3)
```

**5. 幂等性设计**
```python
# 使用文件哈希去重
content_hash = hashlib.md5(file_content).hexdigest()
existing = db.query(Document).filter(
    Document.content_hash == content_hash
).first()
if existing:
    raise ValueError("文档已存在")
```

---

## 4. 系统设计问题

### Q11: 如何设计一个高可用的 RAG 系统？

**参考答案：**

**架构设计要点**：

```
┌─────────────────────────────────────────────────────────┐
│                      负载均衡器                          │
│                   (Nginx / HAProxy)                     │
└─────────────────────────┬───────────────────────────────┘
                          │
          ┌───────────────┼───────────────┐
          ▼               ▼               ▼
    ┌──────────┐    ┌──────────┐    ┌──────────┐
    │  API 节点1 │    │  API 节点2 │    │  API 节点3 │
    └─────┬─────┘    └─────┬─────┘    └─────┬─────┘
          │               │               │
          └───────────────┼───────────────┘
                          │
    ┌─────────────────────┼─────────────────────┐
    │                     │                     │
    ▼                     ▼                     ▼
┌────────┐          ┌────────┐          ┌────────┐
│ MySQL  │          │ Redis  │          │ChromaDB│
│ (主从) │          │(集群)  │          │(副本)  │
└────────┘          └────────┘          └────────┘
```

**关键设计**：

| 组件 | 高可用策略 |
|------|-----------|
| **API 服务** | 多实例部署 + 负载均衡 |
| **MySQL** | 主从复制 + 自动切换 |
| **Redis** | 主从 + 哨兵/集群模式 |
| **ChromaDB** | 本地存储，可扩展为云服务 |
| **LLM API** | 多服务商备份（DeepSeek + OpenAI） |

**容错机制**：
```python
async def call_llm_with_fallback(question, context):
    try:
        return await deepseek_client.generate(question, context)
    except DeepSeekError:
        logger.warning("DeepSeek 失败，切换到 OpenAI")
        return await openai_client.generate(question, context)
```

---

### Q12: 如何优化 RAG 系统的检索质量？

**参考答案：**

**1. 混合检索**
```python
# 向量检索
vector_results = vector_store.search_vectors(query_embedding, n_results=10)

# 关键词检索（可选）
keyword_results = keyword_search(query, index)

# 结果融合
combined_results = rank_fusion(vector_results, keyword_results)
```

**2. 重排序（Rerank）**
```python
# 第一阶段：快速向量检索（Top 100）
initial_results = vector_store.search(query_embedding, n_results=100)

# 第二阶段：精确重排序（Top 10）
reranked = cross_encoder.rerank(query, initial_results, top_k=10)
```

**3. 查询扩展**
```python
# 使用 LLM 生成相关查询
related_queries = llm.generate(f"""
基于这个问题生成3个相关的搜索查询：
问题：{question}
""")
```

**4. 相似度阈值调优**
```python
# 根据业务场景调整
THRESHOLDS = {
    "strict": 0.7,   # 高精度场景
    "normal": 0.5,   # 一般场景
    "relaxed": 0.3   # 高召回场景
}
```

**5. 元数据过滤**
```python
# 只检索特定文档
results = collection.query(
    query_embeddings=[query_vector],
    n_results=5,
    where={"file_type": "pdf"}  # 只检索 PDF
)
```

---

### Q13: 如何处理大文档和长文本？

**参考答案：**

**策略一：层级索引**
```python
class HierarchicalIndexer:
    def __init__(self):
        self.chunk_index = None      # 块级索引
        self.document_index = None   # 文档级索引

    def index(self, document, chunks):
        # 文档级向量（所有块拼接）
        doc_vector = self.compute_doc_embedding(document.content)

        # 块级向量
        chunk_vectors = [self.compute_chunk_embedding(c) for c in chunks]

        self.document_index.add(doc_vector)
        self.chunk_index.add_many(chunk_vectors)

    def search(self, query):
        # 先检索文档
        doc_results = self.document_index.search(query, top_k=3)

        # 再在文档内检索块
        for doc in doc_results:
            local_chunks = self.chunk_index.search(query, top_k=3,
                                                   filter={"doc_id": doc.id})
```

**策略二：滑动窗口 + 重叠**
```python
def sliding_window_split(text, window_size=500, overlap=50):
    chunks = []
    start = 0
    while start < len(text):
        end = start + window_size
        chunk = text[start:end]
        chunks.append(chunk)
        start = end - overlap  # 滑动窗口
    return chunks
```

**策略三：摘要引导检索**
```python
# 为每个文档生成摘要
summary = llm.summarize(document.content)

# 存储摘要向量
doc_summary_vector = embedding.encode(summary)

# 检索时先匹配摘要
summary_match = vector_store.search(summary_vector, top_k=3)

# 再在匹配的文档中检索具体内容
```

---

## 5. 性能优化问题

### Q14: 如何提升 RAG 系统的响应速度？

**参考答案：**

**1. 缓存优化**
```python
# 多级缓存
class MultiLevelCache:
    def __init__(self):
        self.l1 = InMemoryCache()  # 内存缓存（微秒级）
        self.l2 = RedisCache()    # Redis 缓存（毫秒级）

    def get(self, key):
        result = self.l1.get(key)
        if result:
            return result

        result = self.l2.get(key)
        if result:
            self.l1.set(key, result)  # 回填 L1
        return result
```

**2. 向量检索优化**
```python
# 使用更快的模型
model = SentenceTransformer("all-MiniLM-L6-v2")  # 384 维
# vs
model = SentenceTransformer("BAAI/bge-large-zh-v1.5")  # 1024 维

# 预计算 + 缓存 Embedding
embedding_cache = {}

def get_embedding(text):
    key = hash(text)
    if key not in embedding_cache:
        embedding_cache[key] = model.encode(text)
    return embedding_cache[key]
```

**3. 并行处理**
```python
# 并行向量化和存储
async def process_document(file_path):
    # 1. 解析文档
    content = parser.parse(file_path)

    # 2. 并行处理
    chunks_task = asyncio.to_thread(split_text, content)
    embed_task = asyncio.to_thread(compute_embeddings, content)

    chunks, embeddings = await asyncio.gather(chunks_task, embed_task)

    # 3. 批量存储
    vector_store.add_batch(embeddings, chunks)
```

**4. 索引优化**
```python
# ChromaDB HNSW 参数调优
collection = client.create_collection(
    name="knowledge",
    metadata={"hnsw:space": "cosine"}  # 余弦相似度
)
```

---

### Q15: 如何降低 LLM API 的调用成本？

**参考答案：**

**1. 缓存重复问题**
```python
# 问题指纹
question_fingerprint = hashlib.md5(
    (question + str(session_id)).encode()
).hexdigest()

# 缓存查询
cached = redis.get(f"qa:{question_fingerprint}")
if cached:
    return json.loads(cached)
```

**2. 压缩 Prompt**
```python
# 截取关键上下文
context = "\n\n".join([
    f"[来源{i+1}] {chunk['content'][:500]}"
    for i, chunk in enumerate(top_chunks)
])
```

**3. 选择性价比模型**
```python
# 按场景选择模型
if question_type == "simple_fact":
    model = "deepseek-coder"  # 便宜快速
elif question_type == "complex_analysis":
    model = "deepseek-chat"   # 能力更强
```

**4. 拒绝无意义调用**
```python
# 问题太简单，直接返回
SIMPLE_PATTERNS = ["你好", "hi", "hello", "你是谁"]
if any(p in question.lower() for p in SIMPLE_PATTERNS):
    return "您好！有什么可以帮助您的吗？"
```

---

## 6. 项目经验总结

### 6.1 技术成长

| 技术 | 学习要点 |
|------|----------|
| **FastAPI** | 异步编程、中间件、依赖注入 |
| **向量数据库** | ANN 算法、相似度计算、Embedding |
| **RAG 架构** | 检索+生成、Prompt 工程、结果评估 |
| **系统设计** | 分层架构、缓存策略、容错机制 |

### 6.2 遇到的问题及解决方案

| 问题 | 解决方案 |
|------|----------|
| 中文文档检索效果差 | 使用支持中文的 Embedding 模型 |
| LLM 幻觉问题 | 严格过滤低相似度检索结果 |
| API 响应慢 | Redis 缓存 + 批量处理 |
| 文件编码问题 | UTF-8 标准化 + 错误处理 |
| 向量检索召回率低 | 调整 chunk_size 和 overlap |

### 6.3 项目亮点总结

1. **完整的 RAG 流程**：文档解析 → 文本切分 → 向量化 → 检索 → 生成
2. **生产级架构**：分层设计、异常处理、日志审计
3. **性能优化**：多级缓存、批量处理、异步 I/O
4. **可扩展性**：运行时配置、模块化设计
5. **运维友好**：健康检查、统计监控、操作日志

### 6.4 面试加分项

| 加分点 | 说明 |
|--------|------|
| 向量数据库原理 | 理解 HNSW、LSH 等 ANN 算法 |
| RAG 优化技巧 | Hybrid Search、Rerank、Query Rewrite |
| LLM 工程经验 | Prompt 优化、Token 控制、错误处理 |
| 系统设计能力 | 高可用、可扩展、成本控制 |

---

## 附录：推荐阅读

### 论文
- [Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks](https://arxiv.org/abs/2005.11401)
- [Dense Passage Retrieval for Open-Domain Question Answering](https://arxiv.org/abs/2004.04906)

### 工具
- [ChromaDB](https://docs.trychroma.com/)
- [sentence-transformers](https://www.sbert.net/)
- [LangChain](https://python.langchain.com/)

### 实践
- 尝试不同的 Embedding 模型
- 实验不同的 chunk_size 和 overlap
- 评估不同相似度阈值的效果
- 对比不同 LLM 的回答质量

---

*本文档由 Cursor Agent 生成，供项目复盘和面试准备使用*
