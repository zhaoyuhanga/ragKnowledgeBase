# Redis缓存 - 20K薪资面试题

> 本文档包含Redis相关面试题，涵盖数据类型、持久化、集群、缓存设计等核心知识点。

---

## 第一部分：基础概念（共8题）

### Q1: Redis的数据类型有哪些？

**题目类型**：基础概念类

**问题描述**：Redis支持哪些数据类型？各自的使用场景是什么？

**答案要点**：

**五种基本数据类型：**

| 类型 | 命令示例 | 数据结构 | 使用场景 |
|------|----------|----------|----------|
| String | GET/SET | 简单动态字符串(SDS) | 缓存、计数器、分布式锁 |
| Hash | HSET/HGET | 压缩列表/哈希表 | 存储对象、购物车 |
| List | LPUSH/RPOP | 压缩列表/链表 | 消息队列、排行榜 |
| Set | SADD/SMEMBERS | 哈希表/整数集合 | 标签、好友关系 |
| Sorted Set | ZADD/ZRANGE | 压缩列表/跳表 | 有序列表、排行榜 |

**详细说明：**

```redis
# String - 字符串
SET key "value"
GET key
INCR counter          # 原子递增
SETNX key value       # 不存在则设置（分布式锁）

# Hash - 哈希表
HSET user:1 name "Tom" age "25"
HGET user:1 name
HGETALL user:1
HINCRBY user:1 age 1

# List - 列表
LPUSH mylist "a"       # 左侧插入
RPUSH mylist "b"       # 右侧插入
LRANGE mylist 0 -1     # 获取全部
LPOP mylist            # 左侧弹出

# Set - 集合
SADD tags "java" "redis"
SMEMBERS tags
SISMEMBER tags "java"
SINTER set1 set2       # 交集

# Sorted Set - 有序集合
ZADD leaderboard 100 "Tom"
ZADD leaderboard 200 "Jerry"
ZRANGE leaderboard 0 -1 WITHSCORES  # 按分数排序
ZREVRANGE leaderboard 0 9           # 倒序前10
```

**三种特殊类型：**

| 类型 | 说明 | 使用场景 |
|------|------|----------|
| Bitmap | 位图 | 用户签到、统计 |
| HyperLogLog | 基数统计 | UV统计 |
| Geospatial | 地理位置 | 附近的人 |

```redis
# Bitmap - 用户签到
SETBIT sign:2024:user:1 0 1    # 1月1日签到
GETBIT sign:2024:user:1 0      # 检查是否签到
BITCOUNT sign:2024:user:1       # 签到天数

# HyperLogLog - 统计UV
PFADD page:uv "user1" "user2"
PFCOUNT page:uv

# Geospatial - 附近的人
GEOADD company 116.404 39.915 "office"
GEODIST company office home km     # 距离
GEORADIUS company 116 39 10 km     # 附近10km
```

---

### Q2: Redis的持久化机制是什么？

**题目类型**：技术原理类

**问题描述**：Redis有哪些持久化方式？各自的优缺点是什么？

**答案要点**：

**RDB（Redis Database）持久化：**

```redis
# RDB配置
save 900 1        # 900秒内至少1个key变化则保存
save 300 10       # 300秒内至少10个key变化则保存
save 60 10000     # 60秒内至少10000个key变化则保存

# 手动触发
BGSAVE            # 后台异步保存
SAVE              # 同步保存（阻塞）
```

**AOF（Append Only File）持久化：**

```redis
# AOF配置
appendonly yes                    # 开启AOF
appendfilename "appendonly.aof"

# 同步策略
appendfsync always               # 每条命令同步（最安全，最慢）
appendfsync everysec             # 每秒同步（默认，推荐）
appendfsync no                   # 由系统决定（最快，可能丢失数据）

# AOF重写
BGREWRITEAOF                    # 后台重写AOF
```

**对比：**

| 特性 | RDB | AOF |
|------|------|-----|
| 文件大小 | 小 | 大 |
| 恢复速度 | 快 | 慢 |
| 数据完整性 | 可能丢失数据 | 可配置 |
| 性能影响 | fork子进程 | 主线程 |
| 适用场景 | 备份、容灾 | 实时持久化 |

**混合持久化（RDB+AOF）：**

```redis
# 开启混合持久化
aof-use-rdb-preamble yes

# 重写时生成RDB格式，快速恢复
# 新数据用AOF格式追加
```

---

### Q3: Redis过期键的删除策略是什么？

**题目类型**：技术原理类

**问题描述**：Redis如何处理过期键？有哪些删除策略？

**答案要点**：

**三种删除策略：**

| 策略 | 说明 | 优点 | 缺点 |
|------|------|------|------|
| 定时删除 | 设置定时器 | 内存友好 | CPU压力大 |
| 惰性删除 | 访问时检查 | 节省CPU | 内存浪费 |
| 定期删除 | 周期性检查 | 平衡方案 | 需配置 |

**惰性删除实现：**

```redis
# 每次访问key时检查是否过期
GET key
# 如果过期则删除并返回nil
```

**定期删除流程：**

```
┌─────────────────────────────────────────────────────────────┐
│                    定期删除流程                               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Redis.conf: hz 10  # 每秒执行10次                          │
│                                                             │
│  每次随机检查:                                               │
│  1. 检查所有设置了过期时间的key                              │
│  2. 删除已过期的key                                        │
│  3. 如果超过25%的key过期，继续检查                          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**内存淘汰策略（当内存满时）：**

```redis
# maxmemory-policy 配置
# noeviction      - 不淘汰，返回错误（默认）
# volatile-lru    - LRU算法淘汰设置了过期时间的key
# allkeys-lru     - LRU算法淘汰所有key
# volatile-random - 随机淘汰设置了过期时间的key
# allkeys-random  - 随机淘汰所有key
# volatile-ttl    - 淘汰TTL最短的key

# LRU算法配置
maxmemory-samples 5    # 采样数量，越多越精确但越慢
```

---

### Q4: Redis为什么这么快？

**题目类型**：技术原理类

**问题描述**：Redis为什么性能这么高？它的核心设计是什么？

**答案要点**：

**高性能原因：**

| 原因 | 说明 |
|------|------|
| 内存存储 | 基于内存，O(1)访问 |
| 单线程 | 避免上下文切换和锁竞争 |
| IO多路复用 | 非阻塞IO，事件驱动 |
| 高效数据结构 | 针对场景优化的数据结构 |

**单线程模型：**

```python
# Redis 6.0之前是单线程
# 单线程指处理命令的线程是单线程
# 但有后台线程处理持久化等任务

# IO多路复用
# 客户端连接 → 事件监听 → 事件处理
#   ↓
# SELECT/EPOLL/KQUEUE
```

**高效数据结构：**

```redis
# String - SDS (Simple Dynamic String)
# - 预分配空间，避免频繁扩容
# - 惰性空间释放
# - 二进制安全

# Hash - 压缩列表/哈希表
# - 小数据用压缩列表(ziplist)
# - 大数据用哈希表(hashtable)

# List - 压缩列表/双向链表
# - 少量元素用压缩列表
# - 大量元素用链表

# Set - 整数集合/哈希表
# - 全是整数且少量用整数集合(intset)
# - 其他情况用哈希表

# Sorted Set - 压缩列表/跳表
# - 小数据用压缩列表
# - 大量数据用跳表(skip list)
```

---

### Q5: Redis的发布订阅是什么？

**题目类型**：基础概念类

**问题描述**：Redis的发布订阅模式是什么？如何使用？

**答案要点**：

**发布订阅模式：**

```redis
# 频道模式
PUBLISH channel:news "Hello"        # 发布消息
SUBSCRIBE channel:news            # 订阅频道
UNSUBSCRIBE channel:news          # 取消订阅

# 模式匹配订阅
PSUBSCRIBE news:*                 # 匹配多个频道
PUNSUBSCRIBE news:*               # 取消匹配订阅

# 查看订阅信息
PUBSUB CHANNELS [pattern]         # 活跃频道
PUBSUB NUMSUB channel:news       # 订阅者数量
```

**使用场景：**

```python
import redis

r = redis.Redis()

# 发布者
def publish_message(channel, message):
    r.publish(channel, message)

# 订阅者
def subscribe(channel):
    pubsub = r.pubsub()
    pubsub.subscribe(channel)
    
    for message in pubsub.listen():
        if message['type'] == 'message':
            print(f"收到: {message['data']}")

# 发布消息
publish_message('chat:room1', 'Hello everyone')

# 注意：发布订阅是即发即弃，不保留消息
# 订阅者必须提前订阅才能收到消息
```

**与消息队列对比：**

| 特性 | Redis发布订阅 | Redis Stream |
|------|--------------|--------------|
| 消息持久化 | 不支持 | 支持 |
| 消息确认 | 不支持 | 支持 |
| 消费者组 | 不支持 | 支持 |
| 消息回溯 | 不支持 | 支持 |
| 适用场景 | 实时通知 | 消息队列 |

---

### Q6: Redis的Pipeline是什么？

**题目类型**：技术原理类

**问题描述**：Redis Pipeline是什么？它有什么作用？

**答案要点**：

**Pipeline原理：**

```
┌─────────────────────────────────────────────────────────────┐
│                    Pipeline 原理                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  普通模式:                                                 │
│  Client → Command1 → Server → Response1 → Client           │
│  Client → Command2 → Server → Response2 → Client           │
│  Client → Command3 → Server → Response3 → Client           │
│  RTT × 3                                                  │
│                                                             │
│  Pipeline模式:                                            │
│  Client → Command1 Command2 Command3 → Server             │
│  Client ← Response1 Response2 Response3 ← Server          │
│  RTT × 1                                                  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**使用示例：**

```python
import redis

r = redis.Redis()

# 普通方式 - 多次网络往返
for key in keys:
    r.get(key)

# Pipeline - 一次网络往返
pipe = r.pipeline()
for key in keys:
    pipe.get(key)
results = pipe.execute()  # 批量执行

# Pipeline命令组合
pipe = r.pipeline()
pipe.set('key1', 'value1')
pipe.set('key2', 'value2')
pipe.get('key1')
pipe.incr('counter')
results = pipe.execute()
# results = [True, True, b'value1', 1]
```

**注意事项：**

```python
# 1. Pipeline不保证原子性
pipe = r.pipeline(transaction=False)

# 2. 开启事务
pipe = r.pipeline(transaction=True)  # 或 pipe.multi()

# 3. Pipeline大小控制
# 避免一次性发送过多命令
batch_size = 1000
for i in range(0, len(keys), batch_size):
    batch_keys = keys[i:i+batch_size]
    pipe = r.pipeline()
    for key in batch_keys:
        pipe.get(key)
    pipe.execute()
```

---

### Q7: Redis的事务是什么？

**题目类型**：基础概念类

**问题描述**：Redis的事务是什么？它和传统数据库事务有什么区别？

**答案要点**：

**Redis事务命令：**

```redis
MULTI        # 开启事务
SET key1 value1
SET key2 value2
GET key1
EXEC         # 执行事务

# 或者使用WATCH实现乐观锁
WATCH key1
GET key1
MULTI
SET key1 new_value
EXEC          # 如果key1在WATCH后被修改，返回(nil)
```

**事务特性：**

| 特性 | Redis事务 | 数据库事务 |
|------|-----------|------------|
| 原子性 | 全部执行/全部不执行 | 支持 |
| 隔离性 | 无隔离级别 | 支持 |
| 一致性 | 保证 | 支持 |
| 持久性 | 取决于持久化配置 | 支持 |
| 回滚 | 不支持部分回滚 | 支持 |

**代码示例：**

```python
import redis

r = redis.Redis()

# 正常事务
pipe = r.pipeline(transaction=True)
pipe.multi()
pipe.set('balance:1', 1000)
pipe.decrby('balance:1', 100)
pipe.incrby('balance:2', 100)
pipe.exec()

# WATCH实现乐观锁
def transfer(from_id, to_id, amount):
    with r.pipeline() as pipe:
        while True:
            pipe.watch(f'balance:{from_id}')
            balance = int(pipe.get(f'balance:{from_id}'))
            if balance < amount:
                pipe.unwatch()
                return False
            pipe.multi()
            pipe.decrby(f'balance:{from_id}', amount)
            pipe.incrby(f'balance:{to_id}', amount)
            try:
                pipe.exec()
                return True
            except redis.WatchError:
                continue  # 重试
```

---

### Q8: Redis的Lua脚本是什么？

**题目类型**：技术原理类

**问题描述**：Redis Lua脚本有什么作用？如何使用？

**答案要点**：

**Lua脚本优势：**

```redis
# 保证原子性 - Lua脚本执行期间不会执行其他命令
# 高效 - 减少网络往返

# 经典场景：分布式锁
EVAL "
    if redis.call('SETNX', KEYS[1], ARGV[1], 'EX', ARGV[2]) == 1 then
        return 1
    else
        return 0
    end
" 1 "lock:key" "unique_value" 10
```

**脚本示例：**

```python
import redis

r = redis.Redis()

# 执行Lua脚本
script = """
local key = KEYS[1]
local limit = tonumber(ARGV[1])
local expire = tonumber(ARGV[2])

local current = tonumber(redis.call('GET', key) or '0')
if current < limit then
    redis.call('INCR', key)
    if current == 0 then
        redis.call('EXPIRE', key, expire)
    end
    return 1
else
    return 0
end
"""

# 限流
result = r.eval(script, 1, 'rate:limit:user:1', 100, 60)

# 注册脚本（缓存SHA）
sha = r.script_load(script)
result = r.evalsha(sha, 1, 'rate:limit:user:1', 100, 60)
```

**脚本管理命令：**

```redis
SCRIPT LOAD script         # 加载脚本，返回SHA
SCRIPT EXISTS sha1 sha2    # 检查脚本是否存在
SCRIPT FLUSH              # 清空所有脚本缓存
SCRIPT KILL               # 终止正在运行的脚本
```

---

## 第二部分：缓存设计（共8题）

### Q9: 什么是缓存穿透？如何解决？

**题目类型**：场景解决类

**问题描述**：什么是缓存穿透？如何避免缓存穿透？

**答案要点**：

**缓存穿透定义：**
查询不存在的数据，每次都查询数据库，给数据库造成压力。

```
请求 → Redis（未命中）→ 数据库（也未命中）→ 返回空
  ↓
大量请求涌入数据库
```

**解决方案：**

```python
# 方案1: 布隆过滤器
from bloom_filter import BloomFilter

bf = BloomFilter(max_elements=100000, error_rate=0.01)

# 添加存在的key
for item in existing_items:
    bf.add(f"item:{item.id}")

# 查询时检查
def get_item(item_id):
    key = f"item:{item_id}"
    if key in bloom_filter:
        # 可能存在，查Redis
        return redis.get(key)
    else:
        # 一定不存在，直接返回
        return None

# 方案2: 缓存空值
def get_item(item_id):
    key = f"item:{item_id}"
    value = redis.get(key)
    
    if value is None:
        # 查数据库
        item = db.query(item_id)
        if item:
            redis.setex(key, 3600, json.dumps(item))
        else:
            # 缓存空值，短暂过期
            redis.setex(key, 300, "NULL")
        return item
    elif value == "NULL":
        return None
    else:
        return json.loads(value)

# 方案3: 参数校验
def get_item(item_id):
    if item_id <= 0:
        return None
    # 继续查询
```

---

### Q10: 什么是缓存雪崩？如何解决？

**题目类型**：场景解决类

**问题描述**：什么是缓存雪崩？如何避免？

**答案要点**：

**缓存雪崩定义：**
大量缓存同时过期/失效，导致大量请求直接打到数据库。

```
时间点 T ──┬── Redis缓存过期
          ├── Redis缓存过期 ──→ 数据库崩溃
          └── Redis缓存过期
```

**解决方案：**

```python
# 方案1: 过期时间随机化
import random

def set_with_random_expiry(key, value, base_ttl=3600):
    ttl = base_ttl + random.randint(0, 300)  # 1小时±5分钟
    redis.setex(key, ttl, value)

# 方案2: 热点数据永不过期 + 定期更新
def get_item(item_id):
    key = f"item:{item_id}"
    
    # 先查缓存
    value = redis.get(key)
    if value:
        return json.loads(value)
    
    # 查数据库
    item = db.query(item_id)
    
    # 设置缓存（永不过期）
    redis.set(key, json.dumps(item))
    
    # 后台任务定期更新热门缓存
    return item

# 方案3: 多级缓存
class MultiLevelCache:
    def __init__(self):
        self.l1_cache = {}  # 本地缓存
        self.l2_cache = redis  # Redis缓存
        self.db = database
    
    def get(self, key):
        # L1缓存
        if key in self.l1_cache:
            return self.l1_cache[key]
        
        # L2缓存
        value = self.l2_cache.get(key)
        if value:
            self.l1_cache[key] = value
            return value
        
        # 数据库
        value = self.db.get(key)
        self.l2_cache.setex(key, 3600, value)
        self.l1_cache[key] = value
        return value

# 方案4: 熔断降级
def get_item_with_fallback(item_id):
    try:
        # 尝试从缓存获取
        value = redis.get(key)
        if value:
            return json.loads(value)
        
        # 缓存未命中，查数据库
        value = db.query(item_id)
        if value:
            redis.setex(key, 3600, json.dumps(value))
        return value
    except redis.ConnectionError:
        # Redis故障，降级到数据库
        return db.query(item_id)
```

---

### Q11: 什么是缓存击穿？如何解决？

**题目类型**：场景解决类

**问题描述**：什么是缓存击穿？如何避免？

**答案要点**：

**缓存击穿定义：**
热点key过期瞬间，大量并发请求直接打向数据库。

```
时刻 T: 热点key过期
  ↓
大量并发请求 → Redis（未命中）→ 数据库 → 数据库崩溃
```

**解决方案：**

```python
# 方案1: 分布式锁
import redis
import time

r = redis.Redis()

def get_item_with_lock(item_id):
    key = f"item:{item_id}"
    lock_key = f"lock:{key}"
    
    # 先查缓存
    value = r.get(key)
    if value:
        return json.loads(value)
    
    # 获取锁
    lock = r.set(lock_key, "1", nx=True, ex=5)
    if lock:
        try:
            # 双重检查
            value = r.get(key)
            if value:
                return json.loads(value)
            
            # 查数据库
            item = db.query(item_id)
            if item:
                r.setex(key, 3600, json.dumps(item))
            return item
        finally:
            r.delete(lock_key)
    else:
        # 未获取到锁，等待后重试
        time.sleep(0.1)
        return get_item_with_lock(item_id)

# 方案2: 逻辑过期 + 异步更新
def get_item(item_id):
    key = f"item:{item_id}"
    value = r.get(key)
    
    if value:
        data = json.loads(value)
        expire_time = data['expire_time']
        
        # 未过期，直接返回
        if expire_time > time.time():
            return data['item']
        
        # 已过期，尝试获取更新锁
        lock_key = f"lock:{key}"
        if r.set(lock_key, "1", nx=True, ex=5):
            # 异步更新（使用线程池）
            executor.submit(update_cache, item_id)
        
        return data['item']
    else:
        # 缓存为空，直接查数据库
        return db.query(item_id)

def update_cache(item_id):
    item = db.query(item_id)
    key = f"item:{item_id}"
    data = {
        'item': item,
        'expire_time': time.time() + 3600  # 逻辑过期时间
    }
    r.set(key, json.dumps(data))

# 方案3: 互斥锁（Redisson实现）
from redisson import Redisson

redisson = Redisson()
rlock = redisson.getLock(f"lock:item:{item_id}")

try:
    rlock.lock(10)  # 等待10秒
    # 查询并更新缓存
finally:
    rlock.unlock()
```

---

### Q12: 如何设计一个缓存架构？

**题目类型**：场景解决类

**问题描述**：如何设计企业级的缓存架构？有哪些核心组件？

**答案要点**：

**缓存架构设计：**

```
┌─────────────────────────────────────────────────────────────┐
│                    缓存架构设计                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  应用层                                                       │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐                   │
│  │  L1缓存  │  │  L1缓存  │  │  L1缓存  │                   │
│  │ (本地)  │  │ (本地)  │  │ (本地)  │                   │
│  └─────────┘  └─────────┘  └─────────┘                   │
│       │            │            │                         │
│       └────────────┼────────────┘                         │
│                    ▼                                        │
│  ┌─────────────────────────────────────┐                  │
│  │           L2缓存 (Redis集群)         │                  │
│  │   ┌─────┐ ┌─────┐ ┌─────┐         │                  │
│  │   │ Master│ │ Slave │ │ Slave │         │                  │
│  │   └─────┘ └─────┘ └─────┘         │                  │
│  └─────────────────────────────────────┘                  │
│                    │                                        │
│                    ▼                                        │
│  ┌─────────────────────────────────────┐                  │
│  │           数据库 (MySQL)              │                  │
│  └─────────────────────────────────────┘                  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**缓存组件设计：**

```python
class CacheManager:
    def __init__(self):
        # L1本地缓存
        self.l1_cache = {}
        self.l1_cache_expire = {}
        
        # L2 Redis缓存
        self.redis = redis.Redis()
        
        # L3 数据库
        self.db = database
        
        # 配置
        self.l1_ttl = 60          # L1缓存1分钟
        self.l2_ttl = 3600        # L2缓存1小时
    
    def get(self, key):
        # L1查询
        if key in self.l1_cache:
            if self.l1_cache_expire.get(key, 0) > time.time():
                return self.l1_cache[key]
            del self.l1_cache[key]
        
        # L2查询
        value = self.redis.get(key)
        if value:
            # 回填L1
            self.l1_cache[key] = value
            self.l1_cache_expire[key] = time.time() + self.l1_ttl
            return value
        
        # L3查询
        value = self.db.query(key)
        if value:
            self.redis.setex(key, self.l2_ttl, value)
            self.l1_cache[key] = value
            self.l1_cache_expire[key] = time.time() + self.l1_ttl
        
        return value
    
    def delete(self, key):
        # 删除多级缓存
        self.l1_cache.pop(key, None)
        self.l1_cache_expire.pop(key, None)
        self.redis.delete(key)
```

**缓存策略：**

| 策略 | 说明 | 使用场景 |
|------|------|----------|
| Cache Aside | 应用操作缓存 | 读多写少 |
| Read Through | 缓存自动加载 | 统一管理 |
| Write Through | 同步写入缓存和DB | 数据一致性要求高 |
| Write Behind | 异步写入数据库 | 高并发写入 |

---

### Q13: Redis如何实现分布式锁？

**题目类型**：场景解决类

**问题描述**：如何使用Redis实现分布式锁？有哪些注意事项？

**答案要点**：

**基础实现：**

```python
import redis
import time
import uuid

class RedisLock:
    def __init__(self, redis_client):
        self.redis = redis_client
        self.lock_key = None
        self.lock_value = None
    
    def acquire(self, key, timeout=10, retry=3, retry_delay=0.2):
        """获取锁"""
        self.lock_key = key
        self.lock_value = str(uuid.uuid4())
        
        for _ in range(retry):
            # SET NX EX 原子操作
            if self.redis.set(self.lock_key, self.lock_value, 
                            nx=True, ex=timeout):
                return True
            time.sleep(retry_delay)
        return False
    
    def release(self):
        """释放锁"""
        if self.lock_key and self.lock_value:
            # Lua脚本保证原子性
            script = """
            if redis.call('GET', KEYS[1]) == ARGV[1] then
                return redis.call('DEL', KEYS[1])
            else
                return 0
            end
            """
            self.redis.eval(script, 1, self.lock_key, self.lock_value)
    
    def __enter__(self):
        if not self.acquire(self.lock_key):
            raise Exception("Failed to acquire lock")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()
```

**可重入锁实现：**

```python
class ReentrantRedisLock:
    def __init__(self, redis_client):
        self.redis = redis_client
        self.locks = {}  # thread_local存储
    
    def acquire(self, key, timeout=10):
        thread_id = threading.current_thread().ident
        
        # 如果当前线程已持有锁
        if key in self.locks:
            self.locks[key]['count'] += 1
            return True
        
        lock_value = str(uuid.uuid4())
        if self.redis.set(key, lock_value, nx=True, ex=timeout):
            self.locks[key] = {
                'value': lock_value,
                'count': 1
            }
            return True
        return False
    
    def release(self, key):
        thread_id = threading.current_thread().ident
        
        if key not in self.locks:
            return
        
        self.locks[key]['count'] -= 1
        if self.locks[key]['count'] <= 0:
            del self.locks[key]
            self.redis.delete(key)
```

**注意事项：**

```python
# 1. 锁超时设置
# 任务执行时间 > 锁超时时间 会导致锁自动释放
# 解决：Redisson的WatchDog自动续期

# 2. 主从切换问题
# 单机Redis可能丢失数据（主从异步复制）
# 解决：RedLock（多个独立Redis实例）

# 3. 建议使用成熟库
from redisson import Redisson

redisson = Redisson()
lock = redisson.getLock("my-lock")
lock.lock(30)  # 自动续期
try:
    # 业务逻辑
finally:
    lock.unlock()
```

---

### Q14: Redis Cluster如何工作？

**题目类型**：技术原理类

**问题描述**：Redis Cluster是如何工作的？它的槽位分配是怎样的？

**答案要点**：

**Cluster架构：**

```
┌─────────────────────────────────────────────────────────────┐
│                   Redis Cluster架构                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  16384个槽位分配到多个节点                                  │
│                                                             │
│        槽0-5460      槽5461-10922    槽10923-16383           │
│     ┌─────────┐    ┌─────────┐    ┌─────────┐            │
│     │ Node1   │    │ Node2   │    │ Node3   │            │
│     │ Master  │    │ Master  │    │ Master  │            │
│     └────┬────┘    └────┬────┘    └────┬────┘            │
│          │                │                │                 │
│     ┌────┴────┐    ┌────┴────┐    ┌────┴────┐            │
│     │ Slave1  │    │ Slave2  │    │ Slave3  │            │
│     │ (副本)  │    │ (副本)  │    │ (副本)  │            │
│     └─────────┘    └─────────┘    └─────────┘            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**槽位计算：**

```python
# CRC16算法计算key所属槽位
def slot(key):
    return crc16(key) % 16384

# Redis命令
CLUSTER SLOTS                    # 查看槽位分配
CLUSTER ADDSLOTS <slot>         # 添加槽位
CLUSTER KEYSLOT <key>           # 查看key的槽位

# 客户端重定向
# MOVED <slot> <node_ip:port>
# ASK <slot> <node_ip:port>     # 只在迁移时使用
```

**集群操作：**

```python
import redis

# 连接集群
r = redis.RedisCluster(
    host='localhost',
    port=7000,
    decode_responses=True
)

# 自动路由
r.set('key1', 'value1')    # 自动路由到正确节点
r.get('key1')

# 批量操作（MGET/MSET）需要相同槽位
r.mset({'key1': 'v1', 'key2': 'v2'})  # 要求在同一节点
```

**故障转移：**

```
1. Master节点宕机
2. 从节点检测到主节点不可用
3. 从节点发起选举
4. 多数从节点投票通过
5. 从节点升级为Master
6. 其他节点更新路由表
```

---

### Q15: Redis和Memcached有什么区别？

**题目类型**：技术对比类

**问题描述**：Redis和Memcached有哪些区别？各自的优势是什么？

**答案要点**：

**核心区别对比：**

| 特性 | Redis | Memcached |
|------|-------|-----------|
| 数据类型 | 丰富（5种+） | 只支持String |
| 持久化 | 支持 | 不支持 |
| 集群 | 原生Cluster | 需要第三方 |
| 内存管理 | 自定义内存分配 | slab机制 |
| 线程模型 | 单线程+后台线程 | 多线程 |
| 数据结构 | 优化过的数据结构 | 简单KV |
| 事务 | 支持Lua脚本 | 不支持 |
| 复制 | 支持主从 | 支持主从 |

**选择建议：**

```python
# Memcached适用场景
# - 简单KV缓存
# - 多线程高并发
# - 不需要持久化
# - 内存固定大小

# Redis适用场景
# - 丰富的数据类型
# - 需要持久化
# - 分布式缓存
# - 消息队列
# - 计数器、排行榜
```

---

### Q16: 如何监控Redis？

**题目类型**：场景解决类

**问题描述**：如何监控Redis？有哪些关键指标？

**答案要点**：

**监控命令：**

```redis
# INFO命令 - 获取Redis状态
INFO                          # 所有信息
INFO memory                   # 内存信息
INFO stats                    # 统计信息
INFO replication              # 复制信息
INFO clients                  # 客户端信息
INFO commandstats             # 命令统计

# 实时统计
MONITOR                       # 实时打印命令（仅调试用）

# 慢查询日志
SLOWLOG GET 10               # 获取最近10条慢查询
SLOWLOG RESET                 # 清空慢查询日志

# 配置
slowlog-log-slower-than 1000  # 超过1ms记录
slowlog-max-len 128           # 最多128条
```

**关键指标：**

| 指标 | 说明 | 告警阈值 |
|------|------|----------|
| used_memory | 已使用内存 | >最大内存80% |
| connected_clients | 连接数 | >10000 |
| blocked_clients | 阻塞客户端 | >0 |
| rdb_changes_since_last_save | 未保存变更 | 持续增长 |
| evicted_keys | 淘汰的key数 | >0 |
| keyspace_hits | 缓存命中率 | <80% |

**Python监控示例：**

```python
import redis
import time

def monitor_redis(redis_client):
    """监控Redis关键指标"""
    info = redis_client.info()
    
    metrics = {
        'memory_used': info['used_memory_human'],
        'memory_peak': info['used_memory_peak_human'],
        'clients_connected': info['connected_clients'],
        'total_commands': info['total_commands_processed'],
        'keyspace_hits': info['keyspace_hits'],
        'keyspace_misses': info['keyspace_misses'],
        'hits_rate': info['keyspace_hits'] / 
                      (info['keyspace_hits'] + info['keyspace_misses']) * 100,
        'evicted_keys': info['evicted_keys'],
    }
    
    return metrics

# 建议使用Prometheus + Redis Exporter
```

---

## 第三部分：高级特性（共4题）

### Q17: Redis Sentinel是什么？

**题目类型**：技术原理类

**问题描述**：Redis Sentinel是什么？它是如何实现高可用的？

**答案要点**：

**Sentinel架构：**

```
┌─────────────────────────────────────────────────────────────┐
│                   Redis Sentinel 架构                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│         ┌──────────────────────────────────────┐           │
│         │           Sentinel集群                  │           │
│         │    (1-3个Sentinel节点)                │           │
│         │    ┌────┐ ┌────┐ ┌────┐           │           │
│         │    │ S1 │ │ S2 │ │ S3 │           │           │
│         │    └────┘ └────┘ └────┘           │           │
│         └───────────────┬──────────────────────┘           │
│                         │                                    │
│    ┌───────────────────┼─────────────────────┐            │
│    │                   │                      │            │
│    ▼                   ▼                      ▼            │
│ ┌─────┐            ┌─────┐              ┌─────┐          │
│ │Master│            │Master│              │Master│          │
│ └──┬──┘            └──┬──┘              └──┬──┘          │
│    │                   │                     │             │
│    ▼                   ▼                     ▼             │
│ ┌─────┐            ┌─────┐              ┌─────┐          │
│ │Slave│            │Slave│              │Slave│          │
│ └─────┘            └─────┘              └─────┘          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Sentinel功能：**

```python
# Sentinel监控
# - 定期检查Master/Slave健康状态
# - 自动故障转移
# - 主从切换

# 客户端连接
from redis.sentinel import Sentinel

sentinel = Sentinel([
    ('localhost', 26379),
    ('localhost', 26380),
], socket_timeout=0.1)

# 获取主节点
master = sentinel.master_for('mymaster')
# 获取从节点
slave = sentinel.slave_for('mymaster')

# 自动故障转移时客户端重连
master.set('key', 'value')
```

---

### Q18: Redis Stream是什么？

**题目类型**：技术原理类

**问题描述**：Redis Stream是什么？它与List和Pub/Sub有什么区别？

**答案要点**：

**Stream特点：**

```redis
# 创建Stream
XADD mystream * field1 value1 field2 value2
# * 表示自动生成ID

# 读取消息
XREAD COUNT 10 STREAMS mystream 0
XRANGE mystream - +

# 消费者组
XGROUP CREATE mystream mygroup 0    # 从头开始
XREADGROUP GROUP mygroup consumer1 STREAMS mystream ">"

# 确认消息
XACK mystream mygroup message_id

# 查看消费者组信息
XINFO GROUPS mystream
XINFO CONSUMERS mystream mygroup
```

**对比：**

| 特性 | List | Pub/Sub | Stream |
|------|------|---------|--------|
| 消息持久化 | 支持 | 不支持 | 支持 |
| 消息确认 | 不支持 | 不支持 | 支持 |
| 消费者组 | 不支持 | 不支持 | 支持 |
| 消息回溯 | 不支持 | 不支持 | 支持 |
| 广播 | 不支持 | 支持 | 支持 |
| 消息堆积 | 有限制 | 无 | 可配置 |

**消息队列示例：**

```python
import redis

r = redis.Redis()

# 发送消息
def send_message(stream, data):
    return r.xadd(stream, data)

# 消费消息
def consume_messages(stream, group, consumer):
    # 创建消费者组
    try:
        r.xgroup_create(stream, group, '0')
    except redis.ResponseError:
        pass
    
    # 读取消息
    messages = r.xreadgroup(
        group, consumer,
        {stream: '>'},
        count=10,
        block=5000
    )
    
    for stream_name, entries in messages:
        for msg_id, data in entries:
            # 处理消息
            process(data)
            # 确认消息
            r.xack(stream_name, group, msg_id)
```

---

## 附录：知识点总结

**Redis核心知识点：**

| 类别 | 关键知识点 |
|------|----------|
| 数据类型 | String、Hash、List、Set、ZSet、Stream |
| 持久化 | RDB、AOF、混合持久化 |
| 缓存问题 | 穿透、雪崩、击穿 |
| 集群 | 主从、Sentinel、Cluster |
| 高级特性 | Pipeline、Lua脚本、事务 |
| 监控 | INFO、Slowlog、MONITOR |

---

*本文档共计18道Redis面试题，涵盖数据类型、持久化、集群、缓存设计等核心知识点。*
