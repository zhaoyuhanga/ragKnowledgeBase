import { request } from './api';
import type {
  ApiResponse,
  KeywordIndexRequest,
  KeywordIndexResponse,
  BatchIndexResponse,
  KeywordSearchRequest,
  KeywordSearchResponse,
  KeywordStatistics
} from '../types/api';

/**
 * 关键词索引服务 - 符合API文档
 * Base URL: /api/v1/keyword
 */

// 构建关键词索引
export const buildKeywordIndex = async (
  documentId: number,
  versionId?: number
): Promise<ApiResponse<KeywordIndexResponse>> => {
  return request<KeywordIndexResponse>('POST', `/keyword/index/${documentId}`, {
    version_id: versionId
  } as KeywordIndexRequest);
};

// 批量构建关键词索引
export const batchBuildKeywordIndex = async (
  documentIds: number[]
): Promise<ApiResponse<BatchIndexResponse>> => {
  return request<BatchIndexResponse>('POST', '/keyword/index/batch', documentIds);
};

// 关键词检索
export const keywordSearch = async (
  params: KeywordSearchRequest
): Promise<ApiResponse<KeywordSearchResponse>> => {
  return request<KeywordSearchResponse>('POST', '/keyword/search', params);
};

// 获取索引统计
export const getKeywordStatistics = async (): Promise<ApiResponse<KeywordStatistics>> => {
  return request<KeywordStatistics>('GET', '/keyword/statistics');
};
