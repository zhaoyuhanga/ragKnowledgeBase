// API ????
export interface ApiResponse<T = any> {
  success: boolean
  message: string
  code: number
  data: T
}

// ????
export interface Document {
  id: number
  filename: string
  file_type: string
  file_size: number
  status: number
  chunk_count: number
  created_at: string
  updated_at: string
  // AI ??????
  source_type?: 'local' | 'ai_generated'
  generated_from_question?: string
  generated_at?: string
  llm_model?: string
  llm_provider?: string
}

// ??????
export interface DocumentListResponse {
  items: Document[]
  total: number
  page: number
  page_size: number
}

// ????
export interface QARequest {
  question: string
  top_k?: number
  search_mode?: 'local' | 'ai_generated' | 'all'
  enable_ai_extend?: boolean
}

// ????
export interface QAResponse {
  answer: string
  sources: SourceItem[]
  cache_hit: boolean
  response_time_ms: number
  error?: string
  ai_extend?: boolean
  ai_doc_id?: number
}

// ???
export interface SourceItem {
  chunk_id: number
  document_id: number
  filename: string
  content: string
  similarity: number
  source_type?: 'local' | 'ai_generated'
}

// ????
export interface QAHistory {
  id: number
  question: string
  answer: string
  referenced_chunks: string[]
  response_time_ms: number
  cache_hit: boolean
  source_type: 'local' | 'ai_generated'
  session_id: string
  created_at: string
}

// ?????
export interface KnowledgeStats {
  total_documents: number
  total_chunks: number
  collection_size: number
  last_updated: string
}

// ????
export interface SystemStats {
  total_queries: number
  today_queries: number
  total_documents: number
  total_chunks: number
  cache_hit_rate: number
  avg_response_time: number
}

// ????
export interface SystemConfig {
  deepseek_model: string
  embedding_model: string
  chunk_size: number
  chunk_overlap: number
  top_k: number
  temperature: number
  max_tokens: number
}

// ????
export interface UploadResponse {
  id: number
  filename: string
  file_type: string
  file_size: number
  status: number
}
