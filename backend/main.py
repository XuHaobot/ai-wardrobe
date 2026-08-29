"""
AI 智能衣橱 - FastAPI 主入口
基于多模态大模型的个性化穿搭推荐系统

技术栈: Python/FastAPI + ChromaDB + 通义千问VL + Function Calling
"""
import os
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from database import init_db
from config import get_settings
from seed_demo import ensure_demo_closet


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期"""
    # 启动时初始化
    settings = get_settings()
    os.makedirs(settings.upload_dir, exist_ok=True)
    os.makedirs(Path(__file__).resolve().parent / "data", exist_ok=True)
    init_db()
    ensure_demo_closet()
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


class CachedStaticFiles(StaticFiles):
    """衣物图/模特底图/试穿结果图基本不变，允许浏览器缓存一周（弱网二次打开提速明显）"""

    async def get_response(self, path, scope):
        response = await super().get_response(path, scope)
        if response.status_code == 200:
            response.headers["Cache-Control"] = "public, max-age=604800"
        return response


app.mount("/uploads", CachedStaticFiles(directory=settings.upload_dir), name="uploads")


class _SkipPathGZip:
    """对指定路径前缀跳过 gzip（图片本身已压缩，跳过以省 CPU），其余路径启用"""

    def __init__(self, app, skip_prefixes=(), minimum_size=1024):
        self.app = app
        self.gzip_app = GZipMiddleware(app, minimum_size=minimum_size)
        self.skip_prefixes = skip_prefixes

    async def __call__(self, scope, receive, send):
        path = scope.get("path", "") if scope.get("type") == "http" else ""
        if any(path.startswith(p) for p in self.skip_prefixes):
            await self.app(scope, receive, send)
        else:
            await self.gzip_app(scope, receive, send)


# gzip 压缩 JS/CSS/JSON（dist 产物 ~1.5MB → 传输 ~400KB），跳过 /uploads 图片
app.add_middleware(_SkipPathGZip, skip_prefixes=("/uploads",))

# 注册路由
from routers.auth import router as auth_router
from routers.closet import router as closet_router
from routers.recommend import router as recommend_router
from routers.tryon import router as tryon_router
from routers.weather import router as weather_router
from routers.chat import router as chat_router
from routers.locate import router as locate_router
from routers.history import router as history_router

app.include_router(auth_router, tags=["用户认证"])
app.include_router(closet_router, tags=["衣橱管理"])
app.include_router(recommend_router, tags=["穿搭推荐"])
app.include_router(tryon_router, tags=["虚拟试穿"])
app.include_router(weather_router, tags=["天气查询"])
app.include_router(chat_router, tags=["AI对话"])
app.include_router(locate_router, tags=["定位服务"])
app.include_router(history_router, tags=["搭配历史"])


@app.get("/api")
async def api_root():
    """API 信息（服务健康检查）。根路径 / 必须留给前端 SPA ——
    此前根路径返回 JSON 说明，部署后用户打开首页看到的是 JSON 而非应用。"""
    return {
        "name": "AI 智能衣橱",
        "version": "2.0.0",
        "description": "基于多模态大模型的个性化穿搭推荐系统 - API 服务",
    }


# ============================================================
# 生产环境：托管前端构建产物（仅当 dist 存在时生效，本地开发不受影响）
# 单容器同时提供 API 与 SPA，CloudRun 部署无需额外静态服务器
# ============================================================
_FRONTEND_DIST = Path(__file__).resolve().parent.parent / "ai-outfit-recommender" / "dist"
if not _FRONTEND_DIST.exists():
    _FRONTEND_DIST = Path("/app/static")  # Docker 内备选路径

# 这些前缀属于后端 API，未匹配时应返回 404 而非 SPA 首页
_API_PREFIXES = (
    "api/", "auth/", "recommend/", "items/", "closet/", "tryon/",
    "weather/", "uploads/", "user/", "users/", "locate/", "outfit/",
)


@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    # 已注册的 API 路由优先匹配；这里只处理未匹配的路径
    if _FRONTEND_DIST.exists():
        target = _FRONTEND_DIST / full_path
        if full_path and target.is_file():
            return FileResponse(str(target))
        if not full_path.startswith(_API_PREFIXES):
            return FileResponse(str(_FRONTEND_DIST / "index.html"))
    raise HTTPException(status_code=404, detail="Not Found")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)
