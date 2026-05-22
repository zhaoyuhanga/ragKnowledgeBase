\# 技术上下文与踩坑记录



\## 1. 项目技术栈

\- 前端：React 18 + Vite + Ant Design 5

\- 状态管理：Zustand（不引入Redux）

\- API请求：axios实例，已配置统一错误处理（见`src/utils/request.js`）

\- 样式方案：Tailwind CSS + CSS Modules



\## 2. 已解决的难题（附解决方案）

\- \*\*问题1\*\*：大文件上传（>100MB）导致浏览器卡顿  

&#x20; \*\*解决\*\*：采用`axios` + `onUploadProgress` + 分片上传（每片5MB），后台支持合并。

&#x20; \*\*关键代码\*\*：`src/components/Uploader/index.jsx` 第120-180行



\- \*\*问题2\*\*：WebSocket重连导致重复消息  

&#x20; \*\*解决\*\*：维护心跳定时器，断线后指数退避重连，并使用消息去重Map。  

&#x20; \*\*相关文件\*\*：`src/services/websocket.js`



\## 3. 未经验证的假设/待优化项

\- 假设：用户同时在线不超过500人（超出需换MQTT方案）

\- 待优化：首屏加载时间（当前2.5s，目标<1.5s），可考虑路由懒加载+图片预处理



\## 4. 外部依赖与版本锁定

\- 地图组件：Leaflet 1.9.2（不升级到2.0，因为API变更）

\- 后端API：swagger文档地址 `http://xxx/docs`，测试环境Token需附加`X-Test-Mode: true`

