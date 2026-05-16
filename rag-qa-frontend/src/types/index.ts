// API 响应类型
export interface ApiResponse<T = any> {
  success: boolean
  message: string
  code: number
  data: T
}

// 文档类型
export interface Document {
  id: number
  filename: string  // 后端返回的是 filename，不�?title
  file_type: string
  file_size: number
  status: number  // 后端返回的是数字: 0=处理�? 1=已完�? 2=失败
  chunk_count: number
  created_at: string
  updated_at: string
}

// 文档列表响应
export interface DocumentListResponse {
  items: Document[]
  total: number
  page: number
  page_size: number
}

// 问答请求
export interface QARequest {
  question: string
  top_k?: number
}

// 问答响应
export interface QAResponse {
  answer: string
  sources: SourceItem[]
  cache_hit: boolean
  response_time_ms: number
  error?: string
}

// 来源�?
export interface SourceItem {
  chunk_id: number
  document_id: number
  filename: string
  content: string
  similarity: number
}

// 问答历史
export interface QAHistory {
  id: number
  question: string
  answer: string
  referenced_chunks: string[]
  response_time_ms: number
  cache_hit: boolean
  session_id: string
  created_at: string
}

// 知识库统�?
export interface KnowledgeStats {
  total_documents: number
  total_chunks: number
  collection_size: number
  last_updated: string
}

// 系统统计
export interface SystemStats {
  total_queries: number
  today_queries: number
  total_documents: number
  total_chunks: number
  cache_hit_rate: number
  avg_response_time: number
}

// 系统配置
export interface SystemConfig {
  deepseek_model: string
  embedding_model: string
  chunk_size: number
  chunk_overlap: number
  top_k: number
  temperature: number
  max_tokens: number
}

// 上传响应
export interface UploadResponse {
  id: number
  filename: string
  file_type: string
  file_size: number
  status: number
}
