# RAG 问答系统 - Docker 部署指南

**版本：** V1.0
**日期：** 2026-05-13

---

## 1. 概述

本指南介绍如何使用 Docker 和 Docker Compose 部署 RAG 问答系统。

### 1.1 部署架构

```
┌─────────────────────────────────────────────────────────┐
│                    Docker Network                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │   FastAPI   │  │    MySQL    │  │    Redis    │    │
│  │   App       │  │   8.0       │  │   7         │    │
│  │  (Port 8000)│  │  (Port 3306)│  │  (Port 6379)│    │
│  └─────────────┘  └─────────────┘  └─────────────┘    │
└─────────────────────────────────────────────────────────┘
```

### 1.2 前提条件

| 软件 | 版本要求 | 说明 |
|------|----------|------|
| Docker | 20.10+ | 容器引擎 |
| Docker Compose | 2.0+ | 容器编排 |

---

## 2. 快速部署

### 2.1 克隆项目

```bash
cd d:/work/agent
```

### 2.2 配置环境变量

```bash
# 复制环境变量模板
copy .env.example .env

# 编辑 .env 文件，配置必要的参数
```

`.env` 文件配置：

```env
# DeepSeek API 密钥（必需）
DEEPSEEK_API_KEY=your_api_key_here

# MySQL 密码
MYSQL_PASSWORD=your_mysql_password

# 应用端口
APP_PORT=8000
```

### 2.3 启动服务

```bash
# 构建并启动所有服务
docker-compose up -d --build

# 查看服务状态
docker-compose ps
```

### 2.4 验证部署

```bash
# 检查应用健康状态
curl http://localhost:8000/api/v1/system/health
```

---

## 3. Docker 命令详解

### 3.1 启动服务

```bash
# 前台运行（查看日志）
docker-compose up

# 后台运行
docker-compose up -d

# 带构建运行
docker-compose up -d --build
```

### 3.2 停止服务

```bash
# 停止服务（保留数据）
docker-compose stop

# 停止并删除容器
docker-compose down

# 停止并删除容器和数据卷
docker-compose down -v
```

### 3.3 查看日志

```bash
# 查看所有服务日志
docker-compose logs

# 实时查看应用日志
docker-compose logs -f app

# 查看最近 100 行日志
docker-compose logs --tail 100 app
```

### 3.4 服务管理

```bash
# 重启服务
docker-compose restart app

# 进入容器
docker-compose exec app bash

# 进入 MySQL 容器
docker-compose exec mysql mysql -u root -p
```

### 3.5 重建服务

```bash
# 重建特定服务
docker-compose up -d --build app

# 重建所有服务
docker-compose down
docker-compose up -d --build
```

---

## 4. 数据管理

### 4.1 数据持久化

| 数据类型 | 存储位置 | 说明 |
|----------|----------|------|
| MySQL 数据 | `mysql_data` 卷 | 数据库文件 |
| Redis 数据 | `redis_data` 卷 | 缓存数据 |
| 上传文档 | `./data/documents` | 用户上传的文档 |
| ChromaDB 数据 | `./data/chroma` | 向量数据 |
| 应用日志 | `./logs` | 应用运行日志 |

### 4.2 备份数据

```bash
# 备份 MySQL 数据
docker-compose exec mysql mysqldump -u root -p rag_qa > backup.sql

# 备份 ChromaDB 数据
cp -r ./data/chroma ./data/chroma.backup

# 备份 Redis 数据
docker-compose exec redis redis-cli SAVE
docker cp rag-qa-redis:/data/dump.rdb ./redis_backup.rdb
```

### 4.3 恢复数据

```bash
# 恢复 MySQL 数据
docker-compose exec -T mysql mysql -u root -p rag_qa < backup.sql

# 恢复 ChromaDB 数据
cp -r ./data/chroma.backup/* ./data/chroma/
```

---

## 5. 生产环境配置

### 5.1 创建生产环境配置

```bash
# 创建生产环境 .env 文件
copy .env.production.example .env
```

`.env.production` 示例：

```env
# ==================== 应用配置 ====================
APP_ENV=production
DEBUG=false
LOG_LEVEL=WARNING

# ==================== MySQL 配置 ====================
MYSQL_PASSWORD=your_secure_password_here

# ==================== DeepSeek API ====================
DEEPSEEK_API_KEY=your_production_api_key

# ==================== 安全配置 ====================
SECRET_KEY=your-very-long-random-secret-key-change-this
```

### 5.2 使用生产配置启动

```bash
# 使用生产环境变量启动
docker-compose --env-file .env.production up -d
```

### 5.3 Nginx 反向代理配置（可选）

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # 超时配置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    location /docs {
        proxy_pass http://localhost:8000/docs;
    }
}
```

---

## 6. 常见问题

### 6.1 容器启动失败

**问题：** `app` 容器持续重启

**排查步骤：**

```bash
# 查看容器日志
docker-compose logs app

# 检查端口占用
netstat -an | grep 8000

# 检查 MySQL 健康状态
docker-compose ps mysql
```

**解决方案：**

```bash
# 清理并重新构建
docker-compose down -v
docker-compose up -d --build
```

### 6.2 MySQL 连接失败

**问题：** 应用无法连接 MySQL

**排查步骤：**

```bash
# 检查 MySQL 日志
docker-compose logs mysql

# 检查网络连通性
docker-compose exec app ping mysql
```

### 6.3 磁盘空间不足

**问题：** `no space left on device`

**解决方案：**

```bash
# 清理未使用的 Docker 资源
docker system prune -a

# 清理日志
truncate -s 0 ./logs/*.log
```

### 6.4 内存不足

**问题：** 容器 OOM

**解决方案：**

```yaml
# docker-compose.yml 中添加资源限制
services:
  app:
    deploy:
      resources:
        limits:
          memory: 2G
```

---

## 7. 更新部署

### 7.1 更新应用版本

```bash
# 拉取最新代码
git pull

# 重新构建并启动
docker-compose up -d --build
```

### 7.2 回滚版本

```bash
# 查看容器历史
docker ps --all --format "{{.Names}} {{.CreatedAt}}"

# 使用之前的镜像版本
docker-compose down
docker-compose run -d app:<previous-tag>
```

---

## 8. 监控和日志

### 8.1 日志管理

```bash
# 应用日志
docker-compose logs -f app

# MySQL 日志
docker-compose logs -f mysql

# Redis 日志
docker-compose logs -f redis

# 所有日志
docker-compose logs -f
```

### 8.2 健康检查

```bash
# 检查所有服务状态
docker-compose ps

# 检查服务健康状态
curl http://localhost:8000/api/v1/system/health
```

---

**文档版本历史**

| 版本 | 日期 | 修改内容 |
|------|------|----------|
| V1.0 | 2026-05-13 | 初始版本 |
