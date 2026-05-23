# RAG知识库系统 - 后端项目

## 项目简介

RAG（Retrieval-Augmented Generation）知识库系统后端，基于 Python 3.12 + FastAPI 构建，提供文档智能解析、混合检索与智能问答服务。

## 技术栈

| 组件 | 技术 | 版本 |
|------|------|------|
| 后端框架 | Python 3.12 + FastAPI | 3.12+ |
| 主数据库 | MySQL | 8.0 |
| 向量数据库 | Milvus | 2.4+ |
| 消息队列 | RabbitMQ | 3.12+ |
| 缓存 | Redis | 7.x |
| 文档解析 | PyMuPDF + python-docx | - |

## 项目结构

```
backend/
├── src/
│   ├── main.py                 # 应用入口
│   ├── core/                   # 核心配置
│   │   ├── config.py           # 配置管理
│   │   ├── database.py         # 数据库连接
│   │   ├── milvus.py           # Milvus连接
│   │   ├── mq.py               # RabbitMQ连接
│   │   └── cache.py            # Redis缓存
│   └── app/
│       ├── api/v1/             # API路由
│       │   ├── health.py       # 健康检查
│       │   ├── documents.py    # 文档管理
│       │   ├── retrieval.py    # 检索服务
│       │   └── qa.py           # 问答服务
│       ├── models/             # 数据模型
│       │   ├── document.py     # 文档模型
│       │   ├── chunk.py        # Chunk模型
│       │   └── qa.py          # 问答日志模型
│       ├── schemas/            # Pydantic模型
│       ├── services/           # 业务逻辑
│       │   ├── document_service.py
│       │   ├── retrieval_service.py
│       │   └── qa_service.py
│       ├── repositories/       # 数据访问层
│       └── common/            # 公共模块
│           ├── response.py     # 统一响应
│           ├── exception.py    # 统一异常
│           ├── logging.py      # 日志配置
│           └── middleware.py   # 中间件
├── resources/                   # 配置文件
│   ├── application-local.yml   # 本地环境
│   ├── application-dev.yml     # 开发环境
│   └── application-prod.yml   # 生产环境
├── tests/                       # 测试文件
└── requirements.txt            # 依赖包
```

## 环境配置

### 前置要求

1. Python 3.12+
2. MySQL 8.0（端口3308）
3. Redis 7.x（端口6379）
4. Milvus 2.4+（端口19530）
5. RabbitMQ 3.12+（端口5672）

### 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

### 环境变量

创建 `.env` 文件或设置环境变量：

```bash
# 环境配置
export APP_ENV=local  # local/dev/prod

# MySQL配置
export MYSQL_HOST=localhost
export MYSQL_PORT=3308
export MYSQL_USERNAME=root
export MYSQL_PASSWORD=root
export MYSQL_DATABASE=rag_db

# Redis配置
export REDIS_HOST=localhost
export REDIS_PORT=6379
export REDIS_PASSWORD=

# Milvus配置
export MILVUS_HOST=localhost
export MILVUS_PORT=19530

# RabbitMQ配置
export RABBITMQ_HOST=localhost
export RABBITMQ_PORT=5672
export RABBITMQ_USERNAME=guest
export RABBITMQ_PASSWORD=guest

# JWT配置
export JWT_SECRET_KEY=your-secret-key
```

## 启动服务

### 开发环境

```bash
cd backend
uvicorn src.main:app --reload --host 127.0.0.1 --port 8011
```

### 生产环境

```bash
cd backend
uvicorn src.main:app --host 0.0.0.0 --port 8011 --workers 4
```

## API文档

启动服务后访问：
- Swagger UI: http://localhost:8011/docs
- ReDoc: http://localhost:8011/redoc

## 接口列表

### 健康检查

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/v1/health` | GET | 健康检查 |
| `/api/v1/health/db` | GET | 数据库健康检查 |
| `/api/v1/health/redis` | GET | Redis健康检查 |
| `/api/v1/health/milvus` | GET | Milvus健康检查 |
| `/api/v1/health/rabbitmq` | GET | RabbitMQ健康检查 |

### 文档管理

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/v1/documents` | GET | 查询文档列表 |
| `/api/v1/documents/{id}` | GET | 获取文档详情 |
| `/api/v1/documents` | POST | 创建文档 |
| `/api/v1/documents/{id}` | PUT | 更新文档 |
| `/api/v1/documents/{id}` | DELETE | 删除文档 |
| `/api/v1/documents/upload` | POST | 上传文档 |

### 检索服务

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/v1/retrieval/hybrid` | POST | 混合检索 |
| `/api/v1/retrieval/vector` | POST | 向量检索 |
| `/api/v1/retrieval/keyword` | POST | 关键词检索 |
| `/api/v1/retrieval/suggest` | GET | 检索建议 |

### 问答服务

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/v1/qa` | POST | 问答 |
| `/api/v1/qa/history` | GET | 会话历史 |
| `/api/v1/qa/{id}/feedback` | POST | 提交反馈 |
| `/api/v1/qa/sessions` | GET | 会话列表 |

## 运行测试

```bash
cd backend
pytest tests/ -v --tb=short
```

## 统一响应格式

### 成功响应

```json
{
  "code": 0,
  "message": "success",
  "data": {},
  "traceId": "202605221200000001",
  "timestamp": "2026-05-22T12:00:00+08:00"
}
```

### 错误响应

```json
{
  "code": "BIZ_2001",
  "message": "数据不存在",
  "data": null,
  "traceId": "202605221200000001",
  "timestamp": "2026-05-22T12:00:00+08:00"
}
```

## 错误码规范

| 前缀 | 范围 | 说明 |
|------|------|------|
| SYS_1xxx | 1000-1999 | 系统错误 |
| BIZ_2xxx | 2000-2999 | 业务错误 |
| DOC_3xxx | 3000-3999 | 文档错误 |
| RET_4xxx | 4000-4999 | 检索错误 |
| AUTH_9xxx | 9000-9999 | 认证错误 |

## 开发规范

1. 所有代码注释使用中文
2. 所有日志输出使用中文
3. 配置文件使用YAML格式
4. 敏感信息从环境变量读取
5. 路由层只做参数校验，业务逻辑在服务层

## 许可证

MIT License
