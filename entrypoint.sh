#!/bin/sh
# AI 智能衣橱 生产启动脚本
set -e

# CloudBase / 容器注入的端口，缺省 8080
export PORT="${PORT:-8080}"

echo "[START] AI 智能衣橱 后端 + 前端 (port=$PORT)"

# 直接以 uvicorn 拉起；lifespan 内会 init_db + 预置演示衣橱
exec uvicorn main:app --host 0.0.0.0 --port "$PORT"
