import os
os.chdir('d:/work/agentV1/rag-qa-system')

from app.core.vectorstore import vector_store

# 获取 collection 统计
collection = vector_store.collection
print(f"Collection: {collection.name}")
print(f"Total vectors: {collection.count()}")
print()

# 获取所有向量，查看 metadata
results = collection.get(include=["metadatas"])
metadatas = results.get("metadatas", [])

# 按文档分组统计
doc_stats = {}
for m in metadatas:
    doc_id = m.get("document_id")
    if doc_id:
        if doc_id not in doc_stats:
            doc_stats[doc_id] = {"count": 0, "filename": m.get("filename")}
        doc_stats[doc_id]["count"] += 1

print("=== Documents in vector store ===")
for doc_id, stats in sorted(doc_stats.items()):
    print(f"Document ID={doc_id}: {stats['filename']} ({stats['count']} chunks)")
