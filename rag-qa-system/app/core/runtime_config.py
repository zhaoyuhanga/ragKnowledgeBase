"""
RAG 问答系统 - 运行时配置管理模块
支持从 system_configs 数据库表加载运行时可调配置
"""

from typing import Optional, Dict, Any, TYPE_CHECKING
from pydantic import BaseModel
from app.core.logger import get_logger

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

logger = get_logger(__name__)


class RuntimeConfigData(BaseModel):
    """运行时配置数据模型（仅包含 DB 可管理的配置）"""
    retrieval_top_k: int = 5
    similarity_threshold: float = 0.2
    enable_mmr: bool = False
    mmr_diversity: float = 0.5
    chunk_size: int = 500
    chunk_overlap: int = 50
    chunk_min_size: int = 50
    access_token_expire_minutes: int = 30


# DB key -> RuntimeConfigData attribute
DB_KEY_MAP: Dict[str, str] = {
    "RETRIEVAL_TOP_K": "retrieval_top_k",
    "SIMILARITY_THRESHOLD": "similarity_threshold",
    "ENABLE_MMR": "enable_mmr",
    "MMR_DIVERSITY": "mmr_diversity",
    "CHUNK_SIZE": "chunk_size",
    "CHUNK_OVERLAP": "chunk_overlap",
    "CHUNK_MIN_SIZE": "chunk_min_size",
    "ACCESS_TOKEN_EXPIRE_MINUTES": "access_token_expire_minutes",
}


class RuntimeConfigManager:
    """运行时配置管理器"""

    _instance: Optional["RuntimeConfigManager"] = None
    _data: RuntimeConfigData

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._data = RuntimeConfigData()
        return cls._instance

    def load_from_db(self, db: "Session") -> int:
        """从数据库加载配置，返回加载的配置项数量"""
        try:
            from app.models.system_config import SystemConfig
            configs = db.query(SystemConfig).all()
            loaded = 0

            for config in configs:
                if config.key in DB_KEY_MAP:
                    attr = DB_KEY_MAP[config.key]
                    typed_val = config.get_typed_value()
                    if getattr(self._data, attr) != typed_val:
                        setattr(self._data, attr, typed_val)
                        loaded += 1
                        logger.debug(f"Loaded config from DB: {config.key} = {typed_val}")

            if loaded > 0:
                logger.info(f"Runtime config loaded {loaded} items from DB")
            return loaded
        except Exception as e:
            logger.warning(f"Failed to load runtime config from DB: {e}")
            return 0

    def get_all(self) -> Dict[str, Any]:
        return self._data.model_dump()

    def update(self, updates: Dict[str, Any]) -> Dict[str, Any]:
        updated = {}
        for key, value in updates.items():
            if hasattr(self._data, key):
                setattr(self._data, key, value)
                updated[key] = value
                logger.info(f"Runtime config updated: {key} = {value}")
        return updated

    def reset(self):
        self._data = RuntimeConfigData()
        logger.info("Runtime config reset to defaults")

    def update_from_db_key(self, key: str, value: Any) -> bool:
        """根据 DB 配置键更新运行时配置"""
        if key not in DB_KEY_MAP:
            return False
        attr = DB_KEY_MAP[key]
        if hasattr(self._data, attr):
            setattr(self._data, attr, value)
            return True
        return False

    # ---- properties ----

    @property
    def retrieval_top_k(self) -> int:
        return self._data.retrieval_top_k

    @retrieval_top_k.setter
    def retrieval_top_k(self, v: int):
        self._data.retrieval_top_k = max(1, min(50, v))

    @property
    def similarity_threshold(self) -> float:
        return self._data.similarity_threshold

    @similarity_threshold.setter
    def similarity_threshold(self, v: float):
        self._data.similarity_threshold = max(0.0, min(1.0, v))

    @property
    def enable_mmr(self) -> bool:
        return self._data.enable_mmr

    @enable_mmr.setter
    def enable_mmr(self, v: bool):
        self._data.enable_mmr = bool(v)

    @property
    def mmr_diversity(self) -> float:
        return self._data.mmr_diversity

    @mmr_diversity.setter
    def mmr_diversity(self, v: float):
        self._data.mmr_diversity = max(0.0, min(1.0, v))

    @property
    def chunk_size(self) -> int:
        return self._data.chunk_size

    @chunk_size.setter
    def chunk_size(self, v: int):
        self._data.chunk_size = max(50, min(5000, v))

    @property
    def chunk_overlap(self) -> int:
        return self._data.chunk_overlap

    @chunk_overlap.setter
    def chunk_overlap(self, v: int):
        self._data.chunk_overlap = max(0, min(500, v))

    @property
    def chunk_min_size(self) -> int:
        return self._data.chunk_min_size

    @chunk_min_size.setter
    def chunk_min_size(self, v: int):
        self._data.chunk_min_size = max(1, min(1000, v))

    @property
    def access_token_expire_minutes(self) -> int:
        return self._data.access_token_expire_minutes

    @access_token_expire_minutes.setter
    def access_token_expire_minutes(self, v: int):
        self._data.access_token_expire_minutes = max(1, min(10080, v))


runtime_config = RuntimeConfigManager()


def get_runtime_config() -> RuntimeConfigManager:
    return runtime_config
