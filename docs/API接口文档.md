# RAG知识库系统 - API接口文档

## 基本信息


| 项目       | 内容                             |
| -------- | ------------------------------ |
| 文档版本     | 1.0.0                          |
| 更新日期     | 2026-05-23                     |
| API版本    | v1                             |
| Base URL | `http://localhost:8011/api/v1` |


---

## 一、统一规范

### 1.1 统一响应格式

所有接口均返回统一格式的JSON响应：

```json
{
  "code": 0,
  "message": "success",
  "data": {},
  "traceId": "202605231200000001",
  "timestamp": "2026-05-23T12:00:00+08:00"
}
```

**响应字段说明：**


| 字段        | 类型     | 说明               |
| --------- | ------ | ---------------- |
| code      | int    | 状态码，0表示成功，非0表示错误 |
| message   | string | 消息描述             |
| data      | object | 响应数据             |
| traceId   | string | 追踪ID             |
| timestamp | string | 时间戳              |


### 1.2 分页响应格式

列表接口使用分页响应格式：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [],
    "total": 100,
    "page_no": 1,
    "page_size": 20,
    "pages": 5
  },
  "traceId": "202605231200000001",
  "timestamp": "2026-05-23T12:00:00+08:00"
}
```

### 1.3 错误码说明


| 前缀        | 范围        | 说明   |
| --------- | --------- | ---- |
| SYS_1xxx  | 1000-1999 | 系统错误 |
| BIZ_2xxx  | 2000-2999 | 业务错误 |
| DOC_3xxx  | 3000-3999 | 文档错误 |
| RET_4xxx  | 4000-4999 | 检索错误 |
| QUEUE_xxx | -         | 队列错误 |
| AUTH_9xxx | 9000-9999 | 认证错误 |


### 1.4 通用错误响应

```json
{
  "code": "BIZ_2001",
  "message": "数据不存在",
  "data": null,
  "traceId": "202605231200000001",
  "timestamp": "2026-05-23T12:00:00+08:00"
}
```

---

## 二、健康检查接口 `/health`

### 2.1 健康检查

**接口地址：** `GET /health`

**功能说明：** 检查系统整体健康状态

**请求参数：** 无

**响应示例：**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "status": "healthy",
    "service": "RAG知识库系统",
    "version": "1.0.0",
    "environment": "local"
  }
}
```

### 2.2 数据库健康检查

**接口地址：** `GET /health/db`

**功能说明：** 检查MySQL数据库连接状态

**请求参数：** 无

**响应示例：**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "status": "connected",
    "type": "mysql"
  }
}
```

### 2.3 Redis健康检查

**接口地址：** `GET /health/redis`

**功能说明：** 检查Redis缓存连接状态

**请求参数：** 无

**响应示例：**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "status": "connected",
    "type": "redis"
  }
}
```

### 2.4 Milvus健康检查

**接口地址：** `GET /health/milvus`

**功能说明：** 检查Milvus向量数据库连接状态

**请求参数：** 无

**响应示例：**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "status": "connected",
    "type": "milvus"
  }
}
```

### 2.5 RabbitMQ健康检查

**接口地址：** `GET /health/rabbitmq`

**功能说明：** 检查RabbitMQ消息队列连接状态

**请求参数：** 无

**响应示例：**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "status": "connected",
    "type": "rabbitmq"
  }
}
```

---

## 三、文档管理接口 `/documents`

### 3.1 单文件上传

**接口地址：** `POST /documents/upload`

**功能说明：** 上传单个文档文件，自动识别文件类型并保存。如果文件已存在（通过Hash检测），则关联到已有版本。

**Content-Type：** `multipart/form-data`

**请求参数：**


| 参数名           | 类型     | 必填  | 说明     |
| ------------- | ------ | --- | ------ |
| file          | binary | 是   | 上传的文件  |
| business_id   | string | 否   | 业务归属ID |
| business_name | string | 否   | 业务归属名称 |
| creator_id    | int    | 否   | 创建人ID  |
| creator_name  | string | 否   | 创建人姓名  |


**响应示例：**

```json
{
  "code": 0,
  "message": "上传成功",
  "data": {
    "document_id": 1,
    "version_id": 1,
    "task_id": "uuid-string",
    "name": "文档.pdf",
    "doc_type": "pdf",
    "file_size": 1024000,
    "is_duplicate": false,
    "status": "pending"
  }
}
```

### 3.2 批量上传

**接口地址：** `POST /documents/batch-upload`

**功能说明：** 批量上传多个文档文件，支持最多20个文件同时上传

**Content-Type：** `multipart/form-data`

**请求参数：**


| 参数名           | 类型       | 必填  | 说明             |
| ------------- | -------- | --- | -------------- |
| files         | binary[] | 是   | 上传的文件列表（最多20个） |
| business_id   | string   | 否   | 业务归属ID         |
| business_name | string   | 否   | 业务归属名称         |
| creator_id    | int      | 否   | 创建人ID          |
| creator_name  | string   | 否   | 创建人姓名          |


**响应示例：**

```json
{
  "code": 0,
  "message": "批量上传完成",
  "data": {
    "total": 5,
    "success": 4,
    "failed": 1,
    "duplicates": 1,
    "documents": [
      {
        "document_id": 1,
        "version_id": 1,
        "name": "文档1.pdf",
        "status": "pending"
      }
    ],
    "failed_files": [
      {
        "name": "文档5.pdf",
        "error": "文件类型不支持"
      }
    ]
  }
}
```

### 3.3 文档列表

**接口地址：** `GET /documents`

**功能说明：** 获取文档列表，支持分页查询和多种筛选条件

**请求参数：**


| 参数名         | 类型     | 必填  | 默认值 | 说明                                |
| ----------- | ------ | --- | --- | --------------------------------- |
| page_no     | int    | 否   | 1   | 页码                                |
| page_size   | int    | 否   | 20  | 每页数量（最大100）                       |
| business_id | string | 否   | -   | 业务归属ID                            |
| status      | int    | 否   | -   | 状态：0-待解析 1-解析中 2-已解析 3-解析失败 9-已删除 |
| keyword     | string | 否   | -   | 名称关键词搜索                           |
| start_date  | string | 否   | -   | 创建开始日期（ISO格式）                     |
| end_date    | string | 否   | -   | 创建结束日期（ISO格式）                     |


**响应示例：**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [
      {
        "id": 1,
        "name": "知识库文档.pdf",
        "doc_type": "pdf",
        "business_id": "biz001",
        "business_name": "测试业务",
        "current_version_id": 1,
        "total_versions": 1,
        "status": 2,
        "status_name": "已解析",
        "total_pages": 50,
        "total_chunks": 120,
        "creator_name": "张三",
        "created_at": "2026-05-22T10:00:00+08:00"
      }
    ],
    "total": 100,
    "page_no": 1,
    "page_size": 20,
    "pages": 5
  }
}
```

### 3.4 文档详情

**接口地址：** `GET /documents/{document_id}`

**功能说明：** 根据文档ID获取文档详细信息，包括文档信息和版本列表

**路径参数：**


| 参数名         | 类型  | 必填  | 说明   |
| ----------- | --- | --- | ---- |
| document_id | int | 是   | 文档ID |


**响应示例：**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": 1,
    "name": "知识库文档.pdf",
    "doc_type": "pdf",
    "business_id": "biz001",
    "business_name": "测试业务",
    "current_version_id": 1,
    "total_versions": 2,
    "status": 2,
    "status_name": "已解析",
    "total_pages": 50,
    "total_chunks": 120,
    "creator_name": "张三",
    "created_at": "2026-05-22T10:00:00+08:00",
    "updated_at": "2026-05-22T11:00:00+08:00",
    "versions": [
      {
        "id": 2,
        "version": 2,
        "file_name": "知识库文档_v2.pdf",
        "file_size": 2048000,
        "status": 2,
        "uploaded_at": "2026-05-22T11:00:00+08:00"
      }
    ]
  }
}
```

### 3.5 删除文档

**接口地址：** `DELETE /documents/{document_id}`

**功能说明：** 软删除指定文档，将文档状态标记为已删除

**路径参数：**


| 参数名         | 类型  | 必填  | 说明   |
| ----------- | --- | --- | ---- |
| document_id | int | 是   | 文档ID |


**响应示例：**

```json
{
  "code": 0,
  "message": "删除成功",
  "data": null
}
```

### 3.6 版本列表

**接口地址：** `GET /documents/{document_id}/versions`

**功能说明：** 获取指定文档的所有版本列表

**路径参数：**


| 参数名         | 类型  | 必填  | 说明   |
| ----------- | --- | --- | ---- |
| document_id | int | 是   | 文档ID |


**响应示例：**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [
      {
        "id": 2,
        "version": 2,
        "file_name": "知识库文档_v2.pdf",
        "file_size": 2048000,
        "status": 2,
        "status_name": "已完成",
        "uploaded_at": "2026-05-22T11:00:00+08:00"
      },
      {
        "id": 1,
        "version": 1,
        "file_name": "知识库文档.pdf",
        "file_size": 1024000,
        "status": 2,
        "status_name": "已完成",
        "uploaded_at": "2026-05-22T10:00:00+08:00"
      }
    ]
  }
}
```

### 3.7 版本详情

**接口地址：** `GET /documents/{document_id}/versions/{version_id}`

**功能说明：** 获取指定版本的详细信息

**路径参数：**


| 参数名         | 类型  | 必填  | 说明   |
| ----------- | --- | --- | ---- |
| document_id | int | 是   | 文档ID |
| version_id  | int | 是   | 版本ID |


**响应示例：**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": 1,
    "version": 1,
    "file_name": "知识库文档.pdf",
    "file_size": 1024000,
    "status": 2,
    "status_name": "已完成",
    "total_pages": 50,
    "total_elements": 320,
    "uploader_name": "张三",
    "uploaded_at": "2026-05-22T10:00:00+08:00",
    "parsed_at": "2026-05-22T10:05:00+08:00"
  }
}
```

---

## 四、导入任务接口 `/import-tasks`

### 4.1 任务详情

**接口地址：** `GET /import-tasks/{task_id}`

**功能说明：** 根据任务ID获取导入任务的详细信息

**路径参数：**


| 参数名     | 类型     | 必填  | 说明   |
| ------- | ------ | --- | ---- |
| task_id | string | 是   | 任务ID |


**响应示例：**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": 1,
    "task_id": "uuid-string",
    "document_id": 1,
    "version_id": 1,
    "task_type": "import",
    "task_status": "completed",
    "priority": 5,
    "progress": 100,
    "retry_count": 0,
    "max_retry": 3,
    "error_type": null,
    "error_message": null,
    "started_at": "2026-05-22T10:00:00+08:00",
    "completed_at": "2026-05-22T10:05:00+08:00",
    "cost_seconds": 300,
    "created_at": "2026-05-22T10:00:00+08:00"
  }
}
```

### 4.2 任务列表

**接口地址：** `GET /import-tasks`

**功能说明：** 获取导入任务列表，支持分页查询和多种筛选条件

**请求参数：**


| 参数名         | 类型     | 必填  | 默认值 | 说明          |
| ----------- | ------ | --- | --- | ----------- |
| page_no     | int    | 否   | 1   | 页码          |
| page_size   | int    | 否   | 20  | 每页数量（最大100） |
| document_id | int    | 否   | -   | 文档ID        |
| task_type   | string | 否   | -   | 任务类型        |
| task_status | string | 否   | -   | 任务状态        |


**响应示例：**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [
      {
        "id": 1,
        "task_id": "uuid-string",
        "document_id": 1,
        "task_type": "import",
        "task_status": "completed",
        "status_name": "已完成",
        "progress": 100,
        "created_at": "2026-05-22T10:00:00+08:00"
      }
    ],
    "total": 100,
    "page_no": 1,
    "page_size": 20,
    "pages": 5
  }
}
```

---

## 五、文档解析接口 `/documents/{id}/`

### 5.1 触发文档解析

**接口地址：** `POST /documents/{document_id}/parse`

**功能说明：** 根据文档ID触发文档解析任务

**路径参数：**


| 参数名         | 类型  | 必填  | 说明   |
| ----------- | --- | --- | ---- |
| document_id | int | 是   | 文档ID |


**请求参数：**


| 参数名        | 类型  | 必填  | 说明             |
| ---------- | --- | --- | -------------- |
| version_id | int | 否   | 版本ID，不传则使用最新版本 |


**响应示例：**

```json
{
  "code": 0,
  "message": "解析任务已创建",
  "data": {
    "task_id": "uuid-string",
    "document_id": 1,
    "version_id": 1,
    "status": "pending"
  }
}
```

### 5.2 查询解析状态

**接口地址：** `GET /documents/{document_id}/parse-status`

**功能说明：** 查询文档的解析状态，包括解析进度、质量统计等

**路径参数：**


| 参数名         | 类型  | 必填  | 说明   |
| ----------- | --- | --- | ---- |
| document_id | int | 是   | 文档ID |


**响应示例：**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "document_id": 1,
    "version_id": 1,
    "status": 2,
    "status_name": "解析完成",
    "parse_progress": 100,
    "total_pages": 50,
    "total_elements": 320,
    "quality_summary": {
      "good": 300,
      "warning": 15,
      "bad": 5
    },
    "started_at": "2026-05-22T10:00:00+08:00",
    "completed_at": "2026-05-22T10:05:00+08:00",
    "cost_seconds": 300
  }
}
```

### 5.3 获取解析元素列表

**接口地址：** `GET /documents/{document_id}/elements`

**功能说明：** 获取文档的解析元素列表，支持分页和筛选

**路径参数：**


| 参数名         | 类型  | 必填  | 说明   |
| ----------- | --- | --- | ---- |
| document_id | int | 是   | 文档ID |


**请求参数：**


| 参数名          | 类型     | 必填  | 默认值 | 说明          |
| ------------ | ------ | --- | --- | ----------- |
| page_no      | int    | 否   | -   | 页码筛选        |
| element_type | string | 否   | -   | 元素类型筛选      |
| quality_flag | string | 否   | -   | 质量标记筛选      |
| page_index   | int    | 否   | 1   | 页码          |
| page_size    | int    | 否   | 20  | 每页数量（最大100） |


**响应示例：**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [
      {
        "id": 1,
        "element_id": "uuid-string",
        "document_id": 1,
        "version_id": 1,
        "page_no": 1,
        "element_type": "title",
        "content": "文档标题",
        "reading_order": 1,
        "title_level": 1,
        "title_path": "文档标题",
        "confidence": 0.95,
        "quality_flag": "good"
      }
    ],
    "total": 320,
    "page_no": 1,
    "page_size": 20,
    "pages": 16
  }
}
```

### 5.4 获取元素详情

**接口地址：** `GET /documents/{document_id}/elements/{element_id}`

**功能说明：** 获取指定元素的详细信息

**路径参数：**


| 参数名         | 类型     | 必填  | 说明   |
| ----------- | ------ | --- | ---- |
| document_id | int    | 是   | 文档ID |
| element_id  | string | 是   | 元素ID |


**响应示例：**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": 1,
    "element_id": "uuid-string",
    "document_id": 1,
    "version_id": 1,
    "page_no": 1,
    "element_type": "paragraph",
    "content": "段落内容",
    "enhanced_content": "增强后的内容",
    "reading_order": 2,
    "title_level": null,
    "title_path": "文档标题",
    "bbox": {"x": 100, "y": 200, "width": 500, "height": 50},
    "confidence": 0.98,
    "is_merged": false,
    "quality_flag": "good"
  }
}
```

### 5.5 重新解析文档

**接口地址：** `POST /documents/{document_id}/reparse`

**功能说明：** 清除旧解析结果，重新解析文档

**路径参数：**


| 参数名         | 类型  | 必填  | 说明   |
| ----------- | --- | --- | ---- |
| document_id | int | 是   | 文档ID |


**响应示例：**

```json
{
  "code": 0,
  "message": "重新解析完成",
  "data": {
    "task_id": "uuid-string",
    "document_id": 1,
    "version_id": 1,
    "status": "pending"
  }
}
```

---

## 六、清洗服务接口 `/cleaning`

### 6.1 创建清洗规则

**接口地址：** `POST /cleaning/rules`

**功能说明：** 创建新的清洗规则

**请求参数：**

```json
{
  "rule_name": "页眉清洗",
  "rule_type": "regex_delete",
  "rule_config": {
    "patterns": ["^第\\s*\\d+\\s*页$"]
  },
  "scope_type": "global",
  "priority": 10,
  "enabled": true,
  "description": "删除页眉标记"
}
```


| 参数名         | 类型     | 必填  | 说明     |
| ----------- | ------ | --- | ------ |
| rule_name   | string | 是   | 规则名称   |
| rule_type   | string | 是   | 规则类型   |
| rule_config | object | 是   | 规则配置   |
| scope_type  | string | 否   | 适用范围类型 |
| priority    | int    | 否   | 优先级    |
| enabled     | bool   | 否   | 是否启用   |
| description | string | 否   | 规则描述   |


**响应示例：**

```json
{
  "code": 0,
  "message": "清洗规则创建成功",
  "data": {
    "id": 1,
    "rule_name": "页眉清洗",
    "rule_type": "regex_delete",
    "rule_config": {...},
    "priority": 10,
    "enabled": true
  }
}
```

### 6.2 更新清洗规则

**接口地址：** `PUT /cleaning/rules/{rule_id}`

**功能说明：** 更新指定的清洗规则

**路径参数：**


| 参数名     | 类型  | 必填  | 说明   |
| ------- | --- | --- | ---- |
| rule_id | int | 是   | 规则ID |


**请求参数：** 同创建清洗规则

**响应示例：**

```json
{
  "code": 0,
  "message": "清洗规则更新成功",
  "data": {...}
}
```

### 6.3 删除清洗规则

**接口地址：** `DELETE /cleaning/rules/{rule_id}`

**功能说明：** 删除指定的清洗规则

**路径参数：**


| 参数名     | 类型  | 必填  | 说明   |
| ------- | --- | --- | ---- |
| rule_id | int | 是   | 规则ID |


**响应示例：**

```json
{
  "code": 0,
  "message": "清洗规则删除成功",
  "data": null
}
```

### 6.4 获取清洗规则列表

**接口地址：** `GET /cleaning/rules`

**功能说明：** 获取清洗规则列表

**请求参数：**


| 参数名          | 类型     | 必填  | 默认值   | 说明          |
| ------------ | ------ | --- | ----- | ----------- |
| page         | int    | 否   | 1     | 页码          |
| page_size    | int    | 否   | 20    | 每页数量（最大100） |
| scope        | string | 否   | -     | 适用范围筛选      |
| rule_type    | string | 否   | -     | 规则类型筛选      |
| enabled_only | bool   | 否   | false | 是否只返回启用的规则  |


**响应示例：**

```json
{
  "code": 0,
  "message": "获取清洗规则列表成功",
  "data": {
    "items": [...],
    "total": 10,
    "page": 1,
    "page_size": 20
  }
}
```

### 6.5 清洗文档

**接口地址：** `POST /cleaning/documents/{document_id}`

**功能说明：** 对指定文档的解析元素进行清洗处理

**路径参数：**


| 参数名         | 类型  | 必填  | 说明   |
| ----------- | --- | --- | ---- |
| document_id | int | 是   | 文档ID |


**请求参数：**


| 参数名        | 类型     | 必填  | 说明   |
| ---------- | ------ | --- | ---- |
| version_id | int    | 否   | 版本ID |
| config     | object | 否   | 清洗配置 |


**响应示例：**

```json
{
  "code": 0,
  "message": "文档清洗成功，共处理 320 个元素",
  "data": {
    "document_id": 1,
    "version_id": 1,
    "total_elements": 320,
    "processed_elements": 320,
    "removed_elements": 15,
    "desensitized_count": 5,
    "avg_quality_score": 0.85,
    "processing_time_ms": 1500
  }
}
```

### 6.6 批量清洗文档

**接口地址：** `POST /cleaning/documents/batch`

**功能说明：** 批量清洗多个文档

**请求参数：**

```json
{
  "document_ids": [1, 2, 3],
  "config": {
    "enable_encoding_fix": true,
    "enable_noise_removal": true
  }
}
```

**响应示例：**

```json
{
  "code": 0,
  "message": "批量清洗完成，成功 2 个，失败 1 个",
  "data": {
    "total": 3,
    "success_count": 2,
    "failed_count": 1,
    "results": [
      {
        "document_id": 1,
        "success": true,
        "total_elements": 320,
        "processing_time_ms": 1500
      }
    ]
  }
}
```

### 6.7 获取清洗日志

**接口地址：** `GET /cleaning/logs`

**功能说明：** 获取清洗日志列表

**请求参数：**


| 参数名         | 类型  | 必填  | 默认值  | 说明          |
| ----------- | --- | --- | ---- | ----------- |
| document_id | int | 是   | 文档ID |             |
| version_id  | int | 否   | 版本ID |             |
| page        | int | 否   | 1    | 页码          |
| page_size   | int | 否   | 20   | 每页数量（最大100） |


**响应示例：**

```json
{
  "code": 0,
  "message": "获取清洗日志列表成功",
  "data": {
    "items": [
      {
        "id": 1,
        "document_id": 1,
        "element_id": "uuid",
        "rule_id": 1,
        "rule_name": "页眉清洗",
        "rule_type": "regex_delete",
        "action": "delete",
        "hit_count": 5,
        "created_at": "2026-05-22T10:00:00+08:00"
      }
    ],
    "total": 50,
    "page": 1,
    "page_size": 20
  }
}
```

---

## 七、切分服务接口 `/chunks`

### 7.1 切分文档

**接口地址：** `POST /chunks/documents/{document_id}`

**功能说明：** 对指定文档的清洗后元素进行语义切分，生成可检索的文本块

**路径参数：**


| 参数名         | 类型  | 必填  | 说明   |
| ----------- | --- | --- | ---- |
| document_id | int | 是   | 文档ID |


**请求参数：**


| 参数名        | 类型     | 必填  | 说明   |
| ---------- | ------ | --- | ---- |
| version_id | int    | 否   | 版本ID |
| config     | object | 否   | 切分配置 |


**切分配置参数：**


| 参数名                | 类型    | 默认值  | 说明       |
| ------------------ | ----- | ---- | -------- |
| target_tokens      | int   | 600  | 目标Token数 |
| max_tokens         | int   | 900  | 最大Token数 |
| min_tokens         | int   | 120  | 最小Token数 |
| overlap_tokens     | int   | 100  | 重叠Token数 |
| semantic_threshold | float | 0.85 | 语义切分阈值   |


**响应示例：**

```json
{
  "code": 0,
  "message": "文档切分成功，共生成 45 个Chunk",
  "data": {
    "document_id": 1,
    "version_id": 1,
    "total_chunks": 45,
    "strategy_used": "title_based",
    "avg_tokens": 580,
    "min_tokens": 120,
    "max_tokens": 890,
    "processing_time_ms": 2000
  }
}
```

### 7.2 批量切分文档

**接口地址：** `POST /chunks/documents/batch`

**功能说明：** 批量切分多个文档

**请求参数：**

```json
{
  "document_ids": [1, 2, 3],
  "config": {
    "target_tokens": 600,
    "overlap_tokens": 100
  }
}
```

**响应示例：**

```json
{
  "code": 0,
  "message": "批量切分完成，成功 2 个，失败 1 个",
  "data": {
    "total_documents": 3,
    "success_count": 2,
    "failed_count": 1,
    "total_chunks": 90,
    "results": [...]
  }
}
```

### 7.3 获取Chunk列表

**接口地址：** `GET /chunks/documents/{document_id}`

**功能说明：** 获取文档的Chunk列表

**路径参数：**


| 参数名         | 类型  | 必填  | 说明   |
| ----------- | --- | --- | ---- |
| document_id | int | 是   | 文档ID |


**请求参数：**


| 参数名        | 类型     | 必填  | 默认值 | 说明          |
| ---------- | ------ | --- | --- | ----------- |
| version_id | int    | 否   | -   | 版本ID        |
| chunk_type | string | 否   | -   | Chunk类型筛选   |
| page       | int    | 否   | 1   | 页码          |
| page_size  | int    | 否   | 20  | 每页数量（最大100） |


**响应示例：**

```json
{
  "code": 0,
  "message": "获取Chunk列表成功",
  "data": {
    "items": [
      {
        "id": 1,
        "chunk_id": "uuid",
        "chunk_index": 1,
        "chunk_type": "paragraph",
        "content": "这是Chunk内容...",
        "token_count": 580,
        "page_start": 1,
        "page_end": 1,
        "title_path": "第一章/第一节",
        "quality_score": 0.92,
        "status": 1
      }
    ],
    "total": 45,
    "page": 1,
    "page_size": 20
  }
}
```

### 7.4 获取Chunk详情

**接口地址：** `GET /chunks/{chunk_id}`

**功能说明：** 获取指定Chunk的详细信息

**路径参数：**


| 参数名      | 类型  | 必填  | 说明         |
| -------- | --- | --- | ---------- |
| chunk_id | int | 是   | Chunk数据库ID |


**响应示例：**

```json
{
  "code": 0,
  "message": "获取Chunk详情成功",
  "data": {
    "id": 1,
    "document_id": 1,
    "version_id": 1,
    "chunk_index": 1,
    "content": "完整的Chunk内容",
    "enhanced_content": "增强后的内容",
    "chunk_type": "paragraph",
    "title_path": "第一章/第一节",
    "page_start": 1,
    "page_end": 1,
    "token_count": 580,
    "quality_score": 0.92,
    "created_at": "2026-05-22T10:00:00+08:00"
  }
}
```

### 7.5 获取切分统计

**接口地址：** `GET /chunks/documents/{document_id}/statistics`

**功能说明：** 获取文档切分统计信息

**路径参数：**


| 参数名         | 类型  | 必填  | 说明   |
| ----------- | --- | --- | ---- |
| document_id | int | 是   | 文档ID |


**响应示例：**

```json
{
  "code": 0,
  "message": "获取统计信息成功",
  "data": {
    "total_chunks": 45,
    "avg_tokens": 580,
    "min_tokens": 120,
    "max_tokens": 890,
    "avg_length": 2900,
    "chunk_type_distribution": {
      "paragraph": 38,
      "table": 5,
      "image": 2
    },
    "quality_distribution": {
      "good": 40,
      "warning": 4,
      "bad": 1
    }
  }
}
```

---

## 八、向量化服务接口 `/embedding`

### 8.1 批量文本向量化

**接口地址：** `POST /embedding/encode`

**功能说明：** 批量将文本列表向量化

**请求参数：**

```json
["RAG知识库系统", "文档检索", "混合检索"]
```

**响应示例：**

```json
{
  "code": 0,
  "message": "成功向量化 3 个文本",
  "data": {
    "count": 3,
    "cached_count": 1,
    "dimension": 1024,
    "model_name": "Qwen3-Embedding"
  }
}
```

### 8.2 单个文本向量化

**接口地址：** `POST /embedding/encode/single`

**功能说明：** 将单个文本向量化

**请求参数：**

```json
"RAG知识库系统"
```

**响应示例：**

```json
{
  "code": 0,
  "message": "文本向量化成功",
  "data": {
    "text": "RAG知识库系统",
    "dimension": 1024,
    "cached": false,
    "model_name": "Qwen3-Embedding"
  }
}
```

### 8.3 向量化文档Chunks

**接口地址：** `POST /embedding/chunks/{document_id}`

**功能说明：** 将文档的所有Chunks向量化并存储到向量数据库

**路径参数：**


| 参数名         | 类型  | 必填  | 说明   |
| ----------- | --- | --- | ---- |
| document_id | int | 是   | 文档ID |


**请求参数：**


| 参数名        | 类型   | 必填  | 默认值  | 说明     |
| ---------- | ---- | --- | ---- | ------ |
| version_id | int  | 否   | -    | 版本ID   |
| use_cache  | bool | 否   | true | 是否使用缓存 |


**响应示例：**

```json
{
  "code": 0,
  "message": "文档向量化成功",
  "data": {
    "document_id": 1,
    "version_id": 1,
    "total_chunks": 45,
    "vectorized_chunks": 45,
    "cached_chunks": 10,
    "processing_time_ms": 5000
  }
}
```

### 8.4 向量检索

**接口地址：** `POST /embedding/search`

**功能说明：** 根据查询文本检索相似的Chunks

**请求参数：**


| 参数名          | 类型     | 必填  | 默认值 | 说明            |
| ------------ | ------ | --- | --- | ------------- |
| query        | string | 是   | -   | 查询文本          |
| top_k        | int    | 否   | 10  | 返回结果数量（最大100） |
| document_ids | string | 否   | -   | 文档ID列表，逗号分隔   |


**响应示例：**

```json
{
  "code": 0,
  "message": "检索成功，返回 10 条结果",
  "data": {
    "query": "RAG知识库系统",
    "top_k": 10,
    "total_results": 10,
    "results": [
      {
        "chunk_id": 1,
        "document_id": 1,
        "content": "Chunk内容...",
        "score": 0.95,
        "title_path": "第一章/第一节"
      }
    ]
  }
}
```

### 8.5 删除文档向量

**接口地址：** `DELETE /embedding/chunks/{document_id}`

**功能说明：** 删除文档的所有向量

**路径参数：**


| 参数名         | 类型  | 必填  | 说明   |
| ----------- | --- | --- | ---- |
| document_id | int | 是   | 文档ID |


**请求参数：**


| 参数名        | 类型  | 必填  | 说明   |
| ---------- | --- | --- | ---- |
| version_id | int | 否   | 版本ID |


**响应示例：**

```json
{
  "code": 0,
  "message": "成功删除 45 个向量",
  "data": {
    "deleted_count": 45
  }
}
```

### 8.6 获取向量统计

**接口地址：** `GET /embedding/statistics`

**功能说明：** 获取向量统计信息

**响应示例：**

```json
{
  "code": 0,
  "message": "获取统计信息成功",
  "data": {
    "collection_name": "document_chunks",
    "total_entities": 1000,
    "dimension": 1024
  }
}
```

### 8.7 初始化向量集合

**接口地址：** `POST /embedding/initialize`

**功能说明：** 初始化Milvus向量集合

**响应示例：**

```json
{
  "code": 0,
  "message": "向量集合初始化成功",
  "data": null
}
```

---

## 九、关键词索引服务接口 `/keyword`

### 9.1 构建关键词索引

**接口地址：** `POST /keyword/index/{document_id}`

**功能说明：** 对文档的Chunks进行分词并构建倒排索引

**路径参数：**


| 参数名         | 类型  | 必填  | 说明   |
| ----------- | --- | --- | ---- |
| document_id | int | 是   | 文档ID |


**请求参数：**


| 参数名        | 类型  | 必填  | 说明   |
| ---------- | --- | --- | ---- |
| version_id | int | 否   | 版本ID |


**响应示例：**

```json
{
  "code": 0,
  "message": "关键词索引构建成功，共索引 45 个Chunk，320 个词项",
  "data": {
    "document_id": 1,
    "version_id": 1,
    "indexed_chunks": 45,
    "total_terms": 320,
    "processing_time_ms": 500
  }
}
```

### 9.2 批量构建关键词索引

**接口地址：** `POST /keyword/index/batch`

**功能说明：** 批量构建关键词索引

**请求参数：**

```json
[1, 2, 3]
```

**响应示例：**

```json
{
  "code": 0,
  "message": "批量索引构建完成，成功 3 个，失败 0 个",
  "data": {
    "total_documents": 3,
    "success_count": 3,
    "failed_count": 0,
    "total_chunks": 135,
    "total_terms": 960,
    "results": [...]
  }
}
```

### 9.3 关键词检索

**接口地址：** `POST /keyword/search`

**功能说明：** 根据关键词检索匹配的Chunks

**请求参数：**


| 参数名          | 类型     | 必填  | 默认值 | 说明             |
| ------------ | ------ | --- | --- | -------------- |
| query        | string | 是   | -   | 查询文本           |
| top_k        | int    | 否   | 50  | 返回结果数量（最大200）  |
| document_ids | string | 否   | -   | 文档ID列表，逗号分隔    |
| chunk_types  | string | 否   | -   | Chunk类型列表，逗号分隔 |


**响应示例：**

```json
{
  "code": 0,
  "message": "检索成功，返回 50 条结果",
  "data": {
    "query": "RAG系统",
    "top_k": 50,
    "total_results": 50,
    "avg_score": 0.75,
    "results": [
      {
        "chunk_id": 1,
        "document_id": 1,
        "content": "Chunk内容...",
        "score": 0.95,
        "matched_terms": ["RAG", "系统"]
      }
    ]
  }
}
```

### 9.4 获取索引统计

**接口地址：** `GET /keyword/statistics`

**功能说明：** 获取关键词索引统计信息

**响应示例：**

```json
{
  "code": 0,
  "message": "获取统计信息成功",
  "data": {
    "total_indexed_chunks": 1000,
    "total_terms": 50000,
    "avg_terms_per_chunk": 50,
    "top_terms": [
      {"term": "RAG", "frequency": 500},
      {"term": "知识库", "frequency": 450}
    ]
  }
}
```

---

## 十、检索服务接口 `/retrieval`

### 10.1 混合检索

**接口地址：** `POST /retrieval/hybrid`

**功能说明：** 结合向量检索和关键词检索，返回融合后的结果

**请求参数：**

```json
{
  "query": "RAG知识库系统如何实现检索？",
  "top_k": 10,
  "doc_ids": [1, 2, 3],
  "fusion_method": "rrf",
  "enable_rewrite": true,
  "vector_top_k": 100,
  "keyword_top_k": 100
}
```


| 参数名            | 类型     | 必填  | 默认值   | 说明                      |
| -------------- | ------ | --- | ----- | ----------------------- |
| query          | string | 是   | -     | 查询文本                    |
| top_k          | int    | 否   | 10    | 返回数量                    |
| doc_ids        | int[]  | 否   | -     | 限定文档ID列表                |
| fusion_method  | string | 否   | rrf   | 融合方法（rrf/weighted/rank） |
| enable_rewrite | bool   | 否   | false | 是否启用查询改写                |


**响应示例：**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "query": "RAG知识库系统如何实现检索？",
    "total": 10,
    "results": [
      {
        "chunk": {
          "chunk_id": 1,
          "document_id": 1,
          "version_id": 1,
          "title_path": "第三章/检索流程",
          "content": "RAG检索系统通过...",
          "score": 0.85,
          "chunk_type": "paragraph"
        },
        "vector_score": 0.9,
        "keyword_score": 0.75,
        "fusion_score": 0.85
      }
    ],
    "retrieval_time_ms": 156
  }
}
```

### 10.2 向量检索

**接口地址：** `POST /retrieval/vector`

**功能说明：** 基于语义相似度进行向量检索（Milvus）

**请求参数：**


| 参数名     | 类型     | 必填  | 默认值 | 说明          |
| ------- | ------ | --- | --- | ----------- |
| query   | string | 是   | -   | 查询文本        |
| top_k   | int    | 否   | 10  | 返回数量（最大100） |
| doc_ids | int[]  | 否   | -   | 限定文档ID列表    |


**响应示例：**

```json
{
  "code": 0,
  "message": "success",
  "data": [
    {
      "chunk_id": 1,
      "document_id": 1,
      "content": "Chunk内容...",
      "score": 0.95
    }
  ]
}
```

### 10.3 关键词检索

**接口地址：** `POST /retrieval/keyword`

**功能说明：** 基于关键词匹配进行全文检索（MySQL BM25）

**请求参数：** 同向量检索

**响应示例：** 同向量检索

### 10.4 检索建议

**接口地址：** `GET /retrieval/suggest`

**功能说明：** 根据已有文本提供检索建议

**请求参数：**


| 参数名   | 类型     | 必填  | 默认值 | 说明         |
| ----- | ------ | --- | --- | ---------- |
| query | string | 是   | -   | 查询文本       |
| limit | int    | 否   | 5   | 返回数量（最大20） |


**响应示例：**

```json
{
  "code": 0,
  "message": "success",
  "data": [
    "RAG系统",
    "RAG知识库",
    "RAG检索"
  ]
}
```

### 10.5 查询改写

**接口地址：** `POST /retrieval/rewrite`

**功能说明：** 对查询进行规范化、多查询生成、子查询分解等处理

**请求参数：**

```json
{
  "query": "RAG系统是啥？",
  "enable_multi_query": true,
  "enable_subquery": true,
  "enable_hyde": false,
  "enable_background": false,
  "max_queries": 5
}
```


| 参数名                | 类型     | 必填  | 默认值   | 说明        |
| ------------------ | ------ | --- | ----- | --------- |
| query              | string | 是   | -     | 原始查询      |
| enable_multi_query | bool   | 否   | false | 是否启用多查询生成 |
| enable_subquery    | bool   | 否   | false | 是否启用子查询分解 |
| enable_hyde        | bool   | 否   | false | 是否启用HyDE  |
| enable_background  | bool   | 否   | false | 是否启用后退提示  |
| max_queries        | int    | 否   | 5     | 最大查询数量    |


**响应示例：**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "original_query": "RAG系统是啥？",
    "normalized_query": "rag 系统 是 啥",
    "multi_queries": [
      "RAG系统是啥？",
      "rag 系统",
      "RAG平台是什么",
      "rag retrieval system"
    ],
    "sub_queries": [],
    "hyde_answer": null,
    "background_query": null
  }
}
```

### 10.6 融合测试

**接口地址：** `POST /retrieval/fusion`

**功能说明：** 测试不同融合方法的效果

**请求参数：**

```json
{
  "vector_results": [...],
  "keyword_results": [...],
  "method": "rrf",
  "rrf_k": 60,
  "vector_weight": 0.6,
  "keyword_weight": 0.4
}
```

**响应示例：**

```json
{
  "code": 0,
  "message": "success",
  "data": [...]
}
```

### 10.7 获取检索统计

**接口地址：** `GET /retrieval/statistics`

**功能说明：** 获取检索统计信息

**响应示例：**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "total_vectors": 10000,
    "total_keywords": 50000,
    "avg_vector_search_time_ms": 50,
    "avg_keyword_search_time_ms": 20,
    "avg_fusion_time_ms": 5
  }
}
```

---

## 十一、问答服务接口 `/qa`

### 11.1 问答接口

**接口地址：** `POST /qa`

**功能说明：** 根据用户问题，生成答案

**请求参数：**

```json
{
  "question": "RAG知识库系统如何实现检索？",
  "session_id": "uuid",
  "use_rerank": true,
  "top_k": 20,
  "rerank_top_k": 10,
  "max_context_tokens": 4000,
  "temperature": 0.7
}
```


| 参数名                | 类型     | 必填  | 默认值  | 说明          |
| ------------------ | ------ | --- | ---- | ----------- |
| question           | string | 是   | -    | 用户问题        |
| session_id         | string | 否   | -    | 会话ID        |
| use_rerank         | bool   | 否   | true | 是否使用重排      |
| top_k              | int    | 否   | 20   | 检索TopK      |
| rerank_top_k       | int    | 否   | 10   | 重排后TopK     |
| max_context_tokens | int    | 否   | 4000 | 最大上下文Token数 |
| temperature        | float  | 否   | 0.7  | 生成温度        |


**响应示例：**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "qa_id": 1,
    "question": "RAG知识库系统如何实现检索？",
    "answer": "关于RAG知识库检索...",
    "references": [
      {
        "chunk_id": 1,
        "document_id": 1,
        "title_path": "第三章/检索流程",
        "page_start": 10,
        "content_preview": "RAG检索系统通过..."
      }
    ],
    "session_id": "uuid",
    "total_time_ms": 1250,
    "retrieval_time_ms": 200,
    "rerank_time_ms": 150,
    "context_time_ms": 50,
    "generation_time_ms": 850
  }
}
```

### 11.2 提交用户反馈

**接口地址：** `POST /qa/feedback`

**功能说明：** 提交用户对问答答案的反馈

**请求参数：**

```json
{
  "qa_id": 1,
  "feedback": 0,
  "feedback_reason": "答案不准确，希望更详细",
  "quality_score": 2
}
```


| 参数名             | 类型     | 必填  | 说明              |
| --------------- | ------ | --- | --------------- |
| qa_id           | int    | 是   | 问答记录ID          |
| feedback        | int    | 是   | 反馈值（1-满意 0-不满意） |
| feedback_reason | string | 否   | 反馈原因            |
| quality_score   | int    | 否   | 质量评分（1-5）       |


**响应示例：**

```json
{
  "code": 0,
  "message": "反馈提交成功",
  "data": {
    "success": true,
    "message": "反馈提交成功",
    "analysis_id": 1
  }
}
```

### 11.3 查询会话历史

**接口地址：** `GET /qa/history`

**功能说明：** 获取指定会话的历史问答记录

**请求参数：**


| 参数名        | 类型     | 必填  | 默认值 | 说明          |
| ---------- | ------ | --- | --- | ----------- |
| session_id | string | 是   | -   | 会话ID        |
| page_no    | int    | 否   | 1   | 页码          |
| page_size  | int    | 否   | 20  | 每页数量（最大100） |


**响应示例：**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [...],
    "total": 50,
    "page_no": 1,
    "page_size": 20,
    "pages": 3
  }
}
```

### 11.4 查询问答日志

**接口地址：** `GET /qa/logs`

**功能说明：** 查询问答历史记录

**请求参数：**


| 参数名            | 类型     | 必填  | 默认值 | 说明               |
| -------------- | ------ | --- | --- | ---------------- |
| tenant_id      | int    | 否   | 1   | 租户ID             |
| user_id        | int    | 否   | -   | 用户ID             |
| session_id     | string | 否   | -   | 会话ID             |
| start_date     | string | 否   | -   | 开始日期（YYYY-MM-DD） |
| end_date       | string | 否   | -   | 结束日期（YYYY-MM-DD） |
| has_feedback   | bool   | 否   | -   | 是否有反馈            |
| feedback_value | int    | 否   | -   | 反馈值（1-满意 0-不满意）  |
| min_score      | int    | 否   | -   | 最低评分（1-5）        |
| max_score      | int    | 否   | -   | 最高评分（1-5）        |
| keyword        | string | 否   | -   | 关键词搜索            |
| page_no        | int    | 否   | 1   | 页码               |
| page_size      | int    | 否   | 20  | 每页数量（最大100）      |


**响应示例：**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [
      {
        "id": 1,
        "user_id": 1,
        "session_id": "uuid",
        "question": "RAG系统如何工作？",
        "answer": "RAG系统通过...",
        "feedback": "helpful",
        "quality_score": 5,
        "created_at": "2026-05-23T12:00:00+08:00"
      }
    ],
    "total": 100,
    "page_no": 1,
    "page_size": 20,
    "pages": 5
  }
}
```

### 11.5 获取问答日志详情

**接口地址：** `GET /qa/logs/{qa_id}`

**功能说明：** 获取指定问答记录的详细信息

**路径参数：**


| 参数名   | 类型  | 必填  | 说明     |
| ----- | --- | --- | ------ |
| qa_id | int | 是   | 问答日志ID |


**响应示例：**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": 1,
    "question": "RAG系统如何工作？",
    "answer": "RAG系统通过...",
    "references": [...],
    "feedback": 1,
    "feedback_reason": null,
    "quality_score": 5,
    "avg_retrieval_score": 0.85,
    "total_time_ms": 1250,
    "created_at": "2026-05-23T12:00:00+08:00"
  }
}
```

### 11.6 获取反馈统计

**接口地址：** `GET /qa/feedback/statistics`

**功能说明：** 获取反馈统计信息

**请求参数：**


| 参数名        | 类型     | 必填  | 默认值 | 说明   |
| ---------- | ------ | --- | --- | ---- |
| tenant_id  | int    | 否   | 1   | 租户ID |
| start_date | string | 否   | -   | 开始日期 |
| end_date   | string | 否   | -   | 结束日期 |


**响应示例：**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "total_count": 1000,
    "positive_count": 850,
    "negative_count": 150,
    "positive_rate": 85.0,
    "avg_quality_score": 4.2,
    "top_issues": [
      {"category": "retrieval_inaccurate", "count": 80, "percentage": 53.33},
      {"category": "answer_incorrect", "count": 70, "percentage": 46.67}
    ],
    "retrieval_issue_count": 80,
    "generation_issue_count": 70,
    "pending_analysis_count": 50,
    "handled_count": 100
  }
}
```

### 11.7 查询会话列表

**接口地址：** `GET /qa/sessions`

**功能说明：** 获取用户的会话列表

**请求参数：**


| 参数名       | 类型  | 必填  | 默认值 | 说明          |
| --------- | --- | --- | --- | ----------- |
| user_id   | int | 否   | -   | 用户ID        |
| tenant_id | int | 否   | 1   | 租户ID        |
| page_no   | int | 否   | 1   | 页码          |
| page_size | int | 否   | 20  | 每页数量（最大100） |


**响应示例：**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [...],
    "total": 50,
    "page_no": 1,
    "page_size": 20,
    "pages": 3
  }
}
```

### 11.8 获取问答统计

**接口地址：** `GET /qa/statistics`

**功能说明：** 获取问答统计信息

**请求参数：**


| 参数名        | 类型     | 必填  | 默认值 | 说明   |
| ---------- | ------ | --- | --- | ---- |
| tenant_id  | int    | 否   | 1   | 租户ID |
| start_date | string | 否   | -   | 开始日期 |
| end_date   | string | 否   | -   | 结束日期 |


**响应示例：**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "total_count": 1000,
    "avg_quality_score": 4.2,
    "helpful_count": 850,
    "not_helpful_count": 150,
    "avg_retrieval_time_ms": 185.5,
    "avg_generation_time_ms": 820.3
  }
}
```

### 11.9 创建优化规则

**接口地址：** `POST /qa/rules`

**功能说明：** 创建新的优化规则

**请求参数：**

```json
{
  "rule_name": "提高检索阈值",
  "rule_type": "retrieval",
  "rule_config": {
    "min_score_threshold": 0.5,
    "top_k": 20
  },
  "trigger_condition": {
    "issue_category": "retrieval_inaccurate",
    "min_occurrence": 10
  },
  "priority": 1,
  "enabled": true,
  "description": "当检索不准确问题超过10次时，提高检索阈值",
  "expected_effect": "减少低质量检索结果"
}
```

**响应示例：**

```json
{
  "code": 0,
  "message": "规则创建成功",
  "data": {...}
}
```

### 11.10 查询优化规则

**接口地址：** `GET /qa/rules`

**功能说明：** 查询优化规则列表

**请求参数：**


| 参数名       | 类型     | 必填  | 默认值 | 说明          |
| --------- | ------ | --- | --- | ----------- |
| rule_type | string | 否   | -   | 规则类型        |
| enabled   | bool   | 否   | -   | 是否启用        |
| page_no   | int    | 否   | 1   | 页码          |
| page_size | int    | 否   | 20  | 每页数量（最大100） |


**响应示例：**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [...],
    "total": 10,
    "page_no": 1,
    "page_size": 20,
    "pages": 1
  }
}
```

### 11.11 更新优化规则

**接口地址：** `PUT /qa/rules/{rule_id}`

**功能说明：** 更新指定的优化规则

**路径参数：**


| 参数名     | 类型  | 必填  | 说明   |
| ------- | --- | --- | ---- |
| rule_id | int | 是   | 规则ID |


**请求参数：** 同创建优化规则

**响应示例：**

```json
{
  "code": 0,
  "message": "规则更新成功",
  "data": {...}
}
```

### 11.12 删除优化规则

**接口地址：** `DELETE /qa/rules/{rule_id}`

**功能说明：** 删除指定的优化规则

**路径参数：**


| 参数名     | 类型  | 必填  | 说明   |
| ------- | --- | --- | ---- |
| rule_id | int | 是   | 规则ID |


**响应示例：**

```json
{
  "code": 0,
  "message": "规则删除成功",
  "data": null
}
```

---

## 十二、队列管理接口 `/queue`

### 12.1 发布解析任务

**接口地址：** `POST /queue/publish/parse`

**功能说明：** 发布解析任务到队列

**请求参数：**

```json
{
  "document_id": 1,
  "version_id": 1,
  "priority": 5,
  "file_path": "/path/to/file.pdf",
  "config": {}
}
```

**响应示例：**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "task_id": "uuid-string",
    "queue_name": "rag_parse_queue",
    "routing_key": "rag.parse.start"
  }
}
```

### 12.2 发布清洗任务

**接口地址：** `POST /queue/publish/clean`

**功能说明：** 发布清洗任务到队列

**请求参数：**

```json
{
  "document_id": 1,
  "version_id": 1,
  "priority": 5,
  "element_ids": [1, 2, 3],
  "config": {}
}
```

**响应示例：**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "task_id": "uuid-string",
    "queue_name": "rag_clean_queue",
    "routing_key": "rag.clean.start"
  }
}
```

### 12.3 发布切分任务

**接口地址：** `POST /queue/publish/chunk`

**功能说明：** 发布切分任务到队列

**请求参数：**

```json
{
  "document_id": 1,
  "version_id": 1,
  "priority": 5,
  "element_ids": [],
  "config": {}
}
```

### 12.4 发布向量化任务

**接口地址：** `POST /queue/publish/embedding`

**功能说明：** 发布向量化任务到队列

**请求参数：**

```json
{
  "document_id": 1,
  "version_id": 1,
  "priority": 5,
  "chunk_ids": [1, 2, 3],
  "batch_size": 32
}
```

### 12.5 发布索引任务

**接口地址：** `POST /queue/publish/index`

**功能说明：** 发布索引任务到队列

**请求参数：**

```json
{
  "document_id": 1,
  "version_id": 1,
  "priority": 5,
  "chunk_ids": [1, 2, 3],
  "index_type": "keyword"
}
```

### 12.6 批量发布任务

**接口地址：** `POST /queue/publish/batch`

**功能说明：** 批量发布任务到队列

**请求参数：**

```json
{
  "task_type": "parse",
  "tasks": [
    {
      "document_id": 1,
      "version_id": 1,
      "priority": 5
    },
    {
      "document_id": 2,
      "version_id": 2,
      "priority": 5
    }
  ]
}
```

**响应示例：**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "total": 2,
    "success": 2,
    "failed": 0,
    "tasks": [
      {"task_id": "uuid1", "success": true},
      {"task_id": "uuid2", "success": true}
    ]
  }
}
```

### 12.7 获取队列列表

**接口地址：** `GET /queue/queues`

**功能说明：** 获取所有队列的列表

**响应示例：**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "queues": [
      {"name": "rag_parse_queue", "display_name": "Rag Parse Queue"},
      {"name": "rag_clean_queue", "display_name": "Rag Clean Queue"},
      {"name": "rag_chunk_queue", "display_name": "Rag Chunk Queue"},
      {"name": "rag_embedding_queue", "display_name": "Rag Embedding Queue"},
      {"name": "rag_index_queue", "display_name": "Rag Index Queue"}
    ]
  }
}
```

### 12.8 获取队列统计

**接口地址：** `GET /queue/queues/{queue_name}/stats`

**功能说明：** 获取指定队列的统计信息

**路径参数：**


| 参数名        | 类型     | 必填  | 说明   |
| ---------- | ------ | --- | ---- |
| queue_name | string | 是   | 队列名称 |


**响应示例：**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "queue_name": "rag_parse_queue",
    "message_count": 10,
    "consumer_count": 2,
    "note": "统计信息需要连接RabbitMQ获取"
  }
}
```

### 12.9 获取死信队列消息

**接口地址：** `GET /queue/dlx/messages`

**功能说明：** 获取死信队列中的消息

**请求参数：**


| 参数名    | 类型  | 必填  | 默认值 | 说明     |
| ------ | --- | --- | --- | ------ |
| limit  | int | 否   | 10  | 返回数量限制 |
| offset | int | 否   | 0   | 偏移量    |


**响应示例：**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "messages": [],
    "total": 0,
    "note": "死信消息需要连接RabbitMQ获取"
  }
}
```

### 12.10 删除死信消息

**接口地址：** `DELETE /queue/dlx/messages/{message_id}`

**功能说明：** 删除指定的死信消息

**路径参数：**


| 参数名        | 类型     | 必填  | 说明   |
| ---------- | ------ | --- | ---- |
| message_id | string | 是   | 消息ID |


**响应示例：**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "message_id": "uuid",
    "deleted": true
  }
}
```

### 12.11 清空死信队列

**接口地址：** `DELETE /queue/dlx/messages`

**功能说明：** 清空死信队列中的所有消息

**响应示例：**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "cleared": true,
    "note": "死信队列已清空"
  }
}
```

---

## 附录

### A. 文档状态说明


| 状态值 | 状态名  | 说明         |
| --- | ---- | ---------- |
| 0   | 待解析  | 文档已上传，等待解析 |
| 1   | 解析中  | 正在解析文档     |
| 2   | 已解析  | 文档解析完成     |
| 3   | 解析失败 | 文档解析失败     |
| 4   | 已清洗  | 文档已清洗      |
| 5   | 已切分  | 文档已切分      |
| 6   | 已向量化 | 文档已向量化     |
| 9   | 已删除  | 文档已删除      |


### B. 任务类型说明


| 类型     | 说明    |
| ------ | ----- |
| import | 导入任务  |
| parse  | 解析任务  |
| clean  | 清洗任务  |
| chunk  | 切分任务  |
| embed  | 向量化任务 |
| index  | 索引任务  |


### C. 任务状态说明


| 状态        | 说明  |
| --------- | --- |
| pending   | 等待中 |
| running   | 执行中 |
| completed | 已完成 |
| failed    | 失败  |
| retry     | 重试中 |


### D. Chunk类型说明


| 类型        | 说明  |
| --------- | --- |
| paragraph | 段落  |
| title     | 标题  |
| table     | 表格  |
| image     | 图片  |
| chart     | 图表  |
| list      | 列表  |
| code      | 代码  |
| header    | 页眉  |
| footer    | 页脚  |


### E. 质量标记说明


| 标记      | 说明   |
| ------- | ---- |
| good    | 质量良好 |
| warning | 质量警告 |
| bad     | 质量差  |


---

*本文档由系统自动生成*