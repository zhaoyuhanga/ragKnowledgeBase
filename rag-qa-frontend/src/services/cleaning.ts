import { request } from './api';
import type {
  ApiResponse,
  PaginatedResponse,
  CleaningRule,
  CreateCleaningRuleRequest,
  CleaningRuleParams,
  CleaningResult,
  BatchCleaningResult,
  CleaningLog,
  CleaningLogParams
} from '../types/api';

/**
 * 清洗服务 - 符合API文档
 * Base URL: /api/v1/cleaning
 */

// 创建清洗规则
export const createCleaningRule = async (
  data: CreateCleaningRuleRequest
): Promise<ApiResponse<CleaningRule>> => {
  return request<CleaningRule>('POST', '/cleaning/rules', data);
};

// 更新清洗规则
export const updateCleaningRule = async (
  ruleId: number,
  data: CreateCleaningRuleRequest
): Promise<ApiResponse<CleaningRule>> => {
  return request<CleaningRule>('PUT', `/cleaning/rules/${ruleId}`, data);
};

// 删除清洗规则
export const deleteCleaningRule = async (
  ruleId: number
): Promise<ApiResponse<null>> => {
  return request<null>('DELETE', `/cleaning/rules/${ruleId}`);
};

// 获取清洗规则列表
export const getCleaningRules = async (
  params?: CleaningRuleParams
): Promise<ApiResponse<PaginatedResponse<CleaningRule>>> => {
  return request<PaginatedResponse<CleaningRule>>('GET', '/cleaning/rules', undefined, params as Record<string, unknown>);
};

// 清洗文档
export const cleanDocument = async (
  documentId: number,
  versionId?: number,
  config?: Record<string, unknown>
): Promise<ApiResponse<CleaningResult>> => {
  return request<CleaningResult>('POST', `/cleaning/documents/${documentId}`, {
    version_id: versionId,
    config
  });
};

// 批量清洗文档
export const batchCleanDocuments = async (
  documentIds: number[],
  config?: Record<string, unknown>
): Promise<ApiResponse<BatchCleaningResult>> => {
  return request<BatchCleaningResult>('POST', '/cleaning/documents/batch', {
    document_ids: documentIds,
    config
  });
};

// 获取清洗日志
export const getCleaningLogs = async (
  params: CleaningLogParams
): Promise<ApiResponse<PaginatedResponse<CleaningLog>>> => {
  return request<PaginatedResponse<CleaningLog>>('GET', '/cleaning/logs', undefined, params as unknown as Record<string, unknown>);
};
