-- ============================================================
-- RAG 问答系统 - 数据库初始化脚本
-- 创建数据库和表结构
-- ============================================================

-- 创建数据库（如果不存在）
CREATE DATABASE IF NOT EXISTS rag_qa 
    DEFAULT CHARACTER SET utf8mb4 
    DEFAULT COLLATE utf8mb4_unicode_ci;

-- 使用数据库
USE rag_qa;

-- ============================================================
-- 文档表
-- 存储上传的文档元信息
-- ============================================================
CREATE TABLE IF NOT EXISTS documents (
    -- 主键，自增ID
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '文档ID',
    
    -- 文件名
    filename VARCHAR(255) NOT NULL COMMENT '文件名',
    
    -- 文件存储路径
    file_path VARCHAR(512) NOT NULL COMMENT '文件存储路径',
    
    -- 文件类型 (pdf/md/txt/docx)
    file_type VARCHAR(50) NOT NULL COMMENT '文件类型',
    
    -- 文件大小（字节）
    file_size BIGINT NOT NULL COMMENT '文件大小（字节）',
    
    -- 文件内容哈希（用于去重）
    content_hash VARCHAR(64) NULL INDEX COMMENT '文件内容哈希',
    
    -- 处理状态 (0=处理中, 1=已完成, 2=失败)
    status TINYINT NOT NULL DEFAULT 0 COMMENT '处理状态: 0=处理中, 1=已完成, 2=失败',
    
    -- 切分块数量
    chunk_count INT NOT NULL DEFAULT 0 COMMENT '切分块数量',
    
    -- 错误信息
    error_message TEXT NULL COMMENT '错误信息',
    
    -- 创建时间
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    
    -- 更新时间
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    -- 索引
    INDEX idx_document_status (status),
    INDEX idx_document_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='文档表';

-- ============================================================
-- 文档块表
-- 存储文档切分后的文本块
-- ============================================================
CREATE TABLE IF NOT EXISTS document_chunks (
    -- 主键，自增ID
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '文档块ID',
    
    -- 外键，关联文档表
    document_id BIGINT NOT NULL COMMENT '文档ID',
    
    -- 块序号
    chunk_index INT NOT NULL COMMENT '块序号',
    
    -- 文本内容
    content TEXT NOT NULL COMMENT '文本内容',
    
    -- 字符数量
    char_count INT NOT NULL COMMENT '字符数量',
    
    -- ChromaDB 中的向量ID
    vector_id VARCHAR(64) NULL INDEX COMMENT '向量ID',
    
    -- 创建时间
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    
    -- 外键约束
    CONSTRAINT fk_chunk_document FOREIGN KEY (document_id) 
        REFERENCES documents(id) 
        ON DELETE CASCADE,
    
    -- 索引
    INDEX idx_chunk_document_id (document_id),
    INDEX idx_chunk_document_index (document_id, chunk_index)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='文档块表';

-- ============================================================
-- 问答日志表
-- 存储用户问答记录
-- ============================================================
CREATE TABLE IF NOT EXISTS qa_logs (
    -- 主键，自增ID
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '问答日志ID',
    
    -- 用户问题
    question TEXT NOT NULL COMMENT '用户问题',
    
    -- 系统回答
    answer TEXT NULL COMMENT '系统回答',
    
    -- 引用的文档块ID列表 (JSON格式)
    referenced_chunks JSON NULL COMMENT '引用的文档块ID列表',
    
    -- 响应耗时（毫秒）
    response_time_ms INT NULL COMMENT '响应耗时（毫秒）',
    
    -- 是否命中缓存
    cache_hit BOOLEAN NOT NULL DEFAULT FALSE COMMENT '是否命中缓存',
    
    -- 会话ID（用于多轮对话）
    session_id VARCHAR(64) NULL INDEX COMMENT '会话ID',
    
    -- 创建时间
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP INDEX COMMENT '创建时间',
    
    -- 索引
    INDEX idx_qa_session_time (session_id, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='问答日志表';

-- ============================================================
-- 系统日志表
-- 存储系统操作日志
-- ============================================================
CREATE TABLE IF NOT EXISTS system_logs (
    -- 主键，自增ID
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '系统日志ID',
    
    -- 模块名称
    module VARCHAR(50) NOT NULL INDEX COMMENT '模块名称',
    
    -- 操作名称
    operation VARCHAR(100) NOT NULL COMMENT '操作名称',
    
    -- 操作状态
    status VARCHAR(20) NOT NULL COMMENT '操作状态',
    
    -- 操作详情 (JSON格式)
    details JSON NULL COMMENT '操作详情',
    
    -- 用户ID
    user_id VARCHAR(64) NULL COMMENT '用户ID',
    
    -- 耗时（毫秒）
    duration_ms INT NULL COMMENT '耗时（毫秒）',
    
    -- 错误信息
    error_message TEXT NULL COMMENT '错误信息',
    
    -- 创建时间
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP INDEX COMMENT '创建时间',
    
    -- 索引
    INDEX idx_system_log_module_time (module, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='系统日志表';

-- ============================================================
-- 初始化完成提示
-- ============================================================
SELECT '数据库初始化完成!' AS status;
