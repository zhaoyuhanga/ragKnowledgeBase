# 前端技术面试题

## 目录

1. [Vue 3 核心特性](#1-vue-3-核心特性)
2. [TypeScript 类型系统](#2-typescript-类型系统)
3. [Vue Router 路由管理](#3-vue-router-路由管理)
4. [Pinia 状态管理](#4-pinia-状态管理)
5. [Axios HTTP 请求](#5-axios-http-请求)
6. [Element Plus 组件库](#6-element-plus-组件库)
7. [Vite 构建工具](#7-vite-构建工具)

---

## 1. Vue 3 核心特性

### 问题 1：Vue 3 中的 Composition API 相比 Options API 有什么优势？

**答案：**

**Options API（传统方式）：**

```vue
<template>
  <div>{{ message }}</div>
  <button @click="increment">点击次数: {{ count }}</button>
</template>

<script>
export default {
  data() {
    return {
      message: 'Hello Vue',
      count: 0
    }
  },
  methods: {
    increment() {
      this.count++
    }
  },
  computed: {
    doubleCount() {
      return this.count * 2
    }
  },
  watch: {
    count(newVal) {
      console.log(`count 变化: ${newVal}`)
    }
  }
}
</script>
```

**Composition API（组合式 API）：**

```vue
<template>
  <div>{{ message }}</div>
  <button @click="increment">点击次数: {{ count }}</button>
  <div>双倍: {{ doubleCount }}</div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'

// 响应式状态
const message = ref('Hello Vue')
const count = ref(0)

// 方法
const increment = () => {
  count.value++
}

// 计算属性
const doubleCount = computed(() => count.value * 2)

// 监听器
watch(count, (newVal) => {
  console.log(`count 变化: ${newVal}`)
})
</script>
```

**Composition API 的优势：**

| 特性 | Options API | Composition API |
|------|-------------|----------------|
| 代码组织 | 按选项类型分散 | 按逻辑功能聚合 |
| 逻辑复用 | Mixins（不推荐） | Composables（推荐） |
| 类型推导 | 需要额外配置 | 原生支持更好 |
| Tree-shaking | 困难 | 容易 |
| 代码量 | 较多 | 较少 |

**逻辑复用示例（Composables）：**

```typescript
// useCounter.ts
import { ref, computed } from 'vue'

export function useCounter(initialValue = 0) {
  const count = ref(initialValue)
  
  const increment = () => count.value++
  const decrement = () => count.value--
  const reset = () => count.value = initialValue
  
  const doubleCount = computed(() => count.value * 2)
  
  return {
    count,
    increment,
    decrement,
    reset,
    doubleCount
  }
}

// 组件中使用
<script setup>
import { useCounter } from '@/composables/useCounter'

const { count, increment, decrement, reset, doubleCount } = useCounter(10)
</script>
```

**项目中应用：**

```vue
<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'

const question = ref('')
const loading = ref(false)
const streaming = ref(false)
const currentAnswer = ref<QAResponse | null>(null)

const showFinalAnswer = computed(() => {
  return currentAnswer.value?.answer && !streaming.value
})

onMounted(() => {
  fetchHistory()
})
</script>
```

**为什么使用：**
- 更好的逻辑复用
- 更好的类型推断
- 更好的代码组织
- 更好的 Tree-shaking

---

### 问题 2：Vue 3 中的响应式系统是如何工作的？

**答案：**

**1. ref 和 reactive**

```typescript
import { ref, reactive, readonly } from 'vue'

// ref: 用于基本类型
const count = ref(0)
console.log(count.value)  // 访问值

// reactive: 用于对象
const state = reactive({
  count: 0,
  name: '张三',
  nested: { value: 1 }
})

// readonly: 只读响应式
const original = reactive({ count: 0 })
const copy = readonly(original)
```

**2. ref 和 reactive 的区别**

| 特性 | ref | reactive |
|------|-----|----------|
| 适用类型 | 基本类型和对象 | 仅对象 |
| 访问方式 | `.value` | 直接访问 |
| 重新赋值 | 支持 | 不支持（需替换整个对象） |
| 解构 | 保持响应式 | 丢失响应式 |

```typescript
// ref 的优势
const obj = ref({ count: 0 })
obj.value = { count: 1 }  // 可以重新赋值

// reactive 的问题
const state = reactive({ count: 0 })
// state.count = 1  // 可以
// state = reactive({})  // 错误！不能重新赋值整个对象
```

**3. toRefs 和 toRef**

解决 reactive 对象解构后丢失响应式的问题：

```typescript
import { reactive, toRefs, toRef } from 'vue'

const state = reactive({
  count: 0,
  name: '张三'
})

// toRefs: 将响应式对象的每个属性转为 ref
const { count, name } = toRefs(state)

// toRef: 将响应式对象的某个属性转为 ref
const countRef = toRef(state, 'count')
```

**4. 响应式原理**

Vue 3 使用 ES Proxy 实现响应式：

```javascript
// 简化版的响应式实现
function reactive(obj) {
  return new Proxy(obj, {
    get(target, key) {
      track(target, key)  // 收集依赖
      return Reflect.get(target, key)
    },
    set(target, key, value) {
      Reflect.set(target, key, value)
      trigger(target, key)  // 触发更新
      return true
    }
  })
}
```

**5. computed 计算属性**

```typescript
import { ref, computed } from 'vue'

const firstName = ref('张')
const lastName = ref('三')

// 只读计算属性
const fullName = computed(() => `${firstName.value} ${lastName.value}`)

// 可写计算属性
const fullNameWritable = computed({
  get: () => `${firstName.value} ${lastName.value}`,
  set: (value) => {
    const [first, last] = value.split(' ')
    firstName.value = first
    lastName.value = last
  }
})
```

**为什么使用响应式：**
- 数据变化自动更新视图
- 精确的依赖追踪
- 高效的更新机制

---

### 问题 3：Vue 3 中的 watch 和 watchEffect 有什么区别？

**答案：**

**1. watch - 懒执行**

```typescript
import { ref, watch } from 'vue'

const count = ref(0)

// 基本用法：监听单个 ref
watch(count, (newValue, oldValue) => {
  console.log(`count 从 ${oldValue} 变为 ${newValue}`)
}, { immediate: true })  // immediate: 立即执行

// 监听多个 ref
const first = ref(0)
const second = ref(0)

watch([first, second], ([newFirst, newSecond], [oldFirst, oldSecond]) => {
  console.log(`变化: ${oldFirst}->${newFirst}, ${oldSecond}->${newSecond}`)
})

// 监听 reactive 对象的属性
const state = reactive({ count: 0, name: '' })

watch(() => state.count, (newVal) => {
  console.log(`count 变化: ${newVal}`)
})

// 深度监听
watch(() => state, (newState) => {
  console.log('state 变化:', newState)
}, { deep: true })
```

**2. watchEffect - 立即执行**

```typescript
import { ref, watchEffect } from 'vue'

const count = ref(0)

// watchEffect 会立即执行，并在依赖变化时重新执行
watchEffect(() => {
  console.log(`count 的值: ${count.value}`)
  // 自动追踪 count.value 的访问
})
```

**3. 区别对比**

| 特性 | watch | watchEffect |
|------|-------|------------|
| 首次执行 | 需要 `immediate: true` | 自动执行 |
| 回调参数 | 有 (new, old) | 没有 |
| 依赖追踪 | 手动指定 | 自动追踪 |
| 适用场景 | 需要旧值时 | 不需要旧值时 |
| 性能 | 更好（可精确指定依赖） | 可能包含不必要的副作用 |

**4. 停止监听**

```typescript
import { ref, watchEffect } from 'vue'

const count = ref(0)

const stop = watchEffect(() => {
  console.log(`count: ${count.value}`)
})

// 手动停止
stop()

// 在组件中使用，组件卸载时自动停止
```

**项目中应用：**

```vue
<script setup>
import { ref, watch } from 'vue'

const currentPage = ref(1)
const pageSize = ref(10)

// 监听分页变化，重新获取数据
watch([currentPage, pageSize], () => {
  fetchData()
})
</script>
```

---

## 2. TypeScript 类型系统

### 问题 4：TypeScript 中的 interface 和 type 有什么区别？

**答案：**

**1. 基本语法**

```typescript
// interface
interface User {
  id: number
  name: string
  email?: string  // 可选属性
  readonly createdAt: Date  // 只读属性
}

// type
type Point = {
  x: number
  y: number
}

// 两者都可以描述对象
const user: User = { id: 1, name: '张三', createdAt: new Date() }
const point: Point = { x: 10, y: 20 }
```

**2. 主要区别**

| 特性 | interface | type |
|------|-----------|------|
| 声明合并 | 支持（同名自动合并） | 不支持 |
| 扩展 | `extends` | `&` 交叉类型 |
| 计算属性 | 不支持 | 支持 |
| 描述基本类型 | 不支持 | 支持 |
| class 实现 | 可以 | 不可以直接 |

```typescript
// interface 声明合并
interface Window {
  title: string
}
interface Window {
  ts: TypeScriptAPI
}
// Window 包含两个接口的所有成员

// type 交叉类型
type Animal = { name: string }
type Bear = Animal & { honey: boolean }

// interface 扩展
interface Animal {
  name: string
}
interface Bear extends Animal {
  honey: boolean
}
```

**3. 最佳实践**

```typescript
// 推荐用 interface 描述对象类型（可扩展）
interface User {
  id: number
  name: string
}

// 推荐用 type 描述联合类型、交叉类型
type Status = 'pending' | 'success' | 'error'
type Result = Success | Error

// 复杂的泛型约束
type Nullable<T> = T | null
type Partial<T> = { [P in keyof T]?: T[P] }
```

**项目中应用：**

```typescript
// src/types/index.ts
interface Document {
  id: number
  filename: string
  file_type: string
  file_size: number
  status: number
  chunk_count: number
  created_at: string
}

interface QAResponse {
  answer: string
  sources: SourceItem[]
  cache_hit: boolean
  response_time_ms: number
}
```

**为什么需要 TypeScript：**
- 静态类型检查
- IDE 智能提示
- 代码文档化
- 重构更安全

---

### 问题 5：TypeScript 中的泛型是如何工作的？

**答案：**

**1. 基本泛型**

```typescript
// 泛型函数
function identity<T>(arg: T): T {
  return arg
}

const num = identity<number>(42)
const str = identity('hello')  // 类型推断

// 泛型接口
interface Container<T> {
  value: T
  getValue(): T
}

const numberContainer: Container<number> = {
  value: 42,
  getValue() { return this.value }
}
```

**2. 泛型约束**

```typescript
// 使用 extends 约束类型
interface HasLength {
  length: number
}

function logLength<T extends HasLength>(arg: T): T {
  console.log(arg.length)
  return arg
}

logLength('hello')  // 字符串有 length
logLength([1, 2, 3])  // 数组有 length
logLength({ length: 10 })  // 对象有 length
// logLength(123)  // 错误！数字没有 length

// keyof 约束
function getProperty<T, K extends keyof T>(obj: T, key: K): T[K] {
  return obj[key]
}

const user = { name: '张三', age: 25 }
const name = getProperty(user, 'name')  // string
const age = getProperty(user, 'age')  // number
```

**3. 泛型默认值**

```typescript
interface Response<T = any> {
  code: number
  data: T
  message: string
}

// 使用默认类型
const response: Response = { code: 0, data: 'ok', message: '成功' }

// 指定具体类型
const userResponse: Response<User> = {
  code: 0,
  data: { id: 1, name: '张三' },
  message: '成功'
}
```

**4. 条件类型**

```typescript
// 条件类型
type NonNullable<T> = T extends null | undefined ? never : T

type A = NonNullable<string | null | undefined>  // string

// 提取返回值类型
type ReturnType<T> = T extends (...args: any[]) => infer R ? R : never

function getUser() { return { id: 1, name: '张三' } }
type UserType = ReturnType<typeof getUser>  // { id: number, name: string }
```

**项目中应用：**

```typescript
// API 返回类型
interface ApiResponse<T> {
  code: number
  message: string
  data: T
}

interface PageResult<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}

// 使用泛型
async function fetchData<T>(url: string): Promise<ApiResponse<T>> {
  const res = await fetch(url)
  return res.json()
}

const users = await fetchData<User[]>('/api/users')
```

---

## 3. Vue Router 路由管理

### 问题 6：Vue Router 中的路由守卫是如何工作的？

**答案：**

**1. 三种路由守卫**

```typescript
import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [...]
})

// 全局前置守卫
router.beforeEach((to, from, next) => {
  // to: 目标路由
  // from: 来源路由
  // next: 放行函数
  
  const isAuthenticated = checkAuth()
  
  if (to.meta.requiresAuth && !isAuthenticated) {
    next('/login')
  } else {
    next()  // 放行
  }
})

// 全局解析守卫（在组件解析之后）
router.beforeResolve((to, from, next) => {
  console.log('组件已解析，准备切换')
  next()
})

// 全局后置守卫（切换完成后）
router.afterEach((to, from) => {
  console.log(`导航到: ${to.path}`)
})
```

**2. 路由独享守卫**

```typescript
const routes = [
  {
    path: '/admin',
    component: Admin,
    beforeEnter: (to, from, next) => {
      // 仅对 /admin 路由生效
      if (isAdmin()) {
        next()
      } else {
        next('/403')
      }
    }
  }
]
```

**3. 组件内守卫**

```vue
<script setup>
import { onMounted, onBeforeUnmount } from 'vue'
import { onBeforeRouteLeave, onBeforeRouteUpdate } from 'vue-router'

// 路由进入前
onBeforeRouteEnter((to, from, next) => {
  // 组件实例还未创建，无法访问 this
  // 可以通过 next(vm => {}) 访问组件实例
  next(vm => {
    vm.loadData()
  })
})

// 路由更新时（同一组件，参数变化）
onBeforeRouteUpdate((to, from) => {
  console.log('参数变化:', to.params.id)
  this.loadData(to.params.id)
})

// 路由离开时
onBeforeRouteLeave((to, from) => {
  const answer = window.confirm('确定要离开吗？')
  if (answer) {
    next()
  } else {
    next(false)  // 取消导航
  }
})
</script>
```

**4. 守卫执行顺序**

```
导航触发
    ↓
全局 beforeEach
    ↓
路由独享 beforeEnter
    ↓
组件 beforeRouteEnter
    ↓
全局 beforeResolve
    ↓
导航确认
    ↓
组件挂载
    ↓
全局 afterEach
```

**项目中应用：**

```typescript
// router/index.ts
import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'Login',
      component: () => import('@/views/Login.vue')
    },
    {
      path: '/qa',
      name: 'QA',
      component: () => import('@/views/QA.vue'),
      meta: { requiresAuth: true }
    }
  ]
})

// 路由守卫
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  
  if (to.meta.requiresAuth && !token) {
    next('/login')
  } else {
    next()
  }
})
```

---

## 4. Pinia 状态管理

### 问题 7：Pinia 相比 Vuex 有什么优势？如何在项目中使用？

**答案：**

**1. Pinia 的优势**

| 特性 | Pinia | Vuex |
|------|-------|------|
| API 设计 | 更简洁 | 较复杂 |
| TypeScript 支持 | 原生 | 需要额外配置 |
| 体积 | ~1KB | ~20KB |
| mutations | 不需要 | 需要 |
| 插件支持 | 有 | 有 |
| 开发者工具 | 支持 | 支持 |

**2. Pinia Store 定义**

```typescript
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

// 使用 Composition API 风格（推荐）
export const useUserStore = defineStore('user', () => {
  // 状态
  const userInfo = ref<User | null>(null)
  const token = ref<string | null>(null)
  
  // 计算属性
  const isLoggedIn = computed(() => !!token.value)
  const userName = computed(() => userInfo.value?.name || '未登录')
  
  // 方法
  function setUser(user: User, userToken: string) {
    userInfo.value = user
    token.value = userToken
    localStorage.setItem('token', userToken)
  }
  
  function logout() {
    userInfo.value = null
    token.value = null
    localStorage.removeItem('token')
  }
  
  // 返回
  return {
    userInfo,
    token,
    isLoggedIn,
    userName,
    setUser,
    logout
  }
})
```

**3. 组件中使用**

```vue
<script setup>
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()

// 访问状态
console.log(userStore.userName)

// 修改状态
userStore.setUser({ id: 1, name: '张三' }, 'token123')

// 调用方法
userStore.logout()
</script>
```

**4. Pinia 配置**

```typescript
// main.ts
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.mount('#app')
```

**项目中应用：**

虽然项目安装了 Pinia，但目前使用 localStorage 直接管理状态：

```typescript
// API 请求中直接使用 localStorage
const token = localStorage.getItem('token')
const res = await fetch('/api/v1/qa/ask/stream', {
  headers: {
    'Authorization': token ? `Bearer ${token}` : ''
  }
})
```

---

## 5. Axios HTTP 请求

### 问题 8：Axios 中如何实现请求拦截器和响应拦截器？

**答案：**

**1. 请求拦截器**

```typescript
import axios, { AxiosInstance, AxiosRequestConfig } from 'axios'

const api: AxiosInstance = axios.create({
  baseURL: '/api/v1',
  timeout: 120000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    // 添加 token
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    
    console.log(`请求: ${config.method?.toUpperCase()} ${config.url}`)
    return config
  },
  (error) => {
    console.error('请求错误:', error)
    return Promise.reject(error)
  }
)
```

**2. 响应拦截器**

```typescript
// 响应拦截器
api.interceptors.response.use(
  (response) => {
    // 2xx 状态码
    const { data } = response
    
    // 统一处理业务错误
    if (data.success === false) {
      console.error('业务错误:', data.message)
      return Promise.reject(new Error(data.message))
    }
    
    return data
  },
  (error) => {
    // 非 2xx 状态码
    const { response } = error
    
    if (response) {
      switch (response.status) {
        case 401:
          // 未授权，跳转登录
          localStorage.removeItem('token')
          window.location.href = '/login'
          break
        case 403:
          console.error('无权限访问')
          break
        case 404:
          console.error('请求的资源不存在')
          break
        case 500:
          console.error('服务器内部错误')
          break
      }
    } else if (error.request) {
      console.error('网络错误，请检查网络连接')
    }
    
    return Promise.reject(error)
  }
)
```

**3. 项目中的封装**

```typescript
// api/request.ts
import axios from 'axios'

const request = axios.create({
  baseURL: '/api/v1',
  timeout: 120000
})

request.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  }
)

request.interceptors.response.use(
  (response) => response.data,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default request

// api/index.ts
import request from './request'

export const getDocuments = (params: any) => 
  request.get('/documents', { params })

export const uploadDocument = (data: FormData) => 
  request.post('/documents/upload', data, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })

export const askQuestion = (data: { question: string }) => 
  request.post('/qa/ask', data)
```

---

## 6. Element Plus 组件库

### 问题 9：Element Plus 中的表单验证是如何工作的？

**答案：**

**1. 基本用法**

```vue
<template>
  <el-form :model="form" :rules="rules" ref="formRef">
    <el-form-item label="用户名" prop="username">
      <el-input v-model="form.username" />
    </el-form-item>
    
    <el-form-item label="邮箱" prop="email">
      <el-input v-model="form.email" />
    </el-form-item>
    
    <el-form-item>
      <el-button type="primary" @click="submit">提交</el-button>
      <el-button @click="reset">重置</el-button>
    </el-form-item>
  </el-form>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import type { FormInstance, FormRules } from 'element-plus'

const formRef = ref<FormInstance>()

const form = reactive({
  username: '',
  email: ''
})

const rules = reactive<FormRules>({
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '长度在 3 到 20 个字符', trigger: 'blur' }
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' }
  ]
})

const submit = async () => {
  if (!formRef.value) return
  
  await formRef.value.validate((valid) => {
    if (valid) {
      console.log('表单提交:', form)
    } else {
      console.log('表单验证失败')
    }
  })
}

const reset = () => {
  formRef.value?.resetFields()
}
</script>
```

**2. 自定义验证器**

```typescript
const validatePass = (rule: any, value: any, callback: any) => {
  if (value === '') {
    callback(new Error('请输入密码'))
  } else if (value.length < 6) {
    callback(new Error('密码长度不能少于 6 位'))
  } else {
    callback()
  }
}

const validatePassCheck = (rule: any, value: any, callback: any) => {
  if (value === '') {
    callback(new Error('请确认密码'))
  } else if (value !== form.password) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const rules = reactive({
  password: [{ validator: validatePass, trigger: 'blur' }],
  checkPass: [{ validator: validatePassCheck, trigger: 'blur' }]
})
```

**3. 异步验证**

```typescript
const validateUsername = async (rule: any, value: any, callback: any) => {
  if (!value) {
    callback(new Error('请输入用户名'))
    return
  }
  
  try {
    const response = await checkUsernameExists(value)
    if (response.exists) {
      callback(new Error('用户名已存在'))
    } else {
      callback()
    }
  } catch (error) {
    callback(new Error('验证失败'))
  }
}
```

---

## 7. Vite 构建工具

### 问题 10：Vite 相比 Webpack 有什么优势？

**答案：**

**1. 核心区别**

| 特性 | Vite | Webpack |
|------|------|---------|
| 开发服务器 | ESM 原生支持 | 需要额外配置 |
| 热更新 | 毫秒级 | 较慢 |
| 构建速度 | 快（esbuild） | 较慢 |
| 配置文件 | 简洁 | 复杂 |
| 生态 | 快速成长 | 成熟稳定 |

**2. Vite 工作原理**

```
开发环境：
┌─────────────────────────────────────┐
│  浏览器请求 /src/main.ts            │
│         ↓                          │
│  Vite 服务器拦截请求                │
│         ↓                          │
│  返回处理后的 ES Module             │
│  （HMR 支持，仅更新变化的模块）       │
└─────────────────────────────────────┘

生产环境：
┌─────────────────────────────────────┐
│  Rollup 打包                        │
│         ↓                          │
│  代码分割 Tree-shaking             │
│         ↓                          │
│  生成优化的静态资源                 │
└─────────────────────────────────────┘
```

**3. Vite 配置**

```typescript
// vite.config.ts
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

export default defineConfig({
  plugins: [vue()],
  
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src')
    }
  },
  
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  },
  
  build: {
    target: 'es2015',
    cssCodeSplit: true,
    sourcemap: false
  }
})
```

**4. 环境变量**

```typescript
// .env.development
VITE_API_BASE_URL=http://localhost:8000

// .env.production
VITE_API_BASE_URL=https://api.example.com

// 代码中使用
console.log(import.meta.env.VITE_API_BASE_URL)
```

**为什么使用 Vite：**
- 极快的开发服务器启动
- 毫秒级热更新
- 简洁的配置
- 更好的开发体验

---

## 版本信息

- 文档版本: 1.0.0
- 更新日期: 2026-05-18
