# RAG知识库管理系统 - 前端

基于 React + TypeScript + Ant Design 的 RAG 知识库管理系统前端。

## 功能特性

- **仪表盘**: 系统概览、统计数据、最近文档和问答
- **文档管理**: 文档上传、解析、删除、版本管理
- **清洗规则**: 清洗规则CRUD、正则表达式配置
- **问答管理**: 智能问答、会话历史、反馈统计
- **检索测试**: 混合检索、查询改写、融合方法测试
- **队列管理**: RabbitMQ队列监控、死信队列处理
- **系统设置**: 健康检查、数据库配置、检索/问答参数配置

## 技术栈

- React 18
- TypeScript
- Vite
- Ant Design 5
- React Router 6
- Axios
- Day.js

## API对接

本项目严格按照 `docs/API接口文档.md` 文档进行开发:

- **Base URL**: `http://localhost:8011/api/v1`
- **统一响应格式**: `{ code, message, data, traceId, timestamp }`
- **分页格式**: `{ items, total, page_no, page_size, pages }`

### 接口列表

| 模块 | 接口数 | 说明 |
|------|--------|------|
| 健康检查 | 5 | 系统、MySQL、Redis、Milvus、RabbitMQ |
| 文档管理 | 7 | 上传、列表、详情、删除、版本 |
| 导入任务 | 2 | 任务详情、任务列表 |
| 文档解析 | 5 | 解析、状态、元素、重新解析 |
| 清洗服务 | 7 | 规则CRUD、文档清洗、日志 |
| 切分服务 | 5 | 切分、批量、列表、详情、统计 |
| 向量化服务 | 7 | 编码、检索、统计、初始化 |
| 关键词索引 | 4 | 索引、检索、统计 |
| 检索服务 | 7 | 混合检索、向量化、关键词、改写 |
| 问答服务 | 12 | 问答、反馈、历史、规则 |
| 队列管理 | 11 | 发布、队列、统计、死信处理 |

## 开发

```bash
# 安装依赖
npm install

# 开发模式
npm run dev

# 构建
npm run build
```

## 目录结构

```
rag-qa-frontend/
├── public/
├── src/
│   ├── components/     # 公共组件
│   │   ├── Header.tsx
│   │   ├── Sidebar.tsx
│   │   ├── Layout.tsx
│   │   └── Stats.tsx
│   ├── pages/          # 页面组件
│   │   ├── Dashboard.tsx
│   │   ├── Documents.tsx
│   │   ├── CleaningRules.tsx
│   │   ├── QA.tsx
│   │   ├── RetrievalTest.tsx
│   │   ├── QueueManagement.tsx
│   │   └── Settings.tsx
│   ├── services/      # API服务层
│   │   ├── api.ts
│   │   ├── health.ts
│   │   ├── documents.ts
│   │   ├── parse.ts
│   │   ├── cleaning.ts
│   │   ├── chunks.ts
│   │   ├── embedding.ts
│   │   ├── keyword.ts
│   │   ├── retrieval.ts
│   │   ├── qa.ts
│   │   └── queue.ts
│   ├── types/         # TypeScript类型定义
│   │   └── api.ts
│   ├── styles/         # 全局样式
│   │   └── global.css
│   ├── App.tsx
│   └── main.tsx
├── index.html
├── package.json
├── tsconfig.json
└── vite.config.ts
```

## 配置

### 代理配置

开发环境下，Vite 配置了代理将 `/api` 请求转发到后端:

```typescript
// vite.config.ts
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:8011',
      changeOrigin: true
    }
  }
}
```

### 环境变量

如果需要自定义后端地址，可以在 `vite.config.ts` 中修改代理配置，或创建 `.env` 文件:

```
VITE_API_BASE_URL=http://localhost:8011/api/v1
```
