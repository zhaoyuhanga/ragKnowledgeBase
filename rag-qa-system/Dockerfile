# ============================================================
# RAG 问答系统 - Docker 镜像配置
# 基于 Python 3.12 的多阶段构建
# ============================================================

# ============================================================
# 第一阶段：构建阶段
# ============================================================
FROM python:3.12-slim AS builder

# 设置工作目录
WORKDIR /build

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖（优化层）
RUN pip install --no-cache-dir --user --upgrade pip && \
    pip install --no-cache-dir --user -r requirements.txt

# ============================================================
# 第二阶段：运行阶段
# ============================================================
FROM python:3.12-slim

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    APP_HOME=/app

# 安装运行时依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 创建应用目录
RUN mkdir -p ${APP_HOME}
WORKDIR ${APP_HOME}

# 从构建阶段复制依赖
COPY --from=builder /root/.local ${APP_HOME}/.local
COPY --from=builder /usr/local/lib/python3.12/site-packages ${APP_HOME}/.local/lib/python3.12/site-packages

# 设置 PATH
ENV PATH=${APP_HOME}/.local/bin:${PATH}

# 复制应用代码
COPY app/ ${APP_HOME}/app/
COPY scripts/ ${APP_HOME}/scripts/
COPY data/ ${APP_HOME}/data/
COPY logs/ ${APP_HOME}/logs/

# 复制配置文件
COPY requirements.txt ${APP_HOME}/
COPY .env.example ${APP_HOME}/.env

# 创建必要的目录
RUN mkdir -p ${APP_HOME}/data/documents \
    ${APP_HOME}/data/chroma \
    ${APP_HOME}/logs

# 设置所有者
RUN chown -R python:python ${APP_HOME}

# 切换到非 root 用户
USER python

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 启动命令
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
