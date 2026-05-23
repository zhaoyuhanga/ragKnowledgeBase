import { request } from './api';
import type {
  ApiResponse,
  HealthStatus,
  ComponentHealth
} from '../types/api';

/**
 * 健康检查服务 - 符合API文档
 * Base URL: /api/v1
 */

// 系统整体健康状态
export const getHealth = async (): Promise<ApiResponse<HealthStatus>> => {
  return request<HealthStatus>('GET', '/health');
};

// 数据库健康状态
export const getHealthDb = async (): Promise<ApiResponse<ComponentHealth>> => {
  return request<ComponentHealth>('GET', '/health/db');
};

// Redis健康状态
export const getHealthRedis = async (): Promise<ApiResponse<ComponentHealth>> => {
  return request<ComponentHealth>('GET', '/health/redis');
};

// Milvus健康状态
export const getHealthMilvus = async (): Promise<ApiResponse<ComponentHealth>> => {
  return request<ComponentHealth>('GET', '/health/milvus');
};

// RabbitMQ健康状态
export const getHealthRabbitmq = async (): Promise<ApiResponse<ComponentHealth>> => {
  return request<ComponentHealth>('GET', '/health/rabbitmq');
};

// 批量获取所有健康状态
export const getAllHealthStatus = async () => {
  const [health, db, redis, milvus, rabbitmq] = await Promise.all([
    getHealth(),
    getHealthDb(),
    getHealthRedis(),
    getHealthMilvus(),
    getHealthRabbitmq()
  ]);
  return { health, db, redis, milvus, rabbitmq };
};
