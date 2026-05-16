# Codex ↔ Cursor 协作协议

## 角色分工

- **Codex（架构师/QA）**：需求分析、问题诊断、任务拆分、代码验收、回归检查
- **Cursor（主力开发）**：接收任务卡片、编码实现、标记完成

## 任务队列机制

所有任务通过 `tasks/` 目录进行文件级 handoff：

```
tasks/
  queue/       ← Cursor 待处理任务
  feedback/    ← Codex 验收不通过，待返工
  done/        ← 验收通过，归档
  task-template.md
```

## 工作流

### Phase 1：Codex 分析 & 派发任务
1. Codex 扫描项目，诊断问题/需求
2. 为每个独立问题创建 `tasks/queue/TASK-XXX.md`（基于 `task-template.md`）
3. 任务卡片必须包含：问题描述、涉及文件、预期修改方向、验收标准
4. 用 `cursor tasks/queue/TASK-XXX.md` 打开任务让开发者审阅

### Phase 2：Cursor 开发
1. 开发者打开 `tasks/queue/` 中的任务卡片
2. 根据任务描述实现代码修改
3. 修改完成后更新任务卡片状态为 `done`，填写完成情况

### Phase 3：Codex 验收
1. Codex 检出已完成任务（状态为 `done` 的卡片）
2. 逐条对照验收标准，检查代码变更（`git diff`）
3. Codex 运行相关测试验证
4. 对每个任务给出判定：
   - ✅ 通过 → 移动卡片到 `tasks/done/`，标记验收结论
   - ❌ 不通过 → 移动卡片到 `tasks/feedback/`，附具体返工意见

### Phase 4：返工循环（如需要）
1. 开发者检查 `tasks/feedback/` 中的卡片
2. 根据 Codex 反馈修改代码
3. Codex 再次验收（最多 3 轮，超时启动人工介入）

### Phase 5：清理检查
1. Codex 检查是否有临时代码、调试日志、多余 import
2. 发现问题 → 新建清理任务卡片
3. Cursor 执行清理

## 任务卡片约定
- 文件名格式：`TASK-{序号}-{简短描述}.md`，如 `TASK-001-fix-login-timeout.md`
- 状态字段用 emoji 标记，便于视觉扫描
- 验收标准用 checkbox，验收时逐条勾选
