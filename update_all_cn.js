const fs = require('fs');

function updateFile(filePath) {
  let content = fs.readFileSync(filePath, 'utf8');
  
  // Comprehensive replacements
  content = content
    // Dashboard
    .replace(/Perf/gi, '系统性能')
    .replace(/Cache Rate/g, '缓存命中率')
    .replace(/Avg Time/gi, '平均响应时间')
    .replace(/KB Overview/g, '知识库概览')
    .replace(/Docs/gi, '文档数量')
    .replace(/Chunks/gi, '文档块数')
    .replace(/Queries/gi, '问答次数')
    .replace(/Today/gi, '今日问答')
    .replace(/Actions/gi, '快捷操作')
    .replace(/QA\b/g, '开启问答')
    .replace(/Upload/gi, '上传文档')
    .replace(/Rebuild/gi, '重建索引')
    .replace(/Refresh/gi, '刷新数据')
    .replace(/Rebuild started/gi, '重建任务已启动')
    .replace(/Refreshed/gi, '数据已刷新')
    // QA
    .replace(/Smart Q&A/gi, '智能问答')
    .replace(/Based on Knowledge Base/gi, '基于知识库内容回答')
    .replace(/Enter your question/gi, '请输入您的问题')
    .replace(/Ask/gi, '提问')
    .replace(/Answer/gi, '回答')
    .replace(/Cache Hit/gi, '命中缓存')
    .replace(/Generated/gi, '实时生成')
    .replace(/Time:/gi, '耗时')
    .replace(/Sources/gi, '参考来源')
    .replace(/Similarity:/gi, '相似度')
    .replace(/History/gi, '历史记录')
    .replace(/No history yet/gi, '暂无历史记录')
    .replace(/Loading\.\.\./gi, '加载中')
    .replace(/Answer generated/gi, '回答已生成')
    // Layout
    .replace(/RAG QA System/g, 'RAG 问答系统')
    .replace(/Dashboard/g, '仪表盘')
    .replace(/Q&A/g, '知识问答')
    .replace(/Documents/g, '文档管理')
    .replace(/Knowledge Base/g, '知识库管理')
    .replace(/Settings/g, '系统设置')
    .replace(/Healthy/g, '系统正常')
    .replace(/Error/g, '异常')
    // Login
    .replace(/System Login/g, '系统登录')
    .replace(/Username/g, '用户名')
    .replace(/Password/g, '密码')
    .replace(/Enter username/g, '请输入用户名')
    .replace(/Enter password/g, '请输入密码')
    .replace(/Please enter username/g, '请输入用户名')
    .replace(/Please enter password/g, '请输入密码')
    .replace(/Login/g, '登录')
    .replace(/Login successful/g, '登录成功')
    .replace(/Login failed/g, '登录失败')
    // Knowledge
    .replace(/Vector Count/g, '向量数量')
    .replace(/Last Updated/g, '最后更新')
    .replace(/Rebuild Knowledge Base Index/g, '重建知识库索引')
    .replace(/Rebuild index will reprocess/g, '重建索引将重新处理')
    .replace(/This operation may take/g, '此操作可能需要')
    .replace(/Clear Cache/g, '清除缓存')
    .replace(/Clear Q&A history/g, '清除问答历史')
    .replace(/Knowledge Base Search Test/g, '知识库检索测试')
    .replace(/Enter search query/g, '输入测试查询内容')
    .replace(/Search Results/g, '检索结果')
    .replace(/fragments found/g, '个相关片段')
    .replace(/Fragment/g, '片段')
    .replace(/No results found/g, '未找到相关结果')
    // Documents
    .replace(/Search document name/g, '搜索文档名称')
    .replace(/Status filter/g, '状态筛选')
    .replace(/All/gi, '全部')
    .replace(/Processing/gi, '处理中')
    .replace(/Completed/gi, '已完成')
    .replace(/Failed/gi, '失败')
    .replace(/Upload Document/g, '上传文档')
    .replace(/No documents yet/g, '暂无文档')
    .replace(/Document Name/g, '文档名称')
    .replace(/Type/g, '类型')
    .replace(/Size/g, '大小')
    .replace(/Status/g, '状态')
    .replace(/Chunks/gi, '文档块')
    .replace(/Upload Time/g, '上传时间')
    .replace(/Actions/g, '操作')
    .replace(/Preview/g, '预览')
    .replace(/Delete/g, '删除')
    .replace(/Drop files here or/g, '将文件拖到此处，或')
    .replace(/click to upload/g, '点击上传')
    .replace(/Supports PDF/g, '支持 PDF')
    .replace(/Cancel/g, '取消')
    .replace(/Start Upload/g, '开始上传')
    .replace(/Document Preview/g, '文档预览')
    .replace(/Please select files/g, '请选择要上传的文件')
    .replace(/uploaded successfully/g, '上传成功')
    .replace(/upload failed/g, '上传失败')
    .replace(/Unable to preview/g, '无法预览此文档')
    .replace(/Preview loading failed/g, '预览加载失败')
    .replace(/Are you sure you want to delete/g, '确定要删除文档')
    .replace(/Confirm Delete/g, '确认删除')
    .replace(/Deleted successfully/g, '删除成功')
    // System
    .replace(/System Status/g, '系统状态')
    .replace(/Health Check/g, '健康检查')
    .replace(/Normal/g, '正常')
    .replace(/API Version/g, 'API 版本')
    .replace(/Development/g, '开发环境')
    .replace(/Refresh Status/g, '刷新状态')
    .replace(/System Configuration/g, '系统配置')
    .replace(/LLM Model/g, 'LLM 模型')
    .replace(/Embedding Model/g, 'Embedding 模型')
    .replace(/Chunk Size/g, '分块大小')
    .replace(/Chunk Overlap/g, '分块重叠')
    .replace(/Top K Retrieval/g, 'Top K 检索数')
    .replace(/Similarity Threshold/g, '相似度阈值')
    .replace(/MySQL Database/g, 'MySQL 数据库')
    .replace(/Refresh Config/g, '刷新配置')
    .replace(/Environment Variables/g, '环境变量配置')
    .replace(/Variable Name/g, '变量名')
    .replace(/Description/g, '说明')
    .replace(/Required/g, '必填')
    .replace(/Yes/g, '是')
    .replace(/No/g, '否')
    .replace(/About/g, '关于系统')
    .replace(/RAG Knowledge Base/g, 'RAG 知识库')
    .replace(/Version/g, '版本')
    .replace(/An intelligent/g, '基于 RAG')
    .replace(/technology\./g, '技术的智能问答系统')
    .replace(/Supports document/g, '支持文档上传')
    .replace(/DeepSeek API key/g, 'DeepSeek API 密钥')
    .replace(/DeepSeek API base URL/g, 'DeepSeek API 基础地址')
    .replace(/DeepSeek model name/g, 'DeepSeek 模型名称')
    .replace(/MySQL database/g, 'MySQL 数据库连接')
    .replace(/Redis connection/g, 'Redis 连接')
    .replace(/Embedding model name/g, 'Embedding 模型名称')
    .replace(/Document chunk size/g, '文档分块大小')
    .replace(/Document chunk overlap/g, '文档分块重叠');

  // Write with UTF-8 BOM
  const bom = Buffer.from([0xEF, 0xBB, 0xBF]);
  const contentBuffer = Buffer.from(content, 'utf8');
  fs.writeFileSync(filePath, Buffer.concat([bom, contentBuffer]));
  
  return content.includes('系统性能');
}

// Update all Vue files
const files = [
  'D:/work/agentV1/rag-qa-frontend/src/views/Dashboard.vue',
  'D:/work/agentV1/rag-qa-frontend/src/views/QA.vue',
  'D:/work/agentV1/rag-qa-frontend/src/views/Layout.vue',
  'D:/work/agentV1/rag-qa-frontend/src/views/Login.vue',
  'D:/work/agentV1/rag-qa-frontend/src/views/Knowledge.vue',
  'D:/work/agentV1/rag-qa-frontend/src/views/Documents.vue',
  'D:/work/agentV1/rag-qa-frontend/src/views/System.vue',
  'D:/work/agentV1/rag-qa-frontend/src/router/index.ts',
  'D:/work/agentV1/rag-qa-frontend/index.html'
];

files.forEach(f => {
  const result = updateFile(f);
  console.log(f.split('/').pop() + ': ' + (result ? 'OK' : 'No changes'));
});
