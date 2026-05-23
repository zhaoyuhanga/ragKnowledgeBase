import { request } from './api';
import type {
  ApiResponse,
  PaginatedResponse,
  QARequest,
  QAResponse,
  QAResponseData,
  QAFeedbackRequest,
  QAFeedbackResponse,
  QAHistoryItem,
  QALogItem,
  QALogDetail,
  QAFeedbackStatistics,
  QASession,
  QASessionParams,
  QAStatistics,
  QARule,
  CreateQARuleRequest,
  QARuleParams
} from '../types/api';

/**
 * 问答服务 - 符合API文档
 * Base URL: /api/v1/qa
 */

// 问答接口
export const askQuestion = async (
  params: QARequest
): Promise<ApiResponse<QAResponse>> => {
  return request<QAResponse>('POST', '/qa', params);
};

// 流式问答接口
export const askQuestionStream = async (
  params: QARequest
): Promise<Response> => {
  const response = await fetch(`${API_BASE_URL}/qa/stream`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(params),
  });
  return response;
};

// 提交反馈
export const submitFeedback = async (
  params: QAFeedbackRequest
): Promise<ApiResponse<QAFeedbackResponse>> => {
  return request<QAFeedbackResponse>('POST', '/qa/feedback', params);
};

// 查询会话历史
export const getQAHistory = async (
  sessionId: string,
  pageNo?: number,
  pageSize?: number
): Promise<ApiResponse<PaginatedResponse<QAHistoryItem>>> => {
  return request<PaginatedResponse<QAHistoryItem>>(
    'GET',
    '/qa/history',
    undefined,
    {
      session_id: sessionId,
      page_no: pageNo,
      page_size: pageSize
    }
  );
};

// 查询问答日志
export const getQALogs = async (
  params: {
    tenant_id?: number;
    user_id?: number;
    session_id?: string;
    start_date?: string;
    end_date?: string;
    has_feedback?: boolean;
    feedback_value?: number;
    min_score?: number;
    max_score?: number;
    keyword?: string;
    page_no?: number;
    page_size?: number;
  }
): Promise<ApiResponse<PaginatedResponse<QALogItem>>> => {
  return request<PaginatedResponse<QALogItem>>('GET', '/qa/logs', undefined, params);
};

// 获取问答日志详情
export const getQALogDetail = async (
  qaId: number
): Promise<ApiResponse<QALogDetail>> => {
  return request<QALogDetail>('GET', `/qa/logs/${qaId}`);
};

// 获取反馈统计
export const getFeedbackStatistics = async (
  tenantId?: number,
  startDate?: string,
  endDate?: string
): Promise<ApiResponse<QAFeedbackStatistics>> => {
  return request<QAFeedbackStatistics>('GET', '/qa/feedback/statistics', undefined, {
    tenant_id: tenantId,
    start_date: startDate,
    end_date: endDate
  });
};

// 查询会话列表
export const getQASessions = async (
  params?: QASessionParams
): Promise<ApiResponse<PaginatedResponse<QASession>>> => {
  return request<PaginatedResponse<QASession>>('GET', '/qa/sessions', undefined, params as Record<string, unknown>);
};

// 获取问答统计
export const getQAStatistics = async (
  tenantId?: number,
  startDate?: string,
  endDate?: string
): Promise<ApiResponse<QAStatistics>> => {
  return request<QAStatistics>('GET', '/qa/statistics', undefined, {
    tenant_id: tenantId,
    start_date: startDate,
    end_date: endDate
  });
};

// 创建优化规则
export const createQARule = async (
  data: CreateQARuleRequest
): Promise<ApiResponse<QARule>> => {
  return request<QARule>('POST', '/qa/rules', data);
};

// 查询优化规则
export const getQARules = async (
  params?: QARuleParams
): Promise<ApiResponse<PaginatedResponse<QARule>>> => {
  return request<PaginatedResponse<QARule>>('GET', '/qa/rules', undefined, params as Record<string, unknown>);
};

// 更新优化规则
export const updateQARule = async (
  ruleId: number,
  data: CreateQARuleRequest
): Promise<ApiResponse<QARule>> => {
  return request<QARule>('PUT', `/qa/rules/${ruleId}`, data);
};

// 删除优化规则
export const deleteQARule = async (
  ruleId: number
): Promise<ApiResponse<null>> => {
  return request<null>('DELETE', `/qa/rules/${ruleId}`);
};
