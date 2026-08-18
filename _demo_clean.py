# -*- coding: utf-8 -*-
"""
干净端到端演示：上传一份内容充实的 RAG 介绍文档 → 同步全链路 → 检索 → 问答（流式+非流式）
"""
import json
import time
import urllib.request

BASE = "http://127.0.0.1:8011/api/v1"

DOC_TEXT = """RAG知识库系统完整技术方案

第一章 系统概述
RAG（检索增强生成）知识库系统是一套完整的文档智能处理与问答平台，核心目标是为企业知识库提供"上传即用"的精准问答能力。
系统将文档解析、语义切分、向量化存储、混合检索与生成式问答整合为一条自动化流水线，并支持基于用户反馈的持续优化闭环。

第二章 文档解析
文档解析模块支持Word、PDF、图片、Excel、Markdown等多种格式。对于电子版PDF，系统直接提取文本层与坐标信息；对于扫描版PDF，系统自动识别并调用OCR引擎完成文字识别。
解析产物是统一的DocumentElement结构，包含元素类型、内容、页码、坐标、阅读顺序与置信度，供后续清洗与切分使用。

第三章 清洗与切分
清洗模块负责编码修复、乱码检测、页眉页脚与广告噪声过滤、敏感信息脱敏以及内容质量评分，清洗规则可通过管理界面动态配置并持久化到数据库。
切分模块根据文档结构自动选择策略：有标题层级的文档按标题切分，无结构的文档按语义边界切分，并配置目标600、最大900、重叠100的Token参数，保证语义完整。

第四章 向量化与存储
系统使用Qwen3-Embedding模型将文本转化为1024维向量，向量统一归一化后写入Milvus向量数据库，同时将文本原文与元数据存储到MySQL。
Redis用于缓存文档与查询的Embedding结果，避免重复计算。文档支持版本管理，同一文档多次上传会自动创建新版本。

第五章 混合检索
检索采用向量检索与关键词检索融合的方案：Milvus负责语义相似度召回，MySQL倒排索引负责关键词精确匹配，两者通过RRF算法融合排序。
系统还支持查询改写、多查询扩展与HyDE假设文档嵌入等增强策略，最终由重排序模型对候选结果精排，保证答案引用的准确率。

第六章 问答与反馈
问答服务基于检索增强生成，将检索到的证据与问题组装为Prompt，调用DeepSeek大模型生成带引用来源的答案，并支持SSE流式输出。
用户可以对答案进行满意/不满意反馈，系统会分析反馈数据、识别低质召回与解析问题，并据此优化清洗规则与检索权重，形成持续改进的闭环。

第七章 系统架构
系统后端基于Python FastAPI构建，使用RabbitMQ消息队列异步处理解析、清洗、切分、向量化等耗时任务，支持失败重试与死信队列。
前端采用React与Ant Design开发，提供文档管理、清洗规则配置、问答交互、检索测试、队列监控与系统设置等功能页面。
"""


def api(method, path, body=None, files=None, timeout=120):
    url = BASE + path
    if files:
        boundary = "----demo" + str(time.time())
        parts = []
        for fname, fpath, ftype in files:
            with open(fpath, "rb") as f:
                data = f.read()
            parts.append(
                f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"{fname}\"\r\n"
                f"Content-Type: {ftype}\r\n\r\n".encode() + data + b"\r\n"
            )
        parts.append(f"--{boundary}--\r\n".encode())
        req = urllib.request.Request(url, data=b"".join(parts), method=method)
        req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
    else:
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(url, data=data, method=method)
        if body is not None:
            req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def sse_stream(question, timeout=240):
    req = urllib.request.Request(
        BASE + "/qa/stream",
        data=json.dumps({"question": question, "use_rerank": True, "top_k": 8}).encode(),
        headers={"Content-Type": "application/json"}, method="POST")
    events, chunks, answer = [], [], ""
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        for raw in resp:
            line = raw.decode("utf-8").strip()
            if line.startswith("event: "):
                events.append(line[7:])
            elif line.startswith("data: ") and "content" in events:
                try:
                    c = json.loads(line[6:]).get("content", "")
                    if c:
                        chunks.append(c)
                except Exception:
                    pass
    answer = "".join(chunks)
    return events, answer


TEST_FILE = "D:\\work\\agentV1\\backend\\data\\demo_rag.txt"
with open(TEST_FILE, "w", encoding="utf-8") as f:
    f.write(DOC_TEXT)

print("=== 1. 上传文档 ===")
r = api("POST", "/documents/upload", files=[("demo_rag.txt", TEST_FILE, "text/plain")])
assert r["code"] == 0, r
doc_id, version_id = r["data"]["document_id"], r["data"]["version_id"]
print(f"document_id={doc_id} version_id={version_id}")

print("=== 2. 同步全链路（解析+清洗+切分+向量化） ===")
r = api("POST", f"/documents/{doc_id}/parse-sync", timeout=300)
d = r["data"]
print("stages:", json.dumps(d.get("stages", {}), ensure_ascii=False)[:400])
assert d.get("total_chunks", 0) >= 2, f"chunks 过少: {d.get('total_chunks')}"

print("=== 3. 混合检索 ===")
for q in ["混合检索如何融合向量与关键词", "系统使用什么消息队列", "如何实现文档版本管理"]:
    r = api("POST", "/retrieval/hybrid", {"query": q, "top_k": 3, "use_rerank": False})
    n = len(r["data"].get("results", [])) if isinstance(r["data"], dict) else 0
    print(f"  '{q}' -> {n} 条")

print("=== 4. 流式问答 ===")
events, answer = sse_stream("RAG知识库系统的混合检索是如何工作的？")
print("events:", [e for e in events if e != "content"][:5], f"content x{events.count('content')}")
print("answer:", answer[:200])
assert "start" in events and "content" in events and "done" in events
assert len(answer) > 20

print("=== 5. 非流式问答 ===")
r = api("POST", "/qa", {"question": "系统支持哪些文档格式？", "use_rerank": True, "top_k": 8}, timeout=180)
a = r["data"]["result"]["answer"]
print("answer:", a[:200])
assert r["code"] == 0 and len(a) > 20

print("\n===== 干净演示全部通过 =====")
