<template>
  <div class="system-page">
    <el-card shadow="hover" class="status-card">
      <template #header><span>系统状态</span></template>
      <el-descriptions :column="3" border>
        <el-descriptions-item label="健康检查">
          <el-tag :type="systemHealth === 'healthy' ? 'success' : 'danger'">{{ systemHealth === 'healthy' ? '正常' : '异常' }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="API 版本">v1.0.0</el-descriptions-item>
        <el-descriptions-item label="部署环境"><el-tag type="info">开发环境</el-tag></el-descriptions-item>
      </el-descriptions>
      <div class="status-actions"><el-button @click="checkHealth"><el-icon><Refresh /></el-icon>刷新状态</el-button></div>
    </el-card>

    <el-card shadow="hover" class="config-card">
      <template #header>
        <span>检索配置</span>
        <el-tag type="warning" size="small" style="margin-left: 8px">实时生效</el-tag>
      </template>
      <div v-if="loading" class="loading-container"><el-icon class="is-loading"><Loading /></el-icon><span>加载中...</span></div>
      <div v-else class="runtime-config">
        <div class="config-item">
          <div class="config-label">
            <span class="label-text">Top K 检索数</span>
            <span class="label-tip">控制每次检索返回的相关文档数量</span>
          </div>
          <div class="config-control">
            <el-input-number v-model="runtimeConfig.retrieval_top_k" :min="1" :max="50" size="large" />
            <el-button type="primary" size="small" @click="updateConfig">保存</el-button>
          </div>
        </div>
        <el-divider />
        <div class="config-item">
          <div class="config-label">
            <span class="label-text">相似度阈值</span>
            <span class="label-tip">低于此阈值的检索结果将被过滤（0-1，值越高匹配越严格）</span>
          </div>
          <div class="config-control">
            <el-input-number v-model="runtimeConfig.similarity_threshold" :min="0" :max="1" :step="0.05" :precision="2" size="large" />
            <el-button type="primary" size="small" @click="updateConfig">保存</el-button>
          </div>
        </div>
        <el-divider />
        <div class="config-item">
          <div class="config-label">
            <span class="label-text">当前值预览</span>
          </div>
          <div class="current-values">
            <el-tag type="success">Top K: {{ runtimeConfig.retrieval_top_k }}</el-tag>
            <el-tag type="warning">相似度: {{ runtimeConfig.similarity_threshold }}</el-tag>
          </div>
        </div>
      </div>
    </el-card>

    <el-card shadow="hover" class="about-card">
      <template #header><span>关于系统</span></template>
      <div class="about-content">
        <div class="about-logo"><el-icon size="64" color="#409EFF"><ChatLineSquare /></el-icon></div>
        <h2>RAG 知识库问答系统</h2>
        <p class="version">版本 1.0.0</p>
        <p class="description">基于 RAG 技术的智能问答系统，支持文档上传、智能问答、知识库管理等功能。</p>
        <div class="tech-stack"><el-tag v-for="tech in techStack" :key="tech" size="small">{{ tech }}</el-tag></div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { ChatLineSquare, Refresh, Loading } from '@element-plus/icons-vue'
import { healthCheck, getRuntimeConfig, updateSystemConfig } from '@/api'

const systemHealth = ref<'healthy' | 'unhealthy'>('unhealthy')
const loading = ref(false)
const runtimeConfig = reactive({
  retrieval_top_k: 5,
  similarity_threshold: 0.2
})

const techStack = ['FastAPI', 'PyTorch', 'ChromaDB', 'Redis', 'MySQL', 'Vue 3', 'Element Plus']

const checkHealth = async () => {
  try {
    await healthCheck()
    systemHealth.value = 'healthy'
  } catch { systemHealth.value = 'unhealthy' }
}

const fetchRuntimeConfig = async () => {
  loading.value = true
  try {
    const res = await getRuntimeConfig()
    if (res.data) {
      runtimeConfig.retrieval_top_k = res.data.retrieval_top_k || 5
      runtimeConfig.similarity_threshold = res.data.similarity_threshold || 0.2
    }
  } catch (error) { console.error('Failed to fetch config:', error) }
  finally { loading.value = false }
}

const updateConfig = async () => {
  try {
    await updateSystemConfig({
      retrieval_top_k: runtimeConfig.retrieval_top_k,
      similarity_threshold: runtimeConfig.similarity_threshold
    })
    ElMessage.success('配置已更新，将实时影响问答检索')
  } catch (error) {
    console.error('Failed to update config:', error)
    ElMessage.error('配置更新失败')
  }
}

onMounted(() => { checkHealth(); fetchRuntimeConfig() })
</script>

<style scoped>
.system-page { max-width: 1000px; margin: 0 auto; }
.status-card, .config-card, .about-card { margin-bottom: 20px; }
.status-actions { margin-top: 16px; padding-top: 16px; border-top: 1px solid #ebeef5; }
.loading-container { display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 40px 0; gap: 12px; color: #909399; }
.about-content { text-align: center; padding: 20px; }
.about-logo { margin-bottom: 16px; }
.about-content h2 { margin-bottom: 8px; color: #303133; }
.version { color: #909399; margin-bottom: 16px; }
.description { color: #606266; line-height: 1.8; margin-bottom: 20px; max-width: 600px; margin-left: auto; margin-right: auto; }
.tech-stack { display: flex; justify-content: center; gap: 8px; flex-wrap: wrap; }
.runtime-config { padding: 20px 0; }
.config-item { display: flex; justify-content: space-between; align-items: center; padding: 16px 0; }
.config-label { flex: 1; }
.label-text { display: block; font-size: 16px; font-weight: 500; color: #303133; margin-bottom: 4px; }
.label-tip { display: block; font-size: 12px; color: #909399; }
.config-control { display: flex; align-items: center; gap: 12px; }
.current-values { display: flex; gap: 12px; }
</style>
