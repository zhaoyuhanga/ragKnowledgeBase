// ============================================
// API 统一响应格式
// ============================================

/** 统一响应格式 - 符合API文档 */
export interface ApiResponse<T = unknown> {
  code: number;
  message: string;
  data: T;
  traceId: string;
  timestamp: string;
}

/** 错误响应格式 */
export interface ApiErrorResponse {
  code: string;
  message: string;
  data: null;
  traceId: string;
  timestamp: string;
}

/** 分页响应格式 - 符合API文档 */
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page_no: number;
  page_size: number;
  pages: number;
}

/** 分页请求参数 */
export interface PaginationParams {
  page_no?: number;
  page_size?: number;
}

// ============================================
// 健康检查相关类型
// ============================================

export interface HealthStatus {
  status: 'healthy' | 'unhealthy';
  service: string;
  version: string;
  environment: string;
}

export interface ComponentHealth {
  status: 'connected' | 'disconnected';
  type: string;
}

// ============================================
// 文档管理相关类型
// ============================================

export interface DocumentUploadResponse {
  document_id: number;
  version_id: number;
  task_id: string;
  name: string;
  doc_type: string;
  file_size: number;
  is_duplicate: boolean;
  status: string;
}

export interface BatchUploadResponse {
  total: number;
  success: number;
  failed: number;
  duplicates: number;
  documents: {
    document_id: number;
    version_id: number;
    name: string;
    status: string;
  }[];
  failed_files: {
    name: string;
    error: string;
  }[];
}

export interface DocumentItem {
  id: number;
  name: string;
  doc_type: string;
  business_id: string;
  business_name: string;
  current_version_id: number;
  total_versions: number;
  status: number;
  status_name: string;
  total_pages: number;
  total_chunks: number;
  creator_name: string;
  created_at: string;
}

export interface DocumentDetail extends DocumentItem {
  updated_at: string;
  versions: DocumentVersion[];
}

export interface DocumentVersion {
  id: number;
  version: number;
  file_name: string;
  file_size: number;
  status: number;
  status_name?: string;
  uploaded_at: string;
}

export interface VersionDetail extends DocumentVersion {
  total_pages: number;
  total_elements: number;
  uploader_name: string;
  uploaded_at: string;
  parsed_at?: string;
}

export interface DocumentListParams {
  page_no?: number;
  page_size?: number;
  business_id?: string;
  status?: number;
  keyword?: string;
  start_date?: string;
  end_date?: string;
}

// ============================================
// 导入任务相关类型
// ============================================

export interface ImportTaskItem {
  id: number;
  task_id: string;
  document_id: number;
  task_type: string;
  task_status: string;
  status_name?: string;
  progress: number;
  created_at: string;
}

export interface ImportTaskDetail {
  id: number;
  task_id: string;
  document_id: number;
  version_id: number;
  task_type: string;
  task_status: string;
  priority: number;
  progress: number;
  retry_count: number;
  max_retry: number;
  error_type: string | null;
  error_message: string | null;
  started_at: string;
  completed_at: string;
  cost_seconds: number;
  created_at: string;
}

export interface ImportTaskParams {
  page_no?: number;
  page_size?: number;
  document_id?: number;
  task_type?: string;
  task_status?: string;
}

// ============================================
// 文档解析相关类型
// ============================================

export interface ParseTaskResponse {
  task_id: string;
  document_id: number;
  version_id: number;
  status: string;
}

export interface ParseStatus {
  document_id: number;
  version_id: number;
  status: number;
  status_name: string;
  parse_progress: number;
  total_pages: number;
  total_elements: number;
  quality_summary: {
    good: number;
    warning: number;
    bad: number;
  };
  started_at: string;
  completed_at: string;
  cost_seconds: number;
}

export interface ParseElement {
  id: number;
  element_id: string;
  document_id: number;
  version_id: number;
  page_no: number;
  element_type: string;
  content: string;
  reading_order: number;
  title_level: number | null;
  title_path: string;
  confidence: number;
  quality_flag: 'good' | 'warning' | 'bad';
}

export interface ElementDetail extends ParseElement {
  enhanced_content?: string;
  bbox?: {
    x: number;
    y: number;
    width: number;
    height: number;
  };
  is_merged: boolean;
}

export interface ElementListParams {
  page_no?: number;
  element_type?: string;
  quality_flag?: string;
  page_index?: number;
  page_size?: number;
}

// ============================================
// 清洗服务相关类型
// ============================================

export interface CleaningRule {
  id: number;
  rule_name: string;
  rule_type: string;
  rule_config: Record<string, unknown>;
  scope_type?: string;
  priority: number;
  enabled: boolean;
  description?: string;
  created_at?: string;
  updated_at?: string;
}

export interface CreateCleaningRuleRequest {
  rule_name: string;
  rule_type: string;
  rule_config: Record<string, unknown>;
  scope_type?: string;
  priority?: number;
  enabled?: boolean;
  description?: string;
}

export interface CleaningRuleParams {
  page?: number;
  page_size?: number;
  scope?: string;
  rule_type?: string;
  enabled_only?: boolean;
}

export interface CleaningResult {
  document_id: number;
  version_id: number;
  total_elements: number;
  processed_elements: number;
  removed_elements: number;
  desensitized_count: number;
  avg_quality_score: number;
  processing_time_ms: number;
}

export interface BatchCleaningResult {
  total: number;
  success_count: number;
  failed_count: number;
  results: {
    document_id: number;
    success: boolean;
    total_elements?: number;
    processing_time_ms?: number;
    error?: string;
  }[];
}

export interface CleaningLog {
  id: number;
  document_id: number;
  element_id: string;
  rule_id: number;
  rule_name: string;
  rule_type: string;
  action: string;
  hit_count: number;
  created_at: string;
}

export interface CleaningLogParams {
  document_id: number;
  version_id?: number;
  page?: number;
  page_size?: number;
}

// ============================================
// 切分服务相关类型
// ============================================

export interface ChunkConfig {
  target_tokens?: number;
  max_tokens?: number;
  min_tokens?: number;
  overlap_tokens?: number;
  semantic_threshold?: number;
}

export interface ChunkResult {
  document_id: number;
  version_id: number;
  total_chunks: number;
  strategy_used: string;
  avg_tokens: number;
  min_tokens: number;
  max_tokens: number;
  processing_time_ms: number;
}

export interface ChunkItem {
  id: number;
  chunk_id: string;
  chunk_index: number;
  chunk_type: string;
  content: string;
  token_count: number;
  page_start: number;
  page_end: number;
  title_path: string;
  quality_score: number;
  status: number;
}

export interface ChunkDetail extends ChunkItem {
  document_id: number;
  version_id: number;
  enhanced_content?: string;
  created_at: string;
}

export interface ChunkParams {
  version_id?: number;
  chunk_type?: string;
  page?: number;
  page_size?: number;
}

export interface ChunkStatistics {
  total_chunks: number;
  avg_tokens: number;
  min_tokens: number;
  max_tokens: number;
  avg_length: number;
  chunk_type_distribution: Record<string, number>;
  quality_distribution: Record<string, number>;
}

// ============================================
// 向量化服务相关类型
// ============================================

export interface EncodeTextRequest {
  texts: string[];
}

export interface EncodeTextResponse {
  count: number;
  cached_count: number;
  dimension: number;
  model_name: string;
}

export interface EncodeSingleTextRequest {
  text: string;
}

export interface EncodeSingleTextResponse {
  text: string;
  dimension: number;
  cached: boolean;
  model_name: string;
}

export interface EmbedChunksRequest {
  version_id?: number;
  use_cache?: boolean;
}

export interface EmbedChunksResponse {
  document_id: number;
  version_id: number;
  total_chunks: number;
  vectorized_chunks: number;
  cached_chunks: number;
  processing_time_ms: number;
}

export interface EmbeddingSearchRequest {
  query: string;
  top_k?: number;
  document_ids?: string;
}

export interface EmbeddingSearchResult {
  chunk_id: number;
  document_id: number;
  content: string;
  score: number;
  title_path?: string;
}

export interface EmbeddingSearchResponse {
  query: string;
  top_k: number;
  total_results: number;
  results: EmbeddingSearchResult[];
}

export interface EmbeddingStatistics {
  collection_name: string;
  total_entities: number;
  dimension: number;
}

// ============================================
// 关键词索引相关类型
// ============================================

export interface KeywordIndexRequest {
  version_id?: number;
}

export interface KeywordIndexResponse {
  document_id: number;
  version_id: number;
  indexed_chunks: number;
  total_terms: number;
  processing_time_ms: number;
}

export interface BatchIndexResponse {
  total_documents: number;
  success_count: number;
  failed_count: number;
  total_chunks: number;
  total_terms: number;
  results: KeywordIndexResponse[];
}

export interface KeywordSearchRequest {
  query: string;
  top_k?: number;
  document_ids?: string;
  chunk_types?: string;
}

export interface KeywordSearchResult {
  chunk_id: number;
  document_id: number;
  content: string;
  score: number;
  matched_terms: string[];
}

export interface KeywordSearchResponse {
  query: string;
  top_k: number;
  total_results: number;
  avg_score: number;
  results: KeywordSearchResult[];
}

export interface KeywordStatistics {
  total_indexed_chunks: number;
  total_terms: number;
  avg_terms_per_chunk: number;
  top_terms: { term: string; frequency: number }[];
}

// ============================================
// 检索服务相关类型
// ============================================

export interface HybridSearchRequest {
  query: string;
  top_k?: number;
  doc_ids?: number[];
  fusion_method?: 'rrf' | 'weighted' | 'rank';
  enable_rewrite?: boolean;
  vector_top_k?: number;
  keyword_top_k?: number;
}

export interface HybridSearchResult {
  chunk: {
    chunk_id: number;
    document_id: number;
    version_id: number;
    title_path: string;
    content: string;
    score: number;
    chunk_type: string;
  };
  vector_score: number;
  keyword_score: number;
  fusion_score: number;
}

export interface HybridSearchResponse {
  query: string;
  total: number;
  results: HybridSearchResult[];
  retrieval_time_ms: number;
}

export interface VectorSearchRequest {
  query: string;
  top_k?: number;
  doc_ids?: number[];
}

export interface KeywordSearchOnlyRequest {
  query: string;
  top_k?: number;
  doc_ids?: number[];
}

export interface SuggestRequest {
  query: string;
  limit?: number;
}

export interface QueryRewriteRequest {
  query: string;
  enable_multi_query?: boolean;
  enable_subquery?: boolean;
  enable_hyde?: boolean;
  enable_background?: boolean;
  max_queries?: number;
}

export interface QueryRewriteResponse {
  original_query: string;
  normalized_query: string;
  multi_queries: string[];
  sub_queries: string[];
  hyde_answer: string | null;
  background_query: string | null;
}

export interface RetrievalStatistics {
  total_vectors: number;
  total_keywords: number;
  avg_vector_search_time_ms: number;
  avg_keyword_search_time_ms: number;
  avg_fusion_time_ms: number;
}

// ============================================
// 问答服务相关类型
// ============================================

export interface QARequest {
  question: string;
  session_id?: string;
  use_rerank?: boolean;
  top_k?: number;
  rerank_top_k?: number;
  max_context_tokens?: number;
  temperature?: number;
}

export interface QAReference {
  chunk_id: number;
  document_id: number;
  title_path: string;
  page_start: number;
  content_preview: string;
}

export interface QAResponseData {
  qa_id: number;
  question: string;
  answer: string;
  references: QAReference[];
  session_id: string;
  total_time_ms: number;
  retrieval_time_ms: number;
  rerank_time_ms: number;
  context_time_ms: number;
  generation_time_ms: number;
}

// 后端实际返回的格式是 { result: QAResponseData }
export interface QAResponse {
  result: QAResponseData;
}

export interface QAFeedbackRequest {
  qa_id: number;
  feedback: number;
  feedback_reason?: string;
  quality_score?: number;
}

export interface QAFeedbackResponse {
  success: boolean;
  message: string;
  analysis_id: number;
}

export interface QAHistoryItem {
  id: number;
  question: string;
  answer: string;
  feedback?: number;
  quality_score?: number;
  created_at: string;
}

export interface QALogItem {
  id: number;
  user_id: number;
  session_id: string;
  question: string;
  answer: string;
  feedback?: string;
  quality_score?: number;
  created_at: string;
}

export interface QALogDetail {
  id: number;
  question: string;
  answer: string;
  references: QAReference[];
  session_id?: string;
  feedback?: string;
  feedback_reason?: string;
  quality_score?: number;
  avg_retrieval_score?: number;
  retrieval_time_ms?: number;
  generation_time_ms?: number;
  total_time_ms: number;
  created_at: string;
}

// 兼容前端使用的类型别名
export type QALogDetailData = QALogDetail;

export interface QAFeedbackStatistics {
  total_count: number;
  positive_count: number;
  negative_count: number;
  positive_rate: number;
  avg_quality_score: number;
  top_issues: { category: string; count: number; percentage: number }[];
  retrieval_issue_count: number;
  generation_issue_count: number;
  pending_analysis_count: number;
  handled_count: number;
}

export interface QASession {
  id: number;
  session_id: string;
  user_id: number;
  last_question?: string;
  created_at: string;
  updated_at: string;
}

export interface QASessionParams {
  user_id?: number;
  tenant_id?: number;
  page_no?: number;
  page_size?: number;
}

export interface QAStatistics {
  total_count: number;
  avg_quality_score: number;
  helpful_count: number;
  not_helpful_count: number;
  avg_retrieval_time_ms: number;
  avg_generation_time_ms: number;
}

export interface QARule {
  id: number;
  rule_name: string;
  rule_type: string;
  rule_config: Record<string, unknown>;
  trigger_condition?: Record<string, unknown>;
  priority: number;
  enabled: boolean;
  description?: string;
  expected_effect?: string;
  created_at?: string;
  updated_at?: string;
}

export interface CreateQARuleRequest {
  rule_name: string;
  rule_type: string;
  rule_config: Record<string, unknown>;
  trigger_condition?: Record<string, unknown>;
  priority?: number;
  enabled?: boolean;
  description?: string;
  expected_effect?: string;
}

export interface QARuleParams {
  rule_type?: string;
  enabled?: boolean;
  page_no?: number;
  page_size?: number;
}

// ============================================
// 队列管理相关类型
// ============================================

export interface PublishParseTaskRequest {
  document_id: number;
  version_id: number;
  priority?: number;
  file_path: string;
  config?: Record<string, unknown>;
}

export interface PublishTaskResponse {
  task_id: string;
  queue_name: string;
  routing_key: string;
}

export interface PublishCleanTaskRequest {
  document_id: number;
  version_id: number;
  priority?: number;
  element_ids?: number[];
  config?: Record<string, unknown>;
}

export interface PublishChunkTaskRequest {
  document_id: number;
  version_id: number;
  priority?: number;
  element_ids?: number[];
  config?: Record<string, unknown>;
}

export interface PublishEmbeddingTaskRequest {
  document_id: number;
  version_id: number;
  priority?: number;
  chunk_ids?: number[];
  batch_size?: number;
}

export interface PublishIndexTaskRequest {
  document_id: number;
  version_id: number;
  priority?: number;
  chunk_ids?: number[];
  index_type?: string;
}

export interface BatchPublishRequest {
  task_type: string;
  tasks: {
    document_id: number;
    version_id: number;
    priority?: number;
  }[];
}

export interface BatchPublishResponse {
  total: number;
  success: number;
  failed: number;
  tasks: { task_id: string; success: boolean }[];
}

export interface QueueInfo {
  name: string;
  display_name: string;
}

export interface QueueStatistics {
  queue_name: string;
  message_count: number;
  consumer_count: number;
  note?: string;
}

export interface DLXMessage {
  message_id: string;
  content: string;
  created_at: string;
}

export interface DLXMessagesResponse {
  messages: DLXMessage[];
  total: number;
  note?: string;
}

// ============================================
// 枚举常量
// ============================================

/** 文档状态 */
export enum DocumentStatus {
  PendingParse = 0,    // 待解析
  Parsing = 1,         // 解析中
  Parsed = 2,          // 已解析
  ParseFailed = 3,     // 解析失败
  Cleaned = 4,         // 已清洗
  Chunked = 5,         // 已切分
  Vectorized = 6,      // 已向量化
  Deleted = 9          // 已删除
}

/** 文档状态映射 */
export const DocumentStatusMap: Record<number, string> = {
  [DocumentStatus.PendingParse]: '待解析',
  [DocumentStatus.Parsing]: '解析中',
  [DocumentStatus.Parsed]: '已解析',
  [DocumentStatus.ParseFailed]: '解析失败',
  [DocumentStatus.Cleaned]: '已清洗',
  [DocumentStatus.Chunked]: '已切分',
  [DocumentStatus.Vectorized]: '已向量化',
  [DocumentStatus.Deleted]: '已删除'
};

/** 任务状态 */
export enum TaskStatus {
  Pending = 'pending',
  Running = 'running',
  Completed = 'completed',
  Failed = 'failed',
  Retry = 'retry'
}

/** 任务状态映射 */
export const TaskStatusMap: Record<string, string> = {
  [TaskStatus.Pending]: '等待中',
  [TaskStatus.Running]: '执行中',
  [TaskStatus.Completed]: '已完成',
  [TaskStatus.Failed]: '失败',
  [TaskStatus.Retry]: '重试中'
};

/** 任务类型 */
export const TaskTypeMap: Record<string, string> = {
  'import': '导入任务',
  'parse': '解析任务',
  'clean': '清洗任务',
  'chunk': '切分任务',
  'embed': '向量化任务',
  'index': '索引任务'
};

/** Chunk类型 */
export const ChunkTypeMap: Record<string, string> = {
  'paragraph': '段落',
  'title': '标题',
  'table': '表格',
  'image': '图片',
  'chart': '图表',
  'list': '列表',
  'code': '代码',
  'header': '页眉',
  'footer': '页脚'
};

/** 质量标记 */
export const QualityFlagMap: Record<string, { label: string; color: string }> = {
  'good': { label: '良好', color: 'success' },
  'warning': { label: '警告', color: 'warning' },
  'bad': { label: '差', color: 'error' }
};
