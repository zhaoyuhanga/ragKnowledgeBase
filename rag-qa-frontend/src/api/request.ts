import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '@/router'

const API_BASE_URL = '/api/v1'

const request = axios.create({
  baseURL: API_BASE_URL,
  timeout: 120000
})

// 请求拦截器
request.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
request.interceptors.response.use(
  (response) => {
    const res = response.data
    // 后端使用 success 字段表示成功/失败
    if (res.success === false) {
      ElMessage.error(res.message || '请求失败')
      return Promise.reject(new Error(res.message || '请求失败'))
    }
    // 返回完整的响应数据
    return res
  },
  (error) => {
    // 统一处理401未授权
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      const currentPath = router.currentRoute.value.fullPath
      if (currentPath !== '/login') {
        router.push(`/login?redirect=${encodeURIComponent(currentPath)}`)
        ElMessage.warning('登录已过期，请重新登录')
      }
      return Promise.reject(error)
    }
    const message = error.response?.data?.message || error.message || '网络错误'
    ElMessage.error(message)
    return Promise.reject(error)
  }
)

export default request
