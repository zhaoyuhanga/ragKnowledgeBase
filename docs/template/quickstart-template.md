# 项目名称 - 快速启动与交付文档

## 一、项目概述

### 1.1 项目简介

[简要描述项目功能]

### 1.2 技术栈


| 层级  | 技术                   | 版本    | 说明         |
| --- | -------------------- | ----- | ---------- |
| 后端  | Python FastAPI       | 3.12+ | REST API服务 |
| 前端  | Vue 3 + Element Plus | 最新    | SPA管理后台    |
| 数据库 | MySQL                | 8.0   | 主数据存储      |
| 缓存  | Redis                | 7.x   | 会话缓存       |


### 1.3 服务端口


| 服务    | 端口   | 说明        |
| ----- | ---- | --------- |
| 后端API | 8011 | FastAPI服务 |
| 前端    | 3011 | Vue开发服务器  |
| MySQL | 3308 | 数据库服务     |
| Redis | 6379 | 缓存服务      |


---

## 二、环境配置

### 2.1 环境类型说明


| 环境    | 用途   | 数据库             | Redis           | API地址                                                    |
| ----- | ---- | --------------- | --------------- | -------------------------------------------------------- |
| local | 开发调试 | localhost:3308  | localhost:6379  | [http://localhost:8011](http://localhost:8011)           |
| dev   | 团队联调 | dev-mysql:3308  | dev-redis:6379  | [http://dev-api.example.com](http://dev-api.example.com) |
| prod  | 正式上线 | prod-mysql:3306 | prod-redis:6379 | [https://api.example.com](https://api.example.com)       |


### 2.2 后端环境配置

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
  pool_size: 5
  max_overflow: 10

redis:
  host: localhost
  port: 6379
  password: ""
  db: 0

jwt:
  secret_key: local-dev-secret-key-change-in-production
  algorithm: HS256
  access_token_expire_minutes: 120

app:
  name: project-system
  version: 1.0.0
  debug: true
  env: local
  logging:
    level: DEBUG
    audit_enabled: true
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
  pool_size: 20
  max_overflow: 40

redis:
  host: ${REDIS_HOST}
  port: ${REDIS_PORT:6379}
  password: ${REDIS_PASSWORD:}
  db: 0

jwt:
  secret_key: ${JWT_SECRET_KEY}
  algorithm: HS256
  access_token_expire_minutes: 60

app:
  name: project-system
  version: ${APP_VERSION:1.0.0}
  debug: false
  env: prod
  logging:
    level: INFO
    audit_enabled: true
```

### 2.3 前端环境配置

#### .env.local（本地环境）

```bash
# API配置
VITE_API_BASE_URL=http://localhost:8011
VITE_API_PREFIX=/api/v1

# 环境标识
VITE_APP_ENV=local
VITE_APP_DEBUG=true
```

#### .env.dev（开发环境）

```bash
# API配置
VITE_API_BASE_URL=https://dev-api.example.com
VITE_API_PREFIX=/api/v1

# 环境标识
VITE_APP_ENV=dev
VITE_APP_DEBUG=false
```

#### .env.production（生产环境）

```bash
# API配置
VITE_API_BASE_URL=https://api.example.com
VITE_API_PREFIX=/api/v1

# 环境标识
VITE_APP_ENV=production
VITE_APP_DEBUG=false
```

---

## 三、快速启动脚本

### 3.1 项目根目录启动脚本

#### start-all-local.bat（Windows 本地启动）

```batch
@echo off
chcp 65001 > nul
echo ========================================
echo   项目名称 - 本地环境一键启动
echo ========================================
echo.

:: 检查并启动 MySQL
echo [1/4] 检查 MySQL 服务...
sc query MySQL | findstr "RUNNING" > nul
if errorlevel 1 (
    echo   MySQL 未运行，正在启动...
    net start MySQL
) else (
    echo   MySQL 已运行
)

:: 检查并启动 Redis
echo [2/4] 检查 Redis 服务...
sc query Redis | findstr "RUNNING" > nul
if errorlevel 1 (
    echo   Redis 未运行，正在启动...
    net start Redis
) else (
    echo   Redis 已运行
)

:: 启动后端
echo [3/4] 启动后端服务...
start "Backend" cmd /k "cd /d %~dp0backend\src && python -m uvicorn main:app --host 127.0.0.1 --port 8011 --reload"

:: 启动前端
echo [4/4] 启动前端服务...
start "Frontend" cmd /k "cd /d %~dp0frontend && npm run dev:local"

echo.
echo ========================================
echo   启动完成！
echo   前端地址: http://localhost:3011
echo   后端地址: http://localhost:8011
echo   API文档:  http://localhost:8011/doc.html
echo ========================================
echo.
pause
```

#### start-all-local.sh（Linux/Mac 本地启动）

```bash
#!/bin/bash

echo "========================================"
echo "  项目名称 - 本地环境一键启动"
echo "========================================"
echo ""

# 启动后端
echo "[1/3] 启动后端服务..."
cd backend/src
nohup python -m uvicorn main:app --host 127.0.0.1 --port 8011 --reload > ../logs/backend.log 2>&1 &
BACKEND_PID=$!
echo "  后端已启动 (PID: $BACKEND_PID)"

# 等待后端启动
sleep 3

# 启动前端
echo "[2/3] 启动前端服务..."
cd ../frontend
npm run dev:local > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
echo "  前端已启动 (PID: $FRONTEND_PID)"

echo ""
echo "========================================"
echo "  启动完成！"
echo "  前端地址: http://localhost:3011"
echo "  后端地址: http://localhost:8011"
echo "  API文档:  http://localhost:8011/doc.html"
echo "========================================"
echo ""
```

### 3.2 后端启动脚本

#### backend-start.bat（Windows 后端启动）

```batch
@echo off
chcp 65001 > nul
echo ========================================
echo   后端服务启动中...
echo ========================================

cd /d %~dp0src

echo 选择环境:
echo   1. 本地环境 (local)
echo   2. 开发环境 (dev)
echo   3. 生产环境 (prod)
set /p choice=请选择 (1-3):

if "%choice%"=="1" set ENV=local
if "%choice%"=="2" set ENV=dev
if "%choice%"=="3" set ENV=prod

echo.
echo 启动 %ENV% 环境后端服务...
python -m uvicorn main:app --host 127.0.0.1 --port 8011 --reload --env %ENV%

pause
```

### 3.3 前端启动脚本

#### frontend-start.bat（Windows 前端启动）

```batch
@echo off
chcp 65001 > nul
echo ========================================
echo   前端服务启动中...
echo ========================================

cd /d %~dp0

echo 选择环境:
echo   1. 本地环境 (local)
echo   2. 开发环境 (dev)
echo   3. 生产环境 (prod)
set /p choice=请选择 (1-3):

if "%choice%"=="1" set NPM_CMD=npm run dev:local
if "%choice%"=="2" set NPM_CMD=npm run dev:dev
if "%choice%"=="3" set NPM_CMD=npm run build:prod

echo.
echo 启动前端服务...
%NPM_CMD%

pause
```

### 3.4 数据库初始化脚本

#### db-init.bat（Windows 数据库初始化）

```batch
@echo off
chcp 65001 > nul
echo ========================================
echo   数据库初始化
echo ========================================

set MYSQL_HOST=localhost
set MYSQL_PORT=3308
set MYSQL_USER=root
set MYSQL_PASS=root
set DB_NAME=project_db

echo.
echo [1/3] 创建数据库...
mysql -h%MYSQL_HOST% -P%MYSQL_PORT% -u%MYSQL_USER% -p%MYSQL_PASS% -e "CREATE DATABASE IF NOT EXISTS %DB_NAME% DEFAULT CHARACTER SET utf8mb4;"

echo [2/3] 执行初始化脚本...
mysql -h%MYSQL_HOST% -P%MYSQL_PORT% -u%MYSQL_USER% -p%MYSQL_PASS% %DB_NAME% < resources/init.sql

echo [3/3] 导入测试数据...
mysql -h%MYSQL_HOST% -P%MYSQL_PORT% -u%MYSQL_USER% -p%MYSQL_PASS% %DB_NAME% < resources/seed.sql

echo.
echo ========================================
echo   数据库初始化完成！
echo ========================================
pause
```

### 3.5 停止服务脚本

#### stop-all.bat（Windows 停止所有服务）

```batch
@echo off
chcp 65001 > nul
echo ========================================
echo   停止所有服务
echo ========================================

echo 停止后端服务...
taskkill /FI "WINDOWTITLE eq Backend*" /F > nul 2>&1
taskkill /IM python.exe /FI "WINDOWTITLE eq Backend*" /F > nul 2>&1

echo 停止前端服务...
taskkill /FI "WINDOWTITLE eq Frontend*" /F > nul 2>&1
taskkill /IM node.exe /FI "WINDOWTITLE eq Frontend*" /F > nul 2>&1

echo.
echo 所有服务已停止
pause
```

---

## 四、各环境启动命令

### 4.1 本地环境（local）

```bash
# 后端
cd backend/src
uvicorn main:app --host 127.0.0.1 --port 8011 --reload

# 前端
cd frontend
npm run dev:local
```

### 4.2 开发环境（dev）

```bash
# 后端
cd backend/src
uvicorn main:app --host 0.0.0.0 --port 8011

# 前端
cd frontend
npm run dev:dev
```

### 4.3 生产环境（prod）

```bash
# 后端
cd backend/src
nohup python -m uvicorn main:app --host 0.0.0.0 --port 8011 > logs/app.log 2>&1 &

# 前端构建
cd frontend
npm run build:prod
```

---

## 五、快速启动流程

### 5.1 前置条件

- Python 3.12+
- Node.js 18+
- MySQL 8.0
- Redis 7.x

### 5.2 快速启动流程

```bash
# 1. 克隆项目
git clone <项目地址>
cd project-name

# 2. 初始化数据库
.\scripts\db-init.bat    # Windows
./scripts/db-init.sh      # Linux/Mac

# 3. 启动所有服务
.\start-all-local.bat     # Windows
./start-all-local.sh      # Linux/Mac
```

### 5.3 访问系统


| 地址                                                                   | 说明            |
| -------------------------------------------------------------------- | ------------- |
| [http://localhost:3011](http://localhost:3011)                       | 前端管理后台        |
| [http://localhost:8011/doc.html](http://localhost:8011/doc.html)     | Swagger API文档 |
| [http://localhost:8011/redoc.html](http://localhost:8011/redoc.html) | ReDoc API文档   |


---

## 六、测试账号


| 用户名    | 密码     | 角色  | 权限   |
| ------ | ------ | --- | ---- |
| admin  | 123456 | 管理员 | 全部权限 |
| user01 | 123456 | 用户  | 部分权限 |


---

## 七、项目结构

```
project-name/
├── scripts/                   # 启动脚本
│   ├── start-all-local.bat
│   ├── start-all-local.sh
│   ├── backend-start.bat
│   ├── frontend-start.bat
│   ├── db-init.bat
│   └── stop-all.bat
│
├── backend/                    # 后端项目
│   ├── src/
│   │   ├── main.py
│   │   └── app/
│   ├── resources/
│   │   ├── application-local.yml
│   │   ├── application-prod.yml
│   │   ├── init.sql
│   │   └── seed.sql
│   └── logs/
│
├── frontend/                   # 前端项目
│   ├── src/
│   ├── .env.local
│   ├── .env.dev
│   └── .env.production
│
└── docs/                      # 文档目录
```

---

## 八、验收标准

### 功能验收

- 后端 8011 可启动
- 前端 3011 可启动
- MySQL 连接正常
- Redis 连接正常
- Swagger/OpenAPI 可查看接口文档

### 测试结果

- 单元测试通过
- 接口测试通过
- 前端构建成功

---

## 九、版本信息

- 版本号：1.0.0
- 更新日期：YYYY-MM-DD

