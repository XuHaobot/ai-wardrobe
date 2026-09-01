# ============================================================
# AI 智能衣橱 部署镜像（带国内极速源加速）
# ============================================================

# ---------- 阶段 1：构建前端 ----------
FROM node:20-alpine AS frontend
WORKDIR /build
COPY ai-outfit-recommender/package.json ai-outfit-recommender/package-lock.json* ./
RUN npm install --registry=https://registry.npmmirror.com
COPY ai-outfit-recommender/ ./
RUN npm run build

# ---------- 阶段 2：运行环境 ----------
FROM python:3.12-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/backend \
    PORT=8080

WORKDIR /app/backend

# 安装 Python 依赖（使用阿里云高速镜像源）
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com

# 复制后端代码
COPY backend/ ./

# 前端构建产物
COPY --from=frontend /build/dist /app/ai-outfit-recommender/dist

# 启动脚本
COPY entrypoint.sh ./entrypoint.sh
RUN chmod +x ./entrypoint.sh

EXPOSE 8080
ENTRYPOINT ["./entrypoint.sh"]
