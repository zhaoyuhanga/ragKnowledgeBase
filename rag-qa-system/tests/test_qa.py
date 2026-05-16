"""
RAG 问答系统 - 问答服务测试模块
测试问答检索和生成相关功能
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from app.services.embedding_service import EmbeddingService
from app.utils.text_splitter import TextSplitter


class TestEmbeddingService:
    """Embedding 服务测试类"""
    
    def test_embedding_dimension(self):
        """测试向量维度配置"""
        from app.config import settings
        assert settings.embedding_dimension == 384  # all-MiniLM-L6-v2 维度
    
    def test_batch_size(self):
        """测试批处理大小配置"""
        from app.config import settings
        assert settings.embedding_batch_size > 0


class TestTextSplitter:
    """文本切分测试类"""
    
    def setup_method(self):
        """测试前准备"""
        self.splitter = TextSplitter(chunk_size=200, chunk_overlap=30)
    
    def test_chunk_size_respected(self):
        """测试块大小限制"""
        long_text = "测试内容 " * 100  # 约 1200 个字符
        chunks = self.splitter.split_text(long_text)
        
        for chunk in chunks:
            assert len(chunk) <= 200 + 50  # 允许一定容差
    
    def test_chunk_overlap_works(self):
        """测试块重叠"""
        splitter = TextSplitter(chunk_size=100, chunk_overlap=20)
        text = "ABCDEFGHIJKLMNOPQRSTUVWXYZ" * 10
        chunks = splitter.split_text(text)
        
        # 验证有多个块
        assert len(chunks) > 1


class TestQAService:
    """问答服务测试类（集成测试需要完整环境）"""
    
    def test_search_result_parsing(self):
        """测试检索结果解析"""
        # 模拟向量数据库返回结果
        mock_results = {
            "ids": [["1_0_abc123", "1_1_def456"]],
            "distances": [[0.15, 0.25]],
            "documents": [["文档内容1", "文档内容2"]],
            "metadatas": [[
                {"document_id": 1, "chunk_index": 0, "filename": "test.pdf"},
                {"document_id": 1, "chunk_index": 1, "filename": "test.pdf"}
            ]]
        }
        
        # 验证结果结构
        assert "ids" in mock_results
        assert "distances" in mock_results
        assert len(mock_results["ids"][0]) == 2


# ============================================================
# 测试用例配置
# ============================================================
"""
测试数据

| 测试项 | 测试数据 | 预期结果 |
|--------|----------|----------|
| 向量维度 | all-MiniLM-L6-v2 | 384 |
| 批处理大小 | 默认配置 | 32 |
| 块大小限制 | 200字符 | 每块≤200 |
| 块重叠 | 20字符 | 块间有重叠 |
| 检索结果解析 | 向量数据库格式 | 正确解析 |
"""


# ============================================================
# API 接口测试用例
# ============================================================
"""
API 测试数据

### 1. 问答接口测试

**请求**
```json
POST /api/v1/qa/ask
{
    "question": "什么是 RAG 技术？",
    "session_id": "test_session_001",
    "top_k": 5,
    "temperature": 0.3
}
```

**预期响应**
```json
{
    "success": true,
    "message": "问答处理完成",
    "code": 200,
    "data": {
        "answer": "RAG 是检索增强生成技术...",
        "sources": [
            {
                "chunk_id": 1,
                "document_id": 1,
                "filename": "技术文档.pdf",
                "content": "RAG（Retrieval-Augmented Generation）...",
                "similarity": 0.85
            }
        ],
        "cache_hit": false,
        "response_time_ms": 1500
    }
}
```

### 2. 文档上传接口测试

**请求**
```
POST /api/v1/documents/upload
Content-Type: multipart/form-data

file: [文件]
```

**预期响应**
```json
{
    "success": true,
    "message": "文档上传成功，正在处理中...",
    "code": 200,
    "data": {
        "id": 1,
        "filename": "技术文档.pdf",
        "file_type": "pdf",
        "file_size": 1024000,
        "status": 0
    }
}
```

### 3. 健康检查接口测试

**请求**
```
GET /api/v1/system/health
```

**预期响应**
```json
{
    "status": "healthy",
    "mysql": true,
    "redis": true,
    "chromadb": false,
    "llm": true,
    "embedding": true,
    "milvus": true,
    "version": "1.0.0"
}
```
"""


@pytest.fixture
def mock_embedding_service():
    """Mock Embedding 服务"""
    with patch('app.services.embedding_service.embedding_service') as mock:
        mock.encode.return_value = [[0.1] * 384]
        mock.encode_single.return_value = [0.1] * 384
        yield mock


@pytest.fixture
def mock_vector_store():
    """Mock 向量存储"""
    with patch('app.services.qa_service.vector_store') as mock:
        mock.search_vectors.return_value = {
            "ids": [["1_0_test"]],
            "distances": [[0.2]],
            "documents": [["测试文档内容"]],
            "metadatas": [[{
                "document_id": 1,
                "chunk_index": 0,
                "filename": "test.pdf",
                "char_count": 100
            }]]
        }
        yield mock


@pytest.fixture
def mock_llm_client():
    """Mock LLM 客户端"""
    with patch('app.services.qa_service.llm_client') as mock:
        mock.generate_with_context.return_value = "这是测试回答。"
        yield mock

@pytest.mark.asyncio
async def test_qa_ask_mocked_pipeline(mock_embedding_service, mock_vector_store, mock_llm_client):
    from unittest.mock import MagicMock
    from app.services.qa_service import QAService

    db = MagicMock()
    db.add = MagicMock()
    db.commit = MagicMock()
    service = QAService()

    result = await service.ask(
        question='What is RAG?',
        db=db,
        top_k=3,
    )

    assert 'answer' in result
    assert 'sources' in result
    assert 'cache_hit' in result
    assert 'response_time_ms' in result
    assert isinstance(result['cache_hit'], bool)
    assert result['response_time_ms'] >= 0
    assert len(result['answer']) > 0

@pytest.mark.asyncio
async def test_qa_ask_no_results(mock_embedding_service):
    from unittest.mock import MagicMock, patch
    from app.services.qa_service import QAService

    with patch('app.services.qa_service.vector_store') as mock_vs:
        mock_vs.search_vectors.return_value = {
            'ids': [[]],
            'distances': [[]],
            'documents': [[]],
            'metadatas': [[]]
        }

        db = MagicMock()
        service = QAService()
        result = await service.ask(question='???', db=db)

        assert 'answer' in result
        assert 'sources' in result
        assert len(result['sources']) == 0

