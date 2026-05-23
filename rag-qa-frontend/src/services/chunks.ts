import { request } from './api';
import type {
  ApiResponse,
  PaginatedResponse,
  ChunkConfig,
  ChunkResult,
  ChunkItem,
  ChunkDetail,
  ChunkParams,
  ChunkStatistics
} from '../types/api';

/**
 * 切分服务 - 符合API文档
 * Base URL: /api/v1/chunks
 */

// 切分文档
export const chunkDocument = async (
  documentId: number,
  versionId?: number,
  config?: ChunkConfig
): Promise<ApiResponse<ChunkResult>> => {
  return request<ChunkResult>('POST', `/chunks/documents/${documentId}`, {
    version_id: versionId,
    config
  });
};

// 批量切分文档
export const batchChunkDocuments = async (
  documentIds: number[],
  config?: ChunkConfig
): Promise<ApiResponse<ChunkResult>> => {
  return request<ChunkResult>('POST', '/chunks/documents/batch', {
    document_ids: documentIds,
    config
  });
};

// 获取Chunk列表
export const getChunks = async (
  documentId: number,
  params?: ChunkParams
): Promise<ApiResponse<PaginatedResponse<ChunkItem>>> => {
  return request<PaginatedResponse<ChunkItem>>(
    'GET',
    `/chunks/documents/${documentId}`,
    undefined,
    params as Record<string, unknown>
  );
};

// 获取Chunk详情
export const getChunkDetail = async (
  chunkId: number
): Promise<ApiResponse<ChunkDetail>> => {
  return request<ChunkDetail>('GET', `/chunks/${chunkId}`);
};

// 获取切分统计
export const getChunkStatistics = async (
  documentId: number
): Promise<ApiResponse<ChunkStatistics>> => {
  return request<ChunkStatistics>('GET', `/chunks/documents/${documentId}/statistics`);
};
