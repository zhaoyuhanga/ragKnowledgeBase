import { request } from './api';
import type {
  ApiResponse,
  PublishParseTaskRequest,
  PublishTaskResponse,
  PublishCleanTaskRequest,
  PublishChunkTaskRequest,
  PublishEmbeddingTaskRequest,
  PublishIndexTaskRequest,
  BatchPublishRequest,
  BatchPublishResponse,
  QueueInfo,
  QueueStatistics,
  DLXMessagesResponse
} from '../types/api';

/**
 * 队列管理服务 - 符合API文档
 * Base URL: /api/v1/queue
 */

// 发布解析任务
export const publishParseTask = async (
  data: PublishParseTaskRequest
): Promise<ApiResponse<PublishTaskResponse>> => {
  return request<PublishTaskResponse>('POST', '/queue/publish/parse', data);
};

// 发布清洗任务
export const publishCleanTask = async (
  data: PublishCleanTaskRequest
): Promise<ApiResponse<PublishTaskResponse>> => {
  return request<PublishTaskResponse>('POST', '/queue/publish/clean', data);
};

// 发布切分任务
export const publishChunkTask = async (
  data: PublishChunkTaskRequest
): Promise<ApiResponse<PublishTaskResponse>> => {
  return request<PublishTaskResponse>('POST', '/queue/publish/chunk', data);
};

// 发布向量化任务
export const publishEmbeddingTask = async (
  data: PublishEmbeddingTaskRequest
): Promise<ApiResponse<PublishTaskResponse>> => {
  return request<PublishTaskResponse>('POST', '/queue/publish/embedding', data);
};

// 发布索引任务
export const publishIndexTask = async (
  data: PublishIndexTaskRequest
): Promise<ApiResponse<PublishTaskResponse>> => {
  return request<PublishTaskResponse>('POST', '/queue/publish/index', data);
};

// 批量发布任务
export const batchPublishTasks = async (
  data: BatchPublishRequest
): Promise<ApiResponse<BatchPublishResponse>> => {
  return request<BatchPublishResponse>('POST', '/queue/publish/batch', data);
};

// 获取队列列表
export const getQueues = async (): Promise<ApiResponse<{ queues: QueueInfo[] }>> => {
  return request<{ queues: QueueInfo[] }>('GET', '/queue/queues');
};

// 获取队列统计
export const getQueueStats = async (
  queueName: string
): Promise<ApiResponse<QueueStatistics>> => {
  return request<QueueStatistics>('GET', `/queue/queues/${queueName}/stats`);
};

// 获取死信队列消息
export const getDLXMessages = async (
  limit?: number,
  offset?: number
): Promise<ApiResponse<DLXMessagesResponse>> => {
  return request<DLXMessagesResponse>('GET', '/queue/dlx/messages', undefined, {
    limit,
    offset
  });
};

// 删除死信消息
export const deleteDLXMessage = async (
  messageId: string
): Promise<ApiResponse<{ message_id: string; deleted: boolean }>> => {
  return request<{ message_id: string; deleted: boolean }>('DELETE', `/queue/dlx/messages/${messageId}`);
};

// 清空死信队列
export const clearDLXMessages = async (): Promise<ApiResponse<{ cleared: boolean; note: string }>> => {
  return request<{ cleared: boolean; note: string }>('DELETE', '/queue/dlx/messages');
};
