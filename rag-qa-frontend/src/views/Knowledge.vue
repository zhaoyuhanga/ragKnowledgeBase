<template>
  <div class="knowledge-page">
    <el-row :gutter="20" class="stats-row">
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <el-icon class="stat-icon" style="color: #409EFF"><Document /></el-icon>
            <div class="stat-info"><p class="stat-label">文档数量</p><p class="stat-value">{{ stats.total_documents }}</p></div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <el-icon class="stat-icon" style="color: #67C23A"><Collection /></el-icon>
            <div class="stat-info"><p class="stat-label">文档块数</p><p class="stat-value">{{ stats.total_chunks }}</p></div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <el-icon class="stat-icon" style="color: #E6A23C"><Cpu /></el-icon>
            <div class="stat-info"><p class="stat-label">向量数量</p><p class="stat-value">{{ stats.collection_size }}</p></div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <el-icon class="stat-icon" style="color: #F56C6C"><Clock /></el-icon>
            <div class="stat-info"><p class="stat-label">最后更新</p><p class="stat-value small">{{ formatTime(stats.last_updated) }}</p></div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="actions-row">
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header><span>重建知识库索引</span></template>
          <p class="action-desc">重建索引将重新处理所有已上传的文档，更新向量数据库中的嵌入表示。此操作可能需要较长时间。</p>
          <el-button type="warning" :loading="rebuilding" @click="handleRebuild"><el-icon><Refresh /></el-icon>重建索引</el-button>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header><span>清除缓存</span></template>
          <p class="action-desc">清除 Redis 缓存中的问答历史和临时数据。此操作不会影响已上传的文档和向量数据。</p>
          <el-button type="danger" :loading="clearing" @click="handleClearCache"><el-icon><Delete /></el-icon>清除缓存</el-button>
        </el-card>
      </el-col>
    </el-row>

    <el-card shadow="hover" class="search-card">
      <template #header><span>知识库检索测试</span></template>
      <div class="search-form">
        <el-input v-model="searchQuery" placeholder="输入测试查询内容" style="flex: 1"><template #prefix><el-icon><Search /></el-icon></template></el-input>
        <el-input-number v-model="searchTopK" :min="1" :max="20" :step="1" controls-position="right" style="width: 120px"><template #prefix>Top K</template></el-input-number>
        <el-button type="primary" :loading="searching" @click="handleSearch">检索</el-button>
      </div>
      <div v-if="searchResults.length > 0" class="search-results">
        <h4>检索结果 (找到 {{ searchResults.length }} 个相关片段)</h4>
        <el-divider />
        <div v-for="(result, index) in searchResults" :key="index" class="result-item">
          <div class="result-header"><span class="result-index">片段 {{ index + 1 }}</span></div>
          <div class="result-content markdown-content">{{ result }}</div>
        </div>
      </div>
      <el-empty v-else-if="searched && searchResults.length === 0" description="未找到相关结果" />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Document, Collection, Cpu, Clock, Refresh, Delete, Search } from '@element-plus/icons-vue'
import { getKnowledgeStats, rebuildKnowledgeBase, clearCache, searchKnowledge } from '@/api'

const stats = reactive({ total_documents: 0, total_chunks: 0, collection_size: 0, last_updated: '' })
const rebuilding = ref(false)
const clearing = ref(false)
const searchQuery = ref('')
const searchTopK = ref(5)
const searching = ref(false)
const searched = ref(false)
const searchResults = ref<string[]>([])

const formatTime = (time: string) => { if (!time) return '-'; return new Date(time).toLocaleString('zh-CN') }

const fetchStats = async () => {
  try {
    const res = await getKnowledgeStats()
    stats.total_documents = res.data.documents?.total || 0
    stats.total_chunks = res.data.chunks?.total || 0
    stats.collection_size = res.data.vectors?.count || 0
  } catch (error) { console.error('Failed to fetch stats:', error) }
}

const handleRebuild = async () => {
  rebuilding.value = true
  try { await rebuildKnowledgeBase(); ElMessage.success('重建任务已启动'); setTimeout(fetchStats, 5000) }
  catch (error) { console.error('Rebuild failed:', error) }
  finally { rebuilding.value = false }
}

const handleClearCache = async () => {
  clearing.value = true
  try { await clearCache(); ElMessage.success('缓存已清除') }
  catch (error) { console.error('Clear cache failed:', error) }
  finally { clearing.value = false }
}

const handleSearch = async () => {
  if (!searchQuery.value.trim()) { ElMessage.warning('请输入查询内容'); return }
  searching.value = true; searched.value = true
  try {
    const res = await searchKnowledge(searchQuery.value, searchTopK.value)
    searchResults.value = res.data.results?.map((r: any) => r.content) || []
    if (searchResults.value.length === 0) ElMessage.info('未找到相关结果')
  } catch (error) { console.error('Search failed:', error); searchResults.value = [] }
  finally { searching.value = false }
}

onMounted(() => { fetchStats() })
</script>

<style scoped>
.knowledge-page { max-width: 1400px; margin: 0 auto; }
.stats-row { margin-bottom: 20px; }
.stat-card { height: 100px; }
.stat-content { display: flex; align-items: center; gap: 16px; }
.stat-icon { font-size: 40px; }
.stat-info { flex: 1; }
.stat-label { color: #909399; font-size: 14px; margin-bottom: 8px; }
.stat-value { font-size: 24px; font-weight: 600; color: #303133; }
.stat-value.small { font-size: 14px; }
.actions-row { margin-bottom: 20px; }
.action-desc { color: #606266; margin-bottom: 16px; line-height: 1.6; }
.search-card { margin-bottom: 20px; }
.search-form { display: flex; gap: 16px; margin-bottom: 20px; }
.search-results { margin-top: 20px; }
.search-results h4 { color: #303133; margin-bottom: 8px; }
.result-item { margin-bottom: 16px; padding: 16px; background: #f9fafb; border-radius: 8px; border-left: 4px solid #409EFF; }
.result-header { margin-bottom: 8px; }
.result-index { font-weight: 500; color: #409EFF; }
.result-content { color: #606266; line-height: 1.8; white-space: pre-wrap; word-break: break-word; }
</style>
