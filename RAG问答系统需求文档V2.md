# RAG 问答系统需求文档 V2

**版本：** V2.0  
**日期：** 2026-05-17  
**状态：** 正式版  
**项目类型：** 前后端分离 Web 应用（Vue 3 + FastAPI）

---

## 1. 项目概述

### 1.1 项目背景

本项目是一个基于检索增强生成（RAG）技术的本地知识库问答系统，支持对私有文档（PDF、Word、Markdown、TXT）进行智能问答。项目采用前后端分离架构，后端基于 FastAPI 构建 RESTful API，前端基于 Vue 3 构建单页应用。

### 1.2 项目目标

- 实现私有文档的智能化问答功能
- 支持多种文档格式的解析、处理与向量化存储
- 提供友好的 Web 界面和 RESTful API 接口
- 演示 RAG 技术的完整落地流程
- 支持流式输出，提升用户体验

### 1.3 技术架构

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           前端 (Vue 3 + Element Plus)                   │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐   │
│  │  登录   │  │ 仪表盘  │  │  问答   │  │  文档   │  │  知识库  │   │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘  └─────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼ HTTP/SSE
┌─────────────────────────────────────────────────────────────────────────┐
│                           后端 (FastAPI)                                │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │                        API Router                                 │  │
│  │  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐   │  │
│  │  │   认证    │  │   文档    │  │   问答    │  │   系统    │   │  │
│  │  └───────────┘  └───────────┘  └───────────┘  └───────────┘   │  │
│  └─────────────────────────────────────────────────────────────────┘  │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐            │
│  │   LLM 模块    │  │  向量存储模块  │  │   缓存模块    │            │
│  │  (DeepSeek)  │  │   (Milvus)   │  │   (Redis)    │            │
│  └───────────────┘  └───────────────┘  └───────────────┘            │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
        ┌────────────────────────────┼────────────────────────────┐
        ▼                            ▼                            ▼
┌───────────────┐          ┌───────────────┐          ┌───────────────┐
│   Milvus      │          │    MySQL      │          │    Redis     │
│  向量数据库    │          │   关系数据库   │          │    缓存      │
└───────────────┘          └───────────────┘          └───────────────┘
```

---

## 2. 技术选型

### 2.1 后端技术栈


| 组件            | 选型                    | 说明                 |
| ------------- | --------------------- | ------------------ |
| **编程语言**      | Python 3.12           | AI/ML 生态丰富         |
| **Web 框架**    | FastAPI               | 高性能，异步支持，自动 API 文档 |
| **ORM**       | SQLAlchemy            | 数据库 ORM 映射         |
| **LLM**       | DeepSeek API          | 兼容 OpenAI SDK，成本低  |
| **Embedding** | sentence-transformers | 本地运行，维度 384        |
| **向量数据库**     | Milvus                | 高性能向量检索，支持 MMR 重排序 |
| **元数据管理**     | MySQL 8.0             | 文档信息、分块映射、QA 日志    |
| **缓存**        | Redis                 | 问答缓存，降低 API 调用成本   |


### 2.2 前端技术栈


| 组件           | 选型           | 说明                        |
| ------------ | ------------ | ------------------------- |
| **框架**       | Vue 3        | 组合式 API (Composition API) |
| **UI 库**     | Element Plus | 企业级 Vue 3 UI 组件库          |
| **构建工具**     | Vite         | 快速开发与热更新                  |
| **状态管理**     | Pinia        | Vue 3 专属状态管理              |
| **路由**       | Vue Router 4 | 单页应用路由                    |
| **HTTP 客户端** | Axios        | API 请求                    |
| **Markdown** | marked       | Markdown 渲染               |


---

## 3. 功能需求

### 3.1 认证模块


| 功能点      | 优先级 | 描述                    |
| -------- | --- | --------------------- |
| 用户登录     | P0  | 用户名密码认证，返回 JWT Token  |
| Token 验证 | P0  | API 请求携带 Token 进行身份验证 |
| 会话管理     | P1  | Token 过期时间可配置         |


### 3.2 仪表盘模块


| 功能点    | 优先级 | 描述                    |
| ------ | --- | --------------------- |
| 统计数据展示 | P0  | 展示问答次数、文档数量、文档块数、今日问答 |
| 系统性能指标 | P0  | 显示缓存命中率、平均响应时间        |
| 快捷操作入口 | P0  | 一键跳转到问答、文档上传、索引重建等功能  |
| 数据刷新   | P1  | 支持手动刷新统计数据            |


### 3.3 文档管理模块


| 功能点  | 优先级 | 描述                   |
| ---- | --- | -------------------- |
| 文档上传 | P0  | 支持拖拽上传多个文件，显示上传进度    |
| 支持格式 | P0  | PDF、DOCX、DOC、TXT、MD  |
| 文档列表 | P0  | 分页展示、状态筛选、名称搜索       |
| 文档状态 | P0  | 处理中/已完成/失败 三种状态      |
| 文档预览 | P1  | Markdown 渲染，在线预览文本内容 |
| 文档删除 | P0  | 删除文档及其关联的向量数据        |
| 文档详情 | P1  | 查看文档基本信息、错误原因等       |


### 3.4 知识库管理模块


| 功能点   | 优先级 | 描述             |
| ----- | --- | -------------- |
| 知识库统计 | P0  | 文档数量、块数、向量数量统计 |
| 索引重建  | P0  | 清空并重新构建整个知识库索引 |
| 缓存管理  | P0  | 清空 Redis 问答缓存  |
| 检索测试  | P1  | 手动输入查询，查看检索结果  |


### 3.5 问答模块（核心功能）


| 功能点      | 优先级 | 描述                       |
| -------- | --- | ------------------------ |
| 智能问答     | P0  | 接收问题，返回基于知识库的回答          |
| 流式输出     | P0  | SSE 流式返回回答，边生成边展示        |
| 缓存命中     | P0  | 缓存问题快速返回，区分"命中缓存"和"实时生成" |
| 引用来源     | P1  | 返回回答依据的文档片段及相似度          |
| Top K 配置 | P1  | 可配置检索的文档块数量              |
| 问答历史     | P1  | 分页查看历史问答记录               |


#### 3.5.1 流式输出流程

```
用户提问 → 检查缓存 → [命中] → 流式返回缓存内容 → 显示"命中缓存"
                     ↓ [未命中]
              → 向量检索 → 获取相关文档块
                     ↓
              → 调用 DeepSeek API（流式）
                     ↓
              → 逐 token 流式返回 → 显示"实时生成"
                     ↓
              → 保存到缓存 → 完成
```

#### 3.5.2 缓存命中 vs 实时生成


| 场景   | 输出速度    | 标签显示   | 说明                   |
| ---- | ------- | ------ | -------------------- |
| 缓存命中 | 快速      | "命中缓存" | 直接从 Redis 返回         |
| 实时生成 | 取决于 LLM | "实时生成" | 调用 DeepSeek API 流式生成 |


### 3.6 系统设置模块


| 功能点    | 优先级 | 描述                                     |
| ------ | --- | -------------------------------------- |
| 健康检查   | P0  | 检查 MySQL、Redis、Milvus、LLM、Embedding 状态 |
| 系统配置管理 | P0  | 分组查看和编辑系统配置                            |
| 配置分组   | P1  | 按类别分组展示配置项                             |
| 运行时配置  | P1  | 动态调整检索、切分等参数                           |


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

- 支持 Docker Compose 一键部署
- 配置文件集中管理，便于环境切换
- 完善的错误处理与异常提示
- 系统状态实时监控

### 4.3 可扩展性需求

- 模块化设计，便于替换底层组件
- 支持配置化切换 LLM Provider
- 数据库设计预留扩展字段
- MMR（最大边际相关性）重排序支持

### 4.4 安全性需求

- API 请求支持 JWT Token 认证
- 敏感配置通过环境变量注入
- 用户输入做必要的安全过滤

---

## 5. 数据模型设计

### 5.1 MySQL 表结构

#### 5.1.1 文档表 (documents)


| 字段            | 类型           | 说明                      |
| ------------- | ------------ | ----------------------- |
| id            | BIGINT       | 主键，自增                   |
| filename      | VARCHAR(255) | 文件名                     |
| file_path     | VARCHAR(512) | 文件存储路径                  |
| file_type     | VARCHAR(50)  | 文件类型 (pdf/docx/txt/md)  |
| file_size     | BIGINT       | 文件大小（字节）                |
| content_hash  | VARCHAR(64)  | 内容哈希，用于去重               |
| status        | TINYINT      | 状态 (0=处理中, 1=已完成, 2=失败) |
| chunk_count   | INT          | 切分块数量                   |
| error_message | TEXT         | 错误信息（处理失败时）             |
| created_at    | DATETIME     | 上传时间                    |
| updated_at    | DATETIME     | 更新时间                    |


#### 5.1.2 文档块表 (document_chunks)


| 字段          | 类型          | 说明                |
| ----------- | ----------- | ----------------- |
| id          | BIGINT      | 主键，自增             |
| document_id | BIGINT      | 外键，关联 documents 表 |
| chunk_index | INT         | 块序号               |
| content     | TEXT        | 文本内容              |
| char_count  | INT         | 字符数量              |
| vector_id   | VARCHAR(64) | Milvus 中的向量 ID    |
| created_at  | DATETIME    | 创建时间              |


#### 5.1.3 问答日志表 (qa_logs)


| 字段                | 类型          | 说明           |
| ----------------- | ----------- | ------------ |
| id                | BIGINT      | 主键，自增        |
| question          | TEXT        | 用户问题         |
| answer            | TEXT        | 系统回答         |
| referenced_chunks | JSON        | 引用的文档块 ID 列表 |
| response_time_ms  | INT         | 响应耗时（毫秒）     |
| cache_hit         | BOOLEAN     | 是否命中缓存       |
| session_id        | VARCHAR(64) | 会话 ID（多轮对话用） |
| created_at        | DATETIME    | 问答时间         |


#### 5.1.4 系统配置表 (system_configs)


| 字段          | 类型           | 说明                               |
| ----------- | ------------ | -------------------------------- |
| id          | BIGINT       | 主键，自增                            |
| key         | VARCHAR(100) | 配置键                              |
| value       | TEXT         | 配置值                              |
| value_type  | VARCHAR(20)  | 值类型 (string/number/boolean/json) |
| group_name  | VARCHAR(50)  | 配置分组                             |
| name        | VARCHAR(100) | 配置名称                             |
| description | TEXT         | 配置描述                             |
| editable    | BOOLEAN      | 是否可编辑                            |
| sensitive   | BOOLEAN      | 是否敏感（密码类）                        |
| created_at  | DATETIME     | 创建时间                             |
| updated_at  | DATETIME     | 更新时间                             |


### 5.2 Milvus Collection 设计

```
Collection: knowledge_base

Fields:
  - id: VARCHAR(256)     # 主键，向量 ID
  - document_id: INT64    # 文档 ID
  - chunk_index: INT64   # 块序号
  - content: VARCHAR     # 文本内容
  - filename: VARCHAR    # 文件名
  - embedding: FLOAT_VECTOR[384]  # 向量

Index:
  - metric_type: IP (内积相似度)
  - index_type: IVF_FLAT
```

### 5.3 Redis 缓存设计


| Key 模式          | 类型   | 说明   | TTL |
| --------------- | ---- | ---- | --- |
| qa:cache:{hash} | Hash | 问答缓存 | 24h |


缓存内容结构：

```json
{
  "answer": "回答内容",
  "sources": [{"vector_id": "...", "filename": "...", ...}]
}
```

---

## 6. API 接口设计

### 6.1 认证接口


| 方法   | 路径                 | 描述   |
| ---- | ------------------ | ---- |
| POST | /api/v1/auth/login | 用户登录 |


### 6.2 文档管理


| 方法     | 路径                             | 描述      |
| ------ | ------------------------------ | ------- |
| POST   | /api/v1/documents/upload       | 上传文档    |
| GET    | /api/v1/documents              | 获取文档列表  |
| GET    | /api/v1/documents/{id}         | 获取文档详情  |
| GET    | /api/v1/documents/{id}/preview | 预览文档内容  |
| GET    | /api/v1/documents/{id}/chunks  | 获取文档块列表 |
| DELETE | /api/v1/documents/{id}         | 删除文档    |


### 6.3 知识库管理


| 方法     | 路径                              | 描述      |
| ------ | ------------------------------- | ------- |
| GET    | /api/v1/knowledge/stats         | 获取知识库统计 |
| POST   | /api/v1/knowledge/rebuild       | 重建知识库索引 |
| POST   | /api/v1/knowledge/chunks/search | 检索相关文档块 |
| DELETE | /api/v1/knowledge/cache/clear   | 清空问答缓存  |


### 6.4 问答接口


| 方法   | 路径                    | 描述          |
| ---- | --------------------- | ----------- |
| POST | /api/v1/qa/ask        | 提交问答请求（非流式） |
| POST | /api/v1/qa/ask/stream | 流式问答（SSE）   |
| GET  | /api/v1/qa/history    | 获取问答历史      |


#### 6.4.1 流式问答事件格式

```
data: {"type":"sources","sources":[...]}

data: {"type":"token","content":"你"}
data: {"type":"token","content":"好"}
data: {"type":"token","content":"！"}
...

data: {"type":"done","answer":"...","sources":[...],"response_time_ms":1500,"cache_hit":false}

data: [DONE]
```

### 6.5 系统管理


| 方法   | 路径                           | 描述       |
| ---- | ---------------------------- | -------- |
| GET  | /api/v1/system/health        | 健康检查     |
| GET  | /api/v1/system/stats         | 系统统计     |
| GET  | /api/v1/system/config        | 获取运行时配置  |
| POST | /api/v1/system/config        | 更新运行时配置  |
| GET  | /api/v1/system/configs       | 获取所有系统配置 |
| PUT  | /api/v1/system/configs/{key} | 更新配置项    |


---

## 7. 项目结构

### 7.1 后端项目结构

```
rag-qa-system/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI 应用入口
│   ├── config.py                  # 配置管理
│   ├── api/
│   │   ├── __init__.py
│   │   ├── deps.py               # 依赖注入
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── auth.py           # 认证接口
│   │       ├── documents.py      # 文档管理接口
│   │       ├── knowledge.py      # 知识库接口
│   │       ├── qa.py            # 问答接口
│   │       └── system.py         # 系统接口
│   ├── core/
│   │   ├── __init__.py
│   │   ├── database.py          # MySQL 连接
│   │   ├── vectorstore.py       # Milvus 操作
│   │   ├── cache.py             # Redis 操作
│   │   ├── llm.py               # DeepSeek API
│   │   ├── logger.py            # 日志管理
│   │   └── runtime_config.py    # 运行时配置
│   ├── services/
│   │   ├── __init__.py
│   │   ├── document_service.py  # 文档处理服务
│   │   ├── knowledge_service.py # 知识库服务
│   │   ├── qa_service.py       # 问答服务
│   │   └── system_config_service.py  # 配置服务
│   ├── models/
│   │   ├── __init__.py
│   │   ├── document.py          # 文档数据模型
│   │   ├── qa.py               # 问答模型
│   │   └── system_config.py    # 配置模型
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── document.py         # 文档请求/响应
│   │   ├── qa.py              # 问答请求/响应
│   │   └── common.py           # 通用响应
│   └── utils/
│       ├── __init__.py
│       ├── file_parser.py     # 文件解析
│       └── text_splitter.py   # 文本切分
├── data/
│   └── documents/             # 文档存储
├── scripts/
│   └── init.py               # 初始化脚本
├── requirements.txt
├── .env.example
└── README.md
```

### 7.2 前端项目结构

```
rag-qa-frontend/
├── src/
│   ├── main.ts               # 应用入口
│   ├── App.vue               # 根组件
│   ├── api/
│   │   ├── index.ts         # API 导出
│   │   └── request.ts       # Axios 封装
│   ├── router/
│   │   └── index.ts         # 路由配置
│   ├── types/
│   │   ├── index.ts         # 类型定义
│   │   └── element-plus.d.ts
│   ├── views/
│   │   ├── Layout.vue       # 布局组件
│   │   ├── Login.vue        # 登录页
│   │   ├── Dashboard.vue    # 仪表盘
│   │   ├── QA.vue           # 智能问答
│   │   ├── Documents.vue    # 文档管理
│   │   ├── Knowledge.vue    # 知识库管理
│   │   └── System.vue       # 系统设置
│   └── styles/
│       └── global.css       # 全局样式
├── index.html
├── package.json
├── vite.config.ts
└── tsconfig.json
```

---

## 8. 配置项说明

### 8.1 后端环境变量 (.env)

```env
# 应用配置
APP_ENV=development
APP_HOST=0.0.0.0
APP_PORT=8000
SECRET_KEY=your-secret-key

# MySQL 配置
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_DATABASE=rag_qa
MYSQL_USER=root
MYSQL_PASSWORD=123456

# Redis 配置
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
CACHE_DEFAULT_TTL=86400

# Milvus 配置
MILVUS_HOST=localhost
MILVUS_PORT=19530
MILVUS_COLLECTION_NAME=knowledge_base

# DeepSeek API 配置
DEEPSEEK_API_KEY=your-api-key
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat

# Embedding 配置
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_DEVICE=cpu
EMBEDDING_DIMENSION=384

# 文件上传配置
UPLOAD_DIR=./data/documents
ALLOWED_EXTENSIONS=pdf,docx,doc,txt,md
MAX_FILE_SIZE=10485760
```

### 8.2 运行时可配置参数


| 参数                   | 默认值   | 说明         |
| -------------------- | ----- | ---------- |
| retrieval_top_k      | 5     | Top K 检索数  |
| similarity_threshold | 0.2   | 相似度阈值      |
| enable_mmr           | false | 启用 MMR 重排序 |
| mmr_diversity        | 0.5   | MMR 多样性参数  |
| chunk_size           | 500   | 文档分块大小     |
| chunk_overlap        | 50    | 分块重叠大小     |
| chunk_min_size       | 50    | 最小块大小      |


---

## 9. 部署方案

### 9.1 Docker Compose 部署

```yaml
version: '3.8'

services:
  backend:
    build: .
    ports:
      - "8000:8000"
    environment:
      - MYSQL_HOST=mysql
      - REDIS_HOST=redis
      - MILVUS_HOST=milvus
    volumes:
      - ./data:/app/data
    depends_on:
      - mysql
      - redis
      - milvus
    restart: unless-stopped

  frontend:
    build: ./rag-qa-frontend
    ports:
      - "3000:3000"
    depends_on:
      - backend

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

  milvus:
    image: milvusdb/milvus:v2.3
    ports:
      - "19530:19530"
    volumes:
      - milvus_data:/var/lib/milvus

volumes:
  mysql_data:
  redis_data:
  milvus_data:
```

---

## 10. 开发计划

### 阶段一：基础框架搭建

- 项目结构初始化
- 配置文件与环境变量管理
- MySQL 数据库连接与表结构
- Milvus 向量数据库初始化
- FastAPI 框架与路由配置

### 阶段二：核心功能实现

- 文档上传与解析（PDF/DOCX/TXT/MD）
- 文本切分与向量化存储
- 问答检索与生成
- 流式输出实现
- Redis 缓存集成

### 阶段三：前端界面开发

- 登录认证页面
- 仪表盘展示
- 文档管理页面
- 知识问答页面
- 知识库管理页面
- 系统设置页面

### 阶段四：优化与完善

- 缓存命中与实时生成区分
- 系统配置管理
- 健康检查与监控
- MMR 重排序支持

---

## 11. 风险评估


| 风险项               | 可能性 | 影响  | 应对措施                 |
| ----------------- | --- | --- | -------------------- |
| DeepSeek API 调用超时 | 中   | 中   | 增加超时配置与重试，本地缓存结果     |
| 向量检索召回率低          | 中   | 高   | 优化切分策略，调整检索参数，启用 MMR |
| 大文件处理内存溢出         | 低   | 中   | 流式读取，限制文件大小，分块处理     |
| Milvus 数据丢失       | 低   | 高   | 定期备份，配置持久化存储         |


---

## 12. 附录

### 12.1 参考资料

- [FastAPI 文档](https://fastapi.tiangolo.com/)
- [Milvus 官方文档](https://milvus.io/docs)
- [Vue 3 文档](https://vuejs.org/)
- [Element Plus 文档](https://element-plus.org/)
- [DeepSeek API 文档](https://platform.deepseek.com/)

### 12.2 术语表


| 术语           | 说明                                    |
| ------------ | ------------------------------------- |
| RAG          | Retrieval-Augmented Generation，检索增强生成 |
| Chunk        | 文本切分后的最小单元                            |
| Embedding    | 将文本转换为向量的技术                           |
| Vector Store | 存储向量数据的数据库                            |
| MMR          | Max Marginal Relevance，最大边际相关性        |
| SSE          | Server-Sent Events，服务器推送事件            |
| Token        | 语言模型处理的最小单位                           |


---

## 文档版本历史


| 版本   | 日期         | 修改内容                          | 作者  |
| ---- | ---------- | ----------------------------- | --- |
| V1.0 | 2026-05-13 | 初始版本                          | -   |
| V2.0 | 2026-05-17 | 完整实现版本，更新技术栈，增加流式输出、缓存管理等核心功能 | -   |


