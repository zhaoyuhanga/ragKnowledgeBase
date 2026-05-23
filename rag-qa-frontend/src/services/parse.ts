import { request } from './api';
import type {
  ApiResponse,
  PaginatedResponse,
  ImportTaskItem,
  ImportTaskDetail,
  ImportTaskParams,
  ParseTaskResponse,
  ParseStatus,
  ParseElement,
  ElementDetail,
  ElementListParams
} from '../types/api';

/**
 * 导入任务服务 - 符合API文档
 * Base URL: /api/v1/import-tasks
 */

// 任务详情
export const getImportTaskDetail = async (
  taskId: string
): Promise<ApiResponse<ImportTaskDetail>> => {
  return request<ImportTaskDetail>('GET', `/import-tasks/${taskId}`);
};

// 任务列表
export const getImportTasks = async (
  params?: ImportTaskParams
): Promise<ApiResponse<PaginatedResponse<ImportTaskItem>>> => {
  return request<PaginatedResponse<ImportTaskItem>>('GET', '/import-tasks', undefined, params as Record<string, unknown>);
};

/**
 * 文档解析服务 - 符合API文档
 * Base URL: /api/v1/documents
 */

// 触发文档解析
export const triggerParse = async (
  documentId: number,
  versionId?: number
): Promise<ApiResponse<ParseTaskResponse>> => {
  return request<ParseTaskResponse>('POST', `/documents/${documentId}/parse`, { version_id: versionId });
};

// 查询解析状态
export const getParseStatus = async (
  documentId: number
): Promise<ApiResponse<ParseStatus>> => {
  return request<ParseStatus>('GET', `/documents/${documentId}/parse-status`);
};

// 获取解析元素列表
export const getElements = async (
  documentId: number,
  params?: ElementListParams
): Promise<ApiResponse<PaginatedResponse<ParseElement>>> => {
  return request<PaginatedResponse<ParseElement>>(
    'GET',
    `/documents/${documentId}/elements`,
    undefined,
    params as Record<string, unknown>
  );
};

// 获取元素详情
export const getElementDetail = async (
  documentId: number,
  elementId: string
): Promise<ApiResponse<ElementDetail>> => {
  return request<ElementDetail>('GET', `/documents/${documentId}/elements/${elementId}`);
};

// 重新解析文档
export const reparseDocument = async (
  documentId: number
): Promise<ApiResponse<ParseTaskResponse>> => {
  return request<ParseTaskResponse>('POST', `/documents/${documentId}/reparse`);
};
