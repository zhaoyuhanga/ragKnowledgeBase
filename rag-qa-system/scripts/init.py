"""
RAG 问答系统 - 初始化命令脚本
提供命令行工具进行数据库初始化等操作
"""

import sys
import argparse
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))


def init_database():
    """初始化数据库"""
    print("正在初始化数据库...")
    from app.core.database import init_db, engine
    
    try:
        init_db()
        print("数据库初始化完成！")
    except Exception as e:
        print(f"数据库初始化失败: {e}")
        sys.exit(1)


def reset_database():
    """重置数据库"""
    print("警告：即将重置数据库，所有数据将被删除！")
    confirm = input("确认继续？(y/N): ")
    
    if confirm.lower() != 'y':
        print("已取消操作")
        return
    
    from app.core.database import Base
    
    try:
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        print("数据库重置完成！")
    except Exception as e:
        print(f"数据库重置失败: {e}")
        sys.exit(1)


def init_vectorstore():
    """初始化向量数据库"""
    print("正在初始化向量数据库...")
    from app.core.vectorstore import vector_store
    
    try:
        _ = vector_store.collection
        print("向量数据库初始化完成！")
    except Exception as e:
        print(f"向量数据库初始化失败: {e}")
        sys.exit(1)


def download_embedding_model():
    """下载 Embedding 模型"""
    print("正在检查/下载 Embedding 模型...")
    from app.services.embedding_service import embedding_service
    
    try:
        dim = embedding_service.get_embedding_dimension()
        print(f"Embedding 模型就绪，向量维度: {dim}")
    except Exception as e:
        print(f"Embedding 模型初始化失败: {e}")
        sys.exit(1)


def init_all():
    """初始化所有组件"""
    print("=" * 50)
    print("开始初始化 RAG 问答系统...")
    print("=" * 50)
    
    init_database()
    init_vectorstore()
    download_embedding_model()
    
    print("=" * 50)
    print("初始化完成！")
    print("=" * 50)


def main():
    parser = argparse.ArgumentParser(description="RAG 问答系统初始化工具")
    subparsers = parser.add_subparsers(dest="command", help="可用命令")
    
    # init 命令
    subparsers.add_parser("init", help="初始化所有组件")
    
    # db 命令
    db_parser = subparsers.add_parser("db", help="数据库操作")
    db_subparsers = db_parser.add_subparsers(dest="db_command")
    db_subparsers.add_parser("init", help="初始化数据库")
    db_subparsers.add_parser("reset", help="重置数据库")
    
    # vector 命令
    subparsers.add_parser("vector", help="初始化向量数据库")
    
    # model 命令
    subparsers.add_parser("model", help="下载/检查 Embedding 模型")
    
    args = parser.parse_args()
    
    if args.command == "init":
        init_all()
    elif args.command == "db":
        if args.db_command == "init":
            init_database()
        elif args.db_command == "reset":
            reset_database()
        else:
            db_parser.print_help()
    elif args.command == "vector":
        init_vectorstore()
    elif args.command == "model":
        download_embedding_model()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
