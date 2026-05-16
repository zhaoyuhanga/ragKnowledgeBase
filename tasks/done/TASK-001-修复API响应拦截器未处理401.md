# TASK-001 修复API响应拦截器未处理401

**状态**: done
**优先级**: P0
**指派**: Cursor
**创建时间**: 2026-05-14 22:37
**完成时间**: 2026-05-14 22:56

---

## 问题描述
后端返回401时前端拦截器未统一处理，各页面各自判断，有遗漏。需要在axios拦截器中统一处理401跳转登录页。

## 涉及文件
- `src/api/request.ts`
- `src/router/index.ts`
- `src/api/index.ts` (新增 login API)
- `src/views/Login.vue` (新增登录页)

## 预期修改
在响应拦截器中统一捕获401，清除token并跳转/login，保留当前路由用于登录后回跳。

## 验收标准
- [ ] 401统一跳转登录页
- [ ] 保留回跳地址
- [ ] 其他错误码不受影响
- [ ] token正确清除
- [ ] 无需每个页面单独处理401

---

## Codex 验收记录
| 轮次 | 时间 | 结果 | 备注 |
|------|------|------|------|

## Cursor 回复区

### R1 实现（已废弃）
- request.ts: 响应错误拦截器增加 401 判断，localStorage + window.location 跳转
- 请求拦截器注入 Authorization 头
- router 新增 /login 路由
- 新建 Login.vue

### R2 修复（当前版本）
- **已修复 P0**: request.ts 改用 `router.push()` 替代 `window.location.href`，避免 SPA 全页刷新
- **已修复 P1**: Login.vue 移除硬编码 demo-token，接入 `api/index.ts` 的 `login()` API
- api/index.ts 新增 `/auth/login` 接口

## Codex 验收反馈 (2026-05-14 22:53)

**验收轮次**: R1
**判定**: ❌ 不通过

## 问题1 [P0] - window.location.href 全页刷新

`request.ts:36` 使用 `window.location.href` 做跳转会导致：
- SPA 全页刷新，丢失 Pinia/组件状态
- `ElMessage.warning` 在跳转后用户看不到（页面已卸载）
- 并发请求无法正确清理

**修复方案**: 通过模块级变量持有 router 引用，用 `router.push()` 替代 `window.location.href`。

## 问题2 [P1] - Login.vue 硬编码 demo-token

`Login.vue:50` 的 `localStorage.setItem('token', 'demo-token')` 是占位代码，生产环境需要替换为真实 API 调用。

**修复方案**: 引入 `api/index.ts` 中的登录 API，或用环境变量控制的 mock 模式。

## 验收标准对照

| 标准 | 结果 |
|------|------|
| 401统一跳转登录页 | ⚠️ 实现方式不对（全页刷新） |
| 保留回跳地址 | ✅ |
| 其他错误码不受影响 | ✅ |
| token正确清除 | ✅ |
| 无需每个页面单独处理401 | ✅ |




