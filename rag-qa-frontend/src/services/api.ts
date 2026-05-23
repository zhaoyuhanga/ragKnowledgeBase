import axios, { AxiosInstance, AxiosError } from 'axios';
import type { ApiResponse, ApiErrorResponse } from '../types/api';

// API Base URL
const BASE_URL = '/api/v1';

// 创建Axios实例
const apiClient: AxiosInstance = axios.create({
  baseURL: BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器
apiClient.interceptors.request.use(
  (config) => {
    // 添加认证token等
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 响应拦截器
apiClient.interceptors.response.use(
  (response) => {
    return response;
  },
  (error: AxiosError<ApiErrorResponse>) => {
    if (error.response) {
      const { data } = error.response;
      console.error('API Error:', data);
      
      // 处理业务错误
      if (data?.code && data.code.startsWith('AUTH_')) {
        // 认证错误，跳转登录
        window.location.href = '/login';
      }
    } else if (error.request) {
      console.error('Network Error: No response received');
    } else {
      console.error('Request Error:', error.message);
    }
    return Promise.reject(error);
  }
);

// 通用请求方法
export const request = async <T>(
  method: 'GET' | 'POST' | 'PUT' | 'DELETE',
  url: string,
  data?: unknown,
  params?: Record<string, unknown>
): Promise<ApiResponse<T>> => {
  const response = await apiClient.request<ApiResponse<T>>({
    method,
    url,
    data,
    params,
  });
  return response.data;
};

// 导出实例供直接使用
export { apiClient, BASE_URL };
