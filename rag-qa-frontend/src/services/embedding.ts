import { request } from './api';
import type {
  ApiResponse,
  EncodeTextResponse,
  EncodeSingleTextResponse,
  EmbedChunksResponse,
  EmbeddingSearchRequest,
  EmbeddingSearchResponse,
  EmbeddingStatistics
} from '../types/api';

/**
 * 向量化服务 - 符合API文档
 * Base URL: /api/v1/embedding
 */

// 批量文本向量化
export const encodeTexts = async (
  texts: string[]
): Promise<ApiResponse<EncodeTextResponse>> => {
  return request<EncodeTextResponse>('POST', '/embedding/encode', texts);
};

// 单个文本向量化
export const encodeSingleText = async (
  text: string
): Promise<ApiResponse<EncodeSingleTextResponse>> => {
  return request<EncodeSingleTextResponse>('POST', '/embedding/encode/single', text);
};

// 向量化文档Chunks
export const embedChunks = async (
  documentId: number,
  versionId?: number,
  useCache?: boolean
): Promise<ApiResponse<EmbedChunksResponse>> => {
  return request<EmbedChunksResponse>('POST', `/embedding/chunks/${documentId}`, {
    version_id: versionId,
    use_cache: useCache ?? true
  });
};

// 向量检索
export const embeddingSearch = async (
  params: EmbeddingSearchRequest
): Promise<ApiResponse<EmbeddingSearchResponse>> => {
  return request<EmbeddingSearchResponse>('POST', '/embedding/search', params);
};

// 删除文档向量
export const deleteDocumentVectors = async (
  documentId: number,
  versionId?: number
): Promise<ApiResponse<{ deleted_count: number }>> => {
  return request<{ deleted_count: number }>('DELETE', `/embedding/chunks/${documentId}`, undefined, {
    version_id: versionId
  });
};

// 获取向量统计
export const getEmbeddingStatistics = async (): Promise<ApiResponse<EmbeddingStatistics>> => {
  return request<EmbeddingStatistics>('GET', '/embedding/statistics');
};

// 初始化向量集合
export const initializeEmbedding = async (): Promise<ApiResponse<null>> => {
  return request<null>('POST', '/embedding/initialize');
};
