"""
虚拟试穿服务
"""
import os
import logging
import sys
from sqlalchemy.orm import Session
from models.item import ClosetItem
from utils.ai_tryon import generate_tryon
from services.closet_service import _extract_name
from config import get_settings

logger = logging.getLogger("tryon_service")
# 确保日志输出到控制台
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("[tryon] %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)


class TryOnService:

    @staticmethod
    async def try_on(
        db: Session,
        user_id: int,
        gender: str,
        clothing_urls: list[str],
    ) -> dict:
        """
        虚拟试穿：
        1. 加载模特底图
        2. 加载选中的衣物图片
        3. 查询衣物描述
        4. 调用AI生成试穿图
        """
        settings = get_settings()

        # 加载模特底图
        model_filename = "女.png" if gender == "female" else "男.png"
        model_path = os.path.join(settings.upload_dir, model_filename)
        if not os.path.exists(model_path):
            model_path = os.path.join(settings.upload_dir, "model_" + model_filename)
        if not os.path.exists(model_path):
            # 扫描 uploads 目录找模特图
            for f in os.listdir(settings.upload_dir):
                if "女" in f or "model" in f.lower():
                    model_path = os.path.join(settings.upload_dir, f)
                    break
        if not os.path.exists(model_path):
            logger.warning(f"Model image not found: {model_filename}, upload_dir={settings.upload_dir}")
            return {"success": False, "imageUrl": None, "message": f"模特底图 {model_filename} 不存在，请上传模特图到 uploads 目录"}

        with open(model_path, "rb") as f:
            model_image = f.read()
        logger.info(f"Model image loaded: {model_path} ({len(model_image)} bytes)")

        # 加载衣物图片和信息
        clothing_images = []
        clothing_items = []

        for url in clothing_urls:
            # 查询DB: 尝试精确匹配和模糊匹配
            item = db.query(ClosetItem).filter(
                ClosetItem.url == url,
                ClosetItem.user_id == user_id,
            ).first()

            if not item:
                # 模糊匹配: 只比较文件路径部分
                from sqlalchemy import func
                url_path = url.split("://")[-1] if "://" in url else url
                url_path = "/" + url_path.lstrip("/")
                item = db.query(ClosetItem).filter(
                    ClosetItem.user_id == user_id,
                    ClosetItem.url.like(f"%{url_path}%"),
                ).first()

            if item:
                clothing_items.append({
                    "url": item.url,
                    "name": _extract_name(item.description or ""),
                    "description": item.description or "",
                    "category": item.category or "",
                })
                img_bytes = TryOnService._load_image_bytes(item.url, settings)
                if img_bytes:
                    clothing_images.append(img_bytes)
                    logger.info(f"Loaded clothing image from DB: {len(img_bytes)} bytes from {item.url[:60]}")
                else:
                    logger.warning(f"Failed to load image for: {item.url}")
            else:
                # DB中没找到，尝试直接从文件系统加载
                logger.info(f"Item not in DB, trying direct file load for: {url}")
                img_bytes = TryOnService._load_image_bytes(url, settings)
                if img_bytes:
                    clothing_images.append(img_bytes)
                    # 从文件名推断信息
                    filename = url.split("/")[-1] if "/" in url else url
                    clothing_items.append({
                        "url": url,
                        "name": filename,
                        "description": "",
                        "category": "short_sleeve",  # 默认分类
                    })
                    logger.info(f"Loaded clothing image from file: {len(img_bytes)} bytes from {url[:60]}")
                else:
                    logger.warning(f"Could not load image from file: {url}")

        if not clothing_images:
            return {"success": False, "imageUrl": None, "message": "未找到有效的衣物图片"}

        logger.info(f"Calling AI tryon with {len(clothing_images)} images, {len(clothing_items)} items")
        result = await generate_tryon(model_image, clothing_images, clothing_items, gender)
        return result

    @staticmethod
    def _load_image_bytes(url: str, settings) -> bytes | None:
        """
        从URL加载图片字节数据
        支持: 本地路径 /uploads/xxx.jpg, COS公网URL, 其他HTTP URL
        """
        # 情况1: 相对路径 /uploads/xxx.jpg
        if url.startswith("/uploads/"):
            filename = url.split("/uploads/")[-1]
            local_path = os.path.join(settings.upload_dir, filename)
            if os.path.exists(local_path):
                with open(local_path, "rb") as f:
                    return f.read()

        # 情况2: 腾讯云 COS 公网 URL (https://bucket.cos.region.myqcloud.com/key)
        if url.startswith("http") and ".myqcloud.com" in url:
            import httpx
            try:
                resp = httpx.get(url, timeout=20, follow_redirects=True)
                if resp.status_code == 200:
                    logger.info(f"Downloaded from COS: {url[:80]} ({len(resp.content)} bytes)")
                    return resp.content
                else:
                    logger.warning(f"COS download HTTP {resp.status_code}: {url[:80]}")
            except Exception as e:
                logger.error(f"COS download failed: {e}")
            # COS 下载失败，尝试从本地缓存加载
            filename = url.split("/")[-1]
            local_path = os.path.join(settings.upload_dir, filename)
            if os.path.exists(local_path):
                logger.info(f"Fallback to local cache: {local_path}")
                with open(local_path, "rb") as f:
                    return f.read()
            return None

        # 情况3: 本地开发URL http://localhost:8080/uploads/xxx.jpg
        if url.startswith("http") and "/uploads/" in url:
            filename = url.split("/uploads/")[-1]
            local_path = os.path.join(settings.upload_dir, filename)
            if os.path.exists(local_path):
                with open(local_path, "rb") as f:
                    return f.read()

        # 情况4: 其他外部URL，HTTP下载
        if url.startswith("http"):
            import httpx
            try:
                resp = httpx.get(url, timeout=15, follow_redirects=True)
                return resp.content
            except Exception as e:
                logger.error(f"HTTP download failed: {e}")

        return None
