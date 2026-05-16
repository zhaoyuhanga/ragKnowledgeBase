import { createRouter, createWebHistory, RouteRecordRaw } from 'vue-router'
import Layout from '@/views/Layout.vue'

const routes: RouteRecordRaw[] = [
  { path: '/login', name: 'Login', component: () => import('@/views/Login.vue'), meta: { title: '登录' } },
  {
    path: '/', component: Layout, redirect: '/dashboard',
    children: [
      { path: 'dashboard', name: 'Dashboard', component: () => import('@/views/Dashboard.vue'), meta: { title: '仪表盘', icon: 'Odometer' } },
      { path: 'qa', name: 'QA', component: () => import('@/views/QA.vue'), meta: { title: '知识问答', icon: 'ChatDotRound' } },
      { path: 'documents', name: 'Documents', component: () => import('@/views/Documents.vue'), meta: { title: '文档管理', icon: 'Document' } },
      { path: 'knowledge', name: 'Knowledge', component: () => import('@/views/Knowledge.vue'), meta: { title: '知识库管理', icon: 'Collection' } },
      { path: 'system', name: 'System', component: () => import('@/views/System.vue'), meta: { title: '系统设置', icon: 'Setting' } }
    ]
  }
]

const router = createRouter({ history: createWebHistory(), routes })

export default router
