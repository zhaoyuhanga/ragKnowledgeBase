# RAG 架构核心面试题集

> 本文档包含 30 道 RAG（检索增强生成）架构相关的高频面试题，涵盖 RAG 原理、检索优化、生成优化、评估指标等核心概念。所有答案均为中文，代码附有详细中文解释。

---

## 目录

1. [RAG 基础](#1-rag-基础)
2. [检索优化](#2-检索优化)
3. [生成优化](#3-生成优化)
4. [RAG 评估](#4-rag-评估)
5. [高级 RAG](#5-高级-rag)

---

## 1. RAG 基础

### Q1: 什么是 RAG？它的核心思想是什么？

**参考答案：**

**RAG 定义：**
RAG（Retrieval-Augmented Generation，检索增强生成）是一种结合检索系统和生成模型的技术架构，让大语言模型能够基于外部知识库生成准确回答。

**核心思想：**

```
传统 LLM：
用户问题 ──▶ LLM 直接回答（可能幻觉）

RAG：
用户问题 ──▶ 检索相关文档 ──▶ 结合上下文 ──▶ LLM 生成
                          │
                          ▼
                    ┌──────────────┐
                    │  知识库文档   │
                    └──────────────┘
```

**三阶段流程：**

| 阶段 | 任务 | 技术 |
|------|------|------|
| **检索** | 从知识库找到相关文档 | 向量检索、关键词检索 |
| **增强** | 将检索结果注入 Prompt | 上下文拼接、Prompt 工程 |
| **生成** | 基于上下文生成回答 | LLM |

**项目实现：**

```python
# rag-qa-system/app/services/qa_service.py

async def ask(self, question: str):
    # 1. 检索阶段
    query_embedding = embedding_service.encode_single(question)
    search_results = vector_store.search_vectors(
        query_embedding=query_embedding,
        n_results=5
    )
    
    # 2. 增强阶段
    retrieved_chunks = self._parse_search_results(search_results)
    context_texts = [chunk["content"] for chunk in retrieved_chunks]
    
    # 3. 生成阶段
    answer = llm.generate_with_context(
        question=question,
        context=context_texts
    )
    
    return answer
```

---

### Q2: RAG 与微调（Fine-tuning）的区别？

**参考答案：**

**对比表格：**

| 特性 | RAG | Fine-tuning |
|------|------|-------------|
| **数据更新** | 实时更新知识库 | 需要重新训练 |
| **知识来源** | 外部文档 | 训练数据 |
| **幻觉问题** | 减少 | 可能减少 |
| **成本** | 低（无需训练） | 高（需要训练） |
| **部署** | 简单 | 复杂 |
| **适用场景** | 知识频繁变化 | 任务模式固定 |
| **响应质量** | 依赖检索质量 | 依赖训练数据 |

**选择建议：**

```python
# 选择 RAG 的场景
if knowledge_changes_frequently:
    use_rag = True

if need_to_show_sources:
    use_rag = True  # RAG 可追溯来源

if task_pattern_fixed_and_training_data_available:
    use_fine_tuning = True

# 最佳实践：RAG + Fine-tuning 组合
```

---

### Q3: RAG 的评估指标有哪些？

**参考答案：**

**三大评估维度：**

| 维度 | 指标 | 说明 |
|------|------|------|
| **检索质量** | Hit Rate、MRR、MAP | 检索到相关文档的能力 |
| **生成质量** | ROUGE、BLEU | 生成内容与参考的相似度 |
| **端到端** | 答案准确率、幻觉率 | 整体效果 |

**检索指标：**

```python
# Hit Rate @ K
def hit_rate_at_k(retrieved: list, relevant: list, k: int) -> float:
    """前K个结果中包含相关文档的比例"""
    retrieved_k = set(retrieved[:k])
    relevant_set = set(relevant)
    return len(retrieved_k & relevant_set) / len(relevant_set)

# MRR (Mean Reciprocal Rank)
def mean_reciprocal_rank(queries: list) -> float:
    """相关文档首次出现位置的倒数平均"""
    ranks = []
    for query in queries:
        for i, doc in enumerate(query["retrieved"]):
            if doc in query["relevant"]:
                ranks.append(1 / (i + 1))
                break
    return sum(ranks) / len(ranks) if ranks else 0

# MAP (Mean Average Precision)
def mean_average_precision(queries: list) -> float:
    """平均精确率的均值"""
    aps = []
    for query in queries:
        precisions = []
        relevant_count = 0
        for i, doc in enumerate(query["retrieved"]):
            if doc in query["relevant"]:
                relevant_count += 1
                precisions.append(relevant_count / (i + 1))
        aps.append(sum(precisions) / len(query["relevant"]))
    return sum(aps) / len(aps)
```

**生成指标：**

```python
from rouge import Rouge

def evaluate_rouge(reference: str, hypothesis: str) -> dict:
    """计算 ROUGE 分数"""
    rouge = Rouge()
    scores = rouge.get_scores(hypothesis, reference)
    return scores[0]

# BLEU 分数
from nltk.translate.bleu_score import sentence_bleu
bleu = sentence_bleu(reference_tokens, hypothesis_tokens)
```

---

### Q4: 什么是 Chunking？为什么需要文本切分？

**参考答案：**

**Chunking 定义：**
将长文档切分为小块文本，每个小块独立向量化存储。

**为什么需要切分：**

| 原因 | 说明 |
|------|------|
| **LLM 上下文限制** | Token 数量有限 |
| **检索精度** | 小块更容易准确匹配问题 |
| **向量表示** | 长文本稀释语义焦点 |
| **成本控制** | 减少输入 Token 数量 |

**切分策略：**

```python
# 项目中的切分策略
class TextSplitter:
    def __init__(self, chunk_size=500, chunk_overlap=50):
        self.chunk_size = chunk_size  # 块大小
        self.chunk_overlap = chunk_overlap  # 重叠大小
    
    def split(self, text: str) -> list[str]:
        # 1. 按段落分割
        paragraphs = text.split('\n\n')
        
        # 2. 合并小段落
        chunks = []
        current = []
        
        for para in paragraphs:
            if sum(len(p) for p in current) + len(para) <= self.chunk_size:
                current.append(para)
            else:
                chunks.append('\n\n'.join(current))
                # 重叠：保留最后一个段落
                current = [current[-1]] if len(current) > 1 else []
                current.append(para)
        
        if current:
            chunks.append('\n\n'.join(current))
        
        return chunks
```

---

### Q5: 如何选择 Chunk Size？

**参考答案：**

**选择考虑因素：**

| 因素 | 说明 |
|------|------|
| **语义完整性** | 块内语义应完整 |
| **查询匹配度** | 块应包含常见问题的答案 |
| **向量维度** | 块大小影响向量表示 |

**Chunk Size 对比：**

| Size | 优点 | 缺点 |
|------|------|------|
| **100-200** | 匹配精确 | 可能丢失上下文 |
| **300-500** | 平衡（项目使用） | - |
| **800-1000** | 上下文完整 | 可能稀释语义 |

**自适应切分：**

```python
def smart_chunk(text: str) -> list[str]:
    """智能切分策略"""
    chunks = []
    
    # 1. 优先按段落切分
    paragraphs = text.split('\n\n')
    
    # 2. 按句子合并到合适大小
    current = []
    current_size = 0
    
    for para in paragraphs:
        para_size = len(para)
        
        if current_size + para_size <= 500:
            current.append(para)
            current_size += para_size
        else:
            if current:
                chunks.append('\n\n'.join(current))
            
            # 处理超过限制的大段落
            if para_size > 500:
                # 按句子切分
                sentences = split_sentences(para)
                current = []
                current_size = 0
                
                for sentence in sentences:
                    if current_size + len(sentence) <= 500:
                        current.append(sentence)
                        current_size += len(sentence)
                    else:
                        if current:
                            chunks.append(' '.join(current))
                        current = [sentence]
                        current_size = len(sentence)
            else:
                current = [para]
                current_size = para_size
    
    if current:
        chunks.append('\n\n'.join(current))
    
    return chunks
```

---

## 2. 检索优化

### Q6: 如何提升检索质量？

**参考答案：**

**检索优化策略：**

| 策略 | 说明 | 效果 |
|------|------|------|
| **混合检索** | 向量+关键词 | 互补 |
| **重排序** | Cross-Encoder 重排 | 精度提升 |
| **查询扩展** | 同义词/问题改写 | 召回提升 |
| **元数据过滤** | 按类型/时间过滤 | 精准召回 |
| **MMR** | 多样性重排 | 减少冗余 |

**混合检索实现：**

```python
def hybrid_search(query: str, top_k: int = 5):
    """混合检索"""
    # 1. 向量检索
    query_embedding = embedding_service.encode_single(query)
    vector_results = vector_store.search(
        query_embedding=query_embedding,
        n_results=top_k * 2
    )
    
    # 2. 关键词检索
    keyword_results = keyword_search(query, top_k * 2)
    
    # 3. 结果融合（RRF 算法）
    def reciprocal_rank_fusion(results_list, k=60):
        """RRF 融合"""
        scores = {}
        for results in results_list:
            for rank, doc in enumerate(results):
                score = 1 / (k + rank + 1)
                scores[doc] = scores.get(doc, 0) + score
        
        return sorted(scores.items(), key=lambda x: x[1], reverse=True)
    
    fused = reciprocal_rank_fusion(
        [vector_results, keyword_results]
    )
    
    return fused[:top_k]
```

---

### Q7: 什么是 Query Rewrite（查询改写）？

**参考答案：**

**Query Rewrite 技术：**

```python
# 1. 同义词扩展
def expand_query(query: str) -> str:
    """同义词扩展"""
    synonyms = {
        "电脑": ["计算机", "PC"],
        "存储": ["保存", "写入"],
    }
    
    words = query.split()
    expanded = []
    for word in words:
        expanded.append(word)
        if word in synonyms:
            expanded.extend(synonyms[word])
    
    return ' '.join(expanded)

# 2. HyDE（Hypothetical Document Embeddings）
def hyde_rewrite(query: str) -> str:
    """使用 LLM 生成假设性答案，再检索"""
    prompt = f"""基于这个问题生成一个可能的答案：

问题：{query}

生成的答案应该能帮助找到相关文档。"""
    
    hypothetical_answer = llm.generate(prompt)
    
    # 用假设答案检索
    return hypothetical_answer

# 3. 子查询分解
def decompose_query(query: str) -> list[str]:
    """将复杂问题分解为多个简单问题"""
    prompt = f"""将这个问题分解为多个简单的子问题：

问题：{query}

列出所有子问题，每个一行。"""
    
    sub_queries = llm.generate(prompt).split('\n')
    return [q.strip() for q in sub_queries if q.strip()]
```

---

### Q8: 什么是 Cross-Encoder 重排序？

**参考答案：**

**重排序流程：**

```
粗排阶段：
问题 ──▶ 向量检索 Top 100 ──▶ 快速筛选

精排阶段：
Top 100 ──▶ Cross-Encoder ──▶ Top 10
```

**Cross-Encoder 实现：**

```python
from sentence_transformers import CrossEncoder

# 加载交叉编码器
cross_encoder = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')

def rerank(query: str, candidates: list[str], top_k: int = 10) -> list:
    """重排序"""
    # 构建查询-文档对
    pairs = [(query, doc) for doc in candidates]
    
    # 计算相关性分数
    scores = cross_encoder.predict(pairs)
    
    # 按分数排序
    doc_scores = sorted(zip(candidates, scores), key=lambda x: x[1], reverse=True)
    
    return doc_scores[:top_k]

# 项目应用
def search_with_rerank(query: str, top_k: int = 10):
    """带重排序的检索"""
    # 1. 向量检索（粗排）
    vector_results = vector_search(query, n_results=100)
    
    # 2. Cross-Encoder 重排
    reranked = rerank(query, vector_results, top_k=top_k)
    
    return reranked
```

---

### Q9: 什么是 MMR（最大边际相关性）？

**参考答案：**

**MMR 原理：**

```
不使用 MMR：
结果: [Python入门, Python进阶, Python高级, Django框架, Flask框架]
问题: Python 相关的所有内容
问题: 所有结果都是 Python，可能高度重复

使用 MMR：
结果: [Python入门, Django框架, Python进阶, Flask框架, Python高级]
问题: Python 核心内容 + Web框架，多样性更好
```

**MMR 实现：**

```python
def mmr_search(
    query_embedding: list,
    candidates: list,
    lambda_mult: float = 0.5,
    top_k: int = 5
) -> list:
    """
    Max Marginal Relevance 检索
    在相关性和多样性之间取得平衡
    """
    selected = []
    remaining = candidates.copy()
    
    for _ in range(min(top_k, len(candidates))):
        best_score = -float('inf')
        best_doc = None
        
        for doc in remaining:
            # 相关性分数
            relevance = cosine_similarity(query_embedding, doc.embedding)
            
            # 多样性分数（与已选文档的最大相似度）
            diversity = 0
            if selected:
                max_sim = max(
                    cosine_similarity(doc.embedding, s.embedding)
                    for s in selected
                )
                diversity = max_sim
            
            # MMR 分数
            mmr_score = relevance - lambda_mult * diversity
            
            if mmr_score > best_score:
                best_score = mmr_score
                best_doc = doc
        
        if best_doc:
            selected.append(best_doc)
            remaining.remove(best_doc)
    
    return selected

# 项目配置
# runtime_config.enable_mmr = True
# runtime_config.mmr_diversity = 0.5
```

---

### Q10: 如何处理检索不到结果的情况？

**参考答案：**

**空结果处理策略：**

```python
def handle_empty_results(original_query: str, max_retries: int = 3):
    """处理检索为空的情况"""
    
    for attempt in range(max_retries):
        results = vector_search(original_query, n_results=5)
        
        if results:
            return results
        
        # 策略1：放宽相似度阈值
        lower_threshold()
        
        # 策略2：使用关键词检索
        keyword_results = keyword_search(original_query)
        if keyword_results:
            return keyword_results
        
        # 策略3：问题简化
        simplified_query = simplify_query(original_query)
        if simplified_query != original_query:
            original_query = simplified_query
            continue
    
    # 最终策略：返回"无法回答"
    return None  # 触发无法回答逻辑
```

---

## 3. 生成优化

### Q11: 如何设计 RAG 的 Prompt？

**参考答案：**

**Prompt 设计原则：**

| 原则 | 说明 |
|------|------|
| **引用来源** | 明确要求引用参考文档 |
| **约束生成** | 不在文档中时明确说明 |
| **格式规范** | 指定输出格式 |
| **角色设定** | 设定助手角色 |

**Prompt 模板：**

```python
RAG_PROMPT_TEMPLATE = """你是一个专业的知识库问答助手。

【任务】
基于提供的参考文档回答用户问题。

【参考文档】
{context}

【用户问题】
{question}

【回答规则】
1. 只根据参考文档中的信息回答，不要编造内容
2. 如果文档中没有相关信息，明确回复"根据当前知识库无法回答此问题"
3. 回答要清晰、准确、简洁
4. 可以引用文档中的原话来支持回答
5. 如果有多个相关文档，综合它们的信息给出完整回答
6. 在回答末尾标注参考的文档编号

【回答格式】
【回答】
[你的回答]

【参考来源】
[引用的文档编号和相关内容]"""

def build_prompt(question: str, contexts: list[str]) -> str:
    """构建 RAG Prompt"""
    context = "\n\n".join([
        f"[文档{i+1}]: {ctx}"
        for i, ctx in enumerate(contexts)
    ])
    
    return RAG_PROMPT_TEMPLATE.format(
        context=context,
        question=question
    )
```

---

### Q12: 如何处理 LLM 的幻觉问题？

**参考答案：**

**幻觉控制策略：**

```python
# 1. 严格的 Prompt 约束
STRICT_PROMPT = """重要规则：
- 只回答文档中明确包含的信息
- 不要推测或编造任何数字、日期、名称
- 不确定时必须说"信息不足，无法确定"
- 所有回答必须能在参考文档中找到依据"""

# 2. 答案验证
def verify_answer(question: str, answer: str, contexts: list[str]) -> tuple:
    """验证答案是否基于上下文"""
    
    # 检查敏感声明
    suspicious_phrases = [
        "根据公开资料", "据统计", "资料显示"
    ]
    
    for phrase in suspicious_phrases:
        if phrase in answer:
            return False, f"发现未授权引用: {phrase}"
    
    # 检查关键词是否在文档中
    answer_keywords = extract_keywords(answer)
    for keyword in answer_keywords[:5]:  # 检查前5个关键词
        found = any(keyword in ctx for ctx in contexts)
        if not found:
            return False, f"答案中的关键词在文档中未找到: {keyword}"
    
    return True, "验证通过"

# 3. 多角度验证
def generate_with_verification(question: str, contexts: list[str]) -> str:
    """带验证的生成"""
    answer = llm.generate(build_prompt(question, contexts))
    
    is_valid, msg = verify_answer(question, answer, contexts)
    
    if not is_valid:
        # 重新生成，更强调事实性
        answer = llm.generate(
            build_prompt(question, contexts) + 
            "\n\n注意：上述回答存在问题，请确保回答严格基于文档。"
        )
    
    return answer
```

---

### Q13: 如何实现多轮对话 RAG？

**参考答案：**

**多轮对话 RAG 实现：**

```python
async def chat(session_id: str, question: str) -> str:
    """多轮对话 RAG"""
    
    # 1. 获取对话历史
    history = get_conversation_history(session_id)
    
    # 2. 检索相关文档
    contexts = retrieve_context(question, top_k=5)
    
    # 3. 构建带历史的 Prompt
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    
    # 添加历史对话
    for user_msg, assistant_msg in history[-5:]:
        messages.append({"role": "user", "content": user_msg})
        messages.append({"role": "assistant", "content": assistant_msg})
    
    # 添加当前问题（带上下文）
    current_question = f"""基于以下参考文档回答问题：

【参考文档】
{chr(10).join([f'[{i+1}] {ctx}' for i, ctx in enumerate(contexts)])}

【用户问题】
{question}"""
    
    messages.append({"role": "user", "content": current_question})
    
    # 4. 生成回答
    answer = llm.chat(messages)
    
    # 5. 保存对话历史
    save_conversation_history(session_id, question, answer)
    
    return answer
```

---

### Q14: 如何优化 Token 使用成本？

**参考答案：**

**成本优化策略：**

```python
# 1. 上下文压缩
def compress_context(contexts: list[str], max_tokens: int = 3000) -> list[str]:
    """压缩上下文"""
    total_tokens = sum(estimate_tokens(ctx) for ctx in contexts)
    
    if total_tokens <= max_tokens:
        return contexts
    
    # 按相似度排序，保留最相关的
    ranked = contexts  # 假设已按相似度排序
    
    compressed = []
    current_tokens = 0
    
    for ctx in ranked:
        ctx_tokens = estimate_tokens(ctx)
        if current_tokens + ctx_tokens <= max_tokens:
            compressed.append(ctx)
            current_tokens += ctx_tokens
        else:
            break
    
    return compressed

# 2. 摘要压缩
def summarize_and_compress(contexts: list[str]) -> list[str]:
    """摘要压缩长文档"""
    compressed = []
    
    for ctx in contexts:
        tokens = estimate_tokens(ctx)
        
        if tokens > 500:
            summary = llm.generate(f"用50字概括：{ctx}")
            compressed.append(summary)
        else:
            compressed.append(ctx)
    
    return compressed

# 3. 选择性上下文
def selective_context(question: str, contexts: list[str], max_items: int = 3) -> list[str]:
    """选择性上下文"""
    # 选择与问题最相关的 N 个上下文
    scores = [calculate_relevance(question, ctx) for ctx in contexts]
    ranked = sorted(zip(contexts, scores), key=lambda x: x[1], reverse=True)
    return [ctx for ctx, _ in ranked[:max_items]]
```

---

### Q15: RAG 的常见失败模式有哪些？

**参考答案：**

**失败模式及解决方案：**

| 失败模式 | 原因 | 解决方案 |
|----------|------|----------|
| **检索不到相关文档** | 知识库覆盖不足 | 补充文档、优化 Embedding |
| **检索到错误文档** | Embedding 模型不匹配 | 使用领域适配模型 |
| **LLM 忽略上下文** | Prompt 约束不足 | 强化 Prompt 约束 |
| **生成幻觉** | LLM 过度发挥 | 使用更严格的 Prompt |
| **上下文过长截断** | Token 限制 | 上下文压缩 |

**问题诊断流程：**

```python
def diagnose_rag_failure(question: str) -> dict:
    """RAG 问题诊断"""
    results = {
        "retrieval": {},
        "generation": {},
        "suggestions": []
    }
    
    # 1. 检查检索
    contexts = vector_search(question, n_results=5)
    if not contexts:
        results["retrieval"]["status"] = "empty"
        results["suggestions"].append("补充相关文档")
    else:
        # 检查检索质量
        for ctx in contexts:
            relevance = calculate_relevance(question, ctx)
            if relevance < 0.3:
                results["retrieval"]["low_quality"] = True
    
    # 2. 检查生成
    answer = llm.generate(build_prompt(question, contexts))
    is_valid, msg = verify_answer(question, answer, contexts)
    
    if not is_valid:
        results["generation"]["issues"] = msg
        results["suggestions"].append("优化 Prompt 或使用更严格的约束")
    
    return results
```

---

## 4. RAG 评估

### Q16: 如何评估 RAG 系统？

**参考答案：**

**评估框架：**

```python
class RAGEvaluator:
    """RAG 评估器"""
    
    def __init__(self, rag_system):
        self.rag = rag_system
    
    def evaluate(self, test_cases: list) -> dict:
        """评估 RAG 系统"""
        results = {
            "retrieval_metrics": {},
            "generation_metrics": {},
            "end_to_end_metrics": {}
        }
        
        retrieval_scores = {"hit_rate": [], "mrr": []}
        generation_scores = {"rouge": [], "bleu": []}
        accuracy_scores = []
        
        for case in test_cases:
            # 执行 RAG
            answer, contexts = self.rag.ask(case["question"])
            
            # 检索评估
            hr = hit_rate_at_k(contexts, case["relevant_docs"], k=5)
            retrieval_scores["hit_rate"].append(hr)
            
            # 生成评估
            if case.get("reference_answer"):
                rouge = calculate_rouge(case["reference_answer"], answer)
                generation_scores["rouge"].append(rouge)
            
            # 端到端评估
            accuracy = evaluate_answer_correctness(
                answer, case["expected_answer"]
            )
            accuracy_scores.append(accuracy)
        
        results["retrieval_metrics"] = {
            "avg_hit_rate": mean(retrieval_scores["hit_rate"]),
            "avg_mrr": mean(retrieval_scores["mrr"])
        }
        results["generation_metrics"] = {
            "avg_rouge": mean(generation_scores["rouge"])
        }
        results["end_to_end_metrics"] = {
            "accuracy": mean(accuracy_scores)
        }
        
        return results
```

---

### Q17: 什么是 RAGAS 评估指标？

**参考答案：**

**RAGAS 指标定义：**

| 指标 | 说明 | 计算方法 |
|------|------|----------|
| **Faithfulness** | 答案对上下文的忠诚度 | LLM 判断 |
| **Answer Relevance** | 答案与问题的相关性 | LLM 判断 |
| **Context Relevance** | 上下文中与问题相关的比例 | LLM 判断 |

**LLM 作为评估器：**

```python
def evaluate_faithfulness(question: str, answer: str, contexts: list[str]) -> float:
    """评估忠诚度"""
    
    prompt = f"""评估以下回答对参考文档的忠诚度。

问题：{question}
回答：{answer}
参考文档：{chr(10).join(contexts)}

评估标准：
1. 回答中的所有信息是否都能在参考文档中找到？
2. 回答是否有编造或推测的内容？

评分（0-1）：
- 1 = 完全基于文档
- 0.5 = 部分基于文档
- 0 = 完全编造

只输出分数，不要其他内容。"""
    
    score = llm.generate(prompt)
    return float(score.strip())

def evaluate_context_relevance(question: str, contexts: list[str]) -> float:
    """评估上下文相关性"""
    
    prompt = f"""评估以下参考文档对问题的相关性。

问题：{question}
参考文档：{chr(10).join([f'{i+1}. {ctx}' for i, ctx in enumerate(contexts)])}

请评估每个文档与问题的相关程度（0-1），然后给出总体相关性分数。

只输出0-1之间的数字。"""
    
    score = llm.generate(prompt)
    return float(score.strip())
```

---

## 5. 高级 RAG

### Q18: 什么是 Agentic RAG？

**参考答案：**

**Agentic RAG 概念：**
让 LLM 扮演 Agent，能够主动决定检索策略、调用工具、修正查询。

**实现示例：**

```python
class AgenticRAG:
    """Agentic RAG 系统"""
    
    def __init__(self):
        self.tools = {
            "vector_search": self.vector_search,
            "keyword_search": self.keyword_search,
            "web_search": self.web_search,
            "calculator": self.calculator,
        }
    
    def ask(self, question: str) -> str:
        """Agent 处理问题"""
        
        # 1. Agent 规划
        plan = self.plan(question)
        
        # 2. 执行计划
        results = []
        for step in plan["steps"]:
            tool = step["tool"]
            params = step["params"]
            result = self.tools[tool](**params)
            results.append({"tool": tool, "result": result})
        
        # 3. 生成最终答案
        answer = self.synthesize(question, results)
        
        return answer
    
    def plan(self, question: str) -> dict:
        """Agent 规划执行步骤"""
        prompt = f"""分析这个问题，决定需要调用哪些工具：

问题：{question}

可用工具：
1. vector_search: 向量检索知识库
2. keyword_search: 关键词检索
3. web_search: 网络搜索
4. calculator: 数学计算

输出 JSON 格式的执行计划。"""
        
        plan_text = llm.generate(prompt)
        return json.loads(plan_text)
```

---

### Q19: 什么是 Self-RAG？

**参考答案：**

**Self-RAG 原理：**

```
问题 ──▶ LLM 生成回答 + 反思 token ──▶ 评估相关性和效用 ──▶ 选择最佳回答
```

**Self-RAG 实现：**

```python
def self_rag(question: str, num_candidates: int = 3) -> str:
    """Self-RAG 生成"""
    
    # 1. 检索多个候选上下文
    candidates = []
    for _ in range(num_candidates):
        ctx = vector_search(question)
        candidates.append(ctx)
    
    # 2. 对每个候选生成回答
    answers = []
    for ctx in candidates:
        answer = llm.generate(build_prompt(question, ctx))
        
        # 3. 生成反思
        reflection = generate_reflection(question, ctx, answer)
        
        # 4. 评分
        is_relevant = is_context_relevant(question, ctx)
        is_grounded = is_answer_grounded(answer, ctx)
        is_useful = is_answer_useful(question, answer)
        
        answers.append({
            "answer": answer,
            "scores": {
                "relevance": is_relevant,
                "groundedness": is_grounded,
                "utility": is_useful
            }
        })
    
    # 5. 选择最佳回答
    best = max(answers, key=lambda x: 
        sum(x["scores"].values()) / 3
    )
    
    return best["answer"]
```

---

### Q20: 如何构建企业级 RAG 系统？

**参考答案：**

**企业级 RAG 架构：**

```
┌─────────────────────────────────────────────────────────────┐
│                        RAG 系统架构                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐     ┌──────────────┐     ┌────────────┐│
│  │  数据接入层   │     │  预处理层    │     │  索引层    ││
│  │  - 各种数据源 │────▶│  - 解析     │────▶│  - 向量化  ││
│  │  - 增量同步   │     │  - 切分     │     │  - 存储   ││
│  │  - 版本管理   │     │  - 质量过滤  │     │  - 索引   ││
│  └──────────────┘     └──────────────┘     └────────────┘│
│                                                             │
│  ┌──────────────────────────────────────────────────────┐│
│  │                     查询处理层                        ││
│  │  - Query 解析  - 查询扩展  - 意图识别  - 路由选择  ││
│  └──────────────────────────────────────────────────────┘│
│                                                             │
│  ┌──────────────┐     ┌──────────────┐     ┌────────────┐│
│  │    检索层     │────▶│   重排层     │────▶│   生成层    ││
│  │  - 混合检索   │     │  - Cross   │     │  - Prompt ││
│  │  - 层级检索   │     │  - RRF    │     │  - 验证   ││
│  │  - 元数据过滤 │     │  - MMR    │     │  - 引用   ││
│  └──────────────┘     └──────────────┘     └────────────┘│
│                                                             │
│  ┌──────────────────────────────────────────────────────┐│
│  │                     评估与监控                        ││
│  │  - 检索指标  - 生成指标  - 端到端指标  - 告警     ││
│  └──────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

**关键组件实现：**

```python
# 企业级 RAG 类
class EnterpriseRAG:
    def __init__(self):
        self.preprocessor = DataPreprocessor()
        self.indexer = VectorIndexer()
        self.retriever = HybridRetriever()
        self.reranker = CrossEncoderReranker()
        self.generator = RAGGenerator()
        self.evaluator = RAGEvaluator()
    
    def ingest(self, documents: list[Document]):
        """数据接入"""
        # 解析
        parsed = [self.preprocessor.parse(doc) for doc in documents]
        # 切分
        chunks = [self.preprocessor.chunk(p) for p in parsed]
        # 向量化
        embeddings = self.indexer.encode(chunks)
        # 存储
        self.indexer.store(chunks, embeddings)
    
    def query(self, question: str) -> Answer:
        """查询处理"""
        # 扩展
        expanded = self.expand_query(question)
        # 检索
        candidates = self.retriever.search(expanded)
        # 重排
        ranked = self.reranker.rerank(question, candidates)
        # 生成
        answer = self.generator.generate(question, ranked)
        return answer
```

---

### Q21-30: 常见面试问题汇总

**Q21: RAG 和知识图谱的区别？**

```python
# RAG: 非结构化文本检索
# 知识图谱: 结构化三元组
# 组合使用效果更好
```

**Q22: 如何处理多模态 RAG？**

```python
# 图像 + 文本检索
# 使用 CLIP 模型编码图像和文本
image_embeddings = clip_model.encode_image(image)
text_embeddings = clip_model.encode_text(text)
```

**Q23: RAG 的实时性问题？**

```python
# 增量索引
# 定期全量重建
# 混合存储策略
```

**Q24: 如何处理领域术语？**

```python
# 领域词表
# 领域适配 Embedding
# 术语扩展
```

**Q25: RAG 的安全隐私问题？**

```python
# 访问控制
# 数据脱敏
# 审计日志
```

**Q26: RAG 与向量数据库的关系？**

```python
# 向量数据库是 RAG 的存储基础设施
# 存储文档向量和元数据
# 支持高效检索
```

**Q27: 如何提升检索召回率？**

```python
# HyDE
# 查询扩展
# 重写
# 混合检索
```

**Q28: RAG 的冷启动问题？**

```python
# 种子数据
# 模板生成
# 人工标注
```

**Q29: 如何实现多语言 RAG？**

```python
# 多语言 Embedding
# 翻译中间层
# 语言检测路由
```

**Q30: 项目中的 RAG 优化经验？**

```python
# 1. 文档预处理优化
# 2. 检索策略调优
# 3. Prompt 迭代优化
# 4. 缓存策略
```

---

## 附录：面试重点总结

### 核心知识点

| 类别 | 重点内容 |
|------|----------|
| **RAG 原理** | 检索-增强-生成三阶段 |
| **检索优化** | 混合检索、重排序、MMR |
| **生成优化** | Prompt 工程、幻觉控制 |
| **评估指标** | Hit Rate、MRR、Faithfulness |
| **高级 RAG** | Agentic RAG、Self-RAG |

---

*本文档共 30 道面试题，覆盖 RAG 架构的核心技术点*
