import request from './request'
import type {
  ApiResponse,
  Document,
  DocumentListResponse,
  QARequest,
  QAResponse,
  QAHistory,
  KnowledgeStats,
  SystemStats,
  SystemConfig,
  UploadResponse
} from '@/types'

// ==================== 文档管理 ====================

// 获取文档列表
export const getDocuments = (params: {
  page?: number
  page_size?: number
  status?: string
}) => {
  return request.get<ApiResponse<DocumentListResponse>>('/documents', { params })
}

// 获取单个文档详情
export const getDocument = (id: number) => {
  return request.get<ApiResponse<Document>>(`/documents/${id}`)
}

// 上传文档
export const uploadDocument = (formData: FormData) => {
  return request.post<ApiResponse<UploadResponse>>('/documents/upload', formData)
}

// 删除文档
export const deleteDocument = (id: number) => {
  return request.delete<ApiResponse<null>>(`/documents/${id}`)
}

// 预览文档内容
export const previewDocument = (id: number) => {
  return request.get<ApiResponse<{ content: string }>>(`/documents/${id}/preview`)
}

// ==================== 问答系统 ====================

// 提交问答请求
export const askQuestion = (data: QARequest) => {
  return request.post<ApiResponse<QAResponse>>('/qa/ask', data)
}

// 获取问答历史
export const getQAHistory = (params: {
  page?: number
  page_size?: number
}) => {
  return request.get<ApiResponse<{ items: QAHistory[]; total: number }>>('/qa/history', { params })
}

// ==================== 知识库管理 ====================

// 获取知识库统计
export const getKnowledgeStats = () => {
  return request.get<ApiResponse<KnowledgeStats>>('/knowledge/stats')
}

// 重建知识库索引
export const rebuildKnowledgeBase = () => {
  return request.post<ApiResponse<null>>('/knowledge/rebuild')
}

// 检索知识库
export const searchKnowledge = (query: string, top_k?: number) => {
  return request.post<ApiResponse<{ query: string; results: any[]; total: number }>>('/knowledge/chunks/search', {
    query,
    top_k
  })
}

// 清除缓存
export const clearCache = () => {
  return request.delete<ApiResponse<null>>('/knowledge/cache/clear')
}


// ==================== 认证 ====================

// 登录
export const login = (data: { username: string; password: string }) => {
  return request.post<ApiResponse<{ token: string }>>('/auth/login', data)
}
// ==================== 系统管理 ====================

// 健康检查
export const healthCheck = () => {
  return request.get<ApiResponse<{ status: string }>>('/system/health')
}

// 获取系统统计
export const getSystemStats = () => {
  return request.get<ApiResponse<SystemStats>>('/system/stats')
}

// 获取系统配置
export const getSystemConfig = () => {
  return request.get<ApiResponse<SystemConfig>>('/system/config')
}

// 更新系统运行时配置
export const updateSystemConfig = (config: {
  retrieval_top_k?: number
  similarity_threshold?: number
  deepseek_model?: string
  chunk_size?: number
  chunk_overlap?: number
}) => {
  return request.post<ApiResponse<any>>('/system/config', config)
}

// 获取运行时配置
export const getRuntimeConfig = () => {
  return request.get<ApiResponse<any>>('/system/config/runtime')
}

// ==================== 系统配置管理（数据库） ====================

// 获取所有系统配置
export const getConfigs = () => {
  return request.get<ApiResponse<any[]>>('/system/configs')
}

// 获取配置分组
export const getConfigGroups = () => {
  return request.get<ApiResponse<any[]>>('/system/configs/groups')
}

// 获取分组后的配置
export const getGroupedConfigs = () => {
  return request.get<ApiResponse<any>>('/system/configs/grouped')
}

// 获取单个配置
export const getConfig = (key: string) => {
  return request.get<ApiResponse<any>>(`/system/configs/${key}`)
}

// 更新配置
export const updateConfig = (key: string, value: string) => {
  return request.put<ApiResponse<any>>(`/system/configs/${key}`, { value })
}

// 批量更新配置
export const batchUpdateConfigs = (configs: Record<string, any>) => {
  return request.post<ApiResponse<any>>('/system/configs/batch', { configs })
}

// 初始化默认配置
export const initializeConfigs = () => {
  return request.post<ApiResponse<{ count: number }>>('/system/configs/initialize')
}

