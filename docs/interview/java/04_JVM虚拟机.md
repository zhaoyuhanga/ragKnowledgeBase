# JVM虚拟机 - 20K薪资面试题

> 本文档包含JVM虚拟机相关面试题，涵盖内存结构、垃圾回收、类加载、性能调优等核心知识点。

---

## 第一部分：内存结构（共8题）

### Q1: JVM的整体结构是怎样的？

**题目类型**：基础概念类

**问题描述**：JVM的整体结构是什么？有哪些主要的组件？

**答案要点**：

**JVM架构图：**

```
┌─────────────────────────────────────────────────────────────────┐
│                         JVM运行时数据区                          │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐            │
│  │ 方法区  │  │ 堆      │  │ 虚拟机栈│  │ 本地栈  │            │
│  │ Method  │  │ Heap    │  │ VMStack │  │ NatStack│            │
│  │  Area   │  │         │  │         │  │         │            │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘            │
├─────────────────────────────────────────────────────────────────┤
│                        执行引擎                                   │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐            │
│  │ 解释器  │  │ JIT编译 │  │ 垃圾   │  │ 线程   │            │
│  │        │  │  器     │  │ 回收器 │  │ 管理   │            │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘            │
├─────────────────────────────────────────────────────────────────┤
│                        本地库接口                                 │
│                     (JNI, JNI接口)                               │
└─────────────────────────────────────────────────────────────────┘
                              ↓
                    ┌─────────────────┐
                    │    本地方法库    │
                    │ Native Libs     │
                    └─────────────────┘
```

**各组件说明：**

| 组件 | 说明 |
|------|------|
| Class Loader | 类加载器，负责加载.class文件 |
| 运行时数据区 | 存储运行时数据（堆、栈、方法区等） |
| 执行引擎 | 执行字节码，包括解释器和JIT编译器 |
| 本地库接口 | JNI，调用本地方法 |
| 本地方法库 | C/C++本地库 |

---

### Q2: JVM内存区域是如何划分的？各区域的作用是什么？

**题目类型**：基础概念类

**问题描述**：JVM运行时数据区有哪些？各区域的作用和特点是什么？

**答案要点**：

**内存区域划分：**

| 区域 | 线程私有/共享 | 异常 | 大小 |
|------|--------------|------|------|
| 程序计数器 | 私有 | 无 | 固定 |
| 虚拟机栈 | 私有 | StackOverflowError, OOM | 可动态扩展 |
| 本地方法栈 | 私有 | StackOverflowError, OOM | 可动态扩展 |
| 堆 | 共享 | OOM | 可动态扩展 |
| 方法区 | 共享 | OOM | 可动态扩展 |
| 运行时常量池 | 共享 | OOM | 方法区的一部分 |
| 直接内存 | 共享 | OOM | 不在JVM规定范围内 |

**各区域详解：**

```java
// 1. 程序计数器 - 当前线程执行的字节码行号指示器
public class ProgramCounter {
    public static void main(String[] args) {
        // 每条线程有自己的程序计数器
        // 执行Java方法记录字节码地址
        // 执行Native方法为空
    }
}

// 2. 虚拟机栈 - 方法调用的栈帧
public class VMStackDemo {
    public void method1() {
        method2();  // 方法调用
    }
    
    public void method2() {
        int a = 1;
        int b = 2;
        int c = a + b;
    }
    // 每个方法调用创建一个栈帧(Stack Frame)
    // 包含: 局部变量表、操作数栈、动态链接、方法返回地址
}

// 3. 堆 - 对象实例和数组
public class HeapDemo {
    public static void main(String[] args) {
        // new创建的对象分配在堆上
        Object obj = new Object();
        int[] arr = new int[1024];
        
        // GC主要管理的区域
        // 线程共享
    }
}

// 4. 方法区 - 类信息、常量、静态变量
public class MethodAreaDemo {
    // 方法区存储
    static String STATIC_FIELD = "static";  // 静态变量
    static final String CONSTANT = "constant";  // 常量
    
    public void method() {
        // 方法字节码存储在方法区
    }
}
```

**JDK1.8变化：**

| 区域 | JDK1.7 | JDK1.8+ |
|------|--------|---------|
| 方法区 | PermGen（永久代） | Metaspace（元空间） |
| 字符串常量池 | PermGen | 堆中 |
| 静态变量 | PermGen | 堆中 |
| 位置 | 堆内存 | 本地内存（堆外） |

---

### Q3: 什么是堆？堆内存是如何划分的？

**题目类型**：基础概念类

**问题描述**：JVM堆内存是如何划分的？各区域的作用是什么？

**答案要点**：

**堆内存结构（JDK1.7）：**

```
┌────────────────────────────────────────┐
│                  新生代                 │
│  ┌──────────┐         ┌─────────────┐│
│  │  Eden    │ S0(Survivor)│ S1(Survivor)││
│  │  伊甸园区 │   幸存区0  │    幸存区1   ││
│  └──────────┘         └─────────────┘│
│        8/10              1/10         │
└────────────────────────────────────────┘
                    │
                    │ 老年代
              ┌─────┴─────┐
              │   Old Gen  │
              │   老年代    │
              └───────────┘
                     │
                     │ 1/2
```

**各区域作用：**

| 区域 | 比例 | 说明 |
|------|------|------|
| Eden | 80% | 新对象分配区域 |
| Survivor S0 | 10% | 幸存者区域1 |
| Survivor S1 | 10% | 幸存者区域2 |
| Old Generation | 50% | 长寿对象、 大对象 |

**对象分配过程：**

```java
public class ObjectAllocation {
    public static void main(String[] args) {
        // 对象分配优先在Eden区
        Object obj = new Object();  // 优先分配到Eden
        
        // 大对象直接进入老年代
        // -XX:PretenureSizeThreshold=1M
        byte[] large = new byte[2 * 1024 * 1024];  // 直接进入老年代
        
        // 长期存活的对象进入老年代
        // -XX:MaxTenuringThreshold=15（默认15次）
        // 对象每经过一次Minor GC，年龄+1
        // 年龄达到阈值后进入老年代
    }
}
```

**对象晋升老年代的条件：**
1. 年龄达到MaxTenuringThreshold（默认15）
2. Survivor区相同年龄所有对象大小之和 > Survivor空间的一半

---

### Q4: 什么是栈？栈帧的结构是什么？

**题目类型**：技术原理类

**问题描述**：JVM虚拟机栈是什么？栈帧由哪些部分组成？

**答案要点**：

**栈帧结构：**

```
┌──────────────────────────────┐
│      栈帧 Frame              │
├──────────────────────────────┤
│  ┌────────────────────────┐  │
│  │  局部变量表 Local Vars │  │
│  │  - 方法参数           │  │
│  │  - 局部变量           │  │
│  └────────────────────────┘  │
├──────────────────────────────┤
│  ┌────────────────────────┐  │
│  │  操作数栈 Operand Stack│  │
│  │  - 计算中间结果       │  │
│  │  - 方法参数压栈/出栈  │  │
│  └────────────────────────┘  │
├──────────────────────────────┤
│  ┌────────────────────────┐  │
│  │  动态链接 Dynamic Link │  │
│  │  - 指向常量池引用     │  │
│  └────────────────────────┘  │
├──────────────────────────────┤
│  ┌────────────────────────┐  │
│  │  返回地址 Return Addr  │  │
│  │  - 方法返回位置       │  │
│  └────────────────────────┘  │
└──────────────────────────────┘
```

**局部变量表：**

```java
public class LocalVarsDemo {
    public int method(int a, int b) {
        int c = 10;
        int d = c + a + b;
        return d;
    }
}

// 字节码分析
// 方法的局部变量表：
// 0: this (非静态方法)
// 1: int a
// 2: int b
// 3: int c
// 4: int d
```

**操作数栈示例：**

```java
public int calculate() {
    int a = 10;
    int b = 20;
    int c = a + b;
    return c;
}

// 字节码
// 0: bipush 10    -> 操作数栈: [10]
// 2: istore_1     -> 变量a = 10, 操作数栈: []
// 3: bipush 20    -> 操作数栈: [20]
// 5: istore_2     -> 变量b = 20, 操作数栈: []
// 6: iload_1       -> 操作数栈: [10]
// 7: iload_2       -> 操作数栈: [10, 20]
// 8: iadd          -> 操作数栈: [30]
// 9: istore_3      -> 变量c = 30, 操作数栈: []
// 10: iload_3      -> 操作数栈: [30]
// 11: ireturn
```

---

### Q5: 什么是直接内存？它有什么作用？

**题目类型**：基础概念类

**问题描述**：什么是直接内存？它与堆内存有什么区别？

**答案要点**：

**直接内存特点：**

| 特性 | 堆内存 | 直接内存 |
|------|--------|----------|
| 位置 | JVM堆 | 本地内存 |
| 管理 | GC管理 | 手动管理 |
| 垃圾回收 | 会回收 | 需要手动释放 |
| IO性能 | 需要复制 | 零拷贝，性能高 |
| 大小 | 受堆限制 | 受物理内存限制 |
| 分配 | new操作 | ByteBuffer.allocateDirect() |

**使用场景：**

```java
// 1. NIO中的ByteBuffer
// JDK1.4引入的NIO使用直接内存
import java.nio.ByteBuffer;

public class DirectMemoryDemo {
    public static void main(String[] args) {
        // 堆内存缓冲区
        ByteBuffer heapBuffer = ByteBuffer.allocate(1024);
        
        // 直接内存缓冲区 - 避免JVM堆和本地内存之间的复制
        ByteBuffer directBuffer = ByteBuffer.allocateDirect(1024);
        
        // 适用场景：
        // - 需要频繁IO操作
        // - 大量数据交换
        // - 减少GC压力
    }
}

// 2. 性能对比
// 传统IO: 磁盘 → 内核缓冲区 → 用户缓冲区 → 应用
// NIO直接内存: 磁盘 → 内核缓冲区 → 直接内存缓冲区 → 应用
//            ↓（零拷贝）
//           网络
```

**配置参数：**

```bash
# 设置直接内存大小
-Xmx256m -XX:MaxDirectMemorySize=512m

# 默认与-Xmx相同或物理内存的1/4
```

**注意事项：**
```java
// 直接内存溢出处理
// -XX:+DisableExplicitGC 会影响直接内存回收
// 建议显式调用 System.gc() 或使用 Cleaner 释放

public class DirectMemoryCleanup {
    public static void main(String[] args) throws IOException {
        // 分配直接内存
        ByteBuffer buffer = ByteBuffer.allocateDirect(1024 * 1024 * 100);
        
        // 手动释放（JDK9+）
        // buffer = null;
        // System.gc();
    }
}
```

---

### Q6: 什么是Minor GC和Major GC/Full GC？

**题目类型**：基础概念类

**问题描述**：JVM中的Minor GC、Major GC和Full GC有什么区别？

**答案要点**：

**GC分类：**

| 类型 | 发生区域 | 触发条件 | 停顿时间 |
|------|----------|----------|----------|
| Minor GC | 新生代 | Eden区满 | 短 |
| Major GC | 老年代 | 老年代满 | 长 |
| Full GC | 全堆 | 老年代满/显式调用 | 最长 |

**触发条件对比：**

```java
// Minor GC触发条件
// Eden区空间不足
public class MinorGCDemo {
    public static void main(String[] args) {
        // 频繁创建对象，填满Eden区
        while(true) {
            byte[] obj = new byte[1024 * 1024];  // 1MB对象
        }
    }
}

// Full GC触发条件
public class FullGCDemo {
    // 1. 老年代空间不足
    // 2. System.gc()调用
    // 3. 元空间不足
    // 4. 对象晋升失败（老年代空间不足容纳大对象）
    // 5. GC Roots增加导致空间不足
}
```

**GC过程：**

```
┌─────────┐
│  Eden   │ ────────────────────── Minor GC ────► 新对象
└────┬────┘
     │ 对象超过 Survivor 容量 或 年龄达到阈值
     ↓
┌─────────┐
│   Old   │ ◄─────── Major/Full GC ────────── 老年代对象
└─────────┘
     │
     │ Full GC (全堆扫描)
     ↓
┌─────────┐
│ Metaspace│ ◄─── Metaspace GC ───────────── 类卸载
└─────────┘
```

**优化建议：**
- Minor GC频繁 → 增大新生代
- Full GC频繁 → 检查对象生命周期
- 避免大对象直接进入老年代

---

### Q7: 什么是逃逸分析？它有什么作用？

**题目类型**：技术原理类

**问题描述**：什么是逃逸分析？JVM如何通过逃逸分析进行优化？

**答案要点**：

**逃逸分析定义：**
分析对象的动态作用域，判断对象是否逃逸出方法或线程。

**逃逸类型：**

```java
public class EscapeAnalysisDemo {
    
    // 情况1：没有逃逸 - 标量替换
    public void noEscape() {
        int x = 10;  // 局部变量，不需要分配对象
        Point p = new Point(1, 2);  // 如果p不逃逸，可能被优化
    }
    
    // 情况2：方法逃逸
    public Point methodEscape() {
        Point p = new Point(1, 2);
        return p;  // 对象作为返回值，逃逸
    }
    
    // 情况3：线程逃逸
    public static Point shared;  // 类变量，线程间共享
    
    public void threadEscape() {
        Point p = new Point(1, 2);
        shared = p;  // 被其他线程访问，线程逃逸
    }
}
```

**逃逸分析优化：**

| 优化方式 | 说明 | 条件 |
|----------|------|------|
| 栈上分配 | 对象在栈上分配，线程退出时自动释放 | 方法内创建，线程不逃逸 |
| 标量替换 | 将对象拆解为原始类型 | 对象不逃逸 |
| 同步消除 | 消除不必要的同步 | 锁对象不逃逸 |

```java
// 栈上分配示例（JIT优化）
public class StackAllocation {
    public static void main(String[] args) {
        long start = System.currentTimeMillis();
        for (int i = 0; i < 100_000_000; i++) {
            allocate();
        }
        long end = System.currentTimeMillis();
        System.out.println("耗时: " + (end - start) + "ms");
    }
    
    static void allocate() {
        // 如果没有逃逸，JIT可能进行栈上分配
        byte[] bytes = new byte[2];
        bytes[0] = 1;
        bytes[1] = 2;
    }
}

// JVM参数
// -XX:+DoEscapeAnalysis  开启逃逸分析（默认开启）
// -XX:+EliminateAllocations  开启标量替换（默认开启）
```

---

### Q8: 对象创建的过程是怎样的？

**题目类型**：技术原理类

**问题描述**：Java中对象的创建过程是怎样的？内存是如何分配的？

**答案要点**：

**对象创建步骤：**

```java
public class ObjectCreation {
    public static void main(String[] args) {
        Object obj = new Object();
        // 对象创建过程：
    }
}
```

**创建过程详解：**

```
1. 类加载检查
   │
   ├── 检查常量池中是否有该类的符号引用
   ├── 检查是否已加载、解析和初始化
   │
   ▼
2. 分配内存
   │
   ├── 分配方式：
   │   ├── 指针碰撞（Bump the Pointer）- 规整内存
   │   └── 空闲列表（Free List）- 不规整内存
   │
   ├── 线程安全问题：
   │   ├── CAS + 重试
   │   └── TLAB（Thread Local Allocation Buffer）
   │
   ▼
3. 初始化零值
   │
   ├── 将分配到的内存空间初始化为零值
   ├── 保证对象的实例字段可以不赋初值直接使用
   │
   ▼
4. 设置对象头
   │
   ├── Mark Word（哈希码、GC年龄、锁状态等）
   ├── 指向类元数据的指针
   ├── 数组长度（如果是数组）
   │
   ▼
5. 执行构造函数
   │
   └── <init>方法执行
```

**内存分配方式：**

```java
// 指针碰撞
// 适用于：Serial、ParNew等带compact过程的收集器
// 原理：堆内存规整，一边是已用空间，一边是空闲空间
// 分配：移动指针

// 空闲列表
// 适用于：CMS等基于Mark-Sweep的收集器
// 原理：堆内存不规整，维护一个空闲列表
// 分配：从列表中找到足够大的空间
```

**TLAB（线程本地分配缓冲）：**

```bash
# -XX:+UseTLAB  开启TLAB（默认开启）
# -XX:TLABSize  设置TLAB大小
# -XX:+PrintTLAB  打印TLAB信息

# TLAB工作原理：
# 每个线程在Eden区预分配一块缓存
# 线程在自己的TLAB中分配对象
# 避免多线程分配冲突
```

---

## 第二部分：垃圾回收（共8题）

### Q9: 如何判断对象是否需要回收？有哪些算法？

**题目类型**：技术原理类

**问题描述**：JVM如何判断一个对象是否需要回收？有哪些回收算法？

**答案要点**：

**引用计数算法：**

```java
// 原理：对象每被引用一次，计数器+1，引用失效-1
// 计数器为0时被回收

// 问题：无法处理循环引用
public class ReferenceCounting {
    public static void main(String[] args) {
        // 循环引用示例
        Node a = new Node();
        Node b = new Node();
        a.next = b;  // b引用计数+1
        b.next = a;  // a引用计数+1
        
        // 虽然没有其他引用，但计数不为0
        // 引用计数算法无法回收
    }
}
```

**可达性分析算法：**

```java
// 原理：从GC Roots开始向下搜索，标记可达对象
// 不可达的对象被回收

// GC Roots包括：
// 1. 虚拟机栈（栈帧中的本地变量表）中引用的对象
// 2. 方法区中静态属性引用的对象
// 3. 方法区中常量引用的对象
// 4. 本地方法栈中JNI引用的对象
// 5. JVM内部引用（Class对象、异常对象等）
// 6. 同步锁持有的对象
// 7. 类加载器

public class GC roots {
    // GC Roots 示例
    static Object staticObj = new Object();  // 静态变量 - GC Root
    
    public static void main(String[] args) {
        Object localVar = new Object();  // 局部变量 - GC Root
        
        method();
    }
    
    public static void method() {
        // 等待方法执行完毕
    }
}
```

**引用类型：**

| 类型 | 说明 | 回收时机 |
|------|------|----------|
| 强引用 | Object obj = new Object() | 永远不会回收 |
| 软引用 | SoftReference | 内存不足时回收 |
| 弱引用 | WeakReference | 下次GC时回收 |
| 虚引用 | PhantomReference | 随时可能被回收 |

```java
public class ReferenceTypes {
    public static void main(String[] args) {
        // 强引用
        Object strong = new Object();
        
        // 软引用 - 适合缓存
        SoftReference<Object> soft = new SoftReference<>(new Object());
        if (soft.get() != null) {
            // 对象还在
        }
        
        // 弱引用 - 适合缓存/注册表
        WeakReference<Object> weak = new WeakReference<>(new Object());
        if (weak.get() != null) {
            // 对象还在
        }
        
        // 虚引用 - 用于跟踪对象回收
        ReferenceQueue<Object> queue = new ReferenceQueue<>();
        PhantomReference<Object> phantom = new PhantomReference<>(
            new Object(), queue);
    }
}
```

---

### Q10: 常见的垃圾收集算法有哪些？

**题目类型**：技术原理类

**问题描述**：JVM中有哪些垃圾收集算法？各自的特点是什么？

**答案要点**：

**四种基础算法：**

```java
// 1. 标记-清除算法（Mark-Sweep）
// 标记存活对象，然后清除未标记对象
// 缺点：产生内存碎片
/*
┌─────────────────────────────┐
│ 标记阶段:                   │
│ [X][X][  ][  ][X][  ]     │
│   ↑     ↑       ↑         │
│ 标记存活对象                 │
├─────────────────────────────┤
│ 清除阶段:                   │
│ [X][X][  ][  ][X][  ] → [X][X][X]   │
│           产生碎片          │
└─────────────────────────────┘
*/

// 2. 复制算法（Copying）
// 将内存分成两块，每次只使用一块
// 优点：无碎片
// 缺点：可用内存减半
/*
┌─────────────┬─────────────┐
│    From     │     To      │
│ [A][B][C][  ]│             │
└──────┬──────┴─────────────┘
       │ 复制存活对象
       ↓
┌─────────────────────────────┐
│             To              │
│    [A][B][C]                │
└─────────────────────────────┘
*/

// 3. 标记-整理算法（Mark-Compact）
// 标记后移动存活对象，清理边界
// 优点：无碎片，适合老年代
/*
┌─────────────────────────────┐
│ 整理前:                    │
│ [X][  ][X][  ][X][  ]      │
│       ↓ 移动存活对象        │
├─────────────────────────────┤
│ 整理后:                    │
│ [X][X][X][  ][  ][  ]      │
│       紧凑排列              │
└─────────────────────────────┘
*/

// 4. 分代收集算法（Generational）
// 根据对象存活周期划分不同区域
// 新生代：复制算法（对象存活率低）
// 老年代：标记-整理算法（对象存活率高）
```

**算法对比：**

| 算法 | 优点 | 缺点 | 适用区域 |
|------|------|------|----------|
| 标记-清除 | 无需移动对象 | 产生碎片 | 老年代 |
| 复制 | 无碎片，实现简单 | 可用内存减半 | 新生代 |
| 标记-整理 | 无碎片 | 需要移动对象 | 老年代 |
| 分代收集 | 综合优化 | 参数调优复杂 | 通用 |

---

### Q11: 常见的垃圾收集器有哪些？

**题目类型**：技术原理类

**问题描述**：JVM有哪些垃圾收集器？各自的特点和适用场景是什么？

**答案要点**：

**收集器关系图：**

```
┌─────────────────────────────────────────────────────────────────┐
│                        垃圾收集器                                │
├─────────────────────────────────────────────────────────────────┤
│ 新生代收集器           │  老年代收集器                           │
│ ─────────────          │  ─────────────                         │
│ Serial (串行)          │  Serial Old (串行)                     │
│ ParNew (并行)          │  Parallel Old (并行)                   │
│ Parallel Scavenge      │  CMS                                   │
│                        │  G1                                    │
│                        │  ZGC (JDK11+)                          │
│                        │  Shenandoah (JDK12+)                    │
└─────────────────────────────────────────────────────────────────┘
```

**各收集器详解：**

```java
// 1. Serial收集器 - 单线程，最古老
// -XX:+UseSerialGC
// 特点：简单高效，Stop The World
// 适用：Client模式，几十MB内存

// 2. ParNew收集器 - Serial的多线程版本
// -XX:+UseParNewGC
// 特点：多线程并行，Stop The World
// 适用：多CPU服务器，配合CMS

// 3. Parallel Scavenge收集器 - 吞吐量优先
// -XX:+UseParallelGC
// 特点：吞吐量高，可自适应调节
// 参数：-XX:MaxGCPauseMillis, -XX:GCTimeRatio

// 4. Serial Old收集器 - Serial老年代版本
// -XX:+UseSerialOldGC
// 特点：标记-整理算法

// 5. Parallel Old收集器 - Parallel老年代版本
// -XX:+UseParallelOldGC
// 特点：标记-整理，多线程

// 6. CMS收集器 - 短停顿优先
// -XX:+UseConcMarkSweepGC
// 特点：
// - 初始标记（STW）- 标记GC Roots
// - 并发标记 - 追踪存活对象
// - 重新标记（STW）- 修正并发标记
// - 并发清除 - 清理垃圾
// 缺点：CPU敏感，产生碎片

// 7. G1收集器 - 面向服务端的收集器
// -XX:+UseG1GC
// 特点：
// - 整体标记-整理，局部复制
// - 划分多个Region
// - 可预测停顿时间
// 参数：-XX:MaxGCPauseMillis
```

**收集器对比：**

| 收集器 | 线程 | 停顿时间 | 吞吐量 | 适用场景 |
|--------|------|----------|--------|----------|
| Serial | 单 | 长 | 低 | Client、少量内存 |
| ParNew | 多 | 长 | 中 | 多CPU、配合CMS |
| Parallel Scavenge | 多 | 长 | 高 | 后台计算 |
| CMS | 多 | 短 | 中 | 互联网服务 |
| G1 | 多 | 可控 | 高 | 大内存服务端 |

---

### Q12: G1收集器是如何工作的？

**题目类型**：技术原理类

**问题描述**：G1收集器是什么？它是如何工作的？有哪些特点？

**答案要点**：

**G1特点：**

```java
// G1 (Garbage First) 收集器特点：
// 1. 面向服务端应用
// 2. 将堆划分为多个大小相等的Region
// 3. 优先回收价值最大的Region
// 4. 可预测停顿时间模型
// 5. 整体标记-整理，局部复制
```

**Region结构：**

```
┌────────────────────────────────────────────────────────┐
│                    G1 Heap                             │
│                                                        │
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐         │
│  │ Eden │ │ Eden │ │ Eden │ │ Eden │ │ Eden │ ...    │
│  └──────┘ └──────┘ └──────┘ └──────┘ └──────┘         │
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐                  │
│  │ S0   │ │ S1   │ │ Old  │ │ Old  │ ...              │
│  └──────┘ └──────┘ └──────┘ └──────┘                  │
│  ┌──────┐ ┌──────┐ ┌──────┐                            │
│  │ Humongous │ │ Humongous │ │ 未使用 │                │
│  │ (大对象区) │ │           │ │        │                │
│  └──────┘ └──────┘ └──────┘                            │
│                                                        │
│  ┌──────────────────────────────────────┐             │
│  │          Card Table                   │             │
│  └──────────────────────────────────────┘             │
└────────────────────────────────────────────────────────┘

// Region大小：1MB - 32MB（必须是2的幂）
// Humongous区：超过Region 50%的对象
```

**GC过程：**

```
┌─────────────────────────────────────────────────────────┐
│  1. 年轻代GC (Young GC)                                 │
│  - Eden区满时触发                                       │
│  - 复制到Survivor区或晋升到Old区                        │
│  - Stop The World，但停顿时间可控                       │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  2. Mixed GC                                           │
│  - 收集所有年轻代 + 部分老年代                          │
│  - 由参数控制收集比例                                   │
│  - -XX:InitiatingHeapOccupancyPercent (默认45%)        │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  3. Full GC (可能发生)                                 │
│  - 并发模式失败                                        │
│  - 晋升失败                                            │
│  - 分配失败                                            │
└─────────────────────────────────────────────────────────┘
```

**配置参数：**

```bash
# 启用G1
-XX:+UseG1GC

# 设置停顿时间目标
-XX:MaxGCPauseMillis=200

# 设置Region大小
-XX:G1HeapRegionSize=4m

# 设置Mixed GC比例
-XX:InitiatingHeapOccupancyPercent=45

# 设置每次Mixed GC回收的Region比例
-XX:G1OldCSetRegionThresholdPercent=10
```

---

### Q13: ZGC和Shenandoah收集器有什么特点？

**题目类型**：技术原理类

**问题描述**：ZGC和Shenandoah收集器是什么？它们有哪些特点？

**答案要点**：

**ZGC收集器（JDK11+）：**

```java
// ZGC (Z Garbage Collector) 特点：
// 1. 低停顿 - 停顿时间控制在10ms以内
// 2. 并发执行 - 大部分工作与应用线程并发
// 3. 可扩展 -停顿时间不随堆大小增加而增加
// 4. 着色指针 - 使用指针着色技术跟踪对象状态
```

**ZGC原理：**

```java
// 着色指针技术
// 42位地址中保留几位作为标记位
// 每次GC时，改变对象引用的标记位
// 应用程序看到的总是有效地址

// ZGC阶段
// 1. Pause Mark Start - 初始标记（STW）
// 2. Concurrent Mark - 并发标记
// 3. Pause Mark End - 再标记（STW）
// 4. Concurrent Prepare for Relocate - 准备重定位
// 5. Pause Relocate Start - 初始重定位（STW）
// 6. Concurrent Relocate - 并发重定位
// 7. Concurrent Remap - 并发重映射
```

**Shenandoah收集器（JDK12+）：**

```java
// Shenandoah特点：
// 1. 低停顿 - 类似ZGC
// 2. OpenJDK社区开发
// 3. 转发指针 - 在对象头添加指针
// 4. 可与CMS等其他收集器协作
```

**对比：**

| 特性 | ZGC | Shenandoah |
|------|-----|------------|
| 首次引入 | JDK11 | JDK12 |
| 停顿时间 | <10ms | <10ms |
| 吞吐量影响 | <15% | <15% |
| 内存开销 | 着色指针 | 转发指针 |
| 并发整理 | 是 | 是 |
| 支持老年代 | 是 | 是 |
| 分代支持 | JDK15+实验支持 | 无 |
| 生产可用 | JDK15+ | JDK12+ |

**配置：**

```bash
# ZGC配置
-XX:+UseZGC
-XX:MaxGCPauseMillis=10
-Xmx16g

# Shenandoah配置
-XX:+UseShenandoahGC
-XX:MaxGCPauseMillis=10
```

---

### Q14: 什么是Stop The World？如何优化？

**题目类型**：技术原理类

**问题描述**：Stop The World是什么？为什么需要它？如何优化？

**答案要点**：

**Stop The World定义：**
垃圾回收时，暂停所有应用线程（除GC线程外），直到GC完成。

```java
// STW演示
public class STWDemo {
    public static void main(String[] args) {
        // 假设此时发生GC
        System.out.println("开始");
        // ... GC发生，线程暂停
        System.out.println("结束");  // GC完成后才执行
    }
}
```

**不可避免的STW：**

| 阶段 | 原因 |
|------|------|
| 初始标记 | 标记GC Roots直接引用的对象 |
| 再标记 | 修正并发标记期间产生的变化 |
| 根扫描 | 扫描所有GC Roots |

**优化策略：**

```java
// 1. 选择合适的收集器
// CMS和G1减少停顿时间
// ZGC和Shenandoah实现并发GC

// 2. 调整GC参数
// -XX:MaxGCPauseMillis=200  设置停顿目标
// -XX:GCTimeRatio=99        设置吞吐量目标

// 3. 减少GC频率
// 对象池化重用
// 基本类型替代包装类型
// 合理设置对象生命周期

// 4. 减少年轻代大小（但可能增加GC频率）
// -Xmn512m  设置年轻代大小

// 5. 代码层面优化
public class CodeOptimization {
    // 避免创建大量临时对象
    public String bad() {
        String s = "";
        for (int i = 0; i < 100; i++) {
            s += "item" + i;  // 每次循环创建新StringBuilder
        }
        return s;
    }
    
    public String good() {
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < 100; i++) {
            sb.append("item").append(i);
        }
        return sb.toString();
    }
}
```

---

### Q15: 什么是Minor GC、Major GC和Full GC？如何优化？

**题目类型**：场景解决类

**问题描述**：Minor GC、Major GC和Full GC有什么区别？如何优化GC性能？

**答案要点**：

**GC类型对比：**

```java
// Minor GC - 新生代垃圾收集
// 触发条件：Eden区空间不足
// 特点：频率高，停顿时间短
// 优化：增大Eden区或Survivor区

// Major GC - 老年代垃圾收集
// 触发条件：老年代空间不足
// 特点：停顿时间长
// 优化：增大老年代或优化对象分配

// Full GC - 全堆垃圾收集
// 触发条件：
//   - 老年代空间不足
//   - 元空间不足
//   - System.gc()调用
//   - Minor GC前检查到老年代空间不足
// 特点：停顿时间最长
// 优化：全面优化
```

**优化实践：**

```bash
# 1. 监控GC日志
-Xlog:gc*:file=gc.log:time:filecount=5,filesize=10M

# 2. 推荐参数配置
# 吞吐量优先场景
java -Xmx4g -Xms4g \
     -XX:+UseParallelGC \
     -XX:+UseParallelOldGC \
     -XX:MaxGCPauseMillis=500 \
     -XX:GCTimeRatio=19 \
     MyApp

# 延迟敏感场景
java -Xmx4g -Xms4g \
     -XX:+UseG1GC \
     -XX:MaxGCPauseMillis=200 \
     -XX:InitiatingHeapOccupancyPercent=45 \
     MyApp
```

**常见问题与解决：**

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| Minor GC频繁 | Eden区太小 | -Xmn增大或 SurvivorRatio调整 |
| Full GC频繁 | 对象过早晋升 | 增大Survivor或年龄阈值 |
| GC停顿过长 | 大堆+传统收集器 | 使用G1/ZGC |
| 内存持续增长 | 内存泄漏 | 检查代码或增加堆大小 |

---

## 第三部分：类加载机制（共5题）

### Q16: 什么是类加载机制？类加载的过程是什么？

**题目类型**：技术原理类

**问题描述**：JVM类加载机制是什么？类加载的过程分为哪几步？

**答案要点**：

**类加载过程：**

```
┌─────────────────────────────────────────────────────────┐
│                 类加载全过程                              │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  1. 加载 (Loading)                                     │
│     ├── 通过类的全限定名获取类的二进制字节流             │
│     ├── 将字节流转换为方法区运行时数据结构               │
│     └── 生成java.lang.Class对象作为访问入口             │
│                                                         │
│  2. 验证 (Verification)                                │
│     ├── 文件格式验证                                    │
│     ├── 元数据验证                                      │
│     ├── 字节码验证                                      │
│     └── 符号引用验证                                    │
│                                                         │
│  3. 准备 (Preparation)                                 │
│     └── 为类变量分配内存，设置初始值                     │
│                                                         │
│  4. 解析 (Resolution)                                  │
│     └── 将符号引用转换为直接引用                         │
│                                                         │
│  5. 初始化 (Initialization)                             │
│     └── 执行<clinit>方法，初始化类变量                   │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

**各阶段详解：**

```java
// 1. 加载 - 类的二进制字节流来源
// - Class文件
// - JAR/WAR包
// - 网络
// - 动态代理生成
// - 其他源

// 2. 验证 - 确保Class文件格式正确
// - 是否以0xCAFEBABE开头
// - 版本号是否支持
// - 元数据完整性
// - 字节码有效性

// 3. 准备 - 为static变量分配内存
public class PrepareDemo {
    static int a = 10;      // 准备阶段: a=0
    static final int b = 20; // 准备阶段: b=20 (编译时常量)
}

// 4. 解析 - 符号引用转为直接引用
// 符号引用：CONSTANT_Class_info, CONSTANT_Methodref_info等
// 直接引用：内存地址、偏移量

// 5. 初始化 - 执行static代码块
public class InitDemo {
    static int a;
    static {
        a = 10;  // <clinit>中执行
        System.out.println("初始化");
    }
}
```

---

### Q17: 有哪些类加载器？它们的关系是什么？

**题目类型**：基础概念类

**问题描述**：JVM有哪些类加载器？它们之间是什么关系？

**答案要点**：

**三层类加载器结构：**

```
┌────────────────────────────────────────┐
│       Bootstrap ClassLoader            │
│   (启动类加载器，C++实现，jvm.dll)      │
│   加载JAVA_HOME/lib下的核心类库        │
└────────────────┬───────────────────────┘
                 │ 继承(不是，是委托)
                 ↓
┌────────────────────────────────────────┐
│       Extension ClassLoader            │
│     (扩展类加载器, Launcher$ExtClassLoader)
│   加载JAVA_HOME/lib/ext下的类          │
└────────────────┬───────────────────────┘
                 │ 委托
                 ↓
┌────────────────────────────────────────┐
│       Application ClassLoader          │
│   (应用类加载器, Launcher$AppClassLoader)
│   加载classpath下的类                  │
└────────────────┬───────────────────────┘
                 │
                 ↓
┌────────────────────────────────────────┐
│       自定义类加载器                    │
│     (User ClassLoader)                 │
│   加载指定路径下的类                    │
└────────────────────────────────────────┘
```

**类加载器代码：**

```java
public class ClassLoaderDemo {
    public static void main(String[] args) {
        // 获取各类加载器
        ClassLoader loader = ClassLoaderDemo.class.getClassLoader();
        
        System.out.println("应用类加载器: " + loader);
        System.out.println("扩展类加载器: " + loader.getParent());
        System.out.println("启动类加载器: " + loader.getParent().getParent());
        
        // 输出示例:
        // 应用类加载器: sun.misc.Launcher$AppClassLoader@18b4aac2
        // 扩展类加载器: sun.misc.Launcher$ExtClassLoader@4e25154f
        // 启动类加载器: null (由C++实现)
    }
}

// 自定义类加载器
public class MyClassLoader extends ClassLoader {
    private String classPath;
    
    public MyClassLoader(String classPath) {
        this.classPath = classPath;
    }
    
    @Override
    protected Class<?> findClass(String name) throws ClassNotFoundException {
        byte[] classData = loadClassData(name);
        if (classData == null) {
            throw new ClassNotFoundException();
        }
        return defineClass(name, classData, 0, classData.length);
    }
    
    private byte[] loadClassData(String name) {
        // 从指定路径加载class文件
        String fileName = classPath + File.separator + 
            name.replace('.', File.separatorChar) + ".class";
        // ... 读取文件
        return data;
    }
}
```

**双亲委派模型：**

```java
// 双亲委派模型原理
protected Class<?> loadClass(String name, boolean resolve) {
    synchronized (getClassLoadingLock(name)) {
        // 1. 检查类是否已加载
        Class<?> c = findLoadedClass(name);
        if (c == null) {
            try {
                // 2. 优先让父加载器加载
                if (parent != null) {
                    c = parent.loadClass(name, false);
                } else {
                    // 3. 父加载器为空，尝试Bootstrap
                    c = findBootstrapClassOrNull(name);
                }
            } catch (ClassNotFoundException e) {
                // 父加载器找不到
            }
            
            // 4. 父加载器找不到，自己加载
            if (c == null) {
                c = findClass(name);
            }
        }
        
        if (resolve) {
            resolveClass(c);
        }
        return c;
    }
}

// 好处：
// 1. 保证类的唯一性
// 2. 保证核心类的安全（不被篡改）
// 例如：java.lang.Object始终由Bootstrap加载
```

---

### Q18: 什么是双亲委派模型？如何打破它？

**题目类型**：技术原理类

**问题描述**：双亲委派模型是什么？为什么需要它？如何打破它？

**答案要点**：

**双亲委派流程：**

```
┌─────────────────────────────────────────────────────────┐
│                    类加载请求                            │
└────────────────────────┬────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│                 检查是否已加载                           │
│              findLoadedClass(name)                       │
└────────────────────────┬────────────────────────────────┘
                         ↓
              ┌──────────┴──────────┐
              │     parent != null   │
              ↓                     ↓
         ┌─────┴─────┐         ┌─────┴─────┐
         │   有父加载器  │         │   无父加载器  │
         │  父加载器    │         │  Bootstrap │
         │ loadClass  │         │  findBootstrap│
         └─────┬─────┘         └────────────┘
               │                       │
               └──────────┬────────────┘
                          ↓
         ┌────────────────────────────────┐
         │      父加载器找不到             │
         │       findClass(name)         │
         │       自己加载                 │
         └────────────────────────────────┘
```

**为什么需要双亲委派：**

```java
// 1. 保证类的唯一性
// 2. 保证核心类库的安全
// 3. 防止类的重复加载

// 举例：用户自定义java.lang.String
// 会被Bootstrap类加载器加载
// 核心的String类不会被自定义的类覆盖

// 问题场景：JDBC驱动加载
// SPI (Service Provider Interface)
// DriverManager被Bootstrap加载
// 但驱动由Application加载
// 需要打破双亲委派
```

**打破双亲委派的方式：**

```java
// 1. SPI机制 - Service Loader
// Thread.currentThread().setContextClassLoader()
public class SPIDemo {
    public static void main(String[] args) {
        // 设置线程上下文类加载器
        Thread.currentThread().setContextClassLoader(
            new MyClassLoader());
        
        // SPI会使用这个类加载器
        ServiceLoader<Driver> loader = 
            ServiceLoader.load(Driver.class);
    }
}

// 2. 热部署/热替换
// OSGi, JDWP等框架

// 3. Tomcat自定义类加载器
public class TomcatClassLoader {
    // WebAppClassLoader - 加载WEB-INF/lib和classes
    // 优先加载本地类，不遵循双亲委派
    
    // CommonClassLoader - 加载Tomcat核心类
    // 遵循双亲委派
}
```

---

### Q19: 什么是运行时数据区？线程共享和线程私有的区域有哪些？

**题目类型**：基础概念类

**问题描述**：JVM运行时数据区包括哪些区域？哪些是线程私有的？哪些是线程共享的？

**答案要点**：

**区域划分：**

| 区域 | 线程私有 | 说明 |
|------|----------|------|
| 程序计数器 | 是 | 当前线程字节码行号 |
| 虚拟机栈 | 是 | 方法调用的栈帧 |
| 本地方法栈 | 是 | Native方法栈帧 |
| 堆 | 否 | 对象实例、数组 |
| 方法区 | 否 | 类信息、常量、静态变量 |
| 运行时常量池 | 否 | 方法区的一部分 |
| 直接内存 | 否 | 本地内存，堆外 |

**线程私有区域详解：**

```java
// 1. 程序计数器
// - 记录当前线程执行的字节码地址
// - 执行Native方法时为空(Undefined)
// - 唯一没有OutOfMemoryError的区域

// 2. 虚拟机栈
// - 每个方法调用创建一个栈帧
// - 栈帧包含：局部变量表、操作数栈、动态链接、方法返回地址
// - 异常：StackOverflowError（栈深度不够）、OOM（内存不足）

public class VMStackDemo {
    // 递归调用可能导致栈溢出
    public int compute() {
        return compute() + 1;  // 无限递归
    }
    
    // 参数设置
    // -Xss1m  设置栈大小为1MB
}

// 3. 本地方法栈
// - 为Native方法服务
// - HotSpot将本地方法栈和虚拟机栈合一
```

**线程共享区域详解：**

```java
// 1. 堆（Heap）
// - 几乎所有对象实例在这里分配
// - GC的主要管理区域
// - 分为新生代和老年代

// 2. 方法区（Method Area）
// - 存储：类信息、运行时常量池、静态变量、JIT编译代码
// - JDK1.8前使用PermGen（永久代）
// - JDK1.8+使用Metaspace（元空间）
//   - 使用本地内存
//   - 可自动扩展

// 参数配置
// JDK1.7
// -XX:PermSize=128m
// -XX:MaxPermSize=256m

// JDK1.8+
// -XX:MetaspaceSize=128m
// -XX:MaxMetaspaceSize=512m
```

---

### Q20: 如何排查JVM问题？有哪些常用工具？

**题目类型**：场景解决类

**问题描述**：如何排查JVM相关问题？有哪些常用的诊断工具？

**答案要点**：

**常用诊断工具：**

```bash
# 1. jps - Java进程状态
jps -lvm
# 输出：进程ID  主类名 [程序参数]

# 2. jstat - 统计信息
# 查看GC情况
jstat -gcutil <pid> 1000 10
# 输出：S0 S1 E O M CCS YGC YGCT FGC FGCT GCT

# 3. jmap - 内存映像
# 生成堆dump
jmap -dump:format=b,file=heap.hprof <pid>

# 查看对象统计
jmap -histo <pid>
# 输出：instance_count  shallow_size  class_name

# 4. jstack - 线程栈
jstack <pid>
# 输出：线程名、状态、栈帧

# 5. jinfo - 配置信息
jinfo -flags <pid>
jinfo -sysprops <pid>

# 6. jcmd - 综合命令
jcmd <pid> GC.heap_dump filename=heap.hprof
jcmd <pid> GC.class_histogram
```

**可视化工具：**

| 工具 | 说明 |
|------|------|
| JConsole | JDK自带，监控内存、线程、类等 |
| VisualVM | JDK自带，功能强大的分析工具 |
| JMC | Java Mission Control，商业版 |
| MAT | Eclipse Memory Analyzer，分析堆dump |
| GCViewer | 分析GC日志 |
| arthas | 阿里开源，线上诊断工具 |

**常见问题排查：**

```java
// 1. OOM问题排查
// 添加参数生成dump
-XX:+HeapDumpOnOutOfMemoryError
-XX:HeapDumpPath=/path/to/dump

// 2. CPU高问题排查
// 1) top -c 查看进程
// 2) top -Hp <pid> 查看线程
// 3) jstack <pid> 获取线程栈
// 4) 找到CPU高的线程ID（转换为16进制）
// 5) 在线程栈中找到对应线程

// 3. 死锁问题排查
// jstack -l <pid> 查看是否有死锁
// 输出包含：Found 1 deadlock

// 4. 内存泄漏排查
// 1) jmap -histo 查看对象分布
// 2) 多次dump对比
// 3) 使用MAT分析引用链
```

**arthas使用：**

```bash
# 1. 下载启动
java -jar arthas-boot.jar

# 2. 常用命令
dashboard          # 查看JVM概览
thread             # 查看线程
thread -b          # 查看死锁
heapdump           # 导出堆dump
jvm                # 查看JVM信息
gc                 # 查看GC情况
profiler           # CPU/内存分析
watch              # 观察方法调用
```

---

## 附录：知识点总结

**JVM核心知识点：**

| 类别 | 关键知识点 |
|------|----------|
| 内存结构 | 堆、栈、方法区、程序计数器 |
| 垃圾回收 | 算法（标记-清除、复制、标记-整理）、收集器 |
| 类加载 | 双亲委派、类加载过程、自定义加载器 |
| 性能调优 | GC日志、参数配置、问题排查 |
| 运行时 | 字节码、解释器、JIT编译 |

**推荐JVM参数：**

```bash
# 通用配置
-Xms4g                        # 初始堆大小
-Xmx4g                        # 最大堆大小
-Xss1m                        # 栈大小
-XX:+UseG1GC                  # 使用G1收集器
-XX:MaxGCPauseMillis=200      # 停顿目标

# 生产环境推荐
-XX:+UseG1GC
-XX:MaxGCPauseMillis=200
-XX:+HeapDumpOnOutOfMemoryError
-XX:HeapDumpPath=/var/log/java
-Xlog:gc*:file=/var/log/gc.log:time:filecount=10,filesize=50M
```

---

*本文档共计20道JVM虚拟机面试题，涵盖内存结构、垃圾回收、类加载等核心知识点。*
