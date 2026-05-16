# Phase 2：企业功能

**版本：** V1.0  
**日期：** 2026-05-17  
**预计周期：** 3-4 周  
**优先级：** P1

---

## 一、阶段概述

### 1.1 阶段目标

满足企业级客户的安全合规需求和集成能力，包括单点登录、审计日志、数据导入导出和 webhook 通知。

### 1.2 核心功能

| 模块 | 功能点 | 优先级 | 工作量 |
|------|--------|--------|--------|
| SSO 单点登录 | LDAP/SAML/OIDC 集成 | P1 | 5 天 |
| 审计日志 | 完整操作审计追踪 | P1 | 3 天 |
| 数据导入导出 | 多种格式支持 | P1 | 3 天 |
| Webhook 通知 | 事件驱动通知 | P2 | 2 天 |

### 1.3 技术架构

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          Phase 2 架构                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────┐    │
│   │                      企业身份提供者                                  │    │
│   │   ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐   │    │
│   │   │  LDAP  │  │  AD    │  │ Okta  │  │ Azure │  │飞书/钉钉│   │    │
│   │   └────────┘  └────────┘  └────────┘  └────────┘  └────────┘   │    │
│   └─────────────────────────────────────────────────────────────────┘    │
│                                    │                                       │
│                                    ▼                                       │
│   ┌─────────────────────────────────────────────────────────────────┐    │
│   │                      Auth Service (SSO Module)                   │    │
│   │   SAML Handler │ OIDC Handler │ LDAP Sync │ OAuth2 Handler      │    │
│   └─────────────────────────────────────────────────────────────────┘    │
│                                    │                                       │
│   ┌─────────────────────────────────────────────────────────────────┐    │
│   │                       Audit Service                              │    │
│   │   ┌──────────────┐ ┌──────────────┐ ┌──────────────┐            │    │
│   │   │  Event Hub  │ │  Log Store  │ │  Query API  │            │    │
│   │   └──────────────┘ └──────────────┘ └──────────────┘            │    │
│   └─────────────────────────────────────────────────────────────────┘    │
│                                    │                                       │
│   ┌─────────────────────────────────────────────────────────────────┐    │
│   │                    Notification Service                           │    │
│   │   ┌──────────────┐ ┌──────────────┐ ┌──────────────┐            │    │
│   │   │  Webhook    │ │    Email    │ │ In-App Notif│            │    │
│   │   └──────────────┘ └──────────────┘ └──────────────┘            │    │
│   └─────────────────────────────────────────────────────────────────┘    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 二、功能需求详述

### 2.1 SSO 单点登录

#### 2.1.1 支持的 SSO 协议

| 协议 | 支持程度 | 描述 |
|------|----------|------|
| **SAML 2.0** | 完整支持 | 支持 IdP 和 SP 两种模式 |
| **OIDC** | 完整支持 | 现代认证协议，OAuth 2.0 的上层封装 |
| **LDAP** | 完整支持 | 企业目录服务集成 |
| **OAuth 2.0** | 基础支持 | 第三方应用授权 |

#### 2.1.2 功能需求

| 需求ID | 需求描述 | 验收条件 | 验证方法 |
|--------|----------|----------|----------|
| SSO-001 | SAML 配置 | 可配置 SAML IdP 信息 | 配置后可发起 SSO |
| SSO-002 | SAML SSO 登录 | 点击后跳转 IdP 登录 | 登录成功跳转回系统 |
| SSO-003 | SAML 属性映射 | 用户属性映射到本地用户 | 字段正确同步 |
| SSO-004 | OIDC 配置 | 可配置 OIDC Provider | 配置后可发起 SSO |
| SSO-005 | OIDC SSO 登录 | 支持 OIDC 协议登录 | 登录成功 |
| SSO-006 | LDAP 集成 | 连接企业 LDAP 服务器 | 用户列表同步 |
| SSO-007 | LDAP 用户同步 | 自动同步 LDAP 用户 | 用户自动创建 |
| SSO-008 | SSO 会话管理 | SSO 用户会话管理 | 会话正常维持 |
| SSO-009 | 本地账号绑定 | SSO 用户绑定本地账号 | 可使用本地账号登录 |
| SSO-010 | 自动注册 | 新用户自动创建 | 首次登录自动注册 |

#### 2.1.3 SAML 配置项

```yaml
saml:
  enabled: true
  idp:
    entity_id: "https://idp.example.com/saml"
    sso_url: "https://idp.example.com/saml/sso"
    slo_url: "https://idp.example.com/saml/slo"
    x509_cert: |
      -----BEGIN CERTIFICATE-----
      MIIDpDCCA...
      -----END CERTIFICATE-----
  sp:
    entity_id: "https://app.example.com/saml/metadata"
    acs_url: "https://app.example.com/saml/acs"
    sls_url: "https://app.example.com/saml/sls"
  attribute_mapping:
    email: "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress"
    username: "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/name"
    first_name: "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/givenname"
    last_name: "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/surname"
    groups: "http://schemas.xmlsoap.org/claims/Group"
```

#### 2.1.4 OIDC 配置项

```yaml
oidc:
  enabled: true
  providers:
    okta:
      client_id: "your-client-id"
      client_secret: "your-client-secret"
      issuer: "https://your-org.okta.com"
      scopes: ["openid", "profile", "email"]
      userinfo_endpoint: "https://your-org.okta.com/oauth2/v1/userinfo"
    azure:
      client_id: "your-client-id"
      client_secret: "your-client-secret"
      tenant_id: "your-tenant-id"
```

#### 2.1.5 LDAP 配置项

```yaml
ldap:
  enabled: true
  server:
    host: "ldap.example.com"
    port: 636
    use_ssl: true
    bind_dn: "cn=admin,dc=example,dc=com"
    bind_password: "admin-password"
  search:
    base_dn: "ou=users,dc=example,dc=com"
    filter: "(objectClass=person)"
    attributes:
      - uid
      - mail
      - cn
      - memberOf
  sync:
    schedule: "0 2 * * *"  # 每天凌晨2点
    auto_create_users: true
    group_mapping:
      "cn=admins,ou=groups,dc=example,dc=com": "admin"
      "cn=users,ou=groups,dc=example,dc=com": "user"
```

#### 2.1.6 接口设计

```
# SSO 配置管理
GET    /api/v1/sso/config                      # 获取 SSO 配置
PUT    /api/v1/sso/config                      # 更新 SSO 配置
POST   /api/v1/sso/test-connection            # 测试连接

# SAML
GET    /api/v1/sso/saml/metadata              # SP 元数据
GET    /api/v1/sso/saml/login                 # 发起 SAML 登录
POST   /api/v1/sso/saml/acs                  # SAML ACS 回调
GET    /api/v1/sso/saml/logout                # SAML 登出
POST   /api/v1/sso/saml/sls                  # SAML SLS 回调

# OIDC
GET    /api/v1/sso/oidc/{provider}/login     # 发起 OIDC 登录
GET    /api/v1/sso/oidc/{provider}/callback  # OIDC 回调

# LDAP
POST   /api/v1/sso/ldap/sync                  # 手动同步用户
GET    /api/v1/sso/ldap/users                # 获取 LDAP 用户列表
```

### 2.2 审计日志系统

#### 2.2.1 审计事件类型

| 事件分类 | 事件类型 | 说明 |
|----------|----------|------|
| **认证事件** | login_success | 登录成功 |
| | login_failed | 登录失败 |
| | logout | 登出 |
| | mfa_enabled | 启用 MFA |
| | password_changed | 密码修改 |
| **用户事件** | user_created | 用户创建 |
| | user_updated | 用户更新 |
| | user_deleted | 用户删除 |
| | user_disabled | 用户禁用 |
| **权限事件** | role_created | 角色创建 |
| | role_updated | 角色更新 |
| | permission_granted | 权限授予 |
| | permission_revoked | 权限撤销 |
| **知识库事件** | kb_created | 知识库创建 |
| | kb_updated | 知识库更新 |
| | kb_deleted | 知识库删除 |
| | member_added | 成员添加 |
| | member_removed | 成员移除 |
| **文档事件** | document_uploaded | 文档上传 |
| | document_downloaded | 文档下载 |
| | document_deleted | 文档删除 |
| | document_accessed | 文档访问 |
| **问答事件** | question_asked | 提问 |
| | feedback_submitted | 反馈提交 |
| **系统事件** | config_changed | 配置变更 |
| | api_key_created | API Key 创建 |
| | api_key_deleted | API Key 删除 |
| | sso_config_changed | SSO 配置变更 |

#### 2.2.2 审计日志需求

| 需求ID | 需求描述 | 验收条件 | 验证方法 |
|--------|----------|----------|----------|
| AL-001 | 登录审计 | 记录所有登录事件 | 查看审计日志 |
| AL-002 | 操作审计 | 记录关键操作 | 查看审计日志 |
| AL-003 | 敏感操作 | 记录高风险操作 | 查看审计日志 |
| AL-004 | 日志查询 | 支持多条件查询 | 查询验证 |
| AL-005 | 日志导出 | 导出审计日志 | 导出文件正确 |
| AL-006 | 日志保留 | 满足合规保留期 | 配置验证 |
| AL-007 | 实时监控 | 关键事件实时告警 | 告警触发测试 |
| AL-008 | 不可篡改 | 日志防篡改 | 安全测试 |

#### 2.2.3 审计日志字段

```sql
CREATE TABLE audit_log (
    id                  BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    
    -- 事件标识
    event_id            CHAR(36) NOT NULL UNIQUE COMMENT '事件唯一ID',
    event_type          VARCHAR(50) NOT NULL COMMENT '事件类型',
    event_category      VARCHAR(30) NOT NULL COMMENT '事件分类',
    
    -- 时间
    occurred_at         DATETIME(3) NOT NULL COMMENT '事件发生时间',
    
    -- 用户信息
    user_id             BIGINT UNSIGNED DEFAULT NULL COMMENT '用户ID',
    user_email          VARCHAR(255) DEFAULT NULL COMMENT '用户邮箱(冗余)',
    user_ip             VARCHAR(45) DEFAULT NULL COMMENT '用户IP',
    user_agent          VARCHAR(500) DEFAULT NULL COMMENT 'User-Agent',
    
    -- 资源信息
    resource_type       VARCHAR(50) DEFAULT NULL COMMENT '资源类型',
    resource_id         VARCHAR(100) DEFAULT NULL COMMENT '资源ID',
    resource_name       VARCHAR(200) DEFAULT NULL COMMENT '资源名称',
    
    -- 操作信息
    action              VARCHAR(50) NOT NULL COMMENT '操作类型',
    action_description  TEXT DEFAULT NULL COMMENT '操作描述',
    
    -- 请求信息
    request_method      VARCHAR(10) DEFAULT NULL COMMENT 'HTTP方法',
    request_path        VARCHAR(500) DEFAULT NULL COMMENT '请求路径',
    request_params      JSON DEFAULT NULL COMMENT '请求参数(脱敏)',
    request_body        JSON DEFAULT NULL COMMENT '请求体(脱敏)',
    response_status     INT DEFAULT NULL COMMENT '响应状态码',
    
    -- 变更详情
    old_value           JSON DEFAULT NULL COMMENT '变更前值',
    new_value           JSON DEFAULT NULL COMMENT '变更后值',
    
    -- 上下文
    session_id          VARCHAR(100) DEFAULT NULL COMMENT '会话ID',
    correlation_id      VARCHAR(100) DEFAULT NULL COMMENT '追踪ID',
    
    -- 元数据
    metadata            JSON DEFAULT NULL COMMENT '额外信息',
    
    -- 完整性
    checksum            VARCHAR(64) DEFAULT NULL COMMENT '校验和',
    
    created_at          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_event_type (event_type),
    INDEX idx_user_id (user_id),
    INDEX idx_resource (resource_type, resource_id),
    INDEX idx_occurred_at (occurred_at),
    INDEX idx_request_path (request_path(255))
);
```

#### 2.2.4 接口设计

```
# 审计日志查询
GET    /api/v1/audit-logs                     # 日志列表
GET    /api/v1/audit-logs/{event_id}         # 日志详情

# 审计日志导出
POST   /api/v1/audit-logs/export             # 导出日志

# 审计统计
GET    /api/v1/audit-logs/stats/overview     # 概览统计
GET    /api/v1/audit-logs/stats/by-type      # 按类型统计
GET    /api/v1/audit-logs/stats/by-user      # 按用户统计
GET    /api/v1/audit-logs/stats/trend        # 趋势统计

# 审计配置
GET    /api/v1/audit-logs/config             # 获取配置
PUT    /api/v1/audit-logs/config             # 更新配置
```

### 2.3 数据导入导出

#### 2.3.1 导入功能

| 格式 | 支持 | 说明 |
|------|------|------|
| CSV | ✅ | FAQ 批量导入 |
| Excel | ✅ | FAQ 批量导入 |
| JSON | ✅ | 结构化数据导入 |
| Markdown | ✅ | 文档批量导入 |
| PDF | ✅ | 文档导入 |
| DOCX | ✅ | 文档导入 |

#### 2.3.2 导入需求

| 需求ID | 需求描述 | 验收条件 | 验证方法 |
|--------|----------|----------|----------|
| IM-001 | CSV 导入 FAQ | 批量导入问答对 | 导入成功 |
| IM-002 | Excel 导入 FAQ | 导入问答对 | 导入成功 |
| IM-003 | JSON 导入 | 结构化数据导入 | 导入成功 |
| IM-004 | 文档批量导入 | 批量上传文档 | 导入成功 |
| IM-005 | 模板下载 | 下载导入模板 | 模板正确 |
| IM-006 | 导入预览 | 预览导入数据 | 预览正确 |
| IM-007 | 导入校验 | 数据格式校验 | 错误提示明确 |
| IM-008 | 导入进度 | 显示导入进度 | 进度正确 |
| IM-009 | 导入回滚 | 失败时回滚 | 数据回滚 |

#### 2.3.3 导出功能

| 格式 | 支持 | 说明 |
|------|------|------|
| CSV | ✅ | 问答历史导出 |
| Excel | ✅ | 数据报表导出 |
| JSON | ✅ | 结构化数据导出 |
| PDF | ✅ | 报告导出 |
| Markdown | ✅ | 文档导出 |

#### 2.3.4 导出需求

| 需求ID | 需求描述 | 验收条件 | 验证方法 |
|--------|----------|----------|----------|
| EX-001 | 问答历史导出 | 导出问答记录 | 文件正确 |
| EX-002 | 知识库备份 | 导出知识库完整数据 | 备份完整 |
| EX-003 | 用户数据导出 | 导出用户数据 | 符合 GDPR |
| EX-004 | 审计日志导出 | 导出审计日志 | 符合合规要求 |
| EX-005 | 统计报表导出 | 导出运营报表 | 格式正确 |
| EX-006 | 批量导出 | 批量导出多个知识库 | 导出成功 |
| EX-007 | 定时导出 | 定时导出数据 | 自动执行 |
| EX-008 | 导出进度 | 显示导出进度 | 进度正确 |

#### 2.3.5 FAQ 导入模板

```csv
# faq_import_template.csv
question,answer,category,tags,status
"问题1","回答1","分类1","标签1,标签2","active"
"问题2","回答2","分类2","标签3","active"
```

#### 2.3.6 接口设计

```
# 导入
GET    /api/v1/imports/templates             # 获取导入模板
POST   /api/v1/imports/upload                # 上传导入文件
GET    /api/v1/imports/{job_id}             # 导入进度
GET    /api/v1/imports/{job_id}/preview     # 导入预览
POST   /api/v1/imports/{job_id}/execute     # 执行导入
DELETE /api/v1/imports/{job_id}             # 取消导入

# 导出
POST   /api/v1/exports                      # 创建导出任务
GET    /api/v1/exports/{job_id}             # 导出进度
GET    /api/v1/exports/{job_id}/download    # 下载导出文件
DELETE /api/v1/exports/{job_id}             # 删除导出任务

# 备份
POST   /api/v1/backups                       # 创建备份
GET    /api/v1/backups                       # 备份列表
GET    /api/v1/backups/{id}                 # 备份详情
POST   /api/v1/backups/{id}/restore         # 恢复备份
DELETE /api/v1/backups/{id}                 # 删除备份
```

### 2.4 Webhook 通知

#### 2.4.1 支持的事件类型

| 事件分类 | 事件类型 | 说明 |
|----------|----------|------|
| **文档事件** | document.uploaded | 文档上传完成 |
| | document.processed | 文档处理完成 |
| | document.failed | 文档处理失败 |
| | document.deleted | 文档删除 |
| **问答事件** | question.asked | 用户提问 |
| | answer.generated | 回答生成完成 |
| | feedback.submitted | 用户反馈 |
| **知识库事件** | kb.updated | 知识库更新 |
| | kb.member_added | 成员添加 |
| | kb.member_removed | 成员移除 |
| **用户事件** | user.created | 用户创建 |
| | quota.exceeded | 配额超限 |
| **系统事件** | alert.triggered | 告警触发 |
| | maintenance.scheduled | 维护计划 |

#### 2.4.2 Webhook 需求

| 需求ID | 需求描述 | 验收条件 | 验证方法 |
|--------|----------|----------|----------|
| WH-001 | 创建 Webhook | 配置 URL 和事件 | 创建成功 |
| WH-002 | Webhook 列表 | 查看所有 Webhook | 列表正确 |
| WH-003 | 编辑 Webhook | 修改 Webhook 配置 | 修改成功 |
| WH-004 | 删除 Webhook | 删除 Webhook | 删除成功 |
| WH-005 | 事件订阅 | 订阅感兴趣的事件 | 事件触发发送 |
| WH-006 | 重试机制 | 发送失败自动重试 | 重试成功 |
| WH-007 | 签名验证 | 支持 HMAC 签名 | 签名验证正确 |
| WH-008 | Webhook 日志 | 查看发送历史 | 日志完整 |
| WH-009 | 测试 Webhook | 发送测试事件 | 测试成功 |
| WH-010 | 批量配置 | 批量管理 Webhook | 配置成功 |

#### 2.4.3 Webhook 配置

```json
{
  "id": "wh_123456",
  "name": "My Webhook",
  "url": "https://example.com/webhook",
  "secret": "whsec_xxxxx",
  "events": [
    "document.processed",
    "answer.generated"
  ],
  "headers": {
    "X-Custom-Header": "custom-value"
  },
  "is_active": true,
  "retry_policy": {
    "max_retries": 3,
    "retry_delay_seconds": [60, 300, 900]
  },
  "timeout_seconds": 30
}
```

#### 2.4.4 Webhook 消息格式

```json
{
  "id": "evt_123456",
  "type": "document.processed",
  "api_version": "2.0",
  "created_at": "2026-05-17T10:30:00Z",
  "data": {
    "object": "document",
    "id": "doc_789",
    "filename": "report.pdf",
    "status": "processed",
    "chunk_count": 15
  }
}
```

#### 2.4.5 接口设计

```
# Webhook 管理
GET    /api/v1/webhooks                     # Webhook 列表
POST   /api/v1/webhooks                    # 创建 Webhook
GET    /api/v1/webhooks/{id}               # Webhook 详情
PUT    /api/v1/webhooks/{id}               # 更新 Webhook
DELETE /api/v1/webhooks/{id}              # 删除 Webhook

# Webhook 测试
POST   /api/v1/webhooks/{id}/test          # 发送测试事件

# Webhook 日志
GET    /api/v1/webhooks/{id}/logs          # 发送日志
GET    /api/v1/webhooks/{id}/logs/{log_id} # 日志详情
POST   /api/v1/webhooks/{id}/logs/{log_id}/retry # 重试发送

# 事件列表
GET    /api/v1/webhooks/events              # 支持的事件类型
```

---

## 三、非功能需求

### 3.1 性能需求

| 指标 | 目标值 | 说明 |
|------|--------|------|
| SSO 登录响应 | ≤ 2s | 完整的 SSO 流程 |
| 审计日志写入 | ≤ 50ms | 异步写入 |
| 审计日志查询 | ≤ 500ms | 分页查询 |
| 导入处理速度 | ≥ 1000 条/分钟 | 大批量导入 |
| Webhook 发送 | ≤ 100ms | 异步发送 |

### 3.2 安全需求

| 需求 | 说明 |
|------|------|
| SSO 加密 | SAML/OIDC 响应加密验证 |
| 审计日志防篡改 | 数字签名/哈希链 |
| Webhook 签名 | HMAC-SHA256 签名 |
| 敏感数据脱敏 | 审计日志中脱敏 |
| 数据传输加密 | TLS 1.2+ |

### 3.3 合规需求

| 需求 | 说明 |
|------|------|
| GDPR 合规 | 用户数据导出、删除权 |
| 审计日志保留 | 至少 1 年 |
| SOC2 支持 | 审计追踪完整性 |
| 数据加密存储 | 敏感字段加密 |

---

## 四、测试计划

### 4.1 SSO 测试用例

| 用例ID | 用例名称 | 预期结果 |
|--------|----------|----------|
| SSO-UT-001 | SAML 登录完整流程 | 登录成功并跳转 |
| SSO-UT-002 | OIDC 登录完整流程 | 登录成功并跳转 |
| SSO-UT-003 | LDAP 用户同步 | 用户自动同步 |
| SSO-UT-004 | SSO 会话过期 | 重新认证 |
| SSO-UT-005 | 本地账号绑定 | 绑定后可用本地登录 |

### 4.2 审计日志测试用例

| 用例ID | 用例名称 | 预期结果 |
|--------|----------|----------|
| AL-UT-001 | 登录事件记录 | 登录事件完整记录 |
| AL-UT-002 | 操作事件记录 | 操作事件完整记录 |
| AL-UT-003 | 日志多条件查询 | 查询结果正确 |
| AL-UT-004 | 日志导出 | 导出文件完整 |
| AL-UT-005 | 日志防篡改 | 篡改检测有效 |

### 4.3 导入导出测试用例

| 用例ID | 用例名称 | 预期结果 |
|--------|----------|----------|
| IM-UT-001 | CSV FAQ 导入 | 1000 条导入成功 |
| IM-UT-002 | 大文件导入 | 10MB 文件导入成功 |
| IM-UT-003 | 导入校验失败 | 错误提示明确 |
| EX-UT-001 | 问答历史导出 | 导出文件正确 |
| EX-UT-002 | 知识库备份导出 | 备份完整可恢复 |

### 4.4 Webhook 测试用例

| 用例ID | 用例名称 | 预期结果 |
|--------|----------|----------|
| WH-UT-001 | Webhook 创建 | 创建成功 |
| WH-UT-002 | 事件触发发送 | 事件发送成功 |
| WH-UT-003 | 发送失败重试 | 重试机制生效 |
| WH-UT-004 | 签名验证 | HMAC 验证通过 |
| WH-UT-005 | Webhook 日志查询 | 日志记录完整 |

---

## 五、交付物清单

### 5.1 代码交付

| 交付物 | 说明 | 验收标准 |
|--------|------|----------|
| SSO 模块代码 | SAML/OIDC/LDAP 集成 | 功能测试通过 |
| 审计服务代码 | 审计日志系统 | 功能测试通过 |
| 导入导出模块 | 数据导入导出 | 功能测试通过 |
| Webhook 模块 | 事件通知系统 | 功能测试通过 |

### 5.2 文档交付

| 文档 | 说明 |
|------|------|
| SSO 配置指南 | 各协议配置说明 |
| Webhook 开发指南 | 集成文档 |
| 审计日志 API | 接口文档 |
| 数据导入导出指南 | 使用手册 |

---

## 六、验收清单

### 6.1 SSO 单点登录验收

| 序号 | 验收项 | 验收条件 | 验证方法 | 状态 |
|------|--------|----------|----------|------|
| 1 | SAML 配置 | 可配置 IdP 信息 | 配置测试 | ⬜ |
| 2 | SAML 登录 | 完整登录流程 | 功能测试 | ⬜ |
| 3 | SAML 属性映射 | 属性正确同步 | 数据验证 | ⬜ |
| 4 | OIDC 配置 | 可配置 Provider | 配置测试 | ⬜ |
| 5 | OIDC 登录 | 完整登录流程 | 功能测试 | ⬜ |
| 6 | LDAP 连接 | 连接企业 LDAP | 连接测试 | ⬜ |
| 7 | LDAP 用户同步 | 用户自动同步 | 同步测试 | ⬜ |
| 8 | 会话管理 | SSO 会话正常 | 功能测试 | ⬜ |

### 6.2 审计日志验收

| 序号 | 验收项 | 验收条件 | 验证方法 | 状态 |
|------|--------|----------|----------|------|
| 1 | 登录审计 | 记录登录事件 | 日志查询 | ⬜ |
| 2 | 操作审计 | 记录操作事件 | 日志查询 | ⬜ |
| 3 | 日志查询 | 多条件查询正常 | 功能测试 | ⬜ |
| 4 | 日志导出 | 导出文件正确 | 功能测试 | ⬜ |
| 5 | 日志统计 | 统计数据正确 | 数据验证 | ⬜ |
| 6 | 防篡改 | 篡改检测有效 | 安全测试 | ⬜ |

### 6.3 数据导入导出验收

| 序号 | 验收项 | 验收条件 | 验证方法 | 状态 |
|------|--------|----------|----------|------|
| 1 | CSV 导入 | FAQ 导入成功 | 功能测试 | ⬜ |
| 2 | Excel 导入 | FAQ 导入成功 | 功能测试 | ⬜ |
| 3 | JSON 导入 | 结构化导入成功 | 功能测试 | ⬜ |
| 4 | 导入预览 | 预览数据正确 | 功能测试 | ⬜ |
| 5 | 导入校验 | 错误提示明确 | 功能测试 | ⬜ |
| 6 | 问答导出 | 导出文件正确 | 功能测试 | ⬜ |
| 7 | 知识库备份 | 备份完整 | 恢复测试 | ⬜ |

### 6.4 Webhook 验收

| 序号 | 验收项 | 验收条件 | 验证方法 | 状态 |
|------|--------|----------|----------|------|
| 1 | 创建 Webhook | 创建成功 | 功能测试 | ⬜ |
| 2 | 事件订阅 | 事件触发发送 | 功能测试 | ⬜ |
| 3 | 重试机制 | 失败自动重试 | 功能测试 | ⬜ |
| 4 | 签名验证 | HMAC 验证正确 | 安全测试 | ⬜ |
| 5 | 日志记录 | 发送历史完整 | 日志查询 | ⬜ |
| 6 | 测试事件 | 测试发送成功 | 功能测试 | ⬜ |

---

## 七、风险与应对

| 风险 | 影响 | 可能性 | 应对措施 |
|------|------|--------|----------|
| SSO 协议兼容性 | 高 | 中 | 多协议支持，降低耦合 |
| 大批量导入性能 | 中 | 中 | 异步队列 + 分批处理 |
| Webhook 发送延迟 | 低 | 中 | 独立消息队列 |
| 审计日志数据量 | 中 | 中 | 分表 + 定期归档 |

---

## 八、版本历史

| 版本 | 日期 | 修改内容 | 作者 |
|------|------|----------|------|
| V1.0 | 2026-05-17 | 初始版本 | - |
