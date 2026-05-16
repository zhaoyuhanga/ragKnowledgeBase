# MySQL + SQLAlchemy 面试题集

> 本文档包含 30 道 MySQL 数据库与 SQLAlchemy ORM 相关的高频面试题，涵盖数据库设计、ORM 映射、查询优化、事务管理等核心概念。所有答案均为中文，代码附有详细中文解释。

---

## 目录

1. [MySQL 基础](#1-mysql-基础)
2. [SQLAlchemy ORM](#2-sqlalchemy-orm)
3. [数据库操作](#3-数据库操作)
4. [查询与过滤](#4-查询与过滤)
5. [事务与并发](#5-事务与并发)
6. [性能优化](#6-性能优化)
7. [索引与约束](#7-索引与约束)
8. [项目实践](#8-项目实践)

---

## 1. MySQL 基础

### Q1: MySQL 的存储引擎有哪些？InnoDB 和 MyISAM 有什么区别？

**参考答案：**

**MySQL 存储引擎对比：**

| 特性 | InnoDB | MyISAM |
|------|--------|--------|
| **事务支持** | 支持 | 不支持 |
| **外键约束** | 支持 | 不支持 |
| **行级锁** | 支持 | 不支持（表级锁） |
| **并发性能** | 高 | 低 |
| **崩溃恢复** | 自动恢复 | 需要修复 |
| **索引** | B+Tree + Hash | B+Tree |
| **表空间** | 共享 + 独立 | 独立 |
| **全文索引** | 5.6+ 支持 | 原生支持 |

**InnoDB 核心特性：**

```sql
-- InnoDB 特点：
-- 1. 支持事务（ACID）
-- 2. 行级锁，支持高并发
-- 3. MVCC（多版本并发控制）
-- 4. 自动崩溃恢复
-- 5. 支持外键约束

-- 查看存储引擎
SHOW ENGINES;

-- 查看表引擎
SHOW TABLE STATUS FROM database_name WHERE Name = 'documents';

-- 创建 InnoDB 表
CREATE TABLE documents (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    filename VARCHAR(255) NOT NULL,
    status INT DEFAULT 0
) ENGINE=InnoDB;
```

**InnoDB vs MyISAM 选择：**

| 场景 | 推荐引擎 |
|------|----------|
| 事务系统、订单处理 | InnoDB |
| 日志系统、审计表 | InnoDB |
| 读多写少、全文搜索 | MyISAM |
| 高并发读写 | InnoDB |
| 临时表、缓存 | Memory |

**项目中的选择：**
项目使用 InnoDB，因为需要事务支持和外键约束。

---

### Q2: 什么是事务？MySQL 的事务特性是什么？

**参考答案：**

**事务的 ACID 特性：**

| 特性 | 说明 | 实现机制 |
|------|------|----------|
| **Atomic（原子性）** | 事务是最小执行单位 | Undo Log |
| **Consistency（一致性）** | 事务前后数据状态一致 | 约束、触发器 |
| **Isolation（隔离性）** | 并发事务互不干扰 | 锁、MVCC |
| **Durability（持久性）** | 事务提交后永久保存 | Redo Log |

**事务语法：**

```sql
-- 开启事务
START TRANSACTION;
-- 或
BEGIN;

-- 执行操作
INSERT INTO documents (filename, status) VALUES ('test.pdf', 0);
UPDATE documents SET status = 1 WHERE id = 1;

-- 提交事务
COMMIT;

-- 回滚事务
ROLLBACK;

-- 设置保存点
SAVEPOINT savepoint1;
ROLLBACK TO savepoint1;
```

**Python/SQLAlchemy 中的事务：**

```python
from sqlalchemy.orm import Session

# 方式1：自动提交
db = Session(bind=engine)
db.add(document)
db.commit()  # 自动提交

# 方式2：手动控制
db.begin()  # 开启事务
try:
    db.add(doc1)
    db.add(doc2)
    db.commit()
except Exception as e:
    db.rollback()  # 回滚
    raise

# 方式3：上下文管理器
with db.begin():
    db.add(doc1)
    db.add(doc2)
    # 自动提交或回滚
```

**事务隔离级别：**

```sql
-- 查看当前隔离级别
SELECT @@transaction_isolation;

-- 设置隔离级别
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;

-- 隔离级别对比
| 级别 | 脏读 | 不可重复读 | 幻读 |
|------|------|-----------|------|
| READ UNCOMMITTED | 可能 | 可能 | 可能 |
| READ COMMITTED | 不可能 | 可能 | 可能 |
| REPEATABLE READ | 不可能 | 不可能 | 可能 |
| SERIALIZABLE | 不可能 | 不可能 | 不可能 |

-- InnoDB 默认：REPEATABLE READ
-- MySQL 默认：REPEATABLE READ
```

---

### Q3: MySQL 的锁机制是什么？什么是行锁和表锁？

**参考答案：**

**锁类型分类：**

| 分类维度 | 锁类型 | 说明 |
|----------|--------|------|
| **粒度** | 行锁 | 锁定单行数据 |
| | 表锁 | 锁定整张表 |
| **模式** | 共享锁 (S) | 允许多个读操作 |
| | 排他锁 (X) | 独占写操作 |
| **算法** | 记录锁 | 锁定索引记录 |
| | 间隙锁 | 锁定索引间隙 |
| | Next-Key | 记录锁 + 间隙锁 |

**行锁示例：**

```sql
-- 锁定 id=1 的行（排他锁）
SELECT * FROM documents WHERE id = 1 FOR UPDATE;

-- 锁定满足条件的行（InnoDB 会锁定扫描到的所有行）
SELECT * FROM documents WHERE status = 0 FOR UPDATE;

-- 共享锁（其他事务可以读，但不能写）
SELECT * FROM documents WHERE id = 1 LOCK IN SHARE MODE;
```

**间隙锁（Gap Lock）：**

```sql
-- 锁定 id 在 1-10 之间的间隙
SELECT * FROM documents WHERE id BETWEEN 1 AND 10 FOR UPDATE;
-- 锁定：(1, 10) 之间的所有间隙
-- 防止其他事务在这个范围内插入新记录

-- 作用：防止幻读（Phantom Read）
```

**表锁示例：**

```sql
-- 锁定整张表
LOCK TABLES documents READ;  -- 共享表锁

LOCK TABLES documents WRITE;  -- 排他表锁

-- 解锁
UNLOCK TABLES;
```

**InnoDB 行锁实现：**

```sql
-- InnoDB 通过索引实现行锁
-- 如果查询没有使用索引，会升级为表锁

-- 示例：没有索引会导致表锁
SELECT * FROM documents WHERE filename = 'test.pdf' FOR UPDATE;
-- 可能锁定整张表

-- 使用索引则只锁定匹配的行
ALTER TABLE documents ADD INDEX idx_filename(filename);
SELECT * FROM documents WHERE filename = 'test.pdf' FOR UPDATE;
-- 只锁定匹配的行
```

**死锁及处理：**

```sql
-- 查看死锁日志
SHOW ENGINE INNODB STATUS;

-- 解决死锁：
-- 1. InnoDB 自动检测并回滚小事务
-- 2. 按固定顺序访问表
-- 3. 避免长事务
-- 4. 减少锁持有时间
```

---

### Q4: 什么是 MVCC？它是如何工作的？

**参考答案：**

**MVCC 概念：**
MVCC（Multi-Version Concurrency Control，多版本并发控制）是一种并发控制机制，通过保存数据的多个版本来实现读写并发。

**核心思想：**

```
时间线：
T1 ────── T2 ────── T3 ────── T4
  │         │         │         │
  │    [事务A开始]   │         │
  │    [读取数据V1]  │         │
  │                  │    [事务A提交]
  │                  │         │
  │         [事务B开始]         │
  │         [修改数据]          │
  │         [写入V2]           │
  │                  │    [事务B提交]
  │                  │         │

结果：事务A看到的是V1版本（快照）
      事务B修改后是V2版本
```

**InnoDB MVCC 实现：**

```sql
-- InnoDB 为每行数据添加两个隐藏列：
-- 1. DB_TRX_ID：最后修改的事务ID
-- 2. DB_ROLL_PTR：指向 undo log 的指针

-- 查看隐藏列（内部实现）
-- SELECT id, filename, DB_TRX_ID, DB_ROLL_PTR FROM documents;
```

**Read View（读视图）：**

```sql
-- Read View 包含：
-- 1. active_txids：活跃事务ID列表
-- 2. min_txid：最小活跃事务ID
-- 3. max_txid：下一个事务ID
-- 4. creator_txid：当前事务ID

-- 读取规则：
-- 1. 如果行的 txid < min_txid：已提交，可读
-- 2. 如果行的 txid >= max_txid：本事务开始后创建，不可读
-- 3. 如果 txid in active_txids：可能未提交，不可读，需要根据 undo log 找历史版本
```

**不同隔离级别的行为：**

```sql
-- READ COMMITTED：每次读取都生成新的 Read View
-- 可能出现不可重复读

-- REPEATABLE READ（InnoDB默认）：事务开始时生成 Read View
-- 整个事务期间使用同一个 Read View
-- InnoDB 使用 MVCC + Gap Lock 防止幻读

-- SERIALIZABLE：
-- MVCC 退化为锁机制
-- 读取时加共享锁
```

---

### Q5: MySQL 的日志类型有哪些？Redo Log 和 Binlog 有什么区别？

**参考答案：**

**MySQL 日志类型：**

| 日志类型 | 作用 | 写入时机 | 内容 |
|----------|------|----------|------|
| **Binlog** | 主从复制、数据恢复 | 事务提交后 | 数据变更（逻辑） |
| **Redo Log** | 崩溃恢复、持久性 | 事务执行中 | 数据变更（物理） |
| **Undo Log** | MVCC、回滚 | 事务执行中 | 修改前的数据 |
| **Error Log** | 错误记录 | 发生错误时 | 错误信息 |
| **Slow Query Log** | 慢查询分析 | 查询执行后 | 慢查询SQL |

**Binlog vs Redo Log 对比：**

| 特性 | Binlog | Redo Log |
|------|--------|-----------|
| **归属** | MySQL Server | InnoDB 存储引擎 |
| **内容** | 逻辑日志（SQL语句） | 物理日志（页变更） |
| **写入时机** | 事务提交后 | 事务执行中 |
| **写入方式** | 顺序写 | 循环写 |
| **用途** | 主从复制、数据恢复 | 崩溃恢复 |
| **格式** | STATEMENT/ROW/MIXED | 物理页 |
| **删除** | 手动删除或 expire_logs_days | 循环覆盖 |

**Redo Log 作用：**

```sql
-- Redo Log 文件配置
-- innodb_log_files_in_group: 2  (日志组文件数)
-- innodb_log_file_size: 48MB   (日志文件大小)

-- 查看 Redo Log 状态
SHOW VARIABLES LIKE 'innodb%log%';

-- Redo Log 工作流程：
-- 1. 事务修改数据页
-- 2. 在 Redo Log Buffer 中记录变更
-- 3. 事务提交时，将 Redo Log 写入磁盘
-- 4. 崩溃恢复时，根据 Redo Log 重做变更
```

**Binlog 作用：**

```sql
-- 开启 Binlog
-- server-id = 1
-- log_bin = /var/log/mysql/mysql-bin
-- binlog_format = ROW

-- 查看 Binlog
SHOW BINARY LOGS;
SHOW BINLOG EVENTS IN 'mysql-bin.000001';

-- 查看当前 Binlog 位置
SHOW MASTER STATUS;

-- 数据恢复
-- mysqlbinlog mysql-bin.000001 --start-position=100 --stop-position=500 | mysql
```

---

## 2. SQLAlchemy ORM

### Q6: SQLAlchemy 是什么？ORM 的工作原理是什么？

**参考答案：**

**SQLAlchemy 简介：**
SQLAlchemy 是 Python 生态中最流行的 ORM（Object-Relational Mapping）框架，提供数据库操作的完整抽象层。

**ORM 工作原理：**

```
┌─────────────────────────────────────────────────────────────┐
│                      Python 代码                            │
│  document = Document(filename="test.pdf", status=0)        │
│  db.add(document)                                          │
│  db.commit()                                               │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼ SQLAlchemy Core
┌─────────────────────────────────────────────────────────────┐
│  SQLAlchemy 将对象操作转换为 SQL 语句                        │
│  INSERT INTO documents (filename, status) VALUES (?, ?)    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼ 数据库执行
┌─────────────────────────────────────────────────────────────┐
│                      MySQL 数据库                           │
│  保存数据到 documents 表                                    │
└─────────────────────────────────────────────────────────────┘
```

**核心组件：**

| 组件 | 说明 |
|------|------|
| **Engine** | 数据库连接管理 |
| **Session** | 事务会话管理 |
| **Model** | 数据模型类定义 |
| **Query** | 查询构建器 |
| **MetaData** | 数据库元数据 |

**基础使用示例：**

```python
from sqlalchemy import create_engine, Column, Integer, String, BigInteger
from sqlalchemy.orm import declarative_base, Session

# 1. 创建基类
Base = declarative_base()

# 2. 定义模型
class Document(Base):
    __tablename__ = "documents"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    filename = Column(String(255), nullable=False)
    status = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.now)

# 3. 创建引擎
engine = create_engine("mysql+pymysql://user:pass@host/db")

# 4. 创建表
Base.metadata.create_all(engine)

# 5. 操作数据
with Session(engine) as session:
    doc = Document(filename="test.pdf", status=0)
    session.add(doc)
    session.commit()
```

---

### Q7: 如何定义 SQLAlchemy 模型？常用的字段类型有哪些？

**参考答案：**

**常用字段类型：**

| Python 类型 | SQLAlchemy 类型 | MySQL 类型 |
|-------------|-----------------|------------|
| int | Integer | INT |
| bigint | BigInteger | BIGINT |
| float | Float/Double | FLOAT/DOUBLE |
| str | String(length) | VARCHAR |
| text | Text | TEXT |
| bool | Boolean | TINYINT(1) |
| datetime | DateTime | DATETIME |
| date | Date | DATE |
| bytes | LargeBinary/BINARY | BLOB |

**完整模型定义：**

```python
from sqlalchemy import (
    Column, Integer, BigInteger, String, Text, 
    DateTime, Boolean, JSON, ForeignKey, Index
)
from sqlalchemy.orm import relationship
from datetime import datetime

class Document(Base):
    __tablename__ = "documents"
    
    # 主键 - 自增 ID
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    
    # 字符串字段 - 可选长度参数
    filename = Column(String(255), nullable=False, comment="文件名")
    file_path = Column(String(512), nullable=False, comment="文件路径")
    
    # 整数字段 - 带默认值
    status = Column(Integer, default=0, nullable=False, comment="处理状态")
    chunk_count = Column(Integer, default=0, comment="分块数量")
    
    # 大数字段 - 用于存储文件大小
    file_size = Column(BigInteger, nullable=False, comment="文件大小")
    
    # 文本字段 - 用于长文本
    error_message = Column(Text, nullable=True, comment="错误信息")
    
    # JSON 字段 - 存储结构化数据
    metadata = Column(JSON, nullable=True, comment="元数据")
    
    # 布尔字段
    is_active = Column(Boolean, default=True, comment="是否启用")
    
    # 时间字段
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 关联关系
    chunks = relationship("DocumentChunk", back_populates="document")
    
    # 索引定义
    __table_args__ = (
        Index("idx_status", "status"),
        Index("idx_created", "created_at"),
        Index("idx_filename_status", "filename", "status"),  # 复合索引
    )
    
    def __repr__(self):
        return f"<Document(id={self.id}, filename='{self.filename}')>"
```

**关系定义：**

```python
class DocumentChunk(Base):
    __tablename__ = "document_chunks"
    
    id = Column(BigInteger, primary_key=True)
    
    # 外键定义
    document_id = Column(
        BigInteger, 
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # 关系定义
    document = relationship("Document", back_populates="chunks")

# 一对多关系
# Document.chunks → List[DocumentChunk]
# DocumentChunk.document → Document
```

---

### Q8: SQLAlchemy 的 Session 是什么？如何管理会话？

**参考答案：**

**Session 概念：**
Session 是 SQLAlchemy 中管理数据库事务的核心对象，提供与数据库的交互接口。

**Session 创建方式：**

```python
from sqlalchemy.orm import sessionmaker

# 方式1：sessionmaker 工厂
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
session = SessionLocal()

try:
    # 数据库操作
    session.add(doc)
    session.commit()
finally:
    session.close()

# 方式2：上下文管理器（推荐）
with SessionLocal() as session:
    session.add(doc)
    session.commit()  # 自动提交
# 自动关闭

# 方式3：scoped_session（线程安全）
from sqlalchemy.orm import scoped_session
session_factory = sessionmaker(bind=engine)
Session = scoped_session(session_factory)

# 使用
Session.add(doc)
Session.commit()
Session.remove()  # 清理
```

**Session 状态管理：**

```python
# Session 的对象状态
# 1. Transient（瞬态）：新创建，未绑定 Session
# 2. Pending（待定）：已添加，未提交
# 3. Persistent（持久）：已提交，与 Session 关联
# 4. Detached（分离）：提交后，Session 已关闭

doc = Document(filename="test.pdf")  # Transient
session.add(doc)                     # Pending
session.flush()                      # Persistent（同步到数据库，未提交）
session.commit()                     # 提交事务
session.close()                      # Detached

# 修改对象
doc.status = 1  # 自动标记为脏
session.commit()  # 提交修改
```

**Session 常用操作：**

```python
session.add(obj)           # 添加对象
session.add_all([obj1, obj2])  # 批量添加
session.delete(obj)         # 删除对象
session.flush()            # 同步到数据库（不提交）
session.commit()           # 提交事务
session.rollback()         # 回滚事务
session.close()            # 关闭会话
session.expunge(obj)       # 从 Session 移除对象
```

---

### Q9: SQLAlchemy 的查询方式有哪些？如何构建复杂查询？

**参考答案：**

**基本查询：**

```python
from sqlalchemy import select

# 查询所有
all_docs = session.query(Document).all()

# 条件查询
doc = session.query(Document).filter(Document.id == 1).first()
docs = session.query(Document).filter(Document.status == 0).all()

# 使用 select 语句
stmt = select(Document).where(Document.status == 0)
result = session.execute(stmt)
docs = result.scalars().all()
```

**过滤条件：**

```python
from sqlalchemy import and_, or_, not_

# 等于
session.query(Document).filter(Document.status == 0)

# 不等于
session.query(Document).filter(Document.status != 0)

# IN 查询
session.query(Document).filter(Document.id.in_([1, 2, 3]))

# LIKE 查询
session.query(Document).filter(Document.filename.like('%.pdf'))

# BETWEEN
session.query(Document).filter(Document.created_at.between(start, end))

# 多个条件
session.query(Document).filter(
    and_(
        Document.status == 0,
        Document.filename.like('%.pdf')
    )
)

# 或条件
session.query(Document).filter(
    or_(
        Document.status == 0,
        Document.status == 1
    )
)
```

**排序和分页：**

```python
# 排序
session.query(Document).order_by(Document.created_at.desc())  # 降序
session.query(Document).order_by(Document.status, Document.id)  # 多字段

# 分页
page = 1
page_size = 20
offset = (page - 1) * page_size

docs = session.query(Document)\
    .order_by(Document.created_at.desc())\
    .offset(offset)\
    .limit(page_size)\
    .all()
```

**聚合查询：**

```python
from sqlalchemy import func

# COUNT
count = session.query(func.count(Document.id)).scalar()

# SUM
total_size = session.query(func.sum(Document.file_size)).scalar()

# AVG
avg_size = session.query(func.avg(Document.file_size)).scalar()

# 分组统计
from sqlalchemy import case
stats = session.query(
    Document.status,
    func.count(Document.id).label('count')
).group_by(Document.status).all()
```

---

### Q10: SQLAlchemy 的关联查询如何使用？

**参考答案：**

**一对一关系：**

```python
# 定义关系
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    profile = relationship("UserProfile", back_populates="user", uselist=False)

class UserProfile(Base):
    __tablename__ = "user_profiles"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    bio = Column(Text)
    user = relationship("User", back_populates="profile")

# 查询
user = session.query(User).filter(User.id == 1).first()
print(user.profile.bio)  # 直接访问关联对象
```

**一对多关系：**

```python
# 定义
class Document(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True)
    chunks = relationship("DocumentChunk", back_populates="document")

class DocumentChunk(Base):
    __tablename__ = "document_chunks"
    id = Column(Integer, primary_key=True)
    document_id = Column(Integer, ForeignKey("documents.id"))
    document = relationship("Document", back_populates="chunks")

# 查询文档的所有块
doc = session.query(Document).filter(Document.id == 1).first()
chunks = doc.chunks  # 自动加载关联的块

# 使用 selectinload 预加载
from sqlalchemy.orm import selectinload

docs = session.query(Document).options(
    selectinload(Document.chunks)  # 预加载，避免 N+1
).all()

for doc in docs:
    print(len(doc.chunks))  # 不再触发额外查询
```

**多对多关系：**

```python
# 定义关联表
document_tags = Table(
    'document_tags',
    Base.metadata,
    Column('document_id', Integer, ForeignKey('documents.id')),
    Column('tag_id', Integer, ForeignKey('tags.id'))
)

class Document(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True)
    tags = relationship("Tag", secondary=document_tags, back_populates="documents")

class Tag(Base):
    __tablename__ = "tags"
    id = Column(Integer, primary_key=True)
    name = Column(String(50))
    documents = relationship("Document", secondary=document_tags, back_populates="tags")

# 查询
doc = session.query(Document).first()
print(doc.tags)  # 关联的标签列表
```

**懒加载 vs 预加载：**

```python
# 懒加载（默认）- 访问时触发查询
doc = session.query(Document).first()
chunks = doc.chunks  # 触发额外查询

# 预加载 - 一次性加载
from sqlalchemy.orm import selectinload, joinedload

# joinedload：使用 JOIN 加载
docs = session.query(Document).options(
    joinedload(Document.chunks)
).all()

# selectinload：分开查询再合并
docs = session.query(Document).options(
    selectinload(Document.chunks)
).all()
```

---

## 3. 数据库操作

### Q11: 如何使用 SQLAlchemy 进行增删改操作？

**参考答案：**

**新增（Create）：**

```python
# 单条插入
doc = Document(filename="test.pdf", file_size=1024, status=0)
session.add(doc)
session.commit()

# 获取自增 ID
print(doc.id)

# 批量插入
docs = [
    Document(filename="doc1.pdf", file_size=1024),
    Document(filename="doc2.pdf", file_size=2048),
    Document(filename="doc3.pdf", file_size=4096),
]
session.add_all(docs)
session.commit()

# 或使用 bulk_save_objects（更高效）
session.bulk_save_objects(docs)
session.commit()
```

**查询（Read）：**

```python
# 根据主键查询
doc = session.get(Document, 1)  # 推荐，更高效

# 条件查询
doc = session.query(Document).filter(Document.id == 1).first()

# 查询所有
all_docs = session.query(Document).all()

# 切片查询
first_10 = session.query(Document).limit(10).all()
```

**更新（Update）：**

```python
# 方式1：查询后修改
doc = session.query(Document).filter(Document.id == 1).first()
doc.status = 1
doc.updated_at = datetime.now()
session.commit()

# 方式2：批量更新
session.query(Document).filter(
    Document.status == 0
).update({"status": 1}, synchronize_session='fetch')

# 方式3：bulk update
from sqlalchemy import update
stmt = update(Document).where(
    Document.status == 0
).values(status=1, updated_at=datetime.now())
session.execute(stmt)
session.commit()
```

**删除（Delete）：**

```python
# 方式1：查询后删除
doc = session.query(Document).filter(Document.id == 1).first()
session.delete(doc)
session.commit()

# 方式2：条件删除
session.query(Document).filter(Document.status == 2).delete()
session.commit()

# 方式3：bulk delete
from sqlalchemy import delete
stmt = delete(Document).where(Document.status == 2)
session.execute(stmt)
session.commit()
```

**项目中的应用：**

```python
# rag-qa-system/app/services/document_service.py

# 新增文档
document = Document(
    filename=filename,
    file_path=file_path,
    file_type=file_type,
    file_size=file_size,
    content_hash=content_hash,
    status=0,
)
db.add(document)
db.commit()
db.refresh(document)  # 获取自增 ID

# 查询文档
documents, total = document_service.get_document_list(
    db, skip=0, limit=20, status=None
)

# 更新状态
document.status = 1
document.chunk_count = len(chunks)
db.commit()

# 删除文档
db.delete(document)
db.commit()
```

---

### Q12: SQLAlchemy 如何处理数据库事务？

**参考答案：**

**基础事务控制：**

```python
# 自动提交模式（默认关闭）
with Session(engine) as session:
    session.add(doc1)
    session.add(doc2)
    session.commit()  # 显式提交

# 手动回滚
with Session(engine) as session:
    try:
        session.add(doc1)
        session.add(doc2)
        session.commit()
    except Exception as e:
        session.rollback()  # 回滚所有变更
        raise

# 上下文管理器（推荐）
with session.begin():
    session.add(doc1)
    session.add(doc2)
    # 自动提交或回滚
```

**嵌套事务（Savepoint）：**

```python
with session.begin():
    session.add(doc1)  # savepoint A
    
    try:
        with session.begin_nested():  # 创建 savepoint
            session.add(doc2)  # savepoint B
            session.add(doc3)
            # 内部嵌套事务失败
            raise Exception("Nested error")
    except:
        pass  # 嵌套事务回滚，不会影响外部事务
    
    session.add(doc4)  # 继续外部事务
# 外部事务提交：doc1 和 doc4 被保存，doc2 和 doc3 被回滚
```

**并发事务处理：**

```python
from sqlalchemy.orm import with_for_update

# 悲观锁 - FOR UPDATE
doc = session.query(Document).filter(
    Document.id == 1
).with_for_update().first()

# 其他事务尝试修改同一行会被阻塞，直到当前事务提交/回滚

# 乐观锁 - 版本号
class Document(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True)
    version = Column(Integer, default=0)  # 版本号
    
    __mapper_args__ = {"version_id_col": version}  # 启用乐观锁

# 更新时会检查版本号，版本不匹配则抛出 StaleDataError
```

**事务隔离级别：**

```python
from sqlalchemy import event
from sqlalchemy.engine import Engine

@event.listens_for(Engine, "connect")
def set_isolation_level(dbapi_conn, connection_record):
    cursor = dbapi_conn.cursor()
    cursor.execute("SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED")
    cursor.close()

# 或者在连接 URL 中指定
# mysql+pymysql://user:pass@host/db?isolation_level=READ COMMITTED
```

---

### Q13: SQLAlchemy 如何执行原生 SQL？

**参考答案：**

**执行原生 SELECT：**

```python
from sqlalchemy import text

# 简单查询
result = session.execute(text("SELECT * FROM documents WHERE id = :id"), {"id": 1})
row = result.fetchone()

# 多行查询
result = session.execute(text("SELECT * FROM documents WHERE status = :status"), {"status": 0})
rows = result.fetchall()

# 迭代器模式（大数据量）
for row in session.execute(text("SELECT * FROM documents")):
    print(row)
```

**执行原生 DML：**

```python
# INSERT
session.execute(
    text("INSERT INTO documents (filename, status) VALUES (:filename, :status)"),
    {"filename": "test.pdf", "status": 0}
)
session.commit()

# UPDATE
session.execute(
    text("UPDATE documents SET status = :status WHERE id = :id"),
    {"status": 1, "id": 1}
)
session.commit()

# DELETE
session.execute(
    text("DELETE FROM documents WHERE status = :status"),
    {"status": 2}
)
session.commit()
```

**批量执行：**

```python
# 批量 INSERT
from sqlalchemy import bindparam

stmt = text("""
    INSERT INTO documents (filename, status, created_at) 
    VALUES (:filename, :status, :created_at)
""")

session.execute(stmt, [
    {"filename": "doc1.pdf", "status": 0, "created_at": datetime.now()},
    {"filename": "doc2.pdf", "status": 0, "created_at": datetime.now()},
    {"filename": "doc3.pdf", "status": 0, "created_at": datetime.now()},
])
session.commit()

# 批量 UPDATE
session.execute(
    text("UPDATE documents SET status = :status WHERE id = :id"),
    [
        {"status": 1, "id": 1},
        {"status": 1, "id": 2},
        {"status": 1, "id": 3},
    ]
)
session.commit()
```

**与 ORM 混合使用：**

```python
# 使用原生 SQL 查询，结果映射到 ORM 对象
from sqlalchemy.orm import Session

result = session.execute(
    text("SELECT id, filename FROM documents WHERE status = :status"),
    {"status": 0}
)

# 方式1：手动映射
docs = [Document(id=row[0], filename=row[1]) for row in result]

# 方式2：使用 session.bind
# result = session.query(Document).from_statement(text("...")).all()

# 方式3：使用 selectable
from sqlalchemy import select
stmt = select(Document).where(Document.status == 0)
result = session.execute(stmt)
docs = result.scalars().all()
```

---

### Q14: SQLAlchemy 如何处理日期时间类型？

**参考答案：**

**DateTime 字段定义：**

```python
from datetime import datetime
from sqlalchemy import DateTime, Date, Time

class Document(Base):
    __tablename__ = "documents"
    
    # 标准日期时间
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    
    # 自动更新
    updated_at = Column(
        DateTime, 
        default=datetime.now, 
        onupdate=datetime.now
    )
    
    # 可空日期时间
    deleted_at = Column(DateTime, nullable=True)
    
    # 只有日期
    publish_date = Column(Date)
    
    # 只有时间
    schedule_time = Column(Time)
```

**Python 端格式化：**

```python
# 获取日期
doc = session.query(Document).first()

# 直接访问
print(doc.created_at)  # datetime.datetime(2024, 1, 15, 10, 30, 0)

# 格式化为字符串
formatted = doc.created_at.strftime("%Y-%m-%d %H:%M:%S")
print(formatted)  # "2024-01-15 10:30:00"

# 获取日期部分
date_only = doc.created_at.date()  # datetime.date(2024, 1, 15)

# 获取时间部分
time_only = doc.created_at.time()  # datetime.time(10, 30, 0)
```

**数据库端查询：**

```python
from sqlalchemy import func, cast, Date

# 按日期分组
stats = session.query(
    cast(Document.created_at, Date).label('date'),
    func.count(Document.id).label('count')
).group_by(cast(Document.created_at, Date)).all()

# 日期比较
from datetime import datetime, timedelta

# 今天
today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

# 最近7天
week_ago = today - timedelta(days=7)
recent_docs = session.query(Document).filter(
    Document.created_at >= week_ago
).all()

# 日期范围
start_date = datetime(2024, 1, 1)
end_date = datetime(2024, 12, 31, 23, 59, 59)
docs = session.query(Document).filter(
    Document.created_at.between(start_date, end_date)
).all()
```

**时区处理：**

```python
# 存储 UTC 时间
from datetime import timezone

# 创建 UTC 时间
utc_now = datetime.now(timezone.utc)

# 存储到数据库（SQLAlchemy 会自动转换为数据库时区）
doc = Document(created_at=utc_now)
session.add(doc)

# 从数据库读取
doc = session.query(Document).first()
print(doc.created_at)  # 可能已转换为本地时区

# 统一使用 UTC
def utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)  # 去掉时区信息存 MySQL
```

---

### Q15: SQLAlchemy 如何处理 JSON 字段？

**参考答案：**

**JSON 字段定义：**

```python
from sqlalchemy import JSON
from sqlalchemy.dialects.mysql import JSON as MySQLJSON

class Document(Base):
    __tablename__ = "documents"
    
    # 标准 JSON 字段
    metadata = Column(JSON, nullable=True)
    
    # MySQL JSON 字段（推荐用于 MySQL）
    extra_data = Column(MySQLJSON, nullable=True)
```

**JSON 读写操作：**

```python
# 写入 JSON
doc = Document()
doc.metadata = {
    "author": "张三",
    "tags": ["技术", "Python"],
    "stats": {"views": 100, "likes": 50}
}
session.add(doc)
session.commit()

# 读取 JSON
doc = session.query(Document).first()
print(doc.metadata["author"])  # "张三"
print(doc.metadata["tags"])   # ["技术", "Python"]

# 修改 JSON
doc.metadata["tags"].append("RAG")
doc.metadata["stats"]["views"] = 200
session.commit()
```

**JSON 查询（MySQL 5.7+）：**

```python
from sqlalchemy import text

# 使用原生 SQL 查询 JSON 字段
result = session.execute(text("""
    SELECT * FROM documents 
    WHERE JSON_EXTRACT(metadata, '$.author') = '张三'
"""))

# 使用 JSON_CONTAINS
result = session.execute(text("""
    SELECT * FROM documents 
    WHERE JSON_CONTAINS(metadata, '"技术"', '$.tags')
"""))

# 使用 JSON_KEYS
result = session.execute(text("""
    SELECT id, JSON_KEYS(metadata) as keys 
    FROM documents
"""))
```

**JSON 字段索引（MySQL 5.7+）：**

```sql
-- 添加虚拟列
ALTER TABLE documents 
ADD COLUMN author VARCHAR(100) 
GENERATED ALWAYS AS (JSON_UNQUOTE(JSON_EXTRACT(metadata, '$.author')));

-- 在虚拟列上创建索引
CREATE INDEX idx_author ON documents(author);

-- 查询时使用索引
SELECT * FROM documents WHERE author = '张三';
```

**SQLAlchemy JSON 表达式：**

```python
from sqlalchemy import func

# MySQL JSON 函数
# JSON_EXTRACT
session.query(Document).filter(
    func.json_extract(Document.metadata, '$.author') == '"张三"'
)

# JSON_CONTAINS
session.query(Document).filter(
    func.json_contains(Document.metadata, '"技术"', '$.tags')
)
```

---

## 4. 查询与过滤

### Q16: SQLAlchemy 如何实现分页查询？

**参考答案：**

**基础分页：**

```python
def paginate_query(session, page: int, page_size: int):
    """分页查询"""
    offset = (page - 1) * page_size
    
    # 查询数据
    items = session.query(Document)\
        .order_by(Document.created_at.desc())\
        .offset(offset)\
        .limit(page_size)\
        .all()
    
    # 查询总数
    total = session.query(func.count(Document.id)).scalar()
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size
    }
```

**封装为可复用方法：**

```python
class Paginator:
    def __init__(self, query, page: int, page_size: int):
        self.query = query
        self.page = page
        self.page_size = page_size
        self._total = None
    
    @property
    def total(self):
        if self._total is None:
            self._total = self.query.count()
        return self._total
    
    @property
    def total_pages(self):
        return (self.total + self.page_size - 1) // self.page_size
    
    @property
    def items(self):
        offset = (self.page - 1) * self.page_size
        return self.query.offset(offset).limit(self.page_size).all()
    
    def to_dict(self):
        return {
            "items": self.items,
            "total": self.total,
            "page": self.page,
            "page_size": self.page_size,
            "total_pages": self.total_pages
        }

# 使用
paginator = Paginator(
    session.query(Document).filter(Document.status == 0),
    page=1,
    page_size=20
)
result = paginator.to_dict()
```

**游标分页（效率更高）：**

```python
def cursor_paginate(session, cursor: str = None, limit: int = 20):
    """
    游标分页：使用 ID 或时间戳作为游标
    适合数据频繁变动的场景
    """
    query = session.query(Document).order_by(Document.id.desc())
    
    if cursor:
        cursor_id = int(cursor)
        query = query.filter(Document.id < cursor_id)
    
    items = query.limit(limit).all()
    
    next_cursor = str(items[-1].id) if items else None
    
    return {
        "items": items,
        "next_cursor": next_cursor
    }
```

**项目中的分页实现：**

```python
# rag-qa-system/app/services/document_service.py

def get_document_list(
    self,
    db: Session,
    skip: int = 0,
    limit: int = 20,
    status: int = None
) -> Tuple[List[Document], int]:
    """获取文档列表（分页）"""
    query = db.query(Document)
    
    if status is not None:
        query = query.filter(Document.status == status)
    
    total = query.count()
    
    documents = query\
        .order_by(Document.created_at.desc())\
        .offset(skip)\
        .limit(limit)\
        .all()
    
    return documents, total
```

---

### Q17: SQLAlchemy 如何处理 JOIN 查询？

**参考答案：**

**内连接（INNER JOIN）：**

```python
from sqlalchemy import select

# 方式1：ORM 关系查询
docs = session.query(Document).join(
    DocumentChunk, Document.id == DocumentChunk.document_id
).filter(Document.status == 1).all()

# 方式2：select 语句
stmt = select(Document, DocumentChunk).join(
    DocumentChunk, Document.id == DocumentChunk.document_id
).where(Document.status == 1)
result = session.execute(stmt)

# 方式3：使用 relationship 的 join
docs = session.query(Document).join(Document.chunks).all()
```

**左连接（LEFT JOIN）：**

```python
# 使用 outerjoin
from sqlalchemy.orm import joinedload

# 查询文档及其块（可能没有块）
stmt = select(Document).outerjoin(DocumentChunk)

# 使用预加载
docs = session.query(Document).options(
    joinedload(Document.chunks, innerjoin=False)  # LEFT JOIN
).all()

# 过滤关联表
stmt = select(Document).outerjoin(
    DocumentChunk, Document.id == DocumentChunk.document_id
).filter(
    Document.status == 1,
    or_(DocumentChunk.id == None, DocumentChunk.char_count > 100)
)
```

**多表连接：**

```python
# 三表连接
# Document → DocumentChunk → Tag

stmt = select(Document).join(
    DocumentChunk, Document.id == DocumentChunk.document_id
).join(
    document_tags, DocumentChunk.id == document_tags.c.chunk_id
).join(
    Tag, document_tags.c.tag_id == Tag.id
).filter(Tag.name == "技术")
```

**带条件的 JOIN：**

```python
# 只 JOIN 满足条件的块
stmt = select(Document).outerjoin(
    DocumentChunk,
    and_(
        Document.id == DocumentChunk.document_id,
        DocumentChunk.char_count > 100  # 只 JOIN 大块
    )
)
```

---

### Q18: SQLAlchemy 如何处理 group by 和聚合查询？

**参考答案：**

**基础聚合：**

```python
from sqlalchemy import func

# COUNT
count = session.query(func.count(Document.id)).scalar()

# 带条件的 COUNT
count = session.query(func.count(Document.id)).filter(
    Document.status == 0
).scalar()

# SUM
total_size = session.query(
    func.sum(Document.file_size)
).scalar()

# AVG
avg_size = session.query(
    func.avg(Document.file_size)
).scalar()

# MAX / MIN
max_size = session.query(func.max(Document.file_size)).scalar()
min_size = session.query(func.min(Document.file_size)).scalar()
```

**分组查询：**

```python
# 按状态统计数量
stats = session.query(
    Document.status,
    func.count(Document.id).label('count')
).group_by(Document.status).all()

# 结果: [(0, 10), (1, 20), (2, 5)]

# 按状态统计大小
stats = session.query(
    Document.status,
    func.count(Document.id).label('count'),
    func.sum(Document.file_size).label('total_size'),
    func.avg(Document.file_size).label('avg_size')
).group_by(Document.status).all()

# HAVING 过滤
stats = session.query(
    Document.status,
    func.count(Document.id).label('count')
).group_by(Document.status).having(
    func.count(Document.id) > 5
).all()
```

**子查询：**

```python
from sqlalchemy import subquery, select

# 子查询计算平均大小
avg_size_subq = select([func.avg(Document.file_size)]).scalar_subquery()

# 查询大于平均大小的文档
docs = session.query(Document).filter(
    Document.file_size > avg_size_subq
).all()

# 带分组的结果作为子查询
# 查询每个状态中最大的文档
subq = select(
    Document.status,
    func.max(Document.file_size).label('max_size')
).group_by(Document.status).subquery()

result = session.query(
    Document.filename,
    Document.status,
    Document.file_size
).join(
    subq,
    and_(
        Document.status == subq.c.status,
        Document.file_size == subq.c.max_size
    )
).all()
```

**窗口函数（MySQL 8.0+）：**

```python
from sqlalchemy import over, desc

# 每个状态的文档数量
docs = session.query(
    Document.filename,
    Document.status,
    func.count(Document.id).over(
        partition_by=Document.status
    ).label('status_count')
).order_by(Document.status).all()

# 状态内排名
docs = session.query(
    Document.filename,
    Document.file_size,
    func.rank().over(
        partition_by=Document.status,
        order_by=desc(Document.file_size)
    ).label('rank')
).all()
```

---

### Q19: SQLAlchemy 如何处理 UNION 和 UNION ALL？

**参考答案：**

**UNION 合并结果集：**

```python
from sqlalchemy import union, union_all, select

# 查询已处理和失败的文档
stmt1 = select(Document.id, Document.filename).filter(Document.status == 1)
stmt2 = select(Document.id, Document.filename).filter(Document.status == 2)

# UNION（去重）
combined = session.execute(union(stmt1, stmt2)).fetchall()

# UNION ALL（不去重，效率更高）
combined = session.execute(union_all(stmt1, stmt2)).fetchall()
```

**复杂 UNION：**

```python
# 合并不同类型的查询
stmt1 = select(
    Document.id,
    Document.filename,
    Document.file_size,
    literal("document").label('type')
).filter(Document.status == 1)

stmt2 = select(
    DocumentChunk.id,
    DocumentChunk.content,
    DocumentChunk.char_count,
    literal("chunk").label('type')
).filter(DocumentChunk.char_count > 500)

# 合并并排序
combined = select('*').select_from(
    union_all(stmt1, stmt2)
).order_by('file_size').limit(20)

result = session.execute(combined)
```

**UNION 注意事项：**

```python
# 1. 列数必须相同
# 2. 列类型必须兼容
# 3. 列名以第一个 SELECT 为准

# 示例：正确
stmt1 = select(Document.id, Document.filename)
stmt2 = select(QALog.id, QALog.question)  # 两个查询都有 2 列

# 示例：错误
stmt1 = select(Document.id, Document.filename, Document.file_size)
stmt2 = select(QALog.id, QALog.question)  # 列数不匹配
```

---

### Q20: SQLAlchemy 如何实现 distinct 去重查询？

**参考答案：**

**基础去重：**

```python
# DISTINCT 查询
distinct_statuses = session.query(
    Document.status
).distinct().all()

# 等价 SQL:
-- SELECT DISTINCT status FROM documents

# 去重计数
count = session.query(
    func.count(func.distinct(Document.status))
).scalar()

# 等价 SQL:
-- SELECT COUNT(DISTINCT status) FROM documents
```

**基于列组合去重：**

```python
# 查询不重复的 (status, file_type) 组合
distinct_combos = session.query(
    Document.status,
    Document.file_type
).distinct().all()

# 查询每个状态的第一条记录
first_per_status = session.query(
    Document
).distinct(Document.status).all()
```

**distinct() 方法参数：**

```python
# SQLAlchemy 2.0 写法
from sqlalchemy import select, distinct

# distinct() 带列名
stmt = select(
    Document.status,
    func.count('*')
).select_from(Document).group_by(
    distinct(Document.status)
)

# 简单去重
stmt = select(Document).distinct()
```

**去重后分页：**

```python
def get_distinct_docs(session, page: int, page_size: int):
    """去重后分页"""
    # 子查询：获取去重后的文档 ID
    subq = select(
        func.min(Document.id).label('id')
    ).group_by(
        Document.filename,
        Document.content_hash
    ).subquery()
    
    # 关联查询获取完整数据
    offset = (page - 1) * page_size
    
    total = session.query(func.count(subq.c.id)).scalar()
    
    docs = session.query(Document).join(
        subq, Document.id == subq.c.id
    ).offset(offset).limit(page_size).all()
    
    return {"items": docs, "total": total}
```

---

## 5. 事务与并发

### Q21: SQLAlchemy 如何处理并发冲突？

**参考答案：**

**乐观锁（Optimistic Locking）：**

```python
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Document(Base):
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True)
    filename = Column(String(255))
    version = Column(Integer, default=0, nullable=False)
    
    # 启用版本控制
    __mapper_args__ = {"version_id_col": version}

# 更新时会自动检查版本
doc = session.query(Document).get(1)
doc.status = 1
session.commit()  # 版本从 0 变为 1

# 另一个事务尝试更新
session2.query(Document).get(1).status = 2
session2.commit()

# 回到第一个事务尝试提交
doc.status = 3
session.commit()  
# 抛出 StaleDataError，因为版本不匹配
```

**悲观锁（Pessimistic Locking）：**

```python
from sqlalchemy.orm import with_for_update

# SELECT ... FOR UPDATE
doc = session.query(Document).filter(
    Document.id == 1
).with_for_update().first()

# 其他事务尝试修改会被阻塞

# 指定锁等待超时
doc = session.query(Document).filter(
    Document.id == 1
).with_for_update(nowait=False).first()

# NOWAIT - 立即失败
doc = session.query(Document).filter(
    Document.id == 1
).with_for_update(nowait=True).first()
# 立即抛出异常，不等待
```

**手动版本检查：**

```python
def update_with_version_check(session, doc_id: int, expected_version: int):
    """手动版本检查"""
    doc = session.query(Document).filter(
        Document.id == doc_id
    ).first()
    
    if doc.version != expected_version:
        raise StaleDataError(
            f"Document {doc_id} has been modified by another transaction"
        )
    
    doc.version += 1
    session.commit()
    return doc
```

---

### Q22: SQLAlchemy 连接池如何配置？

**参考答案：**

**连接池配置：**

```python
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

# 基础连接池
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=5,        # 基础连接数
    max_overflow=10,    # 最大额外连接数
    pool_timeout=30,   # 获取连接超时（秒）
    pool_recycle=3600,  # 连接回收时间（秒）
    pool_pre_ping=True, # 使用前检测连接
)

# 单例连接池（开发环境）
engine = create_engine(
    DATABASE_URL,
    pool_size=5,
    max_overflow=0,  # 不允许额外连接
)

# 禁用连接池（不推荐）
engine = create_engine(DATABASE_URL, poolclass=NullPool)

# 使用已存在的连接
from sqlalchemy.pool import AssertionPool
engine = create_engine(DATABASE_URL, poolclass=AssertionPool)
```

**不同环境的配置：**

```python
# 开发环境：复用连接
dev_engine = create_engine(
    DATABASE_URL,
    pool_size=5,
    max_overflow=0,  # 避免连接泄漏
    echo=True,  # 打印 SQL
)

# 生产环境：更大连接池
prod_engine = create_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=30,
    pool_timeout=30,
    pool_recycle=1800,  # 30分钟回收
    pool_pre_ping=True,  # 检测连接有效性
)

# 测试环境：每次创建新连接
test_engine = create_engine(
    DATABASE_URL,
    poolclass=StaticPool,
    connect_args={"check_same_thread": False}
)
```

**连接池监控：**

```python
# 获取连接池状态
pool = engine.pool

print(f"连接数: {pool.size()}")
print(f"当前连接: {pool.checkedin()}")
print(f"可用连接: {pool.checkedout()}")

# 预热连接池
engine.pool_prep = True

# 清空连接池
engine.dispose()  # 关闭所有连接并创建新池
```

---

### Q23: 如何处理 SQLAlchemy 的数据库连接问题？

**参考答案：**

**连接错误处理：**

```python
from sqlalchemy.exc import OperationalError, TimeoutError

def safe_execute(session, func, max_retries=3):
    """带重试的执行"""
    for attempt in range(max_retries):
        try:
            return func()
        except OperationalError as e:
            if "Lost connection" in str(e) and attempt < max_retries - 1:
                session.rollback()
                continue
            raise
        except TimeoutError:
            if attempt < max_retries - 1:
                session.rollback()
                continue
            raise
```

**重连机制：**

```python
from sqlalchemy import event

@event.listens_for(engine, "engine_connect")
def ping_connection(dbapi_connection, connection_record, connection_proxy):
    """每次获取连接前 ping 检测"""
    cursor = dbapi_connection.cursor()
    try:
        cursor.execute("SELECT 1")
    except:
        # 连接失效，抛出异常让连接池重新获取
        raise
    finally:
        cursor.close()

# 或者使用 pool_pre_ping
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # 自动检测连接
)
```

**连接超时配置：**

```python
DATABASE_URL = (
    "mysql+pymysql://user:pass@host:3306/db"
    "?connect_timeout=10"      # 连接超时
    "&read_timeout=30"       # 读取超时
    "&write_timeout=30"      # 写入超时
)

engine = create_engine(
    DATABASE_URL,
    connect_args={
        "connect_timeout": 10,
        "read_timeout": 30,
        "write_timeout": 30,
    },
    pool_timeout=30,
)
```

**连接泄漏检测：**

```python
# 检查未关闭的连接
@event.listens_for(engine, "checkout")
def receive_checkout(dbapi_connection, connection_record, connection_proxy):
    connection_record.info["checkout_time"] = time.time()

@event.listens_for(engine, "checkin")
def receive_checkin(dbapi_connection, connection_record):
    checkout_time = connection_record.info.get("checkout_time")
    if checkout_time:
        duration = time.time() - checkout_time
        if duration > 60:  # 超过60秒
            logger.warning(f"连接使用时间过长: {duration:.2f}秒")
```

---

## 6. 性能优化

### Q24: SQLAlchemy 如何避免 N+1 查询问题？

**参考答案：**

**N+1 问题说明：**

```
N+1 查询问题：
- 1次查询获取 N 个文档
- N 次查询获取每个文档的块
- 总共 1 + N 次查询

示例：
docs = session.query(Document).limit(10).all()  # 1次查询
for doc in docs:
    print(doc.chunks)  # 每次访问触发1次查询，10次
# 总共 11 次查询！
```

**解决方案：预加载（Eager Loading）：**

```python
from sqlalchemy.orm import selectinload, joinedload, subqueryload

# 方案1：selectinload（推荐）
# 分开查询，用 IN 子句加载关联数据
docs = session.query(Document).options(
    selectinload(Document.chunks)  # 2次查询
).limit(10).all()

# 等价 SQL:
-- SELECT * FROM documents LIMIT 10;
-- SELECT * FROM document_chunks WHERE document_id IN (1, 2, 3, ...);

# 方案2：joinedload（JOIN 查询）
# 单次查询，使用 LEFT JOIN
docs = session.query(Document).options(
    joinedload(Document.chunks)  # 1次查询
).limit(10).all()

# 方案3：subqueryload
# 使用子查询加载
docs = session.query(Document).options(
    subqueryload(Document.chunks)  # 2次查询
).limit(10).all()
```

**多层预加载：**

```python
# Document → Chunk → Tag (三层关系)
docs = session.query(Document).options(
    selectinload(Document.chunks).selectinload(DocumentChunk.tags)
).limit(10).all()

# 过滤预加载的关联
from sqlalchemy.orm import contains_eager

docs = session.query(Document).join(Document.chunks).options(
    contains_eager(Document.chunks)
).filter(DocumentChunk.char_count > 100).all()
```

**lazy 参数：**

```python
class Document(Base):
    __tablename__ = "documents"
    
    # 关系默认懒加载
    chunks = relationship("DocumentChunk", back_populates="document")
    
    # 预加载关系
    chunks = relationship(
        "DocumentChunk",
        back_populates="document",
        lazy="selectin"  # 自动使用 selectinload
    )
    
    # 立即加载
    chunks = relationship(
        "DocumentChunk",
        back_populates="document",
        lazy="joined"  # 自动使用 joinedload
    )
```

---

### Q25: SQLAlchemy 如何使用索引提升查询性能？

**参考答案：**

**在模型中定义索引：**

```python
class Document(Base):
    __tablename__ = "documents"
    
    id = Column(BigInteger, primary_key=True)
    filename = Column(String(255))
    status = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.now)
    
    # 单列索引
    __table_args__ = (
        Index("idx_status", "status"),  # 状态索引
        Index("idx_created", "created_at"),  # 创建时间索引
        
        # 复合索引（注意列顺序）
        Index("idx_status_created", "status", "created_at"),
        
        # 函数索引（MySQL 5.7+）
        Index("idx_filename_lower", "filename"),  # 存储 filename 的小写
    )
```

**创建索引的方式：**

```sql
-- 直接在数据库创建
CREATE INDEX idx_status ON documents(status);
CREATE INDEX idx_status_created ON documents(status, created_at);

-- 唯一索引
CREATE UNIQUE INDEX idx_content_hash ON documents(content_hash);

-- 全文索引（MySQL 5.6+）
ALTER TABLE documents ADD FULLTEXT INDEX idx_filename_fulltext(filename);
```

**索引使用分析：**

```python
# 查看查询计划
result = session.execute(
    text("EXPLAIN SELECT * FROM documents WHERE status = 0")
)
print(result.fetchall())

# SQLAlchemy 的查询计划
from sqlalchemy import explain

stmt = select(Document).where(Document.status == 0)
print(explain.format_explain(session.execute(stmt)))
```

**复合索引设计原则：**

```python
# 假设经常查询：WHERE status = 0 AND created_at > '2024-01-01'

# 方案1：创建复合索引（最优）
Index("idx_status_created", "status", "created_at")

# 方案2：两个单列索引（也可行）
Index("idx_status", "status")
Index("idx_created", "created_at")

# 复合索引列顺序原则：
# 1. 等值查询的列放前面
# 2. 范围查询的列放后面
```

---

### Q26: SQLAlchemy 如何优化批量操作性能？

**参考答案：**

**批量插入优化：**

```python
# 普通插入（慢）
for data in records:
    doc = Document(**data)
    session.add(doc)
session.commit()

# 批量插入（快）
session.bulk_save_objects([
    Document(**data) for data in records
])
session.commit()

# 原生批量插入（最快）
from sqlalchemy import insert

stmt = insert(Document)
session.execute(stmt, records)
session.commit()

# 批量插入并返回 ID
stmt = insert(Document).returning(Document.id, Document.filename)
result = session.execute(stmt, records)
ids = [row[0] for row in result]  # 获取插入的 ID
```

**批量更新优化：**

```python
# 普通更新（逐行）
for doc in session.query(Document).filter(Document.status == 0).all():
    doc.status = 1
session.commit()

# 批量更新（一次）
session.query(Document).filter(
    Document.status == 0
).update({"status": 1}, synchronize_session=False)
session.commit()

# 使用 bulk_update_mappings
from sqlalchemy.orm import bulk_update_mappings

mappings = [
    {"id": doc.id, "status": 1} for doc in session.query(Document).filter(Document.status == 0).all()
]
session.bulk_update_mappings(Document, mappings)
session.commit()
```

**分批处理大数据：**

```python
def process_large_batch(session, records, batch_size=1000):
    """分批处理大量数据"""
    total = len(records)
    
    for i in range(0, total, batch_size):
        batch = records[i:i + batch_size]
        
        session.bulk_save_objects(batch)
        session.commit()
        
        logger.info(f"处理进度: {min(i + batch_size, total)}/{total}")
```

**性能对比：**

| 方法 | 1000条记录耗时 | 说明 |
|------|---------------|------|
| 逐行插入 | ~5秒 | 最慢 |
| bulk_save_objects | ~0.5秒 | 推荐 |
| insert bulk | ~0.3秒 | 最快 |

---

## 7. 索引与约束

### Q27: SQLAlchemy 如何定义和使用外键约束？

**参考答案：**

**外键定义：**

```python
class DocumentChunk(Base):
    __tablename__ = "document_chunks"
    
    id = Column(BigInteger, primary_key=True)
    
    # 外键定义
    document_id = Column(
        BigInteger,
        ForeignKey("documents.id", ondelete="CASCADE"),  # 级联删除
        nullable=False,
        index=True
    )
    
    # 外键关系
    document = relationship("Document", back_populates="chunks")
```

**级联操作：**

```python
# CASCADE：删除主表记录时自动删除子表记录
ForeignKey("documents.id", ondelete="CASCADE")

# SET NULL：删除时将外键设为 NULL
ForeignKey("documents.id", ondelete="SET NULL")

# SET DEFAULT：删除时使用默认值
ForeignKey("documents.id", ondelete="SET DEFAULT")

# RESTRICT：阻止删除有子记录的主表记录
ForeignKey("documents.id", ondelete="RESTRICT")

# NO ACTION：延迟检查（InnoDB 等同于 RESTRICT）
ForeignKey("documents.id", ondelete="NO ACTION")
```

**多列外键：**

```python
class ChunkTag(Base):
    __tablename__ = "chunk_tags"
    
    chunk_id = Column(BigInteger, ForeignKey("document_chunks.id"))
    tag_id = Column(BigInteger, ForeignKey("tags.id"))
    
    # 复合外键
    __table_args__ = (
        ForeignKeyConstraint(
            ['chunk_id', 'tag_id'],
            ['chunks.id', 'tags.id'],
            ondelete="CASCADE"
        ),
    )
```

**外键查询：**

```python
# 获取文档块关联的文档
chunk = session.query(DocumentChunk).first()
print(chunk.document.filename)  # 通过外键关系访问

# 反向查询：获取文档的所有块
doc = session.query(Document).first()
print(len(doc.chunks))  # 通过反向关系访问
```

---

### Q28: SQLAlchemy 如何定义和使用唯一约束？

**参考答案：**

**唯一约束定义：**

```python
class Document(Base):
    __tablename__ = "documents"
    
    id = Column(BigInteger, primary_key=True)
    filename = Column(String(255), nullable=False)
    content_hash = Column(String(64), unique=True)  # 方式1
    created_at = Column(DateTime, default=datetime.now)
    
    # 唯一约束（方式2）
    __table_args__ = (
        UniqueConstraint("filename", "created_at", name="uix_filename_created"),
    )
```

**复合唯一约束：**

```python
# 文件名和用户ID的组合唯一
class Document(Base):
    __tablename__ = "documents"
    
    user_id = Column(BigInteger)
    filename = Column(String(255))
    
    __table_args__ = (
        UniqueConstraint("user_id", "filename", name="uix_user_filename"),
    )
```

**查询唯一约束：**

```python
# 检查唯一约束冲突
try:
    doc = Document(content_hash="abc123")
    session.add(doc)
    session.commit()
except sqlalchemy.exc.IntegrityError as e:
    if "Duplicate entry" in str(e):
        print("已存在相同 content_hash 的记录")
    session.rollback()
```

**使用 unique 索引：**

```python
# 确保文件不重复
def upload_document(db, user_id: int, filename: str, content: bytes):
    content_hash = hashlib.md5(content).hexdigest()
    
    # 检查是否已存在
    existing = db.query(Document).filter(
        Document.user_id == user_id,
        Document.content_hash == content_hash
    ).first()
    
    if existing:
        return existing
    
    # 创建新记录
    doc = Document(
        user_id=user_id,
        filename=filename,
        content_hash=content_hash
    )
    db.add(doc)
    db.commit()
    return doc
```

---

### Q29: SQLAlchemy 如何处理数据库迁移？

**参考答案：**

**Alembic 迁移工具：**

```bash
# 安装
pip install alembic

# 初始化
alembic init alembic

# 配置 alembic.ini
sqlalchemy.url = mysql+pymysql://user:pass@host/db

# 创建迁移
alembic revision --autogenerate -m "Add documents table"

# 应用迁移
alembic upgrade head

# 回滚
alembic downgrade -1
```

**迁移文件结构：**

```python
# alembic/versions/20240115_add_documents.py

def upgrade():
    op.create_table(
        'documents',
        Column('id', BigInteger(), primary_key=True),
        Column('filename', String(255), nullable=False),
        Column('status', Integer(), default=0),
        Column('created_at', DateTime(), default=func.now()),
    )
    
    # 创建索引
    op.create_index('idx_status', 'documents', ['status'])
    
    # 添加注释
    op.create_table_comment('documents', '文档表')

def downgrade():
    op.drop_index('idx_status', 'documents')
    op.drop_table('documents')
```

**自动生成迁移：**

```python
# alembic/env.py 配置
from alembic import context
from myapp.models import Base  # 导入模型

target_metadata = Base.metadata

# 自动检测模型变更
alembic revision --autogenerate -m "auto migration"
```

**常用 Alembic 命令：**

```bash
alembic current          # 查看当前版本
alembic history          # 查看迁移历史
alembic heads            # 查看最新版本
alembic upgrade head      # 升级到最新
alembic downgrade base    # 回滚到初始
alembic revision --autogenerate -m "描述"  # 创建新迁移
```

---

### Q30: SQLAlchemy 如何处理数据库审计日志？

**参考答案：**

**审计日志模型：**

```python
class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(BigInteger, primary_key=True)
    table_name = Column(String(50), nullable=False)
    record_id = Column(BigInteger, nullable=False)
    action = Column(String(10), nullable=False)  # INSERT/UPDATE/DELETE
    old_values = Column(JSON)  # 变更前的值
    new_values = Column(JSON)  # 变更后的值
    user_id = Column(String(64))
    ip_address = Column(String(50))
    created_at = Column(DateTime, default=datetime.now)
```

**自动审计装饰器：**

```python
from sqlalchemy import event
from functools import wraps

def audit_operation(operation_name):
    """审计装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(session, record, *args, **kwargs):
            old_values = {c.name: getattr(record, c.name) for c in record.__table__.columns}
            
            result = func(session, record, *args, **kwargs)
            
            new_values = {c.name: getattr(record, c.name) for c in record.__table__.columns}
            
            # 记录审计日志
            audit = AuditLog(
                table_name=record.__tablename__,
                record_id=record.id,
                action=operation_name,
                old_values=old_values,
                new_values=new_values,
                user_id=get_current_user_id(),
                created_at=datetime.now()
            )
            session.add(audit)
            
            return result
        return wrapper
    return decorator
```

**使用事件监听：**

```python
from sqlalchemy import event

@event.listens_for(Document, "before_insert")
def audit_insert(mapper, connection, target):
    """插入前审计"""
    print(f"Inserting document: {target.filename}")

@event.listens_for(Document, "after_update")
def audit_update(mapper, connection, target):
    """更新后审计"""
    print(f"Updated document: {target.id}, status: {target.status}")

@event.listens_for(Document, "after_delete")
def audit_delete(mapper, connection, target):
    """删除后审计"""
    print(f"Deleted document: {target.id}")
```

---

## 附录：面试重点总结

### 核心知识点

| 类别 | 重点内容 |
|------|----------|
| **ORM 基础** | 模型定义、会话管理、CRUD 操作 |
| **查询构建** | 过滤、排序、分页、关联查询 |
| **事务控制** | 提交、回滚、隔离级别、锁 |
| **性能优化** | N+1 问题、索引、批量操作 |
| **约束设计** | 主键、外键、唯一约束、检查约束 |

### 常见追问

1. **Session 和 Engine 的区别？**
   - Engine：数据库连接管理，负责底层连接
   - Session：事务会话，管理 ORM 对象

2. **如何选择 eager loading 方式？**
   - joinedload：适合一对一或数据量小
   - selectinload：适合一对多，数据量中等
   - subqueryload：类似 selectinload

3. **索引设计原则？**
   - 等值查询列优先
   - 范围查询列靠后
   - 选择性高的列优先

---

*本文档共 30 道面试题，覆盖 MySQL + SQLAlchemy 的核心技术点*
