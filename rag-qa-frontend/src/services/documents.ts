import { request, apiClient } from './api';
import type {
  ApiResponse,
  PaginatedResponse,
  DocumentUploadResponse,
  BatchUploadResponse,
  DocumentItem,
  DocumentDetail,
  DocumentListParams,
  DocumentVersion,
  VersionDetail
} from '../types/api';

/**
 * 文档管理服务 - 符合API文档
 * Base URL: /api/v1/documents
 */

// 单文件上传 - multipart/form-data
export const uploadDocument = async (formData: FormData): Promise<ApiResponse<DocumentUploadResponse>> => {
  const response = await apiClient.request<ApiResponse<DocumentUploadResponse>>({
    method: 'POST',
    url: '/documents/upload',
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

// 批量上传
export const batchUploadDocuments = async (formData: FormData): Promise<ApiResponse<BatchUploadResponse>> => {
  const response = await apiClient.request<ApiResponse<BatchUploadResponse>>({
    method: 'POST',
    url: '/documents/batch-upload',
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

// 文档列表
export const getDocuments = async (
  params?: DocumentListParams
): Promise<ApiResponse<PaginatedResponse<DocumentItem>>> => {
  return request<PaginatedResponse<DocumentItem>>('GET', '/documents', undefined, params as Record<string, unknown>);
};

// 文档详情
export const getDocumentDetail = async (
  documentId: number
): Promise<ApiResponse<DocumentDetail>> => {
  return request<DocumentDetail>('GET', `/documents/${documentId}`);
};

// 删除文档
export const deleteDocument = async (
  documentId: number
): Promise<ApiResponse<null>> => {
  return request<null>('DELETE', `/documents/${documentId}`);
};

// 版本列表
export const getDocumentVersions = async (
  documentId: number
): Promise<ApiResponse<{ items: DocumentVersion[] }>> => {
  return request<{ items: DocumentVersion[] }>('GET', `/documents/${documentId}/versions`);
};

// 版本详情
export const getVersionDetail = async (
  documentId: number,
  versionId: number
): Promise<ApiResponse<VersionDetail>> => {
  return request<VersionDetail>('GET', `/documents/${documentId}/versions/${versionId}`);
};

// 系统初始化（清空所有数据）
export interface InitializeResult {
  documents_deleted: number;
  versions_deleted: number;
  chunks_deleted: number;
  keyword_indexes_deleted: number;
  tasks_deleted: number;
  qa_logs_deleted: number;
  feedback_analysis_deleted: number;
  optimization_rules_deleted: number;
  milvus_entities_deleted: string | number;
  files_deleted: number;
  errors: string[];
}

export const initializeSystem = async (): Promise<ApiResponse<InitializeResult>> => {
  return request<InitializeResult>('POST', '/documents/initialize');
};
