# XX 批次名称

## 基本信息


| 项目   | 内容         |
| ---- | ---------- |
| 批次编号 | XX         |
| 批次名称 | 功能模块名称     |
| 依赖批次 | XX批次、XX批次  |
| 预计工时 | X小时        |
| 实际工时 | X小时        |
| 执行日期 | YYYY-MM-DD |


---

## 一、Cursor 输入文案

```text
你是资深[技术栈]工程师。请执行第 XX 批开发。

请先阅读：
1. D:/work/project/requirements-doc.md
2. D:/work/project/docs/00-项目开发总纲.md
3. D:/work/project/docs/XX-前置文档.md
4. D:/work/project/docs/XX-本批次文档.md
5. D:/work/project/docs/template/规范强制标准.md  【强制引用】

【强制规范引用】：
请严格遵循 docs/template/规范强制标准.md 中的所有强制规范：

1. 日志格式：JSON格式，包含traceId、method、uri、costMs等字段
2. 接口规范：统一响应格式，code/message/data/traceId/timestamp
3. 环境配置：local/dev/prod 三环境支持
4. 数据库规范：所有表和字段必须有中文注释
5. 代码组织：路由→服务→模型的层级调用
6. 命名规范：数据库小写下划线，Python大驼峰

本批次目标：
1. 目标一
2. 目标二
3. 目标三

前置条件：
- 已完成XX批次的开发
- 后端/前端服务可正常启动

具体任务：
一、任务一：
1. 子任务1.1
2. 子任务1.2

二、任务二：
1. 子任务2.1
2. 子任务2.2

硬性要求：
- 约束条件一
- 约束条件二
- 【强制】所有代码注释必须使用中文
- 【强制】所有日志必须输出中文

验收必须包含：
1. 修改文件列表。
2. 新增能力说明。
3. 验证命令。
4. 验证结果。
5. 未完成事项或风险。
```

---

## 二、批次概述

[简要说明本批次的主要目标和范围]

### 2.1 目标

1. 目标一：详细说明
2. 目标二：详细说明
3. 目标三：详细说明

### 2.2 范围

**包含：**

- 功能范围一
- 功能范围二

**不包含：**

- 排除功能一
- 排除功能二

### 2.3 技术栈


| 层级  | 技术                   | 版本    |
| --- | -------------------- | ----- |
| 后端  | Python FastAPI       | 3.12+ |
| 前端  | Vue 3 + Element Plus | 最新    |
| 数据库 | MySQL                | 8.0   |
| 缓存  | Redis                | 7.x   |


---

## 三、详细设计

### 3.1 功能模块图

```
┌─────────────────────────────────────────────────────────┐
│                      模块名称                            │
├─────────────────────────────────────────────────────────┤
│  子模块1          │  子模块2          │  子模块3        │
│  ┌─────────┐     │  ┌─────────┐     │  ┌─────────┐     │
│  │ 功能点A │     │  │ 功能点C │     │  │ 功能点E │     │
│  └─────────┘     │  └─────────┘     │  └─────────┘     │
│  ┌─────────┐     │  ┌─────────┐     │  ┌─────────┐     │
│  │ 功能点B │     │  │ 功能点D │     │  │ 功能点F │     │
│  └─────────┘     │  └─────────┘     │  └─────────┘     │
└─────────────────────────────────────────────────────────┘
```

### 3.2 API 设计

#### 3.2.1 接口列表


| 方法     | 路径               | 说明  | 依赖  |
| ------ | ---------------- | --- | --- |
| POST   | /api/v1/xxx      | 创建  | 认证  |
| GET    | /api/v1/xxx      | 查询  | 认证  |
| PUT    | /api/v1/xxx/{id} | 更新  | 认证  |
| DELETE | /api/v1/xxx/{id} | 删除  | 认证  |


#### 3.2.2 接口详情

##### POST /api/v1/xxx

**请求参数：**


| 参数名    | 类型      | 必填  | 说明  | 示例  |
| ------ | ------- | --- | --- | --- |
| name   | string  | 是   | 名称  | 测试  |
| status | integer | 否   | 状态  | 1   |


**请求示例：**

```json
{
  "name": "测试",
  "status": 1
}
```

**响应示例：**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": 1,
    "name": "测试",
    "status": 1,
    "created_at": "2026-05-21T12:00:00+08:00"
  },
  "traceId": "202605211200000001",
  "timestamp": "2026-05-21T12:00:00+08:00"
}
```

**错误码：**


| 错误码        | 说明    |
| ---------- | ----- |
| BIZ_2001   | 数据不存在 |
| BIZ_2002   | 数据重复  |
| PARAM_1001 | 参数错误  |


---

## 四、数据库设计

### 4.1 表结构

#### 表名：xxx（中文说明）


| 字段名        | 类型           | 主键  | 非空  | 默认值  | 说明   |
| ---------- | ------------ | --- | --- | ---- | ---- |
| id         | bigint       | 是   | 是   | 自增   | 主键ID |
| name       | varchar(100) | 否   | 是   | -    | 名称   |
| status     | tinyint      | 否   | 否   | 1    | 状态   |
| created_at | datetime     | 否   | 否   | 当前时间 | 创建时间 |
| updated_at | datetime     | 否   | 否   | 当前时间 | 更新时间 |


**索引：**


| 索引名      | 字段   | 类型  | 说明     |
| -------- | ---- | --- | ------ |
| idx_name | name | 普通  | 名称索引   |
| uk_name  | name | 唯一  | 名称唯一索引 |


---

## 五、目录结构

```
project/
├── backend/
│   └── src/
│       └── app/
│           ├── api/v1/          # API 路由
│           ├── models/          # 数据模型
│           ├── schemas/         # Pydantic 模型
│           ├── services/        # 业务逻辑
│           └── common/         # 公共模块
├── frontend/
│   └── src/
│       ├── api/                # API 调用
│       ├── views/              # 页面组件
│       ├── components/         # 公共组件
│       └── stores/             # 状态管理
└── docs/                       # 文档目录
```

---

## 六、环境配置

### 6.1 后端配置

#### application-local.yml（本地环境）

```yaml
server:
  port: 8011
  host: 127.0.0.1

database:
  host: localhost
  port: 3308
  username: root
  password: root
  name: project_db

redis:
  host: localhost
  port: 6379
  password: ""
  db: 0

app:
  name: project-system
  version: 1.0.0
  debug: true
  env: local
```

#### application-prod.yml（生产环境）

```yaml
server:
  port: 8011
  host: 0.0.0.0

database:
  host: ${MYSQL_HOST}
  port: ${MYSQL_PORT:3306}
  username: ${MYSQL_USERNAME}
  password: ${MYSQL_PASSWORD}
  name: ${MYSQL_DATABASE}

redis:
  host: ${REDIS_HOST}
  port: ${REDIS_PORT:6379}
  password: ${REDIS_PASSWORD:}
  db: 0

app:
  name: project-system
  version: ${APP_VERSION:1.0.0}
  debug: false
  env: prod
```

### 6.2 前端配置

#### .env.local（本地环境）

```bash
VITE_API_BASE_URL=http://localhost:8011
VITE_APP_ENV=local
```

#### .env.production（生产环境）

```bash
VITE_API_BASE_URL=https://api.example.com
VITE_APP_ENV=production
```

---

## 七、启动脚本

### 7.1 后端启动

```bash
# 本地环境
cd backend/src
python -m uvicorn main:app --host 127.0.0.1 --port 8011 --reload --env local

# 生产环境
cd backend/src
nohup python -m uvicorn main:app --host 0.0.0.0 --port 8011 > logs/app.log 2>&1 &
```

### 7.2 前端启动

```bash
# 本地环境
cd frontend
npm run dev:local

# 生产构建
npm run build:prod
```

### 7.3 一键启动脚本

#### start-all-local.bat

```batch
@echo off
chcp 65001 > nul
echo ========================================
echo   项目名称 - 本地环境一键启动
echo ========================================

echo 启动后端服务...
start "Backend" cmd /k "cd /d %~dp0backend\src && python -m uvicorn main:app --host 127.0.0.1 --port 8011 --reload"

echo 启动前端服务...
start "Frontend" cmd /k "cd /d %~dp0frontend && npm run dev:local"

echo.
echo 启动完成！
pause
```

---

## 八、测试用例

### 8.1 单元测试

```python
# tests/test_xxx.py
import pytest
from httpx import AsyncClient
from app.main import app

class TestXxx:
    """模块测试"""

    @pytest.mark.asyncio
    async def test_create_success(self):
        """测试创建成功"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/xxx",
                json={"name": "测试"}
            )
            assert response.status_code == 200
            data = response.json()
            assert data["code"] == 0

    @pytest.mark.asyncio
    async def test_create_error(self):
        """测试参数错误"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/xxx",
                json={}
            )
            assert response.status_code == 200
            data = response.json()
            assert data["code"] != 0
```

### 8.2 测试命令

```bash
# 后端测试
cd backend
pytest tests/ -v

# 前端构建
cd frontend
npm run build
```

---

## 九、验收标准

### 9.1 功能验收


| 功能点 | 验收条件 | 状态  |
| --- | ---- | --- |
| 功能A | 条件说明 | ✅   |
| 功能B | 条件说明 | ⏳   |
| 功能C | 条件说明 | ❌   |


### 9.2 接口验收


| 接口  | 路径                      | 状态  |
| --- | ----------------------- | --- |
| 创建  | POST /api/v1/xxx        | ✅   |
| 查询  | GET /api/v1/xxx         | ✅   |
| 更新  | PUT /api/v1/xxx/{id}    | ✅   |
| 删除  | DELETE /api/v1/xxx/{id} | ✅   |


### 9.3 质量验收

- 代码注释完整
- 日志输出正常
- 错误处理完善
- 单元测试通过
- 接口文档同步更新

---

## 十、修改文件清单

### 10.1 新增文件


| 文件路径                             | 说明         |
| -------------------------------- | ---------- |
| backend/src/app/api/v1/xxx.py    | API路由      |
| backend/src/app/models/xxx.py    | 数据模型       |
| backend/src/app/schemas/xxx.py   | Pydantic模型 |
| backend/src/app/services/xxx.py  | 业务逻辑       |
| frontend/src/api/xxx.ts          | API调用      |
| frontend/src/views/xxx/index.vue | 页面组件       |
| tests/test_xxx.py                | 测试文件       |
| resources/xxx.sql                | 数据库脚本      |


### 10.2 修改文件


| 文件路径                         | 修改内容   |
| ---------------------------- | ------ |
| backend/src/main.py          | 注册路由   |
| frontend/src/router/index.ts | 添加路由   |
| docs/API接口文档.md              | 更新接口文档 |


### 10.3 删除文件


| 文件路径                          | 说明    |
| ----------------------------- | ----- |
| backend/src/app/api/v1/old.py | 已废弃接口 |


---

## 十一、常见问题

### Q1: 问题描述

**问题：** 描述

**原因：** 原因分析

**解决方案：** 解决步骤

### Q2: 问题描述

**问题：** 描述

**原因：** 原因分析

**解决方案：** 解决步骤

---

## 十二、后续批次依赖


| 批次   | 依赖内容        |
| ---- | ----------- |
| XX批次 | 使用本批次新增的API |
| XX批次 | 依赖本批次的数据模型  |


---

## 十三、版本记录


| 版本    | 日期         | 修改人 | 修改内容 |
| ----- | ---------- | --- | ---- |
| 1.0.0 | YYYY-MM-DD | 开发者 | 初始版本 |


