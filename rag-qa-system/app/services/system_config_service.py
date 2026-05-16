"""
RAG 问答系统 - 系统配置服务
提供配置的增删改查功能
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.models.system_config import SystemConfig, DEFAULT_CONFIGS, CONFIG_GROUP_NAMES


class SystemConfigService:
    """系统配置服务"""

    def __init__(self, db: Session):
        self.db = db

    def initialize_default_configs(self) -> int:
        """清理旧配置，重新初始化默认配置"""
        self.db.query(SystemConfig).delete()
        self.db.commit()

        count = 0
        for config_data in DEFAULT_CONFIGS:
            config = SystemConfig(**config_data)
            self.db.add(config)
            count += 1
        self.db.commit()
        return count

    def get_all_configs(self) -> List[SystemConfig]:
        """获取所有配置"""
        return self.db.query(SystemConfig).order_by(
            SystemConfig.group, SystemConfig.sort_order
        ).all()

    def get_configs_by_group(self, group: str) -> List[SystemConfig]:
        """按分组获取配置"""
        return self.db.query(SystemConfig).filter(
            SystemConfig.group == group
        ).order_by(SystemConfig.sort_order).all()

    def get_config_by_key(self, key: str) -> Optional[SystemConfig]:
        """根据键名获取配置"""
        return self.db.query(SystemConfig).filter(
            SystemConfig.key == key
        ).first()

    def update_config(self, key: str, value: Any, description: Optional[str] = None) -> Optional[SystemConfig]:
        """更新配置值"""
        config = self.get_config_by_key(key)
        if config:
            if not config.editable:
                return None
            config.set_typed_value(value)
            if description is not None:
                config.description = description
            self.db.commit()
            self.db.refresh(config)
        return config

    def get_grouped_configs(self) -> Dict[str, List[Dict[str, Any]]]:
        """获取分组后的配置"""
        configs = self.get_all_configs()
        grouped = {}
        for config in configs:
            if config.group not in grouped:
                grouped[config.group] = []
            grouped[config.group].append({
                "key": config.key,
                "value": config.value,
                "value_type": config.value_type,
                "name": config.name,
                "description": config.description,
                "editable": config.editable,
                "sensitive": config.sensitive,
                "sort_order": config.sort_order,
            })
        return grouped

    def get_groups_with_names(self) -> List[Dict[str, str]]:
        """获取所有分组及其名称"""
        return [
            {"key": key, "name": name}
            for key, name in CONFIG_GROUP_NAMES.items()
        ]
