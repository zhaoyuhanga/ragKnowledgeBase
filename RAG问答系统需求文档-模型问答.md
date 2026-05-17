# 模型问答模块 - 需求文档

**版本：** V1.2  
**日期：** 2026-05-17  
**状态：** 更新中  
**模块：** 问答模块（QA Module）

---

## 1. 功能概述

### 1.1 核心流程

```
用户提问
    │
    ▼
┌─────────────────┐
│   检查缓存       │ ← Redis 缓存问答结果
└────────┬────────┘
         │
    ┌────┴────┐
    │命中缓存？ │
    └────┬────┘
      YES │ NO
     ┌────┴────┐
     │         │
     ▼         ▼
┌─────────┐ ┌─────────────────┐
│命中缓存  │ │  未命中缓存       │
└────┬────┘ └────────┬────────┘
     │                │
     │         ┌─────▼─────┐
     │         │ 向量检索   │ ← 仅检索"本地导入"的文档块
     │         └─────┬─────┘
     │               │
     │         ┌─────▼─────┐
     │         │  获取结果  │
     │         └─────┬─────┘
     │               │
     │    ┌──────────┴──────────┐
     │    │ 检索结果为空？        │
     │    └──────────┬──────────┘
     │       YES     │     NO
     │       ┌───────┴───────┐
     │       │               │
     │       ▼               ▼
     │ ┌───────────┐ ┌─────────────┐
     │ │ 调用      │ │ 调用 DeepSeek │
     │ │ DeepSeek │ │ API（流式） │
     │ │ API流式  │ └──────┬──────┘
     │ └─────┬─────┘        │
     │       │          ┌────▼────┐
     │       │          │ 逐token │
     │       │          │ 流式返回 │
     │       │          └────┬────┘
     │       │               │
     │       │         ┌─────▼─────┐
     │       │         │ 保存到缓存 │
     │       │         └─────┬─────┘
     │       │               │
     │       │    ┌──────────┴──────────┐
     │       │    │ 异步：生成文档块     │
     │       │    │ 添加到向量数据库     │
     │       │    │ 标记为"AI生成"      │
     │       │    │ 创建文档管理记录     │
     │       │    └──────────┬──────────┘
     │       │               │
     └───────┴───────────────┴──────────┘
                │
                ▼
         ┌─────────────────────┐
         │      返回结果        │
         └─────────────────────┘
```

### 1.2 状态标识


| 状态      | 显示内容    | 说明              |
| ------- | ------- | --------------- |
| `缓存命中`  | "命中缓存"  | 从 Redis 缓存直接返回  |
| `实时生成`  | "实时生成"  | 调用 LLM API 流式生成 |
| `AI 扩展` | "AI 扩展" | AI 生成的内容已加入知识库  |


---

## 2. 功能需求

### 2.1 缓存机制


| 需求项    | 描述                     | 优先级 |
| ------ | ---------------------- | --- |
| 缓存键设计  | 使用问题文本的 MD5 哈希作为缓存 Key | P0  |
| 缓存结构   | 存储：回答文本、来源列表、生成时间      | P0  |
| 缓存命中返回 | 流式返回缓存内容，前端显示"命中缓存"    | P0  |
| 缓存未命中  | 正常走 LLM 生成流程           | P0  |
| 缓存 TTL | 默认 1 小时（可配置）           | P1  |


### 2.2 知识库检索模式


| 模式        | 描述          | 搜索范围                           | 优先级 |
| --------- | ----------- | ------------------------------ | --- |
| **本地知识库** | 仅搜索本地导入的文档  | `source_type = 'local'`        | P0  |
| **AI 扩展** | AI 生成并入库的内容 | `source_type = 'ai_generated'` | P1  |
| **全库搜索**  | 搜索全部内容      | 全部                             | P1  |



| 需求项     | 描述                                          | 优先级 |
| ------- | ------------------------------------------- | --- |
| 来源类型标记  | 向量数据增加 `source_type` 字段                     | P0  |
| 本地导入标记  | 文档上传时标记 `source_type = 'local'`             | P0  |
| AI 生成标记 | AI 生成内容入库时标记 `source_type = 'ai_generated'` | P0  |
| 检索过滤    | 支持按 `source_type` 过滤检索结果                    | P0  |


### 2.3 流式输出


| 需求项      | 描述                                   | 优先级 |
| -------- | ------------------------------------ | --- |
| SSE 协议   | 使用 Server-Sent Events 流式返回           | P0  |
| Token 事件 | 每个 token 单独推送，前端实时显示                 | P0  |
| 状态事件     | 推送 `sources`（来源）、`cache_hit`（是否缓存命中） | P0  |
| 完成事件     | 推送 `done` 事件，包含完整结果                  | P0  |
| 前端状态更新   | 命中缓存时显示"命中缓存"，生成时显示"实时生成"            | P0  |


### 2.4 AI 扩展（知识库增强）


| 需求项     | 描述                                   | 优先级 |
| ------- | ------------------------------------ | --- |
| AI 生成流程 | 向量检索为空时，调用 DeepSeek API 获取回答         | P0  |
| 流式返回    | 直接流式返回 AI 生成的回答给用户                   | P0  |
| 异步入库    | 生成完成后，异步调用接口将回答转为文档块存入向量数据库          | P0  |
| 文档管理展示  | AI 生成的文档在文档管理页面展示                    | P0  |
| 来源标记    | 入库时标记 `source_type = 'ai_generated'` | P0  |
| 模型记录    | 记录生成使用的 LLM 模型                       | P0  |
| 来源追溯    | 返回来源时区分"本地导入"和"AI 生成"                | P0  |


### 2.5 LLM 生成


| 需求项    | 描述                | 优先级 |
| ------ | ----------------- | --- |
| 流式调用   | DeepSeek API 流式输出 | P0  |
| 上下文注入  | 将检索到的文档块作为上下文（如有） | P0  |
| 无上下文生成 | 检索为空时，直接调用 LLM 回答 | P0  |
| 系统提示词  | 使用预定义的系统提示词       | P0  |
| 模型记录   | 保存生成时使用的模型名称      | P0  |
| 错误处理   | API 调用失败时返回友好提示   | P0  |


---

## 3. 数据模型

### 3.1 向量元数据扩展

```python
# DocumentChunk 新增字段
metadata = {
    # ... 现有字段 ...
    
    # 来源类型
    "source_type": str,  # "local" | "ai_generated"
    
    # AI 生成信息（仅 ai_generated 时有值）
    "generated_from_question": str,  # AI 生成时记录原始问题
    "generated_at": datetime,         # AI 生成时间
    "llm_model": str,                 # 使用的 LLM 模型名称，如 "deepseek-chat"
    "llm_provider": str,             # LLM 提供商，如 "deepseek"
}
```

### 3.2 Document 模型扩展

```python
class Document:
    # ... 现有字段 ...
    
    # AI 生成信息
    source_type: str = "local"  # "local" | "ai_generated"
    generated_from_question: str = None  # 原始问题
    generated_at: datetime = None       # 生成时间
    llm_model: str = None               # 使用的模型
    llm_provider: str = None            # 提供商
    
    # AI 生成的内容块数量
    chunk_count: int = 0
```

### 3.3 来源类型枚举


| 类型值            | 说明    | 使用场景         |
| -------------- | ----- | ------------ |
| `local`        | 本地导入  | 用户上传的文档解析后入库 |
| `ai_generated` | AI 生成 | LLM 生成并入库的内容 |


### 3.4 AI 生成文档命名规则

```
AI_Generated_{timestamp}_{question_hash}.txt
示例：AI_Generated_20260517_152300_a1b2c3d4.txt
```

---

## 4. API 接口

### 4.1 流式问答接口

**端点：** `POST /api/v1/qa/ask/stream`

**请求体：**

```json
{
  "question": "什么是 RAG 技术？",
  "session_id": "user_123_session_001",
  "top_k": 5,
  "temperature": 0.3,
  "search_mode": "local",
  "enable_ai_extend": true
}
```

**请求参数说明：**


| 参数                 | 类型     | 默认值     | 说明         |
| ------------------ | ------ | ------- | ---------- |
| `question`         | string | 必填      | 用户问题       |
| `session_id`       | string | null    | 会话 ID      |
| `top_k`            | int    | 5       | 检索数量       |
| `temperature`      | float  | 0.3     | 生成温度       |
| `search_mode`      | string | "local" | 搜索模式       |
| `enable_ai_extend` | bool   | true    | 是否启用 AI 扩展 |


**响应事件：**


| 事件类型        | 数据结构                                                                                       | 说明            |
| ----------- | ------------------------------------------------------------------------------------------ | ------------- |
| `sources`   | `{"type":"sources","sources":[...]}`                                                       | 检索到的文档来源      |
| `token`     | `{"type":"token","content":"某"}`                                                           | 每个 token 增量文本 |
| `ai_extend` | `{"type":"ai_extend","status":"generating"}`                                               | AI 扩展状态       |
| `done`      | `{"type":"done","answer":"...","sources":[...],"cache_hit":false,"response_time_ms":1500}` | 完成事件          |
| `error`     | `{"type":"error","error":"错误信息"}`                                                          | 错误信息          |


### 4.2 响应字段说明


| 字段                 | 类型      | 说明                                      |
| ------------------ | ------- | --------------------------------------- |
| `type`             | string  | 事件类型：sources/token/ai_extend/done/error |
| `content`          | string  | token 文本（type=token 时）                  |
| `sources`          | array   | 检索到的文档来源列表                              |
| `answer`           | string  | 完整回答（type=done 时）                       |
| `cache_hit`        | boolean | 是否命中缓存                                  |
| `source_type`      | string  | 来源类型：local / ai_generated               |
| `response_time_ms` | number  | 响应耗时                                    |
| `error`            | string  | 错误信息（type=error 时）                      |


---

## 5. 文档管理功能

### 5.1 AI 生成文档展示

AI 生成的文档需要在文档管理页面展示，包括：


| 显示字段    | 说明                            |
| ------- | ----------------------------- |
| 文件名     | AI_Generated_{时间戳}_{问题哈希}.txt |
| 来源类型    | AI 生成（标识）                     |
| 原始问题    | 生成该文档的原始用户问题                  |
| 生成时间    | AI 生成的时间                      |
| LLM 模型  | 使用的模型名称（如 deepseek-chat）      |
| LLM 提供商 | 提供商（如 deepseek）               |
| 文档块数    | 拆分后的块数量                       |
| 字符数     | 文档总字符数                        |


### 5.2 查询条件


| 条件字段                      | 类型  | 说明                       |
| ------------------------- | --- | ------------------------ |
| `source_type`             | 枚举  | 筛选来源类型：全部 / 本地导入 / AI 生成 |
| `llm_model`               | 字符串 | 筛选 LLM 模型                |
| `llm_provider`            | 字符串 | 筛选 LLM 提供商               |
| `generated_at_start`      | 日期  | 生成时间开始                   |
| `generated_at_end`        | 日期  | 生成时间结束                   |
| `generated_from_question` | 字符串 | 按原始问题模糊搜索                |


### 5.3 文档列表展示

```
文档列表
├── 本地导入
│   ├── 技术文档.pdf     [上传时间] [5个块]
│   └── 开发指南.md       [上传时间] [3个块]
│
└── AI 生成
    ├── AI_Generated_20260517_152300_a1b2.txt  [2026-05-17 15:23] [deepseek-chat] [3个块]
    │   原始问题：什么是 RAG 技术？
    └── AI_Generated_20260517_153000_c3d4.txt  [2026-05-17 15:30] [deepseek-chat] [2个块]
        原始问题：FastAPI 如何集成 Redis？
```

### 5.4 AI 生成文档详情

```
文档详情 - AI_Generated_20260517_152300_a1b2.txt
├── 基本信息
│   ├── 来源类型：AI 生成
│   ├── 生成时间：2026-05-17 15:23:00
│   └── 字符数：1256
│
├── AI 信息
│   ├── LLM 提供商：deepseek
│   ├── LLM 模型：deepseek-chat
│   └── 原始问题：什么是 RAG 技术？
│
├── 文档块
│   ├── 块 1 (0-500字符) - 向量 ID: xxx
│   ├── 块 2 (500-1000字符) - 向量 ID: xxx
│   └── 块 3 (1000-1256字符) - 向量 ID: xxx
│
└── 操作
    ├── [预览] [删除] [重新生成]
```

---

## 6. 前端交互

### 6.1 问答输入框

- 文本输入框，支持多行
- 提交按钮
- 加载状态指示
- **搜索模式切换**（本地 / AI 扩展 / 全库）
- **AI 扩展开关**（启用 / 禁用）

### 6.2 答案展示区

- 流式文字显示区域
- 来源文档折叠/展开（区分本地/AI）
- 状态标签

### 6.3 状态标签


| 状态    | 标签样式        | 显示时机               |
| ----- | ----------- | ------------------ |
| 命中缓存  | 绿色标签 + 闪电图标 | `cache_hit = true` |
| 实时生成  | 蓝色标签 + 刷新图标 | 开始生成第一个 token 时    |
| AI 扩展 | 紫色标签 + 星星图标 | AI 生成的内容           |


### 6.4 文档管理页面

- **来源类型筛选**：全部 / 本地导入 / AI 生成
- **模型筛选**：按 LLM 模型筛选
- **时间范围筛选**：按生成时间筛选
- **关键词搜索**：按原始问题搜索
- **AI 生成标识**：特殊图标和颜色区分

---

## 7. 技术实现

### 7.1 后端改动


| 文件                         | 改动内容                                                                                                           |
| -------------------------- | -------------------------------------------------------------------------------------------------------------- |
| `models/document.py`       | Document 增加 `source_type`、`llm_model`、`llm_provider`、`generated_from_question`、`generated_at`、`chunk_count` 字段 |
| `models/document_chunk.py` | DocumentChunk 增加 `source_type`、`llm_model`、`llm_provider`、`generated_from_question`、`generated_at` 字段          |
| `vectorstore.py`           | 增加 `source_type` 过滤检索                                                                                          |
| `qa_service.py`            | 1. 增加 `search_mode` 参数 2. 增加 `enable_ai_extend` 参数 3. 检索为空时调用 LLM 4. 异步保存 AI 生成结果到向量数据库 5. 创建 Document 记录      |
| `qa.py`                    | 更新 API 参数                                                                                                      |


### 7.2 数据库改动

```sql
-- Document 表增加字段
ALTER TABLE documents ADD COLUMN source_type VARCHAR(20) DEFAULT 'local';
ALTER TABLE documents ADD COLUMN generated_from_question TEXT;
ALTER TABLE documents ADD COLUMN generated_at DATETIME;
ALTER TABLE documents ADD COLUMN llm_model VARCHAR(100);
ALTER TABLE documents ADD COLUMN llm_provider VARCHAR(50);
ALTER TABLE documents ADD COLUMN chunk_count INT DEFAULT 0;

-- DocumentChunk 表增加字段
ALTER TABLE document_chunks ADD COLUMN source_type VARCHAR(20) DEFAULT 'local';
ALTER TABLE document_chunks ADD COLUMN generated_from_question TEXT;
ALTER TABLE document_chunks ADD COLUMN generated_at DATETIME;
ALTER TABLE document_chunks ADD COLUMN llm_model VARCHAR(100);
ALTER TABLE document_chunks ADD COLUMN llm_provider VARCHAR(50);
```

### 7.3 SSE 事件流示例

```
# 模式1：本地检索有结果
data: {"type":"sources","sources":[{"filename":"文档.pdf","source_type":"local",...}]}
data: {"type":"token","content":"根据文档内容，答案是..."}
data: {"type":"done","answer":"...","sources":[...],"cache_hit":false,"response_time_ms":500}

# 模式2：本地检索为空，启用 AI 扩展
data: {"type":"sources","sources":[]}
data: {"type":"ai_extend","status":"generating"}
data: {"type":"token","content":"根据我的理解，"}
data: {"type":"token","content":"RAG 是..."}
data: {"type":"done","answer":"...","sources":[],"ai_extend":true,"ai_doc_id":123,"response_time_ms":2000}

# 模式3：命中缓存
data: {"type":"sources","sources":[...]}
data: {"type":"token","content":"缓存的回答是..."}
data: {"type":"done","answer":"...","cache_hit":true,"response_time_ms":10}
```

---

## 8. 异步任务设计

### 8.1 AI 生成内容入库

当向量检索为空且 `enable_ai_extend=true` 时：

1. **主流程**：流式返回 AI 回答给用户
2. **异步任务**：将完整回答转为文档块存入向量数据库

```python
async def _save_ai_generated_content(question: str, answer: str):
    """异步保存 AI 生成的内容到向量数据库"""
    from app.config import settings
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    question_hash = hashlib.md5(question.encode()).hexdigest()[:8]
    filename = f"AI_Generated_{timestamp}_{question_hash}.txt"
    
    # 1. 创建文档记录
    doc = Document(
        filename=filename,
        file_type="ai_generated",
        source_type="ai_generated",
        generated_from_question=question,
        generated_at=datetime.now(),
        llm_model=settings.llm_model,
        llm_provider=settings.llm_provider,
    )
    db.add(doc)
    db.flush()
    
    # 2. 文本分块
    chunks = text_splitter.split_text(answer)
    
    # 3. 创建文档块并向量化
    for idx, chunk_text in enumerate(chunks):
        chunk = DocumentChunk(
            document_id=doc.id,
            content=chunk_text,
            chunk_index=idx,
            char_count=len(chunk_text),
            source_type="ai_generated",
            generated_from_question=question,
            generated_at=datetime.now(),
            llm_model=settings.llm_model,
            llm_provider=settings.llm_provider,
        )
        db.add(chunk)
        db.flush()
        
        # 4. 向量化并存入 Milvus
        embedding = embedding_service.encode_single(chunk_text)
        vector_store.add_vectors([embedding], [chunk.to_metadata()])
    
    # 5. 更新文档块数量
    doc.chunk_count = len(chunks)
    db.commit()
    
    logger.info(f"AI 生成内容已入库: doc_id={doc.id}, chunks={len(chunks)}, model={settings.llm_model}")
    
    return doc.id
```

### 8.2 后台任务队列


| 任务类型               | 说明        | 实现方式         |
| ------------------ | --------- | ------------ |
| `ai_content_index` | AI 生成内容入库 | 后台任务（不阻塞主流程） |


---

## 9. API 接口 - 文档管理

### 9.1 文档列表接口扩展

**端点：** `GET /api/v1/documents`

**新增查询参数：**


| 参数                   | 类型       | 默认值  | 说明                          |
| -------------------- | -------- | ---- | --------------------------- |
| `source_type`        | string   | null | 筛选来源类型：local / ai_generated |
| `llm_model`          | string   | null | 筛选 LLM 模型                   |
| `llm_provider`       | string   | null | 筛选 LLM 提供商                  |
| `generated_at_start` | datetime | null | 生成时间开始                      |
| `generated_at_end`   | datetime | null | 生成时间结束                      |
| `question_keyword`   | string   | null | 按原始问题模糊搜索                   |


**响应示例：**

```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": 1,
        "filename": "技术文档.pdf",
        "source_type": "local",
        "created_at": "2026-05-17T10:00:00",
        "chunk_count": 5
      },
      {
        "id": 2,
        "filename": "AI_Generated_20260517_152300_a1b2.txt",
        "source_type": "ai_generated",
        "generated_from_question": "什么是 RAG 技术？",
        "generated_at": "2026-05-17T15:23:00",
        "llm_model": "deepseek-chat",
        "llm_provider": "deepseek",
        "chunk_count": 3
      }
    ],
    "total": 2,
    "page": 1,
    "page_size": 20
  }
}
```

### 9.2 文档详情接口扩展

**端点：** `GET /api/v1/documents/{id}`

**响应扩展字段：**

```json
{
  "success": true,
  "data": {
    "id": 2,
    "filename": "AI_Generated_20260517_152300_a1b2.txt",
    "source_type": "ai_generated",
    "generated_from_question": "什么是 RAG 技术？",
    "generated_at": "2026-05-17T15:23:00",
    "llm_model": "deepseek-chat",
    "llm_provider": "deepseek",
    "chunk_count": 3,
    "char_count": 1256,
    "chunks": [
      {
        "id": 100,
        "chunk_index": 0,
        "content": "...",
        "vector_id": "xxx"
      }
    ]
  }
}
```

---

## 10. 验收标准

### 10.1 功能验收

- 相同问题第二次提问时显示"命中缓存"
- 首次提问时显示"实时生成"
- 流式输出正常，无明显延迟
- 向量检索为空时，自动调用 DeepSeek API 生成回答
- AI 生成的回答流式返回给用户
- AI 生成完成后，异步入库并标记 `source_type='ai_generated'`
- 检索结果可按来源类型过滤
- AI 生成文档在文档管理页面展示
- AI 生成文档显示：原始问题、模型名称、提供商、块数量

### 10.2 搜索模式验收

- `search_mode=local` 仅返回本地导入的文档
- `search_mode=ai_generated` 仅返回 AI 生成的内容
- `search_mode=all` 返回全部内容
- `enable_ai_extend=false` 时，检索为空不调用 LLM

### 10.3 文档管理验收

- 支持按 `source_type` 筛选文档
- 支持按 `llm_model` 筛选文档
- 支持按 `llm_provider` 筛选文档
- 支持按生成时间范围筛选
- 支持按原始问题关键词搜索
- AI 生成文档有明显的视觉标识

### 10.4 性能验收

- 缓存命中响应时间 < 100ms
- 流式输出首 token 延迟 < 2s
- 向量检索时间 < 500ms
- 异步入库不影响主流程响应时间

### 10.5 交互验收

- 状态标签清晰可见（缓存/生成/AI扩展）
- 来源文档区分本地和 AI 生成
- 搜索模式切换正常
- 文档管理筛选功能正常
- 错误信息友好展示

---

## 11. 附录

### 11.1 配置项


| 配置项                           | 默认值  | 说明          |
| ----------------------------- | ---- | ----------- |
| `qa_cache_ttl`                | 3600 | 问答缓存 TTL（秒） |
| `ai_extend_enabled`           | true | 是否启用 AI 扩展  |
| `ai_generated_retention_days` | 30   | AI 生成内容保留天数 |


### 11.2 现有代码参考

- `rag-qa-system/app/services/qa_service.py` - 已有 `ask_stream` 方法
- `rag-qa-system/app/api/v1/qa.py` - 已有 SSE 接口
- `rag-qa-system/app/api/v1/documents.py` - 文档管理接口
- `rag-qa-system/app/core/cache.py` - 已有缓存读写方法
- `rag-qa-system/app/core/vectorstore.py` - 向量存储操作

### 11.3 更新日志


| 版本   | 日期         | 更新内容                        |
| ---- | ---------- | --------------------------- |
| V1.0 | 2026-05-17 | 初始版本                        |
| V1.1 | 2026-05-17 | 增加 AI 扩展功能、来源类型区分、搜索模式切换    |
| V1.2 | 2026-05-17 | 增加 AI 生成文档在文档管理展示、查询条件、模型记录 |


