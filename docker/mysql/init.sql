-- ================================================
-- RAG 数据库初始化脚本
-- 版本: v2.0
-- 基于后端 ORM 模型自动生成
-- MySQL 8.0+
-- ================================================

-- 创建数据库（如果不存在）
CREATE DATABASE IF NOT EXISTS rag_db DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE rag_db;

-- ================================================
-- 1. documents - 文档主表
-- ================================================
DROP TABLE IF EXISTS documents;
CREATE TABLE documents (
    id BIGINT NOT NULL AUTO_INCREMENT COMMENT '文档主键ID',
    name VARCHAR(255) NOT NULL COMMENT '文档名称',
    doc_type VARCHAR(50) NOT NULL COMMENT '文档类型：docx/doc/pdf/txt/md/html/xlsx/png/jpg/jpeg',
    business_id VARCHAR(100) COMMENT '业务归属ID',
    business_name VARCHAR(100) COMMENT '业务归属名称',
    current_version_id BIGINT COMMENT '当前版本ID',
    total_versions INT NOT NULL DEFAULT 1 COMMENT '版本总数',
    status INT NOT NULL DEFAULT 0 COMMENT '状态：0-待解析 1-解析中 2-已解析 3-解析失败 9-已删除',
    total_pages INT DEFAULT 0 COMMENT '总页数',
    total_chunks INT DEFAULT 0 COMMENT '总 Chunk 数',
    creator_id BIGINT COMMENT '创建人ID',
    creator_name VARCHAR(100) COMMENT '创建人姓名',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    is_deleted INT NOT NULL DEFAULT 0 COMMENT '是否删除：0-否 1-是',
    PRIMARY KEY (id),
    INDEX idx_documents_business_id (business_id),
    INDEX idx_documents_status (status),
    INDEX idx_documents_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='文档主表';

-- ================================================
-- 2. document_versions - 文档版本表
-- ================================================
DROP TABLE IF EXISTS document_versions;
CREATE TABLE document_versions (
    id BIGINT NOT NULL AUTO_INCREMENT COMMENT '版本主键ID',
    document_id BIGINT NOT NULL COMMENT '文档ID',
    version INT NOT NULL COMMENT '版本号',
    file_hash VARCHAR(64) NOT NULL COMMENT '文件MD5哈希值',
    file_name VARCHAR(255) NOT NULL COMMENT '原始文件名',
    file_size BIGINT NOT NULL COMMENT '文件大小（字节）',
    file_path VARCHAR(500) NOT NULL COMMENT '文件存储路径',
    mime_type VARCHAR(100) COMMENT 'MIME类型',
    storage_type VARCHAR(20) NOT NULL DEFAULT 'local' COMMENT '存储类型：local/oss/s3',
    status INT NOT NULL DEFAULT 0 COMMENT '状态：0-待解析 1-解析中 2-已解析 3-解析失败',
    parse_status VARCHAR(20) COMMENT '解析状态：pending/processing/completed/failed',
    parse_progress INT DEFAULT 0 COMMENT '解析进度（百分比）',
    parse_confidence VARCHAR(10) COMMENT '解析置信度',
    total_pages INT DEFAULT 0 COMMENT '总页数',
    total_elements INT DEFAULT 0 COMMENT '解析元素总数',
    uploader_id BIGINT COMMENT '上传人ID',
    uploader_name VARCHAR(100) COMMENT '上传人姓名',
    uploaded_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '上传时间',
    parsed_at DATETIME COMMENT '解析完成时间',
    error_message TEXT COMMENT '错误信息',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (id),
    INDEX idx_document_versions_document_id (document_id),
    INDEX idx_document_versions_file_hash (file_hash),
    INDEX idx_document_versions_status (status),
    INDEX idx_document_versions_uploaded_at (uploaded_at),
    CONSTRAINT fk_doc_version_document FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='文档版本表';

-- ================================================
-- 3. import_tasks - 导入任务表
-- ================================================
DROP TABLE IF EXISTS import_tasks;
CREATE TABLE import_tasks (
    id BIGINT NOT NULL AUTO_INCREMENT COMMENT '任务主键ID',
    task_id VARCHAR(64) NOT NULL COMMENT '任务唯一ID（UUID）',
    document_id BIGINT COMMENT '关联文档ID',
    version_id BIGINT COMMENT '关联版本ID',
    task_type VARCHAR(20) NOT NULL COMMENT '任务类型：upload/parse/clean/chunk/embed',
    task_status VARCHAR(20) NOT NULL DEFAULT 'pending' COMMENT '任务状态：pending/running/completed/failed/retry',
    priority INT NOT NULL DEFAULT 5 COMMENT '优先级：1-最高 5-普通',
    progress INT NOT NULL DEFAULT 0 COMMENT '进度（百分比）',
    retry_count INT NOT NULL DEFAULT 0 COMMENT '重试次数',
    max_retry INT NOT NULL DEFAULT 3 COMMENT '最大重试次数',
    error_type VARCHAR(50) COMMENT '错误类型',
    error_message TEXT COMMENT '错误信息',
    error_detail TEXT COMMENT '错误详情',
    started_at DATETIME COMMENT '开始时间',
    completed_at DATETIME COMMENT '完成时间',
    cost_seconds INT COMMENT '耗时（秒）',
    payload JSON COMMENT '任务参数',
    result JSON COMMENT '任务结果',
    creator_id BIGINT COMMENT '创建人ID',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (id),
    UNIQUE KEY uk_import_tasks_task_id (task_id),
    INDEX idx_import_tasks_document_id (document_id),
    INDEX idx_import_tasks_version_id (version_id),
    INDEX idx_import_tasks_task_status (task_status),
    INDEX idx_import_tasks_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='导入任务表';

-- ================================================
-- 4. document_elements - 文档解析元素表
-- ================================================
DROP TABLE IF EXISTS document_elements;
CREATE TABLE document_elements (
    id BIGINT NOT NULL AUTO_INCREMENT COMMENT '元素主键ID',
    document_id BIGINT NOT NULL COMMENT '文档ID',
    version_id BIGINT NOT NULL COMMENT '版本ID',
    element_id VARCHAR(64) NOT NULL COMMENT '元素唯一ID',
    page_no INT COMMENT '页码',
    page_start INT COMMENT '起始页',
    page_end INT COMMENT '结束页',
    element_type VARCHAR(20) NOT NULL COMMENT '元素类型：title/paragraph/table/image/chart/list/header/footer/code',
    content TEXT COMMENT '原始文本内容',
    enhanced_content TEXT COMMENT '增强文本内容',
    reading_order INT DEFAULT 0 COMMENT '阅读顺序',
    title_level INT COMMENT '标题层级（1-6）',
    title_path VARCHAR(500) COMMENT '标题层级路径',
    parent_path VARCHAR(500) COMMENT '父级路径',
    bbox JSON COMMENT '元素坐标',
    confidence FLOAT DEFAULT 1.0 COMMENT '识别置信度（0-1）',
    is_merged INT DEFAULT 0 COMMENT '是否跨页合并',
    table_structure JSON COMMENT '表格结构信息',
    image_description JSON COMMENT '图片描述信息',
    element_metadata JSON COMMENT '元数据',
    quality_flag VARCHAR(20) DEFAULT 'good' COMMENT '质量标记：good/warning/bad',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    PRIMARY KEY (id),
    UNIQUE KEY uk_document_elements_element_id (element_id),
    INDEX idx_document_elements_document_version (document_id, version_id),
    INDEX idx_document_elements_page_no (page_no),
    INDEX idx_document_elements_element_type (element_type),
    INDEX idx_document_elements_reading_order (reading_order),
    INDEX idx_document_elements_quality_flag (quality_flag)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='文档解析元素表';

-- ================================================
-- 5. parse_quality_logs - 解析质量日志表
-- ================================================
DROP TABLE IF EXISTS parse_quality_logs;
CREATE TABLE parse_quality_logs (
    id BIGINT NOT NULL AUTO_INCREMENT COMMENT '日志主键ID',
    document_id BIGINT NOT NULL COMMENT '文档ID',
    version_id BIGINT NOT NULL COMMENT '版本ID',
    page_no INT COMMENT '页码',
    element_id VARCHAR(64) COMMENT '元素ID',
    check_type VARCHAR(50) NOT NULL COMMENT '检查类型：ocr/low_confidence/layout/encoding/table/image',
    quality_flag VARCHAR(20) NOT NULL COMMENT '质量标记：good/warning/bad',
    confidence FLOAT COMMENT '置信度',
    issue_description TEXT COMMENT '问题描述',
    suggestion TEXT COMMENT '修复建议',
    resolved INT NOT NULL DEFAULT 0 COMMENT '是否已解决：0-否 1-是',
    resolved_at DATETIME COMMENT '解决时间',
    resolved_by BIGINT COMMENT '解决人ID',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    PRIMARY KEY (id),
    INDEX idx_parse_quality_document_version (document_id, version_id),
    INDEX idx_parse_quality_page_no (page_no),
    INDEX idx_parse_quality_quality_flag (quality_flag),
    INDEX idx_parse_quality_resolved (resolved)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='解析质量日志表';

-- ================================================
-- 6. document_chunks - 文档Chunk表
-- ================================================
DROP TABLE IF EXISTS document_chunks;
CREATE TABLE document_chunks (
    id BIGINT NOT NULL AUTO_INCREMENT COMMENT 'Chunk主键ID',
    document_id BIGINT NOT NULL COMMENT '文档ID',
    version_id BIGINT NOT NULL COMMENT '版本ID',
    chunk_id VARCHAR(64) NOT NULL COMMENT 'Chunk唯一ID',
    chunk_index INT NOT NULL COMMENT 'Chunk索引',
    content TEXT NOT NULL COMMENT 'Chunk原文',
    enhanced_content TEXT COMMENT '增强文本',
    content_hash VARCHAR(64) NOT NULL COMMENT '内容Hash',
    chunk_type VARCHAR(20) NOT NULL COMMENT 'Chunk类型：paragraph/table/image/chart/code/list',
    title_path VARCHAR(500) COMMENT '标题层级路径',
    chapter_path VARCHAR(500) COMMENT '章节路径',
    page_start INT COMMENT '起始页码',
    page_end INT COMMENT '结束页码',
    token_count INT NOT NULL DEFAULT 0 COMMENT 'Token数量',
    char_count INT NOT NULL DEFAULT 0 COMMENT '字符数量',
    element_ids JSON COMMENT '来源元素ID列表',
    quality_score FLOAT COMMENT '质量评分',
    table_summary TEXT COMMENT '表格摘要',
    table_schema JSON COMMENT '表结构',
    image_description JSON COMMENT '图片描述',
    is_duplicate INT NOT NULL DEFAULT 0 COMMENT '是否重复',
    duplicate_of BIGINT COMMENT '重复的Chunk ID',
    status INT NOT NULL DEFAULT 0 COMMENT '状态：0-待处理 1-已向量化 9-已删除',
    vector_id BIGINT COMMENT '向量ID',
    keyword_indexed INT NOT NULL DEFAULT 0 COMMENT '是否已建关键词索引',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (id),
    UNIQUE KEY uk_document_chunks_chunk_id (chunk_id),
    INDEX idx_chunks_document_version (document_id, version_id),
    INDEX idx_chunks_chunk_type (chunk_type),
    INDEX idx_chunks_content_hash (content_hash),
    INDEX idx_chunks_quality_score (quality_score),
    INDEX idx_chunks_status (status),
    INDEX idx_chunks_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='文档Chunk表';

-- ================================================
-- 7. chunk_keyword_index - Chunk关键词索引表
-- ================================================
DROP TABLE IF EXISTS chunk_keyword_index;
CREATE TABLE chunk_keyword_index (
    id BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
    chunk_id BIGINT NOT NULL COMMENT 'Chunk ID',
    term VARCHAR(128) NOT NULL COMMENT '分词词项',
    field VARCHAR(20) NOT NULL DEFAULT 'content' COMMENT '字段：content/title/enhanced',
    tf INT NOT NULL DEFAULT 1 COMMENT '词频',
    idf FLOAT NOT NULL DEFAULT 0.0 COMMENT '逆文档频率',
    position INT COMMENT '词项位置',
    weight FLOAT NOT NULL DEFAULT 1.0 COMMENT '权重',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    PRIMARY KEY (id),
    UNIQUE KEY uk_keyword_chunk_term_field (chunk_id, term, field),
    INDEX idx_keyword_term (term),
    INDEX idx_keyword_chunk_id (chunk_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Chunk关键词索引表';

-- ================================================
-- 8. qa_logs - 问答日志表
-- ================================================
DROP TABLE IF EXISTS qa_logs;
CREATE TABLE qa_logs (
    id BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
    user_id BIGINT COMMENT '用户ID',
    tenant_id BIGINT DEFAULT 1 COMMENT '租户ID',
    session_id VARCHAR(64) COMMENT '会话ID',
    question TEXT NOT NULL COMMENT '用户问题',
    answer TEXT COMMENT '生成的答案',
    `references` JSON COMMENT '引用来源列表',
    vector_results JSON COMMENT '向量检索结果',
    keyword_results JSON COMMENT '关键词检索结果',
    fusion_results JSON COMMENT '融合检索结果',
    reranked_results JSON COMMENT '重排后结果',
    retrieval_time_ms INT COMMENT '检索耗时(毫秒)',
    generation_time_ms INT COMMENT '生成耗时(毫秒)',
    total_time_ms INT COMMENT '总耗时(毫秒)',
    quality_score INT COMMENT '答案质量评分',
    feedback VARCHAR(50) COMMENT '用户反馈：helpful/not_helpful/null',
    feedback_remark TEXT COMMENT '反馈备注',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    PRIMARY KEY (id),
    INDEX idx_qa_logs_user_id (user_id),
    INDEX idx_qa_logs_tenant_id (tenant_id),
    INDEX idx_qa_logs_session_id (session_id),
    INDEX idx_qa_logs_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='问答日志表';

-- ================================================
-- 9. feedback_analysis - 反馈分析表
-- ================================================
DROP TABLE IF EXISTS feedback_analysis;
CREATE TABLE feedback_analysis (
    id BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
    qa_log_id BIGINT NOT NULL COMMENT '问答日志ID',
    issue_type VARCHAR(50) COMMENT '问题类型：retrieval/generation/both',
    issue_category VARCHAR(100) COMMENT '问题分类',
    issue_description TEXT COMMENT '问题描述',
    involved_chunks TEXT COMMENT '涉及Chunk ID列表',
    retrieval_score BIGINT COMMENT '检索质量评分（1-5）',
    generation_score BIGINT COMMENT '生成质量评分（1-5）',
    suggestions TEXT COMMENT '改进建议列表',
    suggestion_type VARCHAR(100) COMMENT '建议类型',
    handled_status BIGINT DEFAULT 0 COMMENT '处理状态：0-未处理 1-已处理 2-已忽略',
    handler_id BIGINT COMMENT '处理人ID',
    handled_at DATETIME COMMENT '处理时间',
    handler_remark TEXT COMMENT '处理备注',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    PRIMARY KEY (id),
    INDEX idx_feedback_analysis_qa_log_id (qa_log_id),
    INDEX idx_feedback_analysis_issue_type (issue_type),
    INDEX idx_feedback_analysis_handled_status (handled_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='反馈分析表';

-- ================================================
-- 10. optimization_rules - 优化规则表
-- ================================================
DROP TABLE IF EXISTS optimization_rules;
CREATE TABLE optimization_rules (
    id BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
    rule_name VARCHAR(200) NOT NULL COMMENT '规则名称',
    rule_type VARCHAR(50) NOT NULL COMMENT '规则类型：cleaning/chunking/retrieval/rerank',
    rule_config TEXT COMMENT '规则配置（JSON格式）',
    trigger_condition TEXT COMMENT '触发条件（JSON格式）',
    priority BIGINT DEFAULT 2 COMMENT '优先级：1-高 2-中 3-低',
    enabled BIGINT DEFAULT 1 COMMENT '启用状态：0-禁用 1-启用',
    description TEXT COMMENT '规则描述',
    applicable_scope TEXT COMMENT '应用范围（JSON格式）',
    expected_effect TEXT COMMENT '预期效果',
    actual_effect TEXT COMMENT '实际效果评估',
    creator_id BIGINT COMMENT '创建人ID',
    updater_id BIGINT COMMENT '最后修改人ID',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (id),
    INDEX idx_optimization_rules_rule_type (rule_type),
    INDEX idx_optimization_rules_enabled (enabled),
    INDEX idx_optimization_rules_priority (priority)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='优化规则表';

-- ================================================
-- 11. cleaning_rules - 清洗规则表
-- ================================================
DROP TABLE IF EXISTS cleaning_rules;
CREATE TABLE cleaning_rules (
    id BIGINT NOT NULL AUTO_INCREMENT COMMENT '规则主键ID',
    name VARCHAR(100) NOT NULL COMMENT '规则名称',
    rule_type VARCHAR(50) NOT NULL COMMENT '规则类型：regex_delete/regex_replace/struct_delete/quality_control/desensitization',
    rule_config JSON NOT NULL COMMENT '规则配置（JSON格式）',
    priority INT NOT NULL DEFAULT 100 COMMENT '优先级（数字越小越优先）',
    is_enabled INT NOT NULL DEFAULT 1 COMMENT '是否启用：0-禁用 1-启用',
    scope VARCHAR(100) COMMENT '适用范围：all/pdf/docx/image/table',
    business_scope VARCHAR(255) COMMENT '业务范围筛选',
    description VARCHAR(500) COMMENT '规则说明',
    effect_count INT NOT NULL DEFAULT 0 COMMENT '生效次数',
    creator_id BIGINT COMMENT '创建人ID',
    creator_name VARCHAR(100) COMMENT '创建人姓名',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    is_deleted INT NOT NULL DEFAULT 0 COMMENT '是否删除',
    PRIMARY KEY (id),
    INDEX idx_cleaning_rule_type (rule_type),
    INDEX idx_cleaning_is_enabled (is_enabled),
    INDEX idx_cleaning_priority (priority)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='清洗规则表';

-- ================================================
-- 12. cleaning_logs - 清洗日志表
-- ================================================
DROP TABLE IF EXISTS cleaning_logs;
CREATE TABLE cleaning_logs (
    id BIGINT NOT NULL AUTO_INCREMENT COMMENT '日志主键ID',
    document_id BIGINT NOT NULL COMMENT '文档ID',
    version_id BIGINT NOT NULL COMMENT '版本ID',
    element_id VARCHAR(64) COMMENT '元素ID',
    rule_id BIGINT COMMENT '规则ID',
    rule_name VARCHAR(100) COMMENT '规则名称',
    rule_type VARCHAR(50) COMMENT '规则类型',
    action VARCHAR(20) NOT NULL COMMENT '操作：delete/replace/mask/score',
    before_content TEXT COMMENT '处理前内容摘要',
    after_content TEXT COMMENT '处理后内容摘要',
    hit_count INT NOT NULL DEFAULT 1 COMMENT '命中次数',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    PRIMARY KEY (id),
    INDEX idx_cleaning_document_version (document_id, version_id),
    INDEX idx_cleaning_rule_id (rule_id),
    INDEX idx_cleaning_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='清洗日志表';

-- ================================================
-- 初始化预置清洗规则数据
-- ================================================
INSERT INTO cleaning_rules (name, rule_type, rule_config, priority, scope, description) VALUES
('特殊符号清理', 'regex_replace', '{"pattern": "[\\\\x00-\\\\x08\\\\x0b\\\\x0c\\\\x0e-\\\\x1f\\\\x7f]", "replacement": ""}', 5, 'all', '删除控制字符'),
('页眉清洗', 'regex_delete', '{"patterns": ["^第\\\\s*\\\\d+\\\\s*页$", "^Page\\\\s+\\\\d+$", "^\\\\d+/\\\\d+$", "^[上下]篇$"]}', 10, 'all', '删除常见的页眉标记'),
('页脚清洗', 'regex_delete', '{"patterns": ["^©\\\\s*\\\\d{4}", "^版权所有", "^未经授权", "^Confidential$"]}', 11, 'all', '删除常见的页脚标记'),
('水印清洗', 'regex_delete', '{"patterns": ["^草稿$", "^内部资料$", "^机密$", "^Draft$"]}', 12, 'all', '删除水印文字'),
('空白归一化', 'regex_replace', '{"pattern": "\\\\s+", "replacement": " "}', 20, 'all', '将多个空白字符替换为单个空格'),
('广告清洗', 'regex_delete', '{"patterns": ["立即购买", "点击查看", "广告", "推广", "扫码.*关注"]}', 30, 'all', '删除广告和推广信息');

-- ================================================
-- 数据库初始化完成
-- ================================================
SELECT 'Database initialized successfully!' AS 'Init Status';
SHOW TABLES;
