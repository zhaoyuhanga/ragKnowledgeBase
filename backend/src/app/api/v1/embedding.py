# -*- coding: utf-8 -*-
"""
向量化接口路由

本模块提供向量化相关的API接口：
- 文本向量化
- Chunk向量化
- 向量检索
- 向量管理
"""

from typing import Optional

from fastapi import APIRouter, Query
from pydantic import BaseModel

from app.common.logging import logger
from app.common.response import success_response, error_response
from app.services.embedding_service import (
    get_embedding_service,
    get_chunk_embedding_service,
)
from app.repositories.milvus_repository import (
    get_milvus_repository,
    get_vector_search_service,
)
from core.cache import get_embedding_cache

router = APIRouter(prefix="/embedding", tags=["向量化服务"])


# ================================================
# 文本向量化接口
# ================================================

@router.post("/encode", response_model=BaseModel)
async def encode_texts(texts: list[str]):
    """
    批量文本向量化

    Args:
        texts: 待向量化的文本列表

    Returns:
        向量结果
    """
    try:
        service = get_embedding_service()
        vectors, cached_count = service.encode(texts, normalize=True)

        return success_response(data={
            "count": len(texts),
            "cached_count": cached_count,
            "dimension": service.get_embedding_dimension(),
            "model_name": service.get_model_name()
        }, message=f"成功向量化 {len(texts)} 个文本")
    except Exception as e:
        logger.error(f"文本向量化失败: {str(e)}")
        return error_response(message=f"文本向量化失败: {str(e)}")


@router.post("/encode/single", response_model=BaseModel)
async def encode_single_text(text: str):
    """
    单个文本向量化

    Args:
        text: 待向量化的文本

    Returns:
        向量结果
    """
    try:
        service = get_embedding_service()
        vector, cached = service.encode_single(text, normalize=True)

        return success_response(data={
            "text": text[:100] + "..." if len(text) > 100 else text,
            "dimension": len(vector),
            "cached": cached,
            "model_name": service.get_model_name()
        }, message="文本向量化成功")
    except Exception as e:
        logger.error(f"文本向量化失败: {str(e)}")
        return error_response(message=f"文本向量化失败: {str(e)}")


# ================================================
# Chunk向量化接口
# ================================================

@router.post("/chunks/{document_id}", response_model=BaseModel)
async def embed_document_chunks(
    document_id: int,
    version_id: Optional[int] = None,
    use_cache: bool = True
):
    """
    向量化文档Chunks

    将文档的所有Chunks向量化并存储到向量数据库。

    Args:
        document_id: 文档ID
        version_id: 版本ID
        use_cache: 是否使用缓存

    Returns:
        向量化结果
    """
    try:
        from core.database import SessionLocal
        from app.models.document import Document, DocumentVersion

        db = SessionLocal()
        try:
            # 获取版本信息
            if version_id:
                version = db.query(DocumentVersion).filter(
                    DocumentVersion.id == version_id,
                    DocumentVersion.document_id == document_id
                ).first()
            else:
                version = db.query(DocumentVersion).filter(
                    DocumentVersion.document_id == document_id
                ).order_by(DocumentVersion.version.desc()).first()

            if not version:
                return error_response(message="文档版本不存在", code="BIZ_2001")

            # 执行向量化
            service = get_chunk_embedding_service()
            result = service.embed_document_chunks(
                document_id=document_id,
                version_id=version.id,
                use_cache=use_cache
            )

            # 更新文档状态
            doc = db.query(Document).filter(Document.id == document_id).first()
            if doc:
                doc.status = 6  # 已向量化
                db.commit()

            return success_response(data=result, message="文档向量化成功")

        finally:
            db.close()

    except Exception as e:
        logger.error(f"文档向量化失败: {str(e)}")
        return error_response(message=f"文档向量化失败: {str(e)}")


# ================================================
# 向量检索接口
# ================================================

@router.post("/search", response_model=BaseModel)
async def search_vectors(
    query: str,
    top_k: int = Query(default=10, ge=1, le=100, description="返回结果数量"),
    document_ids: Optional[str] = Query(default=None, description="文档ID列表，逗号分隔")
):
    """
    向量检索

    根据查询文本检索相似的Chunks。

    Args:
        query: 查询文本
        top_k: 返回结果数量
        document_ids: 文档ID筛选

    Returns:
        检索结果
    """
    try:
        # 解析文档ID列表
        doc_ids = None
        if document_ids:
            doc_ids = [int(x.strip()) for x in document_ids.split(",") if x.strip()]

        # 执行检索
        service = get_vector_search_service()
        results = service.search_by_text(
            query=query,
            top_k=top_k,
            document_ids=doc_ids
        )

        return success_response(data={
            "query": query,
            "top_k": top_k,
            "total_results": len(results),
            "results": results
        }, message=f"检索成功，返回 {len(results)} 条结果")

    except Exception as e:
        logger.error(f"向量检索失败: {str(e)}")
        return error_response(message=f"向量检索失败: {str(e)}")


# ================================================
# 向量管理接口
# ================================================

@router.delete("/chunks/{document_id}", response_model=BaseModel)
async def delete_document_vectors(
    document_id: int,
    version_id: Optional[int] = None
):
    """
    删除文档向量

    Args:
        document_id: 文档ID
        version_id: 版本ID

    Returns:
        删除结果
    """
    try:
        service = get_chunk_embedding_service()
        result = service.delete_document_vectors(
            document_id=document_id,
            version_id=version_id
        )

        return success_response(data=result, message=f"成功删除 {result['deleted_count']} 个向量")

    except Exception as e:
        logger.error(f"删除向量失败: {str(e)}")
        return error_response(message=f"删除向量失败: {str(e)}")


@router.get("/statistics", response_model=BaseModel)
async def get_vector_statistics():
    """
    获取向量统计信息

    Returns:
        统计信息
    """
    try:
        repo = get_milvus_repository()
        cache = get_embedding_cache()

        # 获取集合统计
        try:
            stats = repo.get_collection_stats("document_chunks")
        except Exception:
            stats = {
                "collection_name": "document_chunks",
                "total_entities": 0,
                "dimension": 1024
            }

        return success_response(data=stats, message="获取统计信息成功")

    except Exception as e:
        logger.error(f"获取统计信息失败: {str(e)}")
        return error_response(message=f"获取统计信息失败: {str(e)}")


@router.post("/initialize", response_model=BaseModel)
async def initialize_collection():
    """
    初始化向量集合

    Returns:
        初始化结果
    """
    try:
        repo = get_milvus_repository()
        repo.initialize_collection()

        return success_response(message="向量集合初始化成功")

    except Exception as e:
        logger.error(f"初始化向量集合失败: {str(e)}")
        return error_response(message=f"初始化向量集合失败: {str(e)}")


@router.get("/status", response_model=BaseModel)
async def get_vector_status():
    """
    获取向量库状态

    返回向量库的连接状态和统计信息，帮助诊断向量库没有数据的问题。

    Returns:
        向量库状态信息
    """
    try:
        from core.milvus import get_milvus_client
        from core.database import SessionLocal
        from app.models.chunk import DocumentChunk

        status_info = {
            "milvus_connected": False,
            "collection_exists": False,
            "collection_stats": None,
            "database_stats": None,
            "pending_chunks": None,
            "errors": []
        }

        # 检查Milvus连接
        try:
            client = get_milvus_client()
            status_info["milvus_connected"] = client.is_connected()
            if not status_info["milvus_connected"]:
                client.connect()
                status_info["milvus_connected"] = client.is_connected()
        except Exception as e:
            status_info["errors"].append(f"Milvus连接失败: {str(e)}")
            return success_response(data=status_info, message="向量库状态获取失败")

        # 检查集合是否存在
        try:
            repo = get_milvus_repository()
            status_info["collection_exists"] = repo.exists("document_chunks")
        except Exception as e:
            status_info["errors"].append(f"检查集合失败: {str(e)}")

        # 获取集合统计
        try:
            status_info["collection_stats"] = repo.get_collection_stats("document_chunks")
        except Exception as e:
            status_info["errors"].append(f"获取集合统计失败: {str(e)}")

        # 获取数据库统计
        try:
            db = SessionLocal()
            try:
                total_chunks = db.query(DocumentChunk).filter(
                    DocumentChunk.status != 9
                ).count()
                embedded_chunks = db.query(DocumentChunk).filter(
                    DocumentChunk.status == 1,
                    DocumentChunk.status != 9
                ).count()
                pending_chunks = db.query(DocumentChunk).filter(
                    DocumentChunk.status == 0,
                    DocumentChunk.status != 9
                ).count()

                status_info["database_stats"] = {
                    "total_chunks": total_chunks,
                    "embedded_chunks": embedded_chunks,
                    "pending_chunks": pending_chunks
                }
                status_info["pending_chunks"] = pending_chunks
            finally:
                db.close()
        except Exception as e:
            status_info["errors"].append(f"获取数据库统计失败: {str(e)}")

        # 判断是否有问题
        if status_info["collection_stats"] and status_info["database_stats"]:
            db_embedded = status_info["database_stats"]["embedded_chunks"]
            milvus_count = status_info["collection_stats"].get("total_entities", 0)

            if db_embedded > 0 and milvus_count == 0:
                status_info["diagnosis"] = "WARNING: 数据库显示有已向量化的chunks，但Milvus中没有数据。可能需要重新初始化Milvus集合。"
            elif db_embedded == 0 and status_info["database_stats"]["total_chunks"] > 0:
                status_info["diagnosis"] = "WARNING: 有未向量化的chunks。请调用 POST /embedding/chunks/{document_id} 进行向量化。"
            elif milvus_count > 0:
                status_info["diagnosis"] = "OK: 向量库正常工作。"
            else:
                status_info["diagnosis"] = "INFO: 向量库为空。请先解析文档。"

        return success_response(data=status_info, message="获取向量库状态成功")

    except Exception as e:
        logger.error(f"获取向量库状态失败: {str(e)}")
        return error_response(message=f"获取向量库状态失败: {str(e)}")


@router.post("/reindex/{document_id}", response_model=BaseModel)
async def reindex_document_vectors(
    document_id: int,
    version_id: Optional[int] = None
):
    """
    重新索引文档向量

    用于修复向量库数据丢失的问题。

    Args:
        document_id: 文档ID
        version_id: 版本ID

    Returns:
        重新索引结果
    """
    try:
        from core.database import SessionLocal
        from app.models.chunk import DocumentChunk

        db = SessionLocal()
        try:
            # 查询待向量化的chunks
            query = db.query(DocumentChunk).filter(
                DocumentChunk.document_id == document_id,
                DocumentChunk.status != 9
            )

            if version_id:
                query = query.filter(DocumentChunk.version_id == version_id)

            chunks = query.all()

            if not chunks:
                return success_response(data={"reindexed": 0}, message="没有待向量化的chunks")

            # 将状态设为待向量化
            chunk_ids = [c.id for c in chunks]
            for chunk in chunks:
                chunk.status = 0
                chunk.vector_id = None
            db.commit()

            # 调用向量化服务
            service = get_chunk_embedding_service()
            result = service.embed_document_chunks(
                document_id=document_id,
                version_id=version_id,
                chunk_ids=chunk_ids
            )

            return success_response(
                data={
                    "document_id": document_id,
                    "total_chunks": len(chunks),
                    "reindexed": result.processed_chunks,
                    "processing_time_ms": result.processing_time_ms
                },
                message=f"成功重新索引 {result.processed_chunks} 个chunks"
            )

        finally:
            db.close()

    except Exception as e:
        logger.error(f"重新索引失败: {str(e)}")
        return error_response(message=f"重新索引失败: {str(e)}")
