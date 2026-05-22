# 后端技术面试题

## 目录

1. [FastAPI 框架](#1-fastapi-框架)
2. [异步编程](#2-异步编程)
3. [SQLAlchemy ORM](#3-sqlalchemy-orm)
4. [数据库连接池](#4-数据库连接池)
5. [Pydantic 数据验证](#5-pydantic-数据验证)
6. [日志系统](#6-日志系统)
7. [中间件与异常处理](#7-中间件与异常处理)

---

## 1. FastAPI 框架

### 问题 1：FastAPI 是如何实现高性能的？

**答案：**

FastAPI 的高性能主要来自以下几个方面：

**1. 基于 Starlette 框架**

FastAPI 构建在 Starlette 之上，Starlette 是一个轻量级的 ASGI 框架。ASGI（Asynchronous Server Gateway Interface）是 Python 的异步 Web 标准，允许处理并发请求。

**2. 异步处理**

FastAPI 支持原生异步函数定义，使用 `async def` 定义异步路由处理器，配合 Uvicorn 或 Gunicorn 的异步 workers，可以同时处理大量并发请求。

```python
# 同步处理器
@app.get("/sync")
def sync_endpoint():
    return {"message": "同步响应"}

# 异步处理器
@app.get("/async")
async def async_endpoint():
    # 在异步函数中可以并发执行多个 I/O 操作
    result = await some_async_operation()
    return {"message": result}
```

**3. 自动生成 OpenAPI 文档**

FastAPI 自动从类型提示生成 OpenAPI/Swagger 文档，减少了手写文档的工作量，同时也提供了交互式 API 测试界面。

**为什么使用：**
- 减少样板代码，提高开发效率
- 类型安全，减少运行时错误
- 自动生成文档，便于 API 维护和测试

---

### 问题 2：FastAPI 中的依赖注入是如何工作的？

**答案：**

FastAPI 的依赖注入系统允许在路由处理器中声明依赖，实现关注点分离和代码复用。

**基本用法：**

```python
from fastapi import Depends, FastAPI, HTTPException
from typing import Optional

# 定义依赖
def verify_api_key(api_key: str = Header(None)):
    if api_key != "secret-key":
        raise HTTPException(status_code=403, detail="无效的 API Key")
    return api_key

# 在路由中使用
@app.get("/items/{item_id}")
def read_item(item_id: str, api_key: str = Depends(verify_api_key)):
    return {"item_id": item_id, "api_key": api_key}

# 带参数的依赖
def pagination(skip: int = 0, limit: int = 10):
    return {"skip": skip, "limit": limit}

@app.get("/items")
def list_items(params: dict = Depends(pagination)):
    return {"params": params}
```

**依赖注入的工作原理：**

1. FastAPI 在请求到达时，构建依赖图的执行顺序
2. 每个 `Depends()` 创建一个依赖项
3. 依赖项的返回值被注入到处理器函数中
4. 依赖可以是同步或异步函数
5. 支持依赖覆盖（用于测试）

**项目中应用：**

在 `app/api/deps.py` 中定义了认证依赖：

```python
async def get_current_user(
    token: str = Depends(get_token_from_header),
    db: Session = Depends(get_db)
) -> User:
    # 验证 token 并返回用户
    ...
```

**为什么使用：**
- 实现关注点分离
- 方便单元测试（可以 mock 依赖）
- 代码复用，减少重复逻辑

---

## 2. 异步编程

### 问题 3：Python 中的 async/await 是如何工作的？

**答案：**

**1. 事件循环（Event Loop）**

事件循环是异步编程的核心，它负责：
- 调度协程的执行
- 处理 I/O 事件
- 管理定时器

```python
import asyncio

# 创建事件循环
async def main():
    print("Hello")
    await asyncio.sleep(1)  # 暂停 1 秒，但不会阻塞其他任务
    print("World")

# 运行
asyncio.run(main())
```

**2. 协程（Coroutine）**

协程是用 `async def` 定义的特殊函数，调用时不会立即执行，而是返回一个协程对象。

```python
async def fetch_data():
    # 这是一个协程函数
    return await some_io_operation()
```

**3. Task 和 Future**

- `Task` 是协程的包装器，用于调度协程的执行
- `Future` 是一个特殊的低层级对象，表示异步操作的最终结果

```python
async def main():
    # 创建 Task，立即开始执行
    task1 = asyncio.create_task(fetch_data("url1"))
    task2 = asyncio.create_task(fetch_data("url2"))
    
    # 并发等待两个任务完成
    result1 = await task1
    result2 = await task2
    
    return result1, result2
```

**4. 异步上下文管理器**

```python
async with asyncio.timeout(10):  # 10 秒超时
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json()
```

**为什么使用 async/await：**
- 在 I/O 密集型场景下提高吞吐量
- 避免线程切换开销
- 代码逻辑清晰，易于维护

---

### 问题 4：FastAPI 中同步和异步函数的区别是什么？

**答案：**

**区别：**

| 特性 | 同步函数 | 异步函数 |
|------|----------|----------|
| 定义方式 | `def func()` | `async def func()` |
| 调用方式 | 直接调用 | `await func()` |
| 执行方式 | 阻塞当前线程 | 暂停执行，等待 I/O |
| 并发能力 | 单线程一次处理一个请求 | 单线程可处理多个请求 |

**使用场景：**

```python
# 使用同步函数的场景（CPU 密集型操作）
@app.get("/compute")
def compute_heavy_task():
    # CPU 密集型计算
    result = heavy_computation()  # 这会阻塞整个事件循环
    return {"result": result}

# 使用异步函数的场景（I/O 密集型操作）
@app.get("/fetch")
async def fetch_remote_data():
    # I/O 密集型操作
    async with httpx.AsyncClient() as client:
        response = await client.get("https://api.example.com/data")
    return response.json()

# 混合使用：在同步函数中运行异步代码
@app.get("/mixed")
def mixed_endpoint():
    result = asyncio.run(fetch_remote_data())
    return {"result": result}
```

**项目中应用：**

在 `qa_service.py` 中使用了异步路由：

```python
@router.post("/ask/stream")
async def ask_question_stream(
    request: QARequest,
    db: Session = Depends(get_db)
):
    async def generate():
        async for chunk in qa_service.ask_stream(...):
            yield chunk
    
    return StreamingResponse(generate(), media_type="text/event-stream")
```

---

## 3. SQLAlchemy ORM

### 问题 5：SQLAlchemy 中 Session 和 Engine 的区别是什么？

**答案：**

**1. Engine（引擎）**

Engine 是与数据库的连接管理器，负责：
- 建立数据库连接
- 管理连接池
- 执行原生 SQL 语句

```python
from sqlalchemy import create_engine

# 创建引擎
engine = create_engine(
    "mysql+pymysql://user:pass@localhost:3306/dbname",
    pool_size=10,           # 连接池大小
    max_overflow=20,        # 额外连接数
    pool_recycle=3600,      # 连接回收时间（秒）
    echo=False              # 是否打印 SQL
)
```

**2. Session（会话）**

Session 是 ORM 的工作单元，负责：
- 管理事务
- 追踪对象的变更
- 提供 CRUD 操作接口

```python
from sqlalchemy.orm import sessionmaker

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 使用会话
def get_user(db, user_id):
    user = db.query(User).filter(User.id == user_id).first()
    return user

def create_user(db, user_data):
    user = User(**user_data)
    db.add(user)
    db.commit()           # 提交事务
    db.refresh(user)      # 刷新对象（获取数据库生成的值）
    return user
```

**生命周期管理：**

```python
# 正确的用法：在请求结束时关闭 Session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# FastAPI 依赖注入
@app.get("/users/{user_id}")
def read_user(user_id: int, db: Session = Depends(get_db)):
    return db.query(User).get(user_id)
```

**项目中应用：**

```python
from app.core.database import SessionLocal, get_db

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

**为什么分开设计：**
- Engine 是进程级别，Session 是请求级别
- 一个 Engine 可以创建多个 Session
- 便于连接池管理和事务控制

---

### 问题 6：SQLAlchemy 中的 query() 和 select() 有什么区别？

**答案：**

**1. ORM Query API（传统方式）**

```python
from sqlalchemy.orm import Query

# 查询所有
users = db.query(User).all()

# 条件查询
user = db.query(User).filter(User.id == 1).first()

# 多条件
users = db.query(User).filter(
    User.age > 18,
    User.status == "active"
).all()

# 排序和分页
users = db.query(User).order_by(User.created_at.desc()).limit(10).offset(0).all()

# 聚合查询
from sqlalchemy import func
count = db.query(func.count(User.id)).scalar()
```

**2. Select API（2.0+ 推荐方式）**

```python
from sqlalchemy import select

# 查询所有
stmt = select(User)
users = db.execute(stmt).scalars().all()

# 条件查询
stmt = select(User).where(User.id == 1)
user = db.execute(stmt).scalar_one_or_none()

# 多条件
stmt = select(User).where(
    User.age > 18,
    User.status == "active"
)

# 排序和分页
stmt = select(User).order_by(User.created_at.desc()).limit(10).offset(0)

# 聚合查询
from sqlalchemy import func, select
stmt = select(func.count(User.id))
count = db.execute(stmt).scalar()
```

**选择建议：**

| 场景 | 推荐方式 |
|------|----------|
| 简单 CRUD | query() 更简洁 |
| 复杂查询 | select() 更灵活 |
| 新项目 | select() 优先 |
| 性能敏感 | select() 可直接返回原始结果 |

---

## 4. 数据库连接池

### 问题 7：数据库连接池的作用是什么？如何配置？

**答案：**

**作用：**

1. **减少连接开销**：避免每次请求都创建新连接
2. **控制并发**：限制最大连接数，防止数据库过载
3. **复用连接**：连接可以被多个请求复用

**连接池工作原理：**

```
请求 1 ──┐
请求 2 ──┼──> 连接池 ──> 数据库
请求 3 ──┘   (固定连接数)
```

**SQLAlchemy 连接池配置：**

```python
from sqlalchemy import create_engine

engine = create_engine(
    "mysql+pymysql://user:pass@localhost:3306/dbname",
    
    # 连接池大小：常驻连接数
    pool_size=10,
    
    # 最大溢出：超过 pool_size 的最大连接数
    max_overflow=20,
    
    # 连接回收时间：超过此时长的连接会被关闭重建
    pool_recycle=3600,
    
    # 连接预热：启动时创建指定数量的连接
    pool_pre_ping=True,  # 每次使用前检查连接是否有效
    
    # 超时时间
    pool_timeout=30
)
```

**参数说明：**

| 参数 | 说明 | 建议值 |
|------|------|--------|
| pool_size | 最小连接数 | CPU 核心数 × 2 |
| max_overflow | 最大额外连接 | pool_size 的 2 倍 |
| pool_recycle | 连接生命周期 | 1 小时 |
| pool_timeout | 获取连接超时 | 30 秒 |

**项目中应用：**

```python
# app/config.py
mysql_pool_size: int = Field(default=10, description="连接池大小")
mysql_max_overflow: int = Field(default=20, description="连接池最大溢出")
```

**为什么使用连接池：**
- 提高性能：避免频繁创建/销毁连接的开销
- 资源控制：防止连接数无限增长
- 稳定性：数据库重启时自动重连

---

## 5. Pydantic 数据验证

### 问题 8：Pydantic v2 中的 Field 和 BaseModel 是如何工作的？

**答案：**

**1. BaseModel（基础模型）**

```python
from pydantic import BaseModel

class User(BaseModel):
    id: int
    name: str
    email: str
    age: Optional[int] = None

# 创建实例
user = User(id=1, name="张三", email="zhang@example.com")
```

**2. Field（字段定义）**

```python
from pydantic import BaseModel, Field

class User(BaseModel):
    id: int = Field(gt=0, description="用户ID，必须大于0")
    name: str = Field(min_length=2, max_length=50, description="用户名")
    email: str = Field(regex=r"^[a-zA-Z0-9_.+-]+@[a-z]+$", description="邮箱")
    age: Optional[int] = Field(default=None, ge=0, le=150, description="年龄")
    password: str = Field(min_length=8, description="密码")
```

**常用验证器：**

| 验证器 | 作用 | 示例 |
|--------|------|------|
| gt | 大于 | `gt=0` |
| ge | 大于等于 | `ge=18` |
| lt | 小于 | `lt=100` |
| le | 小于等于 | `le=100` |
| min_length | 最小长度 | `min_length=2` |
| max_length | 最大长度 | `max_length=50` |
| regex | 正则匹配 | `regex=r"^\w+$"` |

**3. Settings 配置模型**

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    mysql_host: str = "localhost"
    mysql_port: int = 3306
    debug: bool = False
    
    class Config:
        env_file = ".env"  # 从 .env 加载配置
        env_file_encoding = "utf-8"

settings = Settings()
```

**项目中应用：**

```python
# app/schemas/qa.py
class QARequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=1000, description="问题")
    top_k: int = Field(default=5, ge=1, le=20, description="检索数量")
    temperature: float = Field(default=0.3, ge=0, le=2, description="生成温度")
    search_mode: str = Field(default="local", description="搜索模式")
```

**为什么使用 Pydantic：**
- 自动数据验证和转换
- 类型提示支持
- 自动生成 OpenAPI schema
- 环境变量绑定

---

### 问题 9：Pydantic v2 中的模型配置类有什么变化？

**答案：**

Pydantic v2 对模型配置进行了重大改进，从 `class Config` 改为 `model_config`。

**Pydantic v1 方式（已废弃）：**

```python
class User(BaseModel):
    name: str
    email: str
    
    class Config:
        populate_by_name = True
        validate_assignment = True
```

**Pydantic v2 方式：**

```python
from pydantic import BaseModel, ConfigDict

class User(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,    # 允许通过别名或字段名填充
        validate_assignment=True, # 赋值时验证
        str_strip_whitespace=True, # 字符串自动去除首尾空格
        from_attributes=True      # 从 ORM 模型创建
    )
    
    name: str
    email: str
```

**常用配置项：**

| 配置项 | 说明 |
|--------|------|
| `populate_by_name` | 允许使用字段别名填充 |
| `validate_assignment` | 赋值时验证 |
| `str_strip_whitespace` | 字符串自动去除空格 |
| `from_attributes` | 从 ORM 对象创建模型 |
| `arbitrary_types_allowed` | 允许任意类型 |

**运行时配置更新：**

```python
class User(BaseModel):
    name: str
    
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{"name": "张三"}]
        }
    )
```

---

## 6. 日志系统

### 问题 10：项目中使用的 Loguru 相比标准 logging 有什么优势？

**答案：**

**Loguru 的优势：**

**1. 零配置开箱即用**

```python
from loguru import logger

logger.info("这是一条信息日志")
logger.warning("这是一条警告")
logger.error("这是一条错误")
```

**2. 自动格式化**

默认输出包含时间戳、级别、模块名、行号等信息：
```
2026-05-18 10:30:15 | INFO    | app.services.qa:ask:42 - 这是一条信息日志
```

**3. 彩色输出**

终端自动彩色输出，不同级别不同颜色。

**4. 简单的文件日志配置**

```python
from loguru import logger

# 添加文件日志
logger.add(
    "app.log",
    rotation="500 MB",      # 文件大小轮转
    retention="10 days",    # 保留天数
    compression="zip",      # 压缩格式
    level="INFO",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} - {message}"
)

# 同时输出到多个目标
logger.add(sys.stderr, level="DEBUG")  # 控制台
logger.add("file.log", level="INFO")   # 文件
```

**5. 异常追踪**

```python
try:
    risky_operation()
except Exception:
    logger.exception("操作失败")  # 自动记录完整堆栈
```

**项目中应用：**

```python
# app/core/logger.py
from loguru import logger

# 配置日志
logger.add(
    settings.log_file_path,
    rotation="00:00",           # 每天轮转
    retention=settings.log_file_backup_count,
    level=settings.log_level,
    format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}"
)
```

**为什么选择 Loguru：**
- 配置简单，代码量少
- 输出美观，便于调试
- 异常处理强大
- 线程安全

---

## 7. 中间件与异常处理

### 问题 11：FastAPI 中间件是如何工作的？

**答案：**

**中间件的执行顺序：**

```
请求 → 中间件1 → 中间件2 → ... → 路由处理 → ... → 中间件2 → 中间件1 → 响应
```

**自定义中间件示例：**

```python
from fastapi import FastAPI, Request
import time

app = FastAPI()

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    
    # 处理请求
    response = await call_next(request)
    
    # 添加自定义响应头
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    
    return response
```

**项目中应用：**

```python
# 请求日志中间件
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    # 获取请求信息
    method = request.method
    path = request.url.path
    
    try:
        response = await call_next(request)
    except Exception as e:
        logger.error(f"请求处理异常: {method} {path} - {str(e)}")
        raise
    
    # 记录日志
    elapsed = (time.time() - start_time) * 1000
    logger.info(f"{method} {path} - {response.status_code} - {elapsed:.2f}ms")
    
    return response
```

**CORS 中间件配置：**

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # 允许的来源
    allow_credentials=True,                     # 允许凭据
    allow_methods=["GET", "POST"],            # 允许的方法
    allow_headers=["*"],                      # 允许的头
)
```

**注意事项：**
- 中间件按照添加顺序执行
- 异常中间件在最后执行
- 避免在中间件中执行耗时操作

---

### 问题 12：FastAPI 中如何实现全局异常处理？

**答案：**

**1. 全局异常处理器**

```python
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

app = FastAPI()

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"未处理的异常: {str(exc)}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "服务器内部错误",
            "error": str(exc) if settings.debug else "Internal Server Error"
        }
    )
```

**2. 自定义异常类型**

```python
class BusinessException(Exception):
    def __init__(self, code: int, message: str):
        self.code = code
        self.message = message

class NotFoundException(BusinessException):
    def __init__(self, resource: str):
        super().__init__(code=404, message=f"{resource} 不存在")

@app.exception_handler(BusinessException)
async def business_exception_handler(request: Request, exc: BusinessException):
    return JSONResponse(
        status_code=exc.code,
        content={"success": False, "message": exc.message}
    )
```

**3. HTTPException**

```python
from fastapi import HTTPException, status

@app.get("/items/{item_id}")
def read_item(item_id: int):
    item = get_item(item_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="项目不存在"
        )
    return item
```

**项目中应用：**

```python
# app/main.py
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"未处理的异常: {str(exc)}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "服务器内部错误",
            "code": 500,
            "error": str(exc) if settings.debug else "Internal Server Error"
        }
    )
```

**最佳实践：**
- 为不同类型的异常创建不同的处理器
- 在生产环境中隐藏详细错误信息
- 记录完整日志便于排查
- 返回统一的错误响应格式

---

## 版本信息

- 文档版本: 1.0.0
- 更新日期: 2026-05-18
