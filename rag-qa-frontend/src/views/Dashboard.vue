<template>
  <div class="dashboard">
    <el-row :gutter="20" class="stat-cards">
      <el-col :span="6" v-for="stat in statCards" :key="stat.title">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <div class="stat-info">
              <p class="stat-title">{{ stat.title }}</p>
              <p class="stat-value">{{ stat.value }}</p>
            </div>
            <el-icon class="stat-icon" :style="{ color: stat.color }">
              <component :is="stat.icon" />
            </el-icon>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="chart-row">
      <el-col :span="16">
        <el-card shadow="hover">
          <template #header>
            <span>系统性能</span>
          </template>
          <div class="performance-chart">
            <div class="chart-item">
              <span class="chart-label">缓存命中率</span>
              <el-progress :percentage="stats.cache_hit_rate" :color="getProgressColor(stats.cache_hit_rate)" />
              <span class="chart-value">{{ stats.cache_hit_rate }}%</span>
            </div>
            <div class="chart-item">
              <span class="chart-label">平均响应时间</span>
              <el-progress :percentage="Math.min(stats.avg_response_time / 10, 100)" :color="getProgressColor(100 - stats.avg_response_time)" />
              <span class="chart-value">{{ stats.avg_response_time.toFixed(2) }} ms</span>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover">
          <template #header>
            <span>知识库概览</span>
          </template>
          <div class="knowledge-overview">
            <div class="overview-item"><el-icon><Document /></el-icon><span class="label">文档数量</span><span class="value">{{ stats.total_documents }}</span></div>
            <div class="overview-item"><el-icon><Collection /></el-icon><span class="label">文档块数</span><span class="value">{{ stats.total_chunks }}</span></div>
            <div class="overview-item"><el-icon><ChatDotRound /></el-icon><span class="label">问答次数</span><span class="value">{{ stats.total_queries }}</span></div>
            <div class="overview-item"><el-icon><Clock /></el-icon><span class="label">今日问答</span><span class="value">{{ stats.today_queries }}</span></div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="quick-actions">
      <el-col :span="24">
        <el-card shadow="hover">
          <template #header>
            <span>快捷操作</span>
          </template>
          <div class="actions-grid">
            <el-button type="primary" @click="$router.push('/qa')"><el-icon><ChatLineSquare /></el-icon>开启问答</el-button>
            <el-button type="success" @click="$router.push('/documents')"><el-icon><Upload /></el-icon>上传文档</el-button>
            <el-button type="warning" @click="rebuildKnowledgeBase"><el-icon><Refresh /></el-icon>重建索引</el-button>
            <el-button type="info" @click="refreshStats"><el-icon><Refresh /></el-icon>刷新数据</el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { Document, Collection, ChatDotRound, Clock, ChatLineSquare, Upload, Refresh } from '@element-plus/icons-vue'
import { getSystemStats, rebuildKnowledgeBase as rebuildAPI } from '@/api'

const rawStats = ref<any>(null)

const stats = computed(() => {
  if (!rawStats.value) return { total_queries: 0, today_queries: 0, total_documents: 0, total_chunks: 0, cache_hit_rate: 0, avg_response_time: 0 }
  const qa = rawStats.value.qa || {}
  const docs = rawStats.value.documents || {}
  const chunks = rawStats.value.chunks || {}
  const vectors = rawStats.value.vectors || {}
  return {
    total_queries: Number(qa.total_questions) || 0,
    today_queries: Number(qa.today_queries) || 0,
    total_documents: Number(docs.total) || 0,
    total_chunks: Number(chunks.total || vectors.count) || 0,
    cache_hit_rate: Number(qa.cache_rate) || 0,
    avg_response_time: Number(qa.avg_response_time_ms) || 0
  }
})

const statCards = computed(() => [
  { title: '问答次数', value: stats.value.total_queries, icon: 'ChatDotRound', color: '#409EFF' },
  { title: '文档数量', value: stats.value.total_documents, icon: 'Document', color: '#67C23A' },
  { title: '文档块数', value: stats.value.total_chunks, icon: 'Collection', color: '#E6A23C' },
  { title: '今日问答', value: stats.value.today_queries, icon: 'Clock', color: '#F56C6C' }
])

const getProgressColor = (value: number) => {
  if (value >= 80) return '#67C23A'
  if (value >= 60) return '#E6A23C'
  return '#F56C6C'
}

const fetchStats = async () => {
  try {
    const res = await getSystemStats()
    // axios 拦截器返回 response.data = { success, message, code, data: {...} }
    if (res && res.data) {
      rawStats.value = res.data
    } else if (res && res.qa) {
      rawStats.value = res
    }
  } catch (error) { console.error('Failed to fetch stats:', error) }
}

const rebuildKnowledgeBase = async () => {
  try { await rebuildAPI(); ElMessage.success('重建任务已启动') }
  catch (error) { console.error('Rebuild failed:', error) }
}

const refreshStats = () => { fetchStats(); ElMessage.success('数据已刷新') }

onMounted(() => { fetchStats() })
</script>

<style scoped>
.dashboard { max-width: 1400px; margin: 0 auto; }
.stat-cards { margin-bottom: 20px; }
.stat-card { height: 120px; }
.stat-content { display: flex; justify-content: space-between; align-items: center; }
.stat-title { color: #909399; font-size: 14px; margin-bottom: 8px; }
.stat-value { font-size: 28px; font-weight: 600; color: #303133; }
.stat-icon { font-size: 48px; opacity: 0.8; }
.chart-row { margin-bottom: 20px; }
.performance-chart { padding: 20px 0; }
.chart-item { display: flex; align-items: center; margin-bottom: 24px; }
.chart-label { width: 120px; color: #606266; }
.chart-item :deep(.el-progress) { flex: 1; margin: 0 16px; }
.chart-value { width: 80px; text-align: right; font-weight: 500; color: #303133; }
.knowledge-overview { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
.overview-item { display: flex; align-items: center; gap: 12px; padding: 16px; background: #f5f7fa; border-radius: 8px; }
.overview-item .el-icon { font-size: 24px; color: #409EFF; }
.overview-item .label { color: #606266; flex: 1; }
.overview-item .value { font-size: 20px; font-weight: 600; color: #303133; }
.actions-grid { display: flex; gap: 16px; flex-wrap: wrap; }
.actions-grid .el-button { min-width: 140px; }
</style>
