import { request } from './api';
import type {
  ApiResponse,
  HybridSearchRequest,
  HybridSearchResponse,
  VectorSearchRequest,
  KeywordSearchOnlyRequest,
  SuggestRequest,
  QueryRewriteRequest,
  QueryRewriteResponse,
  RetrievalStatistics
} from '../types/api';

/**
 * 检索服务 - 符合API文档
 * Base URL: /api/v1/retrieval
 */

// 混合检索
export const hybridSearch = async (
  params: HybridSearchRequest
): Promise<ApiResponse<HybridSearchResponse>> => {
  return request<HybridSearchResponse>('POST', '/retrieval/hybrid', params);
};

// 向量检索
export const vectorSearch = async (
  params: VectorSearchRequest
): Promise<ApiResponse<unknown[]>> => {
  return request<unknown[]>('POST', '/retrieval/vector', params);
};

// 关键词检索
export const keywordSearchOnly = async (
  params: KeywordSearchOnlyRequest
): Promise<ApiResponse<unknown[]>> => {
  return request<unknown[]>('POST', '/retrieval/keyword', params);
};

// 检索建议
export const getRetrievalSuggest = async (
  params: SuggestRequest
): Promise<ApiResponse<string[]>> => {
  return request<string[]>('GET', '/retrieval/suggest', undefined, params as unknown as Record<string, unknown>);
};

// 查询改写
export const rewriteQuery = async (
  params: QueryRewriteRequest
): Promise<ApiResponse<QueryRewriteResponse>> => {
  return request<QueryRewriteResponse>('POST', '/retrieval/rewrite', params);
};

// 融合测试
export const testFusion = async (
  data: {
    vector_results: unknown[];
    keyword_results: unknown[];
    method: string;
    rrf_k?: number;
    vector_weight?: number;
    keyword_weight?: number;
  }
): Promise<ApiResponse<unknown[]>> => {
  return request<unknown[]>('POST', '/retrieval/fusion', data);
};

// 获取检索统计
export const getRetrievalStatistics = async (): Promise<ApiResponse<RetrievalStatistics>> => {
  return request<RetrievalStatistics>('GET', '/retrieval/statistics');
};
