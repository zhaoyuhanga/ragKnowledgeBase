# Spring Boot高级 - 20K薪资面试题

> 本文档是Spring Boot的高级面试题，涵盖自动配置原理、启动流程、外部化配置、 Actuator监控等核心知识点。

---

## 第一部分：自动配置原理（共8题）

### Q1: Spring Boot自动配置的核心原理是什么？

**题目类型**：技术原理类

**问题描述**：Spring Boot的自动配置是如何实现的？核心注解和流程是什么？

**答案要点**：

**核心注解链：**

```java
@SpringBootApplication
  ├── @SpringBootConfiguration  // 标记配置类
  ├── @EnableAutoConfiguration  // 开启自动配置
  │   └── @Import(AutoConfigurationImportSelector.class)
  └── @ComponentScan  // 组件扫描

// AutoConfigurationImportSelector
public class AutoConfigurationImportSelector 
    implements DeferredImportSelector {
    
    // 1. 获取候选配置
    protected List<String> getCandidateConfigurations() {
        // 加载 META-INF/spring.factories
        // 读取 EnableAutoConfiguration 对应的配置类
        List<String> configurations = SpringFactoriesLoader
            .loadFactoryNames(getSpringFactoryLoaderUseClassLoader(),
                getClass().getClassLoader());
        return configurations;
    }
}
```

**自动配置生效条件：**

```java
// @Conditional系列注解
@Configuration
@ConditionalOnClass(DataSource.class)        // 存在指定类时生效
@ConditionalOnMissingBean(DataSource.class)   // 不存在指定Bean时生效
@ConditionalOnProperty(prefix = "spring.datasource",
    name = "url", havingValue = "xxx")      // 配置满足条件时生效
@EnableConfigurationProperties(DataSourceProperties.class)
public class DataSourceAutoConfiguration {
    // 自动配置逻辑
}
```

**META-INF/spring.factories：**

```properties
# Spring Boot 2.7+ 使用 META-INF/spring/org.springframework.boot.autoconfigure.AutoConfiguration.imports
com.example.config.MyAutoConfiguration

# 旧版本使用 META-INF/spring.factories
org.springframework.boot.autoconfigure.EnableAutoConfiguration=\
com.example.config.MyAutoConfiguration
```

---

### Q2: @EnableAutoConfiguration和@ComponentScan有什么区别？

**题目类型**：技术对比类

**问题描述**：@EnableAutoConfiguration和@ComponentScan的作用有什么区别？它们如何配合工作？

**答案要点**：

**核心区别对比：**

| 特性 | @EnableAutoConfiguration | @ComponentScan |
|------|------------------------|----------------|
| 作用 | 启用自动配置 | 组件扫描 |
| 扫描范围 | META-INF/spring.factories | 指定包路径 |
| 对象 | 自动配置类(@Configuration) | @Component/@Service等 |
| 来源 | 第三方库 | 本应用+依赖 |
| 启用方式 | 通过@Import | 直接扫描 |

**代码示例：**

```java
@SpringBootApplication
public class Application {
    public static void main(String[] args) {
        SpringApplication.run(Application.class, args);
    }
}

// 拆解后的等价写法
@Configuration
@EnableAutoConfiguration  // 启用自动配置
@ComponentScan(basePackages = "com.example")  // 扫描组件
public class Application {}

// 自定义自动配置
@Configuration
@AutoConfiguration
@ConditionalOnClass(DataSource.class)
@EnableConfigurationProperties(DataSourceProperties.class)
public class DataSourceAutoConfiguration {
    @Bean
    @ConditionalOnMissingBean
    public DataSource dataSource(DataSourceProperties properties) {
        return properties.initializeDataSourceBuilder().build();
    }
}
```

---

### Q3: Spring Boot的Condition条件注解有哪些？

**题目类型**：基础概念类

**问题描述**：Spring Boot的@Conditional系列注解有哪些？各自的使用场景是什么？

**答案要点**：

**条件注解家族：**

| 注解 | 作用 |
|------|------|
| @ConditionalOnClass | 存在指定类时生效 |
| @ConditionalOnMissingClass | 不存在指定类时生效 |
| @ConditionalOnBean | 存在指定Bean时生效 |
| @ConditionalOnMissingBean | 不存在指定Bean时生效 |
| @ConditionalOnProperty | 配置属性满足条件时生效 |
| @ConditionalOnResource | 存在指定资源时生效 |
| @ConditionalOnWebApplication | 是Web应用时生效 |
| @ConditionalOnNotWebApplication | 非Web应用时生效 |
| @ConditionalOnExpression | SpEL表达式为true时生效 |

**代码示例：**

```java
@Configuration
public class CacheAutoConfiguration {
    
    // 存在Redis类时生效
    @ConditionalOnClass(RedisOperations.class)
    public static class RedisCacheConfig {
        @Bean
        @ConditionalOnMissingBean(CacheManager.class)
        public CacheManager redisCacheManager() {
            return new RedisCacheManager();
        }
    }
    
    // 存在EhCache类时生效
    @ConditionalOnClass(Ehcache.class)
    public static class EhCacheConfig {
        @Bean
        public CacheManager ehCacheManager() {
            return new EhCacheCacheManager();
        }
    }
    
    // 配置满足条件时生效
    @ConfigurationProperties(prefix = "spring.cache")
    @ConditionalOnProperty(name = "spring.cache.enabled", 
        havingValue = "true", matchIfMissing = true)
    public static class GeneralCacheConfig {}
}
```

---

### Q4: Spring Boot的外部化配置是如何工作的？

**题目类型**：技术原理类

**问题描述**：Spring Boot的外部化配置是如何工作的？有哪些配置源？优先级是什么？

**答案要点**：

**配置源优先级（高到低）：**

```
┌─────────────────────────────────────────────────────────────┐
│                     配置加载优先级                             │
├─────────────────────────────────────────────────────────────┤
│  1. 命令行参数 --spring.config.location                    │
│  2. 命令行参数 --spring.config.additional-location        │
│  3. 操作系统环境变量                                        │
│  4. 打包在jar外的application-{profile}.properties/yml     │
│  5. 打包在jar外的application.properties/yml                │
│  6. @PropertySource注解加载                              │
│  7. 默认属性 (SpringApplication.setDefaultProperties)      │
└─────────────────────────────────────────────────────────────┘
```

**@ConfigurationProperties绑定：**

```java
// 方式1: @Component + @ConfigurationProperties
@Component
@ConfigurationProperties(prefix = "app.user")
public class UserProperties {
    private String name;
    private int age;
    private List<String> roles;
    
    // getters/setters
}

// 方式2: @EnableConfigurationProperties
@Configuration
@EnableConfigurationProperties(UserProperties.class)
public class AppConfig {}

// 方式3: @Bean
@Bean
@ConfigurationProperties(prefix = "app.user")
public UserProperties userProperties() {
    return new UserProperties();
}
```

**Relaxed Binding松弛绑定：**

```yaml
# 各种写法都可以
app:
  user-name: Tom          # kebab-case
  userName: Tom           # camelCase
  user_name: Tom          # snake_case
  USER_NAME: TOM          # SCREAMING_SNAKE_CASE
```

---

### Q5: SpringApplication是如何启动的？

**题目类型**：技术原理类

**问题描述**：SpringApplication的启动流程是什么？有哪些关键步骤？

**答案要点**：

**启动流程图：**

```
┌─────────────────────────────────────────────────────────────┐
│                   SpringApplication.run()流程                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. 创建SpringApplication实例                               │
│     ├── 判断应用类型（Servlet/Reactive/None）              │
│     ├── 加载spring.factories                               │
│     └── 设置Initializers和Listeners                        │
│                                                             │
│  2. prepareEnvironment()                                   │
│     ├── 加载配置文件                                        │
│     ├── 处理active profiles                                │
│     └── 触发ApplicationEnvironmentPreparedEvent             │
│                                                             │
│  3. createApplicationContext()                             │
│     └── 创建对应类型的上下文                                │
│                                                             │
│  4. prepareContext()                                       │
│     ├── 加载主配置类                                       │
│     ├── 设置Environment                                     │
│     └── 加载BeanDefinition                                  │
│                                                             │
│  5. refreshContext() (核心)                               │
│     ├── 启动内嵌Web服务器                                  │
│     ├── 刷新BeanFactory                                    │
│     └── 执行BeanFactoryPostProcessor                       │
│                                                             │
│  6. afterRefresh()                                        │
│     └── 调用CommandLineRunner/ApplicationRunner            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**关键源码：**

```java
public ConfigurableApplicationContext run(String... args) {
    // 1. 创建启动上下文
    DefaultBootstrapContext bootstrapContext = createBootstrapContext();
    
    // 2. 配置headless属性
    configureHeadlessProperty();
    
    // 3. 获取并启动监听器
    SpringApplicationRunListeners listeners = getRunListeners(args);
    listeners.starting();
    
    // 4. 创建并配置Environment
    ConfigurableEnvironment environment = prepareEnvironment(listeners, bootstrapContext);
    
    // 5. 打印Banner
    Banner printedBanner = printBanner(environment);
    
    // 6. 创建上下文
    context = createApplicationContext();
    
    // 7. 准备上下文（核心）
    prepareContext(bootstrapContext, context, environment, 
                  listeners, applicationArguments, printedBanner);
    
    // 8. 刷新上下文（启动服务器、加载Bean）
    refreshContext(context);
    
    // 9. 刷新后处理
    afterRefresh(context, applicationArguments);
    
    // 10. 发布ApplicationReadyEvent
    listeners.running();
    
    return context;
}
```

---

### Q6: Spring Boot的Bean生命周期是什么？

**题目类型**：技术原理类

**问题描述**：Spring Boot中Bean的完整生命周期是什么？有哪些关键节点？

**答案要点**：

**Bean生命周期步骤：**

```
1. 实例化 BeanInstantiation
2. 属性赋值 PropertySet
3. BeanNameAware回调
4. BeanFactoryAware回调
5. BeanClassLoaderAware回调
6. BeanFactoryPostProcessor.postProcessBeanFactory()
7. InstantiationAwareBeanPostProcessor.postProcessBeforeInstantiation()
8. 构造函数执行
9. BeanPostProcessor.postProcessBeforeInitialization()
10. @PostConstruct方法执行
11. InitializingBean.afterPropertiesSet()
12. 自定义init-method
13. BeanPostProcessor.postProcessAfterInitialization()
14. DisposableBean.destroy()
15. 自定义destroy-method
```

**代码示例：**

```java
@Component
public class UserService implements InitializingBean, DisposableBean {
    
    @PostConstruct
    public void init() {
        System.out.println("@PostConstruct 执行");
    }
    
    @Override
    public void afterPropertiesSet() throws Exception {
        System.out.println("InitializingBean.afterPropertiesSet() 执行");
    }
    
    public void customInit() {
        System.out.println("customInit 执行");
    }
    
    @PreDestroy
    public void cleanup() {
        System.out.println("@PreDestroy 执行");
    }
    
    @Override
    public void destroy() throws Exception {
        System.out.println("DisposableBean.destroy() 执行");
    }
    
    public void customDestroy() {
        System.out.println("customDestroy 执行");
    }
}
```

**配置生命周期方法：**

```yaml
spring:
  main:
    lazy-initialization: true  # 懒初始化
```

```java
@Bean(initMethod = "customInit", destroyMethod = "customDestroy")
public UserService userService() {
    return new UserService();
}
```

---

### Q7: SpringApplication有哪些扩展点？

**题目类型**：场景解决类

**问题描述**：SpringApplication有哪些扩展点可以自定义？各自的使用场景是什么？

**答案要点**：

**主要扩展点：**

| 扩展点 | 接口/类 | 使用场景 |
|--------|----------|----------|
| ApplicationContextInitializer | 上下文初始化 | 修改上下文早期状态 |
| ApplicationListener | 应用监听器 | 监听应用事件 |
| CommandLineRunner | 命令行运行器 | 启动后执行任务 |
| ApplicationRunner | 应用运行器 | 替代CommandLineRunner |
| EnvironmentPostProcessor | 环境后处理器 | 修改Environment |
| SpringApplicationRunListener | 运行监听器 | 全流程监控 |

**代码示例：**

```java
// 1. ApplicationContextInitializer
public class MyContextInitializer 
    implements ApplicationContextInitializer<ConfigurableApplicationContext> {
    @Override
    public void initialize(ConfigurableApplicationContext context) {
        System.out.println("上下文初始化");
    }
}

// 注册
// META-INF/spring.factories
org.springframework.context.ApplicationContextInitializer=\
com.example.MyContextInitializer

// 2. ApplicationListener
@Component
public class MyListener implements ApplicationListener<ApplicationEvent> {
    @Override
    public void onApplicationEvent(ApplicationEvent event) {
        System.out.println("事件: " + event.getClass().getSimpleName());
    }
}

// 3. CommandLineRunner
@Component
@Order(1)
public class DataInitRunner implements CommandLineRunner {
    @Override
    public void run(String... args) {
        System.out.println("命令行Runner执行");
    }
}

// 4. ApplicationRunner (推荐)
@Component
@Order(2)
public class AppRunner implements ApplicationRunner {
    @Override
    public void run(ApplicationArguments args) {
        System.out.println("应用Runner执行");
    }
}
```

---

### Q8: Spring Boot的FailFast机制是什么？

**题目类型**：技术原理类

**问题描述**：Spring Boot的FailFast机制是什么？它如何工作？

**答案要点**：

**FailFast机制：**

```java
// 当Bean创建失败时的快速失败机制
// 发生在 refreshContext() 阶段

// 默认情况下，忽略循环依赖检测
// Spring Boot 2.1+ 默认禁用Bean覆盖检测

// 配置
spring.main.fail-fast=false  # 禁用FailFast
spring.main.allow-bean-definition-overriding=true  # 允许Bean覆盖

// 启动失败时的处理
public class FailureAnalyzer {
    // 分析启动失败原因，提供友好的错误信息
}

// 自定义FailureAnalyzer
@Component
public class MyFailureAnalyzer extends AbstractFailureAnalyzer<MyException> {
    @Override
    protected FailureAnalysis analyze(Throwable rootCause, 
            MyException cause) {
        return new FailureAnalysis(
            "配置错误",
            cause.getMessage(),
            new Fix().toFIX()
        );
    }
}
```

**启动失败诊断：**

```bash
# 开启调试模式
java -jar app.jar --debug

# 查看详细日志
java -jar app.jar -verbose

# 使用Spring Boot Analyzer
# https://github.com/nick Powell/spring-boot-analyzer
```

---

## 第二部分：Spring Boot Actuator（共6题）

### Q9: Spring Boot Actuator是什么？如何配置？

**题目类型**：基础概念类

**问题描述**：Spring Boot Actuator是什么？如何集成和配置？

**答案要点**：

**Actuator依赖：**

```xml
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-actuator</artifactId>
</dependency>
```

**端点配置：**

```yaml
management:
  endpoints:
    web:
      exposure:
        include: health,info,metrics,env,beans,caches,threaddump,heapdump
      base-path: /actuator
      enabled-by-default: true
    enabled-by-default: false  # 禁用所有端点
  
  endpoint:
    health:
      show-details: always
      probes:
        enabled: true
    info:
      enabled: true
  
  health:
    db:
      enabled: true
    redis:
      enabled: true
    livenessstate:
      enabled: true
    readinessstate:
      enabled: true
  
  info:
    env:
      enabled: true
```

**常用端点：**

| 端点 | 路径 | 说明 |
|------|------|------|
| /health | 健康检查 | 应用健康状态 |
| /info | 应用信息 | 来自application.info |
| /metrics | 指标 | 各种监控指标 |
| /env | 环境变量 | 配置属性 |
| /beans | Bean列表 | 所有Spring Bean |
| /caches | 缓存信息 | 缓存统计 |
| /threaddump | 线程dump | 线程快照 |
| /heapdump | 堆dump | 堆内存快照 |
| /loggers | 日志配置 | 查看/修改日志级别 |

---

### Q10: 如何自定义Actuator端点？

**题目类型**：场景解决类

**问题描述**：如何自定义Actuator端点？有哪些方式？

**答案要点**：

**自定义端点：**

```java
// 方式1: @Endpoint注解
@Component
@Endpoint(id = "custom", enableByDefault = true)
public class CustomEndpoint {
    
    @ReadOperation
    public Map<String, Object> getInfo() {
        Map<String, Object> info = new HashMap<>();
        info.put("timestamp", System.currentTimeMillis());
        info.put("version", "1.0");
        return info;
    }
    
    @WriteOperation
    public void clearCache(@Selector String cacheName) {
        // 清理指定缓存
    }
    
    @DeleteOperation
    public void reset() {
        // 删除操作
    }
}

// 方式2: @WebEndpoint（仅Web）
@Component
@WebEndpoint(id = "webCustom")
public class WebCustomEndpoint {
    @GetMapping("/webCustom/info")
    public Map<String, Object> getInfo() {
        return Collections.singletonMap("web", true);
    }
}

// 方式3: @ControllerEndpoint
@RestController
@ControllerEndpoint(id = "controller")
public class ControllerEndpoint {
    
    @GetMapping("/actuator/controller/status")
    public Map<String, String> status() {
        return Collections.singletonMap("status", "OK");
    }
}
```

**暴露配置：**

```yaml
management:
  endpoints:
    web:
      exposure:
        include: health,custom
        exclude: env,beans
```

---

### Q11: 如何集成Prometheus监控？

**题目类型**：场景解决类

**问题描述**：Spring Boot如何集成Prometheus进行监控？

**答案要点**：

**依赖配置：**

```xml
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-actuator</artifactId>
</dependency>
<dependency>
    <groupId>io.micrometer</groupId>
    <artifactId>micrometer-registry-prometheus</artifactId>
</dependency>
```

**配置：**

```yaml
management:
  endpoints:
    web:
      exposure:
        include: health,prometheus,metrics
  prometheus:
    metrics:
      export:
        enabled: true
  metrics:
    tags:
      application: ${spring.application.name}
```

**自定义指标：**

```java
@Service
public class OrderService {
    
    private final MeterRegistry meterRegistry;
    private final Counter orderCounter;
    private final Timer orderTimer;
    
    public OrderService(MeterRegistry registry) {
        this.meterRegistry = registry;
        this.orderCounter = Counter.builder("order.created")
            .description("订单创建数量")
            .tag("service", "order")
            .register(registry);
        
        this.orderTimer = Timer.builder("order.process.time")
            .description("订单处理时间")
            .register(registry);
    }
    
    public void createOrder(Order order) {
        orderCounter.increment();
        
        Timer.Sample sample = Timer.start(meterRegistry);
        try {
            // 处理订单
            processOrder(order);
        } finally {
            sample.stop(orderTimer);
        }
    }
    
    @Timed(value = "order.save.time", percentiles = {0.5, 0.95, 0.99})
    public void saveOrder(Order order) {
        // 自动计时
    }
}
```

---

### Q12: 健康检查如何自定义？

**题目类型**：场景解决类

**问题描述**：如何自定义健康检查指标？如何实现自定义健康检查器？

**答案要点**：

**自定义健康检查器：**

```java
// 方式1: 实现HealthIndicator
@Component
public class RedisHealthIndicator implements HealthIndicator {
    
    @Autowired
    private StringRedisTemplate redisTemplate;
    
    @Override
    public Health health() {
        try {
            String result = redisTemplate.getConnectionFactory()
                .getConnection().ping();
            return Health.up()
                .withDetail("response", result)
                .build();
        } catch (Exception e) {
            return Health.down()
                .withDetail("error", e.getMessage())
                .build();
        }
    }
}

// 方式2: 使用@Liveness和@Readiness探针（K8s）
@Component
public class CustomLivenessHealthIndicator 
    implements LivenessHealthIndicator {
    
    @Override
    public Health health() {
        // 检查应用是否存活
        return Health.up().build();
    }
}

@Component
public class CustomReadinessHealthIndicator 
    implements ReadinessHealthIndicator {
    
    @Override
    public Health health() {
        // 检查应用是否就绪（依赖就绪）
        if (!isDependenciesReady()) {
            return Health.down().build();
        }
        return Health.up().build();
    }
}
```

**健康检查聚合：**

```java
// 组合多个健康检查
@Component
public class CompositeHealthContributor implements HealthContributor {
    
    private final Map<String, HealthIndicator> indicators;
    
    @Override
    public HealthIndicator getContributor(String name) {
        return indicators.get(name);
    }
}
```

---

## 第三部分：高级特性（共6题）

### Q13: Spring Boot的懒加载是什么？如何配置？

**题目类型**：基础概念类

**问题描述**：Spring Boot的懒加载机制是什么？如何启用？有什么优缺点？

**答案要点**：

**懒加载配置：**

```yaml
# 全局懒加载
spring:
  main:
    lazy-initialization: true

# 特定Bean懒加载
@Lazy  # 在类或方法上
public class MyService {
    @Lazy
    private MyDependency dependency;
}
```

**优缺点对比：**

| 优点 | 缺点 |
|------|------|
| 加快应用启动速度 | 首次访问变慢 |
| 减少内存占用 | 请求延迟不确定 |
| 避免不必要的Bean创建 | 可能导致请求超时 |

**使用场景：**

```java
// 1. 大型应用优化启动时间
@SpringBootApplication
@Lazy
public class LargeApplication {}

// 2. 解决循环依赖
@Configuration
public class A {
    @Lazy
    @Autowired
    private B b;
}

// 3. 配置类懒加载
@Configuration
@Lazy
public class HeavyConfig {
    @Bean
    public HeavyBean heavyBean() {
        return new HeavyBean();
    }
}
```

---

### Q14: Spring Boot的Banner如何自定义？

**题目类型**：场景解决类

**问题描述**：如何自定义Spring Boot启动Banner？

**答案要点**：

**自定义Banner：**

```java
// 1. 创建banner.txt文件
// src/main/resources/banner.txt
//   ____      _       _     _            _
//  / ___|___ | | __ _| |__ | | ___   ___| |_ _ __ ___  ___ 
// | |   / _ \| |/ _` | '_ \| |/ _ \ / _ \ __| '__/ _ \/ _ \
// | |__| (_) | | (_| | |_) | | (_) | (_) | |_| | |  __/
//  \____\___/|_|\__,_|_.__/|_|\___/ \___/ \__|_|  \___|
// ${application.title} ${application.version}

// 2. 自定义Banner类
public class MyBanner implements Banner {
    @Override
    public void printBanner(Environment environment, 
            Class<?> sourceClass, PrintStream out) {
        String banner = "My Custom Banner";
        out.println(banner);
    }
}

// 3. 注册自定义Banner
SpringApplication app = new SpringApplication(App.class);
app.setBanner(new MyBanner());
app.run(args);

// 4. 禁用Banner
app.setBannerMode(Banner.Mode.LOG);
```

**动态Banner：**

```java
// 带版本信息的Banner
public class VersionBanner implements Banner {
    @Override
    public void printBanner(Environment env, Class<?> cls, PrintStream out) {
        String title = env.getProperty("spring.application.name", "app");
        String version = env.getProperty("app.version", "1.0.0");
        
        out.println("=================================");
        out.println("  " + title + " v" + version);
        out.println("=================================");
    }
}
```

---

### Q15: Spring Boot如何实现异步任务？

**题目类型**：场景解决类

**问题描述**：Spring Boot如何实现异步任务？有哪些配置方式？

**答案要点**：

**异步配置：**

```java
// 1. 启用异步
@Configuration
@EnableAsync
public class AsyncConfig implements AsyncConfigurer {
    
    @Override
    public Executor getAsyncExecutor() {
        ThreadPoolTaskExecutor executor = new ThreadPoolTaskExecutor();
        executor.setCorePoolSize(5);
        executor.setMaxPoolSize(10);
        executor.setQueueCapacity(100);
        executor.setThreadNamePrefix("async-");
        executor.setWaitForTasksToCompleteOnShutdown(true);
        executor.setAwaitTerminationSeconds(60);
        executor.initialize();
        return executor;
    }
    
    @Override
    public AsyncUncaughtExceptionHandler 
            getAsyncUncaughtExceptionHandler() {
        return (ex, method, params) -> {
            System.err.println("异步任务异常: " + ex.getMessage());
        };
    }
}

// 2. 使用@Async
@Service
public class AsyncService {
    
    @Async
    public CompletableFuture<String> asyncMethod() {
        return CompletableFuture.supplyAsync(() -> {
            // 异步执行
            return "result";
        });
    }
    
    @Async("customExecutor")
    public void customAsyncTask() {
        // 使用指定的线程池
    }
}

// 3. 异常处理
@Async
@SneakyThrows  // Lombok
public void asyncWithException() {
    throw new RuntimeException("异步异常");
}
```

**异步任务监控：**

```java
// TaskDecorator添加任务标识
@Configuration
@EnableAsync
public class AsyncConfig implements AsyncConfigurer {
    @Override
    public Executor getAsyncExecutor() {
        ThreadPoolTaskExecutor executor = new ThreadPoolTaskExecutor();
        // ...
        
        // 添加TaskDecorator
        executor.setTaskDecorator(runnable -> {
            String traceId = MDC.get("traceId");
            return () -> {
                try {
                    MDC.put("traceId", traceId);
                    runnable.run();
                } finally {
                    MDC.remove("traceId");
                }
            };
        });
        
        executor.initialize();
        return executor;
    }
}
```

---

### Q16: Spring Boot如何集成 Knife4j（Swagger）？

**题目类型**：场景解决类

**问题描述**：Spring Boot如何集成Knife4j实现API文档？

**答案要点**：

**Knife4j集成：**

```xml
<dependency>
    <groupId>com.github.xiaoymin</groupId>
    <artifactId>knife4j-openapi2-spring-boot-starter</artifactId>
    <version>4.3.0</version>
</dependency>
```

**配置：**

```yaml
springfox:
  documentation:
    enabled: true

knife4j:
  enable: true
  setting:
    language: zh_CN
  basic:
    enable: false
    username: admin
    password: admin123

springdoc:
  api-docs:
    enabled: true
  swagger-ui:
    enabled: true
```

**Swagger配置：**

```java
@Configuration
@EnableSwagger2
@EnableKnife4j
public class SwaggerConfig {
    
    @Bean
    public OpenAPI customOpenAPI() {
        return OpenAPI.builder()
            .info(new Info()
                .title("API文档")
                .version("1.0")
                .description("接口文档说明"))
            .servers(Arrays.asList(
                new Server().url("http://localhost:8080")))
            .build();
    }
}

// 注解使用
@Api(tags = "用户管理")
@RestController
@RequestMapping("/user")
public class UserController {
    
    @ApiOperation("获取用户信息")
    @ApiImplicitParam(name = "id", value = "用户ID", required = true)
    @GetMapping("/{id}")
    public User getUser(@PathVariable Long id) {
        return userService.findById(id);
    }
}
```

---

## 附录：知识点总结

**Spring Boot核心知识点：**

| 类别 | 关键知识点 |
|------|----------|
| 自动配置 | @EnableAutoConfiguration, @Conditional, @ConfigurationProperties |
| 启动流程 | SpringApplication.run(), refreshContext() |
| 外部化配置 | @ConfigurationProperties, Relaxed Binding |
| Actuator | 健康检查, Prometheus, 自定义端点 |
| 高级特性 | 懒加载, 异步任务, Banner |

---

*本文档共计16道Spring Boot高级面试题。*
