# MySQL数据库 - 20K薪资面试题

> 本文档包含MySQL数据库相关面试题，涵盖基础概念、存储引擎、索引、事务、SQL优化等核心知识点。

---

## 第一部分：基础概念（共8题）

### Q1: MySQL的整体架构是怎样的？

**题目类型**：基础概念类

**问题描述**：MySQL的整体架构是什么？各组件的作用是什么？

**答案要点**：

**MySQL架构图：**

```
┌─────────────────────────────────────────────────────────────────┐
│                         客户端层                                │
│    JDBC/ODBC  |  连接池  |  连接管理                           │
└────────────────────────────┬───────────────────────────────────┘
                             │
┌────────────────────────────▼───────────────────────────────────┐
│                        连接层                                    │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐              │
│  │  连接器    │  │  管理器    │  │ 安全认证  │              │
│  │ Connection │  │  Services  │  │  模块     │              │
│  └────────────┘  └────────────┘  └────────────┘              │
└────────────────────────────┬───────────────────────────────────┘
                             │
┌────────────────────────────▼───────────────────────────────────┐
│                        服务层                                    │
│  ┌────────────────────────────────────────────────────────┐  │
│  │                    SQL接口 (SQL Interface)              │  │
│  ├────────────────────────────────────────────────────────┤  │
│  │                    解析器 (Parser)                      │  │
│  ├────────────────────────────────────────────────────────┤  │
│  │                    优化器 (Optimizer)                   │  │
│  ├────────────────────────────────────────────────────────┤  │
│  │                    缓存 (Cache/Buffer)                   │  │
│  └────────────────────────────────────────────────────────┘  │
└────────────────────────────┬───────────────────────────────────┘
                             │
┌────────────────────────────▼───────────────────────────────────┐
│                        存储引擎层                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │  InnoDB  │  │  MyISAM  │  │ Memory   │  │  Archive │   │
│  │  (默认)   │  │          │  │          │  │          │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└────────────────────────────┬───────────────────────────────────┘
                             │
┌────────────────────────────▼───────────────────────────────────┐
│                        物理文件层                              │
│      .frm  |  .ibd  |  .MYD  |  .MYI  |  ibdata1           │
└───────────────────────────────────────────────────────────────┘
```

**各层职责：**

| 层级 | 组件 | 职责 |
|------|------|------|
| 客户端层 | 连接器 | 管理连接、权限验证 |
| 服务层 | SQL接口 | 接收SQL语句 |
| 服务层 | 解析器 | 语法解析、生成解析树 |
| 服务层 | 优化器 | 生成执行计划、选择索引 |
| 服务层 | 缓存 | 查询缓存（JDK8已移除） |
| 存储引擎层 | InnoDB/MyISAM | 数据的存取方式 |
| 物理文件层 | 数据文件 | 磁盘存储 |

---

### Q2: InnoDB和MyISAM存储引擎有什么区别？

**题目类型**：技术对比类

**问题描述**：InnoDB和MyISAM存储引擎有什么区别？各自的使用场景是什么？

**答案要点**：

**核心区别对比：**

| 特性 | InnoDB | MyISAM |
|------|--------|--------|
| 事务支持 | 支持 | 不支持 |
| 外键支持 | 支持 | 不支持 |
| 行锁 | 支持 | 支持表锁 |
| 全文索引 | 5.6+支持 | 支持 |
| 表空间 | 独立表空间/系统表空间 | 三个文件(.frm/.MYD/.MYI) |
| MVCC | 支持 | 不支持 |
| 崩溃恢复 | 自动恢复 | 较差 |
| 适用场景 | 事务场景 | 查询为主 |

**InnoDB特性：**

```sql
-- InnoDB存储结构
-- 数据存储在表空间(tablespace)中
-- 主键索引是聚簇索引(Clustered Index)
-- 支持MVCC多版本并发控制
-- 自动崩溃恢复

CREATE TABLE user_innodb (
    id INT PRIMARY KEY,
    name VARCHAR(50),
    email VARCHAR(100)
) ENGINE=InnoDB;
```

**MyISAM特性：**

```sql
-- MyISAM存储结构
-- .frm 文件存储表结构
-- .MYD 文件存储数据
-- .MYI 文件存储索引
-- 表级锁，并发性能差
-- 支持全文索引

CREATE TABLE user_myisam (
    id INT PRIMARY KEY,
    name VARCHAR(50),
    email VARCHAR(100),
    FULLTEXT(name, email)
) ENGINE=MyISAM;
```

**选择建议：**

| 场景 | 推荐引擎 |
|------|----------|
| 需要事务 | InnoDB |
| 大量INSERT | MyISAM |
| 大量UPDATE/DELETE | InnoDB |
| 表数据量大 | InnoDB |
| 查询为主 | MyISAM |
| 需要外键 | InnoDB |
| 高并发 | InnoDB |

---

### Q3: 什么是聚簇索引和非聚簇索引？

**题目类型**：技术原理类

**问题描述**：MySQL中的聚簇索引和非聚簇索引有什么区别？各自的优缺点是什么？

**答案要点**：

**索引结构对比：**

```
┌─────────────────────────────────────────────────────────────┐
│                     聚簇索引 (InnoDB)                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   主键索引B+树                                              │
│   ┌─────┐                                                   │
│   │ 1   │                                                   │
│   │ 2   │                                                   │
│   │ 3   │──────► 叶节点包含完整行数据                        │
│   │ 5   │                                                   │
│   │ 8   │                                                   │
│   └─────┘                                                   │
│                                                             │
│   数据按主键顺序存储                                        │
│                                                             │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    非聚簇索引 (MyISAM)                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   索引B+树                                                  │
│   ┌─────┐                                                   │
│   │ 1   │                                                   │
│   │ 3   │                                                   │
│   │ 5   │──────► 叶节点存储数据地址                          │
│   │ 8   │                                                   │
│   └─────┘                                                   │
│                                                             │
│   数据文件(.MYD)  ──►  与索引分开存储                        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**InnoDB聚簇索引特点：**

```sql
-- 1. 主键索引的叶节点存储完整行数据
-- 2. 非主键索引的叶节点存储主键值

CREATE TABLE orders (
    id INT PRIMARY KEY,       -- 聚簇索引
    order_no VARCHAR(20),    -- 普通索引
    user_id INT,
    amount DECIMAL(10,2),
    INDEX idx_order_no (order_no),  -- 辅助索引
    INDEX idx_user (user_id)
);

-- 查询优化
SELECT * FROM orders WHERE id = 1;        -- 直接主键索引
SELECT * FROM orders WHERE order_no = 'A'; -- 先辅助索引，再回表
```

**优缺点对比：**

| 特性 | 聚簇索引 | 非聚簇索引 |
|------|----------|------------|
| 优点 | 查询快，无需回表 | 更新快 |
| 缺点 | 更新慢（可能页分裂） | 查询需二次定位 |
| 适用 | 主键查询、范围查询 | 辅助索引查询 |

**使用建议：**

```sql
-- 1. 主键应使用自增ID
-- 避免页分裂，提高插入效率

-- 2. 避免使用UUID作为主键
-- 随机插入，性能差

-- 3. 覆盖索引减少回表
SELECT order_no, user_id FROM orders 
WHERE order_no = 'A';  -- 覆盖索引，无需回表
```

---

### Q4: 索引的类型有哪些？如何选择？

**题目类型**：基础概念类

**问题描述**：MySQL索引有哪些类型？如何选择合适的索引？

**答案要点**：

**索引类型分类：**

```sql
-- 1. 主键索引
-- 唯一且非空，每个表只能一个
ALTER TABLE user ADD PRIMARY KEY (id);

-- 2. 唯一索引
-- 值唯一，可为空
ALTER TABLE user ADD UNIQUE (email);

-- 3. 普通索引
-- 最基本的索引
ALTER TABLE user ADD INDEX (name);

-- 4. 组合索引
-- 多列组合
ALTER TABLE user ADD INDEX (name, email, phone);

-- 5. 全文索引
-- 文本内容搜索
ALTER TABLE article ADD FULLTEXT (title, content);

-- 6. 前缀索引
-- 字符串前缀
ALTER TABLE user ADD INDEX (name(10));
```

**索引数据结构：**

| 类型 | 说明 | 适用场景 |
|------|------|----------|
| B+树索引 | 默认，最常用的索引 | 范围查询、等值查询 |
| Hash索引 | 内存表使用，O(1)查询 | 等值查询 |
| R树索引 | 空间数据 | 地理坐标、多边形 |
| 全文索引 | 文本搜索 | LIKE '%keyword%' |

**组合索引最左前缀原则：**

```sql
-- 创建组合索引
ALTER TABLE orders ADD INDEX idx_composite (status, create_time, amount);

-- 命中索引的情况
SELECT * FROM orders WHERE status = 1;                    -- 命中
SELECT * FROM orders WHERE status = 1 AND create_time > '2024-01-01';  -- 命中
SELECT * FROM orders WHERE status = 1 AND amount > 100;  -- 命中
SELECT * FROM orders WHERE create_time > '2024-01-01';    -- 不命中
SELECT * FROM orders WHERE amount > 100;                  -- 不命中
```

**索引选择建议：**

```sql
-- 1. 区分度高的列放前面
ALTER TABLE user ADD INDEX (status, age);  -- status区分度低，不建议

-- 2. 频繁查询的列建立索引
-- WHERE, JOIN, ORDER BY, GROUP BY中的列

-- 3. 避免过多索引
-- 每个索引都会占用磁盘空间
-- INSERT/UPDATE/DELETE需要维护索引

-- 4. 覆盖索引减少回表
SELECT name, email FROM user WHERE name = 'Tom';  -- 覆盖索引
```

---

### Q5: 什么是事务？事务的特性是什么？

**题目类型**：基础概念类

**问题描述**：什么是数据库事务？事务的ACID特性是什么？

**答案要点**：

**事务概念：**
事务是数据库操作的基本单位，要么全部执行成功，要么全部失败回滚。

**ACID特性：**

| 特性 | 说明 | 保证机制 |
|------|------|----------|
| Atomicity（原子性） | 事务是最小执行单位 | Undo Log |
| Consistency（一致性） | 事务执行前后数据一致 | 应用程序保证 |
| Isolation（隔离性） | 并发事务互不影响 | 锁机制/MVCC |
| Durability（持久性） | 事务提交后数据持久 | Redo Log |

**事务使用示例：**

```sql
-- 开启事务
START TRANSACTION;
-- 或
BEGIN;

-- 转账操作
UPDATE account SET balance = balance - 1000 WHERE user_id = 1;
UPDATE account SET balance = balance + 1000 WHERE user_id = 2;

-- 提交事务
COMMIT;
-- 或回滚
ROLLBACK;
```

**自动提交：**

```sql
-- MySQL默认自动提交
SELECT @@autocommit;  -- 1表示自动提交开启

-- 关闭自动提交
SET autocommit = 0;

-- 手动控制事务
UPDATE account SET balance = balance - 1000 WHERE user_id = 1;
COMMIT;  -- 显式提交

-- 异常时自动回滚
```

**事务隔离级别：**

| 隔离级别 | 脏读 | 不可重复读 | 幻读 |
|----------|------|-----------|------|
| READ UNCOMMITTED | 可能 | 可能 | 可能 |
| READ COMMITTED | 不可能 | 可能 | 可能 |
| REPEATABLE READ (默认) | 不可能 | 不可能 | 可能 |
| SERIALIZABLE | 不可能 | 不可能 | 不可能 |

```sql
-- 查看隔离级别
SELECT @@transaction_isolation;

-- 设置隔离级别
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
```

---

### Q6: 并发事务带来的问题有哪些？

**题目类型**：技术原理类

**问题描述**：并发事务会引发哪些问题？如何解决？

**答案要点**：

**并发问题类型：**

| 问题 | 说明 | 示例 |
|------|------|------|
| 脏读 | 读取到其他事务未提交的数据 | T1修改,T2读取,T1回滚 |
| 不可重复读 | 同一事务两次读取数据不同 | T1读取,T2修改并提交,T1再读 |
| 幻读 | 同一事务两次查询结果不同 | T1查询,T2插入,T1再查询 |

**问题演示：**

```sql
-- 脏读示例
-- 事务1: UPDATE account SET balance = 0 WHERE user_id = 1; (未提交)
-- 事务2: SELECT balance FROM account WHERE user_id = 1; -- 读到0
-- 事务1: ROLLBACK; -- 回滚
-- 结果: 事务2读到了不存在的数据

-- 不可重复读示例
-- 事务1: SELECT balance FROM account WHERE user_id = 1; -- 1000
-- 事务2: UPDATE account SET balance = 2000 WHERE user_id = 1; -- 提交
-- 事务1: SELECT balance FROM account WHERE user_id = 1; -- 2000
-- 结果: 同一事务两次读取结果不同

-- 幻读示例
-- 事务1: SELECT * FROM orders WHERE status = 'pending'; -- 0条
-- 事务2: INSERT INTO orders VALUES (...); -- 提交
-- 事务1: SELECT * FROM orders WHERE status = 'pending'; -- 1条
-- 结果: 同一事务两次查询结果条数不同
```

**解决方案：**

```sql
-- 1. 设置隔离级别
SET SESSION TRANSACTION ISOLATION LEVEL REPEATABLE READ;

-- 2. 使用锁
-- 共享锁: 允许其他事务读，不允许写
SELECT * FROM orders LOCK IN SHARE MODE;

-- 排他锁: 不允许其他事务读写
SELECT * FROM orders FOR UPDATE;

-- 3. MVCC机制 (InnoDB)
-- 多版本并发控制
-- 通过版本链和Read View实现
```

---

### Q7: MVCC机制是什么？如何实现的？

**题目类型**：技术原理类

**问题描述**：MySQL的MVCC机制是什么？它是如何实现的？

**答案要点**：

**MVCC核心概念：**

```
┌─────────────────────────────────────────────────────────────┐
│                        MVCC                                 │
│            Multi-Version Concurrency Control                │
│                  多版本并发控制                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  每个事务在启动时会创建一个Read View                        │
│  用于判断数据的可见性                                       │
│                                                             │
│  事务修改数据时会生成Undo Log版本链                        │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                   Undo Log版本链                      │   │
│  │                                                      │   │
│  │  trx_id=100 (最新)                                  │   │
│  │       ▲                                              │   │
│  │       │                                              │   │
│  │  trx_id=90                                          │   │
│  │       ▲                                              │   │
│  │       │                                              │   │
│  │  trx_id=80 (最旧)                                  │   │
│  │                                                      │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**隐藏字段：**

```sql
-- InnoDB每行数据有三个隐藏字段
-- 1. DB_TRX_ID: 事务ID
-- 2. DB_ROLL_PTR: 回滚指针，指向Undo Log
-- 3. DB_ROW_ID: 行ID（聚簇索引才有）

-- 示例数据行结构
id | name  | salary | DB_TRX_ID | DB_ROLL_PTR | DB_ROW_ID
1  | Alice | 10000  | 100       | 0x...       | 1
```

**Read View结构：**

```sql
-- Read View包含:
-- 1. m_ids: 活跃事务ID列表
-- 2. min_trx_id: 最小活跃事务ID
-- 3. max_trx_id: 创建Read View时最大事务ID
-- 4. creator_trx_id: 当前事务ID

-- 可见性判断:
-- IF (db_trx_id == creator_trx_id) -> 可见（自己的修改）
-- IF (db_trx_id < min_trx_id) -> 可见（已提交）
-- IF (db_trx_id > max_trx_id) -> 不可见（将来事务）
-- IF (db_trx_id in m_ids) -> 不可见（未提交事务）
-- ELSE -> 可见（已提交或通过版本链追溯）
```

**RC和RR隔离级别下的MVCC：**

```sql
-- READ COMMITTED
-- 每次SELECT都创建新的Read View
-- 能读到已提交事务的修改

-- REPEATABLE READ
-- 事务开始时创建Read View，整个事务期间复用
-- 只能读到事务开始前已提交的数据

-- 幻读问题
-- InnoDB通过Next-Key Lock解决
-- 锁定索引范围 + 间隙
```

---

### Q8: 什么是锁？MySQL有哪些锁类型？

**题目类型**：基础概念类

**问题描述**：MySQL的锁机制是什么？有哪些锁类型？

**答案要点**：

**锁分类：**

```
┌─────────────────────────────────────────────────────────────┐
│                        锁类型                                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  按操作类型分:                                              │
│  ├── 共享锁 (S锁)  ──► SELECT ... LOCK IN SHARE MODE      │
│  └── 排他锁 (X锁)  ──► SELECT ... FOR UPDATE              │
│                                                             │
│  按粒度分:                                                  │
│  ├── 表锁      ──► LOCK TABLES                             │
│  ├── 行锁      ──► InnoDB默认                              │
│  ├── 间隙锁    ──► 锁定范围                                │
│  └── Next-Key Lock ──► 行锁+间隙锁                         │
│                                                             │
│  按实现分:                                                  │
│  ├── 记录锁 (Record Lock)  ──► 锁定索引记录                │
│  ├── 意向锁 (Intention Lock) ──► 表级锁标记                │
│  └── 插入意向锁 (Insert Intention)                         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**锁示例：**

```sql
-- 1. 共享锁 - 允许其他事务读，不允许写
SELECT * FROM orders WHERE id = 1 LOCK IN SHARE MODE;

-- 2. 排他锁 - 不允许其他事务读写
SELECT * FROM orders WHERE id = 1 FOR UPDATE;

-- 3. 表锁
LOCK TABLES orders READ;    -- 读锁
LOCK TABLES orders WRITE;  -- 写锁
UNLOCK TABLES;

-- 4. 间隙锁 (Gap Lock)
-- 锁定索引间的间隙
SELECT * FROM orders WHERE id BETWEEN 10 AND 20 FOR UPDATE;
-- 锁定(10, 20)区间，其他事务无法插入
```

**InnoDB行锁原理：**

```sql
-- InnoDB行锁基于索引实现
-- 如果查询不走索引，会锁住整张表

-- 示例1: 查询走索引，使用行锁
SELECT * FROM orders WHERE id = 1 FOR UPDATE;
-- 只锁定id=1这一行

-- 示例2: 查询不走索引，使用表锁
SELECT * FROM orders WHERE name = 'Tom' FOR UPDATE;
-- 如果name无索引，锁定整张表
```

**死锁及处理：**

```sql
-- 死锁示例
-- 事务1: 
UPDATE orders SET status = 'shipped' WHERE id = 1; -- 锁定id=1
UPDATE orders SET status = 'shipped' WHERE id = 2; -- 等待id=2

-- 事务2:
UPDATE orders SET status = 'shipped' WHERE id = 2; -- 锁定id=2
UPDATE orders SET status = 'shipped' WHERE id = 1; -- 死锁！

-- MySQL会自动检测并回滚小事务
-- 通过 innodb_lock_wait_timeout 设置等待时间
SET GLOBAL innodb_lock_wait_timeout = 5;
```

---

## 第二部分：SQL优化（共10题）

### Q9: 如何分析SQL性能？使用EXPLAIN？

**题目类型**：技术原理类

**问题描述**：如何使用EXPLAIN分析SQL性能？各字段的含义是什么？

**答案要点**：

**EXPLAIN使用：**

```sql
EXPLAIN SELECT * FROM orders 
WHERE user_id = 100 
ORDER BY create_time DESC;

+----+-------------+--------+------+---------------+---------+---------+-------+------+-------------+
| id | select_type| table  | type | possible_keys | key     | key_len | ref   | rows | Extra       |
+----+-------------+--------+------+---------------+---------+---------+-------+------+-------------+
|  1 | SIMPLE     | orders | ref  | idx_user      | idx_user| 4       | const |  125 | Using index |
+----+-------------+--------+------+---------------+---------+---------+-------+------+-------------+
```

**字段详解：**

| 字段 | 说明 | 优化建议 |
|------|------|----------|
| id | SELECT标识 | 子查询显示编号 |
| select_type | 查询类型 | SIMPLE(简单) > SUBQUERY > DERIVED > UNION |
| table | 查询表 | 显示表名或别名 |
| type | 连接类型 | system > const > eq_ref > ref > range > index > ALL |
| possible_keys | 可能用到的索引 | 列出可用的索引 |
| key | 实际使用的索引 | NULL表示未使用索引 |
| key_len | 索引长度 | 越短越好 |
| rows | 预估扫描行数 | 越少越好 |
| Extra | 附加信息 | Using index/Using filesort/Using temporary |

**type字段详解：**

| type值 | 说明 | 性能 |
|--------|------|------|
| system | 表只有一行 | 最好 |
| const | 主键或唯一索引等值查询 | 很好 |
| eq_ref | 唯一索引扫描 | 好 |
| ref | 非唯一索引等值查询 | 好 |
| range | 索引范围查询 | 中 |
| index | 全索引扫描 | 差 |
| ALL | 全表扫描 | 最差 |

**Extra字段优化提示：**

```sql
-- Using index: 覆盖索引，无需回表

-- Using filesort: 需要额外排序
-- 优化: 添加适当索引避免排序

-- Using temporary: 使用临时表
-- 优化: 减少GROUP BY/DISTINCT

-- Using index condition: 使用索引下推
-- MySQL 5.6+优化

-- Using where: 使用WHERE过滤
```

---

### Q10: SQL优化有哪些常用技巧？

**题目类型**：场景解决类

**问题描述**：SQL优化有哪些常用技巧？如何写出高效的SQL？

**答案要点**：

**优化技巧总结：**

```sql
-- 1. 避免SELECT *，只查询需要的字段
-- 坏: SELECT * FROM orders;
-- 好: SELECT id, user_id, amount FROM orders;

-- 2. 批量操作代替循环单条
-- 坏: 
INSERT INTO orders (id, amount) VALUES (1, 100);
INSERT INTO orders (id, amount) VALUES (2, 200);

-- 好:
INSERT INTO orders (id, amount) VALUES (1, 100), (2, 200);

-- 3. 使用LIMIT分页
-- 坏: SELECT * FROM orders OFFSET 10000 LIMIT 10;
-- 好: SELECT * FROM orders WHERE id > 10000 LIMIT 10;

-- 4. 避免LIKE通配符开头
-- 坏: SELECT * FROM user WHERE name LIKE '%Tom%';
-- 好: SELECT * FROM user WHERE name LIKE 'Tom%';

-- 5. 使用UNION ALL代替UNION（如果不需要去重）
-- 坏: SELECT name FROM user1 UNION SELECT name FROM user2;
-- 好: SELECT name FROM user1 UNION ALL SELECT name FROM user2;

-- 6. 避免在索引列上使用函数
-- 坏: SELECT * FROM orders WHERE YEAR(create_time) = 2024;
-- 好: SELECT * FROM orders WHERE create_time >= '2024-01-01';

-- 7. 避免隐式类型转换
-- 坏: SELECT * FROM user WHERE user_id = '123'; -- user_id是INT
-- 好: SELECT * FROM user WHERE user_id = 123;

-- 8. 使用EXISTS代替IN（子查询）
-- 坏: SELECT * FROM orders WHERE user_id IN (SELECT id FROM user);
-- 好: SELECT * FROM orders o WHERE EXISTS (SELECT 1 FROM user u WHERE u.id = o.user_id);
```

**索引优化：**

```sql
-- 1. 遵循最左前缀原则
ALTER TABLE orders ADD INDEX idx_status_time (status, create_time);

-- 2. 使用覆盖索引
SELECT user_id, create_time FROM orders 
WHERE status = 'pending' AND create_time > '2024-01-01';

-- 3. 区分度高的列放前面
ALTER TABLE orders ADD INDEX idx_user_time (user_id, create_time);

-- 4. 定期分析表
ANALYZE TABLE orders;
OPTIMIZE TABLE orders;
```

---

### Q11: 什么是慢查询？如何优化？

**题目类型**：场景解决类

**问题描述**：什么是慢查询？如何发现和优化慢查询？

**答案要点**：

**慢查询配置：**

```sql
-- 查看慢查询配置
SHOW VARIABLES LIKE 'slow_query%';
SHOW VARIABLES LIKE 'long_query_time';

-- 开启慢查询日志
SET GLOBAL slow_query_log = 'ON';
SET GLOBAL long_query_time = 1;  -- 超过1秒记录

-- 开启所有查询记录（不推荐用于生产）
SET GLOBAL general_log = 'ON';

-- 慢查询日志路径
SHOW VARIABLES LIKE 'slow_query_log_file';
```

**慢查询分析：**

```sql
-- 查看慢查询日志
-- /var/lib/mysql/mysql-slow.log

-- 使用mysqldumpslow分析
mysqldumpslow -t 10 /var/lib/mysql/mysql-slow.log

-- 输出示例
-- Count: 100  Time=5.00s (500s)  Lock=0.00s (0s)  
-- SELECT * FROM orders WHERE user_id = ?

-- 使用EXPLAIN分析
EXPLAIN SELECT * FROM orders WHERE user_id = 100;

-- 使用PROFILING分析
SET profiling = 1;
SELECT * FROM orders WHERE user_id = 100;
SHOW PROFILES;
SHOW PROFILE FOR QUERY 1;
```

**慢查询优化步骤：**

```sql
-- 1. 确认是否走索引
EXPLAIN SELECT * FROM orders WHERE user_id = 100;

-- 2. 检查索引是否合适
SHOW INDEX FROM orders;

-- 3. 分析执行计划
-- type是否为ALL（全表扫描）
-- rows是否过多
-- 是否Using filesort

-- 4. 添加/优化索引
ALTER TABLE orders ADD INDEX idx_user (user_id);

-- 5. 改写SQL
-- 使用JOIN代替子查询
-- 使用LIMIT分页
-- 使用覆盖索引

-- 6. 案例分析
-- 原始SQL
SELECT o.*, u.name FROM orders o 
INNER JOIN user u ON o.user_id = u.id 
WHERE o.create_time > '2024-01-01';

-- 优化后
SELECT o.id, o.amount, u.name 
FROM orders o 
INNER JOIN user u ON o.user_id = u.id 
WHERE o.create_time > '2024-01-01';
```

---

### Q12: 分页查询如何优化？

**题目类型**：场景解决类

**问题描述**：分页查询性能问题如何解决？深分页如何优化？

**答案要点**：

**分页问题：**

```sql
-- 浅分页 - 性能尚可
SELECT * FROM orders ORDER BY id LIMIT 10 OFFSET 0;  -- 快

-- 深分页 - 性能问题
SELECT * FROM orders ORDER BY id LIMIT 10 OFFSET 10000;  -- 慢
-- 原因: MySQL需要扫描前10010行，丢弃前10000行
```

**优化方案：**

```sql
-- 方案1: 使用主键+WHERE条件
-- 假设每页10条，当前页最大ID是10000

SELECT * FROM orders 
WHERE id > 10000 
ORDER BY id 
LIMIT 10;

-- 方案2: 使用JOIN子查询
SELECT * FROM orders o
INNER JOIN (
    SELECT id FROM orders ORDER BY id LIMIT 10010
) t ON o.id = t.id
ORDER BY o.id
LIMIT 10;

-- 方案3: 使用延迟关联
SELECT * FROM orders o
INNER JOIN (
    SELECT id FROM orders ORDER BY create_time LIMIT 10000, 10
) t ON o.id = t.id;

-- 方案4: 记录上次查询位置
-- 记录上一页最后一条的ID
SELECT * FROM orders 
WHERE id < #{lastId}
ORDER BY id DESC
LIMIT 10;

-- 方案5: 使用游标分页
SELECT * FROM orders 
WHERE create_time > #{cursor}
ORDER BY create_time
LIMIT 10;
```

**性能对比：**

| 方法 | 优点 | 缺点 |
|------|------|------|
| 传统OFFSET | 简单 | 深分页极慢 |
| 主键+WHERE | 简单快速 | 需要连续ID |
| JOIN子查询 | 可用其他排序字段 | 仍需扫描大量行 |
| 延迟关联 | 支持复杂排序 | 两次查询 |
| 记录位置 | 最快 | 不支持跳页 |

---

### Q13: JOIN查询如何优化？

**题目类型**：场景解决类

**问题描述**：多表JOIN查询如何优化？有哪些注意事项？

**答案要点**：

**JOIN类型对比：**

```sql
-- 1. INNER JOIN - 只保留匹配的行
SELECT * FROM orders o
INNER JOIN user u ON o.user_id = u.id;

-- 2. LEFT JOIN - 保留左表所有行
SELECT * FROM user u
LEFT JOIN orders o ON o.user_id = u.id;

-- 3. RIGHT JOIN - 保留右表所有行
SELECT * FROM user u
RIGHT JOIN orders o ON o.user_id = u.id;

-- 4. 小表驱动大表
-- 驱动表: 
--   - LEFT JOIN时左表是驱动表
--   - INNER JOIN时小表是驱动表
-- 原则: 让小表驱动大表，减少join次数
```

**优化建议：**

```sql
-- 1. 确保JOIN字段有索引
ALTER TABLE orders ADD INDEX idx_user (user_id);
ALTER TABLE user ADD INDEX idx_id (id);

-- 2. 避免SELECT *
SELECT o.id, o.amount, u.name FROM orders o
INNER JOIN user u ON o.user_id = u.id;

-- 3. 用小表驱动大表
-- 假设user表小，orders表大
-- 好: SELECT * FROM user u INNER JOIN orders o ON o.user_id = u.id;
-- 坏: SELECT * FROM orders o INNER JOIN user u ON o.user_id = u.id;

-- 4. 减少JOIN次数
-- 坏:
SELECT * FROM a 
JOIN b ON a.id = b.a_id
JOIN c ON b.id = c.b_id
JOIN d ON c.id = d.c_id;

-- 好: 根据条件，适当拆分

-- 5. 使用EXPLAIN分析JOIN
EXPLAIN SELECT * FROM orders o
INNER JOIN user u ON o.user_id = u.id;
```

**多表JOIN优化：**

```sql
-- 案例: 订单、用户、商品、分类四表查询
-- 原始SQL
SELECT o.*, u.name, p.name, c.name
FROM orders o
JOIN user u ON o.user_id = u.id
JOIN product p ON o.product_id = p.id
JOIN category c ON p.category_id = c.id
WHERE o.status = 'completed';

-- 优化后
-- 1. 确保JOIN字段有索引
-- 2. 添加WHERE条件过滤
-- 3. 使用覆盖索引
SELECT 
    o.id order_id, o.amount,
    u.name user_name,
    p.name product_name,
    c.name category_name
FROM orders o
INNER JOIN user u ON o.user_id = u.id
INNER JOIN product p ON o.product_id = p.id
INNER JOIN category c ON p.category_id = c.id
WHERE o.status = 'completed'
AND o.create_time > '2024-01-01';
```

---

### Q14: 如何设计高效的数据库表结构？

**题目类型**：场景解决类

**问题描述**：如何设计高效的数据库表结构？有哪些原则？

**答案要点**：

**表设计原则：**

```sql
-- 1. 适度规范化，避免过度设计
-- 3NF: 
-- - 第一范式: 字段不可分
-- - 第二范式: 非主键字段完全依赖于主键
-- - 第三范式: 非主键字段不能传递依赖于主键

-- 2. 选择合适的数据类型
-- 整型比字符串高效
-- VARCHAR(n) vs CHAR(n): 变长用VARCHAR，定长用CHAR
-- 日期用DATE/DATETIME，不用VARCHAR

-- 示例:
CREATE TABLE user (
    id BIGINT PRIMARY KEY,         -- BIGINT比INT更安全
    username VARCHAR(50) NOT NULL, -- 长度合适
    email VARCHAR(100) NOT NULL,
    status TINYINT DEFAULT 1,      -- 用TINYINT代替VARCHAR
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 3. 避免NULL字段
-- 设置默认值
ALTER TABLE user MODIFY COLUMN status TINYINT NOT NULL DEFAULT 1;

-- 4. 主键设计
-- 使用自增主键或分布式ID
-- 不使用UUID作为主键
```

**字段类型选择：**

| 场景 | 推荐类型 | 避免使用 |
|------|----------|----------|
| 状态/性别 | TINYINT | VARCHAR |
| 金额 | DECIMAL(10,2) | FLOAT/DOUBLE |
| 时间 | DATETIME/TIMESTAMP | VARCHAR |
| 手机号 | VARCHAR(11) | BIGINT |
| 邮箱 | VARCHAR(100) | TEXT |
| 文章内容 | TEXT | VARCHAR |

**反范式设计：**

```sql
-- 有时候需要适当冗余提高查询性能
-- 但要权衡数据一致性

-- 示例: 订单表冗余用户信息
CREATE TABLE orders (
    id BIGINT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    user_name VARCHAR(50) NOT NULL,  -- 冗余字段，避免JOIN
    amount DECIMAL(10,2) NOT NULL,
    create_time DATETIME NOT NULL,
    
    INDEX idx_user_id (user_id)
);
```

---

### Q15: 什么是SQL注入？如何防止？

**题目类型**：安全类

**问题描述**：什么是SQL注入？如何在开发中防止SQL注入？

**答案要点**：

**SQL注入原理：**

```sql
-- 恶意输入
-- 假设用户输入: ' OR '1'='1

-- 原始SQL
SELECT * FROM user WHERE username = 'input' AND password = 'xxx';

-- 注入后
SELECT * FROM user WHERE username = '' OR '1'='1' AND password = 'xxx';

-- 结果: 绕过认证

-- 注入类型
-- 1. 数字注入
SELECT * FROM orders WHERE id = 1;  -- 改为
SELECT * FROM orders WHERE id = 1 OR 1=1;

-- 2. UNION注入
SELECT * FROM user UNION SELECT * FROM admin;

-- 3. 注释注入
SELECT * FROM user WHERE username = 'admin'-- AND password = '';
```

**防止方法：**

```java
// 1. 使用参数化查询（PreparedStatement）
// Java JDBC
String sql = "SELECT * FROM user WHERE username = ? AND password = ?";
PreparedStatement ps = conn.prepareStatement(sql);
ps.setString(1, username);
ps.setString(2, password);
ResultSet rs = ps.executeQuery();

// 2. MyBatis使用#{}占位符
// Mapper
@Select("SELECT * FROM user WHERE username = #{username}")
User findByUsername(@Param("username") String username);

// 3. 严格校验输入
public boolean validateInput(String input) {
    if (input == null) return false;
    // 白名单校验
    return input.matches("^[a-zA-Z0-9_]+$");
}

// 4. 最小权限原则
-- 数据库用户只授予必要权限
GRANT SELECT, INSERT, UPDATE, DELETE ON app_db.* TO 'app_user'@'%';

// 5. 错误信息处理
-- 不暴露数据库错误信息给用户
-- 记录详细日志供管理员查看
```

---

### Q16: 分库分表是什么？如何实现？

**题目类型**：技术原理类

**问题描述**：什么是分库分表？有哪些策略？如何实现？

**答案要点**：

**分库分表原因：**

| 问题 | 解决 |
|------|------|
| 单表数据量过亿 | 分表 |
| 单库并发瓶颈 | 分库 |
| 磁盘空间不足 | 分库 |
| 物理隔离 | 分库 |

**分片策略：**

```sql
-- 1. 垂直拆分 - 按业务拆分
-- 用户库: user, user_profile
-- 订单库: orders, order_items

-- 2. 水平拆分 - 按数据拆分
-- 按用户ID分表
-- user_0: ID % 4 == 0
-- user_1: ID % 4 == 1
-- user_2: ID % 4 == 2
-- user_3: ID % 4 == 3

-- 分片键选择原则
-- - 选择查询最频繁的字段
-- - 选择分布均匀的字段
-- - 避免跨分片查询
```

**分片中间件：**

| 中间件 | 特点 |
|--------|------|
| ShardingSphere-JDBC | 应用层分片，Java ORM框架 |
| ShardingSphere-Proxy | 数据库代理层 |
| MyCat | 基于MySQL Proxy |
| Vitess | YouTube开源 |
| TiDB | NewSQL，分布式SQL |

**分库分表后的问题：**

```sql
-- 1. 跨分片JOIN
-- 解决方案: 多次查询+应用层聚合

-- 2. 跨分片排序分页
-- 解决方案: ES搜索

-- 3. 分布式ID
-- 解决方案:
-- - UUID
-- - Snowflake算法
-- - 数据库号段
-- - Redis INCR

-- 4. 事务一致性
-- 解决方案:
-- - 分布式事务（Seata）
-- - 最终一致性
```

---

### Q17: 数据库主从复制是什么？如何配置？

**题目类型**：技术原理类

**问题描述**：MySQL主从复制是什么？原理是什么？如何配置？

**答案要点**：

**主从复制原理：**

```
┌─────────────────────────────────────────────────────────────┐
│                      主从复制架构                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────┐        ┌──────────┐        ┌──────────┐     │
│  │   主库   │ ──────▶│ Relay Log │ ──────▶│   从库   │     │
│  │ Master   │  Binlog │  Slave    │  Relay   │  Slave   │     │
│  └──────────┘        └──────────┘        └──────────┘     │
│       │                                            │       │
│       │              复制流程:                    │       │
│       │  1. Master写入数据，生成Binlog            │       │
│       │  2. Slave IO线程读取Binlog到Relay Log    │       │
│       │  3. Slave SQL线程重放Relay Log            │       │
│       │                                            │       │
└─────────────────────────────────────────────────────────────┘
```

**配置步骤：**

```ini
# 主库配置 my.cnf
[mysqld]
server-id = 1
log-bin = mysql-bin
binlog-format = ROW  # 推荐ROW模式
sync-binlog = 1
innodb_flush_log_at_trx_commit = 1

# 从库配置 my.cnf
[mysqld]
server-id = 2
relay-log = relay-bin
read-only = 1
replicate-do-db = app_db

# 创建复制账号
CREATE USER 'repl'@'%' IDENTIFIED BY 'password';
GRANT REPLICATION SLAVE ON *.* TO 'repl'@'%';

# 查看主库状态
SHOW MASTER STATUS;
```

```sql
-- 从库配置主从复制
CHANGE MASTER TO
    MASTER_HOST = 'master_host',
    MASTER_PORT = 3306,
    MASTER_USER = 'repl',
    MASTER_PASSWORD = 'password',
    MASTER_LOG_FILE = 'mysql-bin.000001',
    MASTER_LOG_POS = 1234;

-- 启动复制
START SLAVE;

-- 查看复制状态
SHOW SLAVE STATUS\G
-- 关键字段: Slave_IO_Running, Slave_SQL_Running
```

**主从复制模式：**

| 模式 | 说明 | 优点 | 缺点 |
|------|------|------|------|
| 异步复制 | 主库不等待从库 | 性能高 | 可能丢失数据 |
| 半同步复制 | 主库等待至少一个从库 | 数据安全 | 有延迟 |
| 全同步复制 | 主库等待所有从库 | 最安全 | 性能差 |

---

### Q18: 什么是读写分离？如何实现？

**题目类型**：场景解决类

**问题描述**：什么是读写分离？如何实现？有哪些注意事项？

**答案要点**：

**读写分离原理：**

```
┌─────────────────────────────────────────────────────────────┐
│                     读写分离架构                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐                                            │
│  │   应用层    │                                            │
│  └──────┬──────┘                                            │
│         │                                                   │
│    ┌────┴────┐                                             │
│    │ 路由层   │ ── SELECT ──▶ ┌──────────┐                │
│    │ (ShardingSphere/│        │   从库   │                │
│    │  AOP/中间件) │            │  Read-Only│                │
│    │              │ ── 其他 ──▶ │          │                │
│    │              │            │   主库   │                │
│    │              │            │ Read-Write│                │
│    └─────────────┘            └──────────┘                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**实现方式：**

```java
// 方式1: 注解+AOP
@Target(ElementType.METHOD)
@Retention(RetentionPolicy.RUNTIME)
public @interface ReadOnly {
}

// AOP切面
@Aspect
@Component
public class DataSourceAspect {
    @Around("@annotation(readOnly)")
    public Object switchDataSource(ProceedingJoinPoint point, ReadOnly readOnly) {
        DynamicDataSourceHolder.setReadOnly();
        try {
            return point.proceed();
        } finally {
            DynamicDataSourceHolder.clear();
        }
    }
}

// Service使用
@Service
public class UserService {
    @ReadOnly
    public User findById(Long id) {
        return userMapper.findById(id);  // 读从库
    }
    
    public void save(User user) {
        userMapper.insert(user);  // 写主库
    }
}

// 方式2: ShardingSphere
// 配置读写分离规则
// spring.shardingsphere.rules.readwrite-splitting配置
```

**注意事项：**

```sql
-- 1. 主从延迟问题
-- 解决方案:
-- - 强制读主库（重要数据）
-- - 延迟检查（半秒后再读从库）
-- - 缓存兜底

-- 2. 数据一致性
-- 使用事务确保读写都在主库
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
START TRANSACTION;
-- 写操作后立即读，可能读到旧数据

-- 3. 负载均衡
-- 从库间负载均衡
-- 使用Haproxy/Keepalived

-- 4. 故障转移
-- 主库故障时自动切换
-- 配置: gtid_mode + automatic_enforce_gtid_consistency
```

---

## 第三部分：高级特性（共4题）

### Q19: 什么是数据库连接池？有哪些常用连接池？

**题目类型**：基础概念类

**问题描述**：什么是数据库连接池？有哪些常用的连接池？如何配置？

**答案要点**：

**连接池原理：**

```
┌─────────────────────────────────────────────────────────────┐
│                      连接池原理                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  传统方式:                                                   │
│  应用 ────▶ 每请求创建连接 ────▶ 数据库 (性能差)             │
│                                                             │
│  连接池方式:                                                 │
│  应用 ────▶ 获取连接 ────▶ 使用 ────▶ 归还 ────▶ 复用      │
│            (从池中取)                        (回到池中)      │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                    连接池                              │   │
│  │  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐              │   │
│  │  │conn1 │ │conn2 │ │conn3 │ │conn4 │              │   │
│  │  └──────┘ └──────┘ └──────┘ └──────┘              │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**常用连接池对比：**

| 连接池 | 优点 | 缺点 |
|--------|------|------|
| Druid | 功能丰富，监控强 | 性能稍差 |
| HikariCP | 性能最好 | 功能相对少 |
| C3P0 | 早期方案 | 已过时 |

**Druid配置：**

```yaml
spring:
  datasource:
    driver-class-name: com.mysql.cj.jdbc.Driver
    url: jdbc:mysql://localhost:3306/app_db
    username: root
    password: password
    
    # Druid连接池配置
    druid:
      # 初始连接数
      initial-size: 5
      # 最大连接数
      max-active: 20
      # 最小空闲连接
      min-idle: 5
      # 获取连接最大等待时间(ms)
      max-wait: 60000
      # 连接泄漏检测
      remove-abandoned: true
      remove-abandoned-timeout: 300
      # 监控配置
      stat-view-servlet:
        enabled: true
        url-pattern: /druid/*
```

**HikariCP配置：**

```yaml
spring:
  datasource:
    hikari:
      # 连接池大小
      maximum-pool-size: 10
      minimum-idle: 5
      # 连接超时
      connection-timeout: 30000
      idle-timeout: 600000
      max-lifetime: 1800000
      # 连接测试
      connection-test-query: SELECT 1
```

---

### Q20: 如何进行数据库备份和恢复？

**题目类型**：场景解决类

**问题描述**：MySQL数据库如何备份和恢复？有哪些方式？

**答案要点**：

**备份方式对比：**

| 方式 | 原理 | 优点 | 缺点 |
|------|------|------|------|
| mysqldump | 逻辑备份，导出SQL | 跨平台，可恢复单表 | 恢复慢 |
| xtrabackup | 物理备份，复制文件 | 速度快，支持增量 | 恢复复杂 |
| binlog备份 | 增量备份binlog | 恢复点精确 | 需要配合全备 |
| 快照备份 | LVM/ZFS快照 | 毫秒级备份 | 需要LVM支持 |

**mysqldump使用：**

```bash
# 全量备份
mysqldump -h localhost -u root -p --all-databases > backup.sql

# 备份指定数据库
mysqldump -h localhost -u root -p app_db > app_db.sql

# 备份指定表
mysqldump -h localhost -u root -p app_db orders user > tables.sql

# 备份并压缩
mysqldump -h localhost -u root -p app_db | gzip > backup.sql.gz

# 备份结构(不含数据)
mysqldump -h localhost -u root -p --no-data app_db > structure.sql

# 恢复
mysql -h localhost -u root -p app_db < backup.sql

# 恢复压缩备份
gunzip < backup.sql.gz | mysql -h localhost -u root -p
```

**xtrabackup使用：**

```bash
# 全量备份
innobackupex --user=root --password=password /backup/

# 增量备份
innobackupex --user=root --password=password \
    --incremental /backup/inc1 \
    --incremental-basedir=/backup/2024-01-01_00-00-00

# 恢复
innobackupex --copy-back /backup/2024-01-01_00-00-00
```

**定时备份：**

```bash
# crontab配置
# 每天凌晨2点全量备份
0 2 * * * mysqldump -h localhost -u root -p'password' \
    app_db > /backup/app_db_$(date +\%Y\%m\%d).sql

# 每周日凌晨2点全量备份
0 2 * * 0 mysqldump -h localhost -u root -p'password' \
    --all-databases > /backup/full_$(date +\%Y\%m\%d).sql

# 保留最近30天备份
0 0 * * * find /backup -name "*.sql" -mtime +30 -delete
```

---

## 附录：知识点总结

**MySQL核心知识点：**

| 类别 | 关键知识点 |
|------|----------|
| 基础 | 架构、存储引擎、事务特性 |
| 索引 | B+树、聚簇索引、组合索引、最左前缀 |
| SQL优化 | EXPLAIN、慢查询、分页优化、JOIN优化 |
| 事务 | ACID、隔离级别、MVCC、锁机制 |
| 高可用 | 主从复制、读写分离、分库分表 |
| 运维 | 连接池、备份恢复、参数调优 |

**常用配置参数：**

```ini
[mysqld]
# 缓存大小
innodb_buffer_pool_size = 4G  # 建议内存的50-80%

# 连接数
max_connections = 1000

# 日志文件
innodb_log_file_size = 1G
innodb_log_files_in_group = 3

# 其他
slow_query_log = 1
long_query_time = 1
```

---

*本文档共计20道MySQL数据库面试题，涵盖基础概念、存储引擎、索引、事务、SQL优化等核心知识点。*
