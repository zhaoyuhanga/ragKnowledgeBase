# -*- coding: utf-8 -*-
"""
服务模块

本模块包含所有业务逻辑服务。
"""

from app.services.document_service import DocumentService, ImportTaskService
from app.services.version_service import DocumentVersionService
from app.services.storage_service import FileStorageService, get_storage_service
from app.services.retrieval_service import RetrievalService, get_retrieval_service
from app.services.qa_service import QAService, get_qa_service
from app.services.parse_service import ParseService, get_parse_service
from app.services.clean_service import CleanService, get_clean_service
from app.services.chunk_service import ChunkService, get_chunk_service
from app.services.embedding_service import (
    EmbeddingService,
    ChunkEmbeddingService,
    get_embedding_service,
    get_chunk_embedding_service,
)
from app.services.ollama_client import (
    OllamaClient,
    OllamaClientSync,
    get_ollama_client,
)
from app.services.vision_client import (
    VisionClient,
    get_vision_client,
)
from app.services.keyword_service import KeywordIndexService, get_keyword_index_service
from app.services.query_rewrite_service import QueryRewriteService, get_rewrite_service
from app.services.fusion_service import FusionService, get_fusion_service
from app.services.rewrite_llm_client import RewriteLLMClient, get_rewrite_llm_client
from app.services.rerank_service import RerankService, get_rerank_service
from app.services.context_service import (
    ContextAssembler,
    PromptBuilder,
    get_context_assembler,
    get_prompt_builder,
)
from app.services.feedback_service import FeedbackService, get_feedback_service
from app.services.feedback_analyzer import FeedbackAnalyzer, get_feedback_analyzer
from app.services.optimization_engine import OptimizationRuleEngine, get_optimization_engine
from app.services.cleaning_optimizer import CleaningRuleOptimizer, get_cleaning_rule_optimizer
from app.services.rule_audit_service import RuleAuditService, get_rule_audit_service
from app.services.queue_consumer import (
    QueueConsumer,
    QueuePublisher,
    RabbitMQClientWrapper,
    get_queue_publisher,
    close_queue_publisher,
)
from app.services.workers import (
    ParseWorker,
    CleanWorker,
    ChunkWorker,
    EmbeddingWorker,
    IndexWorker,
    get_worker,
    run_worker,
)

__all__ = [
    "DocumentService",
    "ImportTaskService",
    "DocumentVersionService",
    "FileStorageService",
    "get_storage_service",
    "RetrievalService",
    "get_retrieval_service",
    "QAService",
    "get_qa_service",
    "ParseService",
    "get_parse_service",
    "CleanService",
    "get_clean_service",
    "ChunkService",
    "get_chunk_service",
    "EmbeddingService",
    "ChunkEmbeddingService",
    "get_embedding_service",
    "get_chunk_embedding_service",
    # Ollama 客户端
    "OllamaClient",
    "OllamaClientSync",
    "get_ollama_client",
    # 视觉模型客户端
    "VisionClient",
    "get_vision_client",
    "KeywordIndexService",
    "get_keyword_index_service",
    "QueryRewriteService",
    "get_rewrite_service",
    "FusionService",
    "get_fusion_service",
    "RewriteLLMClient",
    "get_rewrite_llm_client",
    "RerankService",
    "get_rerank_service",
    "ContextAssembler",
    "PromptBuilder",
    "get_context_assembler",
    "get_prompt_builder",
    "FeedbackService",
    "get_feedback_service",
    # 反馈分析与优化
    "FeedbackAnalyzer",
    "get_feedback_analyzer",
    "OptimizationRuleEngine",
    "get_optimization_engine",
    "CleaningRuleOptimizer",
    "get_cleaning_rule_optimizer",
    "RuleAuditService",
    "get_rule_audit_service",
    # 队列相关
    "QueueConsumer",
    "QueuePublisher",
    "RabbitMQClientWrapper",
    "get_queue_publisher",
    "close_queue_publisher",
    # Worker相关
    "ParseWorker",
    "CleanWorker",
    "ChunkWorker",
    "EmbeddingWorker",
    "IndexWorker",
    "get_worker",
    "run_worker",
]
