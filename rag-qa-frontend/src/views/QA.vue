<template>
  <div class="qa-page">
    <el-card shadow="hover" class="qa-input-card">
      <template #header>
        <div class="card-header">
          <span>智能问答</span>
          <el-tag type="info">基于知识库内容回答</el-tag>
        </div>
      </template>
      <div class="input-area">
        <el-input v-model="question" type="textarea" :rows="3" placeholder="请输入您的问题，例如..." :disabled="loading" @keyup.enter.ctrl="handleAsk" />
        <div class="input-actions">
          <el-input-number v-model="topK" :min="1" :max="20" :step="1" controls-position="right" style="width: 120px"><template #prefix>Top K</template></el-input-number>
          <el-button type="primary" :loading="loading" :disabled="!question.trim()" @click="handleAsk">
            <el-icon v-if="!loading"><Search /></el-icon>
            提问
          </el-button>
        </div>
      </div>
    </el-card>

    <el-card shadow="hover" class="qa-result-card" v-if="currentAnswer">
      <template #header>
        <div class="card-header">
          <span>回答</span>
          <div class="answer-meta">
            <el-tag :type="currentAnswer.cache_hit ? 'warning' : 'success'" size="small">{{ currentAnswer.cache_hit ? '命中缓存' : '实时生成' }}</el-tag>
            <el-tag type="info" size="small">耗时: {{ currentAnswer.response_time_ms }}ms</el-tag>
          </div>
        </div>
      </template>
      <div class="answer-content markdown-content" v-html="renderedAnswer"></div>
      <div class="sources-section" v-if="currentAnswer.sources && currentAnswer.sources.length > 0">
        <h4><el-icon><Link /></el-icon> 参考来源</h4>
        <el-tag v-for="(source, index) in currentAnswer.sources" :key="index" type="info" class="source-tag">{{ source.filename }} (相似度: {{ (source.similarity * 100).toFixed(1) }}%)</el-tag>
      </div>
    </el-card>

    <el-card shadow="hover" class="history-card">
      <template #header>
        <div class="card-header">
          <span>历史记录</span>
          <el-button text size="small" @click="fetchHistory"><el-icon><Refresh /></el-icon>刷新</el-button>
        </div>
      </template>
      <div v-if="history.length === 0" class="empty-state"><el-empty description="暂无历史记录" /></div>
      <div v-else class="history-list">
        <div v-for="item in history" :key="item.id" class="history-item" @click="loadHistoryItem(item)">
          <div class="history-question">{{ item.question }}</div>
          <div class="history-meta">
            <span class="history-time">{{ formatTime(item.created_at) }}</span>
            <span class="history-meta-item">{{ item.response_time_ms }}ms</span>
          </div>
        </div>
      </div>
      <div class="pagination-wrapper" v-if="historyTotal > pageSize">
        <el-pagination v-model:current-page="currentPage" :page-size="pageSize" :total="historyTotal" layout="prev, pager, next" @current-change="fetchHistory" />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { marked } from 'marked'
import { ElMessage } from 'element-plus'
import { Search, Link, Refresh } from '@element-plus/icons-vue'
import { askQuestion, getQAHistory } from '@/api'
import type { QAResponse, QAHistory } from '@/types'

const question = ref('')
const topK = ref(5)
const loading = ref(false)
const currentAnswer = ref<QAResponse | null>(null)
const history = ref<QAHistory[]>([])
const currentPage = ref(1)
const pageSize = ref(10)
const historyTotal = ref(0)

const renderedAnswer = computed(() => {
  if (!currentAnswer.value?.answer) return ''
  return marked(currentAnswer.value.answer)
})

const formatTime = (time: string) => {
  return new Date(time).toLocaleString('zh-CN')
}

const handleAsk = async () => {
  if (!question.value.trim()) return
  loading.value = true
  try {
    const res = await askQuestion({ question: question.value, top_k: topK.value })
    currentAnswer.value = res.data
    ElMessage.success('回答已生成')
    fetchHistory()
  } catch (error) {
    console.error('Failed to ask question:', error)
  } finally {
    loading.value = false
  }
}

const fetchHistory = async () => {
  try {
    const res = await getQAHistory({ page: currentPage.value, page_size: pageSize.value })
    history.value = res.data.items
    historyTotal.value = res.data.total
  } catch (error) {
    console.error('Failed to fetch history:', error)
  }
}

const loadHistoryItem = (item: QAHistory) => {
  currentAnswer.value = { answer: item.answer, sources: [], cache_hit: item.cache_hit, response_time_ms: item.response_time_ms }
  question.value = item.question
}

onMounted(() => { fetchHistory() })
</script>

<style scoped>
.qa-page { max-width: 1200px; margin: 0 auto; }
.qa-input-card { margin-bottom: 20px; }
.card-header { display: flex; justify-content: space-between; align-items: center; }
.input-area { display: flex; flex-direction: column; gap: 16px; }
.input-actions { display: flex; justify-content: space-between; align-items: center; }
.qa-result-card { margin-bottom: 20px; }
.answer-meta { display: flex; gap: 8px; }
.answer-content { padding: 20px; background: #f9fafb; border-radius: 8px; min-height: 100px; }
.sources-section { margin-top: 20px; padding-top: 20px; border-top: 1px solid #ebeef5; }
.sources-section h4 { display: flex; align-items: center; gap: 8px; margin-bottom: 12px; color: #606266; }
.source-tag { margin-right: 8px; margin-bottom: 8px; }
.history-card { margin-bottom: 20px; }
.history-list { max-height: 400px; overflow-y: auto; }
.history-item { padding: 16px; border-bottom: 1px solid #ebeef5; cursor: pointer; transition: background-color 0.2s; }
.history-item:hover { background-color: #f5f7fa; }
.history-item:last-child { border-bottom: none; }
.history-question { color: #303133; margin-bottom: 8px; font-size: 14px; }
.history-meta { display: flex; justify-content: space-between; color: #909399; font-size: 12px; }
.pagination-wrapper { margin-top: 16px; display: flex; justify-content: center; }
.empty-state { padding: 40px 0; }
</style>
