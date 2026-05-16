<template>
  <div class="system-page">
    <!-- 系统状态卡片 -->
    <el-card shadow="hover" class="status-card">
      <template #header><span>系统状态</span></template>
      <el-descriptions :column="3" border>
        <el-descriptions-item label="健康检查">
          <el-tag :type="systemHealth === 'healthy' ? 'success' : 'danger'">
            {{ systemHealth === 'healthy' ? '正常' : '异常' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="API 版本">v1.0.0</el-descriptions-item>
        <el-descriptions-item label="部署环境">
          <el-tag type="info">{{ envDisplay }}</el-tag>
        </el-descriptions-item>
      </el-descriptions>
      <div class="status-actions">
        <el-button @click="checkHealth"><el-icon><Refresh /></el-icon>刷新状态</el-button>
      </div>
    </el-card>

    <!-- 配置管理卡片 -->
    <el-card shadow="hover" class="config-card">
      <template #header>
        <div class="card-header">
          <span>系统配置管理</span>
          <div class="header-actions">
            <el-button size="small" @click="initializeConfigs" :loading="initLoading">
              <el-icon><Setting /></el-icon>初始化配置
            </el-button>
            <el-button type="primary" size="small" @click="refreshConfigs">
              <el-icon><Refresh /></el-icon>刷新
            </el-button>
          </div>
        </div>
      </template>

      <!-- 加载状态 -->
      <div v-if="loading" class="loading-container">
        <el-icon class="is-loading" size="32"><Loading /></el-icon>
        <span>加载配置中...</span>
      </div>

      <!-- 配置内容 -->
      <div v-else>
        <!-- 分组标签页 -->
        <el-tabs v-model="activeGroup" class="config-tabs">
          <el-tab-pane
            v-for="group in groups"
            :key="group.key"
            :label="`${group.name} (${group.count})`"
            :name="group.key"
          >
            <div class="config-list">
              <el-table :data="getGroupConfigs(group.key)" stripe style="width: 100%">
                <el-table-column prop="name" label="配置项" width="180">
                  <template #default="{ row }">
                    <div>
                      <div class="config-name">{{ row.name || row.key }}</div>
                      <div class="config-key">{{ row.key }}</div>
                    </div>
                  </template>
                </el-table-column>
                <el-table-column prop="description" label="描述" min-width="200">
                  <template #default="{ row }">
                    <span class="config-desc">{{ row.description || '-' }}</span>
                  </template>
                </el-table-column>
                <el-table-column label="类型" width="80">
                  <template #default="{ row }">
                    <el-tag size="small" :type="getTypeTagType(row.value_type)">
                      {{ row.value_type }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column label="值" min-width="200">
                  <template #default="{ row }">
                    <!-- 布尔值 -->
                    <el-switch
                      v-if="row.value_type === 'boolean'"
                      v-model="row._displayValue"
                      @change="handleBooleanChange(row, $event)"
                      :disabled="!row.editable"
                      active-text="是"
                      inactive-text="否"
                    />
                    <!-- 数字值 -->
                    <el-input-number
                      v-else-if="row.value_type === 'number'"
                      v-model="row._displayValue"
                      :min="getNumberMin(row.key)"
                      :max="getNumberMax(row.key)"
                      :step="getNumberStep(row.key)"
                      :precision="getNumberPrecision(row.key)"
                      size="small"
                      :disabled="!row.editable"
                      @change="handleValueChange(row)"
                      controls-position="right"
                      style="width: 150px"
                    />
                    <!-- 字符串值 -->
                    <div v-else class="value-input">
                      <el-input
                        v-model="row._displayValue"
                        size="small"
                        :type="row.sensitive ? 'password' : 'text'"
                        :disabled="!row.editable"
                        @blur="handleValueChange(row)"
                        style="width: 200px"
                      >
                        <template #append v-if="row.sensitive">
                          <el-button
                            :icon="row._showPassword ? 'View' : 'Hide'"
                            @click="row._showPassword = !row._showPassword"
                          />
                        </template>
                      </el-input>
                    </div>
                  </template>
                </el-table-column>
                <el-table-column label="操作" width="100" fixed="right">
                  <template #default="{ row }">
                    <div class="action-buttons">
                      <el-button
                        type="primary"
                        size="small"
                        @click="saveConfig(row)"
                        :disabled="!row.editable || !row._modified"
                        :loading="row._saving"
                      >
                        保存
                      </el-button>
                    </div>
                  </template>
                </el-table-column>
              </el-table>

              <!-- 分组统计 -->
              <div class="group-summary">
                共 {{ getGroupConfigs(group.key).length }} 项配置
              </div>
            </div>
          </el-tab-pane>
        </el-tabs>
      </div>
    </el-card>

    <!-- 关于系统卡片 -->
    <el-card shadow="hover" class="about-card">
      <template #header><span>关于系统</span></template>
      <div class="about-content">
        <div class="about-logo"><el-icon size="64" color="#409EFF"><ChatLineSquare /></el-icon></div>
        <h2>RAG 知识库问答系统</h2>
        <p class="version">版本 1.0.0</p>
        <p class="description">基于 RAG 技术的智能问答系统，支持文档上传、智能问答、知识库管理等功能。</p>
        <div class="tech-stack">
          <el-tag v-for="tech in techStack" :key="tech" size="small">{{ tech }}</el-tag>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { ChatLineSquare, Refresh, Loading, Setting } from '@element-plus/icons-vue'
import { healthCheck, getConfigs, getConfigGroups, updateConfig, initializeConfigs as initConfigsAPI } from '@/api'

interface ConfigItem {
  key: string
  value: string
  raw_value?: string
  value_type: string
  group: string
  name?: string
  description?: string
  editable: boolean
  sensitive: boolean
  _displayValue: any
  _originalValue: any
  _modified: boolean
  _saving: boolean
  _showPassword?: boolean
}

interface GroupItem {
  key: string
  name: string
  count: number
}

const systemHealth = ref<'healthy' | 'unhealthy'>('unhealthy')
const loading = ref(false)
const initLoading = ref(false)
const activeGroup = ref('')
const groups = ref<GroupItem[]>([])
const configs = ref<ConfigItem[]>([])

const techStack = ['FastAPI', 'Milvus', 'Redis', 'MySQL', 'Vue 3', 'Element Plus']

const envDisplay = computed(() => {
  const env = configs.value.find(c => c.key === 'APP_ENV')
  return env?._displayValue === 'production' ? '生产环境' : '开发环境'
})

const getGroupConfigs = (group: string) => {
  return configs.value.filter(c => c.group === group)
}

const getTypeTagType = (type: string) => {
  const map: Record<string, string> = {
    string: 'info',
    number: 'success',
    boolean: 'warning',
    json: 'danger'
  }
  return map[type] || 'info'
}

const getNumberMin = (key: string) => {
  const mins: Record<string, number> = {
    APP_PORT: 1,
    MYSQL_PORT: 1,
    REDIS_PORT: 1,
    MILVUS_PORT: 1,
    RETRIEVAL_TOP_K: 1,
    SIMILARITY_THRESHOLD: 0,
    MMR_DIVERSITY: 0,
    CACHE_DEFAULT_TTL: 60,
    MAX_FILE_SIZE: 1024,
  }
  return mins[key] ?? 0
}

const getNumberMax = (key: string) => {
  const maxs: Record<string, number> = {
    APP_PORT: 65535,
    MYSQL_PORT: 65535,
    REDIS_PORT: 65535,
    MILVUS_PORT: 65535,
    RETRIEVAL_TOP_K: 50,
    SIMILARITY_THRESHOLD: 1,
    MMR_DIVERSITY: 1,
  }
  return maxs[key] ?? 999999
}

const getNumberStep = (key: string) => {
  const steps: Record<string, number> = {
    SIMILARITY_THRESHOLD: 0.05,
    MMR_DIVERSITY: 0.1,
    CACHE_DEFAULT_TTL: 60,
  }
  return steps[key] ?? 1
}

const getNumberPrecision = (key: string) => {
  const precisions: Record<string, number> = {
    SIMILARITY_THRESHOLD: 2,
    MMR_DIVERSITY: 2,
  }
  return precisions[key] ?? 0
}

const parseDisplayValue = (config: ConfigItem) => {
  const val = config.raw_value ?? config.value
  switch (config.value_type) {
    case 'number':
      return Number(val) || 0
    case 'boolean':
      return val?.toLowerCase() === 'true' || val === '1'
    default:
      return val || ''
  }
}

const checkHealth = async () => {
  try {
    const res: any = await healthCheck()
    systemHealth.value = res.status || 'unhealthy'
  } catch {
    systemHealth.value = 'unhealthy'
  }
}

const fetchGroups = async () => {
  try {
    const res: any = await getConfigGroups()
    if (res.data && Array.isArray(res.data)) {
      groups.value = res.data
      if (groups.value.length > 0 && !activeGroup.value) {
        activeGroup.value = groups.value[0].key
      }
    }
  } catch (error) {
    console.error('Failed to fetch groups:', error)
  }
}

const fetchConfigs = async () => {
  loading.value = true
  try {
    const res: any = await getConfigs()
    if (res.data && Array.isArray(res.data)) {
      configs.value = res.data.map((c: any) => ({
        ...c,
        _displayValue: parseDisplayValue(c),
        _originalValue: c.raw_value ?? c.value,
        _modified: false,
        _saving: false,
        _showPassword: false,
      }))
    }
  } catch (error) {
    console.error('Failed to fetch configs:', error)
    ElMessage.error('加载配置失败')
  } finally {
    loading.value = false
  }
}

const refreshConfigs = async () => {
  await Promise.all([fetchGroups(), fetchConfigs()])
  ElMessage.success('配置已刷新')
}

const handleValueChange = (row: ConfigItem) => {
  const currentVal = String(row._displayValue ?? '')
  const originalVal = row._originalValue ?? ''
  row._modified = currentVal !== originalVal
}

const handleBooleanChange = (row: ConfigItem, value: boolean) => {
  row._displayValue = value
  handleValueChange(row)
}

const saveConfig = async (row: ConfigItem) => {
  if (!row.editable) {
    ElMessage.warning('该配置不可编辑')
    return
  }

  row._saving = true
  try {
    let value = row._displayValue
    if (row.value_type === 'boolean') {
      value = value ? 'true' : 'false'
    } else if (row.value_type === 'number') {
      value = String(value)
    } else {
      value = String(value)
    }

    const res: any = await updateConfig(row.key, value)
    if (res.success) {
      row._originalValue = value
      row._modified = false
      ElMessage.success(`配置 ${row.name || row.key} 已保存`)
    } else {
      ElMessage.error(res.message || '保存失败')
    }
  } catch (error: any) {
    console.error('Failed to save config:', error)
    ElMessage.error(error?.response?.data?.detail || '保存失败')
  } finally {
    row._saving = false
  }
}

const initializeConfigs = async () => {
  initLoading.value = true
  try {
    const res: any = await initConfigsAPI()
    if (res.success) {
      ElMessage.success(res.message || '配置初始化成功')
      await refreshConfigs()
    } else {
      ElMessage.error(res.message || '初始化失败')
    }
  } catch (error) {
    console.error('Failed to initialize configs:', error)
    ElMessage.error('初始化失败')
  } finally {
    initLoading.value = false
  }
}

onMounted(async () => {
  await checkHealth()
  await fetchGroups()
  await fetchConfigs()
})
</script>

<style scoped>
.system-page { max-width: 1200px; margin: 0 auto; }
.status-card, .config-card, .about-card { margin-bottom: 20px; }
.status-actions { margin-top: 16px; padding-top: 16px; border-top: 1px solid #ebeef5; }
.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 0;
  gap: 16px;
  color: #909399;
}
.card-header { display: flex; justify-content: space-between; align-items: center; }
.header-actions { display: flex; gap: 8px; }
.config-tabs { margin-top: 0; }
.config-list { padding: 16px 0; }
.config-name { font-weight: 500; color: #303133; }
.config-key { font-size: 12px; color: #909399; font-family: monospace; }
.config-desc { font-size: 13px; color: #606266; }
.value-input { display: flex; align-items: center; }
.group-summary {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #ebeef5;
  color: #909399;
  font-size: 13px;
  text-align: right;
}
.about-content { text-align: center; padding: 20px; }
.about-logo { margin-bottom: 16px; }
.about-content h2 { margin-bottom: 8px; color: #303133; }
.version { color: #909399; margin-bottom: 16px; }
.description { color: #606266; line-height: 1.8; margin-bottom: 20px; max-width: 600px; margin-left: auto; margin-right: auto; }
.tech-stack { display: flex; justify-content: center; gap: 8px; flex-wrap: wrap; }
.action-buttons { display: flex; gap: 4px; }
</style>
