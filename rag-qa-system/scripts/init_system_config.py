"""
系统配置表初始化脚本
将 .env 中的配置迁移到 MySQL 数据库
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.core.database import Base, get_db_url
from app.models.system_config import SystemConfig, DEFAULT_CONFIGS
from app.core.logger import get_logger

logger = get_logger(__name__)


def create_system_configs_table():
    """创建系统配置表"""
    # 创建数据库引擎
    engine = create_engine(get_db_url())

    # 创建表
    Base.metadata.create_all(engine, tables=[SystemConfig.__table__])

    # 创建会话
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # 检查是否已有配置
        existing_count = session.query(SystemConfig).count()

        if existing_count > 0:
            logger.info(f"数据库中已有 {existing_count} 项配置，跳过初始化")
            return existing_count

        # 初始化默认配置
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
    print("系统配置表初始化脚本")
    print("=" * 50)

    try:
        count = create_system_configs_table()
        print(f"\n初始化完成！共 {count} 项配置")
    except Exception as e:
        print(f"\n初始化失败: {e}")
        sys.exit(1)
