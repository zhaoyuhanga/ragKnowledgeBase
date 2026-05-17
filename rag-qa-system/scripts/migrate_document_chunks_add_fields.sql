-- ================================================================
-- SemanticChunker 数据库迁移脚本
-- 为 document_chunks 表添加新字段
-- ================================================================

-- 警告：执行前请备份数据库！
-- 推荐先在测试环境执行

-- ================================================================
-- 迁移脚本
-- ================================================================

-- 1. 添加 token_count 字段
ALTER TABLE document_chunks
ADD COLUMN IF NOT EXISTS token_count INT NULL COMMENT 'token数量';

-- 2. 添加 content_hash 字段
ALTER TABLE document_chunks
ADD COLUMN IF NOT EXISTS content_hash VARCHAR(64) NULL COMMENT '内容哈希';

-- 3. 添加 title_path 字段
ALTER TABLE document_chunks
ADD COLUMN IF NOT EXISTS title_path VARCHAR(512) NULL COMMENT '标题路径';

-- 4. 添加 section_level 字段
ALTER TABLE document_chunks
ADD COLUMN IF NOT EXISTS section_level INT NULL COMMENT '章节层级';

-- 5. 添加 block_type 字段
ALTER TABLE document_chunks
ADD COLUMN IF NOT EXISTS block_type VARCHAR(20) NULL COMMENT '块类型：title/paragraph/list/table/code/mixed';

-- 6. 添加 parent_section_id 字段
ALTER TABLE document_chunks
ADD COLUMN IF NOT EXISTS parent_section_id VARCHAR(64) NULL COMMENT '父章节ID';

-- 7. 添加 chunk_version 字段
ALTER TABLE document_chunks
ADD COLUMN IF NOT EXISTS chunk_version VARCHAR(20) NULL COMMENT 'chunk版本号';

-- ================================================================
-- 回滚脚本（如需回滚）
-- ================================================================
-- ALTER TABLE document_chunks DROP COLUMN IF EXISTS token_count;
-- ALTER TABLE document_chunks DROP COLUMN IF EXISTS content_hash;
-- ALTER TABLE document_chunks DROP COLUMN IF EXISTS title_path;
-- ALTER TABLE document_chunks DROP COLUMN IF EXISTS section_level;
-- ALTER TABLE document_chunks DROP COLUMN IF EXISTS block_type;
-- ALTER TABLE document_chunks DROP COLUMN IF EXISTS parent_section_id;
-- ALTER TABLE document_chunks DROP COLUMN IF EXISTS chunk_version;
