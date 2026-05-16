"""
系统配置表初始化脚本
只保留 8 项运行时可调配置，清理旧数据后重新初始化
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base, get_db_url
from app.models.system_config import SystemConfig, DEFAULT_CONFIGS
from app.core.logger import get_logger

logger = get_logger(__name__)


def create_system_configs_table():
    """清理旧配置，只保留 8 项运行时可调配置"""
    engine = create_engine(get_db_url())

    Base.metadata.create_all(engine, tables=[SystemConfig.__table__])

    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # 清理所有旧配置
        deleted = session.query(SystemConfig).delete()
        session.commit()
        logger.info(f"已清理 {deleted} 项旧配置")

        # 插入新的 8 项默认配置
        count = 0
        for config_data in DEFAULT_CONFIGS:
            config = SystemConfig(**config_data)
            session.add(config)
            count += 1

        session.commit()
        logger.info(f"成功初始化 {count} 项默认配置")

        return count

    except Exception as e:
        session.rollback()
        logger.error(f"初始化配置失败: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    print("=" * 50)
    print("系统配置表初始化脚本（仅保留 8 项运行时可调配置）")
    print("=" * 50)

    try:
        count = create_system_configs_table()
        print(f"\n初始化完成！共 {count} 项配置")
    except Exception as e:
        print(f"\n初始化失败: {e}")
        sys.exit(1)
