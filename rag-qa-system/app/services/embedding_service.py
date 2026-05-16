"""
RAG 问答系统 - Embedding 服务模块
文本向量化和 Embedding 模型管理
"""

from typing import List, Optional
import time

from sentence_transformers import SentenceTransformer

from app.config import settings
from app.core.logger import get_logger

logger = get_logger(__name__)


class EmbeddingService:
    """
    Embedding 服务
    负责文本向量化和模型管理
    """

    _instance: Optional["EmbeddingService"] = None
    _model: Optional[SentenceTransformer] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if EmbeddingService._model is not None:
            return
        self._initialize()

    def _initialize(self):
        """初始化 Embedding 模型"""
        logger.info(f"正在加载 Embedding 模型: {settings.embedding_model}")

        try:
            start_time = time.time()

            EmbeddingService._model = SentenceTransformer(
                model_name_or_path=settings.embedding_model,
                device=settings.embedding_device,
            )

            elapsed = time.time() - start_time
            logger.info(f"Embedding 模型加载完成，耗时: {elapsed:.2f}秒")

            # 验证模型维度
            actual_dim = EmbeddingService._model.get_sentence_embedding_dimension()
            if actual_dim != settings.embedding_dimension:
                logger.warning(
                    f"模型维度不匹配: 配置={settings.embedding_dimension}, "
                    f"实际={actual_dim}，请手动更新配置"
                )

        except Exception as e:
            logger.error(f"Embedding 模型加载失败: {str(e)}")
            raise

    @property
    def model(self) -> SentenceTransformer:
        """获取模型实例"""
        if EmbeddingService._model is None:
            self._initialize()
        return EmbeddingService._model

    def encode(self, texts: str | List[str], **kwargs) -> List[List[float]]:
        """将文本编码为向量"""
        try:
            if isinstance(texts, str):
                texts = [texts]

            cleaned_texts = []
            for text in texts:
                cleaned = text.replace('\x00', '')
                cleaned_texts.append(cleaned)

            embeddings = self.model.encode(
                cleaned_texts,
                batch_size=min(settings.embedding_batch_size, 8),
                show_progress_bar=False,
                convert_to_numpy=True,
                normalize_embeddings=True,
                **kwargs
            )

            return embeddings.tolist()

        except Exception as e:
            logger.error(f"文本向量化失败: {str(e)}")
            raise

    def encode_single(self, text: str) -> List[float]:
        """将单个文本编码为向量"""
        return self.encode(text)[0]

    def get_embedding_dimension(self) -> int:
        """获取向量维度"""
        return settings.embedding_dimension

    def check_health(self) -> bool:
        """检查模型健康状态"""
        try:
            test_text = "这是一个测试文本"
            result = self.encode(test_text)
            return len(result) > 0 and len(result[0]) == self.get_embedding_dimension()
        except Exception as e:
            logger.error(f"Embedding 模型健康检查失败: {str(e)}")
            return False


# 全局 Embedding 服务实例
embedding_service = EmbeddingService()


def get_embedding_service() -> EmbeddingService:
    """获取 Embedding 服务实例"""
    return embedding_service
