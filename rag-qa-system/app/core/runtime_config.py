"""
RAG 问答系统 - 运行时配置管理模块
支持动态修改配置并实时生效
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel
from app.core.logger import get_logger

logger = get_logger(__name__)


class RuntimeConfig(BaseModel):
    """运行时配置模型"""
    retrieval_top_k: int = 5
    similarity_threshold: float = 0.2
    deepseek_model: str = "deepseek-chat"
    chunk_size: int = 500
    chunk_overlap: int = 50


class RuntimeConfigManager:
    """
    运行时配置管理器
    允许动态修改配置，无需重启服务
    """
    
    _instance: Optional["RuntimeConfigManager"] = None
    _config: RuntimeConfig
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._config = RuntimeConfig()
        return cls._instance
    
    def __init__(self):
        self._config = RuntimeConfig()
    
    @property
    def retrieval_top_k(self) -> int:
        """获取 Top K 检索数"""
        return self._config.retrieval_top_k
    
    @retrieval_top_k.setter
    def retrieval_top_k(self, value: int):
        """设置 Top K 检索数"""
        if value < 1:
            value = 1
        if value > 50:
            value = 50
        self._config.retrieval_top_k = value
        logger.info(f"Runtime config updated: retrieval_top_k = {value}")
    
    @property
    def similarity_threshold(self) -> float:
        """获取相似度阈值"""
        return self._config.similarity_threshold
    
    @similarity_threshold.setter
    def similarity_threshold(self, value: float):
        """设置相似度阈值"""
        if value < 0:
            value = 0
        if value > 1:
            value = 1
        self._config.similarity_threshold = value
        logger.info(f"Runtime config updated: similarity_threshold = {value}")
    
    @property
    def deepseek_model(self) -> str:
        """获取 DeepSeek 模型"""
        return self._config.deepseek_model
    
    @deepseek_model.setter
    def deepseek_model(self, value: str):
        """设置 DeepSeek 模型"""
        self._config.deepseek_model = value
        logger.info(f"Runtime config updated: deepseek_model = {value}")
    
    @property
    def chunk_size(self) -> int:
        """获取分块大小"""
        return self._config.chunk_size
    
    @chunk_size.setter
    def chunk_size(self, value: int):
        """设置分块大小"""
        if value < 50:
            value = 50
        if value > 5000:
            value = 5000
        self._config.chunk_size = value
        logger.info(f"Runtime config updated: chunk_size = {value}")
    
    @property
    def chunk_overlap(self) -> int:
        """获取分块重叠"""
        return self._config.chunk_overlap
    
    @chunk_overlap.setter
    def chunk_overlap(self, value: int):
        """设置分块重叠"""
        if value < 0:
            value = 0
        if value > 500:
            value = 500
        self._config.chunk_overlap = value
        logger.info(f"Runtime config updated: chunk_overlap = {value}")
    
    def get_all(self) -> Dict[str, Any]:
        """获取所有配置"""
        return self._config.model_dump()
    
    def update(self, config_dict: Dict[str, Any]) -> Dict[str, Any]:
        """批量更新配置"""
        updated = {}
        for key, value in config_dict.items():
            if hasattr(self, key):
                try:
                    setattr(self, key, value)
                    updated[key] = value
                except Exception as e:
                    logger.error(f"Failed to update config {key}: {e}")
        return updated
    
    def reset(self):
        """重置为默认值"""
        self._config = RuntimeConfig()
        logger.info("Runtime config reset to defaults")


# 全局配置管理器实例
runtime_config = RuntimeConfigManager()


def get_runtime_config() -> RuntimeConfigManager:
    """获取运行时配置管理器"""
    return runtime_config
