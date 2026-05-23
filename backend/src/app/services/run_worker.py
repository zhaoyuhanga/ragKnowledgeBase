# -*- coding: utf-8 -*-
"""
Worker启动脚本

本脚本用于启动消息队列的Worker进程：
1. ParseWorker - 解析任务消费者
2. CleanWorker - 清洗任务消费者
3. ChunkWorker - 切分任务消费者
4. EmbeddingWorker - 向量化任务消费者
5. IndexWorker - 索引任务消费者

使用示例：
    # 启动解析Worker (在 backend 目录运行)
    python -m src.app.services.run_worker parse

    # 启动清洗Worker
    python -m src.app.services.run_worker clean

    # 启动切分Worker
    python -m src.app.services.run_worker chunk

    # 启动向量化Worker
    python -m src.app.services.run_worker embedding

    # 启动索引Worker
    python -m src.app.services.run_worker index

    # 启动所有Worker（多进程）
    python -m src.app.services.run_worker all
"""

import argparse
import multiprocessing
import os
import sys
from typing import List

# 关键：在导入任何模块之前设置 sys.path
# 向上找到 backend/src 目录并添加到 sys.path
# 这样 'app' 和 'core' 模块可以被正确导入
_current = os.path.dirname(os.path.abspath(__file__))  # .../backend/src/app/services
_backend_src = os.path.dirname(_current)  # .../backend/src

# 只添加 backend/src 目录以支持 'app' 导入方式
if _backend_src not in sys.path:
    sys.path.insert(0, _backend_src)

from app.common.logging import logger, setup_logging
from app.services.workers import (
    ParseWorker,
    CleanWorker,
    ChunkWorker,
    EmbeddingWorker,
    IndexWorker,
    get_worker,
)


def run_single_worker(worker_type: str) -> None:
    """
    运行单个Worker

    Args:
        worker_type: Worker类型
    """
    setup_logging()

    logger.info(f"准备启动Worker: {worker_type}")

    worker_map = {
        "parse": ParseWorker,
        "clean": CleanWorker,
        "chunk": ChunkWorker,
        "embedding": EmbeddingWorker,
        "index": IndexWorker
    }

    worker_class = worker_map.get(worker_type)
    if not worker_class:
        logger.error(f"不支持的Worker类型: {worker_type}")
        sys.exit(1)

    worker = worker_class()
    logger.info(f"{worker_type} Worker启动中...")

    try:
        worker.start_consuming()
    except KeyboardInterrupt:
        logger.info(f"{worker_type} Worker接收到停止信号")
        worker.stop_consuming()
    except Exception as e:
        logger.error(f"{worker_type} Worker异常退出: {str(e)}")
        sys.exit(1)


def run_all_workers() -> None:
    """运行所有Worker（多进程模式）"""
    setup_logging()

    logger.info("准备启动所有Worker（多进程模式）...")

    worker_types = ["parse", "clean", "chunk", "embedding", "index"]
    processes: List[multiprocessing.Process] = []

    try:
        for worker_type in worker_types:
            process = multiprocessing.Process(
                target=run_single_worker,
                args=(worker_type,),
                name=f"{worker_type}_worker"
            )
            process.start()
            processes.append(process)
            logger.info(f"{worker_type} Worker进程已启动 (PID: {process.pid})")

        # 等待所有进程
        for process in processes:
            process.join()

    except KeyboardInterrupt:
        logger.info("接收到停止信号，正在停止所有Worker...")
        for process in processes:
            if process.is_alive():
                process.terminate()
                process.join(timeout=5)
    except Exception as e:
        logger.error(f"Worker管理异常: {str(e)}")
        for process in processes:
            if process.is_alive():
                process.terminate()
                process.join(timeout=5)
        sys.exit(1)


def main() -> None:
    """主函数"""
    parser = argparse.ArgumentParser(
        description="RAG知识库系统 - Worker启动脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  python -m app.services.run_worker parse     # 启动解析Worker
  python -m app.services.run_worker clean     # 启动清洗Worker
  python -m app.services.run_worker chunk    # 启动切分Worker
  python -m app.services.run_worker embedding # 启动向量化Worker
  python -m app.services.run_worker index     # 启动索引Worker
  python -m app.services.run_worker all       # 启动所有Worker
        """
    )

    parser.add_argument(
        "worker_type",
        nargs="?",
        default="all",
        choices=["parse", "clean", "chunk", "embedding", "index", "all"],
        help="Worker类型 (默认: all)"
    )

    args = parser.parse_args()

    if args.worker_type == "all":
        run_all_workers()
    else:
        run_single_worker(args.worker_type)


if __name__ == "__main__":
    main()


def run_worker(worker_type: str) -> None:
    """
    运行指定类型的Worker（供其他模块调用）

    Args:
        worker_type: Worker类型
    """
    if worker_type == "all":
        run_all_workers()
    else:
        run_single_worker(worker_type)
