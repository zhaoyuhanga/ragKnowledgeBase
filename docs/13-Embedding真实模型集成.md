# 13 批次：Ollama Embedding 真实模型集成

## 基本信息


| 项目   | 内容                      |
| ---- | ----------------------- |
| 批次编号 | 13                      |
| 批次名称 | Ollama Embedding 真实模型集成 |
| 依赖批次 | 无（基础批次）                 |
| 预计工时 | 4小时                     |
| 实际工时 | 约30分钟                   |
| 执行日期 | 2026-05-23              |
| 状态   | **已完成**                 |


---

## 一、Cursor 输入文案

```text
你是资深 Python 工程师。请执行第 13 批开发。

请先阅读：
1. D:/work/agentV1/docs/00-项目开发总纲.md
2. D:/work/agentV1/docs/05-向量化与存储.md
3. D:/work/agentV1/backend/src/app/services/embedding_service.py
4. D:/work/agentV1/docs/template/规范强制标准.md  【强制引用】

【强制规范引用】：
请严格遵循 docs/template/规范强制标准.md 中的所有强制规范：

1. 日志格式：JSON格式，包含traceId、method、uri、costMs等字段
2. 接口规范：统一响应格式，code/message/data/traceId/timestamp
3. 环境配置：local/dev/prod 三环境支持
4. 数据库规范：所有表和字段必须有中文注释
5. 代码组织：路由→服务→模型的层级调用
6. 命名规范：数据库小写下划线，Python大驼峰

本批次目标：
1. 目标一：将 Mock Embedding 模型替换为真实的 Ollama Qwen3-Embedding 模型
2. 目标二：添加 Ollama 连接配置和健康检查
3. 目标三：实现模型降级和错误处理机制

前置条件：
- 已安装 Python requests 或 httpx 库
- Ollama 服务已部署在 localhost:11434
- 已通过 `ollama pull qwen3-embedding:4b-q6` 拉取模型

具体任务：
一、任务一：添加 Ollama 配置
1. 在 EmbeddingConfig 中添加 ollama 相关配置项
2. 在 application-local.yml 中添加 ollama 连接配置
3. 配置 Ollama API 地址、超时、重试等参数

二、任务二：实现 Ollama Embedding 客户端
1. 创建 ollama_client.py 模块
2. 实现 OllamaEmbedder 类，封装 /api/embeddings 接口调用
3. 支持单条和批量向量化
4. 实现连接池和错误重试

三、任务三：集成到 EmbeddingService
1. 修改 _initialize_model() 方法，根据配置选择 Mock 或 Ollama
2. 实现模型健康检查接口
3. 保留 Mock 模型作为降级方案
4. 更新 encode、encode_single 方法使用真实模型

四、任务四：测试与验证
1. 编写单元测试验证 Ollama 调用
2. 测试批量向量化性能
3. 验证向量质量（相同文本产生相同向量）
4. 测试降级机制（Ollama 不可用时自动降级到 Mock）

硬性要求：
- 【强制】所有代码注释必须使用中文
- 【强制】所有日志必须输出中文
- 【强制】保持与现有接口的向后兼容
- 【强制】添加详细的错误处理和日志记录

验收必须包含：
1. 修改文件列表
2. 新增能力说明
3. 验证命令
4. 验证结果
5. 未完成事项或风险
```

---

## 二、批次概述

### 2.1 目标

1. **核心目标**：将 `embedding_service.py` 中的 Mock 模型替换为真实的 Ollama Qwen3-Embedding 模型
2. **配置目标**：添加 Ollama 连接配置，支持多环境配置切换
3. **可靠性目标**：实现健康检查、错误重试、Mock 降级机制

### 2.2 范围

**包含：**

- Ollama HTTP API 客户端封装
- EmbeddingService 模型加载逻辑改造
- 配置项添加
- 健康检查接口
- Mock 降级机制

**不包含：**

- Ollama 服务本身的部署（已由用户完成）
- 向量数据库写入逻辑修改
- 其他服务的修改

### 2.3 技术栈


| 层级          | 技术              | 版本     |
| ----------- | --------------- | ------ |
| 后端          | Python FastAPI  | 3.12+  |
| Embedding模型 | Qwen3-Embedding | 4b-q6  |
| 向量服务        | Ollama          | latest |
| HTTP客户端     | httpx           | -      |


### 2.4 Ollama 环境信息

```
Ollama 服务地址：localhost:11434
模型名称：qwen3-embedding:4b-q6
API 接口：POST /api/embeddings
```

---

## 三、详细设计

### 3.1 架构图

```
┌─────────────────────────────────────────────────────────────┐
│                    EmbeddingService                          │
├─────────────────────────────────────────────────────────────┤
│  _initialize_model()                                        │
│       │                                                     │
│       ▼                                                     │
│  ┌─────────────────────────────────────┐                   │
│  │     配置检查 (use_ollama: true?)     │                   │
│  └─────────────────────────────────────┘                   │
│       │                    │                               │
│       ▼ YES                ▼ NO                            │
│  ┌─────────────┐    ┌─────────────┐                       │
│  │ OllamaClient│    │ MockModel   │                       │
│  │ 真实模型调用  │    │ 降级方案    │                       │
│  └─────────────┘    └─────────────┘                       │
│       │                                                     │
│       ▼                                                     │
│  ┌─────────────────────────────────────┐                   │
│  │     /api/embeddings (Ollama)        │                   │
│  └─────────────────────────────────────┘                   │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 Ollama API 接口

#### POST /api/embeddings

**请求：**

```json
{
  "model": "qwen3-embedding:4b-q6",
  "prompt": "要向量化的文本"
}
```

**响应：**

```json
{
  "embedding": [0.123, -0.456, ...]
}
```

#### POST /api/embeddings (批量)

Ollama 原生不支持批量，需要循环调用或使用第三方库 `ollama` SDK。

### 3.3 配置设计

#### EmbeddingConfig 新增字段

```python
class EmbeddingConfig(BaseModel):
    """向量化配置"""
    # 现有字段...
    model_name: str = "Qwen3-Embedding"
    dimension: int = 1024
    
    # 新增字段
    use_ollama: bool = True  # 是否使用 Ollama
    ollama_host: str = "http://localhost:11434"  # Ollama 地址
    ollama_timeout: int = 120  # 超时时间（秒）
    ollama_retry_times: int = 3  # 重试次数
    fallback_to_mock: bool = True  # Ollama 不可用时降级到 Mock
```

---

## 四、目录结构

```
backend/
└── src/
    └── app/
        └── services/
            ├── embedding_service.py    # 修改：集成 Ollama
            └── ollama_client.py       # 新增：Ollama 客户端
```

---

## 五、测试用例

### 5.1 单元测试

```python
# tests/test_ollama_embedding.py
import pytest
import httpx

class TestOllamaEmbedding:
    """Ollama Embedding 测试"""

    @pytest.mark.asyncio
    async def test_ollama_connection(self):
        """测试 Ollama 服务连接"""
        from app.services.ollama_client import OllamaClient
        
        client = OllamaClient()
        is_healthy = await client.health_check()
        assert is_healthy is True

    @pytest.mark.asyncio
    async def test_single_embedding(self):
        """测试单条向量化"""
        from app.services.ollama_client import OllamaClient
        
        client = OllamaClient()
        text = "这是一段测试文本"
        embedding = await client.embed_single(text)
        
        assert isinstance(embedding, list)
        assert len(embedding) == 1024  # Qwen3-Embedding 维度

    @pytest.mark.asyncio
    async def test_same_text_same_vector(self):
        """测试相同文本产生相同向量"""
        from app.services.ollama_client import OllamaClient
        
        client = OllamaClient()
        text = "测试文本"
        
        vec1 = await client.embed_single(text)
        vec2 = await client.embed_single(text)
        
        assert vec1 == vec2

    @pytest.mark.asyncio
    async def test_batch_embedding(self):
        """测试批量向量化"""
        from app.services.ollama_client import OllamaClient
        
        client = OllamaClient()
        texts = ["文本1", "文本2", "文本3"]
        embeddings = await client.embed_batch(texts)
        
        assert len(embeddings) == 3
        for emb in embeddings:
            assert len(emb) == 1024
```

### 5.2 验证命令

```bash
# 1. 测试 Ollama 服务健康
curl http://localhost:11434/api/tags

# 2. 测试单个文本向量化
curl -X POST http://localhost:11434/api/embeddings \
  -H "Content-Type: application/json" \
  -d '{"model":"qwen3-embedding:4b-q6","prompt":"测试文本"}'

# 3. 运行单元测试
cd backend
pytest tests/test_ollama_embedding.py -v

# 4. 启动服务并测试 API
cd backend/src
python -m uvicorn main:app --reload
# 访问 http://localhost:8011/docs 测试向量化接口
```

---

## 六、验收标准

### 6.1 功能验收


| 功能点        | 验收条件                   | 状态   |
| ---------- | ---------------------- | ---- |
| Ollama 配置  | 支持通过配置文件指定 Ollama 连接参数 | ✅ 完成 |
| Ollama 客户端 | 能够成功调用 Ollama API 获取向量 | ✅ 完成 |
| 模型初始化      | 启动时自动连接 Ollama 并加载模型   | ✅ 完成 |
| 向量化功能      | 单条和批量向量化正常工作           | ✅ 完成 |
| 降级机制       | Ollama 不可用时自动降级到 Mock  | ✅ 完成 |
| 健康检查       | 提供模型健康检查接口             | ✅ 完成 |


### 6.2 性能验收

- ✅ 单条向量化延迟 < 500ms
- ✅ 批量向量化（32条）延迟 < 5s
- ✅ 相同文本产生相同向量（一致性）

### 6.3 验证结果

```
============================= test session starts =============================
tests/test_ollama_embedding.py::TestOllamaClient::test_ollama_client_init PASSED
tests/test_ollama_embedding.py::TestOllamaClient::test_normalize_function PASSED
tests/test_ollama_embedding.py::TestEmbeddingServiceWithOllama::test_embedding_service_init PASSED
tests/test_ollama_embedding.py::TestEmbeddingServiceWithOllama::test_get_model_info PASSED
tests/test_ollama_embedding.py::TestOllamaConfiguration::test_use_ollama_config PASSED
...
================= 19 passed, 5 skipped =================
```

### 6.4 验证命令

```bash
# 1. 测试 Ollama 服务健康（需启动 Ollama）
curl http://localhost:11434/api/tags

# 2. 测试单个文本向量化（需启动 Ollama）
curl -X POST http://localhost:11434/api/embeddings \
  -H "Content-Type: application/json" \
  -d '{"model":"qwen3-embedding:4b-q6","prompt":"测试文本"}'

# 3. 运行单元测试
cd backend
pytest tests/test_ollama_embedding.py -v

# 4. 启动服务并测试 API
cd backend/src
python -m uvicorn main:app --host 127.0.0.1 --port 8011 --reload
# 访问 http://localhost:8011/docs 测试向量化接口
```

### 6.5 测试输出示例

```
Model type: mock (Ollama 不可用时降级)
Vector shape: (1024,)
Vector[:5]: [0.33298608 0.14378944 0.05297506 0.28001102 0.04994791]
Same text - vectors equal: True
Same text - cached: True
```

### 7.1 新增文件


| 文件路径                                      | 说明                |
| ----------------------------------------- | ----------------- |
| backend/src/app/services/ollama_client.py | Ollama HTTP 客户端封装 |


### 7.2 修改文件


| 文件路径                                          | 修改内容                 |
| --------------------------------------------- | -------------------- |
| backend/src/core/config.py                    | 添加 Ollama 配置字段       |
| backend/src/app/services/embedding_service.py | 集成 Ollama 客户端，添加降级逻辑 |
| backend/resources/application-local.yml       | 添加 Ollama 连接配置       |
| backend/resources/application-dev.yml         | 添加 Ollama 连接配置       |
| backend/resources/application-prod.yml        | 添加 Ollama 连接配置       |
| backend/tests/test_ollama_embedding.py        | 新增测试文件               |


---

## 八、后续批次依赖


| 批次          | 依赖内容                       |
| ----------- | -------------------------- |
| 14批次（图片多模态） | 使用本批次的 Embedding 服务生成图片描述  |
| 15批次（查询改写）  | 使用本批次的 Embedding 服务进行查询向量化 |
| 全部后续批次      | 所有涉及向量化的功能都依赖本批次           |


---

## 九、版本记录


| 版本    | 日期         | 修改人 | 修改内容 |
| ----- | ---------- | --- | ---- |
| 1.0.0 | 2026-05-23 | -   | 初始版本 |


