# sentence-transformers 面试题集

> 本文档包含 30 道 sentence-transformers 和 Embedding 模型相关的高频面试题，涵盖模型原理、文本向量化、相似度计算等核心概念。所有答案均为中文，代码附有详细中文解释。

---

## 目录

1. [Embedding 基础](#1-embedding-基础)
2. [模型使用](#2-模型使用)
3. [性能优化](#3-性能优化)
4. [中文优化](#4-中文优化)
5. [项目实践](#5-项目实践)

---

## 1. Embedding 基础

### Q1: 什么是文本 Embedding？它有什么用？

**参考答案：**

**Embedding 定义：**
Embedding（嵌入）是将文本、图像等非结构化数据转换为固定维度数值向量的技术，使语义相似的内容在向量空间中距离相近。

**核心作用：**

| 作用 | 说明 | 应用场景 |
|------|------|----------|
| **语义表示** | 将文本转为稠密向量 | 语义搜索 |
| **相似度计算** | 计算向量间的距离 | 推荐系统 |
| **聚类分析** | 将相似内容聚在一起 | 内容分类 |
| **语义运算** | 向量加减实现语义运算 | 类比推理 |

**向量空间示意：**

```
                    技术相关
                       ↑
                       |
        [Python]   [Java]   [Go]
           \        |        /
            \       |       /
             \      |      /
              \     |     /
    艺术相关 ←————————+————————→ 商业相关
              /     |     \
             /      |      \
            /       |       \
       [绘画]    [音乐]    [营销]
                       |
                       ↓
                    创意相关

语义相近的内容聚集在一起
```

**项目中的应用：**

```python
from sentence_transformers import SentenceTransformer

# 加载模型
model = SentenceTransformer("all-MiniLM-L6-v2")

# 文本向量化
text1 = "Python 是一种编程语言"
text2 = "Java 是一种编程语言"
text3 = "画画是一种艺术"

vec1 = model.encode(text1)  # [0.123, -0.456, ...]
vec2 = model.encode(text2)  # [0.125, -0.450, ...]
vec3 = model.encode(text3)  # [-0.789, 0.123, ...]

# 计算相似度
from sklearn.metrics.pairwise import cosine_similarity
sim_12 = cosine_similarity([vec1], [vec2])  # 高相似（都是编程语言）
sim_13 = cosine_similarity([vec1], [vec3])  # 低相似（不同领域）
```

---

### Q2: Embedding 模型是如何工作的？

**参考答案：**

**Transformer 架构原理：**

```
输入文本: "Python 编程"
    │
    ▼
┌─────────────────────────────┐
│        Tokenization          │
│  ["[CLS]", "Python", "编", "程", "[SEP]"]  │
└─────────────────────────────┘
    │
    ▼
┌─────────────────────────────┐
│       Embedding Layer       │
│  将 token 转换为向量         │
└─────────────────────────────┘
    │
    ▼
┌─────────────────────────────┐
│    Transformer Encoder     │
│  ├── Self-Attention        │
│  ├── Feed Forward          │
│  └── Layer Norm            │
└─────────────────────────────┘
    │
    ▼
┌─────────────────────────────┐
│        Pooling             │
│  Mean Pooling / [CLS]      │
└─────────────────────────────┘
    │
    ▼
向量: [0.123, -0.456, 0.789, ...]
```

**自注意力机制（Self-Attention）：**

```python
def self_attention(query, key, value):
    """
    自注意力计算
    Q（查询）、K（键）、V（值）来自同一输入
    """
    # 计算注意力分数
    scores = torch.matmul(query, key.transpose(-2, -1))
    scores = scores / (key.size(-1) ** 0.5)  # 缩放
    
    # Softmax 归一化
    attention_weights = F.softmax(scores, dim=-1)
    
    # 加权求和
    output = torch.matmul(attention_weights, value)
    
    return output
```

**常用 Pooling 策略：**

```python
# 1. Mean Pooling：所有 token 向量的平均值
def mean_pooling(token_embeddings, attention_mask):
    input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
    sum_embeddings = torch.sum(token_embeddings * input_mask_expanded, 1)
    sum_mask = torch.clamp(input_mask_expanded.sum(1), min=1e-9)
    return sum_embeddings / sum_mask

# 2. [CLS] Pooling：使用特殊 token [CLS] 的向量
cls_embedding = token_embeddings[:, 0, :]

# 3. Max Pooling：逐维度取最大值
max_embeddings = torch.max(token_embeddings, 1).values
```

---

### Q3: 常用的中文 Embedding 模型有哪些？

**参考答案：**

**开源中文 Embedding 模型：**

| 模型 | 维度 | 说明 | 适用场景 |
|------|------|------|----------|
| **text2vec-base-chinese** | 768 | 腾讯开源，中文优化 | 通用中文语义 |
| **moka-ai/m3e-base** | 768 | Moka 团队开源 | 中文语义相似度 |
| **BAAI/bge-large-zh-v1.5** | 1024 | BAAI 开源 | 高精度中文 |
| **shibing624/text2vec-base-chinese** | 768 | 效果好 | 中文匹配 |
| **paraphrase-multilingual-MiniLM** | 384 | 多语言支持 | 多语言场景 |

**英文 Embedding 模型：**

| 模型 | 维度 | 说明 |
|------|------|------|
| **all-MiniLM-L6-v2** | 384 | 轻量快速，效果好 |
| **all-mpnet-base-v2** | 768 | 高精度，速度慢 |
| **sentence-transformers/all-MiniLM-L12-v2** | 384 | 12层，平衡 |

**项目选型：**

```python
# 项目使用的模型
model_name = "sentence-transformers/all-MiniLM-L6-v2"
# 输出 384 维向量
# 优势：轻量（80MB），速度快，CPU 友好

# 中文场景推荐（需安装中文模型）
# model_name = "shibing624/text2vec-base-chinese"
# model_name = "BAAI/bge-large-zh-v1.5"  # 更高精度
```

---

### Q4: 什么是向量归一化？为什么需要归一化？

**参考答案：**

**归一化概念：**
向量归一化是将向量的长度（L2 范数）转换为 1 的过程。

```python
import numpy as np

def normalize(vector):
    """L2 归一化"""
    norm = np.linalg.norm(vector)
    if norm == 0:
        return vector
    return vector / norm

# 示例
vec = np.array([3.0, 4.0])  # 长度 = 5
vec_norm = normalize(vec)  # 长度 = 1
```

**为什么需要归一化：**

| 原因 | 说明 |
|------|------|
| **统一度量** | 不同向量的长度不影响相似度计算 |
| **内积等价余弦** | 归一化后内积 = 余弦相似度 |
| **数值稳定** | 避免大数值计算溢出 |
| **距离可比** | 欧氏距离有明确含义 |

**归一化前后对比：**

```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")

# 不归一化
vec1 = model.encode("Python")
vec2 = model.encode("Java")
print(f"不归一化 - 内积: {np.dot(vec1, vec2)}")  # 依赖向量长度

# 归一化
vec1_norm = model.encode("Python", normalize_embeddings=True)
vec2_norm = model.encode("Java", normalize_embeddings=True)
print(f"归一化 - 内积: {np.dot(vec1_norm, vec2_norm)}")  # = 余弦相似度
print(f"归一化 - L2距离: {np.linalg.norm(vec1_norm - vec2_norm)}")  # 有界
```

---

### Q5: 如何计算两个文本的相似度？

**参考答案：**

**常用相似度计算方法：**

```python
import numpy as np

def cosine_similarity(vec1, vec2):
    """余弦相似度"""
    dot = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    return dot / (norm1 * norm2)

def euclidean_distance(vec1, vec2):
    """欧氏距离"""
    return np.linalg.norm(vec1 - vec2)

def manhattan_distance(vec1, vec2):
    """曼哈顿距离"""
    return np.sum(np.abs(vec1 - vec2))

def dot_product(vec1, vec2):
    """点积（归一化后等价于余弦相似度）"""
    return np.dot(vec1, vec2)
```

**完整示例：**

```python
from sentence_transformers import SentenceTransformer
import numpy as np

model = SentenceTransformer("all-MiniLM-L6-v2")

# 待比较的文本
text1 = "机器学习是人工智能的一个分支"
text2 = "深度学习是机器学习的一个分支"
text3 = "今天天气很好"

# 向量化
vec1 = model.encode(text1, normalize_embeddings=True)
vec2 = model.encode(text2, normalize_embeddings=True)
vec3 = model.encode(text3, normalize_embeddings=True)

# 计算相似度
sim_12 = np.dot(vec1, vec2)  # 0.85 - 高相似
sim_13 = np.dot(vec1, vec3)  # 0.23 - 低相似
sim_23 = np.dot(vec2, vec3)  # 0.21 - 低相似

print(f"文本1 vs 文本2: {sim_12:.4f}")  # 都关于机器学习
print(f"文本1 vs 文本3: {sim_13:.4f}")  # 不同领域
print(f"文本2 vs 文本3: {sim_23:.4f}")  # 不同领域
```

**项目中的应用：**

```python
# rag-qa-system/app/core/vectorstore.py

def calculate_similarity(vec1: list, vec2: list) -> float:
    """计算向量相似度（内积）"""
    return np.dot(vec1, vec2)

# 检索时过滤低相似度结果
if similarity < runtime_config.similarity_threshold:
    continue  # 跳过
```

---

## 2. 模型使用

### Q6: 如何使用 sentence-transformers 进行文本向量化？

**参考答案：**

**基础使用：**

```python
from sentence_transformers import SentenceTransformer

# 1. 加载模型
model = SentenceTransformer("all-MiniLM-L6-v2")

# 2. 单条向量化
embedding = model.encode("要转换的文本")
print(f"向量维度: {len(embedding)}")  # 384

# 3. 批量向量化
texts = ["文本1", "文本2", "文本3"]
embeddings = model.encode(texts)
print(f"输出形状: {embeddings.shape}")  # (3, 384)

# 4. 归一化
embedding = model.encode("文本", normalize_embeddings=True)
```

**高级配置：**

```python
# 配置参数
embeddings = model.encode(
    texts,
    batch_size=32,           # 批处理大小
    show_progress_bar=True,   # 显示进度条
    convert_to_numpy=True,    # 转为 numpy 数组
    normalize_embeddings=True, # 归一化
    device="cuda"            # 使用 GPU（可选）
)
```

**项目中的封装：**

```python
# rag-qa-system/app/services/embedding_service.py

class EmbeddingService:
    """Embedding 服务封装"""
    
    _instance = None
    _model = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def _initialize(self):
        """初始化模型"""
        self._model = SentenceTransformer(
            model_name_or_path=settings.embedding_model,
            device=settings.embedding_device,
        )
    
    def encode(self, texts: str | list[str], **kwargs):
        """向量化"""
        if isinstance(texts, str):
            texts = [texts]
        
        # 清理特殊字符
        cleaned = [t.replace('\x00', '') for t in texts]
        
        return self._model.encode(
            cleaned,
            batch_size=settings.embedding_batch_size,
            show_progress_bar=False,
            normalize_embeddings=True,
            **kwargs
        )
    
    def encode_single(self, text: str) -> list[float]:
        """单条向量化"""
        return self.encode(text)[0].tolist()
    
    def encode_batch(self, texts: list[str]) -> list[list[float]]:
        """批量向量化"""
        return self.encode(texts).tolist()
```

---

### Q7: 如何选择合适的 Embedding 模型？

**参考答案：**

**选择维度：**

| 维度 | 考虑因素 |
|------|----------|
| **精度** | 任务对准确度的要求 |
| **速度** | 推理延迟要求 |
| **资源** | 内存/GPU 限制 |
| **语言** | 中文/英文/多语言 |

**模型选择指南：**

```python
# 场景1：追求速度，资源有限
model = "all-MiniLM-L6-v2"  # 384维，80MB，CPU 友好

# 场景2：追求精度
model = "BAAI/bge-large-zh-v1.5"  # 1024维，高精度

# 场景3：中文场景
model = "shibing624/text2vec-base-chinese"  # 中文优化

# 场景4：多语言
model = "paraphrase-multilingual-MiniLM-L12-v2"  # 支持100+语言
```

**模型对比：**

```python
from sentence_transformers import SentenceTransformer
from sentence_transformers.cross_encoder import CrossEncoder
import numpy as np

# 测试不同模型
models = {
    "MiniLM": "all-MiniLM-L6-v2",
    "MPNet": "all-mpnet-base-v2",
    "Chinese": "shibing624/text2vec-base-chinese",
}

test_pairs = [
    ("苹果是一种水果", "香蕉也是一种水果"),
    ("机器学习很重要", "深度学习是机器学习的一部分"),
]

for name, model_name in models.items():
    model = SentenceTransformer(model_name)
    
    print(f"\n=== {name} ===")
    for text1, text2 in test_pairs:
        vec1 = model.encode(text1)
        vec2 = model.encode(text2)
        sim = np.dot(vec1, vec2)
        print(f"  相似度: {sim:.4f}")
```

---

### Q8: 什么是句子 Embedding 和词 Embedding？

**参考答案：**

**词 Embedding（Word Embedding）：**

```python
# 词级别向量
from transformers import AutoTokenizer, AutoModel

tokenizer = AutoTokenizer.from_pretrained("bert-base-chinese")
model = AutoModel.from_pretrained("bert-base-chinese")

# 分词
tokens = tokenizer("机器学习", return_tensors="pt")
outputs = model(**tokens)

# 获取词向量
word_embeddings = outputs.last_hidden_state  # [batch, seq_len, hidden]
print(f"词向量形状: {word_embeddings.shape}")  # [1, 4, 768]
```

**句子 Embedding（Sentence Embedding）：**

```python
# 句子级别向量
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")

# 直接获取句子向量
sentence_embedding = model.encode("机器学习")
print(f"句子向量形状: {sentence_embedding.shape}")  # [384]
```

**区别对比：**

| 特性 | 词 Embedding | 句子 Embedding |
|------|-------------|---------------|
| 粒度 | 单个词 | 整句 |
| 输出 | 多维向量序列 | 单个向量 |
| 聚合 | 需 pooling | 直接输出 |
| 用途 | 词级任务 | 句子级任务 |

**句子 Embedding 的优势：**

```python
# 1. 直接计算句子相似度
vec1 = model.encode("Python 编程语言")
vec2 = model.encode("Java 编程语言")
similarity = np.dot(vec1, vec2)

# 2. 无需分词处理
# 词向量需要先分词，再聚合

# 3. 保留语义顺序
# 句子向量通过 Self-Attention 保留语序信息
```

---

### Q9: 什么是多语言 Embedding 模型？

**参考答案：**

**多语言模型原理：**

```python
# 支持多种语言的模型
model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")

# 中文文本
zh_embedding = model.encode("你好世界")

# 英文文本
en_embedding = model.encode("Hello World")

# 日文文本
ja_embedding = model.encode("こんにちは世界")

# 相似度计算（跨语言）
sim = np.dot(zh_embedding, en_embedding)  # 可能较高（语义相似）
```

**常用多语言模型：**

| 模型 | 支持语言 | 维度 | 说明 |
|------|----------|------|------|
| paraphrase-multilingual-MiniLM-L12-v2 | 50+ | 384 | 小型多语言 |
| multilingual-e5-large | 100+ | 1024 | 高精度多语言 |
| sentence-transformers/LaBSE | 100+ | 768 | Google 开源 |
| mbert-base-multilingual-cased | 100+ | 768 | BERT 多语言版 |

**跨语言检索示例：**

```python
# 建立多语言知识库
documents = {
    "zh": ["机器学习是人工智能的分支", "深度学习是机器学习的分支"],
    "en": ["Machine learning is a branch of AI", "Deep learning is a branch of ML"]
}

# 编码所有文档
all_docs = list(documents.values())
doc_embeddings = model.encode(all_docs)

# 用中文查询英文文档
query = "什么是深度学习"
query_embedding = model.encode(query)

# 检索
similarities = np.dot(query_embedding, doc_embeddings)
top_idx = np.argmax(similarities)
print(f"最相关文档: {all_docs[top_idx]}")
```

---

### Q10: Embedding 模型如何处理中文？

**参考答案：**

**中文处理流程：**

```python
# 中文模型 vs 英文模型
from sentence_transformers import SentenceTransformer

# 英文模型处理中文（效果差）
en_model = SentenceTransformer("all-MiniLM-L6-v2")
zh_text = "这是一个中文句子"
en_vec = en_model.encode(zh_text)  # 基于字符分词，效果差

# 中文专用模型
zh_model = SentenceTransformer("shibing624/text2vec-base-chinese")
zh_vec = zh_model.encode(zh_text)  # 基于词分词，效果好
```

**中文分词 vs 字符级：**

```python
# 字符级（BERT 默认）
# "机器学习" → ["机", "器", "学", "习"]

# 词级（中文模型）
# "机器学习" → ["机器", "学习"]

# 示例对比
print("=== 字符级 ===")
tokens = tokenizer.tokenize("机器学习")
print(tokens)  # ['机', '器', '学', '习']

print("\n=== 词级 ===")
# 使用 jieba 分词
import jieba
tokens = list(jieba.cut("机器学习"))
print(tokens)  # ['机器', '学习']
```

**中文语义理解：**

```python
# 中文模型能理解中文语义
model = SentenceTransformer("shibing624/text2vec-base-chinese")

pairs = [
    ("今天天气很好", "今天阳光明媚"),      # 相似
    ("今天天气很好", "今天下雨了"),        # 不相似
    ("苹果水果", "香蕉水果"),              # 相似
    ("苹果公司", "Apple Inc"),            # 相似（跨语言概念）
]

for text1, text2 in pairs:
    vec1 = model.encode(text1)
    vec2 = model.encode(text2)
    sim = np.dot(vec1, vec2)
    print(f"'{text1}' vs '{text2}': {sim:.4f}")
```

---

## 3. 性能优化

### Q11: 如何优化 Embedding 的推理速度？

**参考答案：**

**速度优化策略：**

| 策略 | 说明 | 加速比 |
|------|------|----------|
| 批量处理 | 一次处理多条 | 5-10x |
| GPU 加速 | 使用 CUDA | 10-50x |
| ONNX 导出 | 优化计算图 | 2-3x |
| 量化 | INT8 量化 | 2-4x |
| 缓存 | 重复文本复用 | 按场景 |

**批量处理：**

```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")

# 反例：逐条处理（慢）
embeddings = []
for text in texts:
    embeddings.append(model.encode(text))

# 正例：批量处理（快）
embeddings = model.encode(texts, batch_size=32)
```

**GPU 加速：**

```python
# 检查 GPU 是否可用
import torch
print(f"CUDA 可用: {torch.cuda.is_available()}")

# 使用 GPU
device = "cuda" if torch.cuda.is_available() else "cpu"
model = SentenceTransformer("all-MiniLM-L6-v2", device=device)

# 推理时会自动使用 GPU
embedding = model.encode(texts)
```

**ONNX 优化：**

```python
# 导出为 ONNX 格式
model.save("model_path")
model = SentenceTransformer("model_path")

# 优化
from optimum.onnxruntime import ORTModel

ort_model = ORTModel.from_pretrained(
    "model_path",
    export=True
)

# 推理
embeddings = ort_model.encode(texts)
```

**项目中的优化：**

```python
# rag-qa-system/app/config.py

class Settings(BaseSettings):
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_device: str = "cpu"  # GPU: "cuda"
    embedding_batch_size: int = 32
    embedding_dimension: int = 384
```

---

### Q12: 如何处理长文本的 Embedding？

**参考答案：**

**长文本处理策略：**

```python
# 策略1：截断
embedding = model.encode(long_text, truncation=True, max_length=512)

# 策略2：滑动窗口
def chunk_and_encode(text, chunk_size=512, overlap=50):
    """滑动窗口切分"""
    chunks = []
    for i in range(0, len(text), chunk_size - overlap):
        chunk = text[i:i + chunk_size]
        if len(chunk) >= 50:  # 最小长度过滤
            chunks.append(chunk)
    
    # 编码所有块
    embeddings = model.encode(chunks)
    
    # 合并（平均池化）
    return np.mean(embeddings, axis=0)

# 策略3：摘要 + 编码
def summarize_and_encode(text, max_length=512):
    """先摘要再编码"""
    summary = summarize_text(text, max_length)
    return model.encode(summary)
```

**语义分块策略：**

```python
# 按语义切分长文本
def semantic_chunk(text, max_tokens=500):
    """语义分块"""
    # 1. 按段落分割
    paragraphs = text.split("\n\n")
    
    # 2. 按 token 数合并
    chunks = []
    current_chunk = []
    current_tokens = 0
    
    for para in paragraphs:
        para_tokens = len(para) // 2  # 估算
        if current_tokens + para_tokens <= max_tokens:
            current_chunk.append(para)
            current_tokens += para_tokens
        else:
            if current_chunk:
                chunks.append("\n\n".join(current_chunk))
            current_chunk = [para]
            current_tokens = para_tokens
    
    if current_chunk:
        chunks.append("\n\n".join(current_chunk))
    
    return chunks

# 对每个块编码
chunks = semantic_chunk(long_text)
embeddings = model.encode(chunks)
```

---

### Q13: 如何缓存 Embedding 结果？

**参考答案：**

**缓存策略：**

```python
import hashlib
import redis

class EmbeddingCache:
    """Embedding 缓存"""
    
    def __init__(self, redis_client):
        self.redis = redis_client
        self.prefix = "embedding:"
    
    def get_cache_key(self, text: str) -> str:
        """生成缓存键"""
        return f"{self.prefix}{hashlib.md5(text.encode()).hexdigest()}"
    
    def get(self, text: str):
        """获取缓存"""
        key = self.get_cache_key(text)
        cached = self.redis.get(key)
        return json.loads(cached) if cached else None
    
    def set(self, text: str, embedding: list):
        """设置缓存"""
        key = self.get_cache_key(text)
        self.redis.setex(key, 86400, json.dumps(embedding))
    
    def get_or_encode(self, text: str, model) -> list:
        """获取或编码"""
        cached = self.get(text)
        if cached:
            return cached
        
        embedding = model.encode(text).tolist()
        self.set(text, embedding)
        return embedding
```

**批量缓存：**

```python
def batch_encode_with_cache(texts: list[str], model, cache: EmbeddingCache):
    """批量编码（带缓存）"""
    results = []
    uncached_texts = []
    uncached_indices = []
    
    # 1. 检查缓存
    for i, text in enumerate(texts):
        cached = cache.get(text)
        if cached:
            results.append(cached)
        else:
            results.append(None)
            uncached_texts.append(text)
            uncached_indices.append(i)
    
    # 2. 批量编码未缓存的
    if uncached_texts:
        embeddings = model.encode(uncached_texts)
        embeddings_list = embeddings.tolist()
        
        # 3. 更新缓存和结果
        for i, (text, embedding) in enumerate(zip(uncached_texts, embeddings_list)):
            idx = uncached_indices[i]
            results[idx] = embedding
            cache.set(text, embedding)
    
    return results
```

---

### Q14: 如何评估 Embedding 模型的效果？

**参考答案：**

**评估指标：**

| 指标 | 说明 | 计算方法 |
|------|------|----------|
| **余弦相似度** | 语义相似度 | cos(vec1, vec2) |
| **欧氏距离** | 向量距离 | L2(vec1, vec2) |
| **Spearman 相关系数** | 排序相关性 | 排序相关性 |
| **准确率@K** | Top-K 准确率 | P@K |

**STS 任务评估：**

```python
from sentence_transformers import SentenceTransformer, evaluation
from datasets import load_dataset

# 加载评估数据集
dataset = load_dataset("sentence-transformers/stsb", split="validation")

evaluator = evaluation.SemanticTextualSimilarityEvaluator(
    sentences1=dataset["sentence1"],
    sentences2=dataset["sentence2"],
    scores=dataset["score"]  # 人工标注的相似度分数
)

# 评估模型
model = SentenceTransformer("all-MiniLM-L6-v2")
metrics = evaluator(model)
print(f"Spearman 相关性: {metrics}")
```

**自定义评估：**

```python
def evaluate_on_custom_data(model, test_pairs: list[tuple]):
    """自定义评估"""
    correct = 0
    total = len(test_pairs)
    
    for text1, text2, expected_sim in test_pairs:
        vec1 = model.encode(text1)
        vec2 = model.encode(text2)
        actual_sim = np.dot(vec1, vec2)
        
        # 判断正确（阈值判断）
        predicted = "similar" if actual_sim > 0.7 else "dissimilar"
        expected = "similar" if expected_sim else "dissimilar"
        
        if predicted == expected:
            correct += 1
    
    accuracy = correct / total
    print(f"准确率: {accuracy:.2%}")

# 测试用例
test_pairs = [
    ("Python 编程", "Java 编程", True),
    ("苹果水果", "香蕉水果", True),
    ("编程语言", "天气", False),
    ("机器学习", "深度学习", True),
]

evaluate_on_custom_data(model, test_pairs)
```

---

### Q15: Embedding 模型如何进行微调？

**参考答案：**

**微调场景：**

| 场景 | 说明 | 数据量 |
|------|------|--------|
| 领域适配 | 适配特定领域 | 1000+ |
| 任务优化 | 针对特定任务 | 500+ |
| 风格迁移 | 调整输出风格 | 1000+ |

**微调代码：**

```python
from sentence_transformers import SentenceTransformer, InputExample, losses
from torch.utils.data import DataLoader

# 1. 准备数据
train_examples = [
    InputExample(texts=["查询1", "相关文档1"], label=1.0),
    InputExample(texts=["查询1", "不相关文档"], label=0.0),
    # ... 更多样本
]

# 2. 创建数据集
train_dataloader = DataLoader(train_examples, shuffle=True, batch_size=16)

# 3. 加载预训练模型
model = SentenceTransformer("all-MiniLM-L6-v2")

# 4. 定义损失函数
train_loss = losses.CosineSimilarityLoss(model)

# 5. 微调
model.fit(
    train_objectives=[(train_dataloader, train_loss)],
    epochs=4,
    warmup_steps=100,
    show_progress_bar=True
)

# 6. 保存
model.save("fine-tuned-model")
```

**对比微调前后：**

```python
# 微调前
original_model = SentenceTransformer("all-MiniLM-L6-v2")

# 微调后
finetuned_model = SentenceTransformer("fine-tuned-model")

# 测试
test_pairs = [
    ("退货政策是什么", "如何申请七天无理由退货"),
    ("退货政策是什么", "今天天气怎么样"),
]

for text1, text2 in test_pairs:
    # 原始模型
    vec1_orig = original_model.encode(text1)
    vec2_orig = original_model.encode(text2)
    sim_orig = np.dot(vec1_orig, vec2_orig)
    
    # 微调模型
    vec1_ft = finetuned_model.encode(text1)
    vec2_ft = finetuned_model.encode(text2)
    sim_ft = np.dot(vec1_ft, vec2_ft)
    
    print(f"'{text1}' vs '{text2}'")
    print(f"  原始: {sim_orig:.4f}, 微调后: {sim_ft:.4f}")
```

---

## 4. 中文优化

### Q16: 如何选择中文 Embedding 模型？

**参考答案：**

**中文模型选择指南：**

| 模型 | 维度 | 特点 | 推荐场景 |
|------|------|------|----------|
| **text2vec-base-chinese** | 768 | 效果好，开源 | 通用中文 |
| **m3e-base** | 768 | Moka 开源，稳定 | 生产环境 |
| **bge-large-zh-v1.5** | 1024 | BAAI 高精度 | 高精度需求 |
| **text2vec-large** | 1024 | 效果最好 | 精度优先 |

**性能对比：**

```python
models = {
    "MiniLM": "sentence-transformers/all-MiniLM-L6-v2",
    "text2vec": "shibing624/text2vec-base-chinese",
    "bge-zh": "BAAI/bge-large-zh-v1.5",
}

test_texts = [
    "人工智能技术的发展",
    "机器学习和深度学习的关系",
    "自然语言处理应用",
]

for name, model_name in models.items():
    model = SentenceTransformer(model_name)
    embeddings = model.encode(test_texts)
    
    # 计算内部相似度
    sim_matrix = np.dot(embeddings, embeddings.T)
    print(f"\n=== {name} ===")
    print(f"相似度矩阵形状: {sim_matrix.shape}")
```

---

### Q17: 如何处理中文歧义词？

**参考答案：**

**歧义示例：**

```python
# 词法歧义
# "苹果" 可以是水果或公司
# "苹果手机" 限定后歧义消除

# 句法歧义
# "咬死了猎人的老虎" 可以是主语或宾语

# 语义歧义
# "打酱油" 可以是字面意思或"不关我事"
```

**消歧策略：**

```python
# 策略1：上下文扩展
def disambiguate_with_context(target_word, context):
    """使用上下文消歧"""
    # 将目标词与上下文拼接
    expanded = f"{context}，特别是{target_word}"
    return model.encode(expanded)

# 示例
target = "苹果"
context1 = "这种水果很好吃"  # 消歧为水果
context2 = "最新款发布了"    # 消歧为公司

vec1 = disambiguate_with_context(target, context1)
vec2 = disambiguate_with_context(target, context2)

# vec1 和 vec2 现在有不同的语义
```

---

### Q18: 如何处理中英文混合文本？

**参考答案：**

**混合文本处理：**

```python
# 使用多语言模型
model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")

# 混合文本向量化
mixed_text = "Python 是最流行的编程语言，AI 是未来的发展方向"
embedding = model.encode(mixed_text)

# 中英对照向量化
texts = [
    "深度学习 Deep Learning",
    "自然语言处理 NLP",
    "计算机视觉 Computer Vision"
]
embeddings = model.encode(texts)
```

**语言识别后处理：**

```python
def encode_with_lang_detection(texts, zh_model, en_model):
    """根据语言选择模型"""
    results = []
    
    for text in texts:
        lang = detect_language(text)
        
        if lang == "zh":
            vec = zh_model.encode(text)
        else:
            vec = en_model.encode(text)
        
        results.append(vec)
    
    return np.array(results)
```

---

### Q19: 中文分词对 Embedding 的影响？

**参考答案：**

**分词方式对比：**

```python
import jieba

text = "自然语言处理是人工智能的重要分支"

# 方式1：字符级
char_tokens = list(text)
print(f"字符级: {char_tokens}")
# ['自', '然', '语', '言', ...]

# 方式2：词级
word_tokens = list(jieba.cut(text))
print(f"词级: {word_tokens}")
# ['自然语言', '处理', '是', '人工智能', '的', '重要', '分支']

# 方式3：BERT Tokenizer
from transformers import AutoTokenizer
tokenizer = AutoTokenizer.from_pretrained("bert-base-chinese")
bert_tokens = tokenizer.tokenize(text)
print(f"BERT: {bert_tokens}")
# ['自', '然', '语', '言', '处', '理', ...]
```

**对相似度的影响：**

```python
# 分词方式影响向量表示
def compare_segmentation(text1, text2, model):
    """对比不同分词方式的相似度"""
    
    # 字符级
    vec1_char = model.encode(list(text1))
    vec2_char = model.encode(list(text2))
    sim_char = np.dot(vec1_char, vec2_char)
    
    # 词级
    vec1_word = model.encode(list(jieba.cut(text1)))
    vec2_word = model.encode(list(jieba.cut(text2)))
    sim_word = np.dot(vec1_word, vec2_word)
    
    return sim_char, sim_word
```

---

### Q20: 如何优化中文检索效果？

**参考答案：**

**检索优化策略：**

```python
# 1. 同义词扩展
synonym_map = {
    "电脑": ["计算机", "PC"],
    "手机": ["移动电话", "智能手机"],
}

def expand_query(query):
    """查询扩展"""
    words = jieba.cut(query)
    expanded = []
    
    for word in words:
        expanded.append(word)
        if word in synonym_map:
            expanded.extend(synonym_map[word])
    
    return " ".join(expanded)

# 2. 同音字处理
# 适用于语音输入场景

# 3. 混合检索
def hybrid_search(query, vector_store, keyword_index):
    """混合向量和关键词检索"""
    # 向量检索
    vec = model.encode(query)
    vector_results = vector_store.search(vec, top_k=10)
    
    # 关键词检索
    keyword_results = keyword_index.search(query)
    
    # 结果融合（RRF 算法）
    fused = reciprocal_rank_fusion(
        [vector_results, keyword_results],
        k=60
    )
    
    return fused
```

**结果重排序：**

```python
def rerank_with_cross_encoder(query, candidates, cross_encoder):
    """使用 Cross-Encoder 重排序"""
    pairs = [(query, doc) for doc in candidates]
    scores = cross_encoder.predict(pairs)
    
    # 按分数排序
    ranked = sorted(zip(candidates, scores), key=lambda x: x[1], reverse=True)
    
    return ranked
```

---

## 5. 项目实践

### Q21: 项目中 Embedding 模块的设计？

**参考答案：**

**单例模式封装：**

```python
# rag-qa-system/app/services/embedding_service.py

from sentence_transformers import SentenceTransformer
from typing import List

class EmbeddingService:
    """Embedding 服务（单例模式）"""
    
    _instance = None
    _model = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if EmbeddingService._model is None:
            self._initialize()
    
    def _initialize(self):
        """初始化模型"""
        EmbeddingService._model = SentenceTransformer(
            model_name_or_path=settings.embedding_model,
            device=settings.embedding_device,
        )
        logger.info(f"Embedding 模型加载完成: {settings.embedding_model}")
    
    def encode(self, texts: str | List[str]) -> List[List[float]]:
        """批量向量化"""
        if isinstance(texts, str):
            texts = [texts]
        
        # 清理特殊字符
        cleaned = [t.replace('\x00', '') for t in texts]
        
        embeddings = EmbeddingService._model.encode(
            cleaned,
            batch_size=settings.embedding_batch_size,
            show_progress_bar=False,
            convert_to_numpy=True,
            normalize_embeddings=True,
        )
        
        return embeddings.tolist()
    
    def encode_single(self, text: str) -> List[float]:
        """单条向量化"""
        return self.encode(text)[0]
```

---

### Q22: 如何处理 Embedding 模型加载失败？

**参考答案：**

**错误处理：**

```python
class EmbeddingService:
    def _initialize(self):
        """安全的模型初始化"""
        try:
            EmbeddingService._model = SentenceTransformer(
                model_name_or_path=settings.embedding_model,
                device=settings.embedding_device,
            )
            
            # 验证模型
            test_text = "测试文本"
            test_vec = EmbeddingService._model.encode(test_text)
            
            if len(test_vec) != settings.embedding_dimension:
                raise ValueError(
                    f"模型维度不匹配: 期望 {settings.embedding_dimension}, "
                    f"实际 {len(test_vec)}"
                )
            
            logger.info(f"Embedding 模型加载成功")
        
        except Exception as e:
            logger.error(f"Embedding 模型加载失败: {e}")
            raise

def get_embedding_with_fallback(text: str) -> List[float]:
    """带降级的获取 Embedding"""
    try:
        return embedding_service.encode_single(text)
    except Exception as e:
        logger.warning(f"Embedding 失败，使用备用方案: {e}")
        # 返回零向量或抛出异常
        return [0.0] * settings.embedding_dimension
```

---

### Q23: Embedding 与 Milvus 如何配合？

**参考答案：**

**数据流程：**

```python
# 1. 文档向量化 → 存储到 Milvus
document = "RAG 是检索增强生成技术"
embedding = embedding_service.encode_single(document)

# 存储到向量数据库
milvus_client.insert_vectors(
    ids=["doc_001"],
    embeddings=[embedding],
    documents=[document],
    metadatas=[{"source": "knowledge_base"}]
)

# 2. 查询向量化 → Milvus 检索
query = "什么是 RAG"
query_embedding = embedding_service.encode_single(query)

# 向量检索
results = milvus_client.search_vectors(
    query_embedding=[query_embedding],
    n_results=5
)
```

**完整示例：**

```python
# rag-qa-system/app/core/vectorstore.py

class VectorStore:
    def __init__(self):
        self.embedding_service = get_embedding_service()
    
    def add_documents(self, documents: List[dict]):
        """添加文档到向量库"""
        texts = [doc["content"] for doc in documents]
        
        # 向量化
        embeddings = self.embedding_service.encode(texts)
        
        # 存储
        ids = [doc["id"] for doc in documents]
        metadatas = [doc.get("metadata", {}) for doc in documents]
        
        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas
        )
    
    def search(self, query: str, top_k: int = 5):
        """向量检索"""
        # 查询向量化
        query_embedding = self.embedding_service.encode_single(query)
        
        # Milvus 检索
        results = self.collection.search(
            data=[query_embedding],
            anns_field="embedding",
            param={"metric_type": "IP", "params": {"ef": 64}},
            limit=top_k
        )
        
        return results
```

---

### Q24: Embedding 的维度如何选择？

**参考答案：**

**维度与性能关系：**

| 维度 | 存储 | 计算 | 精度 | 适用场景 |
|------|------|------|------|----------|
| 384 | 小 | 快 | 中 | 通用、推荐 |
| 768 | 中 | 中 | 高 | 高精度 |
| 1024 | 大 | 慢 | 很高 | 科研、精密 |

**项目选择：**

```python
# 项目使用 all-MiniLM-L6-v2 (384维)
# 选择原因：
# 1. 速度快，CPU 友好
# 2. 存储开销小
# 3. 精度满足 RAG 场景需求
# 4. 模型小（80MB），易部署

EMBEDDING_DIMENSION = 384
```

**维度匹配：**

```python
# Milvus 集合维度必须与模型输出维度一致
milvus_collection = Collection(
    name="knowledge_base",
    schema=CollectionSchema(fields=[
        FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=384),
        # 必须是 384，与模型输出一致
    ])
)
```

---

### Q25: Embedding 模型如何更新和热加载？

**参考答案：**

**模型热更新：**

```python
class EmbeddingService:
    def reload_model(self, new_model_name: str = None):
        """重新加载模型"""
        global EmbeddingService._model
        
        model_name = new_model_name or settings.embedding_model
        
        logger.info(f"正在重新加载 Embedding 模型: {model_name}")
        
        # 加载新模型
        new_model = SentenceTransformer(model_name)
        
        # 替换旧模型
        EmbeddingService._model = new_model
        
        # 清理缓存
        if hasattr(self, '_embedding_cache'):
            self._embedding_cache.clear()
        
        logger.info(f"模型重新加载完成")
    
    def get_model_info(self) -> dict:
        """获取模型信息"""
        return {
            "model_name": settings.embedding_model,
            "dimension": settings.embedding_dimension,
            "device": settings.embedding_device,
        }
```

---

### Q26-30: 常见面试问题汇总

**Q26: Embedding 和 TF-IDF 的区别？**

```python
# TF-IDF: 稀疏向量，词频统计
# Embedding: 稠密向量，语义表示

# TF-IDF 示例
from sklearn.feature_extraction.text import TfidfVectorizer

vectorizer = TfidfVectorizer()
tfidf_matrix = vectorizer.fit_transform(texts)
# 稀疏矩阵，大部分为0

# Embedding 示例
embedding = model.encode(texts)
# 稠密向量，非零值
```

**Q27: 如何处理多模态 Embedding？**

```python
# 多模态模型（文本+图像）
from transformers import CLIPModel

model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")

# 文本 Embedding
text_inputs = clip_processor(text=["一只猫"], return_tensors="pt")
text_features = model.get_text_features(**text_inputs)

# 图像 Embedding
image_inputs = clip_processor(images=image, return_tensors="pt")
image_features = model.get_image_features(**image_inputs)

# 跨模态相似度
similarity = torch.cosine_similarity(text_features, image_features)
```

**Q28: Embedding 如何用于推荐系统？**

```python
# 用户和物品的 Embedding
user_embedding = model.encode(user_profile)
item_embeddings = model.encode(item_descriptions)

# 计算用户对物品的兴趣
interests = np.dot(user_embedding, item_embeddings.T)

# Top-K 推荐
top_k_items = np.argsort(interests)[-10:][::-1]
```

**Q29: Embedding 的维度灾难如何处理？**

```python
# 维度灾难：高维空间中数据稀疏，距离失效

# 解决方案1：PCA 降维
from sklearn.decomposition import PCA

pca = PCA(n_components=128)
reduced = pca.fit_transform(high_dim_embeddings)

# 解决方案2：使用合适的距离度量
# 高维适合用余弦相似度
similarity = np.dot(vec1, vec2) / (norm1 * norm2)

# 解决方案3：HNSW 等近似搜索
```

**Q30: 项目中 Embedding 的典型问题？**

```python
# 项目经验总结：

# 1. 模型选择
# - 中文场景用中文模型
# - 精度优先用 bge-large
# - 速度优先用 MiniLM

# 2. 缓存策略
# - 相同文本重复编码浪费
# - Redis 缓存节省计算

# 3. 维度匹配
# - Milvus 维度必须与模型一致
# - 维度不匹配会导致插入失败

# 4. 批量处理
# - 逐条编码效率低
# - batch_size=32 较优

# 5. 异常处理
# - 模型加载失败要有降级方案
# - 网络问题导致模型下载失败
```

---

## 附录：面试重点总结

### 核心知识点

| 类别 | 重点内容 |
|------|----------|
| **基础原理** | Transformer、自注意力、Pooling |
| **模型使用** | 加载、向量化、批量处理 |
| **性能优化** | 批量、GPU、缓存、量化 |
| **中文处理** | 分词、歧义、多语言 |
| **项目实践** | 单例、缓存、异常处理 |

### 常见追问

1. **为什么 Embedding 向量相似就能代表语义相似？**
   - 训练时用对比学习，让相似句子向量接近

2. **MiniLM 和 MPNet 如何选择？**
   - 速度优先选 MiniLM，精度优先选 MPNet

3. **Embedding 如何应对领域术语？**
   - 微调或使用领域专用模型

---

*本文档共 30 道面试题，覆盖 sentence-transformers 的核心技术点*
