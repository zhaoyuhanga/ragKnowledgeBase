import os
os.chdir('d:/work/agentV1/rag-qa-system')

from app.core.vectorstore import vector_store
from app.services.embedding_service import embedding_service

# 初始化 embedding 服务
embedding = embedding_service

# 测试检索
query = "Aspect 切面"
query_embedding = embedding.encode_single(query)

results = vector_store.search_vectors(query_embedding, n_results=5)

print(f"Query: {query}")
print(f"Found {len(results.get('documents', [[]])[0])} results")
print()

ids = results.get("ids", [[]])[0]
distances = results.get("distances", [[]])[0]
documents = results.get("documents", [[]])[0]
metadatas = results.get("metadatas", [[]])[0]

for i, (vid, dist, doc, meta) in enumerate(zip(ids, distances, documents, metadatas)):
    similarity = 1 - dist / 2
    print(f"Result {i+1}:")
    print(f"  Similarity: {similarity:.4f}")
    print(f"  Document: {meta.get('filename')}")
    print(f"  Content preview: {doc[:200]}...")
    print()
