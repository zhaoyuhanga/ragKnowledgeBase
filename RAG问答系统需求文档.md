# RAG 问答系统需求文档

**版本：** V1.0  
**日期：** 2026-05-13  
**状态：** 初稿  

---

## 1. 项目概述

### 1.1 项目背景

本项目旨在构建一个基于检索增强生成（RAG）技术的本地问答系统，可针对私有文档（PDF、Markdown、TXT）进行智能问答。项目定位为可运行的 RAG Demo，作为技术能力展示及春招项目储备。

### 1.2 项目目标

- 实现私有文档的智能化问答功能
- 支持多种文档格式的解析与处理
- 提供友好的 API 接口供前端调用
- 演示 RAG 技术的完整落地流程

### 1.3 RAG 核心流程

RAG（Retrieval-Augmented Generation）的核心思路是：将私有文档切分后存入向量数据库，用户提问时先检索最相关的文档片段，再把检索到的内容作为上下文传给大模型进行回答。

```
┌─────────────────────────────────────────────────────────────────┐
│  离线阶段：构建知识库                                            │
├─────────────────────────────────────────────────────────────────┤
│  原始文档（PDF/MD/TXT）→ 文本加载 → 文本切分(Chunk) → Embedding  │
│                                    ↓                            │
│                           向量数据库(ChromaDB) + MySQL元数据     │
└─────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────┐
│  在线阶段：问答                                                  │
├─────────────────────────────────────────────────────────────────┤
│  用户提问 → Embedding → 向量检索(ChromaDB) → 获取相关文本块     │
│                                    ↓                            │
│                拼接Prompt → DeepSeek API → 生成回答 → 返回用户  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. 技术选型


| 组件            | 选型                                     | 说明                              |
| ------------- | -------------------------------------- | ------------------------------- |
| **编程语言**      | Python 3.12                            | 语法简洁，AI/ML 生态丰富                 |
| **LLM**       | DeepSeek API (deepseek-v4-flash)       | 兼容 OpenAI SDK，百万 token 上下文，成本极低 |
| **Embedding** | sentence-transformers/all-MiniLM-L6-v2 | 本地运行，免费，无需 API 调用，维度 384，体积小速度快 |
| **向量数据库**     | ChromaDB                               | 轻量级，纯 Python，零配置启动，适合本地开发和原型验证  |
| **元数据管理**     | MySQL 8.0                              | 存储文档信息、分块映射、QA 日志               |
| **缓存**        | Redis                                  | 缓存热点问答，降低 API 调用成本与延迟           |
| **Web 框架**    | FastAPI                                | 高性能，自动生成 API 文档，异步支持            |


---

## 3. 功能需求

### 3.1 文档管理模块


| 功能点  | 优先级 | 描述                          |
| ---- | --- | --------------------------- |
| 文档上传 | P0  | 支持 PDF、Markdown、TXT 格式文件上传  |
| 文档解析 | P0  | 提取文本内容，保留关键结构信息             |
| 文档列表 | P1  | 展示已上传文档的基本信息（名称、类型、大小、上传时间） |
| 文档删除 | P1  | 删除指定文档及其关联的向量数据             |
| 文档预览 | P2  | 支持在线预览文档内容（文本部分）            |


### 3.2 知识库构建模块


| 功能点    | 优先级 | 描述                            |
| ------ | --- | ----------------------------- |
| 文本切分   | P0  | 支持多种切分策略（按段落、按长度、自定义）         |
| 切分参数配置 | P1  | 支持配置 chunk_size、chunk_overlap |
| 向量化存储  | P0  | 将文本块转换为向量并存入 ChromaDB         |
| 元数据存储  | P0  | 在 MySQL 中记录文档与向量的映射关系         |
| 增量索引   | P2  | 支持对新上传文档增量添加到现有知识库            |
| 重建索引   | P2  | 支持清空并重新构建整个知识库                |


### 3.3 问答模块


| 功能点   | 优先级 | 描述                                      |
| ----- | --- | --------------------------------------- |
| 智能问答  | P0  | 接收用户问题，返回基于知识库的回答                       |
| 向量检索  | P0  | 使用 Embedding 模型将问题向量化，从 ChromaDB 检索相似内容 |
| 上下文拼接 | P0  | 将检索结果作为上下文拼接至 Prompt                    |
| 回答生成  | P0  | 调用 DeepSeek API 生成最终回答                  |
| 引用来源  | P1  | 返回回答所依据的文档片段及来源                         |
| 多轮对话  | P2  | 支持基于上下文的连续追问                            |


### 3.4 缓存模块


| 功能点    | 优先级 | 描述            |
| ------ | --- | ------------- |
| 问题缓存   | P1  | 缓存常见问题及回答     |
| 检索结果缓存 | P2  | 缓存向量检索结果      |
| 缓存管理   | P2  | 提供手动刷新、清空缓存接口 |


### 3.5 系统管理模块


| 功能点  | 优先级 | 描述                 |
| ---- | --- | ------------------ |
| 健康检查 | P0  | 检查数据库、向量库、API 连接状态 |
| 统计信息 | P1  | 展示文档数量、向量数量、问答次数等  |
| 日志记录 | P1  | 记录问答日志，便于分析和优化     |


---

## 4. 非功能需求

### 4.1 性能需求


| 指标       | 要求                  |
| -------- | ------------------- |
| 文档上传响应时间 | ≤ 5s（单文件 ≤ 10MB）    |
| 问答响应时间   | ≤ 10s（不含 API 超时）    |
| 向量检索召回率  | Top-K 相关文档召回率 ≥ 80% |
| 系统并发支持   | 支持 10+ 并发请求         |


### 4.2 可用性需求

- 系统支持 Docker Compose 一键部署
- 配置文件集中管理，便于环境切换
- 完善的错误处理与异常提示

### 4.3 可扩展性需求

- 模块化设计，便于替换底层组件（如换用其他向量数据库）
- 支持配置化切换 LLM provider（预留接口）
- 数据库设计预留扩展字段

### 4.4 安全性需求

- API 请求支持基础认证
- 敏感配置通过环境变量注入
- 用户输入做必要的安全过滤

---

## 5. 数据模型设计

### 5.1 MySQL 表结构

#### 5.1.1 文档表 (documents)


| 字段           | 类型           | 说明                      |
| ------------ | ------------ | ----------------------- |
| id           | BIGINT       | 主键，自增                   |
| filename     | VARCHAR(255) | 文件名                     |
| file_path    | VARCHAR(512) | 文件存储路径                  |
| file_type    | VARCHAR(50)  | 文件类型 (pdf/md/txt)       |
| file_size    | BIGINT       | 文件大小（字节）                |
| content_hash | VARCHAR(64)  | 文件内容哈希，用于去重             |
| status       | TINYINT      | 状态 (0=处理中, 1=已完成, 2=失败) |
| chunk_count  | INT          | 切分块数量                   |
| created_at   | DATETIME     | 上传时间                    |
| updated_at   | DATETIME     | 更新时间                    |


#### 5.1.2 文档块表 (document_chunks)


| 字段          | 类型          | 说明                |
| ----------- | ----------- | ----------------- |
| id          | BIGINT      | 主键，自增             |
| document_id | BIGINT      | 外键，关联 documents 表 |
| chunk_index | INT         | 块序号               |
| content     | TEXT        | 文本内容              |
| char_count  | INT         | 字符数量              |
| vector_id   | VARCHAR(64) | ChromaDB 中的向量 ID  |
| created_at  | DATETIME    | 创建时间              |


#### 5.1.3 问答日志表 (qa_logs)


| 字段                | 类型       | 说明           |
| ----------------- | -------- | ------------ |
| id                | BIGINT   | 主键，自增        |
| question          | TEXT     | 用户问题         |
| answer            | TEXT     | 系统回答         |
| referenced_chunks | JSON     | 引用的文档块 ID 列表 |
| response_time_ms  | INT      | 响应耗时（毫秒）     |
| cache_hit         | BOOLEAN  | 是否命中缓存       |
| created_at        | DATETIME | 问答时间         |


### 5.2 ChromaDB Collection 设计

```python
Collection: "knowledge_base"

Fields:
  - id: str          # 自动生成的 UUID
  - embedding: float[384]  # 向量维度
  - document: str    # 文本内容
  - metadata:
      - document_id: int
      - chunk_index: int
      - filename: str
      - file_type: str
```

---

## 6. API 接口设计

### 6.1 文档管理


| 方法     | 路径                             | 描述     |
| ------ | ------------------------------ | ------ |
| POST   | /api/v1/documents/upload       | 上传文档   |
| GET    | /api/v1/documents              | 获取文档列表 |
| GET    | /api/v1/documents/{id}         | 获取文档详情 |
| DELETE | /api/v1/documents/{id}         | 删除文档   |
| GET    | /api/v1/documents/{id}/preview | 预览文档内容 |


### 6.2 知识库管理


| 方法   | 路径                              | 描述           |
| ---- | ------------------------------- | ------------ |
| POST | /api/v1/knowledge/rebuild       | 重建知识库索引      |
| GET  | /api/v1/knowledge/stats         | 获取知识库统计信息    |
| POST | /api/v1/knowledge/chunks/search | 手动检索相关块（调试用） |


### 6.3 问答


| 方法   | 路径                 | 描述     |
| ---- | ------------------ | ------ |
| POST | /api/v1/qa/ask     | 提交问答请求 |
| POST | /api/v1/qa/chat    | 多轮对话   |
| GET  | /api/v1/qa/history | 获取问答历史 |


### 6.4 系统


| 方法   | 路径                         | 描述   |
| ---- | -------------------------- | ---- |
| GET  | /api/v1/system/health      | 健康检查 |
| GET  | /api/v1/system/stats       | 系统统计 |
| POST | /api/v1/system/cache/clear | 清空缓存 |


---

## 7. 项目结构

```
rag-qa-system/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI 应用入口
│   ├── config.py               # 配置管理
│   ├── api/
│   │   ├── __init__.py
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── documents.py    # 文档管理接口
│   │   │   ├── knowledge.py    # 知识库接口
│   │   │   ├── qa.py           # 问答接口
│   │   │   └── system.py       # 系统接口
│   │   └── deps.py             # 依赖注入
│   ├── core/
│   │   ├── __init__.py
│   │   ├── database.py         # MySQL 连接
│   │   ├── vectorstore.py      # ChromaDB 操作
│   │   ├── cache.py            # Redis 操作
│   │   └── llm.py              # DeepSeek API 调用
│   ├── services/
│   │   ├── __init__.py
│   │   ├── document_service.py # 文档处理服务
│   │   ├── chunk_service.py    # 文本切分服务
│   │   ├── embedding_service.py # 向量化服务
│   │   ├── qa_service.py       # 问答服务
│   │   └── cache_service.py    # 缓存服务
│   ├── models/
│   │   ├── __init__.py
│   │   ├── document.py         # 文档数据模型
│   │   ├── chunk.py           # 文档块模型
│   │   └── qa.py              # 问答模型
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── document.py         # 文档请求/响应模型
│   │   ├── qa.py              # 问答请求/响应模型
│   │   └── common.py          # 通用响应模型
│   └── utils/
│       ├── __init__.py
│       ├── file_parser.py     # 文件解析工具
│       └── text_splitter.py   # 文本切分工具
├── tests/
│   ├── __init__.py
│   ├── test_documents.py
│   ├── test_knowledge.py
│   └── test_qa.py
├── data/
│   ├── documents/             # 文档存储目录
│   └── chroma/                # ChromaDB 数据目录
├── scripts/
│   └── init_db.sql            # 数据库初始化脚本
├── docker-compose.yml         # Docker 编排配置
├── Dockerfile                 # 应用容器镜像
├── requirements.txt           # Python 依赖
├── .env.example               # 环境变量示例
├── .gitignore
└── README.md
```

---

## 8. 配置项说明

### 8.1 环境变量配置 (.env)

```env
# 应用配置
APP_ENV=development
APP_HOST=0.0.0.0
APP_PORT=8000

# MySQL 配置
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_DATABASE=rag_qa
MYSQL_USER=root
MYSQL_PASSWORD=123456

# Redis 配置
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=

# DeepSeek API 配置
DEEPSEEK_API_KEY=sk-ddec373703d64cd39fe0f97275866b13
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-v4-flash

# ChromaDB 配置
CHROMA_PERSIST_DIR=./data/chroma

# 向量化模型配置
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_DEVICE=cpu

# 文本切分配置
CHUNK_SIZE=500
CHUNK_OVERLAP=50

# 向量检索配置
RETRIEVAL_TOP_K=5
```

---

## 9. 部署方案

### 9.1 Docker Compose 部署

```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - MYSQL_HOST=mysql
      - REDIS_HOST=redis
      - CHROMA_PERSIST_DIR=/app/data/chroma
    volumes:
      - ./data:/app/data
    depends_on:
      - mysql
      - redis
    restart: unless-stopped

  mysql:
    image: mysql:8.0
    environment:
      MYSQL_ROOT_PASSWORD: root_password
      MYSQL_DATABASE: rag_qa
    volumes:
      - mysql_data:/var/lib/mysql
    ports:
      - "3306:3306"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

volumes:
  mysql_data:
  redis_data:
```

---

## 10. 开发计划

### 阶段一：基础框架搭建 (预计 1 周)

- 项目结构初始化
- 配置文件与环境变量管理
- MySQL 数据库连接与表结构创建
- ChromaDB 初始化配置
- FastAPI 框架搭建与路由配置

### 阶段二：文档处理模块 (预计 1 周)

- 文件上传接口
- PDF 解析实现
- Markdown 解析实现
- TXT 解析实现
- 文档列表与删除功能

### 阶段三：知识库构建 (预计 1 周)

- Embedding 模型集成
- 文本切分策略实现
- 向量化存储流程
- 元数据关联存储
- 知识库重建功能

### 阶段四：问答功能 (预计 1 周)

- 问句向量化
- 相似度检索
- Prompt 模板设计
- DeepSeek API 集成
- 回答组装与返回

### 阶段五：优化与扩展 (预计 0.5 周)

- Redis 缓存集成
- 引用来源追溯
- API 文档完善
- Docker 部署脚本
- 单元测试编写

---

## 11. 风险评估与应对


| 风险项               | 可能性 | 影响  | 应对措施                 |
| ----------------- | --- | --- | -------------------- |
| DeepSeek API 调用超时 | 中   | 中   | 增加超时配置与重试机制，本地缓存结果   |
| 向量检索召回率低          | 中   | 高   | 优化切分策略，调整检索参数，尝试多路召回 |
| 大文件处理内存溢出         | 低   | 中   | 流式读取，限制文件大小，增加分块处理   |
| ChromaDB 数据丢失     | 低   | 高   | 定期备份，配置持久化存储         |


---

## 12. 附录

### 12.1 参考资料

- [ChromaDB 官方文档](https://docs.trychroma.com/)
- [sentence-transformers 文档](https://www.sbert.net/)
- [DeepSeek API 文档](https://platform.deepseek.com/)
- [FastAPI 中文文档](https://fastapi.tiangolo.com/zh/)

### 12.2 术语表


| 术语           | 说明                                    |
| ------------ | ------------------------------------- |
| RAG          | Retrieval-Augmented Generation，检索增强生成 |
| Chunk        | 文本切分后的最小单元                            |
| Embedding    | 将文本转换为向量的技术                           |
| Vector Store | 存储向量数据的数据库                            |
| Token        | 语言模型处理的最小单位                           |


---

*文档版本历史*


| 版本   | 日期         | 修改内容 | 作者  |
| ---- | ---------- | ---- | --- |
| V1.0 | 2026-05-13 | 初始版本 | -   |


