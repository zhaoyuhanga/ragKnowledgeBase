# Redis 缓存面试题集

> 本文档包含 30 道 Redis 缓存相关的高频面试题，涵盖数据结构、持久化、集群、缓存策略等核心概念。所有答案均为中文，代码附有详细中文解释。

---

## 目录

1. [Redis 基础](#1-redis-基础)
2. [数据结构](#2-数据结构)
3. [持久化机制](#3-持久化机制)
4. [缓存策略](#4-缓存策略)
5. [高可用与集群](#5-高可用与集群)
6. [性能优化](#6-性能优化)
7. [项目实践](#7-项目实践)

---

## 1. Redis 基础

### Q1: Redis 是什么？它有哪些核心特点？

**参考答案：**

**Redis 简介：**
Redis（REmote DIctionary Server）是一个开源的、基于内存的键值存储数据库，常用作缓存、消息队列、分布式锁等场景。

**核心特点：**

| 特点 | 说明 |
|------|------|
| **内存存储** | 数据存储在内存中，读写速度极快 |
| **数据结构丰富** | String、Hash、List、Set、ZSet 等 |
| **持久化支持** | 支持 RDB 和 AOF 两种持久化方式 |
| **高可用** | 支持主从复制、哨兵、集群模式 |
| **单线程** | 单线程模型，避免锁竞争 |
| **原子操作** | 所有操作都是原子的 |
| **发布订阅** | 支持消息发布和订阅 |
| **Lua 脚本** | 支持执行 Lua 脚本，保证原子性 |

**应用场景：**

| 场景 | 使用的数据结构 | 说明 |
|------|--------------|------|
| 缓存热点数据 | String/Hash | 加速接口访问 |
| 会话存储 | String | 用户登录状态 |
| 实时排行榜 | ZSet | 游戏、电商排行 |
| 分布式锁 | String | 并发控制 |
| 消息队列 | List | 异步任务处理 |
| 分布式 Session | Hash | 多节点共享 |
| 限流控制 | String | API 限流 |

**项目中的应用：**

```python
# rag-qa-system/app/core/cache.py
import redis
from app.config import settings

# 初始化 Redis 连接
redis_client = redis.Redis(
    host=settings.redis_host,
    port=settings.redis_port,
    db=settings.redis_db,
    password=settings.redis_password or None,
    decode_responses=True  # 自动将 bytes 转为 str
)

# 基础操作
redis_client.set("key", "value")  # 设置键值
value = redis_client.get("key")     # 获取值

# 带过期时间
redis_client.setex("qa:question", 3600, "缓存内容")  # 1小时过期
```

---

### Q2: Redis 和 Memcached 有什么区别？

**参考答案：**

**核心区别对比：**

| 特性 | Redis | Memcached |
|------|-------|-----------|
| **数据结构** | 多种数据结构 | 仅 String |
| **持久化** | 支持 RDB/AOF | 不支持 |
| **主从复制** | 支持 | 不支持 |
| **集群** | 原生集群支持 | 无，需客户端实现 |
| **内存管理** | 多种淘汰策略 | LRU |
| **性能** | 单核最优 | 多核支持 |
| **存储形式** | 二进制安全 | 字符串 |
| **过期策略** | 惰性+定时 | 惰性删除 |
| **事务** | 支持 Lua 脚本 | 不支持 |
| **数据大小** | 最大 512MB | 最大 1MB |

**选择建议：**

| 场景 | 推荐 | 原因 |
|------|------|------|
| 复杂缓存需求 | Redis | 支持多种数据结构 |
| 简单 K-V 缓存 | 两者皆可 | Memcached 更简单 |
| 需要持久化 | Redis | 支持 RDB/AOF |
| 需要集群 | Redis | 原生支持 |
| 纯缓存、追求简单 | Memcached | 轻量级 |
| 高并发简单缓存 | Memcached | 多核支持更好 |

**项目中的选择：**
项目选择 Redis，因为需要：
1. 缓存问答结果（String）
2. 存储会话信息（Hash）
3. 使用 Redis 的过期和持久化功能

---

### Q3: Redis 的线程模型是什么？为什么单线程这么快？

**参考答案：**

**Redis 单线程模型：**

```
                    ┌─────────────────────────────┐
                    │        客户端请求            │
                    └─────────────────────────────┘
                                    │
                                    ▼
                    ┌─────────────────────────────┐
                    │        I/O 多路复用         │
                    │    (select/epoll/kqueue)    │
                    └─────────────────────────────┘
                                    │
                ┌────────────────────┼────────────────────┐
                ▼                    ▼                    ▼
        ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
        │   客户端 A    │    │   客户端 B    │    │   客户端 C    │
        └──────────────┘    └──────────────┘    └──────────────┘
                                │
                                ▼
                    ┌─────────────────────────────┐
                    │      命令处理器（单线程）     │
                    │                             │
                    │  GET/SET/DEL/HGET/...      │
                    └─────────────────────────────┘
                                │
                                ▼
                    ┌─────────────────────────────┐
                    │          内存存储            │
                    └─────────────────────────────┘
```

**为什么单线程这么快：**

| 原因 | 说明 |
|------|------|
| **内存操作** | 纯内存操作，速度快（纳秒级） |
| **无需锁** | 单线程无锁竞争，减少上下文切换 |
| **I/O 多路复用** | 单线程处理多客户端连接 |
| **高效数据结构** | C 语言实现的高效数据结构 |
| **非阻塞 I/O** | 基于事件驱动 |

**Redis 6.0 多线程：**

```bash
# Redis 6.0 引入 I/O 多线程
# 默认关闭，可手动开启
redis-server --io-threads 4

# 配置文件
io-threads 4
io-threads-do-reads yes
```

**多线程模式说明：**
- I/O 线程：处理网络读写
- 命令处理：仍为单线程
- 适用于高并发场景

---

### Q4: Redis 的过期策略和淘汰策略是什么？

**参考答案：**

**过期策略（Expiration）：**

| 策略 | 说明 |
|------|------|
| **惰性删除** | 访问 key 时检查是否过期，过期则删除 |
| **定时删除** | 每隔一段时间，扫描过期的 key 删除 |
| **定期删除** | 每隔一定时间，抽查一部分 key |

**Redis 过期策略实现：**

```python
# 惰性删除（Lazy Expiration）
# Redis 在访问 key 时检查是否过期
# 优点：对 CPU 友好
# 缺点：过期 key 可能长时间存在

# 定时删除（Active Expiration）
# 每隔一段时间，Redis 扫描过期的 key
# 配置：hz 参数控制扫描频率
# hz 10  # 每秒扫描 10 次
```

**内存淘汰策略（MaxMemory Policy）：**

| 策略 | 说明 |
|------|------|
| **noeviction** | 不淘汰，返回错误（默认） |
| **volatile-lru** | 在设置了过期时间的 key 中 LRU 淘汰 |
| **allkeys-lru** | 所有 key 中 LRU 淘汰 |
| **volatile-lfu** | 在设置了过期时间的 key 中 LFU 淘汰 |
| **allkeys-lfu** | 所有 key 中 LFU 淘汰 |
| **volatile-random** | 在设置了过期时间的 key 中随机淘汰 |
| **allkeys-random** | 所有 key 中随机淘汰 |
| **volatile-ttl** | 淘汰 TTL 最小的 key |

**配置淘汰策略：**

```bash
# 配置文件
maxmemory 2gb
maxmemory-policy allkeys-lru

# 命令行
redis-cli CONFIG SET maxmemory-policy allkeys-lru
```

**LRU/LFU 算法：**

```python
# LRU（Least Recently Used）- 最近最少使用
# 记录每个 key 的访问时间，淘汰最久未使用的

# LFU（Least Frequently Used）- 最不经常使用
# 记录每个 key 的访问频率，淘汰访问次数最少的
# 优点：更精确地识别热点数据
```

**项目中的过期设置：**

```python
# rag-qa-system/app/core/cache.py

# 问答缓存：1小时过期
redis_client.setex(f"qa:{question_hash}", 3600, json.dumps(cache_data))

# 配置项
# CACHE_DEFAULT_TTL = 3600
```

---

### Q5: Redis 的数据类型有哪些？各自的使用场景是什么？

**参考答案：**

**Redis 数据类型一览：**

| 类型 | 结构 | 典型场景 |
|------|------|----------|
| **String** | 字符串/数字/二进制 | 缓存、计数器、分布式锁 |
| **Hash** | 字段值对 | 对象存储、Session |
| **List** | 有序列表 | 消息队列、最新列表 |
| **Set** | 无序集合 | 标签、好友关系、去重 |
| **ZSet** | 有序集合 | 排行榜、权重队列 |
| **Bitmap** | 位图 | 签到、用户在线状态 |
| **HyperLogLog** | 基数统计 | UV 统计 |
| **Geospatial** | 地理位置 | 附近的人/店铺 |

**String 常用操作：**

```python
# 字符串操作
redis_client.set("name", "张三")
redis_client.get("name")  # "张三"

# 数字操作
redis_client.set("counter", 0)
redis_client.incr("counter")  # 1
redis_client.incrby("counter", 10)  # 11

# 设置过期时间
redis_client.setex("token", 3600, "abc123")

# 批量操作
redis_client.mset({"key1": "v1", "key2": "v2"})
redis_client.mget(["key1", "key2"])  # ["v1", "v2"]
```

**Hash 常用操作：**

```python
# 存储对象
redis_client.hset("user:1001", "name", "张三")
redis_client.hset("user:1001", "age", "25")
redis_client.hset("user:1001", mapping={"name": "张三", "age": 25})

# 获取字段
redis_client.hget("user:1001", "name")  # "张三"
redis_client.hgetall("user:1001")  # {"name": "张三", "age": "25"}

# 批量操作
redis_client.hmset("user:1002", {"name": "李四", "age": "30"})
redis_client.hmget("user:1002", ["name", "age"])  # ["李四", "30"]

# 计数器
redis_client.hincrby("stats:2024", "page_view", 1)
```

**List 常用操作：**

```python
# 添加元素
redis_client.lpush("queue:tasks", "task1")  # 左侧添加
redis_client.rpush("queue:tasks", "task2")   # 右侧添加

# 获取元素
redis_client.lrange("queue:tasks", 0, -1)  # 获取所有
redis_client.lpop("queue:tasks")  # 左侧弹出
redis_client.rpop("queue:tasks")  # 右侧弹出

# 阻塞操作（消息队列）
redis_client.blpop("queue:tasks", timeout=10)  # 阻塞等待
```

**Set 常用操作：**

```python
# 添加
redis_client.sadd("tags:doc:1001", "Python", "RAG", "AI")

# 获取
redis_client.smembers("tags:doc:1001")  # 所有成员
redis_client.scard("tags:doc:1001")  # 成员数量

# 判断
redis_client.sismember("tags:doc:1001", "Python")  # True

# 集合运算
redis_client.sinter("tags:1", "tags:2")  # 交集
redis_client.sunion("tags:1", "tags:2")  # 并集
redis_client.sdiff("tags:1", "tags:2")   # 差集
```

**ZSet 常用操作：**

```python
# 添加（带分数）
redis_client.zadd("leaderboard", {"Alice": 100, "Bob": 90, "Charlie": 95})

# 获取排名
redis_client.zrevrank("leaderboard", "Alice")  # 0（最高分排第1）
redis_client.zrank("leaderboard", "Bob")  # 1

# 获取分数
redis_client.zscore("leaderboard", "Alice")  # 100

# 获取 Top N
redis_client.zrevrange("leaderboard", 0, 9)  # 前10名
redis_client.zrevrange("leaderboard", 0, 9, withscores=True)  # 带分数
```

---

## 2. 数据结构

### Q6: Redis 的 String 类型底层是如何实现的？

**参考答案：**

**Redis Object 结构：**

```c
// Redis 对象结构
typedef struct redisObject {
    unsigned type:4;        // 类型（String/List/Hash/Set/ZSet）
    unsigned encoding:4;     // 编码方式
    unsigned lru:LRU_BITS;  // LRU 信息
    int refcount;           // 引用计数
    void *ptr;              // 指向数据结构的指针
} robj;
```

**String 类型的编码方式：**

| 编码 | 说明 | 条件 |
|------|------|------|
| **int** | 整数 | 存储的是整数且可用 long 表示 |
| **embstr** | 短字符串 | 字符串长度 <= 44 字节 |
| **raw** | 长字符串 | 字符串长度 > 44 字节 |

**编码转换示意：**

```
embstr（创建时）：
┌────────────────────────────┐
│  RedisObject │  sdshdr    │
│  (ptr指向)   │  (同一块)   │
└────────────────────────────┘
   优点：一次内存分配，内存连续

raw（超过44字节）：
┌──────────────┐    ┌──────────────────┐
│ RedisObject  │───▶│      sdshdr      │
│              │    │   (独立分配)     │
└──────────────┘    └──────────────────┘
   需要两次内存分配
```

**SDS（Simple Dynamic String）：**

```c
// SDS 结构
struct __attribute__ ((__packed__)) sdshdr8 {
    uint8_t len;         // 已使用长度
    uint8_t alloc;       // 总分配长度
    unsigned char flags;  // 类型标志
    char buf[];          // 柔性数组，存储实际字符串
};

// 优势：
// 1. O(1) 获取字符串长度
// 2. 避免缓冲区溢出
// 3. 减少修改时的内存重分配（空间预分配、惰性释放）
```

**常用命令时间复杂度：**

| 命令 | 时间复杂度 | 说明 |
|------|-----------|------|
| SET | O(1) | 设置值 |
| GET | O(1) | 获取值 |
| SETRANGE | O(N) | 范围修改 |
| GETRANGE | O(N) | 范围获取 |
| INCR | O(1) | 原子递增 |
| APPEND | O(1)* | 追加（均摊） |

---

### Q7: Redis 的 List 底层是如何实现的？

**参考答案：**

**List 的编码方式：**

| 编码 | 说明 | 条件 |
|------|------|------|
| **quicklist** | 压缩列表+双向链表 | 默认（Redis 3.2+） |
| **ziplist** | 压缩列表 | 元素少且短 |
| **linkedlist** | 双向链表 | 历史版本 |

**quicklist 结构：**

```
quicklist：
┌─────┬─────┬─────┬─────┬─────┬─────┐
│ QL  │zip1 │zip2 │zip3 │zip4 │zip5 │
└─────┴─────┴─────┴─────┴─────┴─────┘
  ↑
quicklistNode:
┌──────────┬──────────┬──────────┐
│   prev   │   next   │  ziplist │
└──────────┴──────────┴──────────┘

每个 ziplist 包含多个元素
ziplist 是连续的内存块
```

**ziplist 结构：**

```
ziplist：
┌─────────────────────────────────────────────┐
│  zlbytes  │  zltail  │  zllen  │  entries │
│  (4字节)  │  (4字节) │  (2字节) │  (N字节) │
└─────────────────────────────────────────────┘
  │
  ▼
┌──────┬──────┬──────┬──────┐
│prevlen│ encoding│ content │  ... │
│       │        │         │       │
└──────┴──────┴──────┴──────┘
```

**压缩列表特点：**

| 特点 | 说明 |
|------|------|
| 连续内存 | 所有元素存储在一块连续内存 |
| 节省空间 | 无需额外的指针开销 |
| 插入/删除 | O(N)，可能需要内存重分配 |
| 触发条件 | 元素数 < 64 且每项 < 64 字节 |

**List 常用命令复杂度：**

| 命令 | 时间复杂度 | 说明 |
|------|-----------|------|
| LPUSH/RPUSH | O(1) | 头部/尾部添加 |
| LPOP/RPOP | O(1) | 头部/尾部弹出 |
| LINDEX | O(N) | 按索引获取 |
| LRANGE | O(N) | 范围获取 |
| LINSERT | O(N) | 指定位置插入 |
| LTRIM | O(N) | 修剪列表 |

---

### Q8: Redis 的 Hash 底层是如何实现的？

**参考答案：**

**Hash 的编码方式：**

| 编码 | 说明 | 条件 |
|------|------|------|
| **ziplist** | 压缩列表 | field/value 数量少且短 |
| **hashtable** | 哈希表 | 元素较多时 |

**ziplist 存储格式：**

```
Hash 使用 ziplist 时：
key → [field1, value1, field2, value2, ...]

示例：
user:1001 → ["name", "张三", "age", "25", "city", "北京"]
```

**hashtable 结构：**

```
hashtable：
┌────────────────────────────────────────────────┐
│                    dict                        │
│  ┌─────────────────────────────────────────┐  │
│  │              dictht[0]                  │  │
│  │  ┌─────┬─────┬─────┬─────┬─────┬─────┐  │
│  │  │bucket│bucket│bucket│bucket│ ... │ NULL│  │
│  │  └──┬──┴──┬──┴──┬──┴──┬──┴─────┴─────┘  │
│  │     ▼     ▼     ▼     ▼                  │
│  │   [kv1] [kv2] [kv3] [kv4]               │
│  └─────────────────────────────────────────┘  │
│                                                │
│              渐进式 rehash                     │
│  ┌─────────────────────────────────────────┐  │
│  │              dictht[1]                  │  │
│  │   (扩展/收缩时启用，新旧buckets共存)     │  │
│  └─────────────────────────────────────────┘  │
└────────────────────────────────────────────────┘
```

**渐进式 Rehash：**

```python
# 渐进式 rehash 过程：
# 1. 分配新的 hashtable（旧表+1）
# 2. 定时/增量迁移数据
# 3. 迁移完成后释放旧表

# 触发 rehash 的条件：
# - 负载因子 > 1（扩展）
# - 负载因子 < 0.1（收缩）
# 负载因子 = 键数量 / bucket 数量
```

**Hash 常用命令复杂度：**

| 命令 | 时间复杂度 | 说明 |
|------|-----------|------|
| HSET | O(1) | 设置字段 |
| HGET | O(1) | 获取字段 |
| HGETALL | O(N) | 获取所有字段 |
| HMSET | O(N) | 批量设置 |
| HDEL | O(1) | 删除字段 |
| HEXISTS | O(1) | 字段是否存在 |
| HINCRBY | O(1) | 字段递增 |

---

### Q9: Redis 的 Set 和 ZSet 底层是如何实现的？

**参考答案：**

**Set 的编码方式：**

| 编码 | 说明 | 条件 |
|------|------|------|
| **intset** | 整数集合 | 全是整数且元素少 |
| **hashtable** | 哈希表 | 元素较多 |

**intset 结构：**

```c
typedef struct intset {
    uint32_t encoding;  // INTSET_ENC_INT16/32/64
    uint32_t length;    // 元素数量
    int8_t contents[];  // 实际存储（从小到大排序）
} intset;
```

**ZSet 的编码方式：**

| 编码 | 说明 | 条件 |
|------|------|------|
| **ziplist** | 压缩列表 | 元素少且短 |
| **skiplist+hashtable** | 跳表+哈希表 | 元素较多 |

**skiplist 结构：**

```
skiplist（跳跃表）：
Level 3:  ────────────────────────────────▶  NULL
              │                             
Level 2:  ─────▶[node5]──────────────────▶  NULL
              │       │        │            
Level 1:  ─▶[node2]──▶[node3]──▶[node5]──▶  NULL
              │       │        │        │    
Level 0:  ─▶[node1]──▶[node2]──▶[node3]──▶[node4]──▶[node5]──▶  NULL
             (score=1) (score=3) (score=5) (score=7) (score=9)

搜索：从高层向低层跳跃，快速定位
```

**跳表 + 哈希表双重结构：**

```python
# ZSet 同时使用两种数据结构：
# 1. skiplist：按分数排序，支持范围查询
# 2. hashtable：O(1) 查找 member 对应的分数

# 底层实现（Redis 源码简化）：
# typedef struct zset {
#     dict *dict;           // member → score 映射
#     zskiplist *zsl;      // 跳表，按分数排序
# } zset;
```

**常用命令复杂度：**

```python
# Set
redis_client.sadd("tags", "Python", "Java")  # O(N)，N 为添加数量
redis_client.sismember("tags", "Python")     # O(1)
redis_client.smembers("tags")                 # O(N)
redis_client.sinter("set1", "set2")         # O(N*M)

# ZSet
redis_client.zadd("rank", {"A": 100, "B": 90})  # O(log N)
redis_client.zrevrange("rank", 0, 9)              # O(log N + M)
redis_client.zscore("rank", "A")                  # O(1)
redis_client.zrank("rank", "A")                   # O(log N)
```

---

### Q10: 什么是 Redis 的 Pipeline？它有什么作用？

**参考答案：**

**Pipeline 概念：**
Pipeline 是 Redis 的一种优化机制，将多个命令打包发送，减少网络往返次数。

**普通模式 vs Pipeline 模式：**

```
普通模式（多次往返）：
客户端 ──▶ 命令1 ──▶ 等待响应 ──▶ 命令2 ──▶ 等待响应 ──▶ 命令3
           1ms RTT          1ms RTT          1ms RTT
        总耗时：3ms + 执行时间

Pipeline 模式（一次往返）：
客户端 ──▶ [命令1, 命令2, 命令3] ──▶ 批量响应
               1ms RTT
        总耗时：1ms + 执行时间
```

**使用示例：**

```python
import redis

client = redis.Redis()

# 普通方式（多次往返）
for i in range(100):
    client.set(f"key:{i}", f"value:{i}")

# Pipeline 方式（一次往返）
pipe = client.pipeline()
for i in range(100):
    pipe.set(f"key:{i}", f"value:{i}")
pipe.execute()  # 执行所有命令
```

**Pipeline 使用场景：**

| 场景 | 说明 |
|------|------|
| 批量写入 | 批量插入数据 |
| 批量读取 | 批量获取多个 key |
| 批量操作 | 需要原子性的批量操作 |
| 性能优化 | 减少网络延迟影响 |

**事务 vs Pipeline：**

| 特性 | Pipeline | Transaction (MULTI/EXEC) |
|------|---------|------------------------|
| 原子性 | 否 | 是 |
| 错误处理 | 无回滚 | 可回滚 |
| 网络开销 | 一次往返 | 两次往返（QUEUED + EXEC） |
| 使用场景 | 性能优化 | 原子性保证 |

**项目中的应用：**

```python
# 批量设置问答缓存
pipe = redis_client.pipeline()
for qa_data in qa_batch:
    cache_key = f"qa:{hashlib.md5(qa_data['question'].encode()).hexdigest()}"
    pipe.setex(cache_key, 3600, json.dumps(qa_data))
pipe.execute()
```

---

## 3. 持久化机制

### Q11: Redis 的持久化方式有哪些？各有优缺点？

**参考答案：**

**RDB vs AOF 对比：**

| 特性 | RDB | AOF |
|------|-----|-----|
| **方式** | 快照 | 日志 |
| **文件大小** | 小（紧凑） | 大（持续追加） |
| **恢复速度** | 快 | 慢 |
| **数据安全性** | 可能有丢失 | 可配置（everysec/always） |
| **对性能影响** | 阻塞/后台 fork | 持续写入 |
| **恢复完整性** | 可能丢失数据 | 更完整 |
| **文件格式** | 二进制 | 文本 |

**RDB（Redis Database）快照：**

```bash
# 配置
save 900 1      # 900秒内至少1个key变化
save 300 100    # 300秒内至少100个key变化
save 60 10000   # 60秒内至少10000个key变化

# 手动触发
redis-cli SAVE        # 同步（阻塞）
redis-cli BGSAVE      # 后台异步

# 文件
dump.rdb
```

**RDB 流程：**

```c
// BGSAVE 执行流程：
// 1. fork 子进程（COW 开始）
// 2. 子进程遍历内存，写入 RDB 文件
// 3. 完成后通知主进程
// 4. 主进程继续服务
```

**AOF（Append Only File）追加日志：**

```bash
# 配置
appendonly yes
appendfilename "appendonly.aof"

# 同步策略
appendfsync always    # 每次写命令都同步（最安全，最慢）
appendfsync everysec  # 每秒同步（推荐）
appendfsync no        # 由系统决定（最快，可能丢数据）

# 重写机制
auto-aof-rewrite-percentage 100  # 文件大小增长100%时重写
auto-aof-rewrite-min-size 64mb  # 文件大于64MB时可能重写
```

**AOF 重写：**

```bash
# AOF 重写过程：
# 1. fork 子进程
# 2. 子进程遍历内存，生成新的 AOF 文件
# 3. 父进程接收新的写命令，缓存起来
# 4. 子进程重写完成后，父进程将缓存追加到新文件
# 5. 原子性替换为新的 AOF 文件
```

**推荐配置（混合持久化）：**

```bash
# 开启混合持久化
aof-use-rdb-preamble yes

# 优势：
# - AOF 重写时使用 RDB 格式开头
# - 恢复时先加载 RDB，再应用增量 AOF
# - 结合两者优点
```

---

### Q12: Redis 的 RDB 持久化是如何工作的？

**参考答案：**

**RDB 触发条件：**

| 触发方式 | 说明 |
|----------|------|
| 自动触发 | 满足配置文件中的 save 条件 |
| BGSAVE | 后台异步保存（redis-cli BGSAVE） |
| SAVE | 同步保存（阻塞，不推荐） |
| SHUTDOWN | 服务器关闭时自动执行 |
| 主从复制 | 从节点全量同步 |

**COW（Copy-On-Write）机制：**

```
fork 时：
┌─────────────────────────────────────┐
│             主进程内存                │
│  ┌─────────────────────────────┐    │
│  │        共享页（只读）        │    │
│  └─────────────────────────────┘    │
└─────────────────────────────────────┘

fork 后：
┌──────────────────┐  ┌──────────────────┐
│      主进程       │  │      子进程       │
│  ┌────────────┐  │  │  ┌────────────┐  │
│  │ 私有页(COW)│  │  │  │ 私有页(COW)│  │
│  └────────────┘  │  │  └────────────┘  │
└──────────────────┘  └──────────────────┘
         ↑                    ↑
         └────────────────────┘
           最初指向同一物理页

修改时：
┌──────────────────┐  ┌──────────────────┐
│      主进程       │  │      子进程       │
│  ┌────────────┐  │  │  ┌────────────┐  │
│  │ 新分配页   │  │  │  │ 继续共享    │  │
│  └────────────┘  │  │  └────────────┘  │
└──────────────────┘  └──────────────────┘
```

**RDB 文件格式：**

```
RDB 文件结构：
┌────────────────────────────────────────────────────┐
│  REDIS  │  db_version  │  EOF  │  checksum        │
│  (5字节) │  (4字节)    │ (1字节)│ (8字节)        │
└────────────────────────────────────────────────────┘
                          │
                          ▼
                    ┌─────────────────┐
                    │  SELECTDB 标志   │
                    │  数据库编号       │
                    └─────────────────┘
                          │
                          ▼
                    ┌─────────────────┐
                    │  RESIZEDB 标志   │
                    │  hash大小/过期大小│
                    └─────────────────┘
                          │
                          ▼
┌────────────────────────────────────────────────────┐
│  key_value_pair:                                  │
│  ┌──────────┬──────────────┬───────────────────┐  │
│  │过期时间  │  key        │  value            │  │
│  │(可选)   │  (type编码)  │  (根据类型编码)    │  │
│  └──────────┴──────────────┴───────────────────┘  │
└────────────────────────────────────────────────────┘
```

**优缺点分析：**

| 优点 | 缺点 |
|------|------|
| 文件紧凑，适合备份 | 可能丢失最后一次快照后的数据 |
| 恢复速度快 | fork 时可能阻塞（大数据量） |
| 适合灾难恢复 | 文件格式复杂，不易修改 |

---

### Q13: Redis 的 AOF 持久化是如何工作的？

**参考答案：**

**AOF 写入流程：**

```
客户端命令
    │
    ▼
┌─────────────────────────────────────────────────┐
│                  主进程                          │
│  ┌─────────────────────────────────────────┐   │
│  │            aof_buf 缓冲区                 │   │
│  │    [命令1][命令2][命令3]...              │   │
│  └─────────────────────────────────────────┘   │
│                      │                          │
│         ┌────────────┼────────────┐            │
│         ▼            ▼            ▼            │
│    ┌─────────┐  ┌─────────┐  ┌─────────┐    │
│    │always   │  │everysec │  │   no    │    │
│    │ 同步    │  │ 同步    │  │  不同步  │    │
│    └────┬────┘  └────┬────┘  └─────────┘    │
└─────────┼─────────────┼────────────────────────┘
          │             │
          ▼             ▼
    ┌─────────────────────────┐
    │      aof 文件          │
    │  *3\r\n$3\r\nSET\r\n  │
    │  $5\r\nhello\r\n      │
    │  $5\r\nworld\r\n      │
    └─────────────────────────┘
```

**AOF 重写机制：**

```bash
# 手动重写
redis-cli BGREWRITEAOF

# 自动重写条件（满足其一）
# 1. 文件大小比上次重写后增长 100%
# 2. 文件大小大于配置的最小值
auto-aof-rewrite-percentage 100
auto-aof-rewrite-min-size 64mb
```

**AOF 重写流程：**

```
1. fork 子进程
         │
         ▼
2. 子进程遍历内存，生成新 AOF 文件
         │
         ▼
3. 父进程接收新命令，存入 aof_rewrite_buf
         │
         ▼
4. 子进程完成，通知父进程
         │
         ▼
5. 父进程将 aof_rewrite_buf 追加到新文件
         │
         ▼
6. 原子性替换为新 AOF 文件
```

**AOF 优缺点：**

| 优点 | 缺点 |
|------|------|
| 数据安全性更高 | 文件比 RDB 大 |
| 同步策略灵活 | 恢复速度较慢 |
| 易于理解和修改 | 可能对性能产生影响 |

**AOF 格式示例：**

```
*3\r\n                    # 数组，3个元素
$3\r\nSET\r\n            # 字符串 "SET"
$5\r\nhello\r\n          # 字符串 "hello"
$5\r\nworld\r\n          # 字符串 "world"

*5\r\n                    # LPUSH
$6\r\nmylist\r\n
$1\r\na\r\n
$1\r\nb\r\n
$1\r\nc\r\n
```

---

### Q14: Redis 如何处理数据持久化与性能的关系？

**参考答案：**

**性能与安全的权衡：**

```bash
# appendfsync 选项
appendfsync always    # 每次写都同步，最安全但最慢
appendfsync everysec  # 每秒同步，推荐（最多丢1秒数据）
appendfsync no        # 由系统决定，最快（可能丢较多数据）
```

**生产环境推荐配置：**

```bash
# RDB 配置
save 900 1
save 300 100
save 60 10000
stop-writes-on-bgsave-error yes  # BGSAVE 失败时停止写入
rdbcompression yes                # 压缩 RDB 文件
rdbchecksum yes                  # 校验 RDB 文件

# AOF 配置
appendonly yes
appendfsync everysec
no-appendfsync-on-rewrite yes    # 重写时不阻塞
auto-aof-rewrite-percentage 100
auto-aof-rewrite-min-size 64mb
aof-load-truncated yes           # 加载截断的 AOF
aof-use-rdb-preamble yes        # 混合持久化
```

**性能优化技巧：**

```python
# 1. 使用 Pipeline 减少命令数量
pipe = redis_client.pipeline()
for cmd in commands:
    pipe.execute_command(*cmd)
pipe.execute()

# 2. 使用 Lua 脚本原子执行
script = """
local key = KEYS[1]
local value = ARGV[1]
local exists = redis.call('EXISTS', key)
if exists == 1 then
    return 0
else
    redis.call('SET', key, value)
    return 1
end
"""
redis_client.eval(script, 1, "mykey", "value")

# 3. 使用批量操作
redis_client.mset({f"key:{i}": f"value:{i}" for i in range(100)})
```

**监控持久化状态：**

```python
# 查看持久化状态
info = redis_client.info("persistence")
print(f"RDB: {info['rdb_changes_since_last_save']}")
print(f"AOF: {info['aof_current_size']}")
print(f"AOF 重写: {info['aof_rewrite_in_progress']}")
```

---

## 4. 缓存策略

### Q15: 如何设计一个缓存策略？

**参考答案：**

**缓存架构设计：**

```
请求
  │
  ▼
┌──────────────┐
│   缓存层      │
│  (Redis)     │
└──────────────┘
  │命中
  │     │未命中
  ▼     ▼
返回   查询数据库
        │
        ▼
    写入缓存
        │
        ▼
     返回结果
```

**缓存策略模式：**

| 模式 | 说明 | 适用场景 |
|------|------|----------|
| Cache-Aside | 应用自行管理缓存 | 读多写少 |
| Read-Through | 缓存自动加载 | 简化应用逻辑 |
| Write-Through | 写缓存+数据库 | 数据一致性要求高 |
| Write-Behind | 异步写数据库 | 写入性能要求高 |

**Cache-Aside（旁路缓存）：**

```python
# 读操作
def get_user(user_id):
    # 1. 先查缓存
    cache_key = f"user:{user_id}"
    user = redis_client.get(cache_key)
    
    if user:
        return json.loads(user)  # 缓存命中
    
    # 2. 缓存未命中，查询数据库
    user = db.query(User).get(user_id)
    
    if user:
        # 3. 写入缓存
        redis_client.setex(cache_key, 3600, json.dumps(user))
    
    return user

# 写操作
def update_user(user_id, data):
    # 1. 更新数据库
    db.query(User).filter(User.id == user_id).update(data)
    db.commit()
    
    # 2. 删除缓存（而非更新）
    redis_client.delete(f"user:{user_id}")
```

**缓存问题处理：**

```python
# 1. 缓存穿透：布隆过滤器或空值缓存
def get_with_cache(query):
    cache_key = f"query:{hash(query)}"
    result = redis_client.get(cache_key)
    
    if result == "NULL":  # 空值缓存
        return None
    
    if result:
        return json.loads(result)
    
    # 查询数据库
    result = db.query(query)
    
    if result is None:
        redis_client.setex(cache_key, 60, "NULL")  # 缓存空值
    else:
        redis_client.setex(cache_key, 3600, json.dumps(result))
    
    return result

# 2. 缓存击穿：互斥锁或永不过期+异步更新
def get_with_lock(key):
    value = redis_client.get(key)
    if value:
        return value
    
    # 获取锁
    lock_key = f"lock:{key}"
    lock = redis_client.set(lock_key, "1", nx=True, ex=10)
    
    if lock:
        # 加载数据
        value = load_from_db(key)
        redis_client.setex(key, 3600, json.dumps(value))
        redis_client.delete(lock_key)
        return value
    
    # 等待后重试
    time.sleep(0.1)
    return get_with_lock(key)

# 3. 缓存雪崩：过期时间随机化 + 多级缓存
def set_with_random_ttl(key, value):
    ttl = 3600 + random.randint(0, 600)  # 1小时 ± 10分钟
    redis_client.setex(key, ttl, json.dumps(value))
```

**项目中的缓存策略：**

```python
# rag-qa-system/app/core/cache.py
def get_qa_cache(self, question: str) -> Optional[dict]:
    """获取问答缓存"""
    cache_key = f"qa:{hashlib.md5(question.encode()).hexdigest()}"
    cached = self.get(cache_key)
    return json.loads(cached) if cached else None

def set_qa_cache(self, question: str, answer: str, sources: list):
    """设置问答缓存"""
    cache_key = f"qa:{hashlib.md5(question.encode()).hexdigest()}"
    value = {"answer": answer, "sources": sources}
    self.set(cache_key, value, ttl=3600)
```

---

### Q16: 什么是缓存穿透？如何解决？

**参考答案：**

**缓存穿透定义：**
缓存穿透是指查询一个不存在的数据，由于缓存和数据库都没有，每次请求都会打到数据库。

**危害：**
- 大量无效请求打到数据库
- 数据库压力剧增
- 可能导致数据库宕机

**解决方案：**

```python
# 方案1：空值缓存
# 缓存空值，短时间内避免重复查询

def get_user(user_id):
    cache_key = f"user:{user_id}"
    
    # 查询缓存
    cached = redis_client.get(cache_key)
    
    if cached == "NULL_VALUE":  # 空值标记
        return None
    
    if cached:
        return json.loads(cached)
    
    # 查询数据库
    user = db.query(User).get(user_id)
    
    if user:
        redis_client.setex(cache_key, 3600, json.dumps(user))
    else:
        # 缓存空值（短过期时间）
        redis_client.setex(cache_key, 300, "NULL_VALUE")
    
    return user

# 方案2：布隆过滤器
# 使用布隆过滤器判断数据是否存在

from bloom_filter import BloomFilter

bloom = BloomFilter(max_elements=10000, error_rate=0.1)

def init_bloom():
    """初始化布隆过滤器"""
    for user in db.query(User).all():
        bloom.add(f"user:{user.id}")

def get_user_with_bloom(user_id):
    key = f"user:{user_id}"
    
    # 布隆过滤器判断
    if key not in bloom:
        return None  # 一定不存在
    
    # 可能存在，继续查缓存和数据库
    cached = redis_client.get(key)
    if cached:
        return json.loads(cached)
    
    user = db.query(User).get(user_id)
    if user:
        redis_client.setex(key, 3600, json.dumps(user))
    
    return user

# 方案3：参数校验
def get_user(user_id):
    # 参数校验
    if not user_id or not isinstance(user_id, int):
        raise ValueError("Invalid user_id")
    
    # 继续查询...
```

**布隆过滤器原理：**

```
┌────────────────────────────────────────────────────────┐
│              布隆过滤器                                  │
│                                                        │
│   原始数据 ──▶ Hash1 ──▶ 位置1 ──▶ [1][0][1][0][1]    │
│              ──▶ Hash2 ──▶ 位置3 ──▶                  │
│              ──▶ Hash3 ──▶ 位置5 ──▶                  │
│                                                        │
│   查询：计算 Hash1/2/3，若全为1则可能存在，否则一定不存在  │
│                                                        │
│   优点：空间效率高，查询快                              │
│   缺点：可能有误判（假阳性），不能删除                  │
└────────────────────────────────────────────────────────┘
```

---

### Q17: 什么是缓存击穿？如何解决？

**参考答案：**

**缓存击穿定义：**
缓存击穿是指某个热点 key 过期时，大量并发请求同时打到数据库。

**危害：**
- 数据库压力瞬间增大
- 可能压垮数据库
- 服务响应变慢或不可用

**解决方案：**

```python
# 方案1：互斥锁（Mutex）
# 确保只有一个请求去加载数据

import threading

def get_with_mutex(key):
    """使用互斥锁获取数据"""
    # 尝试获取锁
    lock_key = f"lock:{key}"
    lock_acquired = redis_client.set(
        lock_key, "1", nx=True, ex=10  # 10秒过期
    )
    
    if lock_acquired:
        try:
            # 获取到锁，加载数据
            result = load_from_db(key)
            redis_client.setex(key, 3600, json.dumps(result))
            return result
        finally:
            redis_client.delete(lock_key)
    else:
        # 未获取到锁，等待后重试
        time.sleep(0.1)
        cached = redis_client.get(key)
        if cached:
            return json.loads(cached)
        return get_with_mutex(key)  # 递归重试

# 方案2：永不过期 + 异步更新
# 给缓存加一个"数据版本号"，异步更新

def get_with_version(key):
    """使用版本号获取数据"""
    # 获取数据
    data = redis_client.get(key)
    if data:
        return json.loads(data)
    
    # 数据不存在，使用旧数据或空值
    # 触发异步更新
    trigger_async_update(key)
    
    return None

def trigger_async_update(key):
    """异步更新缓存"""
    import threading
    def update():
        result = load_from_db(key)
        redis_client.setex(key, 3600, json.dumps(result))
    
    threading.Thread(target=update).start()

# 方案3：逻辑过期
# 缓存数据带过期时间字段，但实际不删除

def get_with_logic_expire(key):
    """逻辑过期策略"""
    data = redis_client.get(key)
    if not data:
        # 缓存不存在，查询数据库
        result = load_from_db(key)
        redis_client.setex(key, 3600, json.dumps(result))
        return result
    
    data = json.loads(data)
    
    # 检查逻辑过期
    if data.get("expire_at", 0) < time.time():
        # 已逻辑过期，异步更新
        trigger_async_update(key)
    
    return data.get("value")

# 方案4：双层缓存
# L1 本地缓存 + L2 Redis

from functools import lru_cache

class TwoLevelCache:
    def __init__(self):
        self.local_cache = {}  # L1 本地缓存
    
    def get(self, key):
        # L1 命中
        if key in self.local_cache:
            return self.local_cache[key]
        
        # L2 查询
        data = redis_client.get(key)
        if data:
            data = json.loads(data)
            self.local_cache[key] = data
            return data
        
        # 加载数据
        data = load_from_db(key)
        redis_client.setex(key, 3600, json.dumps(data))
        self.local_cache[key] = data
        return data
```

---

### Q18: 什么是缓存雪崩？如何解决？

**参考答案：**

**缓存雪崩定义：**
缓存雪崩是指大量缓存 key 在同一时间过期，导致大量请求同时打到数据库。

**危害：**
- 数据库压力剧增
- 可能导致数据库宕机
- 服务不可用

**解决方案：**

```python
# 方案1：过期时间随机化
# 给缓存过期时间加随机值

def set_with_random_expire(key, value, base_ttl=3600):
    """设置随机过期时间"""
    ttl = base_ttl + random.randint(0, 600)  # ±10分钟
    redis_client.setex(key, ttl, json.dumps(value))

# 查询时
def get_user(user_id):
    cache_key = f"user:{user_id}"
    cached = redis_client.get(cache_key)
    
    if cached:
        return json.loads(cached)
    
    user = db.query(User).get(user_id)
    if user:
        # 使用随机过期时间
        set_with_random_expire(cache_key, user, 3600)
    
    return user

# 方案2：多级缓存
# L1 本地缓存 + L2 Redis + L3 数据库

class MultiLevelCache:
    def __init__(self):
        self.l1_cache = {}  # 本地缓存（永不过期或长过期）
        self.l2_ttl = 3600  # Redis TTL
    
    def get(self, key):
        # L1 查询
        if key in self.l1_cache:
            return self.l1_cache[key]
        
        # L2 查询
        cached = redis_client.get(key)
        if cached:
            data = json.loads(cached)
            self.l1_cache[key] = data  # 回填 L1
            return data
        
        # L3 查询
        data = load_from_db(key)
        if data:
            redis_client.setex(key, self.l2_ttl, json.dumps(data))
            self.l1_cache[key] = data
        
        return data

# 方案3：热点数据永不过期
# 热点数据设置很长的过期时间，异步更新

def set_hot_cache(key, value):
    """热点数据永不过期"""
    redis_client.set(key, json.dumps(value))

def update_hot_cache(key):
    """异步更新热点缓存"""
    import threading
    def update():
        value = load_from_db(key)
        redis_client.set(key, json.dumps(value))
    threading.Thread(target=update).start()

# 方案4：服务降级
# 数据库压力大时，返回默认值或友好提示

def get_with_fallback(key, fallback_data=None):
    """带降级策略的获取"""
    try:
        cached = redis_client.get(key)
        if cached:
            return json.loads(cached)
        
        data = load_from_db(key)
        redis_client.setex(key, 3600, json.dumps(data))
        return data
    except Exception as e:
        logger.error(f"Cache error: {e}")
        return fallback_data  # 降级返回

# 方案5：请求限流
# 使用 Redis 实现请求限流

def rate_limit(user_id, max_requests=100, window=60):
    """请求限流"""
    key = f"rate:{user_id}"
    
    current = redis_client.incr(key)
    if current == 1:
        redis_client.expire(key, window)
    
    return current <= max_requests

def get_user(user_id):
    if not rate_limit(user_id):
        return {"error": "请求过于频繁"}
    
    return get_with_cache(user_id)
```

---

### Q19: 如何实现分布式锁？

**参考答案：**

**分布式锁要求：**

| 要求 | 说明 |
|------|------|
| 互斥性 | 同一时刻只有一个客户端能获取锁 |
| 死锁避免 | 锁要能自动释放，防止死锁 |
| 可重入 | 同一客户端可多次获取同一锁 |
| 高性能 | 加锁/解锁要快 |
| 高可用 | 分布式环境下稳定 |

**Redis 实现分布式锁：**

```python
import time
import uuid

class DistributedLock:
    def __init__(self, redis_client):
        self.redis = redis_client
        self.lock_key = None
        self.lock_value = None
    
    def acquire(self, key, timeout=10):
        """
        获取锁
        key: 锁名称
        timeout: 锁过期时间（秒）
        返回: 是否成功获取
        """
        self.lock_key = f"lock:{key}"
        self.lock_value = str(uuid.uuid4())  # 唯一标识
        
        # SET NX EX 原子操作
        result = self.redis.set(
            self.lock_key,
            self.lock_value,
            nx=True,  # 只有不存在时设置
            ex=timeout  # 过期时间
        )
        return bool(result)
    
    def release(self):
        """释放锁"""
        if not self.lock_key or not self.lock_value:
            return False
        
        # Lua 脚本保证原子性（只有持有者才能释放）
        script = """
        if redis.call("get", KEYS[1]) == ARGV[1] then
            return redis.call("del", KEYS[1])
        else
            return 0
        end
        """
        result = self.redis.eval(script, 1, self.lock_key, self.lock_value)
        return bool(result)
    
    def extend(self, timeout=None):
        """延长锁的过期时间"""
        if not self.lock_key or not self.lock_value:
            return False
        
        script = """
        if redis.call("get", KEYS[1]) == ARGV[1] then
            return redis.call("expire", KEYS[1], ARGV[2])
        else
            return 0
        end
        """
        timeout = timeout or 10
        result = self.redis.eval(script, 1, self.lock_key, self.lock_value, timeout)
        return bool(result)
    
    def __enter__(self):
        if not self.acquire(self.lock_key.replace("lock:", "")):
            raise TimeoutError("获取锁失败")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()
        return False

# 使用上下文管理器
lock = DistributedLock(redis_client)
try:
    lock.acquire("document:123:process")
    # 临界区代码
    process_document(123)
finally:
    lock.release()

# 或者使用 with 语句
with DistributedLock(redis_client) as lock:
    lock.lock_key = "document:123:process"
    process_document(123)
```

**RedLock 算法（多节点分布式锁）：**

```python
import time

class RedLock:
    """RedLock 多节点分布式锁"""
    
    def __init__(self, redis_clients: list):
        self.clients = redis_clients
        self.quorum = len(redis_clients) // 2 + 1
    
    def lock(self, resource, ttl=10000):
        """
        获取 RedLock
        ttl: 锁过期时间（毫秒）
        """
        ttl = int(ttl)
        
        def get_unique_id():
            return str(uuid.uuid4())
        
        token = get_unique_id()
        acquired = 0
        
        # 获取所有节点的锁
        for client in self.clients:
            try:
                if client.set(resource, token, nx=True, px=ttl):
                    acquired += 1
            except:
                pass
        
        # 超过半数节点获取成功
        return acquired >= self.quorum, token
    
    def unlock(self, resource, token):
        """释放 RedLock"""
        for client in self.clients:
            try:
                script = """
                if redis.call("get", KEYS[1]) == ARGV[1] then
                    return redis.call("del", KEYS[1])
                else
                    return 0
                end
                """
                client.eval(script, 1, resource, token)
            except:
                pass
```

---

### Q20: Redis 如何实现消息队列？

**参考答案：**

**Redis 消息队列对比：**

| 特性 | List | Pub/Sub | Stream |
|------|------|---------|--------|
| 持久化 | 支持 | 不支持 | 支持 |
| 消费者组 | 不支持 | 不支持 | 支持 |
| 消息确认 | 不支持 | 不支持 | 支持 |
| 广播 | 不支持 | 支持 | 支持 |
| 顺序性 | FIFO | 无保证 | 可保证 |
| 消息回溯 | 不支持 | 不支持 | 支持 |

**基于 List 的队列：**

```python
# 生产者
def enqueue(queue_name, message):
    """入队"""
    redis_client.rpush(queue_name, json.dumps(message))

# 消费者
def dequeue(queue_name, timeout=0):
    """出队"""
    if timeout > 0:
        result = redis_client.blpop(queue_name, timeout=timeout)
        if result:
            _, message = result
            return json.loads(message)
    else:
        message = redis_client.lpop(queue_name)
        return json.loads(message) if message else None

# 使用示例
enqueue("tasks", {"task_id": 1, "action": "process"})
task = dequeue("tasks", timeout=10)
```

**基于 Pub/Sub 的发布订阅：**

```python
# 发布者
def publish(channel, message):
    redis_client.publish(channel, json.dumps(message))

# 订阅者
def subscribe(channel):
    pubsub = redis_client.pubsub()
    pubsub.subscribe(channel)
    
    for message in pubsub.listen():
        if message["type"] == "message":
            data = json.loads(message["data"])
            process(data)

# 使用
publish("notifications", {"user_id": 1, "msg": "新消息"})
subscribe("notifications")
```

**基于 Stream 的消息队列（推荐）：**

```python
# 生产者
def add_to_stream(stream_name, data):
    """添加消息到 Stream"""
    return redis_client.xadd(stream_name, data)

# 消费者组
def create_consumer_group(stream_name, group_name):
    """创建消费者组"""
    try:
        redis_client.xgroup_create(stream_name, group_name, id="0")
    except:
        pass  # 组已存在

def consume_messages(stream_name, group_name, consumer_name):
    """消费消息"""
    # 读取新消息
    messages = redis_client.xreadgroup(
        group_name,
        consumer_name,
        {stream_name: ">"},  # 只读新消息
        count=10,
        block=5000  # 阻塞等待
    )
    
    for stream, msgs in messages or []:
        for msg_id, data in msgs:
            yield msg_id, data

def ack_message(stream_name, group_name, msg_id):
    """确认消息"""
    redis_client.xack(stream_name, group_name, msg_id)

# 使用示例
STREAM = "qa:tasks"
GROUP = "qa:workers"
CONSUMER = "worker-1"

create_consumer_group(STREAM, GROUP)

for msg_id, data in consume_messages(STREAM, GROUP, CONSUMER):
    try:
        process_task(data)
        ack_message(STREAM, GROUP, msg_id)
    except Exception as e:
        print(f"处理失败: {e}")
```

**Stream 命令详解：**

```bash
# Stream 基本操作
XADD stream_name * field1 value1  # 添加消息（自动ID）
XLEN stream_name                  # 长度
XRANGE stream_name - +           # 范围查询
XREAD STREAMS stream_name $       # 读取新消息

# 消费者组
XGROUP CREATE stream_name group 0  # 创建消费者组
XREADGROUP GROUP group consumer STREAMS stream_name ">"  # 读取新消息
XACK stream_name group msg_id     # 确认消息
XPENDING stream_name group       # 待确认消息
```

---

## 5. 高可用与集群

### Q21: Redis 主从复制是如何工作的？

**参考答案：**

**主从复制流程：**

```
┌─────────────┐                    ┌─────────────┐
│    Master   │                    │    Slave    │
└─────────────┘                    └─────────────┘
      │                                    │
      │  1. SYNC / PSYNC                   │
      │◀───────────────────────────────────│
      │                                    │
      │  2. RDB 快照                       │
      │───────────────────────────────────▶│
      │    (主节点 fork 后台生成)           │
      │                                    │
      │  3. 缓存区命令                     │
      │───────────────────────────────────▶│
      │    (生成 RDB 期间的写命令)         │
      │                                    │
      │  4. 增量同步                       │
      │◀───────────────────────────────────│
      │    (主节点主动推送)                │
```

**复制配置：**

```bash
# 从节点配置
replicaof master_host master_port

# 或命令
redis-cli replicaof master_host master_port

# 取消复制
redis-cli replicaof no one
```

**复制的类型：**

| 类型 | 说明 |
|------|------|
| **全量复制** | 首次同步时，发送完整 RDB 快照 |
| **增量复制** | 断线重连后，发送部分同步 |
| **命令传播** | 正常运行时，持续推送写命令 |

**PSYNC 机制：**

```bash
# PSYNC 参数
# PSYNC <runid> <offset>
# runid: 主节点运行ID
# offset: 从节点已处理的偏移量

# 1. 首次同步：
#    从节点发送 PSYNC ? -1
#    主节点返回 +FULLRESYNC <runid> <offset>

# 2. 增量同步：
#    从节点发送 PSYNC <runid> <offset>
#    主节点返回 +CONTINUE <offset>
```

**复制延迟问题：**

```python
# 检查复制延迟
info = redis_client.info("replication")
print(f"主从延迟: {info.get('master_repl_offset', 0)}")

# 在主节点设置
redis_client.config_set(" repl-diskless-sync", "yes")  # 无盘复制
redis_client.config_set("repl-diskless-sync-delay", 5)  # 延迟等待更多从节点
```

---

### Q22: Redis Sentinel（哨兵）是如何工作的？

**参考答案：**

**哨兵架构：**

```
                    ┌─────────────────────────┐
                    │    应用客户端           │
                    └───────────┬─────────────┘
                                │
                    ┌───────────▼─────────────┐
                    │      Sentinel 集群        │
                    │  (哨兵1, 哨兵2, 哨兵3)   │
                    └───────────┬─────────────┘
                                │
          ┌─────────────────────┼─────────────────────┐
          │                     │                     │
          ▼                     ▼                     ▼
    ┌───────────┐        ┌───────────┐        ┌───────────┐
    │  Master   │        │  Slave1   │        │  Slave2   │
    │ (主节点)   │        │ (从节点)  │        │ (从节点)  │
    └───────────┘        └───────────┘        └───────────┘
```

**哨兵职责：**

| 职责 | 说明 |
|------|------|
| 监控 | 监控主从节点健康状态 |
| 自动故障转移 | 主节点宕机时自动切换 |
| 通知 | 故障时通知应用和管理员 |
| 配置提供 | 为客户端提供主节点地址 |

**哨兵配置：**

```bash
# sentinel.conf
sentinel monitor mymaster 127.0.0.1 6379 2  # 监控主节点，2票生效
sentinel down-after-milliseconds mymaster 30000  # 30秒无响应认为主观下线
sentinel failover-timeout mymaster 180000  # 故障转移超时
sentinel parallel-syncs mymaster 1  # 同时同步的从节点数
```

**故障转移流程：**

```
1. 主观下线（SDOWN）
   哨兵检测到主节点无响应

2. 客观下线（ODOWN）
   多个哨兵投票，超过 quorum 认为是客观下线

3. 选举领头的哨兵
   Raft 算法选出一个哨兵执行故障转移

4. 选择新主节点
   - 优先级高的
   - 偏移量大的（数据最新）
   - runid 小的

5. 故障转移
   - 新主节点执行 SLAVEOF NO ONE
   - 其他从节点指向新主节点
   - 通知客户端新地址

6. 旧主节点恢复
   变为新主节点的从节点
```

**客户端连接哨兵：**

```python
from redis.sentinel import Sentinel

# 连接哨兵集群
sentinel = Sentinel([
    ('localhost', 26379),
    ('localhost', 26380),
    ('localhost', 26381)
], socket_timeout=0.1)

# 获取主节点
master = sentinel.discover_master('mymaster')
print(f"主节点: {master}")

# 获取从节点
slaves = sentinel.discover_slaves('mymaster')
print(f"从节点: {slaves}")

# 获取连接
master_client = sentinel.master_for('mymaster')
slave_client = sentinel.slave_for('mymaster')

# 使用
master_client.set('key', 'value')
value = slave_client.get('key')
```

---

### Q23: Redis Cluster（集群）是如何工作的？

**参考答案：**

**集群架构：**

```
        ┌─────────────────────────────────────────────────┐
        │               Redis Cluster                       │
        │                                                  │
        │  ┌─────────┐    ┌─────────┐    ┌─────────┐     │
        │  │ Node 1  │───▶│ Node 2  │───▶│ Node 3  │     │
        │  │ Master  │◀───│ Master  │◀───│ Master  │     │
        │  └────┬────┘    └────┬────┘    └────┬────┘     │
        │       │              │              │          │
        │       ▼              ▼              ▼          │
        │  ┌─────────┐    ┌─────────┐    ┌─────────┐     │
        │  │ Slave 1 │    │ Slave 2 │    │ Slave 3 │     │
        │  │ (副本)   │    │ (副本)   │    │ (副本)   │     │
        │  └─────────┘    └─────────┘    └─────────┘     │
        └─────────────────────────────────────────────────┘

槽分布：
  Node 1: 0-5460
  Node 2: 5461-10922
  Node 3: 10923-16383
```

**槽（Slot）概念：**

```python
# Redis 集群有 16384 个槽（0-16383）
# 每个节点负责一部分槽

# 键的槽计算
def slot(key):
    return crc16(key) % 16384

# 示例
slot("name")   # 计算 "name" 的槽位
slot("user:1") # 计算 "user:1" 的槽位
```

**集群节点通信：**

```bash
# Gossip 协议
# 节点间互相交换信息，传播：
# - 节点状态
# - 槽信息
# - 新节点
# - 节点故障

# 节点消息类型
# PING/PONG：心跳
# MEET：节点握手
# FAIL：节点故障
# PUBLISH：广播消息
```

**故障检测和转移：**

```python
# 故障检测
# 1. 节点定时发送 PING
# 2. 超过 node-timeout 无响应认为疑似下线
# 3. 集群中超过半数主节点认为下线则确认

# 故障转移
# 1. 从节点发起选举
# 2. 向主节点请求投票
# 3. 获得多数票的从节点成为新主节点
# 4. 接管故障节点的槽
```

**客户端重定向：**

```python
# MOVED 重定向
# 客户端请求错误的节点
# 节点返回 MOVED <slot> <node:port>
# 客户端更新路由表并重试

# ASK 重定向
# 槽迁移过程中使用
# 表示键可能在两个节点
# 客户端先去源节点执行 ASKING 命令，再到目标节点

# 客户端缓存（CASC）
# 客户端缓存槽和节点的映射
# 减少重定向次数
```

**集群操作命令：**

```bash
# 槽分配
redis-cli cluster addslots 0-5460        # 添加槽
redis-cli cluster delslots 5461-10922     # 删除槽
redis-cli cluster reshard 127.0.0.1:7000 # 重新分片

# 节点操作
redis-cli cluster meet 127.0.0.1 7001   # 节点握手
redis-cli cluster forget <node_id>       # 移除节点
redis-cli cluster replicate <node_id>    # 配置为从节点

# 集群状态
redis-cli cluster nodes                  # 节点信息
redis-cli cluster slots                  # 槽分配
redis-cli cluster info                  # 集群信息
```

---

### Q24: Redis 集群和哨兵模式有什么区别？

**参考答案：**

**模式对比：**

| 特性 | Sentinel | Cluster |
|------|----------|---------|
| **数据分片** | 无 | 16384 槽分片 |
| **高可用** | 主从自动切换 | 主从自动切换 |
| **扩展性** | 读写分离 | 水平扩展 |
| **客户端** | 标准 Redis 客户端 | 集群客户端 |
| **节点数量** | 1主+N从 | 多主多从 |
| **故障转移** | 哨兵投票决定 | 从节点投票决定 |
| **配置复杂度** | 较低 | 较高 |

**Sentinel 适用场景：**

```python
# 场景：读多写少，需要读写分离
# 架构：1 主 + 多从

sentinel = Sentinel([
    ('master-host', 26379),
    ('slave1-host', 26379),
    ('slave2-host', 26379)
])

# 写操作走主节点
master = sentinel.master_for('mymaster')
master.set('key', 'value')

# 读操作走从节点
slave = sentinel.slave_for('mymaster')
value = slave.get('key')
```

**Cluster 适用场景：**

```python
# 场景：数据量大，需要分片存储
# 架构：多主多从

from redis.cluster import RedisCluster

# 集群客户端
rc = RedisCluster(
    host='127.0.0.1',
    port=7000,
    decode_responses=True
)

# 自动路由
rc.set('key1', 'value1')  # 自动路由到正确的节点
value = rc.get('key1')

# 支持跨节点操作
# MGET/MSET 自动处理多节点
rc.mset({'key1': 'v1', 'key2': 'v2', 'key3': 'v3'})
```

**选择建议：**

| 场景 | 推荐方案 |
|------|----------|
| 小规模应用，数据量小 | Sentinel |
| 读多写少，需要扩展读 | Sentinel + 从节点 |
| 大数据量，需要分片 | Cluster |
| 高并发，需要高可用 | Cluster |
| 简单部署 | Sentinel |
| 复杂需求 | Cluster |

---

### Q25: Redis 过期键的删除策略是什么？

**参考答案：**

**过期键删除策略：**

| 策略 | 说明 | 优点 | 缺点 |
|------|------|------|------|
| **定时删除** | 设置定时器，键到期即删 | 内存友好 | CPU 压力大 |
| **惰性删除** | 访问时检查，过期则删 | CPU 友好 | 内存可能不足 |
| **定期删除** | 定时扫描，抽查过期键 | 平衡方案 | 实现复杂 |

**Redis 采用的策略：**

```python
# Redis 使用惰性删除 + 定期删除的组合策略

# 1. 惰性删除（Lazy Expiration）
# 在访问键时检查是否过期

def GET(key):
    if key in db and db[key].expire_time < now:
        del db[key]  # 删除过期键
        return None
    return db[key].value

# 2. 定期删除（Active Expiration）
# 每隔一段时间，抽查一部分键

def active_expire_cycle():
    # 遍历数据库
    for db in redis.dbs:
        # 抽查一定数量的键
        for i in range(REDIS_EXPIRE_SHARDS):
            key = db.random_key()
            if key.expire_time < now:
                del key
```

**配置参数：**

```bash
# hz 参数：每秒执行定期删除的次数
hz 10  # 每秒 10 次

# 范围：1-500
# hz 越高，CPU 消耗越大，但过期键清理越及时

# active-expire-effort 参数：清理努力程度
active-expire-effort 1  # 范围 1-10
# 越高越积极清理，但 CPU 消耗越大
```

**主从复制下的过期删除：**

```python
# 主从复制中的过期键处理

# 主节点：
# - 删除过期键后，向从节点发送 DEL 命令
# - 保证主从数据一致

# 从节点：
# - 不会主动删除过期键
# - 返回过期键的值（保证数据可用性）
# - 主节点会发送 DEL 命令同步删除

# 这样设计的原因：
# - 从节点依赖主节点的数据同步来删除过期键
# - 如果从节点独立删除，可能与主节点不一致
```

**AOF/RDB 与过期键：**

```bash
# RDB 持久化
# SAVE/BGSAVE 之前，会检查键的过期时间
# 已过期的键不会被写入 RDB 文件

# AOF 持久化
# 如果键过期但未删除，AOF 不会记录
# 如果键被惰性删除或定期删除，会追加 DEL 命令
```

---

## 6. 性能优化

### Q26: 如何监控 Redis 的性能？

**参考答案：**

**INFO 命令详解：**

```python
# 获取所有信息
info = redis_client.info()
print(f"内存使用: {info['used_memory_human']}")
print(f"连接数: {info['connected_clients']}")
print(f"QPS: {info['instantaneous_ops_per_sec']}")

# 分段获取
info_memory = redis_client.info("memory")
info_stats = redis_client.info("stats")
info_cpu = redis_client.info("cpu")
info_replication = redis_client.info("replication")
info_slowlog = redis_client.info("slowlog")
```

**关键监控指标：**

| 指标 | 说明 | 告警阈值 |
|------|------|----------|
| **used_memory** | 内存使用量 | > 最大内存 80% |
| **connected_clients** | 连接数 | > 1000 |
| **blocked_clients** | 阻塞客户端 | > 0 |
| **instantaneous_ops** | QPS | 持续下降 |
| **keyspace_hits** | 缓存命中率 | < 80% |
| **evicted_keys** | 淘汰键数 | > 0 |
| **rejected_connections** | 拒绝连接 | > 0 |

**慢查询日志：**

```bash
# 配置慢查询
slowlog-log-slower-than 10000  # 10ms 以上记录
slowlog-max-len 128            # 最多保留 128 条

# 查看慢查询
redis-cli SLOWLOG GET 10

# 返回格式：
# [
#   [id, timestamp, duration, command],
#   ...
# ]
```

```python
# 获取慢查询
slowlog = redis_client.slowlog_get(10)
for entry in slowlog:
    print(f"命令: {entry['command']}")
    print(f"耗时: {entry['duration']}μs")
    print(f"时间: {entry['start_time']}")
```

**性能测试：**

```bash
# redis-benchmark 压测
redis-benchmark -h localhost -p 6379 -n 100000 -c 50

# 测试特定命令
redis-benchmark -h localhost -p 6379 -t SET,GET -n 100000

# 测试 Pipeline
redis-benchmark -h localhost -p 6379 -P 10 -n 100000

# 参数说明：
# -n: 请求总数
# -c: 并发连接数
# -P: Pipeline 数量
# -t: 测试的命令
```

**Redis 延迟监控：**

```python
# 延迟监控
redis_client.config_set("latency-monitor-threshold", 100)  # 100ms

# 延迟历史
latency_history = redis_client.latency_graph()

# 延迟诊断
latency_doctor = redis_client.latency_doctor()
```

---

### Q27: Redis 内存优化有哪些技巧？

**参考答案：**

**内存优化策略：**

| 策略 | 说明 | 效果 |
|------|------|------|
| **选择合适数据结构** | 根据场景选择最优结构 | 显著 |
| **键名设计** | 精简键名，使用短前缀 | 中等 |
| **过期时间** | 设置合理的 TTL | 显著 |
| **内存碎片** | 合理配置 activedefrag | 中等 |
| **过期键及时删除** | 避免内存占用 | 显著 |

**数据结构优化：**

```python
# 场景1：存储用户信息
# 不用 Hash 用多个 String
# 反例
redis_client.set("user:1001:name", "张三")
redis_client.set("user:1001:age", "25")
redis_client.set("user:1001:city", "北京")
# 每次操作需要多次网络往返

# 推荐：使用 Hash
redis_client.hset("user:1001", mapping={
    "name": "张三",
    "age": "25",
    "city": "北京"
})
redis_client.hgetall("user:1001")  # 一次获取

# 场景2：存储布尔值
# 使用 Bit 操作代替 String
# 反例
for i in range(10000):
    redis_client.set(f"user:{i}:checkin", 1)

# 推荐：使用 Bitmap
user_id = 1001
date = "20240115"
offset = user_id
redis_client.setbit(f"checkin:{date}", offset, 1)

# 检查是否签到
redis_client.getbit(f"checkin:{date}", offset)

# 场景3：大量计数
# 使用 HyperLogLog 代替 Set
redis_client.pfadd("uv:20240115", "user1", "user2", "user3")
count = redis_client.pfcount("uv:20240115")  # UV 统计
```

**键名设计：**

```python
# 键名过长示例
redis_client.set("user:profile:1001:basic_info:name", "张三")

# 优化：精简键名
redis_client.set("u:p:1001:n", "张三")  # 简短前缀

# 使用哈希替代多个键
redis_client.hset("u:p:1001", "n", "张三")
```

**内存碎片处理：**

```bash
# 查看内存碎片率
redis-cli info memory | grep mem_fragmentation_ratio

# 碎片率 = used_memory_rss / used_memory
# 理想值：1.0 - 1.5
# 过高：需要清理

# 自动碎片清理
activedefrag yes
active-defrag-ignore-bytes 100mb        # 超过100MB碎片时触发
active-defrag-threshold-lower 10        # 碎片率>10%时触发
active-defrag-threshold-upper 100       # 碎片率>100%时最大努力

# 手动碎片清理
redis-cli MEMORY PURGE
```

**内存淘汰策略：**

```bash
# 配置
maxmemory 2gb                    # 最大内存
maxmemory-policy allkeys-lru     # LRU 淘汰所有键

# 可选策略
# noeviction: 不淘汰（默认）
# allkeys-lru: 所有键 LRU
# allkeys-lfu: 所有键 LFU
# volatile-lru: 设置过期键 LRU
# allkeys-random: 所有键随机
# volatile-ttl: 淘汰 TTL 最短的
```

---

### Q28: Redis 大 Key 如何处理？

**参考答案：**

**大 Key 定义：**

| 类型 | 大 Key 标准 |
|------|-------------|
| String | value > 10KB |
| Hash | field 数 > 5000 |
| List | 元素数 > 10000 |
| Set | 元素数 > 10000 |
| ZSet | 元素数 > 10000 |

**查找大 Key：**

```python
# 使用 SCAN 扫描
def find_big_keys(threshold=100000):
    big_keys = []
    
    for key in redis_client.scan_iter(count=1000):
        key_type = redis_client.type(key)
        
        if key_type == 'string':
            size = redis_client.strlen(key)
            if size > threshold:
                big_keys.append((key, 'string', size))
        
        elif key_type == 'hash':
            size = redis_client.hlen(key)
            if size > threshold:
                big_keys.append((key, 'hash', size))
        
        elif key_type == 'list':
            size = redis_client.llen(key)
            if size > threshold:
                big_keys.append((key, 'list', size))
    
    return big_keys

# 使用 redis-cli
# redis-cli --bigkeys
```

**大 Key 处理方案：**

```python
# 方案1：分拆大 Hash
# 将大 Hash 拆分为多个小 Hash

def split_big_hash(hash_key, max_fields=1000):
    """拆分大 Hash"""
    # 获取所有字段
    cursor = 0
    field_count = 0
    new_hash_key = f"{hash_key}:{field_count // max_fields}"
    
    for field in redis_client.hscan_iter(hash_key):
        field_name, value = field
        redis_client.hset(new_hash_key, field_name, value)
        field_count += 1
        
        if field_count % max_fields == 0:
            new_hash_key = f"{hash_key}:{field_count // max_fields}"
    
    # 删除原 Hash
    redis_client.delete(hash_key)

# 方案2：分拆大 List
def split_big_list(list_key, batch_size=1000):
    """分拆大 List"""
    while redis_client.llen(list_key) > batch_size:
        # 弹出前 batch_size 个元素
        elements = redis_client.lrange(list_key, 0, batch_size - 1)
        redis_client.ltrim(list_key, batch_size, -1)
        
        # 存入新 List
        new_key = f"{list_key}:{int(time.time())}"
        redis_client.rpush(new_key, *elements)
```

**渐进式删除：**

```python
def delete_big_key(key):
    """渐进式删除大 Key"""
    key_type = redis_client.type(key)
    
    if key_type == 'list':
        while redis_client.llen(key) > 0:
            redis_client.ltrim(key, 1000, -1)  # 每次删除1000个
        redis_client.delete(key)
    
    elif key_type == 'hash':
        while redis_client.hlen(key) > 0:
            redis_client.hdel(key, *redis_client.hkeys(key)[:1000])
        redis_client.delete(key)
    
    elif key_type == 'set':
        while redis_client.scard(key) > 0:
            redis_client.spop(key, 1000)  # 每次删除1000个
        redis_client.delete(key)
```

---

### Q29: Redis 如何实现延迟队列？

**参考答案：**

**延迟队列实现方案：**

| 方案 | 原理 | 特点 |
|------|------|------|
| **ZSet + 轮询** | 分数=执行时间 | 简单，需要轮询 |
| **Redis + 定时器** | 定时器触发 | 精确，消耗资源 |
| **Redisson** | ZSet + 轮询 | 封装完善 |

**基于 ZSet 的延迟队列：**

```python
import time
import json
import threading

class DelayQueue:
    """基于 Redis ZSet 的延迟队列"""
    
    def __init__(self, redis_client, queue_name):
        self.redis = redis_client
        self.queue_name = queue_name
    
    def add(self, task_id, data, delay_seconds):
        """
        添加延迟任务
        task_id: 任务ID
        data: 任务数据
        delay_seconds: 延迟秒数
        """
        execute_time = time.time() + delay_seconds
        score = execute_time  # 使用时间戳作为分数
        
        member = json.dumps({"id": task_id, "data": data})
        self.redis.zadd(self.queue_name, {member: score})
    
    def poll(self, batch_size=10, block_timeout=5):
        """
        轮询获取可执行的任务
        返回已到期的任务列表
        """
        now = time.time()
        
        # 获取已到期的任务（分数 < 当前时间）
        results = self.redis.zrangebyscore(
            self.queue_name,
            '-inf',  # 最小分数
            now,      # 最大分数：当前时间
            start=0,
            num=batch_size
        )
        
        # 原子性取出任务
        for task_json in results:
            # 移除任务
            removed = self.redis.zrem(self.queue_name, task_json)
            
            if removed:
                yield json.loads(task_json)
    
    def remove(self, task_id):
        """手动删除任务"""
        # 需要遍历找到任务
        tasks = self.redis.zrange(self.queue_name, 0, -1)
        for task_json in tasks:
            task = json.loads(task_json)
            if task['id'] == task_id:
                self.redis.zrem(self.queue_name, task_json)
                return True
        return False

# 使用示例
queue = DelayQueue(redis_client, "delay:tasks")

# 生产者：添加延迟任务
queue.add(
    task_id="task_001",
    data={"action": "send_email", "to": "user@example.com"},
    delay_seconds=60  # 60秒后执行
)

# 消费者：轮询执行
def worker():
    while True:
        tasks = queue.poll(batch_size=10, block_timeout=5)
        for task in tasks:
            try:
                execute_task(task)
            except Exception as e:
                print(f"执行失败: {e}")

# 启动消费者线程
threading.Thread(target=worker, daemon=True).start()
```

**基于定时事件的延迟队列：**

```python
import time
import threading
import heapq

class ScheduledTask:
    """基于定时器的延迟任务"""
    
    def __init__(self, redis_client):
        self.redis = redis_client
        self._running = False
        self._thread = None
    
    def schedule(self, task_id, data, execute_at):
        """
        定时执行任务
        execute_at: 执行时间戳
        """
        # 存入有序集合
        member = json.dumps({"id": task_id, "data": data})
        self.redis.zadd("scheduled:tasks", {member: execute_at})
    
    def start(self):
        """启动调度器"""
        self._running = True
        self._thread = threading.Thread(target=self._run)
        self._thread.start()
    
    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join()
    
    def _run(self):
        while self._running:
            now = time.time()
            
            # 获取当前应执行的任务
            tasks = self.redis.zrangebyscore(
                "scheduled:tasks",
                '-inf',
                now
            )
            
            for task_json in tasks:
                removed = self.redis.zrem("scheduled:tasks", task_json)
                if removed:
                    task = json.loads(task_json)
                    self._execute(task)
            
            time.sleep(0.1)  # 避免 CPU 100%
    
    def _execute(self, task):
        print(f"执行任务: {task}")
```

---

### Q30: Redis 常见面试问题汇总？

**参考答案：**

**项目相关问题：**

**Q: 项目中 Redis 缓存了哪些数据？**

```python
# 项目中的 Redis 使用

# 1. 问答结果缓存
cache_key = f"qa:{hashlib.md5(question.encode()).hexdigest()}"
redis_client.setex(cache_key, 3600, json.dumps(result))

# 2. 会话信息
session_key = f"session:{session_id}"
redis_client.hset(session_key, "user_id", user_id)
redis_client.hset(session_key, "created_at", str(time.time()))
redis_client.expire(session_key, 86400)  # 24小时过期

# 3. 配置缓存
config_key = "system:config"
redis_client.set(config_key, json.dumps(config_data), ex=300)

# 4. 限流
rate_key = f"rate:{user_id}:{int(time.time() / 60)}"
count = redis_client.incr(rate_key)
if count == 1:
    redis_client.expire(rate_key, 60)
```

**Q: Redis 缓存和数据库如何保持一致性？**

```python
# 策略1：Cache-Aside（旁路缓存）
# 读：先缓存，后数据库
# 写：先写数据库，后删缓存

def update_document(doc_id, data):
    # 1. 更新数据库
    db.query(Document).filter(Document.id == doc_id).update(data)
    db.commit()
    
    # 2. 删除缓存（不更新，防止并发问题）
    redis_client.delete(f"doc:{doc_id}")

# 策略2：延迟双删
# 写：先删缓存，再更新数据库，再删缓存

def update_with_delay_delete(doc_id, data):
    # 1. 先删缓存
    redis_client.delete(f"doc:{doc_id}")
    
    # 2. 更新数据库
    db.query(Document).filter(Document.id == doc_id).update(data)
    db.commit()
    
    # 3. 延迟再删缓存（异步线程）
    def delayed_delete():
        time.sleep(0.5)
        redis_client.delete(f"doc:{doc_id}")
    threading.Thread(target=delayed_delete).start()
```

**Q: 如何保证 Redis 的高可用？**

```python
# 1. 使用哨兵或集群
# 2. 配置持久化（RDB + AOF）
# 3. 合理设置内存和淘汰策略
# 4. 监控和告警

# 监控指标
# - 内存使用率
# - 缓存命中率
# - 连接数
# - 慢查询
# - 主从同步延迟
```

---

## 附录：面试重点总结

### 核心知识点

| 类别 | 重点内容 |
|------|----------|
| **数据类型** | String/Hash/List/Set/ZSet 底层实现 |
| **持久化** | RDB 快照、AOF 追加日志、混合持久化 |
| **缓存策略** | 穿透、击穿、雪崩及解决方案 |
| **高可用** | 主从复制、哨兵、集群 |
| **分布式锁** | SET NX EX、Lua 脚本、RedLock |
| **消息队列** | List、Pub/Sub、Stream |

### 常见追问

1. **Redis 为什么这么快？**
   - 内存操作，单线程非阻塞 I/O

2. **如何解决缓存一致性？**
   - 先更新数据库，后删除缓存

3. **Redis 和 Memcached 的区别？**
   - 数据结构、持久化、集群支持

---

*本文档共 30 道面试题，覆盖 Redis 缓存的核心技术点*
