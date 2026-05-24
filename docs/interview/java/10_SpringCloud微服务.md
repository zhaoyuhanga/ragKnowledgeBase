# Spring Cloud微服务 - 20K薪资面试题

> 本文档包含Spring Cloud微服务相关面试题，涵盖服务治理、配置中心、网关、负载均衡、熔断器等核心知识点。

---

## 第一部分：微服务基础（共8题）

### Q1: 什么是微服务架构？它与单体架构有什么区别？

**题目类型**：基础概念类

**问题描述**：微服务架构是什么？它与单体架构有什么区别？微服务有哪些优势和挑战？

**答案要点**：

**架构对比：**

```
┌─────────────────────────────────────────────────────────────┐
│                       单体架构                                │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────┐   │
│  │                  单一应用                              │   │
│  │  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐       │   │
│  │  │  用户   │ │  订单   │ │  支付   │ │  商品   │       │   │
│  │  │ Module │ │ Module │ │ Module │ │ Module │       │   │
│  │  └────────┘ └────────┘ └────────┘ └────────┘       │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                       微服务架构                              │
├─────────────────────────────────────────────────────────────┤
│  ┌────────┐    ┌────────┐    ┌────────┐    ┌────────┐   │
│  │用户服务│    │订单服务│    │支付服务│    │商品服务│   │
│  │ :8001  │    │ :8002  │    │ :8003  │    │ :8004  │   │
│  └────┬────┘    └────┬────┘    └────┬────┘    └────┬────┘│
│       │                │                │                │       │
│       └────────────────┴────────────────┴────────────────┘       │
│                              │                                 │
│                    ┌─────────┴─────────┐                       │
│                    │     服务注册中心   │                       │
│                    │    (Eureka/Nacos) │                       │
│                    └───────────────────┘                       │
└─────────────────────────────────────────────────────────────┘
```

**核心区别对比：**

| 维度 | 单体架构 | 微服务架构 |
|------|----------|------------|
| 部署方式 | 整体部署 | 独立部署 |
| 开发团队 | 大团队 | 小团队自治 |
| 技术栈 | 统一 | 多样化 |
| 可扩展性 | 整体扩展 | 按需扩展 |
| 故障隔离 | 差 | 好 |
| 发布频率 | 低 | 高 |
| 运维复杂度 | 低 | 高 |

**微服务优势：**

```markdown
1. 独立部署 - 各服务可独立发布，不影响其他服务
2. 技术多样性 - 不同服务可用不同技术栈
3. 故障隔离 - 单个服务故障不影响全局
4. 团队自治 - 团队负责独立服务
5. 快速迭代 - 支持持续交付
```

**微服务挑战：**

```markdown
1. 分布式复杂性 - 网络延迟、分布式事务
2. 服务治理 - 注册发现、负载均衡、熔断
3. 运维复杂度 - 监控、日志、部署
4. 数据一致性 - CAP定理权衡
```

---

### Q2: Spring Cloud包含哪些核心组件？

**题目类型**：基础概念类

**问题描述**：Spring Cloud包含哪些核心组件？它们的作用是什么？

**答案要点**：

**Spring Cloud组件全景图：**

```
┌─────────────────────────────────────────────────────────────┐
│                    Spring Cloud 组件生态                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  服务注册与发现                                             │
│  ├── Eureka (Netflix)                                     │
│  ├── Nacos (Alibaba)                                      │
│  └── Consul (HashiCorp)                                    │
│                                                             │
│  配置中心                                                   │
│  ├── Spring Cloud Config                                   │
│  ├── Nacos Config                                          │
│  └── Apollo (携程)                                         │
│                                                             │
│  网关                                                       │
│  ├── Gateway (WebFlux)                                    │
│  └── Zuul (Netflix, 1.x已停更)                            │
│                                                             │
│  负载均衡                                                   │
│  ├── Ribbon (Netflix)                                      │
│  └── LoadBalancer (Spring)                                  │
│                                                             │
│  熔断器                                                     │
│  ├── Hystrix (Netflix, 已停更)                            │
│  └── Resilience4j                                           │
│                                                             │
│  服务调用                                                   │
│  ├── Feign (OpenFeign)                                    │
│  └── OpenFeign                                             │
│                                                             │
│  消息队列                                                   │
│  ├── Stream                                                │
│  └── Bus                                                   │
│                                                             │
│  分布式链路追踪                                             │
│  ├── Sleuth                                                │
│  ├── Zipkin                                               │
│  └── SkyWalking                                           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**推荐技术栈：**

```yaml
# Spring Cloud Alibaba（推荐）
spring:
  cloud:
    nacos:
      discovery:
        server-addr: nacos-server:8848
      config:
        server-addr: nacos-server:8848
        file-extension: yaml
```

---

### Q3: 服务注册与发现是什么？如何实现？

**题目类型**：技术原理类

**问题描述**：什么是服务注册与发现？Spring Cloud如何实现服务注册发现？

**答案要点**：

**服务注册与发现流程：**

```
┌─────────────────────────────────────────────────────────────┐
│                   服务注册与发现机制                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  服务启动时:                                                │
│  服务实例 ──▶ 注册中心 ──▶ 保存实例信息                    │
│  (register)   (Nacos/Eureka)  (IP、端口、健康状态)        │
│                                                             │
│  服务调用时:                                                │
│  调用方 ──▶ 注册中心查询 ──▶ 获取服务实例列表              │
│           (发现)       ──▶ 负载均衡选择                      │
│                        ──▶ 直连目标服务                     │
│                                                             │
│  心跳机制:                                                  │
│  服务实例 ──▶ 定时发送心跳 ──▶ 注册中心                     │
│                (每30秒)    (超时则剔除)                     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Nacos实现：**

```yaml
# 服务端配置 (application.yml)
server:
  port: 8848
spring:
  nacos:
    discovery:
      enabled: true
    namespace: dev

# 客户端配置
spring:
  application:
    name: order-service
  cloud:
    nacos:
      discovery:
        server-addr: nacos-server:8848
        namespace: dev
        group: DEFAULT_GROUP
        weight: 1.0
        enabled: true
        register-enabled: true
```

```java
// 服务启动类
@SpringBootApplication
@EnableDiscoveryClient
public class OrderApplication {
    public static void main(String[] args) {
        SpringApplication.run(OrderApplication.class, args);
    }
}

// 服务调用方发现服务
@RestController
public class OrderController {
    
    @Autowired
    private DiscoveryClient discoveryClient;
    
    @GetMapping("/findInstances")
    public List<ServiceInstance> findInstances() {
        // 查询指定服务实例
        return discoveryClient.getInstances("user-service");
    }
    
    @GetMapping("/getServices")
    public List<String> getServices() {
        // 获取所有服务名
        return discoveryClient.getServices();
    }
}
```

**Eureka实现（已停更，仅供了解）：**

```yaml
# Eureka Server
server:
  port: 8761
eureka:
  instance:
    hostname: eureka-server
  client:
    register-with-eureka: false
    fetch-registry: false

# Eureka Client
eureka:
  client:
    service-url:
      defaultZone: http://eureka-server:8761/eureka/
  instance:
    prefer-ip-address: true
```

---

### Q4: Ribbon和LoadBalancer有什么区别？

**题目类型**：技术对比类

**问题描述**：Ribbon和Spring Cloud LoadBalancer有什么区别？如何选择？

**答案要点**：

**核心区别对比：**

| 特性 | Ribbon | LoadBalancer |
|------|--------|--------------|
| 维护状态 | Netflix已停止维护 | Spring官方维护 |
| 位置 | 独立组件 | 集成在Spring Cloud中 |
| 配置 | 较为复杂 | 简化配置 |
| 负载均衡策略 | 多种内置策略 | 可扩展接口 |
| 组合方式 | 与Feign紧耦合 | 可独立使用 |

**Ribbon负载均衡策略：**

```java
// 内置负载均衡策略
public interface IRule {
    // 轮询
    RoundRobinRule
    
    // 随机
    RandomRule
    
    // 权重
    WeightedResponseTimeRule
    
    // 过滤连续失败的服务
    RetryRule
    
    // 轮询 + 重试
    BestAvailableRule
    
    // 可用性过滤（跳过熔断的服务）
    AvailabilityFilteringRule
    
    // 粘性连接
    StickyKeyHashRule
}

// 自定义Ribbon配置
@Configuration
public class RibbonConfig {
    @Bean
    public IRule rule() {
        // 使用随机策略
        return new RandomRule();
    }
}
```

**LoadBalancer实现：**

```java
// 使用LoadBalancer
@Configuration
public class LoadBalancerConfig {
    @Bean
    public ReactorLoadBalancer<ServiceInstance> randomLoadBalancer(
            ServiceInstanceListSupplier supplier) {
        return new RandomLoadBalancer(supplier);
    }
}

// 服务调用
@RestController
public class UserController {
    
    @Autowired
    private RestTemplate restTemplate;
    
    @Bean
    @LoadBalancerInterceptor
    public RestTemplate restTemplate() {
        return new RestTemplate();
    }
    
    @GetMapping("/call-user")
    public String callUser() {
        // 自动使用负载均衡
        return restTemplate.getForObject(
            "http://user-service/user/1", String.class);
    }
}
```

---

### Q5: Feign是什么？它的工作原理是什么？

**题目类型**：技术原理类

**问题描述**：Feign是什么？它是如何工作的？如何集成和使用？

**答案要点**：

**Feign工作原理：**

```
┌─────────────────────────────────────────────────────────────┐
│                       Feign 调用流程                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. 定义接口                                               │
│  @FeignClient(name = "user-service")                       │
│  public interface UserClient {                            │
│      @GetMapping("/user/{id}")                             │
│      User getUser(@PathVariable Long id);                  │
│  }                                                         │
│                                                             │
│  2. 动态代理创建                                          │
│  Feign.Builder                                            │
│       │                                                    │
│       ▼                                                    │
│  ReflectiveFeign$HardCodedTarget                           │
│       │                                                    │
│       ▼                                                    │
│  SynchronousMethodHandler                                   │
│       │                                                    │
│       ├── LoadBalancerInterceptor (添加服务名解析)          │
│       └── Retryer (重试处理)                               │
│                                                             │
│  3. 请求执行流程                                           │
│  请求 ──▶ Encoder ──▶ Logger ──▶ Client ──▶ 响应         │
│            编码      调试       执行                        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Feign配置：**

```xml
<dependency>
    <groupId>org.springframework.cloud</groupId>
    <artifactId>spring-cloud-starter-openfeign</artifactId>
</dependency>
```

```java
// 启动类
@SpringBootApplication
@EnableFeignClients
public class OrderApplication {}

// 定义Feign客户端
@FeignClient(
    name = "user-service",  // 服务名
    url = "http://localhost:8001",  // 可选
    fallback = UserClientFallback.class,  // 熔断降级
    configuration = FeignConfig.class  // 自定义配置
)
public interface UserClient {
    
    @GetMapping("/user/{id}")
    User getUser(@PathVariable("id") Long id);
    
    @PostMapping("/user")
    User createUser(@RequestBody User user);
}

// 降级实现
@Component
public class UserClientFallback implements UserClient {
    @Override
    public User getUser(Long id) {
        return new User(id, "默认用户");
    }
    
    @Override
    public User createUser(User user) {
        return user;
    }
}

// 自定义配置
@Configuration
public class FeignConfig {
    
    @Bean
    public Logger.Level feignLogger() {
        return Logger.Level.FULL;
    }
    
    @Bean
    public Retryer feignRetryer() {
        // 重试配置
        return new Retryer.Default(100, 1000, 3);
    }
}
```

**高级配置：**

```yaml
spring:
  cloud:
    openfeign:
      client:
        config:
          default:
            loggerLevel: full
            connectTimeout: 5000
            readTimeout: 5000
          user-service:
            loggerLevel: basic
      circuitbreaker:
        enabled: true
```

---

### Q6: 什么是熔断器？Hystrix和Resilience4j有什么区别？

**题目类型**：技术对比类

**问题描述**：什么是熔断器模式？Hystrix和Resilience4j有什么区别？

**答案要点**：

**熔断器原理：**

```
┌─────────────────────────────────────────────────────────────┐
│                    熔断器状态机                               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│                    ┌─────────────┐                          │
│                    │   CLOSED    │                          │
│                    │   关闭状态   │                          │
│                    │  (正常调用)  │                          │
│                    └──────┬──────┘                          │
│                           │ 失败率超过阈值                   │
│                           ▼                                 │
│                    ┌─────────────┐                          │
│                    │    OPEN     │                          │
│                    │   打开状态   │                          │
│                    │ (快速失败)  │                          │
│                    └──────┬──────┘                          │
│                           │ 超时后尝试半开                   │
│                           ▼                                 │
│                    ┌─────────────┐                          │
│                    │ HALF-OPEN   │                          │
│                    │  半开状态   │                          │
│                    │ (尝试请求)  │                          │
│                    └──────┬──────┘                          │
│                      成功 │ 失败                             │
│                           ▼                                 │
│                    ┌─────────────┐                          │
│                    │   CLOSED    │或│    OPEN    │          │
│                    └─────────────┘  └─────────────┘          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Resilience4j配置：**

```xml
<dependency>
    <groupId>io.github.resilience4j</groupId>
    <artifactId>resilience4j-spring-boot3</artifactId>
</dependency>
```

```java
// 熔断器配置
@CircuitBreaker(
    name = "userService",
    fallbackMethod = "fallback"
)
public String callUserService() {
    return restTemplate.getForObject(
        "http://user-service/user/1", String.class);
}

// 降级方法
public String fallback(Exception e) {
    return "服务暂时不可用，请稍后再试";
}

// 重试配置
@Retry(
    name = "userService",
    maxAttempts = 3,
    waitDuration = Duration.ofMillis(500)
)
public String callWithRetry() {
    return restTemplate.getForObject(
        "http://user-service/user/1", String.class);
}

// 限流配置
@RateLimiter(
    name = "userService",
    limitForPeriod = 10,
    limitRefreshPeriod = Duration.ofSeconds(1)
)
public String callWithRateLimit() {
    return restTemplate.getForObject(
        "http://user-service/user/1", String.class);
}
```

```yaml
resilience4j:
  circuitbreaker:
    instances:
      userService:
        registerHealthIndicator: true
        slidingWindowSize: 10
        failureRateThreshold: 50
        waitDurationInOpenState: 10s
        permittedNumberOfCallsInHalfOpenState: 5
  retry:
    instances:
      userService:
        maxAttempts: 3
        waitDuration: 500ms
  ratelimiter:
    instances:
      userService:
        limitForPeriod: 10
        limitRefreshPeriod: 1s
```

---

### Q7: Gateway网关是什么？它有哪些核心概念？

**题目类型**：技术原理类

**问题描述**：Spring Cloud Gateway是什么？它的核心概念和配置是什么？

**答案要点**：

**Gateway架构：**

```
┌─────────────────────────────────────────────────────────────┐
│                   Spring Cloud Gateway                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  请求 ──▶ Gateway Handler Mapping                            │
│              │                                              │
│              ▼                                              │
│         Gateway Web Handler                                  │
│              │                                              │
│              ├── Pre Filters (前置过滤器)                   │
│              │                                              │
│              ▼                                              │
│         Gateway Filter Chain                                 │
│              │                                              │
│              ├── 1. 动态路由                               │
│              ├── 2. 身份认证                               │
│              ├── 3. 限流熔断                               │
│              └── 4. 日志监控                               │
│              │                                              │
│              ├── Post Filters (后置过滤器)                  │
│              ▼                                              │
│         代理到后端服务                                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**路由配置：**

```yaml
spring:
  cloud:
    gateway:
      discovery:
        locator:
          enabled: true  # 启用服务发现定位器
          lower-case-service-id: true
      routes:
        - id: user-service
          uri: lb://user-service  # lb表示负载均衡
          predicates:
            - Path=/user/**
            - After=2024-01-01T00:00:00Z
          filters:
            - StripPrefix=1
            - AddRequestHeader=X-Request, Test
            - name: RequestSize
              args:
                maxSize: 5000000
        
        - id: order-service
          uri: lb://order-service
          predicates:
            - Host=**.example.com
            - Method=GET,POST
          filters:
            - name: CircuitBreaker
              args:
                name: orderCircuitBreaker
                fallbackUri: forward:/fallback
```

**动态路由：**

```java
// 编码方式配置路由
@Configuration
public class GatewayConfig {
    
    @Bean
    public RouteLocator customRouteLocator(
            RouteLocatorBuilder builder) {
        return builder.routes()
            .route("user-route", r -> r
                .path("/api/user/**")
                .filters(f -> f
                    .stripPrefix(1)
                    .addRequestHeader("X-Custom", "HeaderValue"))
                .uri("lb://user-service"))
            .route("order-route", r -> r
                .path("/api/order/**")
                .filters(f -> f
                    .retry(3)
                    .requestRateLimiter()
                        .rateLimiter(redisRateLimiter())
                        .keyResolver(userKeyResolver()))
                .uri("lb://order-service"))
            .build();
    }
    
    @Bean
    public RedisRateLimiter redisRateLimiter() {
        return new RedisRateLimiter(100, 200);
    }
}
```

---

### Q8: Gateway如何实现认证授权？

**题目类型**：场景解决类

**问题描述**：Gateway如何实现统一的认证授权？有哪些实现方式？

**答案要点**：

**认证授权实现：**

```java
// 全局过滤器实现认证
@Component
public class AuthFilter implements GlobalFilter, Ordered {
    
    @Autowired
    private JwtUtil jwtUtil;
    
    @Override
    public Mono<Void> filter(ServerWebExchange exchange, 
            GatewayFilterChain chain) {
        String token = exchange.getRequest()
            .getHeaders().getFirst("Authorization");
        
        // 白名单路径直接放行
        String path = exchange.getRequest().getURI().getPath();
        if (isWhiteList(path)) {
            return chain.filter(exchange);
        }
        
        // 验证Token
        if (StringUtils.isBlank(token) || !token.startsWith("Bearer ")) {
            exchange.getResponse().setStatusCode(
                HttpStatus.UNAUTHORIZED);
            return exchange.getResponse().setComplete();
        }
        
        String jwt = token.substring(7);
        try {
            Claims claims = jwtUtil.parseToken(jwt);
            String userId = claims.getSubject();
            
            // 传递给下游服务
            ServerHttpRequest mutatedRequest = exchange.getRequest()
                .mutate()
                .header("X-User-Id", userId)
                .build();
            
            return chain.filter(
                exchange.mutate().request(mutatedRequest).build());
        } catch (Exception e) {
            exchange.getResponse().setStatusCode(
                HttpStatus.UNAUTHORIZED);
            return exchange.getResponse().setComplete();
        }
    }
    
    @Override
    public int getOrder() {
        return -100;  // 优先级
    }
}

// 权限校验过滤器
@Component
public class PermissionFilter implements GlobalFilter {
    
    @Override
    public Mono<Void> filter(ServerWebExchange exchange, 
            GatewayFilterChain chain) {
        ServerHttpRequest request = exchange.getRequest();
        String userId = request.getHeaders().getFirst("X-User-Id");
        String path = request.getURI().getPath();
        String method = request.getMethod().name();
        
        // 从Redis或数据库查询权限
        if (!hasPermission(userId, path, method)) {
            exchange.getResponse().setStatusCode(
                HttpStatus.FORBIDDEN);
            return exchange.getResponse().setComplete();
        }
        
        return chain.filter(exchange);
    }
}
```

**整合Spring Security：**

```java
@Configuration
@EnableWebFluxSecurity
public class SecurityConfig {
    
    @Bean
    public SecurityWebFilterChain securityWebFilterChain(
            ServerHttpSecurity http) {
        return http
            .csrf().disable()
            .authorizeExchange(exchanges -> exchanges
                .pathMatchers("/auth/**", "/actuator/**").permitAll()
                .pathMatchers("/admin/**").hasAuthority("ROLE_ADMIN")
                .anyExchange().authenticated())
            .httpBasic()
            .and()
            .build();
    }
}
```

---

## 第二部分：配置中心（共6题）

### Q9: Spring Cloud Config是什么？如何使用？

**题目类型**：基础概念类

**问题描述**：Spring Cloud Config是什么？它如何实现配置管理？

**答案要点**：

**Config架构：**

```
┌─────────────────────────────────────────────────────────────┐
│                  Spring Cloud Config 架构                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                    Git仓库                             │  │
│  │  ├── application.yml                                  │  │
│  │  ├── application-dev.yml                             │  │
│  │  ├── order-service.yml                              │  │
│  │  └── order-service-dev.yml                          │  │
│  └──────────────────────────────────────────────────────┘  │
│                              │                               │
│                              ▼                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                  Config Server                         │  │
│  │                  :8888端口                            │  │
│  └──────────────────────────────────────────────────────┘  │
│                              │                               │
│    ┌─────────────┬─────────────┬─────────────┐            │
│    ▼             ▼             ▼                         │
│ ┌──────┐      ┌──────┐      ┌──────┐                   │
│ │Order │      │ User │      │ Pay  │                   │
│ │Service│    │Service│     │Service│                   │
│ └──────┘      └──────┘      └──────┘                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Config Server配置：**

```yaml
server:
  port: 8888
spring:
  application:
    name: config-server
  cloud:
    config:
      server:
        git:
          uri: https://github.com/your-org/config-repo
          default-label: main
          search-paths: config
          username: ${GIT_USERNAME}
          password: ${GIT_PASSWORD}
          timeout: 10
          force-pull: true
```

```java
@SpringBootApplication
@EnableConfigServer
public class ConfigServerApplication {
    public static void main(String[] args) {
        SpringApplication.run(ConfigServerApplication.class, args);
    }
}
```

**Config Client配置：**

```yaml
spring:
  application:
    name: order-service
  cloud:
    config:
      enabled: true
      uri: http://config-server:8888
      profile: dev
      label: main
      fail-fast: true  # 配置获取失败时启动失败
      retry:
        enabled: true
        max-attempts: 6
        multiplier: 1.5
```

---

### Q10: Nacos作为配置中心如何使用？

**题目类型**：场景解决类

**问题描述**：Nacos如何作为配置中心使用？有哪些特性？

**答案要点**：

**Nacos配置中心：**

```yaml
# 配置客户端
spring:
  application:
    name: order-service
  cloud:
    nacos:
      config:
        server-addr: nacos-server:8848
        namespace: dev
        group: DEFAULT_GROUP
        file-extension: yaml
        refresh-enabled: true
        # 共享配置
        shared-configs:
          - data-id: common.yaml
            group: COMMON_GROUP
            refresh: true
        # 扩展配置
        extension-configs:
          - data-id: redis.yaml
            group: EXTENSION_GROUP
            refresh: true
```

```java
// 动态刷新配置
@RestController
@RefreshScope  // 动态刷新
public class ConfigController {
    
    @Value("${app.title:default}")
    private String title;
    
    @GetMapping("/title")
    public String getTitle() {
        return title;
    }
}

// 使用配置对象
@Data
@Component
@RefreshScope
@ConfigurationProperties(prefix = "app.order")
public class OrderProperties {
    private int timeout = 5000;
    private int maxRetries = 3;
    private List<String> allowOrigins;
}
```

**Nacos特性：**

```java
// 监听配置变更
@NacosConfigListener
public void onConfigChange(String config) {
    System.out.println("配置变更: " + config);
}

// Nacos API方式
@Autowired
private ConfigService configService;

public String getConfig(String dataId, String group) {
    return configService.getConfig(dataId, group, 5000);
}

public void publishConfig(String dataId, String group, String content) {
    configService.publishConfig(dataId, group, content);
}
```

---

### Q11: 配置加密如何实现？

**题目类型**：场景解决类

**问题描述**：敏感配置（如数据库密码、API密钥）如何加密存储和使用？

**答案要点**：

**Config Server加密：**

```yaml
# 启用加密
encrypt:
  key: your-256-bit-secret-key  # 对称密钥

# 或者使用RSA
encrypt:
  RSA:
    keystore:
      location: classpath:encryption.jks
      password: changeit
      alias: configserver
```

```bash
# 使用命令行加密
curl -X POST "http://localhost:8888/encrypt" \
  -d "my-secret-password"

# 解密
curl -X POST "http://localhost:8888/decrypt" \
  -d "encrypted-value"
```

**Nacos敏感配置：**

```yaml
# 使用加密配置
spring:
  datasource:
    password: '{cipher}encrypted_password'

# 自定义加密算法
@Configuration
public class EncryptionConfig {
    @Bean
    public TextEncryptor textEncryptor() {
        return new AesTextEncryptor("secret-key");
    }
}
```

**最佳实践：**

```java
// 1. 使用配置中心加密功能
// 2. 敏感值存储在KMS中
// 3. 应用启动时从KMS获取密钥
// 4. 使用Vault管理敏感配置

// Vault集成
@Configuration
public class VaultConfig {
    @Bean
    public VaultTemplate vaultTemplate() {
        VaultOperations ops = new VaultTemplate(
            new VaultEndpoint());
        return new VaultTemplate(ops.connectionFactory());
    }
}
```

---

## 第三部分：服务治理（共6题）

### Q12: 什么是服务雪崩？如何防止？

**题目类型**：技术原理类

**问题描述**：什么是服务雪崩？如何防止服务雪崩？

**答案要点**：

**服务雪崩原因：**

```
┌─────────────────────────────────────────────────────────────┐
│                      服务雪崩效应                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  时刻T: A服务故障                                          │
│      │                                                      │
│      ▼                                                      │
│  时刻T+1: 调用A的超时等待                                  │
│      │                                                      │
│      ▼                                                      │
│  时刻T+2: 线程池/连接池耗尽                                │
│      │                                                      │
│      ▼                                                      │
│  时刻T+3: B服务不可用（依赖A）                            │
│      │                                                      │
│      ▼                                                      │
│  时刻T+4: C服务不可用（依赖B）                            │
│      │                                                      │
│      ▼                                                      │
│  时刻T+5: 整个系统崩溃                                     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**防止策略：**

```java
// 1. 服务超时
@Configuration
public class TimeoutConfig {
    @Bean
    public RestTemplate restTemplate() {
        SimpleClientHttpRequestFactory factory = 
            new SimpleClientHttpRequestFactory();
        factory.setConnectTimeout(3000);
        factory.setReadTimeout(5000);
        return new RestTemplate(factory);
    }
}

// 2. 限流
@RateLimiter(name = "backendService", 
    limitForPeriod = 100, limitRefreshPeriod = 1)
public String callBackend() {
    return restTemplate.getForObject(
        "http://backend/api", String.class);
}

// 3. 熔断器
@CircuitBreaker(name = "backendService", 
    fallbackMethod = "fallback")
public String callBackend() {
    return restTemplate.getForObject(
        "http://backend/api", String.class);
}

// 4. 舱壁模式
@Bean
public ThreadPoolExecutor userServiceExecutor() {
    return new ThreadPoolExecutor(
        10, 20, 60, TimeUnit.SECONDS,
        new LinkedBlockingQueue<>(100),
        new ThreadFactoryBuilder()
            .setNameFormat("user-pool-%d")
            .build());
}

// 5. 资源隔离
@HystrixCommand(
    commandProperties = {
        @HystrixProperty(
            name = "execution.isolation.thread.timeoutInMilliseconds",
            value = "5000"),
        @HystrixProperty(
            name = "circuitBreaker.enabled",
            value = "true"),
        @HystrixProperty(
            name = "fallback.enabled",
            value = "true")
    },
    threadPoolProperties = {
        @HystrixProperty(name = "coreSize", value = "10"),
        @HystrixProperty(name = "maxQueueSize", value = "20")
    }
)
public String callService() {
    // 业务逻辑
}
```

---

### Q13: 分布式链路追踪是什么？如何实现？

**题目类型**：技术原理类

**问题描述**：什么是分布式链路追踪？Spring Cloud Sleuth + Zipkin如何实现？

**答案要点**：

**链路追踪原理：**

```
┌─────────────────────────────────────────────────────────────┐
│                    分布式链路追踪                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Trace: 全链路唯一标识                                       │
│  Span: 单个服务调用单元                                     │
│  Annotation: 关键事件记录                                   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐  │
│  │                    Trace ID                           │  │
│  │  ┌─────┐    ┌─────┐    ┌─────┐    ┌─────┐        │  │
│  │  │Span1│───▶│Span2│───▶│Span3│───▶│Span4│        │  │
│  │  │User │    │Order│    │ User│    │ Pay │        │  │
│  │  │Service│   │Service│   │Service│   │Service│    │  │
│  │  └─────┘    └─────┘    └─────┘    └─────┘        │  │
│  │    cs         sr         ss         cs             │  │
│  │              │                      │               │  │
│  │              ▼                      ▼               │  │
│  │         ┌──────────────────────────────────┐       │  │
│  │         │         Zipkin Server           │       │  │
│  │         └──────────────────────────────────┘       │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Sleuth + Zipkin集成：**

```xml
<dependency>
    <groupId>org.springframework.cloud</groupId>
    <artifactId>spring-cloud-starter-sleuth</artifactId>
</dependency>
<dependency>
    <groupId>org.springframework.cloud</groupId>
    <artifactId>spring-cloud-starter-zipkin</artifactId>
</dependency>
```

```yaml
spring:
  zipkin:
    base-url: http://zipkin-server:9411
    sender:
      type: web  # 或 rabbitmq
  sleuth:
    sampler:
      probability: 1.0  # 采样比例
      rate: 100        # 每秒采样数
    propagation:
      tag:
        custom-key: custom-value
```

**自定义链路数据：**

```java
// 添加链路标签
@Autowired
private Tracer tracer;

@GetMapping("/order/{id}")
public Order getOrder(@PathVariable Long id) {
    Span span = tracer.currentSpan();
    span.tag("order.id", id.toString());
    span.event("start-fetch-order");
    
    Order order = orderService.findById(id);
    
    span.tag("order.status", order.getStatus());
    span.event("order-fetched");
    
    return order;
}

// 异步链路
@Async
@Traced
public void asyncProcess() {
    // 自动传递链路上下文
}
```

---

### Q14: 分布式事务如何处理？

**题目类型**：技术原理类

**问题描述**：微服务架构下如何处理分布式事务？有哪些方案？

**答案要点**：

**分布式事务方案对比：**

| 方案 | 原理 | 优点 | 缺点 |
|------|------|------|------|
| 两阶段提交(2PC) | 协调者统一提交/回滚 | 强一致 | 阻塞、低性能 |
| TCC | Try-Confirm-Cancel | 异步高性能 | 实现复杂 |
| 本地消息表 | 本地表+定时任务 | 简单可靠 | 复杂度转移 |
| Seata | AT/SAGA模式 | 功能完善 | 引入中间件 |
| 最终一致性 | MQ+补偿 | 高性能 | 弱一致 |

**Seata AT模式：**

```xml
<dependency>
    <groupId>com.alibaba.cloud</groupId>
    <artifactId>spring-cloud-starter-alibaba-seata</artifactId>
</dependency>
```

```yaml
seata:
  enabled: true
  application-id: ${spring.application.name}
  tx-service-group: my_tx_group
  config:
    type: nacos
    nacos:
      server-addr: ${NACOS_HOST}:8848
  registry:
    type: nacos
```

```java
// 全局事务注解
@GlobalTransactional(name = "create-order", rollbackFor = Exception.class)
public void createOrder(OrderDTO orderDTO) {
    // 1. 创建订单（本地事务）
    Order order = new Order();
    orderService.save(order);
    
    // 2. 扣减库存（远程服务）
    inventoryClient.deductStock(orderDTO.getProductId(), 
        orderDTO.getQuantity());
    
    // 3. 扣减余额（远程服务）
    accountClient.deductBalance(orderDTO.getUserId(), 
        orderDTO.getAmount());
}

// TCC模式
@LocalTCC
public interface StorageTccService {
    
    @TwoPhaseBusinessAction(
        name = "prepare",
        commitMethod = "commit",
        rollbackMethod = "rollback"
    )
    boolean prepare(
        @BusinessActionContextParameter(paramName = "productId") 
            Long productId,
        @BusinessActionContextParameter(paramName = "count") 
            Integer count);
    
    boolean commit(BusinessActionContext context);
    
    boolean rollback(BusinessActionContext context);
}
```

---

### Q15: 服务降级和熔断如何配置？

**题目类型**：场景解决类

**问题描述**：如何配置服务降级和熔断？有哪些最佳实践？

**答案要点**：

**Gateway熔断降级：**

```yaml
spring:
  cloud:
    gateway:
      routes:
        - id: order-service
          uri: lb://order-service
          filters:
            - name: CircuitBreaker
              args:
                name: orderCircuit
                fallbackUri: forward:/fallback/order
            - name: RequestRateLimiter
              args:
                redis-rate-limiter.replenishRate: 100
                redis-rate-limiter.burstCapacity: 200
```

```java
// Fallback控制器
@RestController
public class FallbackController {
    
    @GetMapping("/fallback/order")
    public Result<List<Order>> orderFallback() {
        return Result.fail(503, "服务暂时不可用，请稍后再试");
    }
}
```

**Feign降级配置：**

```java
// 全局降级配置
@Configuration
public class FeignFallbackConfig {
    
    @Bean
    public Fallback<UserClient> userFallback() {
        return new Fallback<UserClient>() {
            @Override
            public User getUser(Long id) {
                return new User(id, "默认用户");
            }
            
            @Override
            public List<User> getUsers() {
                return Collections.emptyList();
            }
        };
    }
}
```

**最佳实践：**

```java
// 1. 降级返回默认值/缓存
@Service
public class UserServiceFallback implements UserService {
    
    @Autowired
    private UserCache userCache;
    
    @Override
    public User getUser(Long id) {
        // 先尝试从缓存获取
        User cached = userCache.get(id);
        if (cached != null) {
            return cached;
        }
        return new User(id, "默认用户");
    }
}

// 2. 降级返回友好提示
public String fallback() {
    return "服务繁忙，请稍后再试";
}

// 3. 记录降级日志便于监控
public String fallback(Throwable t) {
    log.warn("调用失败，降级处理: {}", t.getMessage());
    return "系统繁忙";
}
```

---

### Q16: 如何实现服务限流？

**题目类型**：场景解决类

**问题描述**：微服务如何实现限流？有哪些限流算法和实现方式？

**答案要点**：

**限流算法：**

| 算法 | 原理 | 优点 | 缺点 |
|------|------|------|------|
| 计数器 | 固定窗口计数 | 简单 | 边界问题 |
| 滑动窗口 | 移动窗口计数 | 精确 | 实现复杂 |
| 漏桶 | 以恒定速率处理 | 稳定 | 不适合突发 |
| 令牌桶 | 令牌补充，匀速获取 | 允许突发 | - |

**Gateway限流：**

```yaml
spring:
  cloud:
    gateway:
      redis-rate-limiter:
        replenishRate: 100      # 每秒补充令牌数
        burstCapacity: 200      # 桶容量
        requestedTokens: 1      # 每个请求消耗令牌
```

```java
// 自定义Key解析器
@Component
public class UserKeyResolver implements KeyResolver {
    
    @Override
    public Mono<String> resolve(ServerWebExchange exchange) {
        // 按用户ID限流
        String userId = exchange.getRequest()
            .getHeaders().getFirst("X-User-Id");
        
        // 或按IP限流
        String ip = exchange.getRequest()
            .getRemoteAddress().getAddress().getHostAddress();
        
        return Mono.justOrEmpty(userId != null ? userId : ip);
    }
}
```

**Resilience4j限流：**

```java
@RateLimiter(name = "backendService", 
    fallbackMethod = "rateLimitFallback")
@GetMapping("/api")
public String api() {
    return "API response";
}

public String rateLimitFallback(Exception e) {
    return "请求过于频繁，请稍后再试";
}
```

**Sentinel集成：**

```xml
<dependency>
    <groupId>com.alibaba.cloud</groupId>
    <artifactId>spring-cloud-starter-alibaba-sentinel</artifactId>
</dependency>
```

```java
// Sentinel注解方式
@SentinelResource(value = "api",
    blockHandler = "blockHandler",
    fallback = "fallback")
public String api() {
    return "response";
}

// 限流处理
public String blockHandler(BlockException e) {
    return "被限流了";
}

// 降级处理
public String fallback(Throwable e) {
    return "服务异常";
}
```

---

## 附录：知识点总结

**Spring Cloud核心知识点：**

| 类别 | 关键知识点 |
|------|----------|
| 服务治理 | 注册发现、负载均衡、熔断降级 |
| 网关 | Gateway路由、过滤器、认证授权 |
| 配置中心 | Config Server、Nacos配置管理 |
| 服务通信 | Feign、Ribbon、LoadBalancer |
| 分布式问题 | 链路追踪、分布式事务、服务限流 |

---

*本文档共计16道Spring Cloud微服务面试题。*
