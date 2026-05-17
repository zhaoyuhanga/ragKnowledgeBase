# RAG 生产级知识库升级建议

生成时间：2026-05-18

## 1. 当前代码现状

本项目后端位于 `rag-qa-system/`，已经具备基础 RAG 闭环：文档上传、解析、切分、Embedding、Milvus 向量入库、Redis QA 缓存、DeepSeek 生成回答和 SSE 流式输出。

关键观察：


| 模块        | 当前实现                                                                                              | 主要问题                                                    |
| --------- | ------------------------------------------------------------------------------------------------- | ------------------------------------------------------- |
| Embedding | `app/config.py` 默认 `moka-ai/m3e-base`，维度 768；`embedding_service.py` 使用 `SentenceTransformer` 本地推理 | **计划删除此代码**，切换到 Ollama 部署的 `Qwen3-Embedding-4B`         |
| 向量库       | `app/core/vectorstore.py` 使用 Milvus，默认 `IVF_FLAT` + `IP`，`nprobe=16` 固定                           | 适合 Demo，不适合高并发和大规模数据；缺少按租户/知识库隔离、分区、索引参数分级配置            |
| 检索链路      | QA 中 `encode_single -> search_vectors -> 拼上下文 -> LLM`                                             | 只有单路 dense 检索；没有 BM25/稀疏检索、query rewrite、reranker、上下文压缩 |
| 重排        | 有 MMR 开关，但 `_mmr_rerank` 依赖未返回的 embedding 字段，且不是语义 reranker                                       | MMR 只能做多样性去重，不能替代 cross-encoder reranker                |
| 分块        | `TextSplitter` 主要按双换行、句子、字符兜底切分                                                                   | 对中文文档标题层级、表格、列表、代码块、页码、章节路径保留不足                         |
| 入库流程      | 上传接口内同步完成解析、切分、Embedding、Milvus 写入                                                                | 大文件和高并发上传会阻塞 API；缺少任务队列、幂等、断点续建和失败重试                    |
| 并发基础      | FastAPI + 同步 SQLAlchemy + Redis 缓存                                                                | 万级并发需要模型服务化、异步化、限流、队列、横向扩展和熔断降级                         |


## 2. Embedding 升级到 Qwen3-Embedding-4B

### 2.1 部署方式

**已在 Docker 中通过 Ollama 部署模型：**

```bash
# 模型：bantai/qwen3-embedding:4b-q6（量化版本，4B 参数）
# 端点：http://localhost:11434/api/embeddings

# 测试验证
curl http://localhost:11434/api/embeddings \
  -H "Content-Type: application/json" \
  -d '{"model":"bantai/qwen3-embedding:4b-q6","prompt":"hello"}'
```

**向量维度：** 3840（4B 模型默认输出维度）

建议目标：

- 模型：`Qwen/Qwen3-Embedding-4B`（通过 Ollama 部署）
- 向量维度：3840
- 相似度：保留 `IP`（内积），需 normalize 后使用
- 调用方式：HTTP REST API (`http://localhost:11434/api/embeddings`)

必须修改点：

1. 配置层
  - `EMBEDDING_MODEL=bantai/qwen3-embedding:4b-q6`（Ollama 模型名）
  - `EMBEDDING_DIMENSION=3840`
  - `EMBEDDING_PROVIDER=ollama`
  - `EMBEDDING_BASE_URL=http://localhost:11434`
  - 增加 `EMBEDDING_TIMEOUT`、`EMBEDDING_MAX_RETRIES`
2. 代码修改
  - **删除** `app/services/embedding_service.py` 中的 `SentenceTransformer` 本地推理代码
  - **删除** `moka-ai/m3e-base` 相关依赖和初始化逻辑
  - **新增** Ollama HTTP 调用方式，使用 `httpx` 调用 embedding API
  - 批量编码时需循环调用或使用 Ollama 的 batch API
3. Milvus schema
  - 当前 collection 的 `embedding` dim 是启动时读取 `settings.embedding_dimension` 创建的。
  - **直接重建 collection**，768 -> 3840 不兼容，删除旧 collection 重建。
  - 可直接使用同名 collection，但必须先删除重建。
4. 数据迁移策略（直接重建，无需灰度）
  - 由于旧 collection 直接删除重建，无需双写/双读策略。
  - 历史文档需重新上传并处理。

### 2.2 清理脚本

在重建索引前，需执行以下清理操作：

```sql
-- =============================================
-- 清理数据库 SQL 脚本
-- 执行前请备份数据！
-- =============================================

-- 1. 清空 documents 表（会级联删除 document_chunks）
TRUNCATE TABLE documents;

-- 或选择性删除（保留 AI 生成文档）
DELETE FROM documents WHERE source_type = 'local';

-- 2. 清空 qa_logs 表（问答历史）
TRUNCATE TABLE qa_logs;

-- 3. 重置 document 相关的索引（如需要）
-- ALTER TABLE documents AUTO_INCREMENT = 1;
-- ALTER TABLE document_chunks AUTO_INCREMENT = 1;
```

```python
# =============================================
# 清理缓存脚本（Redis）
# =============================================

import redis

r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

# 1. 清空所有 RAG 相关缓存
patterns = [
    'qa:*',           # 问答缓存
    'doc:*',          # 文档缓存
    'embed:*',        # Embedding 缓存
    'session:*',      # 会话缓存
]

for pattern in patterns:
    keys = r.keys(pattern)
    if keys:
        r.delete(*keys)
        print(f"Deleted {len(keys)} keys matching '{pattern}'")

# 2. 清空所有缓存
# r.flushdb()  # 注意：这会清空整个数据库

print("Cache cleared successfully")
```

```bash
# =============================================
# Milvus Collection 重建脚本
# =============================================

# 连接到 Milvus 并删除旧 collection
python << 'EOF'
from pymilvus import connections, utility

connections.connect(host="localhost", port="19530")

collection_name = "knowledge_base"

# 检查并删除旧 collection
if utility.has_collection(collection_name):
    print(f"Dropping collection: {collection_name}")
    utility.drop_collection(collection_name)
    print(f"Collection '{collection_name}' dropped")
else:
    print(f"Collection '{collection_name}' does not exist")

connections.disconnect("default")
EOF
```

### 2.3 部署验证

```bash
# 验证 Ollama 服务状态
curl http://localhost:11434/api/tags

# 验证模型加载
curl http://localhost:11434/api/embeddings \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"model":"bantai/qwen3-embedding:4b-q6","prompt":"测试中文嵌入"}'
```

## 3. 补上 Reranker

推荐链路：

```text
用户问题
  -> query rewrite / query expansion
  -> dense recall: Qwen3-Embedding-4B + Milvus top 50-100
  -> sparse recall: BM25 / SPLADE / Milvus sparse top 50-100
  -> fusion: RRF / weighted score
  -> reranker: Qwen3-Reranker-4B 或轻量 reranker top 20-50
  -> context compression
  -> LLM answer
```

落地建议：


| 优先级 | 能力                     | 建议                                                       |
| --- | ---------------------- | -------------------------------------------------------- |
| P0  | Cross-encoder reranker | 新增 `RerankService`，输入 `query + candidate chunks`，输出相关性分数 |
| P0  | 候选召回数量                 | 向量召回不要只取最终 top_k，先召回 50-100 条，rerank 后输出 5-10 条          |
| P0  | 模型选择                   | GPU 足够用 `Qwen3-Reranker-4B`；延迟敏感先用 0.6B 或商用 rerank API   |
| P1  | 分数融合                   | dense、sparse、reranker 分数统一归一化，最终排序可解释                    |
| P1  | 降级策略                   | reranker 超时后退化为融合召回排序，不能阻断问答                             |
| P1  | 批处理                    | 同一查询下多个候选 chunk 合批 rerank，避免逐条调用                         |


需要注意：

- MMR 继续保留用于去重和多样性，但不能作为最终相关性排序。
- Reranker 输入应包含 chunk 的标题路径、表格标题、列表上下文，不只传裸文本。
- 线上必须记录 reranker 前后排序，用于调参和质量评估。

参考来源：

- Milvus 官方文档支持 Hybrid Search，并用 reranking 合并多路向量搜索结果：[https://milvus.io/docs/v2.4.x/multi-vector-search.md](https://milvus.io/docs/v2.4.x/multi-vector-search.md)
- Milvus reranking 文档说明 reranking 是混合搜索中整合多路结果、提升相关性的关键步骤：[https://blog.milvus.io/docs/reranking.md](https://blog.milvus.io/docs/reranking.md)

## 4. 中文语义分块策略

当前 `TextSplitter` 的问题是"先按长度，再按标点兜底"，容易把中文文档的标题、列表、表格关系切碎。建议升级为"结构优先，长度约束兜底"。

推荐策略：

1. 文档解析阶段保留结构
  - Markdown：保留 `# / ## / ###` 标题层级。
  - DOCX：读取 paragraph style，识别 `Heading 1/2/3`；表格转 Markdown table。
  - PDF：优先使用版面解析工具提取标题、段落、表格、页码和坐标，必要时 OCR。
2. 分块单位
  - 标题块：按标题层级形成 section，chunk metadata 写入 `title_path`。
  - 段落块：自然段合并到目标 token 范围。
  - 表格块：完整表格优先不拆；大表按表头 + 若干行分块，每块重复表头。
  - 列表块：同一列表整体保留，超长列表按列表项切，但保留列表标题。
  - 代码块/命令块：完整保留，避免按普通句子切。
3. 长度控制
  - 使用 token 计数，不再只按字符数。
  - 中文知识库建议初始值：`400-800 tokens/chunk`，`80-120 tokens overlap`。
  - 对"定义/FAQ/规章制度"用更小 chunk；对"教程/架构文档/论文"用 parent-child chunk。
4. 上下文增强
  - 每个 chunk 前拼接轻量标题路径，例如：`文档 > 一级标题 > 二级标题`。
  - metadata 保存 `section_id`、`parent_chunk_id`、`page_no`、`table_id`、`list_id`。
  - 检索命中 child chunk 后，可回填 parent section 作为生成上下文。

推荐分块流程：

```text
Parser 输出结构化 DocumentNode
  -> 按标题树构建 Section
  -> Section 内识别段落/表格/列表/代码块
  -> token budget 合并相邻语义单元
  -> 超长单元按专用规则拆分
  -> 生成 chunk + metadata + parent-child 关系
```

## 5. 面向生产级 RAG 的技术升级建议

### 5.1 检索质量


| 能力                     | 建议                               |
| ---------------------- | -------------------------------- |
| 混合检索                   | Dense + BM25/Sparse，使用 RRF 或加权融合 |
| Query Rewrite          | 对口语化、上下文问题做独立查询改写；多轮对话先改写再检索     |
| Multi-query            | 针对复杂问题生成 2-4 个检索子查询并行召回          |
| Parent-child retrieval | 小 chunk 做召回，大 section 做上下文       |
| Metadata filter        | 按知识库、租户、文档类型、时间、权限过滤             |
| Context compression    | 对 rerank 后内容再做去重、摘要、事实句抽取        |
| 引用精确性                  | 答案引用到 chunk、页码、标题路径，支持前端跳转原文     |


### 5.2 文档处理


| 能力    | 建议                                                       |
| ----- | -------------------------------------------------------- |
| 解析质量  | 引入 MinerU / Unstructured / Docling 一类版面解析，表格和扫描 PDF 单独处理 |
| OCR   | 对图片型 PDF 使用 OCR，保存置信度                                    |
| 增量索引  | 用 `content_hash + chunk_hash` 判断变更，只重算变动 chunk           |
| 入库任务化 | 上传只落库和入队，后台 worker 解析、切分、向量化、写库                          |
| 幂等与重试 | 每个文档处理任务有状态机、重试次数、死信队列                                   |
| 数据版本  | 保存 parser 版本、chunker 版本、embedding 版本，便于回滚和重建             |


### 5.3 万级并发架构

"万级并发"要拆成两个指标：并发连接数和实际 QPS。RAG 的瓶颈通常不是 HTTP，而是 embedding、reranker、LLM、Milvus 和数据库连接。

建议目标架构：

```text
Client
  -> CDN / API Gateway / WAF
  -> Load Balancer
  -> FastAPI stateless pods
  -> Redis Cluster: cache, session, rate limit
  -> Retrieval Service: embedding client, Milvus client, reranker client
  -> Model Serving: embedding GPU pool, reranker GPU pool, LLM provider
  -> Milvus Cluster
  -> MySQL primary/replica or TiDB/PostgreSQL
  -> Async Workers: document parsing, indexing, eval jobs
```

必须升级：


| 层      | 建议                                                        |
| ------ | --------------------------------------------------------- |
| API    | 多 worker + 多 pod 横向扩展；SSE 连接与重计算解耦                        |
| DB     | 当前同步 SQLAlchemy 可先保留，但需要读写分离、连接池治理、慢查询治理                  |
| Redis  | 单机改 Redis Cluster/Sentinel；缓存键加入知识库版本和权限上下文               |
| Milvus | standalone 改 cluster；按租户/知识库分区；根据规模选择 HNSW/IVF_PQ/DISKANN |
| 模型     | embedding/reranker/LLM 服务化，限流、超时、重试、熔断、批处理                |
| 队列     | Celery/RQ/Arq/Kafka/RabbitMQ，承接文档入库和离线重建                  |
| 网关     | 认证、限流、配额、黑白名单、请求体大小限制                                     |
| 缓存     | QA 缓存、embedding 缓存、检索结果缓存、rerank 结果缓存                     |
| 降级     | reranker 超时降级，LLM 超时返回检索摘要或排队提示                           |


### 5.4 性能优化


| 场景           | 建议                                   |
| ------------ | ------------------------------------ |
| 查询 embedding | 缓存 query embedding；相同问题和相似问题命中缓存     |
| 批量 embedding | 入库侧按 batch 调用模型服务，避免逐 chunk 请求       |
| 向量检索         | 调优 `nprobe`、索引类型、topK、分区过滤；区分在线和离线索引 |
| Reranker     | 候选上限 20-50；超时 200-500ms；低价值请求可跳过     |
| Prompt       | 控制上下文 token；按引用质量动态裁剪                |
| SSE          | 长连接单独部署或调优 worker，避免占满计算 worker      |


### 5.5 安全与多租户


| 能力          | 建议                                                         |
| ----------- | ---------------------------------------------------------- |
| 权限过滤        | 检索前必须按用户、租户、知识库、文档权限过滤                                     |
| 数据隔离        | metadata 强制写入 `tenant_id`、`kb_id`；Milvus 分区或 collection 隔离 |
| 敏感信息        | 文档入库前做 PII 检测与脱敏策略                                         |
| Prompt 注入防护 | 系统提示明确忽略文档中的指令；对检索内容做来源标记                                  |
| 审计          | 记录谁问了什么、引用了哪些文档、模型生成了什么                                    |
| 删除合规        | 文档删除要同时删除 MySQL、Milvus、缓存、对象存储，并记录审计                       |


### 5.6 质量评估与可观测性

必须建立 RAG 评估闭环：


| 指标                  | 建议                                           |
| ------------------- | -------------------------------------------- |
| Recall@K            | 人工标注问题集，评估检索是否召回正确 chunk                     |
| MRR / NDCG          | 评估排序质量，尤其是 reranker 上线前后                     |
| Answer Faithfulness | 答案是否被引用内容支持                                  |
| Citation Accuracy   | 引用是否指向正确原文                                   |
| Latency             | 分段记录 embedding、Milvus、rerank、LLM、DB、cache 耗时 |
| Cost                | 每次问答 token、模型调用次数、GPU 利用率                    |
| Drift               | 文档更新、模型版本、chunker 版本导致的质量变化                  |


推荐工具：

- OpenTelemetry + Prometheus + Grafana：指标链路
- ELK / Loki：日志聚合
- Langfuse / Phoenix / Ragas：RAG 质量追踪与评估
- 压测：Locust / k6，分别压普通 JSON API 和 SSE 问答流

## 6. 分阶段路线图

### Phase 1：Embedding 升级（Ollama + Qwen3-Embedding-4B）

- 删除 `embedding_service.py` 中的 `SentenceTransformer` 和 `moka-ai/m3e-base` 代码
- 新增 Ollama HTTP 调用适配器
- 更新配置项 `EMBEDDING_PROVIDER=ollama`、`EMBEDDING_DIMENSION=3840`
- 提供清理脚本（数据库 truncate、Redis flush、Milvus drop collection）
- 重建 Milvus collection（3840 维）
- 验证 Ollama embedding API 正常工作

### Phase 2：中文结构化分块

- 重写 parser 输出结构化节点。
- 实现标题层级、段落、表格、列表的语义分块。
- chunk metadata 增加 `title_path`、`section_id`、`page_no`、`chunk_hash`。
- 支持 parent-child retrieval。

### Phase 3：生产化入库与索引

- 上传接口改为异步任务入队。
- 增加任务状态、重试、死信队列、断点续建。
- 支持增量索引和版本化重建。
- Milvus standalone 升级为 cluster，索引参数可按 collection 配置。

### Phase 4：万级并发能力

- API、retrieval、embedding、reranker 拆成独立服务。
- Redis Cluster + 限流 + 多级缓存。
- 增加熔断、降级、超时预算。
- 使用 k6/Locust 做容量测试，输出 QPS、P95/P99、错误率和资源水位。

## 7. 推荐优先级清单


| 优先级 | 事项                                        | 原因                                              |
| --- | ----------------------------------------- | ----------------------------------------------- |
| P0  | Embedding 切换到 Ollama + Qwen3-Embedding-4B | 通过 Ollama 部署，删除 SentenceTransformer/m3e-base 代码 |
| P0  | 重建 Milvus Collection (3840 维)             | 维度变化必须重建，清理旧数据                                  |
| P0  | 新增真正的 reranker                            | 对中文 RAG 准确率提升通常比单纯调 topK 更明显                    |
| P0  | 重做中文结构化分块                                 | 当前长度分块会破坏标题、表格、列表语义                             |
| P0  | 入库异步任务化                                   | 当前上传链路会被大文件和 embedding 阻塞                       |
| P1  | 清理脚本（数据库/缓存/Milvus）                       | 重建前必须清理旧数据                                      |
| P1  | 混合检索 Dense + BM25/Sparse                  | 提升专有名词、编号、命令、代码类查询召回                            |
| P1  | 评估集与指标仪表盘                                 | 没有评估无法判断模型和分块升级是否真的有效                           |
| P2  | 多租户权限过滤与审计                                | 生产知识库必须保证数据隔离和可追溯                               |
| P2  | 上下文压缩与引用校验                                | 降低幻觉，提高答案可解释性                                   |


## 8. Cursor 任务拆分建议

可以按以下任务卡片派发到 `tasks/queue/`：

1. `TASK-004-qwen3-embedding-ollama.md`
  - 删除 `embedding_service.py` 中的 `SentenceTransformer` 和 `moka-ai/m3e-base` 代码
  - 新增 Ollama HTTP 调用方式
  - 更新配置项 `EMBEDDING_PROVIDER=ollama`
  - 验收：可通过 Ollama API 生成 3840 维向量
2. `TASK-005-rebuild-milvus-collection.md`
  - 删除旧 Milvus collection，重建 3840 维 schema
  - 提供清理脚本（数据库 truncate、Redis flush、Milvus drop）
  - 验收：旧 collection 被删除，新 collection 可正常入库和检索
3. `TASK-006-add-rerank-service.md`
  - 新增 reranker 配置与 `RerankService`
  - QA 检索链路改为先召回 topN，再 rerank topK
  - 验收：reranker 可开关、超时可降级、日志记录前后排序
4. `TASK-007-structure-aware-chinese-chunker.md`
  - 改造 parser/chunker，支持标题层级、段落、表格、列表
  - chunk metadata 增加标题路径和结构字段
  - 验收：Markdown/DOCX 表格和列表不被无意义截断
5. `TASK-008-async-indexing-pipeline.md`
  - 上传接口只创建文档记录和任务
  - 后台 worker 处理解析、分块、向量化、入库
  - 验收：大文件上传不阻塞 API，失败任务可重试
6. `TASK-009-rag-observability-and-evaluation.md`
  - 增加检索、rerank、LLM 分段耗时日志
  - 新增离线评估脚本和评估集格式
  - 验收：可输出 Recall@K、MRR、P95/P99 延迟

