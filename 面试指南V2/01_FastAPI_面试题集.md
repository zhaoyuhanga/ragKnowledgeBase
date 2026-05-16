# FastAPI + Uvicorn 面试题集

> 本文档包含 30 道 FastAPI 框架相关的高频面试题，涵盖异步编程、依赖注入、中间件、路由系统等核心概念。所有答案均为中文，代码附有详细中文解释。

---

## 目录

1. [基础概念](#1-基础概念)
2. [异步编程](#2-异步编程)
3. [路由与参数](#3-路由与参数)
4. [依赖注入](#4-依赖注入)
5. [请求体与响应](#5-请求体与响应)
6. [中间件](#6-中间件)
7. [异常处理](#7-异常处理)
8. [性能与部署](#8-性能与部署)

---

## 1. 基础概念

### Q1: FastAPI 是什么？它有什么核心特点？

**参考答案：**

FastAPI 是一个现代、快速（高性能）的 Python Web 框架，专门用于构建 API 接口。它基于 Starlette（异步框架）和 Pydantic（数据验证）构建。

**核心特点：**

| 特点 | 说明 |
|------|------|
| **高性能** | 基于 Starlette 和 Uvicorn，性能接近 Node.js 和 Go |
| **异步支持** | 原生支持 async/await 异步编程 |
| **类型提示** | 利用 Python 类型提示自动生成数据验证 |
| **自动文档** | 自动生成 OpenAPI/Swagger 文档 |
| **数据验证** | 基于 Pydantic 的自动数据验证和序列化 |
| **API 文档** | 提供交互式 API 测试界面 |

**项目中的应用：**

```python
# FastAPI 核心应用创建
from fastapi import FastAPI

app = FastAPI(
    title="RAG 问答系统 API",  # API 标题
    description="基于检索增强生成技术的问答系统",  # API 描述
    version="1.0.0",  # 版本号
    docs_url="/docs",  # Swagger 文档路径
    redoc_url="/redoc",  # ReDoc 文档路径
)

# 定义路由
@app.get("/")
async def root():
    return {"message": "RAG 问答系统"}
```

---

### Q2: FastAPI 与 Flask、Django 有什么区别？

**参考答案：**

| 特性 | FastAPI | Flask | Django |
|------|---------|-------|--------|
| **框架定位** | API 微框架 | 微框架 | 全栈框架 |
| **异步支持** | 原生异步 | 需扩展 | 同步为主 |
| **性能** | 极高 | 中等 | 中等 |
| **数据验证** | Pydantic 内置 | 需手动 | ORM Forms |
| **自动文档** | 内置 Swagger | 需扩展 | DRF 可选 |
| **数据库** | 无内置 | 无内置 | ORM 内置 |
| **适用场景** | API 服务、微服务 | 小型应用、微服务 | 大型 Web 应用 |
| **学习曲线** | 中等 | 平缓 | 陡峭 |

**FastAPI 优势：**
- 自动生成 API 文档
- 原生异步支持，性能优秀
- 类型安全，数据验证自动化

**Django 优势：**
- 全功能自带（ORM、Admin、Auth）
- 适合内容管理系统
- 生态成熟，社区庞大

---

### Q3: Uvicorn 是什么？它与 FastAPI 的关系是什么？

**参考答案：**

**Uvicorn 简介：**
Uvicorn 是一个基于 ASGI（Asynchronous Server Gateway Interface）规范的 Python ASGI 服务器实现。它是运行 FastAPI 应用的推荐服务器。

**核心特性：**

| 特性 | 说明 |
|------|------|
| **ASGI 规范** | 异步服务器网关接口标准 |
| **uvloop** | 使用 uvloop 事件循环，性能极高 |
| **httptools** | 基于 httptools HTTP 解析器 |
| **WebSocket** | 支持 WebSocket 协议 |
| **热重载** | 支持开发模式热重载 |

**启动方式对比：**

```python
# 方式1：命令行启动
# uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 方式2：代码启动
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",  # 应用模块路径
        host="0.0.0.0",  # 监听地址
        port=8000,  # 端口号
        reload=True,  # 开发模式热重载
        log_level="info",  # 日志级别
        workers=4,  # 工作进程数（仅生产模式）
    )

# 方式3：ASGI 应用直接调用
# asyncio.run(app({}).execute("http"))
```

**FastAPI 与 Uvicorn 关系：**
- FastAPI 是应用框架（定义路由、逻辑）
- Uvicorn 是 ASGI 服务器（运行应用、处理请求）
- FastAPI 遵循 ASGI 规范，可部署在任何 ASGI 服务器上

---

### Q4: 什么是 ASGI？它与 WSGI 有什么区别？

**参考答案：**

**ASGI（Asynchronous Server Gateway Interface）：**
ASGI 是 Python 异步 Web 服务器的应用接口规范，是 WSGI 的异步扩展。

**WSGI vs ASGI 对比：**

| 特性 | WSGI | ASGI |
|------|------|------|
| **全称** | Web Server Gateway Interface | Asynchronous Server Gateway Interface |
| **设计目标** | 同步 Web 应用 | 异步 Web 应用 |
| **请求模型** | 同步阻塞 | 异步非阻塞 |
| **WebSocket** | 不支持 | 支持 |
| **Server-Sent Events** | 不支持 | 支持 |
| **并发模型** | 每请求一线程/进程 | 单进程异步事件循环 |
| **兼容性** | 无法直接运行 ASGI 应用 | 可通过适配器运行 WSGI |

**ASGI 应用结构：**

```python
# ASGI 应用是一个异步 callable
async def app(scope, receive, send):
    """
    scope: 包含连接信息的字典（如 HTTP 方法、路径、headers）
    receive: 获取请求消息的异步 callable
    send: 发送响应消息的异步 callable
    """
    # 接收请求
    message = await receive()
    
    # 处理逻辑
    response_body = b"Hello, World!"
    
    # 发送响应
    await send({
        "type": "http.response.start",
        "status": 200,
        "headers": [[b"content-type", b"text/plain"]],
    })
    await send({
        "type": "http.response.body",
        "body": response_body,
    })
```

---

### Q5: FastAPI 中如何定义路径参数（Path Parameter）？

**参考答案：**

**基本语法：**

```python
from fastapi import FastAPI

app = FastAPI()

# 路径参数使用 {} 定义，类型自动验证
@app.get("/items/{item_id}")
async def get_item(item_id: int):
    return {"item_id": item_id}

# 可用的类型验证：
# int, float, str, bool, path 等
```

**类型验证示例：**

```python
@app.get("/documents/{document_id}")
async def get_document(document_id: int):
    """
    document_id 会自动验证是否为整数
    - 如果不是整数，返回 422 错误
    - 如果是整数，传递给函数
    """
    return {"document_id": document_id, "status": "found"}
```

**路径优先级：**
当有多个匹配的路由时，FastAPI 按照定义顺序匹配：

```python
# 静态路由优先于动态路由
@app.get("/documents/all")
async def get_all_documents():
    return {"message": "all documents"}

# 动态路由
@app.get("/documents/{document_id}")
async def get_document(document_id: int):
    return {"document_id": document_id}
```

**项目中的应用：**

```python
# rag-qa-system/app/api/v1/qa.py
@router.get("/{session_id}")
async def get_session_history(
    session_id: str,  # 路径参数
    skip: int = 0,    # 查询参数
    limit: int = 20   # 查询参数
):
    # 获取会话历史
    logs, total = qa_service.get_qa_history(
        session_id=session_id,
        skip=skip,
        limit=limit
    )
    return {"items": logs, "total": total}
```

---

### Q6: FastAPI 中如何定义查询参数（Query Parameter）？

**参考答案：**

**基础用法：**

```python
from fastapi import FastAPI

app = FastAPI()

# 查询参数直接作为函数参数
@app.get("/items")
async def get_items(
    skip: int = 0,      # 可选参数，有默认值
    limit: int = 10,    # 可选参数，有默认值
    category: str = None # 可选参数，可以为 None
):
    return {
        "skip": skip,
        "limit": limit,
        "category": category
    }
```

**必填查询参数：**
不提供默认值的参数变为必填：

```python
@app.get("/search")
async def search(q: str):  # q 是必填参数
    return {"query": q}
```

**参数验证：**
使用 Pydantic 类型注解和验证器：

```python
from fastapi import Query

@app.get("/documents")
async def get_documents(
    skip: int = Query(0, ge=0, description="跳过数量"),  # ge=0 表示 >= 0
    limit: int = Query(20, ge=1, le=100, description="返回数量"),  # 1 <= x <= 100
    status: int = Query(None, description="文档状态筛选")
):
    return {"skip": skip, "limit": limit, "status": status}
```

**布尔类型处理：**
FastAPI 会自动转换字符串 "true"/"false" 为布尔值：

```python
@app.get("/config")
async def get_config(
    enable_cache: bool = False  # ?enable_cache=true
):
    return {"enable_cache": enable_cache}
```

---

### Q7: FastAPI 中如何定义请求体（Request Body）？

**参考答案：**

**使用 Pydantic 模型定义请求体：**

```python
from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import Optional

app = FastAPI()

# 定义 Pydantic 模型
class QAAskRequest(BaseModel):
    """问答请求模型"""
    question: str = Field(..., min_length=1, max_length=1000, description="用户问题")
    top_k: Optional[int] = Field(5, ge=1, le=20, description="检索数量")
    temperature: Optional[float] = Field(0.3, ge=0.0, le=2.0, description="温度参数")
    session_id: Optional[str] = Field(None, description="会话ID")

# 使用 Pydantic 模型作为请求体
@app.post("/ask")
async def ask_question(request: QAAskRequest):
    """
    FastAPI 会自动：
    1. 解析 JSON 请求体
    2. 验证数据类型和约束
    3. 转换为 Pydantic 模型实例
    """
    return {
        "question": request.question,
        "config": {
            "top_k": request.top_k,
            "temperature": request.temperature
        }
    }
```

**嵌套模型：**

```python
class Source(BaseModel):
    """来源文档模型"""
    vector_id: str
    filename: str
    similarity: float

class QAResponse(BaseModel):
    """问答响应模型"""
    answer: str
    sources: list[Source]  # 嵌套列表
    cache_hit: bool
    response_time_ms: int
```

**可选字段处理：**

```python
class DocumentUploadRequest(BaseModel):
    filename: str
    content: Optional[str] = None  # 可选字段
    tags: list[str] = []  # 默认空列表
```

**项目中的应用：**

```python
# rag-qa-system/app/services/qa_service.py
async def ask(
    self,
    question: str,
    db: Session,
    session_id: str = None,
    top_k: int = None,
    temperature: float = 0.3
) -> Dict[str, Any]:
    # 函数参数直接接收解析后的数据
    # 无需手动从 request body 中提取
    pass
```

---

### Q8: FastAPI 如何处理文件上传？

**参考答案：**

**基本文件上传：**

```python
from fastapi import FastAPI, UploadFile, File
from typing import List

app = FastAPI()

@app.post("/upload")
async def upload_file(
    file: UploadFile = File(...),  # 单个文件，必填
    description: str = None  # 其他表单字段
):
    # 读取文件内容
    contents = await file.read()
    
    # 保存到磁盘
    with open(f"uploads/{file.filename}", "wb") as f:
        f.write(contents)
    
    return {
        "filename": file.filename,
        "content_type": file.content_type,
        "size": len(contents)
    }
```

**多文件上传：**

```python
@app.post("/upload/multiple")
async def upload_multiple_files(
    files: List[UploadFile] = File(...)
):
    results = []
    for file in files:
        contents = await file.read()
        results.append({
            "filename": file.filename,
            "size": len(contents)
        })
    return {"files": results}
```

**带额外参数的表单上传：**

```python
from fastapi import Form

@app.post("/documents/upload")
async def upload_document(
    file: UploadFile = File(...),
    category: str = Form(...),  # 表单字段
    tags: str = Form("default")  # 带默认值的表单字段
):
    # 处理上传
    return {
        "filename": file.filename,
        "category": category,
        "tags": tags
    }
```

**项目中的应用：**

```python
# rag-qa-system/app/api/v1/document.py
@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),  # 上传文件
    db: Session = Depends(get_db)
):
    # 读取文件内容
    file_content = await file.read()
    
    # 调用文档服务处理
    document = await document_service.upload_document(
        file_content=file_content,
        filename=file.filename,
        db=db
    )
    
    return {"id": document.id, "filename": document.filename}
```

---

### Q9: FastAPI 如何处理响应模型（Response Model）？

**参考答案：**

**使用 response_model 参数：**

```python
from pydantic import BaseModel
from typing import Optional, List

class DocumentResponse(BaseModel):
    """文档响应模型"""
    id: int
    filename: str
    status: int
    chunk_count: int = 0  # 带默认值

@app.get("/documents/{doc_id}", response_model=DocumentResponse)
async def get_document(doc_id: int):
    # FastAPI 会自动过滤响应，只返回模型中定义的字段
    return {
        "id": doc_id,
        "filename": "test.pdf",
        "status": 1,
        "file_size": 1024,  # 这个字段会被过滤掉
        "internal_data": "secret"  # 这个字段也会被过滤掉
    }
```

**响应状态码设置：**

```python
from fastapi import status

@app.post("/documents", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def create_document():
    return {"id": 1, "filename": "new.pdf", "status": 0}
```

**响应为列表：**

```python
from typing import List

@app.get("/documents", response_model=List[DocumentResponse])
async def list_documents():
    return [
        {"id": 1, "filename": "doc1.pdf", "status": 1},
        {"id": 2, "filename": "doc2.pdf", "status": 1}
    ]
```

**可选响应模型：**

```python
from typing import Optional

@app.get("/document/{doc_id}", response_model=Optional[DocumentResponse])
async def get_document(doc_id: int):
    doc = db.query(Document).get(doc_id)
    if not doc:
        return None  # 返回 200 但 body 为 null
    return doc
```

**项目中的应用：**

```python
# 响应模型自动序列化
class QAAskRequest(BaseModel):
    question: str

class QAResponse(BaseModel):
    answer: str
    sources: List[dict]
    cache_hit: bool
    response_time_ms: int

@router.post("/ask", response_model=QAResponse)
async def ask_question(request: QAAskRequest):
    result = await qa_service.ask(question=request.question, db=db)
    return result  # 自动序列化为 JSON
```

---

### Q10: FastAPI 中如何处理 Header 参数和 Cookie？

**参考答案：**

**Header 参数：**

```python
from fastapi import Header

@app.get("/items")
async def get_items(
    x_request_id: str = Header(None),  # 自动转换 Header 名称
    authorization: str = Header(None)  # 自动转换下划线为连字符
):
    return {
        "x_request_id": x_request_id,
        "authorization": authorization
    }
```

**自定义 Header 名称：**

```python
from fastapi import Header

@app.get("/secure")
async def get_secure_data(
    # 自定义 Header 名称
    user_agent: str = Header(None, alias="User-Agent"),
    content_type: str = Header(None, alias="Content-Type")
):
    return {"user_agent": user_agent}
```

**Cookie 参数：**

```python
from fastapi import Cookie

@app.get("/profile")
async def get_profile(
    session_id: str = Cookie(None)  # 从 Cookie 中获取 session_id
):
    if not session_id:
        return {"error": "Not authenticated"}
    return {"session_id": session_id}
```

**设置 Cookie：**

```python
from fastapi import Response

@app.post("/login")
async def login(response: Response):
    # 设置 Cookie
    response.set_cookie(
        key="session_id",
        value="abc123",
        max_age=3600,  # 有效期（秒）
        httponly=True,  # 禁止 JavaScript 访问
        secure=True,  # 仅 HTTPS
        samesite="lax"  # CSRF 防护
    )
    return {"message": "Logged in"}
```

---

## 2. 异步编程

### Q11: FastAPI 中 async 和 await 的工作原理是什么？

**参考答案：**

**协程（Coroutine）基础：**
Python 中的协程是用 async def 定义的特殊函数，调用时返回一个协程对象：

```python
# 普通函数
def sync_function():
    return "result"

# 异步函数
async def async_function():
    return "result"

# 调用异步函数得到协程对象
coro = async_function()  # <coroutine object>
result = await coro  # 执行协程并获取结果
```

**事件循环（Event Loop）：**
事件循环是异步编程的核心，它管理协程的执行：

```python
import asyncio

# 方式1：asyncio.run()（推荐）
async def main():
    result = await async_function()
    return result

asyncio.run(main())

# 方式2：手动管理事件循环
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
try:
    result = loop.run_until_complete(main())
finally:
    loop.close()
```

**FastAPI 中的异步处理：**

```python
from fastapi import FastAPI
import asyncio

app = FastAPI()

# 异步路由处理器
@app.get("/async")
async def async_handler():
    # 异步等待 I/O 操作
    result = await asyncio.sleep(1)  # 模拟 I/O 等待
    return {"message": "async result"}

# 同步函数会自动在线程池中运行
@app.get("/sync")
def sync_handler():
    # 这是同步代码
    return {"message": "sync result"}
```

**await 可以等待的内容：**
| 类型 | 说明 | 示例 |
|------|------|------|
| 协程 | async 函数调用 | `await async_function()` |
| Task | 计划的任务 | `await task` |
| Future | 异步结果 | `await asyncio.sleep()` |
| 队列 | 异步队列 | `await queue.get()` |

---

### Q12: 什么时候应该使用 async def，什么时候使用普通 def？

**参考答案：**

**使用 async def 的场景：**

```python
# 场景1：调用异步库
async def fetch_data():
    # 使用 httpx 异步 HTTP 客户端
    async with httpx.AsyncClient() as client:
        response = await client.get("https://api.example.com/data")
        return response.json()

# 场景2：访问数据库（使用异步驱动）
async def get_user(db: AsyncSession):
    result = await db.execute(select(User).where(User.id == 1))
    return result.scalar_one_or_none()

# 场景3：使用异步文件 I/O
async def read_file():
    async with aiofiles.open("data.txt", "r") as f:
        content = await f.read()
    return content

# 场景4：同时执行多个 I/O 操作
async def fetch_multiple():
    # 并行执行多个请求
    tasks = [
        fetch_url("https://api1.com"),
        fetch_url("https://api2.com"),
        fetch_url("https://api3.com"),
    ]
    results = await asyncio.gather(*tasks)
    return results
```

**使用普通 def 的场景：**

```python
# 场景1：只进行 CPU 计算
def process_data(data):
    # 同步计算
    return sum(x ** 2 for x in data)

# 场景2：使用同步库
def sync_http_call():
    # 使用同步 requests 库
    response = requests.get("https://api.example.com")
    return response.json()

# 场景3：简单的返回值
@app.get("/health")
def health_check():  # 不需要 async
    return {"status": "ok"}
```

**FastAPI 的自动处理：**

```python
# FastAPI 会自动处理这两种情况
@app.get("/example")
async def async_handler():
    # async def：直接在事件循环中执行
    return await async_operation()

@app.get("/example2")
def sync_handler():
    # 普通 def：自动在线程池中执行
    return sync_operation()
```

**最佳实践：**

```python
# 保持一致性：同一函数调用链中尽量使用 async
async def process_request():
    # 好：整个调用链都是异步的
    data = await fetch_data()
    result = await process_data(data)
    return result

# 避免：混合同步和异步
async def bad_example():
    # 不推荐：同步调用会阻塞事件循环
    data = sync_http_call()
    return await async_process(data)
```

---

### Q13: 如何在 FastAPI 中并行执行多个异步任务？

**参考答案：**

**asyncio.gather() - 并行执行多个任务：**

```python
import asyncio
from fastapi import FastAPI

app = FastAPI()

async def fetch_document(doc_id: int):
    """模拟获取文档"""
    await asyncio.sleep(0.1)
    return {"id": doc_id, "name": f"doc_{doc_id}.pdf"}

async def fetch_user(user_id: int):
    """模拟获取用户"""
    await asyncio.sleep(0.1)
    return {"id": user_id, "name": f"user_{user_id}"}

@app.get("/parallel")
async def parallel_fetch():
    # 并行执行多个协程
    doc_task = fetch_document(1)
    user_task = fetch_user(1)
    
    # gather 等待所有任务完成
    results = await asyncio.gather(doc_task, user_task)
    
    return {
        "document": results[0],
        "user": results[1]
    }
```

**asyncio.create_task() - 创建后台任务：**

```python
@app.post("/process")
async def process_document(doc_id: int):
    # 创建后台任务，立即返回
    task = asyncio.create_task(
        heavy_processing(doc_id)
    )
    
    # 立即返回，不等待处理完成
    return {"message": "Processing started", "task_id": id(task)}

async def heavy_processing(doc_id: int):
    """后台处理任务"""
    await asyncio.sleep(10)  # 模拟长时间处理
    print(f"Document {doc_id} processed")
```

**asyncio.wait() - 等待多个任务：**

```python
async def run_tasks():
    tasks = [fetch_data(i) for i in range(10)]
    
    # 等待所有任务完成
    done, pending = await asyncio.wait(tasks)
    
    # 获取结果
    results = [task.result() for task in done]
    return results
```

**异常处理：**

```python
async def parallel_with_error_handling():
    tasks = [
        fetch_data(1),
        fetch_data(2),
        fetch_may_fail(3),  # 可能失败的任务
    ]
    
    # return_exceptions=True 会捕获异常而非抛出
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # 处理结果和异常
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            print(f"Task {i} failed: {result}")
        else:
            print(f"Task {i} success: {result}")
    
    return results
```

**项目中的应用：**

```python
# 并行处理文档切片和向量化
async def process_document(file_path: str):
    # 解析文档（同步 I/O）
    content = parser.parse(file_path)
    
    # 并行执行切分和向量化
    chunks_task = asyncio.to_thread(split_text, content)
    embed_task = asyncio.to_thread(compute_embeddings, content)
    
    chunks, embeddings = await asyncio.gather(chunks_task, embed_task)
    
    # 批量存储
    await asyncio.to_thread(vector_store.add_batch, embeddings, chunks)
```

---

### Q14: 如何在 FastAPI 中正确处理数据库连接和会话？

**参考答案：**

**使用依赖注入管理数据库会话：**

```python
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session

# 数据库配置
DATABASE_URL = "mysql+aiomysql://user:pass@localhost/db"

# 创建引擎（同步）
from sqlalchemy import create_engine
engine = create_engine(DATABASE_URL)

# 创建会话工厂
def get_db():
    """数据库会话依赖注入"""
    db = SessionLocal()  # 创建新会话
    try:
        yield db  # 提供会话给路由
    finally:
        db.close()  # 确保关闭会话

app = FastAPI()

@app.get("/documents")
async def list_documents(db: Session = Depends(get_db)):
    # db 是已经开启的会话
    documents = db.query(Document).all()
    return documents
```

**异步数据库会话：**

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# 异步引擎
async_engine = create_async_engine(
    "mysql+aiomysql://user:pass@localhost/db",
    echo=True,
)

# 异步会话工厂
AsyncSessionLocal = sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

async def get_async_db():
    """异步数据库会话"""
    async with AsyncSessionLocal() as session:
        yield session

@app.get("/documents")
async def list_documents(db: AsyncSession = Depends(get_async_db)):
    # 使用 await 执行查询
    result = await db.execute(select(Document))
    documents = result.scalars().all()
    return documents
```

**会话管理最佳实践：**

```python
class DocumentService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_document(self, doc_id: int) -> Optional[Document]:
        return self.db.query(Document).filter(
            Document.id == doc_id
        ).first()
    
    def create_document(self, filename: str) -> Document:
        doc = Document(filename=filename, status=0)
        self.db.add(doc)
        self.db.commit()  # 提交事务
        self.db.refresh(doc)  # 刷新获取自动生成字段
        return doc
    
    def delete_document(self, doc_id: int) -> bool:
        doc = self.get_document(doc_id)
        if doc:
            self.db.delete(doc)
            self.db.commit()
            return True
        return False
```

**项目中的应用：**

```python
# rag-qa-system/app/api/v1/qa.py
@router.post("/ask")
async def ask_question(
    request: QAAskRequest,
    db: Session = Depends(get_db)  # 依赖注入数据库会话
):
    # 直接使用会话
    result = await qa_service.ask(
        question=request.question,
        db=db,  # 传递会话给服务层
        session_id=request.session_id,
        top_k=request.top_k
    )
    return result
```

---

### Q15: 什么是依赖注入（Dependency Injection）？FastAPI 中如何使用？

**参考答案：**

**依赖注入概念：**
依赖注入是一种设计模式，允许将依赖（服务、配置等）从外部注入到函数或类中，而不是在内部创建。

**FastAPI 依赖注入系统：**

```python
from fastapi import FastAPI, Depends

app = FastAPI()

# 定义依赖
def get_database():
    """数据库依赖"""
    db = create_db_connection()
    try:
        yield db
    finally:
        db.close()

def verify_token(token: str = Header(...)):
    """认证依赖"""
    if token != "valid-token":
        raise HTTPException(status_code=401, detail="Invalid token")
    return token

# 使用依赖
@app.get("/items")
async def read_items(
    db = Depends(get_database),  # 注入数据库
    token = Depends(verify_token)  # 注入认证
):
    return {"db": db, "token": token}
```

**依赖链：**

```python
# 依赖可以链式调用
def get_current_user(token: str = Depends(verify_token)):
    """从 token 获取当前用户"""
    return get_user_from_token(token)

def get_user_documents(user = Depends(get_current_user)):
    """获取用户文档（自动注入用户）"""
    return get_documents_by_user(user.id)

@app.get("/my-documents")
async def list_my_documents(
    docs = Depends(get_user_documents)
):
    return docs
```

**带参数的依赖：**

```python
from typing import Optional

def pagination(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100)
):
    """分页依赖"""
    return {"skip": skip, "limit": limit}

@app.get("/items")
async def list_items(
    pagination: dict = Depends(pagination)
):
    return pagination
```

**类作为依赖：**

```python
class PaginationParams:
    def __init__(
        self,
        skip: int = Query(0, ge=0),
        limit: int = Query(10, ge=1, le=100)
    ):
        self.skip = skip
        self.limit = limit

@app.get("/items")
async def list_items(params: PaginationParams = Depends()):
    return {"skip": params.skip, "limit": params.limit}
```

**项目中的应用：**

```python
# rag-qa-system/app/api/v1/deps.py
from app.core.database import SessionLocal

def get_db():
    """获取数据库会话的依赖"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# rag-qa-system/app/api/v1/qa.py
from app.api.v1.deps import get_db

@router.post("/ask")
async def ask_question(
    request: QAAskRequest,
    db: Session = Depends(get_db)  # 使用依赖注入
):
    # db 已经准备好可用
    pass
```

---

### Q16: 如何在 FastAPI 中实现后台任务？

**参考答案：**

**BackgroundTasks 组件：**

```python
from fastapi import FastAPI, BackgroundTasks

app = FastAPI()

def send_email(email: str, message: str):
    """后台任务函数（同步）"""
    # 发送邮件逻辑
    print(f"Sending email to {email}: {message}")

@app.post("/register")
async def register(
    email: str,
    background_tasks: BackgroundTasks
):
    # 添加后台任务
    background_tasks.add_task(send_email, email, "Welcome!")
    
    # 立即返回，不等待邮件发送
    return {"message": "Registration successful"}
```

**异步后台任务：**

```python
async def async_send_email(email: str, message: str):
    """异步后台任务"""
    await asyncio.sleep(2)  # 模拟异步操作
    print(f"Email sent to {email}")

@app.post("/send")
async def send_notification(
    email: str,
    background_tasks: BackgroundTasks
):
    # 使用异步任务
    background_tasks.add_task(async_send_email, email, "Notification")
    return {"status": "queued"}
```

**完整的异步任务处理：**

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor
from fastapi import BackgroundTasks

# 线程池用于运行同步代码
executor = ThreadPoolExecutor(max_workers=4)

def heavy_sync_task(data: dict):
    """耗时的同步任务"""
    import time
    time.sleep(5)  # 模拟处理
    return {"processed": True, "data": data}

async def process_document_background(
    document_id: int,
    background_tasks: BackgroundTasks
):
    """后台处理文档"""
    # 启动后台处理
    loop = asyncio.get_event_loop()
    loop.run_in_executor(
        executor,  # 线程池
        heavy_sync_task,  # 同步函数
        {"doc_id": document_id}
    )
    
    return {"status": "processing", "document_id": document_id}
```

**项目中的应用：**

```python
# 在文档上传后异步处理
@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None
):
    # 先保存文件和记录
    document = await save_document(file)
    
    # 添加后台索引任务
    if background_tasks:
        background_tasks.add_task(
            index_document,
            document_id=document.id
        )
    
    return {
        "id": document.id,
        "status": "processing"
    }
```

---

## 3. 路由与参数

### Q17: FastAPI 中如何组织路由？什么是 APIRouter？

**参考答案：**

**APIRouter 的使用：**

```python
# app/api/v1/qa.py
from fastapi import APIRouter, Depends

router = APIRouter(prefix="/qa", tags=["问答"])

@router.post("/ask")
async def ask_question(question: str):
    return {"answer": "..."}

# app/main.py
from fastapi import FastAPI
from app.api.v1 import qa, document, system

app = FastAPI()

# 注册路由
app.include_router(qa.router)
app.include_router(document.router)
app.include_router(system.router)
```

**路由前缀和标签：**

```python
# app/api/v1/qa.py
router = APIRouter(
    prefix="/qa",      # 路由前缀
    tags=["问答模块"],  # OpenAPI 标签
    responses={404: {"description": "Not found"}}
)

@router.get("/history", summary="获取问答历史")
async def get_history():
    pass
```

**路由嵌套：**

```python
# 嵌套路由结构
# app/api/v1/
#   ├── __init__.py
#   ├── qa.py
#   ├── document.py
#   └── system.py

# app/api/v1/__init__.py
from fastapi import APIRouter
from . import qa, document, system

router = APIRouter(prefix="/api/v1")

router.include_router(qa.router)
router.include_router(document.router)
router.include_router(system.router)
```

**项目中的路由组织：**

```python
# rag-qa-system/app/api/v1/__init__.py
from fastapi import APIRouter

api_router = APIRouter(prefix="/api/v1")

# 延迟导入避免循环依赖
def include_routes():
    from . import qa, document, knowledge, system
    api_router.include_router(qa.router)
    api_router.include_router(document.router)
    api_router.include_router(knowledge.router)
    api_router.include_router(system.router)

# rag-qa-system/app/main.py
from app.api.v1 import api_router

app.include_router(
    api_router,
    prefix=settings.api_v1_prefix  # /api/v1
)
```

---

### Q18: FastAPI 中如何实现 API 版本控制？

**参考答案：**

**路径版本控制（推荐）：**

```python
# app/api/v1/items.py
from fastapi import APIRouter

router = APIRouter(prefix="/v1")

@router.get("/items")
async def list_items_v1():
    return {"version": "v1", "items": []}

# app/api/v2/items.py
from fastapi import APIRouter

router = APIRouter(prefix="/v2")

@router.get("/items")
async def list_items_v2():
    return {"version": "v2", "items": [], "new_feature": True}

# app/main.py
from fastapi import FastAPI
from app.api.v1 import items as items_v1
from app.api.v2 import items as items_v2

app = FastAPI()

app.include_router(items_v1.router)
app.include_router(items_v2.router)
```

**Header 版本控制：**

```python
from fastapi import Header, HTTPException

@app.get("/items")
async def list_items(
    x_api_version: str = Header("v1", alias="X-API-Version")
):
    if x_api_version == "v1":
        return {"items": [...], "version": "v1"}
    elif x_api_version == "v2":
        return {"items": [...], "version": "v2", "extra": True}
    else:
        raise HTTPException(status_code=400, detail="Invalid API version")
```

**查询参数版本控制：**

```python
@app.get("/items")
async def list_items(version: str = Query("v1")):
    if version == "v1":
        return list_items_v1()
    return list_items_v2()
```

**项目中的版本控制实践：**

```python
# rag-qa-system/app/config.py
class Settings(BaseSettings):
    api_v1_prefix: str = "/api/v1"
    api_version: str = "1.0.0"

# 路由中使用版本信息
@router.get("/version")
async def get_api_version():
    return {
        "version": settings.api_version,
        "prefix": settings.api_v1_prefix
    }
```

---

### Q19: FastAPI 中如何处理可选参数和默认值？

**参考答案：**

**可选路径参数：**

```python
@app.get("/documents/{document_id}")  # 必填
async def get_document(document_id: int):
    pass

@app.get("/documents/")  # 可选路径
async def list_documents():
    pass
```

**可选查询参数：**

```python
from typing import Optional

@app.get("/search")
async def search(
    q: Optional[str] = None,  # 可选字符串
    category: Optional[str] = None,  # 可选分类
    page: int = 1,  # 有默认值
    size: int = 20   # 有默认值
):
    return {"query": q, "category": category, "page": page, "size": size}
```

**带验证的可选参数：**

```python
from fastapi import Query
from typing import Optional

@app.get("/documents")
async def get_documents(
    status: Optional[int] = Query(
        None,  # 默认值
        ge=0,  # >= 0
        le=10,  # <= 10
        description="文档状态"  # 文档描述
    ),
    created_after: Optional[str] = Query(
        None,
        regex=r"^\d{4}-\d{2}-\d{2}$",  # 日期格式正则
        description="创建日期（YYYY-MM-DD）"
    )
):
    pass
```

**可选请求体字段：**

```python
from pydantic import BaseModel, Field
from typing import Optional

class UpdateDocumentRequest(BaseModel):
    filename: Optional[str] = None
    tags: Optional[list[str]] = None
    status: Optional[int] = Field(None, ge=0, le=10)

@app.patch("/documents/{doc_id}")
async def update_document(
    doc_id: int,
    request: UpdateDocumentRequest
):
    # request 中只有非 None 的字段会被更新
    updates = request.dict(exclude_unset=True)
    return {"updated": updates}
```

**项目中的应用：**

```python
# rag-qa-system/app/services/qa_service.py
async def ask(
    self,
    question: str,
    db: Session,
    session_id: str = None,  # 可选
    top_k: int = None,        # 可选，有默认值
    temperature: float = 0.3  # 有默认值
) -> Dict[str, Any]:
    # 使用 None 或默认值
    k = top_k or runtime_config.retrieval_top_k
    temp = temperature or 0.3
```

---

### Q20: FastAPI 中如何实现请求参数验证？

**参考答案：**

**Pydantic 模型验证：**

```python
from pydantic import BaseModel, Field, validator

class UserCreate(BaseModel):
    # 必填字段
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., pattern=r"^[\w\.-]+@[\w\.-]+\.\w+$")
    
    # 可选字段带默认值
    age: int = Field(18, ge=0, le=150)
    tags: list[str] = Field(default_factory=list)
    
    # 自定义验证器
    @validator("username")
    def username_alphanumeric(cls, v):
        if not v.replace("_", "").replace("-", "").isalnum():
            raise ValueError("用户名只能包含字母、数字、下划线和连字符")
        return v.lower()  # 自动转为小写
    
    @validator("email")
    def email_lowercase(cls, v):
        return v.lower()
    
    class Config:
        # Pydantic v2 配置
        model_config = {
            "json_schema_extra": {
                "example": {
                    "username": "john_doe",
                    "email": "john@example.com",
                    "age": 25
                }
            }
        }
```

**嵌套模型验证：**

```python
class Address(BaseModel):
    street: str
    city: str
    zip_code: str = Field(..., pattern=r"^\d{6}$")

class UserWithAddress(BaseModel):
    username: str
    address: Address  # 嵌套模型自动验证

@app.post("/users")
async def create_user(user: UserWithAddress):
    return user
```

**枚举类型验证：**

```python
from enum import Enum

class DocumentStatus(Enum):
    PROCESSING = 0
    COMPLETED = 1
    FAILED = 2

@app.get("/documents")
async def list_documents(status: DocumentStatus = None):
    return {"status": status.value if status else "all"}
```

**项目中的应用：**

```python
# rag-qa-system/app/schemas/common.py
class PageParams(BaseModel):
    """分页参数"""
    skip: int = Field(0, ge=0, description="跳过数量")
    limit: int = Field(20, ge=1, le=100, description="返回数量")

class DocumentUploadRequest(BaseModel):
    """文档上传请求"""
    filename: str = Field(..., min_length=1, max_length=255)
    category: Optional[str] = Field(None, max_length=50)
    tags: list[str] = Field(default_factory=list)
    
    @validator("filename")
    def validate_filename(cls, v):
        # 验证文件扩展名
        allowed_exts = {".pdf", ".docx", ".md", ".txt"}
        ext = os.path.splitext(v)[1].lower()
        if ext not in allowed_exts:
            raise ValueError(f"不支持的文件类型: {ext}")
        return v
```

---

## 4. 中间件

### Q21: FastAPI 中间件是什么？如何创建自定义中间件？

**参考答案：**

**FastAPI 中间件工作原理：**

中间件是一个可以在请求到达路由之前和响应返回给客户端之前执行代码的函数。

```
请求 → 中间件1 → 中间件2 → 路由处理器 → 中间件2 → 中间件1 → 响应
```

**内置中间件：**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

app = FastAPI()

# CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# GZip 压缩中间件
app.add_middleware(GZipMiddleware, minimum_size=1000)
```

**自定义中间件：**

```python
from fastapi import FastAPI, Request
import time

app = FastAPI()

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """添加处理时间头"""
    start_time = time.time()
    
    # 处理请求
    response = await call_next(request)
    
    # 添加自定义头
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    
    return response

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """请求日志中间件"""
    print(f"{request.method} {request.url.path}")
    
    response = await call_next(request)
    
    print(f"Status: {response.status_code}")
    return response
```

**项目中的请求日志中间件：**

```python
# rag-qa-system/app/main.py
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """请求日志中间件 - 记录每个请求的路径、方法、耗时"""
    start_time = time.time()
    method = request.method
    path = request.url.path
    client_ip = request.client.host if request.client else "unknown"
    
    try:
        response = await call_next(request)
    except Exception as e:
        logger.error(f"请求处理异常: {method} {path} - {str(e)}")
        raise
    
    elapsed = (time.time() - start_time) * 1000
    status_code = response.status_code
    
    # 记录日志
    logger.info(f"{method} {path} - {status_code} - {elapsed:.2f}ms - {client_ip}")
    
    # 添加处理时间响应头
    response.headers["X-Process-Time"] = str(elapsed)
    
    return response
```

**中间件执行顺序：**

```python
app = FastAPI()

# 添加顺序 = 执行顺序（先添加先执行）
app.add_middleware(SomeMiddleware)  # 1. 最后执行
app.add_middleware(AnotherMiddleware)  # 2. 先执行
app.add_middleware(ThirdMiddleware)  # 3. 最先执行
```

---

### Q22: 如何配置 CORS（跨域资源共享）？

**参考答案：**

**CORS 配置选项：**

| 选项 | 说明 | 示例 |
|------|------|------|
| allow_origins | 允许的源列表 | ["http://localhost:3000"] |
| allow_credentials | 是否允许携带凭证 | True/False |
| allow_methods | 允许的 HTTP 方法 | ["GET", "POST"] |
| allow_headers | 允许的请求头 | ["*"] |
| expose_headers | 允许浏览器访问的响应头 | ["X-Request-ID"] |
| max_age | 预检请求缓存时间 | 600（秒） |

**常见 CORS 配置：**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# 开发环境配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# 生产环境配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://example.com"],  # 具体域名
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
    max_age=3600,
)
```

**允许所有源（仅开发环境）：**

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有源
    allow_credentials=False,  # 不能与 "*" 一起使用 True
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**项目中的 CORS 配置：**

```python
# rag-qa-system/app/config.py
class Settings(BaseSettings):
    cors_origins_list: list[str] = ["http://localhost:5173", "http://localhost:3000"]
    cors_allow_credentials: bool = True
    cors_allow_methods_list: list[str] = ["*"]
    cors_allow_headers: str = "*"

# rag-qa-system/app/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods_list,
    allow_headers=settings.cors_allow_headers.split(","),
)
```

**CORS 预检请求（OPTIONS）：**
FastAPI 会自动处理 OPTIONS 预检请求，无需手动定义。

---

### Q23: FastAPI 如何处理静态文件和静态资源？

**参考答案：**

**配置静态文件目录：**

```python
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import os

app = FastAPI()

# 创建静态文件目录
static_dir = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(static_dir, exist_ok=True)

# 挂载静态文件
app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
async def root():
    return {"message": "API is running"}
```

**访问静态文件：**
文件 `static/css/style.css` 可以通过 `/static/css/style.css` 访问。

**前端构建产物：**

```python
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pathlib import Path

app = FastAPI()

# Vue/React 构建产物目录
dist_dir = Path(__file__).parent / "frontend" / "dist"

if dist_dir.exists():
    app.mount("/", StaticFiles(directory=str(dist_dir), html=True), name="static")

# API 路由需要放在挂载之前
@app.get("/api/health")
async def health():
    return {"status": "ok"}
```

**动态生成文件：**

```python
from fastapi import Response
from fastapi.responses import StreamingResponse
import io

@app.get("/download/{filename}")
async def download_file(filename: str):
    # 动态生成文件内容
    content = f"Generated content for {filename}"
    
    return Response(
        content=content,
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )
```

**项目中的前端部署：**

```python
# rag-qa-system/app/main.py
# 在应用启动时挂载前端静态文件
frontend_dist = Path(__file__).parent.parent / "rag-qa-frontend" / "dist"

if frontend_dist.exists():
    app.mount(
        "/",
        StaticFiles(directory=str(frontend_dist), html=True),
        name="frontend"
    )
```

---

## 5. 异常处理

### Q24: FastAPI 如何处理 HTTP 异常？

**参考答案：**

**常用 HTTP 异常：**

| 状态码 | 异常 | 说明 |
|--------|------|------|
| 400 | HTTPException(400) | 坏请求 |
| 401 | HTTPException(401) | 未授权 |
| 403 | HTTPException(403) | 禁止访问 |
| 404 | HTTPException(404) | 未找到 |
| 422 | HTTPException(422) | 验证错误（Pydantic 自动处理） |
| 500 | HTTPException(500) | 服务器内部错误 |

**基本用法：**

```python
from fastapi import FastAPI, HTTPException

app = FastAPI()

@app.get("/items/{item_id}")
async def get_item(item_id: int):
    if item_id not in database:
        raise HTTPException(
            status_code=404,
            detail=f"Item {item_id} not found"
        )
    return database[item_id]

@app.post("/items")
async def create_item(item: Item):
    if item.name in [i.name for i in database.values()]:
        raise HTTPException(
            status_code=400,
            detail="Item already exists"
        )
    return item
```

**带自定义头的异常：**

```python
raise HTTPException(
    status_code=401,
    detail="Invalid authentication token",
    headers={"WWW-Authenticate": "Bearer"}
)
```

**全局异常处理器：**

```python
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

app = FastAPI()

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": exc.detail,
            "status_code": exc.status_code
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error",
            "detail": str(exc) if app.debug else None
        }
    )
```

**项目中的异常处理：**

```python
# rag-qa-system/app/main.py
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理器 - 捕获所有未处理的异常"""
    logger.error(f"未处理的异常: {str(exc)}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "服务器内部错误",
            "code": 500,
            "error": str(exc) if settings.debug else "Internal Server Error",
        }
    )

# rag-qa-system/app/api/v1/qa.py
@router.post("/ask")
async def ask_question(request: QAAskRequest, db: Session = Depends(get_db)):
    try:
        result = await qa_service.ask(question=request.question, db=db)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"问答处理失败: {e}")
        raise HTTPException(status_code=500, detail="问答处理失败")
```

---

### Q25: FastAPI 如何实现统一的响应格式？

**参考答案：**

**定义统一响应模型：**

```python
from pydantic import BaseModel
from typing import Generic, TypeVar, Optional, List

T = TypeVar("T")

class ResponseModel(BaseModel, Generic[T]):
    """统一响应模型"""
    success: bool = True
    message: str = "操作成功"
    data: Optional[T] = None
    code: int = 200
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "获取成功",
                "data": {...},
                "code": 200
            }
        }

class PageResponse(BaseModel, Generic[T]):
    """分页响应模型"""
    items: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int
```

**创建响应工厂函数：**

```python
from fastapi.responses import JSONResponse

def success_response(data=None, message="操作成功", code=200):
    """成功响应"""
    return JSONResponse({
        "success": True,
        "message": message,
        "data": data,
        "code": code
    })

def error_response(message="操作失败", code=400, errors=None):
    """错误响应"""
    return JSONResponse({
        "success": False,
        "message": message,
        "code": code,
        "errors": errors
    }, status_code=code)

# 使用示例
@app.get("/items")
async def list_items():
    return success_response(
        data={"items": [...], "total": 100},
        message="获取列表成功"
    )

@app.post("/items")
async def create_item():
    return success_response(
        data={"id": 1},
        message="创建成功",
        code=201
    )
```

**项目中的统一响应：**

```python
# rag-qa-system/app/schemas/common.py
class SuccessResponse(BaseModel):
    """成功响应"""
    success: bool = True
    message: str = "操作成功"
    data: Optional[dict] = None

class ErrorResponse(BaseModel):
    """错误响应"""
    success: bool = False
    message: str
    error: Optional[str] = None
    code: int = 400

# API 中使用
@router.post("/ask")
async def ask_question(request: QAAskRequest):
    try:
        result = await qa_service.ask(...)
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"success": False, "message": str(e)}
        )
```

---

## 6. 性能与部署

### Q26: 如何优化 FastAPI 应用的性能？

**参考答案：**

**1. 异步 I/O 优化：**

```python
# 使用异步数据库驱动
from sqlalchemy.ext.asyncio import create_async_engine

async_engine = create_async_engine(
    "mysql+aiomysql://user:pass@host/db",
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
)

# 使用异步 Redis 客户端
import redis.asyncio as aioredis
redis = await aioredis.from_url("redis://localhost")
```

**2. 数据库连接池：**

```python
# SQLAlchemy 连接池配置
from sqlalchemy import create_engine

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=5,        # 基础连接数
    max_overflow=10,    # 额外连接数
    pool_pre_ping=True, # 检测连接有效性
    pool_recycle=3600,  # 一小时后回收连接
)
```

**3. 缓存优化：**

```python
# 多级缓存
class CacheManager:
    def __init__(self):
        self.local_cache = {}  # L1: 内存缓存
        self.redis_cache = redis  # L2: Redis 缓存
    
    async def get(self, key):
        # 先查内存
        if key in self.local_cache:
            return self.local_cache[key]
        
        # 再查 Redis
        value = await self.redis_cache.get(key)
        if value:
            self.local_cache[key] = value  # 回填 L1
        return value
```

**4. 响应压缩：**

```python
from fastapi.middleware.gzip import GZipMiddleware

app = FastAPI()
app.add_middleware(GZipMiddleware, minimum_size=1000)
```

**5. 批量处理：**

```python
# 批量向量化
async def batch_encode(texts: list[str], batch_size: int = 32):
    results = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        embeddings = await asyncio.to_thread(
            embedding_model.encode, batch
        )
        results.extend(embeddings)
    return results
```

**6. 数据库查询优化：**

```python
# 使用 selectinload 避免 N+1 查询
from sqlalchemy.orm import selectinload

result = await db.execute(
    select(Document)
    .options(selectinload(Document.chunks))  # 预加载关联数据
    .where(Document.id == doc_id)
)
```

---

### Q27: FastAPI 应用如何部署到生产环境？

**参考答案：**

**Uvicorn 生产部署：**

```bash
# 基础命令
uvicorn app.main:app --host 0.0.0.0 --port 8000

# 生产配置
uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 4 \          # 多工作进程
    --loop uvloop \         # 使用 uvloop 事件循环
    --http httptools \     # 使用 httptools HTTP 解析器
    --log-level info \      # 日志级别
    --access-log           # 启用访问日志
```

**Gunicorn + Uvicorn Workers：**

```bash
# gunicorn.conf.py
workers = 4
worker_class = "uvicorn.workers.UvicornWorker"
bind = "0.0.0.0:8000"
timeout = 120
keepalive = 5

# 启动
gunicorn -c gunicorn.conf.py app.main:app
```

**Docker 部署：**

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用
COPY . .

# 运行
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
    restart: unless-stopped
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
```

**Nginx 反向代理：**

```nginx
server {
    listen 80;
    server_name api.example.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket 支持
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

**项目中的部署配置：**

```python
# rag-qa-system/app/main.py
if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
        workers=1 if settings.debug else 4,
    )
```

---

### Q28: FastAPI 如何处理 WebSocket 连接？

**参考答案：**

**基本 WebSocket 端点：**

```python
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

app = FastAPI()

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: int):
    await websocket.accept()  # 接受连接
    
    try:
        while True:
            # 接收消息
            data = await websocket.receive_text()
            
            # 处理消息
            response = f"Echo: {data}"
            
            # 发送消息
            await websocket.send_text(response)
            
    except WebSocketDisconnect:
        print(f"Client {client_id} disconnected")
```

**广播消息：**

```python
from typing import List

class ConnectionManager:
    """WebSocket 连接管理器"""
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
    
    async def broadcast(self, message: str):
        """广播消息给所有连接的客户端"""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                disconnected.append(connection)
        
        # 清理断开的连接
        for conn in disconnected:
            self.disconnect(conn)

manager = ConnectionManager()

@app.websocket("/ws/broadcast")
async def broadcast_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.broadcast(data)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
```

**带认证的 WebSocket：**

```python
@app.websocket("/ws/chat/{room_id}")
async def chat_endpoint(
    websocket: WebSocket,
    room_id: str,
    token: str = Query(...)
):
    # 验证 token
    user = verify_token(token)
    if not user:
        await websocket.close(code=4001)
        return
    
    await websocket.accept()
    
    try:
        while True:
            data = await websocket.receive_json()
            # 处理聊天消息
            await broadcast_to_room(room_id, {
                "user": user.id,
                "message": data["message"]
            })
    except WebSocketDisconnect:
        await leave_room(room_id, user.id)
```

---

### Q29: FastAPI 如何实现认证和授权？

**参考答案：**

**JWT 认证：**

```python
from datetime import datetime, timedelta
from jose import jwt
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"

def create_access_token(data: dict, expires_delta: timedelta = None):
    """创建 JWT Token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=30))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return pwd_context.verify(plain_password, hashed_password)

def hash_password(password: str) -> str:
    """哈希密码"""
    return pwd_context.hash(password)

# 认证依赖
def get_current_user(token: str = Depends(oauth2_scheme)):
    """获取当前用户"""
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    return {"user_id": user_id}

# 受保护的路由
@app.get("/protected")
async def protected_route(user: dict = Depends(get_current_user)):
    return {"user_id": user["user_id"], "message": "Protected data"}
```

**OAuth2 密码流：**

```python
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """登录获取 Token"""
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/me")
async def read_users_me(current_user = Depends(get_current_user)):
    return current_user
```

**项目中的认证：**

```python
# rag-qa-system/app/api/v1/auth.py
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """验证 JWT Token"""
    token = credentials.credentials
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm]
        )
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="无效的认证信息")
        return {"user_id": user_id}
    except JWTError:
        raise HTTPException(status_code=401, detail="认证失败")
```

---

### Q30: FastAPI 如何配置日志系统？

**参考答案：**

**使用 loguru：**

```python
# rag-qa-system/app/core/logger.py
from loguru import logger
import sys

def setup_logger():
    """配置日志系统"""
    # 移除默认处理器
    logger.remove()
    
    # 控制台输出
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="INFO",
        colorize=True,
    )
    
    # 文件输出
    logger.add(
        "logs/app_{time:YYYY-MM-DD}.log",
        rotation="00:00",  # 每天轮转
        retention="30 days",  # 保留 30 天
        compression="zip",  # 压缩旧日志
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    )
    
    return logger

logger = setup_logger()

# 使用
logger.info("应用启动")
logger.warning("警告信息")
logger.error("错误信息")
logger.debug("调试信息")
```

**结构化日志：**

```python
# 带额外上下文信息的日志
logger.info(
    "问答请求处理",
    extra={
        "question": question[:50],
        "user_id": user_id,
        "session_id": session_id
    }
)

# 带异常的日志
try:
    risky_operation()
except Exception as e:
    logger.exception(f"操作失败: {e}")  # 自动包含堆栈跟踪
```

**问答日志追踪：**

```python
# rag-qa-system/app/core/logger.py
class QALogger:
    """问答专用日志器"""
    
    def log_query(
        self,
        question: str,
        answer_length: int,
        sources_count: int,
        cache_hit: bool,
        status: str,
        elapsed_ms: float
    ):
        """记录问答日志"""
        logger.info(
            "问答请求",
            extra={
                "event": "qa_query",
                "question_preview": question[:100],
                "answer_length": answer_length,
                "sources_count": sources_count,
                "cache_hit": cache_hit,
                "status": status,
                "elapsed_ms": round(elapsed_ms, 2)
            }
        )

qa_logger = QALogger()
```

---

## 附录：面试重点总结

### 核心知识点

| 类别 | 重点内容 |
|------|----------|
| **异步编程** | async/await、协程、事件循环、并发执行 |
| **依赖注入** | Depends、依赖链、类依赖 |
| **路由系统** | 路径参数、查询参数、APIRouter、版本控制 |
| **请求响应** | Request Body、Response Model、文件上传、Header/Cookie |
| **中间件** | CORS、日志、压缩、自定义中间件 |
| **异常处理** | HTTPException、全局处理器、统一响应格式 |
| **性能优化** | 连接池、缓存、批量处理、异步驱动 |
| **部署运维** | Uvicorn、Docker、Nginx、生产配置 |

### 常见追问

1. **FastAPI 的性能为什么高？**
   - 基于 Starlette 异步框架
   - 使用 uvloop 事件循环
   - 使用 httptools 高效 HTTP 解析
   - 原生异步 I/O 支持

2. **FastAPI 和 Flask 的选择？**
   - 需要自动文档和类型验证 → FastAPI
   - 简单微服务、快速原型 → Flask
   - 大型全栈应用 → Django

3. **如何处理大文件上传？**
   - 使用 aiofiles 异步写入
   - 流式处理避免内存溢出
   - 配置请求体大小限制

---

*本文档共 30 道面试题，覆盖 FastAPI + Uvicorn 的核心技术点*
