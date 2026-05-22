# RAG 知识库流程设计

技术选型：Python 3.12、Qwen3-Embedding、Milvus、MySQL 8.0。

本文基于现有 `rag.md` 和新增需求整理，重点描述从文档导入、解析、切分、存储到混合检索的完整流程。后续开发可以按模块拆分任务、接口和数据表。

## 1. 整体流程

```mermaid
flowchart TD
    A[文件导入] --> B[文档解析]
    B --> C[清洗与结构还原]
    C --> D[切分 Chunk]
    D --> E[Embedding 向量化]
    D --> F[关键词索引构建]
    E --> G[Milvus 向量库]
    F --> H[MySQL 8.0 全文索引或倒排索引]
    D --> I[MySQL 元数据与版本库]
    G --> J[混合检索]
    H --> J
    I --> J
    J --> K[重排序 Rerank]
    K --> L[上下文组装]
    L --> M[LLM 生成答案]
    M --> N[日志、缓存、反馈闭环]
    N --> O[清洗规则和检索策略持续优化]
```



核心原则：

- 有结构文档优先直接解析结构，例如 Word 标题、段落、表格、批注、目录。
- 无结构文档先做页面级拆分、清晰度识别、版面分析和 OCR，再还原阅读顺序。
- 切分策略按文档结构差异动态选择，优先保证语义完整，其次满足 token 约束。
- 检索必须是混合检索：Milvus 向量检索 + MySQL 关键词检索，融合后再重排序。
- 文档版本、清洗规则、解析质量、Chunk 元数据都进入 MySQL，方便回溯和持续优化。

## 2. 导入流程

```mermaid
flowchart TD
    A[用户上传文件或批量导入] --> B[生成文件 hash]
    B --> C{是否重复文件}
    C -- 是 --> C1[关联已有文档版本或跳过导入]
    C -- 否 --> D[保存原始文件]
    D --> E[识别文件类型]
    E --> F[创建 Document 记录]
    F --> G[创建 DocumentVersion 记录]
    G --> H[进入解析任务队列]
    H --> I[更新导入状态: 待解析]
```



建议保存信息：


| 对象              | 关键字段                                                            |
| --------------- | --------------------------------------------------------------- |
| Document        | document_id、业务归属、文件名、文件类型、当前版本、状态                               |
| DocumentVersion | version_id、document_id、file_hash、storage_path、上传人、上传时间          |
| ImportTask      | task_id、document_id、version_id、status、error_message、retry_count |


## 3. 文件类型识别与解析分流

```mermaid
flowchart TD
    A[解析任务开始] --> B[文件类型识别]
    B --> C{文档是否自带结构标记}
    C -- Word / Markdown / HTML / TXT --> D[结构化解析]
    C -- PDF --> E[PDF 单页拆分]
    C -- 图片 --> F[图片预处理]
    C -- 表格文件 --> G[表格结构解析]

    D --> H[提取标题、段落、列表、表格、图片、页码]
    E --> I[页面清晰度与文本层识别]
    F --> J[图像增强与方向矫正]
    G --> K[Sheet、行列、表头、单元格提取]

    H --> Z[统一中间结构 DocumentElement]
    I --> Z
    J --> Z
    K --> Z
```



统一中间结构建议：


| 字段                       | 说明                                                   |
| ------------------------ | ---------------------------------------------------- |
| element_id               | 元素唯一 ID                                              |
| document_id / version_id | 文档和版本                                                |
| page_no                  | 页码，Word 可为空或按导出页码计算                                  |
| element_type             | title、paragraph、table、image、chart、list、header、footer |
| text                     | 识别后的文本                                               |
| bbox                     | 页面坐标，用于版面还原                                          |
| reading_order            | 阅读顺序                                                 |
| confidence               | OCR 或结构识别置信度                                         |
| parent_path              | 标题层级路径                                               |


## 4. Word 等有标记文档解析流程

```mermaid
flowchart TD
    A[Word / Markdown / HTML] --> B[读取原生结构]
    B --> C[提取标题层级]
    C --> D[提取段落、列表、代码块]
    D --> E[提取表格和表题]
    E --> F[提取图片、图题、替代文本]
    F --> G[处理批注、修订、页眉页脚]
    G --> H[清洗无效内容]
    H --> I[生成结构化元素]
    I --> J[输出 Markdown 化正文和元素树]
```



处理建议：

- Word 文档如果有标题样式，优先用标题样式构建 `title_path`。
- 表格保留表头、合并单元格关系和表格标题。
- 图片如果存在题注或前后说明，需要和图片元素建立关联。
- 批注、修订、页眉页脚是否保留由清洗规则控制。

## 5. PDF 与图片无标记文档解析流程

```mermaid
flowchart TD
    A[PDF 或图片] --> B{是否 PDF}
    B -- 是 --> C[按单页拆分 PDF]
    B -- 否 --> D[作为单页图片处理]
    C --> E[检测文本层]
    E --> F{电子版还是扫描版}
    F -- 电子版 --> G[直接提取文本、字体、坐标、图片]
    F -- 扫描版 --> H[页面转图片]
    D --> H
    H --> I[图像预处理: 去噪、纠偏、增强、旋转检测]
    I --> J[清晰度识别与低质页标记]
    J --> K[版面分析]
    K --> L[元素切割: 文本、标题、表格、图片、图表]
    L --> M[普通文本 OCR]
    L --> N[表格专用 OCR]
    L --> O[图片/图表多模态描述生成]
    M --> P[阅读顺序还原]
    N --> P
    O --> P
    G --> P
    P --> Q[跨栏、跨页、页眉页脚处理]
    Q --> R[合并零散文本为原文结构]
    R --> S[输出 DocumentElement]
```



关键补充：

- 清晰度识别：按 DPI、模糊度、倾斜角、噪声、文字高度判断 OCR 风险。
- 电子版 PDF：优先使用文本层和坐标，避免 OCR 引入错误。
- 扫描版 PDF：重点关注 OCR 效果，低置信度页面进入人工复核或二次 OCR。
- 版面分析：支持单栏、双栏、混合栏、跨页表格、页眉页脚、脚注、图片题注。
- 表格和图片使用专用 OCR 或视觉模型，提升复杂区域识别精度。

## 5.1 图片多模态描述生成

```mermaid
flowchart TD
    A[图片/图表区域] --> B[多模态模型分析]
    B --> C[生成结构化描述]
    C --> D{是否图表类型}
    D -- 是 --> E[提取图表类型、标题、坐标轴、数据序列]
    D -- 否 --> F[生成场景描述、关键物体、文字内容]
    E --> G[生成增强描述文本]
    F --> G
    G --> H[与原图题注和前后文关联]
    H --> I[输出 image_description 字段]
```



图片描述增强建议：


| 字段                 | 说明                   |
| ------------------ | -------------------- |
| description        | 多模态模型生成的场景/内容描述      |
| chart_type         | 图表类型：折线图、柱状图、饼图、流程图等 |
| chart_data_summary | 图表数据摘要（关键数据点、趋势）     |
| alt_text           | 替代文本（如果原图有）          |
| semantic_tags      | 语义标签：人物、产品、场景等       |


多模态模型选型建议：

- 通用图片：Qwen-VL、GPT-4V、Claude Vision
- 图表理解：专用图表解析模型或带图表理解的通用模型
- 输出格式：结构化 JSON，便于后续检索和引用

## 6. 版面分析与结构还原流程

```mermaid
flowchart TD
    A[页面元素集合] --> B[按 bbox 初步排序]
    B --> C[识别页眉页脚和页码]
    C --> D[识别栏结构: 单栏 / 双栏 / 多栏]
    D --> E[识别标题、正文、脚注、题注]
    E --> F[识别表格、图片、图表区域]
    F --> G[建立元素邻接关系]
    G --> H[按阅读顺序重排]
    H --> I[跨页段落合并]
    I --> J[跨页表格合并]
    J --> K[低置信度片段标记]
    K --> L[还原为章节树和 Markdown 正文]
```



输出要求：

- 每个元素保留 `page_no`、`bbox`、`confidence`，便于引用原文位置。
- 跨页合并要保留来源页范围，例如 `page_start`、`page_end`。
- 低置信度 OCR 内容不要静默入库，应标记并可按业务配置决定是否参与检索。

## 7. 清洗规则流程

```mermaid
flowchart TD
    A[结构化元素] --> B[读取 MySQL 清洗规则]
    B --> C[编码修复与乱码检测]
    C --> D[噪声过滤]
    D --> E[页眉页脚和水印处理]
    E --> F[广告、目录、免责声明处理]
    F --> G[重复段落和模板文本识别]
    G --> H[敏感信息脱敏]
    H --> I[质量评分]
    I --> J{是否达到入库阈值}
    J -- 否 --> K[标记为需复核或丢弃]
    J -- 是 --> L[生成 CleanDocument]
```



清洗规则建议放在 MySQL：


| 表                     | 说明                       |
| --------------------- | ------------------------ |
| cleaning_rule         | 规则名称、规则类型、正则或配置、启停状态、优先级 |
| cleaning_rule_scope   | 适用业务、文档类型、文件来源           |
| cleaning_rule_version | 规则版本、变更人、变更说明            |
| cleaning_log          | 命中规则、处理前后摘要、处理时间         |


规则类型示例：

- 正则删除：页眉、页脚、固定免责声明。
- 正则替换：空白归一化、异常符号修复。
- 结构删除：目录页、封面页、空白页。
- 质量控制：OCR 置信度低于阈值、乱码比例超过阈值。
- 脱敏规则：手机号、身份证号、邮箱、客户编号。

## 8. 切分总流程

```mermaid
flowchart TD
    A[CleanDocument / DocumentElement] --> B[判断文档结构类型]
    B --> C{是否有明确章节结构}
    C -- 是 --> D[按标题层级优先切分]
    C -- 否 --> E[按段落和语义边界切分]
    D --> F[语义连贯性检测]
    E --> F
    F --> G[合并过短片段]
    G --> H[超长片段强制拆分]
    H --> I[添加合理 Overlap]
    I --> J[图表与标题或说明合并]
    J --> K[生成 ChunkMetadata]
    K --> L[计算 content_hash]
    L --> M[输出 Chunk 列表]
```



推荐默认参数：


| 参数                 | 建议值    | 说明          |
| ------------------ | ------ | ----------- |
| target_tokens      | 600    | 常规文本目标长度    |
| max_tokens         | 900    | 超过后强制拆分     |
| min_tokens         | 120    | 过短片段尽量向前后合并 |
| overlap_tokens     | 80-120 | 兜底保留上下文     |
| semantic_threshold | 按验证集调参 | 句间语义断点阈值    |


## 9. 不同结构的切片策略

```mermaid
flowchart TD
    A[待切分元素] --> B{元素类型}
    B -- 标题 + 段落 --> C[章节内语义切片]
    B -- 表格 --> D[表题 + 表头 + 行块切片]
    B -- 图片 / 图表 --> E[图题 + 视觉描述 + 相关正文合并]
    B -- 列表 --> F[保持列表项完整]
    B -- 代码块 --> G[代码块独立切片]
    B -- OCR 零散文本 --> H[先还原段落再切片]
    C --> I[Token 约束]
    D --> I
    E --> I
    F --> I
    G --> I
    H --> I
    I --> J[生成最终 Chunk]
```



策略补充：

- 语义切片：用模型判断句子间语义连贯性，在主题变化处切断。
- 重叠机制：Overlap 是信息完整性的兜底，不应替代合理的语义边界。
- 图表重要场景：图表标题、图表 OCR 内容、图表前后说明应合并为同一 Chunk 或建立强关联。
- 表格切片：长表按行块拆分，每个块保留表头、表名、章节路径。
- **长表格跨页处理**：跨页表格切片时可能丢失上下文，每个表格 Chunk 必须包含 `table_summary` 字段，描述表格整体内容和目的。
- OCR 文本：先按阅读顺序还原段落，再参与语义切分。

## 9.1 表格处理增强

```mermaid
flowchart TD
    A[表格元素] --> B[提取表头和表结构]
    B --> C[识别合并单元格关系]
    C --> D[提取表格标题和说明]
    D --> E[生成表格摘要]
    E --> F{表格是否跨页}
    F -- 是 --> G[多页表格合并重组]
    F -- 否 --> H[按行块切片]
    G --> H
    H --> I[每个块附加 table_summary 和 table_schema]
    I --> J[关联章节路径 title_path]
    J --> K[输出 TableChunk]
```



表格摘要字段建议：


| 字段             | 说明                         |
| -------------- | -------------------------- |
| table_summary  | 表格整体内容摘要，1-3 句话描述表格目的和关键数据 |
| table_schema   | 表结构描述：列名、数据类型、含义           |
| table_caption  | 原始表题                       |
| row_count      | 总行数                        |
| is_merged      | 是否包含合并单元格                  |
| spanning_pages | 跨页范围（如果有）                  |


摘要生成策略：

- 使用 LLM 提取表格核心信息：统计了哪些指标、对比了哪些维度
- 每个切片块都附加全局摘要，保证局部内容不丢失全局上下文
- 检索时可通过 table_summary 快速匹配用户查询意图

## 10. 存储流程

```mermaid
flowchart TD
    A[Chunk 列表] --> B[生成 enhanced_content]
    B --> C[Qwen3-Embedding 向量化]
    C --> D[向量归一化]
    D --> E[写入 Milvus]
    A --> F[写入 MySQL Chunk 表]
    A --> G[构建关键词字段]
    G --> H[MySQL FULLTEXT 或倒排索引表]
    E --> I[记录 vector_id]
    H --> J[记录 keyword_index_id]
    F --> K[更新文档版本状态]
    I --> K
    J --> K
```



Milvus 建议字段：


| 字段                    | 说明                          |
| --------------------- | --------------------------- |
| vector_id             | 向量 ID                       |
| embedding             | Qwen3-Embedding 向量          |
| document_id           | 文档 ID                       |
| version_id            | 文档版本                        |
| chunk_id              | Chunk ID                    |
| title_path            | 标题路径                        |
| page_start / page_end | 页码范围                        |
| block_type            | paragraph、table、image、chart |
| source_type           | local、ai_generated          |


MySQL 建议表：


| 表                   | 说明                         |
| ------------------- | -------------------------- |
| documents           | 文档主表                       |
| document_versions   | 文档版本表                      |
| document_elements   | 解析元素表，可选保留                 |
| document_chunks     | Chunk 原文、增强文本、hash、页码、标题路径 |
| chunk_keyword_index | 关键词倒排索引，可替代或补充 FULLTEXT    |
| cleaning_rule       | 清洗规则                       |
| parse_quality_log   | 解析质量与 OCR 置信度              |
| qa_logs             | 问答日志和引用来源                  |


关键词检索实现建议：

- 简化方案：MySQL 8.0 `FULLTEXT` + `ngram` parser，对 `title_path`、`content`、`keywords` 建全文索引。
- 可控方案：维护 `chunk_keyword_index(term, chunk_id, tf, field, position)`，业务可以自定义分词、同义词和权重。

## 10.1 Embedding 缓存层设计

```mermaid
flowchart TD
    A[Query 请求] --> B[计算 Query Hash]
    B --> C{Cache 检查}
    C -- Cache Hit --> D[直接返回缓存的向量]
    C -- Cache Miss --> E[调用 Qwen3-Embedding]
    E --> F[存储向量到缓存]
    F --> G[返回向量]
    D --> H[混合检索]
    G --> H
```



缓存策略建议：


| 缓存维度   | 说明                                       |
| ------ | ---------------------------------------- |
| 查询指纹   | 对 Query 文本做标准化（去停用词、统一大小写）后计算 MD5/SHA256 |
| TTL 设置 | 根据业务查询分布设置，例如 24 小时或 7 天                 |
| 缓存预热   | 对高频 Query 批量预计算 Embedding                |
| 冷热分层   | Redis 热数据 + MySQL/文件冷数据                  |


缓存命中优化：

```python
# Query 标准化示例
def normalize_query(query: str) -> str:
    # 去除多余空格、标点归一化、停用词过滤
    query = re.sub(r'\s+', ' ', query)
    query = query.lower().strip()
    return query
```

缓存层选型建议：


| 方案            | 适用场景      | 优点          | 缺点            |
| ------------- | --------- | ----------- | ------------- |
| Redis Cluster | 高并发、低延迟要求 | 毫秒级响应、支持分布式 | 成本较高、数据量受内存限制 |
| Redis + MySQL | 中等规模、需持久化 | 冷热分层、成本可控   | 架构稍复杂         |
| 本地内存 + Redis  | 单机或小规模集群  | 简单、无网络开销    | 扩展性差          |


缓存失效策略：

- 文档更新时：清除相关 Query 缓存或使用版本号控制
- 定期全量刷新：防止 Embedding 模型更新导致的不一致
- LRU 淘汰：控制缓存大小，防止内存溢出

## 11. 查询改写流程

```mermaid
flowchart TD
    A[用户原始问题] --> B[问题规范化]
    B --> C[口语化改写为清晰问题]
    C --> D[意图识别与实体抽取]
    D --> E{是否复杂多意图}
    E -- 是 --> F[子查询分解]
    E -- 否 --> G[保留单查询]
    F --> H[多查询生成 3 到 5 个]
    G --> H
    H --> I[HyDE 生成假设答案]
    I --> J[后退提示生成宏观背景问题]
    J --> K[查询集合去重与权重分配]
    K --> L[进入混合检索]
```



查询增强策略：

- 查询重写：把口语化、含糊问题改成清晰检索表达。
- 多查询生成：一个问题扩展为 3 到 5 个相似问题，提升召回覆盖。
- 子查询分解：复杂问题按多个意图分别检索，然后合并证据。
- HyDE：先让大模型生成假设答案，再用假设答案向量检索。
- 后退提示：把具体问题抽象为宏观背景问题，先检索背景再回答原问题。

## 12. 混合检索流程

```mermaid
flowchart TD
    A[查询集合] --> B[向量检索分支]
    A --> C[关键词检索分支]

    B --> B1[Qwen3-Embedding 编码查询]
    B1 --> B2[Milvus ANN TopN]
    B2 --> B3[向量相似度过滤]

    C --> C1[分词、同义词、关键词归一化]
    C1 --> C2[MySQL FULLTEXT 或倒排索引查询]
    C2 --> C3[BM25 / TF-IDF / 字段权重评分]

    B3 --> D[结果归一化]
    C3 --> D
    D --> E[结果融合 RRF 或加权融合]
    E --> F[去重与版本过滤]
    F --> G[权限过滤和业务过滤]
    G --> H[候选 Chunk TopK]
    H --> I[重排序模型]
    I --> J[最终上下文]
```



融合建议：


| 阶段    | 建议                                             |
| ----- | ---------------------------------------------- |
| 向量召回  | Milvus Top 50-100，适合语义相似问题                     |
| 关键词召回 | MySQL Top 50-100，适合专有名词、编号、精确短语                |
| 分数归一化 | 将 cosine、BM25 等不同分数转成统一区间                      |
| 结果融合  | 优先用 RRF，也可按业务配置 `0.6 * vector + 0.4 * keyword` |
| 过滤    | 文档版本、权限、业务线、时间范围、OCR 质量                        |
| 重排序   | 对融合候选做 Cross-Encoder Rerank，输出最终 TopK          |


## 13. 重排序与上下文组装流程

```mermaid
flowchart TD
    A[候选 Chunk TopK] --> B[构造 query + chunk pair]
    B --> C[重排序模型计算相关性]
    C --> D[按相关性排序]
    D --> E[过滤低分 Chunk]
    E --> F[邻接 Chunk 扩展]
    F --> G[同表格/同图表关联扩展]
    G --> H[按标题路径和页码重组上下文]
    H --> I[去重与 token 预算裁剪]
    I --> J[输出最终 Context]
```



上下文组装要求：

- 保留来源引用：文件名、版本、页码、标题路径、chunk_id。
- 表格和图表内容要完整，不要只取到半张表或只有图题。
- 如果多个 Chunk 来自同一章节，按原文顺序拼接。
- 根据 token 预算动态裁剪，优先保留重排序分高、来源质量高、版本新的证据。

## 14. 回答生成与反馈闭环

```mermaid
flowchart TD
    A[最终 Context] --> B[构造 Prompt]
    B --> C[LLM 生成答案]
    C --> D[引用来源绑定]
    D --> E[事实一致性检查]
    E --> F{是否有足够证据}
    F -- 是 --> G[返回答案和引用]
    F -- 否 --> H[返回无法确认并给出可用背景]
    G --> I[保存 QA 日志]
    H --> I
    I --> J[用户反馈]
    J --> K[分析低质召回、低质 OCR、切分问题]
    K --> L[优化清洗规则、切分参数、检索权重]
```



## 15. 文档版本管理流程

```mermaid
flowchart TD
    A[新文件上传] --> B[计算文件 hash]
    B --> C{同 document 是否已有相同 hash}
    C -- 是 --> D[复用已有版本]
    C -- 否 --> E[创建新版本]
    E --> F[解析新版本]
    F --> G[生成新 Chunk 和新向量]
    G --> H[旧版本标记 inactive]
    H --> I[新版本标记 active]
    I --> J[保留历史版本可回溯]
    J --> K[检索默认只查 active 版本]
```



版本策略：

- 每次文件内容变化创建新 `version_id`。
- Milvus 和 MySQL Chunk 都带 `version_id`。
- 默认检索当前 active 版本，历史问答日志保留当时引用的版本。
- 旧版本向量可以软删除，定期物理清理。

## 16. 异常与质量控制流程

```mermaid
flowchart TD
    A[解析或入库任务] --> B{是否异常}
    B -- 否 --> C[正常完成]
    B -- 是 --> D[记录错误类型]
    D --> E{是否可重试}
    E -- 是 --> F[进入重试队列]
    E -- 否 --> G[标记失败并通知]
    F --> H{超过最大重试次数}
    H -- 否 --> A
    H -- 是 --> G
    C --> I[质量评分入库]
    G --> I
```



质量指标：


| 指标                     | 说明             |
| ---------------------- | -------------- |
| parse_success_rate     | 文档解析成功率        |
| ocr_confidence_avg     | OCR 平均置信度      |
| low_quality_page_count | 低质页面数量         |
| chunk_count            | 切分数量           |
| avg_chunk_tokens       | 平均 Chunk token |
| retrieval_hit_rate     | 检索命中率          |
| no_answer_rate         | 无法回答比例         |


## 16.1 异步队列与消息中间件设计

当前设计中隐含了队列概念，但未明确消息中间件。以下补充 RabbitMQ 作为异步队列的完整设计：

```mermaid
flowchart TD
    A[文件导入] --> B[生成 ImportTask]
    B --> C[发布 ImportTask 消息]
    C --> D[RabbitMQ Queue]

    D --> E[ParseWorker 消费]
    E --> F[解析完成后发布 ParseComplete]
    F --> G[CleanWorker 消费]
    G --> H[清洗完成后发布 CleanComplete]
    H --> I[ChunkWorker 消费]
    I --> J[切分完成后发布 ChunkComplete]
    J --> K[EmbeddingWorker 消费]
    K --> L[向量化完成后发布 EmbeddingComplete]
    L --> M[IndexWorker 消费]
    M --> N[索引完成后发布 IndexComplete]
```



RabbitMQ 配置建议：


| 配置项    | 建议值                                                         |
| ------ | ----------------------------------------------------------- |
| 交换机类型  | topic-exchange，支持多消费者                                       |
| 消息持久化  | durable=true，持久化到磁盘                                         |
| 队列配置   | 按任务类型分区：parse_queue、clean_queue、chunk_queue、embedding_queue |
| 消费者数量  | 根据任务类型配置：解析密集型可多配 Worker                                    |
| 消息 TTL | 根据任务紧急程度设置，避免积压任务过期                                         |
| 死信队列   | 失败消息进入 DLX，记录错误信息供排查                                        |


消息格式建议：

```json
{
  "task_id": "uuid",
  "task_type": "parse|clean|chunk|embedding|index",
  "document_id": "uuid",
  "version_id": "uuid",
  "priority": 1-5,
  "retry_count": 0,
  "created_at": "timestamp",
  "payload": {
    "file_path": "/path/to/file",
    "config": {}
  }
}
```

队列消费策略：


| 策略    | 说明                     |
| ----- | ---------------------- |
| 优先级队列 | 高优先级任务（用户主动刷新）优先处理     |
| 限流控制  | 避免瞬时任务高峰压垮下游服务         |
| 幂等处理  | 消息重复消费时检查任务状态，防止重复处理   |
| 失败重试  | 可重试错误（网络超时）自动重试，最大 N 次 |
| 人工介入  | 不可重试错误（解析失败）标记并通知      |


多租户队列隔离：

- 按业务线或租户创建独立的 VHost
- 不同租户的队列物理隔离，互不影响
- 监控各租户队列积压情况，及时告警

## 17. 推荐开发模块拆分

```mermaid
flowchart LR
    A[ImportService] --> B[ParseService]
    B --> C[CleanService]
    C --> D[ChunkService]
    D --> E[EmbeddingService]
    D --> F[KeywordIndexService]
    E --> G[MilvusRepository]
    F --> H[MySQLKeywordRepository]
    D --> I[DocumentRepository]
    G --> J[RetrievalService]
    H --> J
    J --> K[RerankService]
    K --> L[QAService]
    L --> M[FeedbackService]
    M --> C
    M --> J
    N[QueueConsumer] --> B
    N --> C
    N --> D
    N --> E
    N --> F
    O[CacheService] -.-> J
```



新增服务说明：


| 服务            | 职责                              |
| ------------- | ------------------------------- |
| QueueConsumer | RabbitMQ 消费者，统一管理各 Worker 的消息消费 |
| CacheService  | Embedding 缓存管理、Query 指纹计算、缓存读写  |
| VHostManager  | 多租户 VHost 隔离、资源配额管理             |


优先级建议：

1. 先完成文档导入、版本表、基础解析和 Chunk 入库。
2. 再完成 Qwen3-Embedding + Milvus 向量检索。
3. 接着补 MySQL 关键词检索，形成混合检索闭环。
4. 然后强化 PDF / 图片 OCR、版面分析、表格图片专用处理。
5. 加入 RabbitMQ 异步队列，保障任务可靠性和系统解耦。
6. 加入 Embedding 缓存层，减少高频 Query 重复计算。
7. 最后加入查询改写、多查询、HyDE、后退提示、反馈优化。

