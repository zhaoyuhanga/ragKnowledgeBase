# RAG 知识库系统

基于 FastAPI 的智能 RAG（检索增强生成）知识库系统，支持多格式文档解析、混合检索与智能问答。

## 项目概述

RAG 知识库系统是一个完整的文档智能处理与问答平台，具备以下核心能力：

- **多格式文档解析**：支持 Word、PDF、图片、表格等多种格式
- **语义向量化存储**：基于 Qwen3-Embedding 实现文本向量化
- **混合检索能力**：融合向量语义检索与关键词精确检索
- **智能问答服务**：基于检索增强生成，为用户提供精准答案
- **持续优化闭环**：通过用户反馈不断优化系统效果

## 技术栈


| 组件    | 技术                    | 版本    |
| ----- | --------------------- | ----- |
| 后端框架  | Python 3.12 + FastAPI | 3.12+ |
| 向量数据库 | Milvus                | 2.4+  |
| 主数据库  | MySQL                 | 8.0   |
| 消息队列  | RabbitMQ              | 3.12+ |
| 缓存服务  | Redis                 | 7.x   |
| 文档解析  | PyMuPDF + python-docx | -     |


## 快速开始

### 方式一：使用 Docker Compose（推荐）

#### 1. 启动依赖服务

```bash
# Windows
cd docker
.\start-docker.bat

# Linux/macOS
cd docker
chmod +x start-docker.sh
./start-docker.sh
```

#### 2. 启动后端服务

```bash
# Windows
.\scripts\start-backend.bat

# Linux/macOS
chmod +x scripts/start-backend.sh
./scripts/start-backend.sh
```

### 方式二：本地开发环境

#### 1. 环境要求

- Python 3.12+
- MySQL 8.0（端口 3308）
- Redis 7.x（端口 6379）
- Milvus 2.4+（端口 19530）
- RabbitMQ 3.12+（端口 5672）

#### 2. 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

#### 3. 初始化数据库

```bash
# Windows
.\scripts\db-init.bat

# Linux/macOS
chmod +x scripts/db-init.sh
./scripts/db-init.sh
```

#### 4. 启动服务

```bash
cd backend
python -m uvicorn src.main:app --host 127.0.0.1 --port 8011 --reload
```

### 验证服务

服务启动后，可通过以下地址访问：


| 服务          | 地址                                                           |
| ----------- | ------------------------------------------------------------ |
| API 文档      | [http://127.0.0.1:8011/docs](http://127.0.0.1:8011/docs)     |
| ReDoc 文档    | [http://127.0.0.1:8011/redoc](http://127.0.0.1:8011/redoc)   |
| 健康检查        | [http://127.0.0.1:8011/health](http://127.0.0.1:8011/health) |
| RabbitMQ 管理 | [http://localhost:15672](http://localhost:15672)             |
| Milvus 管理   | [http://localhost:9091](http://localhost:9091)               |


### API 测试

```bash
# 健康检查
curl http://127.0.0.1:8011/health

# 文档列表
curl http://127.0.0.1:8011/api/v1/documents

# 问答接口
curl -X POST http://127.0.0.1:8011/api/v1/qa \
  -H "Content-Type: application/json" \
  -d '{"question": "RAG系统如何工作？"}'
```

## 项目结构

```
rag-system/
├── backend/                    # 后端项目
│   ├── src/
│   │   ├── main.py            # 应用入口
│   │   ├── core/              # 核心配置
│   │   │   ├── config.py      # 配置管理
│   │   │   ├── database.py    # 数据库连接
│   │   │   ├── milvus.py     # Milvus连接
│   │   │   ├── mq.py         # RabbitMQ连接
│   │   │   └── cache.py      # Redis缓存
│   │   └── app/
│   │       ├── api/          # API路由
│   │       │   └── v1/       # API版本
│   │       ├── models/       # 数据模型
│   │       ├── schemas/      # Pydantic模型
│   │       ├── services/     # 业务逻辑
│   │       ├── repositories/ # 数据访问
│   │       ├── parsers/      # 文档解析器
│   │       └── common/       # 公共模块
│   ├── tests/                 # 测试文件
│   └── resources/            # 配置文件
│       ├── application-local.yml
│       ├── application-dev.yml
│       └── application-prod.yml
├── docker/                    # Docker配置
│   ├── docker-compose.yml     # 基础服务编排
│   ├── docker-compose.dev.yml # 开发环境
│   ├── docker-compose.prod.yml # 生产环境
│   ├── Dockerfile            # 后端镜像
│   └── mysql/init.sql        # 数据库初始化
├── scripts/                   # 启动脚本
│   ├── start-backend.bat     # Windows启动
│   ├── start-backend.sh      # Linux/macOS启动
│   ├── stop-all.bat          # Windows停止
│   ├── stop-all.sh           # Linux/macOS停止
│   ├── db-init.bat           # Windows数据库初始化
│   └── db-init.sh            # Linux/macOS数据库初始化
└── docs/                      # 文档目录
```

## API 接口

### 文档管理


| 方法     | 路径                     | 说明   |
| ------ | ---------------------- | ---- |
| POST   | /api/v1/documents      | 上传文档 |
| GET    | /api/v1/documents      | 文档列表 |
| GET    | /api/v1/documents/{id} | 文档详情 |
| DELETE | /api/v1/documents/{id} | 删除文档 |


### 问答接口


| 方法   | 路径                  | 说明   |
| ---- | ------------------- | ---- |
| POST | /api/v1/qa          | 问答生成 |
| POST | /api/v1/qa/feedback | 提交反馈 |
| GET  | /api/v1/qa/logs     | 查询日志 |


### 检索接口


| 方法   | 路径                        | 说明   |
| ---- | ------------------------- | ---- |
| POST | /api/v1/retrieval         | 混合检索 |
| POST | /api/v1/retrieval/rewrite | 查询改写 |


### 清洗与切分


| 方法   | 路径                     | 说明     |
| ---- | ---------------------- | ------ |
| POST | /api/v1/cleaning/rules | 清洗规则管理 |
| POST | /api/v1/chunks/split   | 文档切分   |


### 向量化


| 方法   | 路径                         | 说明   |
| ---- | -------------------------- | ---- |
| POST | /api/v1/embedding/generate | 生成向量 |
| POST | /api/v1/embedding/search   | 向量检索 |


## 配置说明

### 环境配置

系统支持三种环境配置：


| 环境    | 配置文件                  | 用途   |
| ----- | --------------------- | ---- |
| local | application-local.yml | 本地开发 |
| dev   | application-dev.yml   | 团队联调 |
| prod  | application-prod.yml  | 生产部署 |


### 切换环境

```bash
# Linux/macOS
export APP_ENV=dev

# Windows
set APP_ENV=dev
```

### 敏感信息

生产环境建议使用环境变量覆盖敏感配置：

```bash
export DATABASE_PASSWORD=your_password
export REDIS_PASSWORD=your_password
export JWT_SECRET_KEY=your_secret_key
```

## 开发指南

### 代码规范

- 所有代码使用 UTF-8 编码
- 代码注释使用中文
- 遵循 PEP 8 规范
- 使用 type hints

### 测试

```bash
# 运行所有测试
cd backend
pytest tests/ -v

# 运行指定测试
pytest tests/test_document.py -v

# 生成覆盖率报告
pytest tests/ --cov=src --cov-report=html
```

### 日志

日志默认输出到 `./logs/app.log`，可在 `application-*.yml` 中配置。

## 部署指南

### Docker Compose 部署（生产环境）

```bash
cd docker
docker compose -f docker-compose.prod.yml up -d
```

### 手动部署

1. 安装依赖服务（MySQL、Redis、Milvus、RabbitMQ）
2. 配置数据库连接
3. 构建后端应用
4. 配置反向代理（Nginx）
5. 配置 HTTPS

## 常见问题

### Q: 服务启动失败？

检查以下服务是否正常运行：

- MySQL（端口 3308）
- Redis（端口 6379）
- Milvus（端口 19530）
- RabbitMQ（端口 5672）

### Q: 数据库连接失败？

1. 检查 MySQL 服务状态
2. 验证用户名密码
3. 确认端口映射正确

### Q: 向量检索无结果？

1. 确认文档已导入并完成向量化
2. 检查 Milvus 服务状态
3. 验证向量维度配置正确

## 许可证

本项目仅供学习和研究使用。

## 联系方式

如有问题，请提交 Issue 或联系开发团队。