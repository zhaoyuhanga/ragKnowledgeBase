<template>
  <el-container class="layout-container">
    <el-aside :width="isCollapsed ? '64px' : '220px'" class="sidebar">
      <div class="logo">
        <el-icon size="28"><ChatLineSquare /></el-icon>
        <span v-show="!isCollapsed" class="logo-text">RAG 问答系统</span>
      </div>
      <el-menu :default-active="activeMenu" :collapse="isCollapsed" :collapse-transition="false" router class="sidebar-menu">
        <el-menu-item v-for="item in menuItems" :key="item.path" :index="item.path">
          <el-icon><component :is="item.icon" /></el-icon>
          <template #title>{{ item.title }}</template>
        </el-menu-item>
      </el-menu>
      <div class="sidebar-footer">
        <el-button text @click="isCollapsed = !isCollapsed">
          <el-icon v-if="isCollapsed"><DArrowRight /></el-icon>
          <el-icon v-else><DArrowLeft /></el-icon>
        </el-button>
      </div>
    </el-aside>
    <el-container>
      <el-header class="header">
        <div class="header-left"><h2>{{ pageTitle }}</h2></div>
        <div class="header-right">
          <el-tag :type="systemStatus === 'healthy' ? 'success' : 'danger'">
            <el-icon><CircleCheck v-if="systemStatus === 'healthy'" /><CircleClose v-else /></el-icon>
            {{ systemStatus === 'healthy' ? '系统正常' : '系统异常' }}
          </el-tag>
        </div>
      </el-header>
      <el-main class="main-content">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in"><component :is="Component" /></transition>
        </router-view>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { DArrowLeft, DArrowRight, CircleCheck, CircleClose } from '@element-plus/icons-vue'
import { healthCheck } from '@/api'

const route = useRoute()
const isCollapsed = ref(false)
const systemStatus = ref<'healthy' | 'unhealthy'>('unhealthy')

const menuItems = [
  { path: '/dashboard', title: '仪表盘', icon: 'Odometer' },
  { path: '/qa', title: '知识问答', icon: 'ChatDotRound' },
  { path: '/documents', title: '文档管理', icon: 'Document' },
  { path: '/knowledge', title: '知识库管理', icon: 'Collection' },
  { path: '/system', title: '系统设置', icon: 'Setting' }
]

const activeMenu = computed(() => route.path)
const pageTitle = computed(() => {
  const item = menuItems.find(m => m.path === activeMenu.value)
  return item?.title || '仪表盘'
})

const checkHealth = async () => {
  try {
    await healthCheck()
    systemStatus.value = 'healthy'
  } catch {
    systemStatus.value = 'unhealthy'
  }
}

onMounted(() => {
  checkHealth()
  setInterval(checkHealth, 30000)
})
</script>

<style scoped>
.layout-container { height: 100vh; }
.sidebar { background: #001529; display: flex; flex-direction: column; transition: width 0.3s; overflow: hidden; }
.logo { height: 60px; display: flex; align-items: center; justify-content: center; color: white; font-size: 18px; font-weight: 600; border-bottom: 1px solid rgba(255, 255, 255, 0.1); }
.logo-text { margin-left: 8px; white-space: nowrap; }
.sidebar-menu { border-right: none; flex: 1; background: transparent; }
.sidebar-menu:not(.el-menu--collapse) { width: 220px; }
:deep(.el-menu) { background-color: transparent; }
:deep(.el-menu-item) { color: rgba(255, 255, 255, 0.7); }
:deep(.el-menu-item:hover), :deep(.el-menu-item.is-active) { background-color: rgba(255, 255, 255, 0.1); color: white; }
.sidebar-footer { padding: 12px; border-top: 1px solid rgba(255, 255, 255, 0.1); display: flex; justify-content: center; }
.header { background: white; display: flex; align-items: center; justify-content: space-between; padding: 0 24px; box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08); }
.header h2 { margin: 0; font-size: 18px; font-weight: 500; }
.main-content { padding: 24px; overflow-y: auto; }
</style>
