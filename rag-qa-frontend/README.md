# RAG 知识库问答系统 - 前端

基于 Vue 3 + Element Plus 构建的 RAG 知识库问答系统可视化界面。

## 功能特性

- **仪表盘**: 系统运行状态概览、快速操作入口
- **知识问答**: 智能问答、Markdown 回答渲染、历史记录查看
- **文档管理**: 文档上传、预览、删除、状态筛选
- **知识库管理**: 统计信息、索引重建、缓存清理、检索测试
- **系统设置**: 配置查看、健康检查、环境变量说明

## 技术栈

- Vue 3 (Composition API)
- TypeScript
- Vue Router 4
- Pinia
- Element Plus
- Axios
- Vite

## 快速开始

### 安装依赖

```bash
npm install
```

### 开发模式

```bash
npm run dev
```

访问 http://localhost:3000

### 构建生产版本

```bash
npm run build
```

## 项目结构

```
src/
├── api/          # API 接口封装
├── assets/       # 静态资源
├── components/   # 公共组件
├── router/      # 路由配置
├── stores/      # Pinia 状态管理
├── types/       # TypeScript 类型定义
└── views/       # 页面组件
    ├── Dashboard.vue   # 仪表盘
    ├── QA.vue         # 知识问答
    ├── Documents.vue  # 文档管理
    ├── Knowledge.vue   # 知识库管理
    └── System.vue     # 系统设置
```

## 配置说明

前端默认代理到 `http://localhost:8000`（后端地址）。

如需修改，编辑 `vite.config.ts`:

```typescript
server: {
  proxy: {
    '/api': {
      target: 'http://your-backend:8000',
      changeOrigin: true
    }
  }
}
```

## 页面说明

### 仪表盘 (/dashboard)

展示系统统计信息，包括：
- 总查询数、文档数量、文档块数、今日查询
- 缓存命中率、平均响应时间
- 快捷操作入口

### 知识问答 (/qa)

主要功能：
- 输入问题并获取 AI 回答
- 调整 Top K 参数
- 查看回答置信度和响应时间
- 浏览历史问答记录

### 文档管理 (/documents)

主要功能：
- 支持 PDF、DOCX、DOC、TXT、MD 格式上传
- 文档列表、搜索、状态筛选
- 文档预览、删除

### 知识库管理 (/knowledge)

主要功能：
- 查看知识库统计信息
- 重建向量索引
- 清除 Redis 缓存
- 知识库检索测试

### 系统设置 (/system)

主要功能：
- 系统健康检查
- 查看当前配置
- 环境变量说明
- 技术栈信息
