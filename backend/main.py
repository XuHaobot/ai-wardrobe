"""
AI 智能衣橱 - FastAPI 主入口
基于多模态大模型的个性化穿搭推荐系统

技术栈: Python/FastAPI + ChromaDB + 通义千问VL + Function Calling
"""
import os
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from database import init_db
from config import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期"""
    # 启动时初始化
    settings = get_settings()
    os.makedirs(settings.upload_dir, exist_ok=True)
    os.makedirs(Path(__file__).resolve().parent / "data", exist_ok=True)
    init_db()
    print("[OK] 数据库初始化完成")
    print(f"[DIR] 上传目录: {os.path.abspath(settings.upload_dir)}")
    print(f"[KEY] DashScope API: {'已配置' if settings.dashscope_api_key else '未配置'}")
    print(f"[KEY] 高德天气 API: {'已配置' if settings.amap_api_key else '未配置'}")
    print(f"[KEY] 火山引擎: {'已配置' if settings.volc_access_key else '未配置'}")
    print(f"[KEY] 腾讯云 COS: {'已配置' if settings.cos_secret_id else '未配置（衣物图存本地）'}")
    yield
    # 关闭时清理
    print("[BYE] AI衣橱服务关闭")


app = FastAPI(
    title="AI 智能衣橱",
    description="基于多模态大模型的个性化穿搭推荐系统 - FastAPI后端",
    version="2.0.0",
    lifespan=lifespan,
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件 - uploads目录
settings = get_settings()
os.makedirs(settings.upload_dir, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.upload_dir), name="uploads")

# 注册路由
from routers.auth import router as auth_router
from routers.closet import router as closet_router
from routers.recommend import router as recommend_router
from routers.tryon import router as tryon_router
from routers.weather import router as weather_router
from routers.chat import router as chat_router
from routers.locate import router as locate_router

app.include_router(auth_router, tags=["用户认证"])
app.include_router(closet_router, tags=["衣橱管理"])
app.include_router(recommend_router, tags=["穿搭推荐"])
app.include_router(tryon_router, tags=["虚拟试穿"])
app.include_router(weather_router, tags=["天气查询"])
app.include_router(chat_router, tags=["AI对话"])
app.include_router(locate_router, tags=["定位服务"])


@app.get("/")
async def root():
    return {
        "name": "AI 智能衣橱",
        "version": "2.0.0",
        "description": "基于多模态大模型的个性化穿搭推荐系统",
        "features": [
            "多模态衣物识别 (Qwen VL)",
            "向量语义搜索 (DashScope Embedding + ChromaDB)",
            "Agent智能推荐 (Function Calling)",
            "虚拟试穿 (即梦/WanX)",
            "多轮对话 (Memory + SSE Streaming)",
        ],
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)
