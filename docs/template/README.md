# 模板使用说明

## 概述

本文档说明如何使用 `template` 文件夹下的模板来创建新的开发批次文档。

**重要提示：** 所有强制规范标准请参考 `规范强制标准.md`，各批次文档应引用该文档。

---

## 核心文档


| 文档                         | 说明                                          |
| -------------------------- | ------------------------------------------- |
| `规范强制标准.md`                | **强制规范标准**，包含日志格式、接口规范、多环境配置等，是所有开发文档的强制引用源 |
| `README.md`                | 本文档，模板使用说明                                  |
| `outline-template.md`      | 项目总纲模板                                      |
| `batch-template.md`        | 批次开发模板                                      |
| `quickstart-template.md`   | 快速启动模板                                      |
| `prompt-template.md`       | Cursor提示词模板                                 |
| `acceptance-template.md`   | 验收报告模板                                      |
| `requirements-template.md` | 需求文档模板                                      |


---

## 规范引用方式

在批次文档的 Cursor 输入文案中，应包含以下引用：

```text
【强制规范引用】：
请严格遵循 docs/template/规范强制标准.md 中的所有强制规范：

1. 日志格式：JSON格式，包含traceId、method、uri、costMs等字段
2. 接口规范：统一响应格式，code/message/data/traceId/timestamp
3. 环境配置：local/dev/prod 三环境支持
4. 命名规范：数据库小写下划线，Python大驼峰
5. 代码组织：路由→服务→模型的层级调用
```

---

## 一、创建新项目总纲

### 步骤

1. 复制 `outline-template.md` 到 `docs` 目录
2. 重命名为项目名称，如 `00-项目开发总纲.md`
3. 填写项目基本信息
4. 更新技术栈和服务端口
5. 根据实际情况调整规范内容

### 必填项

- 项目名称
- 项目描述
- 技术栈版本
- 服务端口
- 环境配置说明

---

## 二、创建新批次文档

### 步骤

1. 复制 `batch-template.md` 到 `docs` 目录
2. 重命名为批次编号，如 `13-新功能模块.md`
3. 填写批次基本信息
4. 编写 Cursor 输入文案
5. 设计 API 和数据库结构
6. 编写测试用例
7. 定义验收标准

### 批次编号规则

```
01, 02, 03 ...      # 基础批次
09.5                 # 中间批次（API联调）
10, 11, 12 ...      # 后端批次
```

### 必填章节

1. **Cursor 输入文案** - 必须包含技术要求、中文显示要求、环境配置要求
2. **API 设计** - 必须包含接口列表和详细说明
3. **数据库设计** - 必须包含表结构和索引
4. **测试用例** - 必须包含成功和失败场景
5. **验收标准** - 必须包含功能、接口、质量三方面

---

## 三、模板章节说明

### 3.1 批次模板章节


| 章节          | 说明                | 必填  |
| ----------- | ----------------- | --- |
| 基本信息        | 批次编号、名称、依赖、耗时     | 是   |
| Cursor 输入文案 | AI执行指令            | 是   |
| 批次概述        | 目标和范围             | 是   |
| 详细设计        | API、数据库设计         | 是   |
| 目录结构        | 项目文件组织            | 否   |
| 环境配置        | local/dev/prod 配置 | 是   |
| 启动脚本        | 启动命令              | 是   |
| 测试用例        | 单元测试、集成测试         | 是   |
| 验收标准        | 功能、接口、质量验收        | 是   |
| 修改文件清单      | 新增、修改、删除文件        | 是   |
| 常见问题        | FAQ               | 否   |
| 后续批次依赖      | 依赖关系              | 否   |
| 版本记录        | 修改历史              | 是   |


### 3.2 环境配置必填内容

#### 后端

```yaml
# application-local.yml - 本地环境
server:
  port: 8011
  host: 127.0.0.1
database:
  host: localhost
  port: 3308
app:
  env: local
  debug: true

# application-prod.yml - 生产环境
server:
  port: 8011
  host: 0.0.0.0
database:
  host: ${MYSQL_HOST}
  port: ${MYSQL_PORT:3306}
app:
  env: prod
  debug: false
```

#### 前端

```bash
# .env.local - 本地环境
VITE_API_BASE_URL=http://localhost:8011
VITE_APP_ENV=local

# .env.production - 生产环境
VITE_API_BASE_URL=https://api.example.com
VITE_APP_ENV=production
```

### 3.3 启动脚本必填内容

```batch
# Windows 一键启动脚本
start-all-local.bat

# Linux/Mac 一键启动脚本
start-all-local.sh
```

---

## 四、功能修改流程

### 场景1：修改现有功能

1. 创建新的批次文档，如 `XX-功能修改.md`
2. 在 Cursor 输入文案中引用原批次
3. 说明修改点和影响范围
4. 更新相关文档
5. 更新 `docs/00-项目开发总纲.md` 中的验收标准

### 场景2：新增功能

1. 创建新的批次文档，如 `XX-新功能.md`
2. 编写完整的 API 设计
3. 编写数据库设计
4. 编写测试用例
5. 更新 `docs/00-项目开发总纲.md` 中的批次列表

### 场景3：删除功能

1. 创建批次文档记录删除操作
2. 说明影响范围和依赖
3. 删除相关代码文件
4. 更新文档

---

## 五、文档更新规则

### 5.1 主动更新的文档


| 文档             | 更新时机        |
| -------------- | ----------- |
| `00-项目开发总纲.md` | 新增批次、修改验收标准 |
| `API接口文档.md`   | 新增/修改接口     |
| `快速启动文档.md`    | 环境配置变化      |
| 批次文档           | 功能修改        |


### 5.2 被动更新的文档


| 文档   | 被谁更新 |
| ---- | ---- |
| 测试文档 | 测试批次 |
| 部署文档 | 部署批次 |


---

## 六、模板使用检查清单

创建新批次时，确保以下内容都已填写：

- 批次编号和名称
- 依赖批次说明
- Cursor 输入文案（包含中文要求）
- API 接口列表
- API 接口详情（请求/响应示例）
- 数据库表结构
- 环境配置文件（local/prod）
- 启动脚本
- 测试用例（成功+失败场景）
- 验收标准
- 修改文件清单

---

## 七、示例

### 示例：创建第13批次

```bash
# 1. 复制模板
copy docs\template\batch-template.md docs\13-报表导出模块.md

# 2. 修改内容
# - 批次编号: 13
# - 批次名称: 报表导出模块
# - 依赖批次: 09-报表统计模块

# 3. 填写具体内容
# - API: 导出学生、导出成绩、导出考勤
# - 数据库: 导出任务表
# - 测试: 导出成功、导出失败、权限验证

# 4. 更新总纲
# - 在批次列表添加 13-报表导出模块.md
```

---

## 八、模板文件清单

```
docs/template/
├── README.md                    # 本文档
├── outline-template.md          # 项目总纲模板
├── batch-template.md            # 批次开发模板
├── quickstart-template.md       # 快速启动模板
├── prompt-template.md           # Cursor提示词模板
├── acceptance-template.md       # 验收报告模板
└── requirements-template.md     # 需求文档模板
```

## 九、快速创建流程

### 9.1 新项目快速启动

1. 复制 `requirements-template.md` → `需求文档.md`
2. 复制 `outline-template.md` → `00-项目开发总纲.md`
3. 复制 `batch-template.md` → 各批次文档
4. 复制 `quickstart-template.md` → `快速启动文档.md`

### 9.2 新批次快速创建

1. 复制 `batch-template.md` → `XX-批次名称.md`
2. 复制 `prompt-template.md` 中的对应章节到新文档
3. 复制 `acceptance-template.md` → 临时验收使用
4. 执行完成后输出验收报告

