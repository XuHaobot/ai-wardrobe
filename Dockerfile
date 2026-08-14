# ============================================================
# AI 智能衣橱 部署镜像（单容器同时跑前后端）
# 构建上下文：项目根目录（/e/aitryon）
# 说明：前端构建产物 dist 由后端在 / 路径托管（main.py 已加 SPA 托管）
# ============================================================

# ---------- 阶段 1：构建前端 ----------
FROM node:20-alpine AS frontend
WORKDIR /build
COPY ai-outfit-recommender/package.json ai-outfit-recommender/package-lock.json* ./
RUN npm install
COPY ai-outfit-recommender/ ./
RUN npm run build

# ---------- 阶段 2：运行环境 ----------
FROM python:3.12-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/backend \
    PORT=8080

WORKDIR /app/backend

# 安装 Python 依赖
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# 复制后端代码
COPY backend/ ./

# 前端构建产物 → /app/ai-outfit-recommender/dist（与 main.py 的 _FRONTEND_DIST 对应）
COPY --from=frontend /build/dist /app/ai-outfit-recommender/dist

# 启动脚本
COPY entrypoint.sh ./entrypoint.sh
RUN chmod +x ./entrypoint.sh

EXPOSE 8080
ENTRYPOINT ["./entrypoint.sh"]
