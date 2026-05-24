# Spring框架 - 20K薪资面试题

> 本文档包含Spring框架相关面试题，涵盖IoC容器、AOP、事务管理、Spring MVC等核心知识点。

---

## 第一部分：IoC与DI（共8题）

### Q1: 什么是IoC和DI？它们有什么区别？

**题目类型**：基础概念类

**问题描述**：什么是IoC（控制反转）和DI（依赖注入）？它们有什么关系？

**答案要点**：

**IoC定义：**
控制反转（Inversion of Control）是一种软件设计原则，将对象的创建和依赖管理从应用代码中转移到框架或容器。

**DI定义：**
依赖注入（Dependency Injection）是IoC的一种实现方式，由容器在运行期注入对象所需的依赖。

**两者关系：**
```
┌─────────────────────────────────────────────────────────────┐
│                        IoC vs DI                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  IoC是设计思想                                               │
│  ├── 传统: 程序控制对象创建                                 │
│  └── 控制反转: 框架控制对象创建                             │
│                                                             │
│  DI是IoC的具体实现                                          │
│  ├── 构造函数注入                                           │
│  ├── Setter注入                                             │
│  └── 字段注入                                               │
│                                                             │
│  IoC ──► 泛指控制反转思想                                   │
│   │                                                          │
│   └── DI ──► 依赖注入（一种IoC实现）                        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**代码示例：**

```java
// 传统方式 - 程序控制
public class UserService {
    private UserDao userDao = new UserDaoImpl();  // 主动创建
    private MailService mailService = new MailServiceImpl();
}

// IoC方式 - 容器控制
public class UserService {
    private UserDao userDao;  // 不主动创建
    
    // 容器通过构造器注入
    public UserService(UserDao userDao, MailService mailService) {
        this.userDao = userDao;
        this.mailService = mailService;
    }
}
```

---

### Q2: Spring IoC容器的启动过程是怎样的？

**题目类型**：技术原理类

**问题描述**：Spring IoC容器是如何启动的？Bean的生命周期是什么？

**答案要点**：

**IoC容器启动流程：**

```
┌─────────────────────────────────────────────────────────────┐
│                   Spring IoC容器启动流程                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. 容器配置                                                │
│     ├── 加载配置文件(XML/注解/JavaConfig)                  │
│     └── 创建BeanDefinitionReader                             │
│                                                             │
│  2. BeanDefinition注册                                      │
│     └── 解析配置，生成BeanDefinition并注册                   │
│                                                             │
│  3. BeanFactoryPostProcessor处理                            │
│     └── 修改BeanDefinition                                   │
│                                                             │
│  4. Bean实例化                                             │
│     ├── 实例化Bean                                          │
│     ├── 属性填充                                            │
│     └── BeanPostProcessor前置处理                           │
│                                                             │
│  5. 初始化                                                  │
│     ├── Aware接口回调                                       │
│     ├── BeanPostProcessor后置处理                           │
│     └── 初始化方法执行                                       │
│                                                             │
│  6. Bean就绪                                                │
│     └── Bean可被使用                                        │
│                                                             │
│  7. 容器关闭                                                │
│     └── DisposableBean.destroy()                           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Bean生命周期详解：**

```java
public class UserService {
    
    // 1. 构造器执行
    public UserService() {
        System.out.println("1. 构造器执行");
    }
    
    // 2. 设置属性
    @Autowired
    private UserDao userDao;
    
    // 3. Aware接口回调
    public void setBeanName(String name) {
        System.out.println("3. BeanNameAware: " + name);
    }
    
    public void setBeanFactory(BeanFactory factory) {
        System.out.println("3. BeanFactoryAware");
    }
    
    // 4. BeanPostProcessor前置处理
    @PostConstruct
    public void init() {
        System.out.println("4. @PostConstruct");
    }
    
    // 5. 初始化方法
    public void afterPropertiesSet() {
        System.out.println("5. InitializingBean.afterPropertiesSet()");
    }
    
    // 6. BeanPostProcessor后置处理
    @PreDestroy
    public void cleanup() {
        System.out.println("6. @PreDestroy");
    }
    
    public void destroy() {
        System.out.println("6. DisposableBean.destroy()");
    }
}
```

---

### Q3: Bean的作用域有哪些？如何选择？

**题目类型**：基础概念类

**问题描述**：Spring Bean的作用域有哪些？各自的特点是什么？

**答案要点**：

**作用域类型：**

| 作用域 | 说明 | 使用场景 |
|--------|------|----------|
| singleton | 默认，整个容器一个实例 | 无状态Bean |
| prototype | 每次获取创建新实例 | 有状态Bean |
| request | 每次HTTP请求创建 | Web应用 |
| session | 每次HTTP会话创建 | Web应用 |
| application | ServletContext生命周期 | Web应用 |
| websocket | WebSocket生命周期 | WebSocket |

**作用域示例：**

```java
// singleton - 默认
@Component
public class UserService {
    // 整个应用共享一个实例
}

// prototype - 每次创建新实例
@Component
@Scope("prototype")
public class ComplexProcessor {
    // 每次注入都创建新实例
}

// request - 每个请求创建
@Controller
@Scope("request")
public class RequestContext {
    // 每个HTTP请求有独立实例
}

// session - 每个会话创建
@Controller
@Scope("session")
public class UserSession {
    // 每个HTTP会话有独立实例
}

// 配置方式
@Configuration
public class AppConfig {
    @Bean
    @Scope("prototype")
    public MyBean myBean() {
        return new MyBean();
    }
}
```

**作用域问题：**

```java
// prototype作用域的Bean不会被容器管理生命周期
@Component
@Scope("prototype")
public class MyBean {
    public void process() {}
}

// 每次从容器获取都会创建新实例
MyBean bean1 = context.getBean(MyBean.class);
MyBean bean2 = context.getBean(MyBean.class);
// bean1 != bean2

// 如果注入到singleton Bean中
@Component
public class SingletonService {
    private final MyBean prototypeBean;
    
    public SingletonService() {
        // 只会注入一次！
        this.prototypeBean = new MyBean();
    }
}

// 正确做法：使用ObjectFactory延迟获取
@Component
public class SingletonService {
    private final ObjectFactory<MyBean> prototypeBeanFactory;
    
    public SingletonService(ObjectFactory<MyBean> factory) {
        this.prototypeBeanFactory = factory;
    }
    
    public void process() {
        MyBean bean = prototypeBeanFactory.getObject();  // 每次获取新实例
    }
}
```

---

### Q4: 什么是循环依赖？如何解决？

**题目类型**：技术原理类

**问题描述**：什么是循环依赖？Spring是如何解决循环依赖的？

**答案要点**：

**循环依赖定义：**
当两个或多个Bean相互依赖，形成闭环时，就产生了循环依赖。

```java
// 循环依赖示例
@Component
public class A {
    @Autowired
    private B b;
}

@Component
public class B {
    @Autowired
    private A a;
}
```

**Spring三级缓存解决循环依赖：**

```
┌─────────────────────────────────────────────────────────────┐
│                 Spring三级缓存解决循环依赖                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  一级缓存(singletonObjects): 成品Bean，完全初始化           │
│  二级缓存(earlySingletonObjects): 提前曝光的Bean，未填充属性 │
│  三级缓存(singletonFactories): Bean工厂，创建中             │
│                                                             │
│  A创建流程:                                                 │
│  1. 创建A，放入三级缓存                                     │
│  2. 填充属性，发现依赖B                                     │
│  3. 获取B，B创建中...                                      │
│  4. B填充属性，发现依赖A                                   │
│  5. 从三级缓存获取A（不完整）                              │
│  6. B完成创建                                              │
│  7. A完成创建                                              │
│                                                             │
│  注意: 构造器注入无法解决循环依赖！                         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**哪些情况无法解决：**

```java
// 1. 构造器注入 - 无法解决
@Component
public class A {
    public A(B b) { }  // 构造器注入
}

@Component
public class B {
    public B(A a) { }  // 循环依赖，报错
}

// 2. prototype作用域 - 无法解决
@Component
@Scope("prototype")
public class A {
    @Autowired
    private B b;
}

// 3. @DependsOn循环 - 无法解决
@Component
@DependsOn("b")
public class A { }

@Component
@DependsOn("a")
public class B { }
```

**解决方案：**

```java
// 方案1: 使用Setter注入代替构造器注入
@Component
public class A {
    private B b;
    
    @Autowired
    public void setB(B b) {
        this.b = b;
    }
}

// 方案2: 使用@Lazy延迟加载
@Component
public class A {
    @Autowired
    @Lazy
    private B b;
}

// 方案3: 使用ObjectProvider
@Component
public class A {
    @Autowired
    private ObjectProvider<B> bProvider;
    
    public void process() {
        B b = bProvider.getIfAvailable();
    }
}
```

---

### Q5: @Autowired和@Resource有什么区别？

**题目类型**：技术对比类

**问题描述**：@Autowired和@Resource注解有什么区别？各自的使用场景是什么？

**答案要点**：

**核心区别对比：**

| 特性 | @Autowired | @Resource |
|------|-----------|-----------|
| 来源 | Spring注解 | JDK注解(JSR-250) |
| 注入方式 | byType + byName | byName + byType |
| 位置 | 构造器/Setter/字段 | 字段/Setter |
| required属性 | 支持 | 不支持 |
| 优先级 | 先按类型，再按名称 | 先按名称，再按类型 |

**代码示例：**

```java
// @Autowired - Spring注解
@Component
public class UserService {
    
    // 字段注入
    @Autowired
    private UserDao userDao;
    
    // Setter注入
    @Autowired
    public void setOrderService(OrderService orderService) {
        this.orderService = orderService;
    }
    
    // 构造器注入（推荐）
    @Autowired
    public UserService(UserDao userDao, OrderService orderService) {
        this.userDao = userDao;
        this.orderService = orderService;
    }
    
    // 指定Bean名称
    @Autowired
    @Qualifier("mysqlUserDao")
    private UserDao userDao;
    
    // 设为false，找不到不报错
    @Autowired(required = false)
    private Optional<MailService> mailService;
}

// @Resource - JDK注解
@Component
public class UserService {
    
    // 默认按字段名匹配
    @Resource
    private UserDao userDao;
    
    // 指定Bean名称
    @Resource(name = "mysqlUserDao")
    private UserDao userDao;
    
    // 按类型匹配
    @Resource
    private UserService userService;
}
```

**选择建议：**

```java
// 1. 构造器注入 - 推荐（Spring 4.3+无需@Autowired）
public class UserService {
    private UserDao userDao;
    
    // Spring会自动注入
    public UserService(UserDao userDao) {
        this.userDao = userDao;
    }
}

// 2. 字段注入 - 不推荐（难以测试）
// 3. Setter注入 - 可选

// 4. @Required注解已废弃
// 使用构造器注入代替
```

---

### Q6: Spring是如何处理Bean的？有哪些后置处理器？

**题目类型**：技术原理类

**问题描述**：Spring有哪些Bean后置处理器？它们的作用是什么？

**答案要点**：

**BeanPostProcessor接口：**

```java
public interface BeanPostProcessor {
    // 前置处理
    default Object postProcessBeforeInitialization(
            Object bean, String beanName) throws BeansException {
        return bean;
    }
    
    // 后置处理
    default Object postProcessAfterInitialization(
            Object bean, String beanName) throws BeansException {
        return bean;
    }
}
```

**常用后置处理器：**

| 处理器 | 作用 | 常用场景 |
|--------|------|----------|
| AutowiredAnnotationBeanPostProcessor | 处理@Autowired/@Value | 依赖注入 |
| CommonAnnotationBeanPostProcessor | 处理@PostConstruct/@PreDestroy | 生命周期 |
| RequiredAnnotationBeanPostProcessor | 处理@Required | 属性检查 |
| AsyncAnnotationBeanPostProcessor | 处理@Async | 异步执行 |
| ScheduledAnnotationBeanPostProcessor | 处理@Scheduled | 定时任务 |

**自定义BeanPostProcessor示例：**

```java
// 日志增强处理器
@Component
public class LoggingBeanPostProcessor implements BeanPostProcessor {
    
    @Override
    public Object postProcessBeforeInitialization(
            Object bean, String beanName) {
        System.out.println("初始化前: " + beanName);
        return bean;
    }
    
    @Override
    public Object postProcessAfterInitialization(
            Object bean, String beanName) {
        System.out.println("初始化后: " + beanName);
        return bean;
    }
}

// 条件创建处理器
@Component
@ConditionalOnProperty(name = "feature.enabled", havingValue = "true")
public class FeatureBean {
    // 只有配置feature.enabled=true时才创建
}

// AOP代理处理器
@Component
public class AopProxyBeanPostProcessor {
    // 处理@Aspect切面，生成代理对象
}
```

---

### Q7: Spring如何处理事务？@Transactional的原理是什么？

**题目类型**：技术原理类

**问题描述**：Spring事务是如何实现的？@Transactional注解的原理是什么？

**答案要点**：

**事务管理方式：**

```java
// 1. 编程式事务
@Service
public class UserService {
    
    @Autowired
    private TransactionTemplate template;
    
    public void transfer(Long fromId, Long toId, BigDecimal amount) {
        template.execute(status -> {
            // 业务逻辑
            accountDao.decrease(fromId, amount);
            accountDao.increase(toId, amount);
            return null;
        });
    }
}

// 2. 声明式事务（推荐）
@Service
public class UserService {
    
    @Transactional(rollbackFor = Exception.class)
    public void transfer(Long fromId, Long toId, BigDecimal amount) {
        accountDao.decrease(fromId, amount);
        accountDao.increase(toId, amount);
    }
}
```

**@Transactional原理：**

```
┌─────────────────────────────────────────────────────────────┐
│                    @Transactional原理                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. 扫描阶段                                               │
│     TransactionInterceptor                                   │
│     BeanFactoryTransactionAspect                             │
│     └── 处理@Transactional                                  │
│                                                             │
│  2. 创建代理阶段                                           │
│     AnnotationTransactionAspect                              │
│     └── 为Bean创建代理对象                                 │
│                                                             │
│  3. 调用阶段                                               │
│     ┌─────────────────────────────────────────┐            │
│     │          代理对象                        │            │
│     │  ┌─────────────────────────────────┐    │            │
│     │  │  @Transactional方法              │    │            │
│     │  │  1. 检查事务配置                 │    │            │
│     │  │  2. 获取Connection               │    │            │
│     │  │  3. 开启事务(autoCommit=false)   │    │            │
│     │  │  4. 执行目标方法                 │    │            │
│     │  │  5. 正常: commit                │    │            │
│     │  │  6. 异常: rollback             │    │            │
│     │  └─────────────────────────────────┘    │            │
│     └─────────────────────────────────────────┘            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**事务传播行为：**

```java
public enum Propagation {
    REQUIRED      // 默认，有事务加入，无事务创建
    REQUIRES_NEW // 创建新事务，挂起当前事务
    SUPPORTS     // 有事务加入，无事务非事务执行
    MANDATORY    // 必须在事务中，否则抛异常
    NOT_SUPPORTED// 非事务执行，挂起当前事务
    NEVER        // 必须非事务执行，否则抛异常
    NESTED       // 嵌套事务（Savepoint）
}

@Service
public class OuterService {
    @Transactional
    public void outer() {
        innerService.inner();  // REQUIRES_NEW会开启新事务
    }
}

@Service
public class InnerService {
    @Transactional(propagation = Propagation.REQUIRES_NEW)
    public void inner() {
        // 独立事务，不受outer事务影响
    }
}
```

---

### Q8: @Transactional失效的场景有哪些？

**题目类型**：场景解决类

**问题描述**：@Transactional在哪些情况下会失效？如何避免？

**答案要点**：

**失效场景：**

```java
// 1. 非public方法 - 不会生效
@Service
public class UserService {
    
    @Transactional  // 失效！private方法无法被代理
    private void save(User user) {
        userDao.save(user);
    }
}

// 2. 自调用 - 本类方法调用不走代理
@Service
public class UserService {
    
    public void outer() {
        inner();  // this.inner()，不走代理
    }
    
    @Transactional  // 失效！
    public void inner() {
        userDao.save(new User());
    }
}

// 3. 异常被catch - 不会回滚
@Service
public class UserService {
    
    @Transactional
    public void save(User user) {
        try {
            userDao.save(user);
        } catch (Exception e) {
            // 异常被捕获，未抛出，事务认为正常
        }
    }
}

// 4. 异常类型不匹配 - 默认只回滚RuntimeException
@Service
public class UserService {
    
    @Transactional
    public void save(User user) throws Exception {
        userDao.save(user);
        throw new Exception("业务异常");  // 不回滚
    }
    
    // 正确写法
    @Transactional(rollbackFor = Exception.class)
    public void save2(User user) throws Exception {
        userDao.save(user);
        throw new Exception("业务异常");
    }
}

// 5. 数据源未配置事务管理器
@Service
public class UserService {
    
    @Transactional  // 需要显式指定
    public void save(User user) {
        userDao.save(user);
    }
}

// 配置多数据源时
@Service
public class UserService {
    
    @Transactional(transactionManager = "transactionManager1")
    public void save(User user) {
        userDao.save(user);
    }
}
```

**正确使用方式：**

```java
// 方案1: 注入自身代理调用
@Service
public class UserService {
    
    @Autowired
    private UserService self;  // 自注入
    
    public void outer() {
        self.inner();  // 通过代理调用
    }
    
    @Transactional
    public void inner() {
        userDao.save(new User());
    }
}

// 方案2: 使用TransactionTemplate
@Service
public class UserService {
    
    @Autowired
    private TransactionTemplate template;
    
    public void outer() {
        template.execute(status -> {
            inner();  // 事务在模板中
            return null;
        });
    }
    
    private void inner() {
        userDao.save(new User());
    }
}

// 方案3: AOP切面
@Service
public class UserService {
    
    public void outer() {
        transactionTemplate.execute(status -> {
            inner();
            return null;
        });
    }
}
```

---

## 第二部分：AOP（共6题）

### Q9: 什么是AOP？AOP的核心概念是什么？

**题目类型**：基础概念类

**问题描述**：什么是AOP（面向切面编程）？它的核心概念是什么？

**答案要点**：

**AOP定义：**
面向切面编程（AOP）是一种编程范式，通过预编译方式和运行期动态代理实现程序功能的统一维护。

**核心概念：**

| 概念 | 说明 |
|------|------|
| Join Point（连接点） | 程序执行的某个位置，Spring AOP中是方法调用 |
| Pointcut（切点） | 匹配连接点的表达式 |
| Advice（通知） | 切点处执行的逻辑 |
| Aspect（切面） | 切点和通知的组合 |
| Weaving（织入） | 将通知织入目标对象的过程 |
| Target（目标对象） | 被代理的对象 |

**AOP术语对应Spring：**

```
┌─────────────────────────────────────────────────────────────┐
│                      AOP术语对应                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Join Point ──► Spring AOP中只有方法执行是连接点            │
│                                                             │
│  Pointcut ──► @Pointcut("execution(* com.example..*.save(..))")
│                                                             │
│  Advice类型:                                                │
│  ├── @Before      ──► 前置通知                             │
│  ├── @After       ──► 后置通知（finally）                  │
│  ├── @AfterReturning ──► 返回通知                         │
│  ├── @AfterThrowing  ──► 异常通知                         │
│  └── @Around       ──► 环绕通知                           │
│                                                             │
│  Aspect ──► @Aspect + @Component                            │
│                                                             │
│  Weaving ──► 编译时/类加载时/运行时织入                     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**代码示例：**

```java
@Aspect
@Component
public class LoggingAspect {
    
    // 定义切点
    @Pointcut("execution(* com.example.service..*.*(..))")
    public void servicePointcut() {}
    
    // 前置通知
    @Before("servicePointcut()")
    public void before(JoinPoint joinPoint) {
        String method = joinPoint.getSignature().toShortString();
        System.out.println("调用前: " + method);
    }
    
    // 后置通知
    @After("servicePointcut()")
    public void after(JoinPoint joinPoint) {
        String method = joinPoint.getSignature().toShortString();
        System.out.println("调用后: " + method);
    }
    
    // 返回通知
    @AfterReturning(pointcut = "servicePointcut()", returning = "result")
    public void afterReturning(JoinPoint joinPoint, Object result) {
        System.out.println("返回: " + result);
    }
    
    // 异常通知
    @AfterThrowing(pointcut = "servicePointcut()", throwing = "ex")
    public void afterThrowing(JoinPoint joinPoint, Exception ex) {
        System.out.println("异常: " + ex.getMessage());
    }
    
    // 环绕通知
    @Around("servicePointcut()")
    public Object around(ProceedingJoinPoint joinPoint) throws Throwable {
        long start = System.currentTimeMillis();
        try {
            Object result = joinPoint.proceed();
            System.out.println("耗时: " + (System.currentTimeMillis() - start));
            return result;
        } catch (Exception e) {
            System.out.println("异常: " + e.getMessage());
            throw e;
        }
    }
}
```

---

### Q10: Spring AOP和AspectJ AOP有什么区别？

**题目类型**：技术对比类

**问题描述**：Spring AOP和AspectJ AOP有什么区别？各自的优缺点是什么？

**答案要点**：

**核心区别对比：**

| 特性 | Spring AOP | AspectJ |
|------|-----------|---------|
| 织入时机 | 运行时 | 编译时/加载时 |
| 代理方式 | 动态代理/JDK/CGLIB | 字节码织入 |
| 切点 | 方法级别 | 字段/构造函数 |
| 依赖 | 只需Spring | 需要AspectJ编译器 |
| 性能 | 运行时开销 | 无运行时开销 |
| 复杂度 | 简单 | 配置复杂 |

**Spring AOP：**

```java
// 基于代理的AOP
// 支持: 方法执行的连接点
// 不支持: 属性访问、构造函数

// 自动代理
@Configuration
@EnableAspectJAutoProxy
public class AppConfig {
    @Bean
    public AspectBean aspectBean() {
        return new AspectBean();
    }
}

// AspectJ注解
@Aspect
@Component
public class LoggingAspect {
    @Pointcut("execution(* com.example..*.save(..))")
    public void savePointcut() {}
}
```

**AspectJ：**

```java
// Ajc编译器织入
// 支持: 任意连接点
// 需要: aspectj-maven-plugin

// 切点表达式更丰富
@Aspect
public class AspectJApect {
    
    // 方法切点
    @Pointcut("execution(* com.example..*.*(..))")
    public void methodPointcut() {}
    
    // 属性切点
    @Pointcut("get(* com.example.User.name)")
    public void fieldGetPointcut() {}
    
    // 构造函数切点
    @Pointcut("call(com.example.User.new(..))")
    public void constructorPointcut() {}
}

// 配置AspectJ
<plugin>
    <groupId>org.codehaus.mojo</groupId>
    <artifactId>aspectj-maven-plugin</artifactId>
    <configuration>
        <complianceLevel>1.8</complianceLevel>
        <weaveDependencies>
            <dependency>
                <groupId>org.aspectj</groupId>
                <artifactId>aspectjrt</artifactId>
            </dependency>
        </weaveDependencies>
    </configuration>
</plugin>
```

**选择建议：**

| 场景 | 推荐 |
|------|------|
| 简单方法拦截 | Spring AOP |
| 字段拦截 | AspectJ |
| 构造函数拦截 | AspectJ |
| 性能要求高 | AspectJ |
| 开发简单 | Spring AOP |

---

### Q11: JDK动态代理和CGLIB代理有什么区别？

**题目类型**：技术对比类

**问题描述**：Spring AOP使用哪种代理？JDK动态代理和CGLIB代理有什么区别？

**答案要点**：

**代理方式对比：**

| 特性 | JDK动态代理 | CGLIB代理 |
|------|-------------|-----------|
| 实现 | Java反射 | 字节码生成 |
| 原理 | 实现接口，生成代理类 | 继承被代理类 |
| 目标类 | 必须实现接口 | 可以不实现接口 |
| 性能 | 反射调用，略慢 | 运行时生成字节码 |
| 构造函数 | 不调用 | 调用 |

**JDK动态代理原理：**

```java
// JDK动态代理要求目标类实现接口
public interface UserService {
    void save(User user);
}

public class UserServiceImpl implements UserService {
    public void save(User user) {
        System.out.println("保存用户");
    }
}

// InvocationHandler实现
public class JDKProxy implements InvocationHandler {
    private Object target;
    
    public JDKProxy(Object target) {
        this.target = target;
    }
    
    @Override
    public Object invoke(Object proxy, Method method, Object[] args) 
            throws Throwable {
        System.out.println("前置逻辑");
        Object result = method.invoke(target, args);
        System.out.println("后置逻辑");
        return result;
    }
    
    public Object getProxy() {
        return Proxy.newProxyInstance(
            target.getClass().getClassLoader(),
            target.getClass().getInterfaces(),
            this
        );
    }
}

// 使用
UserService proxy = (UserService) new JDKProxy(new UserServiceImpl()).getProxy();
proxy.save(new User());
```

**CGLIB代理原理：**

```java
// CGLIB通过继承生成子类
public class CglibProxy implements MethodInterceptor {
    private Object target;
    
    public CglibProxy(Object target) {
        this.target = target;
    }
    
    @Override
    public Object intercept(Object obj, Method method, Object[] args, 
            MethodProxy proxy) throws Throwable {
        System.out.println("前置逻辑");
        Object result = proxy.invokeSuper(obj, args);  // 调用父类方法
        System.out.println("后置逻辑");
        return result;
    }
    
    public Object getProxy() {
        Enhancer enhancer = new Enhancer();
        enhancer.setSuperclass(target.getClass());
        enhancer.setCallback(this);
        return enhancer.create();
    }
}
```

**Spring中的选择：**

```java
// Spring AOP默认策略:
// - 如果目标类实现了接口，使用JDK动态代理
// - 否则，使用CGLIB

// 强制使用CGLIB
@EnableAspectJAutoProxy(proxyTargetClass = true)

// CGLIB的限制:
// - 不能代理final类
// - 不能代理final方法
```

---

### Q12: AOP有哪些使用场景？

**题目类型**：场景解决类

**问题描述**：AOP在开发中有哪些实际应用场景？

**答案要点**：

**常见应用场景：**

| 场景 | 说明 | 示例 |
|------|------|------|
| 日志记录 | 方法调用前后记录日志 | @Around记录方法耗时 |
| 事务管理 | 方法执行开启/提交事务 | @Transactional |
| 安全控制 | 权限校验 | @PreAuthorize |
| 性能监控 | 方法执行时间统计 | APM监控 |
| 缓存 | 方法结果缓存 | @Cacheable |
| 异常处理 | 统一异常处理 | @ControllerAdvice |
| 参数校验 | 方法参数校验 | @Valid |

**代码示例：**

```java
// 1. 性能监控
@Aspect
@Component
public class PerformanceMonitor {
    
    @Around("@annotation(Monitored)")
    public Object monitor(ProceedingJoinPoint point) throws Throwable {
        long start = System.nanoTime();
        try {
            return point.proceed();
        } finally {
            long duration = System.nanoTime() - start;
            log.info("{} 执行耗时: {}ms", 
                point.getSignature(), duration / 1_000_000);
        }
    }
}

// 2. 参数校验
@Aspect
@Component
public class ValidationAspect {
    
    @Before("execution(* com.example..*.save(..)) && args(user)")
    public void validateSave(User user) {
        if (user.getName() == null || user.getName().isEmpty()) {
            throw new IllegalArgumentException("用户名不能为空");
        }
    }
}

// 3. 权限校验
@Aspect
@Component
public class SecurityAspect {
    
    @Before("execution(* com.example..*.delete(..))")
    public void checkPermission(JoinPoint point) {
        Authentication auth = SecurityContextHolder.getContext()
            .getAuthentication();
        if (auth == null || !auth.isAuthenticated()) {
            throw new AccessDeniedException("未登录");
        }
    }
}

// 4. 缓存
@Aspect
@Component
public class CacheAspect {
    
    @Around("@annotation(Cacheable)")
    public Object cache(ProceedingJoinPoint point) throws Throwable {
        String key = generateKey(point);
        
        Object cached = cache.get(key);
        if (cached != null) {
            return cached;
        }
        
        Object result = point.proceed();
        cache.put(key, result);
        return result;
    }
}

// 5. 统一异常处理
@Aspect
@Component
public class ExceptionHandlerAspect {
    
    @AfterThrowing(pointcut = "@annotation(restController)", 
                   throwing = "ex")
    public void handleException(JoinPoint point, Exception ex) {
        // 统一返回格式
    }
}
```

---

## 第三部分：Spring MVC（共6题）

### Q13: Spring MVC的工作流程是什么？

**题目类型**：技术原理类

**问题描述**：Spring MVC处理请求的完整流程是什么？

**答案要点**：

**完整工作流程：**

```
┌─────────────────────────────────────────────────────────────┐
│                    Spring MVC 请求处理流程                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. 请求 ──▶ DispatcherServlet                              │
│                                                             │
│  2. DispatcherServlet ──▶ HandlerMapping                    │
│     └── 根据URL找到对应的Handler(Controller)                 │
│                                                             │
│  3. DispatcherServlet ──▶ HandlerAdapter                    │
│     └── 执行Handler，返回ModelAndView                        │
│                                                             │
│  4. DispatcherServlet ──▶ ViewResolver                     │
│     └── 解析视图名，找到对应的View                           │
│                                                             │
│  5. View ──▶ 渲染模板，输出HTML                             │
│                                                             │
│  6. 响应 ──▶ 客户端                                         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**核心组件：**

| 组件 | 作用 |
|------|------|
| DispatcherServlet | 前端控制器，统一入口 |
| HandlerMapping | 映射请求到Handler |
| HandlerAdapter | 适配不同类型的Handler |
| HandlerExceptionResolver | 处理异常 |
| ViewResolver | 解析视图名 |
| MultipartResolver | 处理文件上传 |
| LocaleResolver | 处理国际化 |
| ThemeResolver | 处理主题 |

**代码流程示例：**

```java
// 1. DispatcherServlet.doDispatch() 接收请求
// 2. getHandler() 获取HandlerExecutionChain
// 3. getHandlerAdapter() 获取HandlerAdapter
// 4. adapter.handle() 执行Controller，返回ModelAndView
// 5. processDispatchResult() 处理结果

// Controller示例
@Controller
@RequestMapping("/user")
public class UserController {
    
    @GetMapping("/{id}")
    public ModelAndView getUser(@PathVariable Long id) {
        User user = userService.findById(id);
        ModelAndView mav = new ModelAndView("user/detail");
        mav.addObject("user", user);
        return mav;
    }
    
    // 返回JSON
    @GetMapping("/{id}")
    @ResponseBody
    public User getUserJson(@PathVariable Long id) {
        return userService.findById(id);
    }
}
```

---

### Q14: @Controller和@RestController有什么区别？

**题目类型**：技术对比类

**问题描述**：@Controller和@RestController有什么区别？各自的使用场景是什么？

**答案要点**：

**核心区别对比：**

```java
// @Controller
@Controller
public class UserController {
    
    // 需要配合@ResponseBody返回JSON
    @RequestMapping("/user")
    @ResponseBody
    public User getUser() {
        return new User();
    }
    
    // 返回视图
    @RequestMapping("/page")
    public String getPage() {
        return "user/detail";  // 返回视图名
    }
}

// @RestController (== @Controller + @ResponseBody)
@RestController
@RequestMapping("/user")
public class UserRestController {
    
    // 直接返回JSON
    @GetMapping("/{id}")
    public User getUser(@PathVariable Long id) {
        return userService.findById(id);
    }
    
    // 如需返回视图，不适合用@RestController
}

// @RestController源码
@Target({ElementType.TYPE})
@Retention(RetentionPolicy.RUNTIME)
@Documented
@Controller
@ResponseBody
public @interface RestController {
    // ...
}
```

**选择建议：**

| 场景 | 推荐 |
|------|------|
| 返回JSON/REST API | @RestController |
| 返回视图+JSON混合 | @Controller |
| SSM项目（传统Web） | @Controller |
| 微服务/API服务 | @RestController |

---

### Q15: Spring MVC如何处理参数绑定？

**题目类型**：技术原理类

**问题描述**：Spring MVC如何自动绑定请求参数？有哪些绑定方式？

**答案要点**：

**参数绑定方式：**

```java
@Controller
@RequestMapping("/user")
public class UserController {
    
    // 1. 路径变量
    @GetMapping("/{id}")
    public User getUser(@PathVariable Long id) {
        return userService.findById(id);
    }
    
    // 2. 请求参数
    @GetMapping("/search")
    public List<User> search(
            @RequestParam String name,
            @RequestParam(required = false, defaultValue = "1") int page,
            @RequestParam(value = "size", defaultValue = "10") int size) {
        return userService.search(name, page, size);
    }
    
    // 3. 请求头
    @GetMapping("/info")
    public String getInfo(
            @RequestHeader("Authorization") String token,
            @RequestHeader(value = "Accept", defaultValue = "*/*") String accept) {
        return "info";
    }
    
    // 4. Cookie
    @GetMapping("/cookie")
    public String getCookie(@CookieValue("SESSION") String sessionId) {
        return sessionId;
    }
    
    // 5. 请求体(JSON)
    @PostMapping("/save")
    public Result<Void> save(@RequestBody User user) {
        userService.save(user);
        return Result.success();
    }
    
    // 6. 表单数据
    @PostMapping("/form")
    public Result<Void> submitForm(User user) {
        // 自动绑定表单字段
        userService.save(user);
        return Result.success();
    }
    
    // 7. 绑定到Map
    @GetMapping("/params")
    public String params(@RequestParam Map<String, String> params) {
        params.forEach((k, v) -> System.out.println(k + ": " + v));
        return "ok";
    }
}
```

**自定义参数转换：**

```java
// 实现Converter接口
@Component
public class StringToDateConverter implements Converter<String, Date> {
    
    private final DateTimeFormatter formatter = 
        DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");
    
    @Override
    public Date convert(String source) {
        return Date.from(LocalDateTime.parse(source, formatter)
            .atZone(ZoneId.systemDefault())
            .toInstant());
    }
}

// 配置
@Configuration
public class WebConfig implements WebMvcConfigurer {
    
    @Override
    public void addFormatters(FormatterRegistry registry) {
        registry.addConverter(new StringToDateConverter());
    }
}
```

---

### Q16: Spring MVC如何统一处理异常？

**题目类型**：场景解决类

**问题描述**：Spring MVC如何实现全局异常处理？有哪些方式？

**答案要点**：

**异常处理方式：**

```java
// 方式1: @ControllerAdvice + @ExceptionHandler
@ControllerAdvice
public class GlobalExceptionHandler {
    
    // 处理特定异常
    @ExceptionHandler(BusinessException.class)
    @ResponseBody
    public Result<Void> handleBusiness(BusinessException ex) {
        return Result.fail(ex.getCode(), ex.getMessage());
    }
    
    // 处理参数校验异常
    @ExceptionHandler(MethodArgumentNotValidException.class)
    @ResponseBody
    public Result<Void> handleValidation(MethodArgumentNotValidException ex) {
        String message = ex.getBindingResult().getFieldError()
            .getDefaultMessage();
        return Result.fail(400, message);
    }
    
    // 处理所有异常
    @ExceptionHandler(Exception.class)
    @ResponseBody
    public Result<Void> handleAll(Exception ex) {
        log.error("系统异常", ex);
        return Result.fail(500, "系统错误");
    }
}

// 方式2: @RestControllerAdvice
@RestControllerAdvice
public class GlobalExceptionHandler {
    
    @ExceptionHandler(BusinessException.class)
    public Result<Void> handle(BusinessException ex) {
        return Result.fail(ex.getCode(), ex.getMessage());
    }
}

// 方式3: SimpleMappingExceptionResolver
@Configuration
public class ExceptionConfig {
    
    @Bean
    public SimpleMappingExceptionResolver exceptionResolver() {
        SimpleMappingExceptionResolver resolver = 
            new SimpleMappingExceptionResolver();
        
        Properties mappings = new Properties();
        mappings.setProperty("BusinessException", "error/business");
        mappings.setProperty("IllegalArgumentException", "error/param");
        
        resolver.setExceptionMappings(mappings);
        resolver.setDefaultErrorView("error/default");
        
        return resolver;
    }
}
```

**异常处理流程：**

```
┌─────────────────────────────────────────────────────────────┐
│                   异常处理流程                                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Controller抛出异常                                          │
│        │                                                    │
│        ▼                                                    │
│  DispatcherServlet调用processHandlerException()            │
│        │                                                    │
│        ▼                                                    │
│  遍历HandlerExceptionResolvers                              │
│        │                                                    │
│        ├── @ExceptionHandler方法                             │
│        ├── SimpleMappingExceptionResolver                   │
│        └── DefaultHandlerExceptionResolver                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 第四部分：Spring Boot（共5题）

### Q17: Spring Boot自动配置原理是什么？

**题目类型**：技术原理类

**问题描述**：Spring Boot是如何实现自动配置的？原理是什么？

**答案要点**：

**自动配置原理：**

```
┌─────────────────────────────────────────────────────────────┐
│                  Spring Boot 自动配置原理                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  @SpringBootApplication = @SpringBootConfiguration          │
│                            + @EnableAutoConfiguration       │
│                            + @ComponentScan                 │
│                                                             │
│  @EnableAutoConfiguration = @Import(AutoConfigurationImportSelector)
│                                                             │
│  1. Spring Boot启动时扫描 META-INF/spring.factories         │
│  2. 加载EnableAutoConfiguration对应的配置类                │
│  3. 根据条件(@Conditional)判断是否生效                       │
│  4. 配置类中定义@Bean，注入到容器                          │
│                                                             │
│  典型配置类:                                                 │
│  org.springframework.boot.autoconfigure.jdbc.DataSourceAutoConfiguration
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**@Conditional条件注解：**

```java
// 条件注解家族
@ConditionalOnClass      // 存在指定类时生效
@ConditionalOnMissingClass  // 不存在指定类时生效
@ConditionalOnBean      // 存在指定Bean时生效
@ConditionalOnMissingBean  // 不存在指定Bean时生效
@ConditionalOnProperty   // 配置属性满足条件时生效
@ConditionalOnWebApplication  // 是Web应用时生效

// 自定义自动配置示例
@Configuration
@ConditionalOnClass(DataSource.class)
@EnableConfigurationProperties(DataSourceProperties.class)
public class DataSourceAutoConfiguration {
    
    @Bean
    @ConditionalOnMissingBean
    public DataSource dataSource(DataSourceProperties properties) {
        return properties.initializeDataSourceBuilder().build();
    }
}

// spring.factories配置
// META-INF/spring.factories
org.springframework.boot.autoconfigure.EnableAutoConfiguration=\
com.example.config.MyAutoConfiguration
```

**排除自动配置：**

```java
// 方式1: 注解排除
@SpringBootApplication(exclude = {DataSourceAutoConfiguration.class})

// 方式2: 配置排除
spring:
  autoconfigure:
    exclude:
      - org.springframework.boot.autoconfigure.jdbc.DataSourceAutoConfiguration

// 方式3: 配置文件
org.springframework.boot.autoconfigure.EnableAutoConfiguration=\
  com.example.config.MyAutoConfiguration,\
  \!com.example.config.UnwantedConfiguration
```

---

### Q18: Spring Boot的启动流程是什么？

**题目类型**：技术原理类

**问题描述**：Spring Boot应用是如何启动的？启动流程是什么？

**答案要点**：

**启动流程：**

```
┌─────────────────────────────────────────────────────────────┐
│                   Spring Boot 启动流程                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. main() 方法启动                                        │
│                                                             │
│  2. SpringApplication.run()                                │
│     ├── 创建SpringApplication实例                          │
│     └── 调用run()方法                                       │
│                                                             │
│  3. createApplicationContext()                             │
│     └── 创建AnnotationConfigServletWebServerApplicationContext│
│                                                             │
│  4. prepareContext()                                        │
│     ├── 加载spring.factories                               │
│     ├── 设置环境                                            │
│     └── 加载主配置类                                        │
│                                                             │
│  5. refreshContext()                                        │
│     ├── 启动内嵌Tomcat                                     │
│     ├── 刷新容器（创建Bean）                                │
│     └── 执行Runner                                          │
│                                                             │
│  6. afterRefresh()                                         │
│     └── 调用applicationRunner                              │
│                                                             │
│  7. 应用就绪                                               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**关键代码：**

```java
// SpringApplication.run()
public static ConfigurableApplicationContext run(
        Class<?> primarySource, String... args) {
    return new SpringApplication(primarySource).run(args);
}

// run()方法核心逻辑
public ConfigurableApplicationContext run(String... args) {
    StopWatch stopWatch = new StopWatch();
    stopWatch.start();
    
    // 1. 创建引导上下文
    BootstrapContext bootstrapContext = 
        createBootstrapContext();
    
    // 2. 配置headless属性
    configureHeadlessProperty();
    
    // 3. 获取并启动RunListener
    SpringApplicationRunListeners listeners = 
        getRunListeners(args);
    listeners.starting();
    
    // 4. 创建环境
    ConfigurableEnvironment environment = 
        prepareEnvironment(listeners, bootstrapContext);
    
    // 5. 打印Banner
    Banner printedBanner = printBanner(environment);
    
    // 6. 创建上下文
    context = createApplicationContext();
    
    // 7. 准备上下文
    prepareContext(bootstrapContext, context, 
        environment, listeners, applicationArguments, printedBanner);
    
    // 8. 刷新上下文（核心）
    refreshContext(context);
    
    // 9. 刷新后处理
    afterRefresh(context, applicationArguments);
    
    // 10. 执行Runner
    callRunners(context, applicationArguments);
    
    return context;
}
```

---

### Q19: Spring Boot配置文件有哪些？如何加载？

**题目类型**：基础概念类

**问题描述**：Spring Boot支持哪些配置文件？它们是如何加载的？

**答案要点**：

**配置文件类型：**

| 文件名 | 说明 | 加载顺序 |
|--------|------|----------|
| application.properties | properties格式 | 低 |
| application.yml | YAML格式 | 低 |
| application-{profile}.properties | 环境特定配置 | 中 |
| application-{profile}.yml | 环境特定YAML | 中 |
| bootstrap.properties | 引导配置 | 最高 |
| bootstrap.yml | 引导YAML | 最高 |

**配置加载顺序：**

```
┌─────────────────────────────────────────────────────────────┐
│                   配置加载优先级(高到低)                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. 命令行参数 (--spring.config.location=...)                │
│  2. OS环境变量                                              │
│  3. application-{profile}.yml                              │
│  4. application.yml                                         │
│  5. @PropertySource注解                                     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**配置示例：**

```yaml
# application.yml
spring:
  application:
    name: my-app
  profiles:
    active: dev
  
  datasource:
    url: jdbc:mysql://localhost:3306/app
    username: root
    password: ${DB_PASSWORD:default}  # 支持默认值和环境变量

# 多环境配置
# application-dev.yml
spring:
  datasource:
    url: jdbc:mysql://localhost:3306/app_dev

# application-prod.yml  
spring:
  datasource:
    url: jdbc:mysql://prod-db:3306/app_prod
```

**@ConfigurationProperties绑定：**

```java
// 方式1: @ConfigurationProperties + @EnableConfigurationProperties
@Component
@ConfigurationProperties(prefix = "app")
public class AppProperties {
    private String name;
    private int version;
    private List<String> features;
}

// 启用
@SpringBootApplication
@EnableConfigurationProperties(AppProperties.class)
public class Application {}

# 配置
app:
  name: my-application
  version: 1.0
  features:
    - feature1
    - feature2

// 方式2: @ConfigurationProperties + @Bean
@ConfigurationProperties(prefix = "app")
public class AppProperties {
    // getters/setters
}

@Configuration
@EnableConfigurationProperties(AppProperties.class)
public class AppConfig {}

// 方式3: @PropertySource（不推荐）
@PropertySource(value = "classpath:config.properties")
```

---

### Q20: Spring Boot Starter是什么？如何自定义？

**题目类型**：技术原理类

**问题描述**：Spring Boot Starter是什么？如何自定义Starter？

**答案要点**：

**Starter结构：**

```
┌─────────────────────────────────────────────────────────────┐
│                   Spring Boot Starter结构                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  my-starter                                                 │
│  ├── pom.xml                                               │
│  └── src/main/java/                                       │
│      ├── autoconfigure/                                    │
│      │   └── MyAutoConfiguration                           │
│      └── MyStarterAutoConfiguration                        │
│                                                             │
│  autoconfigure模块:                                        │
│  ├── 提供自动配置类                                         │
│  └── spring.factories声明                                  │
│                                                             │
│  starter模块:                                               │
│  ├── 依赖autoconfigure模块                                 │
│  ├── 依赖其他必要的库                                       │
│  └── 提供便捷依赖                                          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**自定义Starter示例：**

```xml
<!-- my-starter-autoconfigure/pom.xml -->
<dependencies>
    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-autoconfigure</artifactId>
    </dependency>
    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-configuration-processor</artifactId>
        <optional>true</optional>
    </dependency>
</dependencies>
```

```java
// 配置属性类
@ConfigurationProperties(prefix = "my.feature")
public class MyFeatureProperties {
    private boolean enabled = true;
    private String message = "Hello";
    
    // getters/setters
}

// 自动配置类
@Configuration
@ConditionalOnClass(MyFeature.class)
@EnableConfigurationProperties(MyFeatureProperties.class)
public class MyFeatureAutoConfiguration {
    
    @Bean
    @ConditionalOnMissingBean
    @ConditionalOnProperty(prefix = "my.feature", name = "enabled", havingValue = "true")
    public MyFeature myFeature(MyFeatureProperties properties) {
        return new MyFeature(properties);
    }
}
```

```properties
# src/main/resources/META-INF/spring.factories
org.springframework.boot.autoconfigure.EnableAutoConfiguration=\
com.example.autoconfigure.MyFeatureAutoConfiguration
```

```xml
<!-- my-starter/pom.xml -->
<dependencies>
    <dependency>
        <groupId>com.example</groupId>
        <artifactId>my-starter-autoconfigure</artifactId>
    </dependency>
    <dependency>
        <groupId>com.example</groupId>
        <artifactId>my-feature-core</artifactId>
    </dependency>
</dependencies>
```

---

## 附录：知识点总结

**Spring核心知识点：**

| 类别 | 关键知识点 |
|------|----------|
| IoC/DI | 控制反转、依赖注入、Bean生命周期 |
| Bean | 作用域、循环依赖、@Autowired/@Resource |
| AOP | 切面、通知、切点、代理方式 |
| 事务 | @Transactional、传播行为、失效场景 |
| MVC | 工作流程、参数绑定、异常处理 |
| Boot | 自动配置、启动流程、Starter |

---

*本文档共计20道Spring框架面试题，涵盖IoC容器、AOP、事务管理、Spring MVC等核心知识点。*
