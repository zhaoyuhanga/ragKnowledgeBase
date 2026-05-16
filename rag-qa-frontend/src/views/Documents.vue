<template>
  <div class="documents-page">
    <el-card shadow="hover" class="toolbar-card">
      <div class="toolbar">
        <div class="toolbar-left">
          <el-input v-model="searchKeyword" placeholder="搜索文档名称" style="width: 300px" clearable>
            <template #prefix><el-icon><Search /></el-icon></template>
          </el-input>
          <el-select v-model="statusFilter" placeholder="状态筛选" style="width: 150px">
            <el-option label="全部" value="" />
            <el-option label="处理中" value="processing" />
            <el-option label="已完成" value="completed" />
            <el-option label="失败" value="failed" />
          </el-select>
        </div>
        <div class="toolbar-right">
          <el-button type="primary" @click="showUploadDialog"><el-icon><Upload /></el-icon>上传文档</el-button>
          <el-button @click="fetchDocuments"><el-icon><Refresh /></el-icon>刷新</el-button>
        </div>
      </div>
    </el-card>

    <el-card shadow="hover" class="documents-card">
      <div v-if="loading" class="loading-container"><el-icon class="is-loading"><Loading /></el-icon><span>加载中...</span></div>
      <div v-else-if="documents.length === 0" class="empty-state"><el-icon><Document /></el-icon><p>暂无文档</p><el-button type="primary" @click="showUploadDialog">上传文档</el-button></div>
      <div v-else class="documents-table">
        <el-table :data="filteredDocuments" stripe style="width: 100%">
          <el-table-column prop="filename" label="文档名称" min-width="200">
            <template #default="{ row }"><div class="document-title"><el-icon><Document /></el-icon><span>{{ row.filename }}</span></div></template>
          </el-table-column>
          <el-table-column prop="file_type" label="类型" width="100">
            <template #default="{ row }"><el-tag size="small" :type="getFileTypeTag(row.file_type)">{{ row.file_type.toUpperCase() }}</el-tag></template>
          </el-table-column>
          <el-table-column prop="file_size" label="大小" width="120"><template #default="{ row }">{{ formatFileSize(row.file_size) }}</template></el-table-column>
          <el-table-column prop="status" label="状态" width="100">
            <template #default="{ row }"><el-tag :type="getStatusType(row.status)" size="small">{{ getStatusText(row.status) }}</el-tag></template>
          </el-table-column>
          <el-table-column prop="chunk_count" label="文档块" width="100" align="center" />
          <el-table-column prop="created_at" label="上传时间" width="180"><template #default="{ row }">{{ formatTime(row.created_at) }}</template></el-table-column>
          <el-table-column label="操作" width="200" fixed="right">
            <template #default="{ row }">
              <el-button link type="primary" size="small" @click="previewDocument(row)">预览</el-button>
              <el-button link type="danger" size="small" @click="handleDelete(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
        <div class="pagination-wrapper">
          <el-pagination v-model:current-page="currentPage" v-model:page-size="pageSize" :total="total" :page-sizes="[10, 20, 50, 100]" layout="total, sizes, prev, pager, next, jumper" @size-change="fetchDocuments" @current-change="fetchDocuments" />
        </div>
      </div>
    </el-card>

    <el-dialog v-model="uploadDialogVisible" title="上传文档" width="500px" @closed="handleUploadClosed">
      <el-upload ref="uploadRef" class="upload-area" drag :auto-upload="false" :on-change="handleFileChange" :on-remove="handleFileRemove" :limit="10" accept=".pdf,.docx,.doc,.txt,.md" multiple>
        <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
        <div class="el-upload__text">将文件拖到此处，或<em>点决上传</em></div>
        <template #tip><div class="el-upload__tip">支持 PDF、DOCX、DOC、TXT、MD 格式，单个文件不超过 50MB</div></template>
      </el-upload>
      <template #footer>
        <el-button @click="uploadDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="uploading" @click="handleUpload">开始上传</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="previewDialogVisible" title="文档预览" width="800px" destroy-on-close>
      <div v-if="previewLoading" class="loading-container"><el-icon class="is-loading"><Loading /></el-icon><span>加载中...</span></div>
      <div v-else class="preview-content markdown-content" v-html="previewContent"></div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { marked } from 'marked'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Refresh, Upload, Document, Loading, UploadFilled } from '@element-plus/icons-vue'
import { getDocuments, deleteDocument, previewDocument as previewAPI, uploadDocument as uploadAPI } from '@/api'
import type { Document as DocumentType } from '@/types'
import type { UploadInstance } from 'element-plus'

const documents = ref<DocumentType[]>([])
const loading = ref(false)
const currentPage = ref(1)
const pageSize = ref(10)
const total = ref(0)
const searchKeyword = ref('')
const statusFilter = ref('')
const uploadDialogVisible = ref(false)
const uploadRef = ref<UploadInstance>()
const fileList = ref<any[]>([])
const uploading = ref(false)
const previewDialogVisible = ref(false)
const previewLoading = ref(false)
const previewContent = ref('')

const filteredDocuments = computed(() => {
  if (!searchKeyword.value) return documents.value
  return documents.value.filter(doc => doc.filename?.toLowerCase().includes(searchKeyword.value.toLowerCase()))
})

const formatFileSize = (size: number) => {
  if (size < 1024) return size + ' B'
  if (size < 1024 * 1024) return (size / 1024).toFixed(2) + ' KB'
  return (size / (1024 * 1024)).toFixed(2) + ' MB'
}

const formatTime = (time: string) => { return new Date(time).toLocaleString('zh-CN') }

const getFileTypeTag = (type: string) => {
  const map: Record<string, string> = { pdf: 'danger', docx: 'primary', doc: 'primary', txt: 'info', md: 'success' }
  return map[type] || 'info'
}

const getStatusType = (status: number) => {
  const map: Record<number, string> = { 0: 'info', 1: 'success', 2: 'danger' }
  return map[status] || 'info'
}

const getStatusText = (status: number) => {
  const map: Record<number, string> = { 0: '处理中', 1: '已完成', 2: '失败' }
  return map[status] || String(status)
}

const fetchDocuments = async () => {
  loading.value = true
  try {
    const res = await getDocuments({ page: currentPage.value, page_size: pageSize.value, status: statusFilter.value || undefined })
    documents.value = res.data.items
    total.value = res.data.total
  } catch (error) { console.error('Failed to fetch documents:', error) }
  finally { loading.value = false }
}

const showUploadDialog = () => { uploadDialogVisible.value = true }
const handleFileChange = (_file: any, files: any[]) => { fileList.value = files }
const handleFileRemove = (_file: any, files: any[]) => { fileList.value = files }
const handleUploadClosed = () => { fileList.value = []; uploadRef.value?.clearFiles() }

const handleUpload = async () => {
  if (fileList.value.length === 0) { ElMessage.warning('请选择要上传的文件'); return }
  uploading.value = true
  let successCount = 0
  try {
    for (const file of fileList.value) {
      const formData = new FormData()
      formData.append('file', file.raw)
      try {
        await uploadAPI(formData)
        ElMessage.success(file.name + ' 上传成功')
        successCount++
      } catch (error) {
        console.error(file.name + ' 上传失败:', error)
        ElMessage.error(file.name + ' 上传失败')
      }
    }
    if (successCount > 0) { uploadDialogVisible.value = false; fetchDocuments() }
  } finally { uploading.value = false }
}

const previewDocument = async (doc: DocumentType) => {
  previewDialogVisible.value = true; previewLoading.value = true
  try {
    const res = await previewAPI(doc.id)
    previewContent.value = marked(res.data.content || '无法预览此文档')
  } catch (error) { previewContent.value = '<p>预览加载失败</p>' }
  finally { previewLoading.value = false }
}

const handleDelete = async (doc: DocumentType) => {
  try {
    await ElMessageBox.confirm('确定要删除文档 "' + doc.filename + '"?', '确认删除', { type: 'warning' })
    await deleteDocument(doc.id)
    ElMessage.success('删除成功')
    fetchDocuments()
  } catch (error: any) { if (error !== 'cancel') console.error('Delete failed:', error) }
}

onMounted(() => { fetchDocuments() })
</script>

<style scoped>
.documents-page { max-width: 1400px; margin: 0 auto; }
.toolbar-card { margin-bottom: 20px; }
.toolbar { display: flex; justify-content: space-between; align-items: center; }
.toolbar-left, .toolbar-right { display: flex; gap: 12px; }
.loading-container { display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 60px 0; gap: 12px; color: #909399; }
.empty-state { text-align: center; padding: 80px 0; color: #909399; }
.empty-state .el-icon { font-size: 64px; margin-bottom: 16px; }
.empty-state p { margin-bottom: 20px; font-size: 16px; }
.document-title { display: flex; align-items: center; gap: 8px; }
.document-title .el-icon { color: #409EFF; }
.pagination-wrapper { margin-top: 20px; display: flex; justify-content: flex-end; }
.upload-area { width: 100%; }
.preview-content { max-height: 500px; overflow-y: auto; padding: 20px; background: #f9fafb; border-radius: 8px; }
</style>
