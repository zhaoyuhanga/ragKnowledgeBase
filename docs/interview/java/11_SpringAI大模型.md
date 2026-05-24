# Spring AI - 20K薪资面试题

> 本文档包含Spring AI相关面试题，涵盖AI模型集成、Prompt工程、RAG实现、向量数据库集成等核心知识点。

---

## 第一部分：Spring AI基础（共8题）

### Q1: 什么是Spring AI？它有什么特点？

**题目类型**：基础概念类

**问题描述**：什么是Spring AI？它与其他AI集成方案有什么区别？

**答案要点**：

**Spring AI是什么：**
Spring AI是Spring生态提供的AI工程化框架，旨在简化AI应用的开发，提供统一的API访问各种AI模型。

**核心特点：**

| 特性 | 说明 |
|------|------|
| 多模型支持 | OpenAI、Azure OpenAI、Anthropic、HuggingFace等 |
| 统一API | 抽象层统一接口，易于切换模型 |
| Prompt工程 | 丰富的Prompt模板和参数配置 |
| 结构化输出 | 支持POJO映射 |
| RAG支持 | 文档处理、向量化、检索增强 |
| 向量存储 | 集成多种向量数据库 |

**架构图：**

```
┌─────────────────────────────────────────────────────────────┐
│                    Spring AI 架构                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  应用层 (Your Application)                                   │
│  ├── @Autowired ChatClient                                 │
│  ├── @Autowired ImageClient                               │
│  └── @Autowired EmbeddingClient                           │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐  │
│  │                    Spring AI Core                     │  │
│  │  ├── ChatMemory           ├── OutputConverter       │  │
│  │  ├── PromptTemplate       ├── FunctionCallback      │  │
│  │  └── Advisor               └── SearchRequest          │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐  │
│  │              Model Access (Spring Boot Starters)      │  │
│  │  ├── openai-spring-boot-starter                      │  │
│  │  ├── anthropic-spring-boot-starter                   │  │
│  │  ├── azure-openai-spring-boot-starter                │  │
│  │  └── huggingface-spring-boot-starter                  │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐  │
│  │              AI Models (第三方服务)                     │  │
│  │  ├── OpenAI GPT-4                                   │  │
│  │  ├── Anthropic Claude                                │  │
│  │  ├── Azure OpenAI                                   │  │
│  │  └── HuggingFace                                    │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**与其他方案对比：**

| 方案 | 优点 | 缺点 |
|------|------|------|
| Spring AI | 统一API、Spring生态集成、丰富的RAG支持 | 相对较新 |
| LangChain4j | 功能丰富、社区活跃 | 学习曲线 |
| 直接SDK | 灵活 | 需要自己处理很多细节 |

---

### Q2: Spring AI支持哪些AI模型？

**题目类型**：基础概念类

**问题描述**：Spring AI支持哪些AI模型？如何集成？

**答案要点**：

**支持模型类型：**

| 类型 | 支持的模型 | Starter依赖 |
|------|------------|-------------|
| 对话模型 | OpenAI GPT, Claude, Azure OpenAI, Cohere | openai-spring-boot-starter |
| 嵌入模型 | OpenAI Ada, HuggingFace, Azure | embedding-openai-spring-boot-starter |
| 图像模型 | OpenAI DALL-E, Stable Diffusion | openai-spring-boot-starter |
| 音频模型 | OpenAI Whisper | openai-spring-boot-starter |

**OpenAI集成：**

```xml
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-web</artifactId>
</dependency>
<dependency>
    <groupId>org.springframework.ai</groupId>
    <artifactId>spring-ai-openai-spring-boot-starter</artifactId>
</dependency>
```

```yaml
spring:
  application:
    name: ai-demo
  ai:
    openai:
      api-key: ${OPENAI_API_KEY}
      base-url: https://api.openai.com
      chat:
        options:
          model: gpt-4o
          temperature: 0.7
```

```java
@RestController
public class ChatController {
    
    @Autowired
    private ChatClient chatClient;
    
    @GetMapping("/chat")
    public String chat(@RequestParam String message) {
        return chatClient.prompt()
            .user(message)
            .call()
            .content();
    }
}
```

**Azure OpenAI集成：**

```yaml
spring:
  ai:
    azure:
      openai:
        endpoint: ${AZURE_OPENAI_ENDPOINT}
        api-key: ${AZURE_OPENAI_API_KEY}
        chat:
          deployment-name: gpt-4o
```

**Claude集成：**

```yaml
spring:
  ai:
    anthropic:
      api-key: ${ANTHROPIC_API_KEY}
      chat:
        options:
          model: claude-3-5-sonnet-20240620
          max-tokens: 1024
```

---

### Q3: ChatClient如何使用？有哪些高级特性？

**题目类型**：技术原理类

**问题描述**：Spring AI的ChatClient如何使用？有哪些高级配置？

**答案要点**：

**基本使用：**

```java
@RestController
public class ChatController {
    
    @Autowired
    private ChatClient chatClient;
    
    // 1. 简单对话
    @GetMapping("/chat")
    public String chat(@RequestParam String message) {
        return chatClient.prompt()
            .user(message)
            .call()
            .content();
    }
    
    // 2. 指定模型
    @GetMapping("/chat-gpt4")
    public String chatWithModel(@RequestParam String message) {
        return chatClient.prompt()
            .options(List.of(
                new OpenAiChatOptions.Builder()
                    .withModel("gpt-4-turbo")
                    .withTemperature(0.5)
                    .build()))
            .user(message)
            .call()
            .content();
    }
}
```

**系统提示词和上下文：**

```java
// 1. 系统提示词
public String chatWithSystem(String message) {
    return chatClient.prompt()
        .system("你是一个专业的Java程序员助手")
        .user(message)
        .call()
        .content();
}

// 2. 多轮对话
ChatResponse response = chatClient.prompt()
    .system("你是一个友好的助手")
    .user("我叫张三")
    .user("我叫什么呢？")
    .call();

String answer = response.getResult().getOutput().getContent();

// 3. 使用Prompt模板
PromptTemplate template = new PromptTemplate(
    "请用{language}语言实现一个{service}服务"
);

Map<String, Object> params = Map.of(
    "language", "Java",
    "service", "用户管理"
);

return chatClient.prompt(template.create(params))
    .call()
    .content();
```

**结构化输出：**

```java
// 1. 使用POJO接收
public record Movie(String title, int year, String director) {}

@GetMapping("/movie")
public Movie getMovie(@RequestParam String title) {
    return chatClient.prompt()
        .user("请给我查询" + title + "电影的信息，返回JSON格式")
        .call()
        .entity(Movie.class);
}

// 2. 使用@SystemMessage
public record Answer(
    @JsonProperty("code") int code,
    @JsonProperty("message") String message
) {}

@PostMapping("/analyze")
public Answer analyze(@RequestBody String text) {
    return chatClient.prompt()
        .system("你是一个分析助手")
        .user(text)
        .call()
        .entity(Answer.class);
}

// 3. 列表输出
public record Product(String name, double price) {}

@GetMapping("/products")
public List<Product> getProducts(@RequestParam String category) {
    PromptTemplate template = new PromptTemplate("""
        给我推荐5个{category}类的产品，返回JSON数组
        """);
    
    ParameterizedTypeReference<List<Product>> typeRef = 
        new ParameterizedTypeReference<>() {};
    
    return chatClient.prompt()
        .user(template.create(Map.of("category", category)))
        .call()
        .entity(typeRef);
}
```

---

### Q4: 什么是Function Calling？如何实现？

**题目类型**：技术原理类

**问题描述**：Spring AI的Function Calling是什么？如何实现自定义函数调用？

**答案要点**：

**Function Calling原理：**

```
┌─────────────────────────────────────────────────────────────┐
│                    Function Calling 流程                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. 定义函数                                                │
│     @Tool(name = "get_weather", description = "获取天气")  │
│     public String getWeather(@ToolParam("城市名称") String city) │
│                                                             │
│  2. LLM识别需要调用函数                                     │
│     user: "北京今天天气如何？"                              │
│     ↓                                                      │
│     LLM判断需要调用 get_weather("北京")                     │
│                                                             │
│  3. 执行函数并返回结果                                      │
│     getWeather("北京") → "晴，25°C"                       │
│                                                             │
│  4. LLM整合结果生成最终回答                                  │
│     "北京今天天气晴朗，温度25°C"                          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**实现方式：**

```java
// 1. 定义函数
@Component
public class WeatherTools {
    
    @Tool(name = "get_weather", 
          description = "获取指定城市的天气信息")
    public String getWeather(
            @ToolParam("城市名称") String city) {
        // 调用天气API
        return "天气晴朗，温度25°C";
    }
    
    @Tool(name = "get_weather_forecast",
          description = "获取未来几天的天气预报")
    public String getForecast(
            @ToolParam("城市名称") String city,
            @ToolParam(value = "天数", defaultValue = "7") int days) {
        return "未来" + days + "天的天气预报";
    }
}

// 2. 使用函数调用
@RestController
public class FunctionCallController {
    
    @Autowired
    private ChatClient chatClient;
    
    @Autowired
    private WeatherTools weatherTools;
    
    @GetMapping("/weather")
    public String weather(@RequestParam String city) {
        return chatClient.prompt()
            .user("北京今天天气怎么样？")
            .tools(weatherTools)  // 注入工具
            .call()
            .content();
    }
}

// 3. 显式函数调用
@GetMapping("/weather-explicit")
public String weatherExplicit(@RequestParam String city) {
    return chatClient.prompt()
        .user("查询天气: " + city)
        .tools(weatherTools)
        .toolOptions(ToolContext.builder()
            .toolName("get_weather")
            .toolArgument("city", city)
            .build())
        .call()
        .content();
}
```

**多函数选择：**

```java
// 函数注册
@Configuration
public class ToolConfig {
    
    @Bean
    public WeatherTools weatherTools() {
        return new WeatherTools();
    }
    
    @Bean
    public StockTools stockTools() {
        return new StockTools();
    }
}

// 在Service中使用
@Service
public class AiAssistantService {
    
    @Autowired
    private ChatClient chatClient;
    
    public String answer(String question) {
        return chatClient.prompt()
            .user(question)
            .tools("get_weather", "get_stock_price", "search_database")
            .call()
            .content();
    }
}
```

---

### Q5: 什么是ChatMemory？如何实现多轮对话？

**题目类型**：技术原理类

**问题描述**：Spring AI的ChatMemory是什么？如何实现多轮对话上下文？

**答案要点**：

**ChatMemory实现：**

```java
// 1. 使用InMemoryChatMemory
@Configuration
public class ChatConfig {
    
    @Bean
    public ChatMemory chatMemory() {
        return new InMemoryChatMemory();
    }
    
    @Bean
    public ChatClient chatClient(ChatMemory chatMemory) {
        return ChatClient.builder(new OpenAiChatModel())
            .defaultAdvisors(
                new MessageChatMemoryAdvisor(chatMemory))
            .build();
    }
}

// 2. 控制器使用
@RestController
public class ChatController {
    
    @Autowired
    private ChatClient chatClient;
    
    // 每次对话关联会话ID
    @GetMapping("/chat/{sessionId}")
    public String chat(@PathVariable String sessionId,
                       @RequestParam String message) {
        // 第二个参数是会话ID，用于区分不同用户对话
        return chatClient.prompt()
            .user(message)
            .advisors(a -> a
                .param("session_id", sessionId))
            .call()
            .content();
    }
}
```

**持久化ChatMemory：**

```java
// 使用JDBC存储对话
@Configuration
public class PersistentChatConfig {
    
    @Bean
    public ChatMemory chatMemory(JdbcTemplate jdbcTemplate) {
        // 自动创建表
        return new JdbcChatMemory(jdbcTemplate);
    }
}

// 自定义存储
@Component
public class RedisChatMemory implements ChatMemory {
    
    @Autowired
    private RedisTemplate<String, Message> redisTemplate;
    
    private static final String KEY_PREFIX = "chat:memory:";
    
    @Override
    public void add(String sessionId, List<Message> messages) {
        String key = KEY_PREFIX + sessionId;
        redisTemplate.opsForList().rightPushAll(key, messages);
    }
    
    @Override
    public List<Message> get(String sessionId, int lastN) {
        String key = KEY_PREFIX + sessionId;
        List<Message> messages = redisTemplate.opsForList()
            .range(key, -lastN, -1);
        return messages != null ? messages : Collections.emptyList();
    }
    
    @Override
    public void clear(String sessionId) {
        redisTemplate.delete(KEY_PREFIX + sessionId);
    }
}
```

---

### Q6: Spring AI如何实现结构化输出？

**题目要点**：技术原理类

**问题描述**：Spring AI如何实现结构化输出？有哪些方式？

**答案要点**：

**结构化输出方式：**

```java
// 1. 使用@JSONField注解
public record UserProfile(
    @JsonProperty("name") String name,
    @JsonProperty("age") int age,
    @JsonProperty("email") String email,
    @JsonProperty("skills") List<String> skills
) {}

@RestController
public class StructuredController {
    
    @Autowired
    private ChatClient chatClient;
    
    @GetMapping("/profile")
    public UserProfile getProfile(@RequestParam String description) {
        return chatClient.prompt()
            .user("分析以下简历，提取关键信息: " + description)
            .call()
            .entity(UserProfile.class);
    }
}

// 2. 使用PromptTemplate
public record ProductAnalysis(
    @JsonProperty("product_name") String productName,
    @JsonProperty("price") double price,
    @JsonProperty("rating") double rating,
    @JsonProperty("pros") List<String> pros,
    @JsonProperty("cons") List<String> cons
) {}

@GetMapping("/analyze")
public ProductAnalysis analyzeProduct(@RequestParam String product) {
    PromptTemplate template = new PromptTemplate("""
        请分析以下产品，返回结构化的JSON：
        {product}
        
        返回格式：
        {
          "product_name": "产品名称",
          "price": 价格,
          "rating": 评分,
          "pros": ["优点1", "优点2"],
          "cons": ["缺点1", "缺点2"]
        }
        """);
    
    return chatClient.prompt()
        .user(template.create(Map.of("product", product)))
        .call()
        .entity(ProductAnalysis.class);
}

// 3. 流式输出
@GetMapping(value = "/stream", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
public Flux<String> streamChat(@RequestParam String message) {
    return chatClient.prompt()
        .user(message)
        .stream()
        .content();
}
```

---

## 第二部分：RAG与向量数据库（共8题）

### Q7: 什么是RAG？如何用Spring AI实现？

**题目类型**：技术原理类

**问题描述**：什么是RAG？Spring AI如何实现RAG（检索增强生成）？

**答案要点**：

**RAG架构：**

```
┌─────────────────────────────────────────────────────────────┐
│                    RAG 检索增强生成                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                   索引阶段 (Indexing)                   │   │
│  │                                                     │   │
│  │  文档 ──▶ 切分 ──▶ Embedding ──▶ 向量存储          │   │
│  │             (Chunks)   (向量化)    (Vector DB)     │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                   检索阶段 (Retrieval)                │   │
│  │                                                     │   │
│  │  Query ──▶ Embedding ──▶ Top-K检索 ──▶ 上下文     │   │
│  │           (向量化)                   (相关文档)     │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                   生成阶段 (Generation)               │   │
│  │                                                     │   │
│  │  原始问题 + 检索上下文 ──▶ LLM ──▶ 答案          │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Spring AI RAG实现：**

```java
// 1. 依赖配置
@Dependency
<dependency>
    <groupId>org.springframework.ai</groupId>
    <artifactId>spring-ai-openai-spring-boot-starter</artifactId>
</dependency>
<dependency>
    <groupId>org.springframework.ai</groupId>
    <artifactId>spring-ai-pgvector-spring-boot-starter</artifactId>
</dependency>

// 2. 文档解析器配置
@Configuration
public class DocumentConfig {
    
    @Bean
    public DocumentReader pdfReader() {
        return new PagePdfDocumentReader("classpath:document.pdf");
    }
    
    @Bean
    public DocumentReader txtReader() {
        return new TextDocumentReader(new FileSystemResource("data/"));
    }
    
    @Bean
    public DocumentSplitter splitter() {
        return new TokenTextSplitter(500, 100, 5, true);
    }
}

// 3. VectorStore配置
@Configuration
public class VectorStoreConfig {
    
    @Bean
    public VectorStore vectorStore(JdbcTemplate jdbcTemplate, 
            EmbeddingModel embeddingModel) {
        return new PgVectorStore(jdbcTemplate, embeddingModel);
    }
}

// 4. 文档存储
@Service
public class DocumentService {
    
    @Autowired
    private VectorStore vectorStore;
    
    public void indexDocument(String content) {
        Document document = new Document(content);
        
        List<Document> documents = List.of(document);
        vectorStore.add(documents);
    }
    
    public void indexDocuments(List<String> contents) {
        List<Document> documents = contents.stream()
            .map(Document::new)
            .toList();
        
        vectorStore.add(documents);
    }
}

// 5. 检索并生成
@Service
public class RagService {
    
    @Autowired
    private VectorStore vectorStore;
    
    @Autowired
    private ChatClient chatClient;
    
    public String answer(String question) {
        // 1. 检索相关文档
        List<Document> documents = vectorStore.similaritySearch(
            SearchRequest.builder()
                .query(question)
                .topK(5)
                .build());
        
        // 2. 构建上下文
        String context = documents.stream()
            .map(Document::getContent)
            .collect(Collectors.joining("\n"));
        
        // 3. 构建Prompt
        PromptTemplate template = new PromptTemplate("""
            基于以下上下文回答问题：
            
            上下文：
            {context}
            
            问题：{question}
            
            如果上下文中没有相关信息，请如实告知。
            """);
        
        // 4. 生成回答
        return chatClient.prompt()
            .user(template.create(Map.of(
                "context", context,
                "question", question)))
            .call()
            .content();
    }
}
```

---

### Q8: Spring AI支持哪些向量数据库？

**题目类型**：基础概念类

**问题描述**：Spring AI支持哪些向量数据库？如何集成？

**答案要点**：

**支持的向量数据库：**

| 数据库 | 依赖 | 说明 |
|--------|------|------|
| PostgreSQL + PGVector | spring-ai-pgvector | 成熟稳定 |
| Milvus | spring-ai-milvus | 国产高性能 |
| Pinecone | spring-ai-pinecone | 云原生 |
| Weaviate | spring-ai-weaviate | 混合搜索 |
| Qdrant | spring-ai-qdrant | 高性能 |
| Redis | spring-ai-redis | 使用RedisVL |
| Chroma | spring-ai-chroma | 轻量级 |
| Neo4j | spring-ai-neo4j | 知识图谱 |

**PGVector集成：**

```yaml
# application.yml
spring:
  datasource:
    url: jdbc:postgresql://localhost:5432/vectordb
    username: postgres
    password: password
  ai:
    openai:
      api-key: ${OPENAI_API_KEY}
    vectorstore:
      pgvector:
        dimensions: 1536
        distance-type: COSINE_DISTANCE
```

```java
@Configuration
public class PgVectorConfig {
    
    @Bean
    public VectorStore vectorStore(JdbcTemplate jdbcTemplate,
            EmbeddingModel embeddingModel) {
        return PgVectorStore.builder(jdbcTemplate, embeddingModel)
            .dimensions(1536)
            .distanceType(DistanceType.COSINE_DISTANCE)
            .build();
    }
}
```

**Milvus集成：**

```yaml
spring:
  ai:
    milvus:
      url: http://localhost:19530
      collection-name: documents
```

```java
@Bean
public VectorStore vectorStore(EmbeddingModel embeddingModel) {
    return MilvusVectorStore.builder(embeddingModel)
        .host("localhost")
        .port(19530)
        .collectionName("documents")
        .build();
}
```

---

### Q9: 如何优化RAG的效果？

**题目类型**：场景解决类

**问题描述**：RAG应用中常见的问题有哪些？如何优化检索效果？

**答案要点**：

**RAG优化策略：**

```java
// 1. 文档切分优化
@Configuration
public class ChunkingConfig {
    
    // 太小丢失上下文，太大引入噪声
    @Bean
    public DocumentSplitter tokenSplitter() {
        // chunkSize: 每个chunk的token数
        // chunkOverlap: 相邻chunk重叠的token数
        // minChunkSizeChars: 最小字符数
        return new TokenTextSplitter(
            500,    // chunkSize
            100,    // chunkOverlap  
            5,      // minChunkSizeChars
            true    // keepSeparator
        );
    }
    
    // 按段落切分
    @Bean
    public DocumentSplitter paragraphSplitter() {
        return new ParagraphDocumentSplitter(2, 4);
    }
}

// 2. 混合检索
@Service
public class HybridRagService {
    
    @Autowired
    private VectorStore vectorStore;
    
    @Autowired
    private JdbcTemplate jdbcTemplate;
    
    public String hybridSearch(String query, int topK) {
        // 向量检索
        List<Document> vectorResults = vectorStore.similaritySearch(
            SearchRequest.builder()
                .query(query)
                .topK(topK)
                .build());
        
        // 关键词检索
        List<Document> keywordResults = keywordSearch(query);
        
        // RRF融合
        List<Document> fusedResults = rrfFusion(
            vectorResults, keywordResults, topK);
        
        // 构建上下文
        return buildContext(fusedResults);
    }
    
    // RRF (Reciprocal Rank Fusion) 算法
    private List<Document> rrfFusion(
            List<Document> vectorResults,
            List<Document> keywordResults,
            int k) {
        Map<String, Double> scores = new HashMap<>();
        
        // 向量检索得分
        for (int i = 0; i < vectorResults.size(); i++) {
            String id = vectorResults.get(i).getId();
            scores.merge(id, 1.0 / (60 + i), Double::sum);
        }
        
        // 关键词检索得分
        for (int i = 0; i < keywordResults.size(); i++) {
            String id = keywordResults.get(i).getId();
            scores.merge(id, 1.0 / (60 + i), Double::sum);
        }
        
        // 按得分排序
        return scores.entrySet().stream()
            .sorted((a, b) -> b.getValue().compareTo(a.getValue()))
            .limit(k)
            .map(e -> findById(e.getKey()))
            .toList();
    }
}

// 3. Query改写
@Service
public class QueryRewriteService {
    
    @Autowired
    private ChatClient chatClient;
    
    public String rewriteQuery(String query) {
        PromptTemplate template = new PromptTemplate("""
            你是一个搜索优化专家。请将以下问题改写得更清晰、更适合检索。
            
            原始问题：{query}
            
            改写要求：
            1. 提取关键实体和概念
            2. 补充可能遗漏的相关术语
            3. 去除口语化表达
            4. 返回改写后的问题
            """);
        
        return chatClient.prompt()
            .user(template.create(Map.of("query", query)))
            .call()
            .content();
    }
}
```

---

### Q10: 如何实现多模态AI（图片理解）？

**题目类型**：技术原理类

**问题描述**：Spring AI如何实现图片理解和多模态AI？

**答案要点**：

**多模态支持：**

```java
// 1. GPT-4V 图片理解
@RestController
public class VisionController {
    
    @Autowired
    private ChatClient chatClient;
    
    @GetMapping("/describe-image")
    public String describeImage(
            @RequestParam String imageUrl) {
        PromptTemplate template = new PromptTemplate("""
            请描述这张图片的内容：
            {image}
            """);
        
        Image image = Image.of(imageUrl);
        
        return chatClient.prompt()
            .user(u -> u
                .text(template.render())
                .media(MimeTypeUtils.IMAGE_PNG, image))
            .call()
            .content();
    }
    
    @PostMapping("/analyze-receipt")
    public ReceiptData analyzeReceipt(
            @RequestParam("file") MultipartFile file) throws IOException {
        PromptTemplate template = new PromptTemplate("""
            从以下发票图片中提取信息，返回JSON格式：
            {
              "merchant": "商家名称",
              "date": "日期",
              "total": "总金额",
              "items": ["商品1", "商品2"]
            }
            """);
        
        Image image = Image.of(
            MimeType.IMAGE_PNG, 
            file.getBytes());
        
        return chatClient.prompt()
            .user(u -> u
                .text(template.render())
                .media(MimeTypeUtils.IMAGE_PNG, image))
            .call()
            .entity(ReceiptData.class);
    }
}

// 2. 本地图片处理
@GetMapping("/describe-local-image")
public String describeLocalImage(
        @RequestParam String filePath) throws IOException {
    
    byte[] imageBytes = Files.readAllBytes(Paths.get(filePath));
    
    return chatClient.prompt()
        .user(u -> u
            .text("请描述这张图片")
            .media(MimeTypeUtils.IMAGE_PNG, 
                new ByteArrayResource(imageBytes)))
        .call()
        .content();
}
```

**图像生成：**

```java
@RestController
public class ImageController {
    
    @Autowired
    private ImageClient imageClient;
    
    @GetMapping("/generate-image")
    public String generateImage(@RequestParam String description) {
        ImageResponse response = imageClient.call(
            new ImagePrompt(description, 
                OpenAiImageOptions.builder()
                    .width(1024)
                    .height(1024)
                    .style(OpenAiImageOptions.ImageStyle.VIVID)
                    .quality(ImageOptions.ImageQuality.HD)
                    .build()));
        
        return response.getResult().getOutput().getUrl();
    }
    
    // Base64图片
    @GetMapping("/generate-base64")
    public String generateBase64(@RequestParam String description) {
        ImageResponse response = imageClient.call(
            new ImagePrompt(description));
        
        return response.getResult().getOutput().getB64Json();
    }
}
```

---

## 第三部分：实战应用（共4题）

### Q11: 如何用Spring AI实现知识库问答？

**题目类型**：场景解决类

**问题描述**：如何用Spring AI实现企业知识库问答系统？

**答案要点**：

**完整实现架构：**

```java
// 1. 文档处理服务
@Service
public class DocumentProcessingService {
    
    @Autowired
    private DocumentParser documentParser;
    
    @Autowired
    private EmbeddingModel embeddingModel;
    
    @Autowired
    private VectorStore vectorStore;
    
    public void processDocument(MultipartFile file) throws Exception {
        // 1. 解析文档
        List<Document> documents = documentParser.parse(file);
        
        // 2. 切分文档
        DocumentSplitter splitter = new TokenTextSplitter(500, 100, 5, true);
        List<Document> chunks = splitter.apply(documents);
        
        // 3. 添加元数据
        for (Document chunk : chunks) {
            chunk.getMetadata().put("filename", file.getOriginalFilename());
            chunk.getMetadata().put("uploadTime", LocalDateTime.now().toString());
        }
        
        // 4. 存储到向量数据库
        vectorStore.add(chunks);
    }
}

// 2. 问答服务
@Service
@Slf4j
public class QAService {
    
    @Autowired
    private VectorStore vectorStore;
    
    @Autowired
    private ChatClient chatClient;
    
    @Autowired
    private QueryRewriter queryRewriter;
    
    public QAResponse answer(String question, String userId) {
        long start = System.currentTimeMillis();
        
        // 1. Query改写
        String rewrittenQuery = queryRewriter.rewrite(question);
        log.info("Query改写: {} -> {}", question, rewrittenQuery);
        
        // 2. 相似度检索
        List<Document> documents = vectorStore.similaritySearch(
            SearchRequest.builder()
                .query(rewrittenQuery)
                .topK(5)
                .build());
        
        // 3. 构建上下文
        String context = buildContext(documents);
        
        // 4. 生成回答
        String answer = chatClient.prompt()
            .system("你是一个专业的知识库问答助手。请基于提供的上下文回答问题。"
                + "如果上下文中没有相关信息，请如实告知，不要编造答案。"
                + "回答要简洁、准确、引用来源。")
            .user("问题：" + question + "\n\n上下文：\n" + context)
            .call()
            .content();
        
        // 5. 记录日志
        long duration = System.currentTimeMillis() - start;
        log.info("问答完成，耗时: {}ms", duration);
        
        return new QAResponse(answer, documents, duration);
    }
    
    private String buildContext(List<Document> documents) {
        if (documents.isEmpty()) {
            return "未找到相关内容";
        }
        
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < documents.size(); i++) {
            Document doc = documents.get(i);
            sb.append(String.format("[%d] 来源：%s\n%s\n\n",
                i + 1,
                doc.getMetadata().get("filename"),
                doc.getContent()));
        }
        return sb.toString();
    }
}

// 3. API接口
@RestController
@RequestMapping("/api/qa")
public class QAController {
    
    @Autowired
    private QAService qaService;
    
    @PostMapping("/ask")
    public Result<QAResponse> ask(@RequestBody QARequest request) {
        QAResponse response = qaService.answer(
            request.getQuestion(), 
            request.getUserId());
        return Result.success(response);
    }
}
```

---

### Q12: 如何实现流式输出？

**题目类型**：场景解决类

**问题描述**：Spring AI如何实现流式输出（Streaming）？

**答案要点**：

**流式输出实现：**

```java
// 1. SSE流式响应
@RestController
@RequestMapping("/api/chat")
public class StreamController {
    
    @Autowired
    private ChatClient chatClient;
    
    @GetMapping(value = "/stream", 
                produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    public Flux<String> streamChat(@RequestParam String message) {
        return chatClient.prompt()
            .user(message)
            .stream()
            .content()
            .log();
    }
    
    // 完整SSE格式
    @GetMapping(value = "/stream-full", 
                produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    public Flux<ServerSentEvent<String>> streamFull(@RequestParam String message) {
        return chatClient.prompt()
            .user(message)
            .stream()
            .content()
            .map(content -> ServerSentEvent.<String>builder()
                .data(content)
                .build());
    }
}

// 2. 带Function Calling的流式
@GetMapping(value = "/stream-tools", 
            produces = MediaType.TEXT_EVENT_STREAM_VALUE)
public Flux<String> streamWithTools(@RequestParam String message) {
    return chatClient.prompt()
        .user(message)
        .tools(myTools)
        .stream()
        .content()
        .log();
}

// 3. 前端接收示例 (JavaScript)
async function streamChat() {
    const response = await fetch('/api/chat/stream?message=你好', {
        headers: { Accept: 'text/event-stream' }
    });
    
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    
    while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const chunk = decoder.decode(value);
        // 处理流式数据
        appendToChat(chunk);
    }
}
```

---

### Q13: Spring AI如何进行单元测试？

**题目类型**：场景解决类

**问题描述**：Spring AI应用如何进行单元测试和集成测试？

**答案要点**：

**测试配置：**

```java
// 1. Mock ChatClient
@ExtendWith(MockitoExtension.class)
class ChatServiceTest {
    
    @Mock
    private ChatClient chatClient;
    
    @InjectMocks
    private ChatService chatService;
    
    @Test
    void testChat() {
        when(chatClient.prompt())
            .thenReturn(new MockPromptSpec<>());
        // 或使用Answer
        when(chatClient.prompt(any()))
            .thenAnswer(invocation -> {
                MockPromptSpec spec = new MockPromptSpec<>();
                when(spec.call()).thenReturn(
                    new GenerativeAIResponseBuilder()
                        .text("测试回复")
                        .build());
                return spec;
            });
    }
}

// 2. 使用Testcontainers测试向量数据库
@Testcontainers
class VectorStoreIntegrationTest {
    
    @Container
    static PostgreSQLContainer<?> postgres = 
        new PostgreSQLContainer<>("pgvector/pgvector:v0.5.1");
    
    @DynamicPropertySource
    static void properties(DynamicPropertyRegistry registry) {
        registry.add("spring.datasource.url", postgres::getJdbcUrl);
        registry.add("spring.datasource.username", postgres::getUsername);
        registry.add("spring.datasource.password", postgres::getPassword);
    }
    
    @Autowired
    private VectorStore vectorStore;
    
    @Test
    void testVectorStore() {
        Document doc = new Document("测试内容");
        vectorStore.add(List.of(doc));
        
        List<Document> results = vectorStore.similaritySearch(
            SearchRequest.builder()
                .query("测试")
                .topK(1)
                .build());
        
        assertThat(results).hasSize(1);
    }
}

// 3. 集成测试
@SpringBootTest
@AutoConfigureMockAI
class RagServiceIntegrationTest {
    
    @Autowired
    private RagService ragService;
    
    @Autowired
    private DocumentService documentService;
    
    @Test
    void testRag() {
        // 准备数据
        documentService.indexDocument("Java是一种面向对象的编程语言");
        
        // 执行问答
        String answer = ragService.answer("什么是Java?");
        
        // 验证
        assertThat(answer).contains("Java");
    }
}
```

---

### Q14: Spring AI的安全最佳实践是什么？

**题目类型**：场景解决类

**问题描述**：使用Spring AI时有哪些安全注意事项？

**答案要点**：

**安全最佳实践：**

```java
// 1. API密钥安全
@Configuration
public class SecurityConfig {
    
    // 不要在代码中硬编码密钥
    // 使用环境变量或密钥管理服务
    @Bean
    public OpenAiApi openAiApi(
            @Value("${spring.ai.openai.api-key}") String apiKey) {
        return new OpenAiApi(apiKey);
    }
}

// 2. 输入验证
@Service
@Slf4j
public class SafeAIService {
    
    private static final int MAX_INPUT_LENGTH = 10000;
    private static final Pattern DANGEROUS_PATTERN = 
        Pattern.compile(".*(<script|.*javascript:).*", 
            Pattern.CASE_INSENSITIVE);
    
    public String safeChat(String input) {
        // 长度限制
        if (input.length() > MAX_INPUT_LENGTH) {
            throw new IllegalArgumentException("输入过长");
        }
        
        // XSS防护
        if (DANGEROUS_PATTERN.matcher(input).matches()) {
            throw new SecurityException("包含危险内容");
        }
        
        return chatClient.prompt()
            .user(input)
            .call()
            .content();
    }
}

// 3. 输出过滤
@Service
public class OutputFilterService {
    
    @Autowired
    private ChatClient chatClient;
    
    public String chatWithFilter(String input) {
        String rawOutput = chatClient.prompt()
            .user(input)
            .call()
            .content();
        
        // 输出过滤
        return sanitizeOutput(rawOutput);
    }
    
    private String sanitizeOutput(String output) {
        // 移除可能的注入内容
        return output
            .replaceAll("<script>", "")
            .replaceAll("</script>", "");
    }
}

// 4. 速率限制
@Configuration
public class RateLimitConfig {
    
    @Bean
    public FilterRegistrationBean<RateLimitFilter> rateLimitFilter() {
        FilterRegistrationBean<RateLimitFilter> registration = 
            new FilterRegistrationBean<>();
        registration.setFilter(new RateLimitFilter());
        registration.addUrlPatterns("/api/*");
        registration.setName("rateLimitFilter");
        return registration;
    }
}

// 5. 审计日志
@Component
public class AIUsageAudit {
    
    @Async
    public void logUsage(String userId, String input, 
            String output, long duration) {
        log.info("AI调用审计 - 用户: {}, 输入长度: {}, "
            + "输出长度: {}, 耗时: {}ms",
            userId, input.length(), output.length(), duration);
    }
}
```

---

## 附录：知识点总结

**Spring AI核心知识点：**

| 类别 | 关键知识点 |
|------|----------|
| 基础 | ChatClient、PromptTemplate、Function Calling、ChatMemory |
| RAG | 文档切分、向量存储、混合检索、Query改写 |
| 多模态 | 图像理解、图像生成 |
| 集成 | OpenAI、Azure、Cohere、多向量数据库 |
| 实战 | 流式输出、测试、安全 |

---

*本文档共计14道Spring AI面试题。*
