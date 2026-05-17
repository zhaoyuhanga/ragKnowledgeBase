-- 修改 qa_logs 表：删除旧的 is_ai_extend 字段，添加 source_type 字段

-- 1. 先删除旧字段（如果存在）
ALTER TABLE qa_logs DROP COLUMN IF EXISTS is_ai_extend;

-- 2. 添加新的 source_type 字段
ALTER TABLE qa_logs ADD COLUMN source_type VARCHAR(32) NOT NULL DEFAULT 'local' COMMENT '来源类型: local/ai_generated' AFTER cache_hit;

-- 3. 更新现有数据：根据 referenced_chunks 判断来源
-- 包含 ai_generated 相关文档的标记为 ai_generated
-- 注意：这个判断可能不完全准确，建议根据实际情况调整
UPDATE qa_logs 
SET source_type = 'ai_generated' 
WHERE referenced_chunks IS NULL 
   OR referenced_chunks = '[]' 
   OR referenced_chunks = '' 
   OR JSON_LENGTH(referenced_chunks) = 0;

-- 4. 其他保持为 local
UPDATE qa_logs SET source_type = 'local' WHERE source_type = 'local';
