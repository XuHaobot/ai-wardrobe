"""
衣橱服务 - 衣物CRUD + AI识别 + COS云存储
"""
import os
import re
import uuid
from typing import Optional

from sqlalchemy.orm import Session

from models.item import ClosetItem
from utils.ai_util import recognize_clothing, extract_name as _extract_name
from services.cos_storage import upload_to_cos, delete_from_cos, is_cos_enabled
from config import get_settings


class ClosetService:

    @staticmethod
    async def add_item(db: Session, user_id: int, image_bytes: bytes, filename: str = "") -> ClosetItem:
        """上传衣物图片 -> AI识别 -> 存本地 + COS云存储"""
        settings = get_settings()

        # 保存到本地（缓存 + 离线备用）
        ext = os.path.splitext(filename)[1] or ".jpg"
        local_name = f"{uuid.uuid4().hex}{ext}"
        upload_dir = settings.upload_dir
        os.makedirs(upload_dir, exist_ok=True)
        local_path = os.path.join(upload_dir, local_name)

        with open(local_path, "wb") as f:
            f.write(image_bytes)

        # 默认使用本地 URL
        url = f"/uploads/{local_name}"

        # 如果 COS 已配置，同时上传到云端
        if is_cos_enabled():
            cos_url = upload_to_cos(image_bytes, filename=local_name, folder="closet")
            if cos_url:
                url = cos_url  # 优先使用 COS URL

        # AI识别
        ai_result = await recognize_clothing(image_bytes)
        description = ai_result.get("description", "")
        category = ai_result.get("category", "all")

        # 从描述中提取颜色和季节
        color = ""
        season = ""
        thickness = ""
        color_match = re.search(r"颜色[:：]\s*(.+?)(?:\n|$)", description)
        if color_match:
            color = color_match.group(1).strip()[:50]
        season_match = re.search(r"适用天气[:：]\s*(.+?)(?:\n|$)", description)
        if season_match:
            season = season_match.group(1).strip()[:20]
        thick_match = re.search(r"厚度[:：]\s*(.+?)(?:\n|$)", description)
        if thick_match:
            thickness = thick_match.group(1).strip()[:20]

        item = ClosetItem(
            url=url,
            description=description,
            category=category,
            color=color,
            season=season,
            thickness=thickness,
            user_id=user_id,
        )
        db.add(item)
        db.commit()
        db.refresh(item)

        # 同时存入向量库
        from services.vector_store import VectorStore
        try:
            vs = VectorStore()
            vs.upsert_item(item.id, item.description or "", {
                "category": item.category,
                "user_id": user_id,
                "url": item.url,
            })
        except Exception:
            pass  # 向量库失败不影响主流程

        return item

    @staticmethod
    def get_items(db: Session, user_id: int, page: int = 1, size: int = 100, category: str = None) -> dict:
        """分页获取用户衣橱"""
        query = db.query(ClosetItem).filter(ClosetItem.user_id == user_id)
        if category and category != "all":
            query = query.filter(ClosetItem.category == category)

        total = query.count()
        items = query.offset((page - 1) * size).limit(size).all()

        return {
            "count": total,
            "items": [
                {
                    "id": item.id,
                    "url": item.url,
                    "name": _extract_name(item.description or ""),
                    "description": item.description,
                    "category": item.category or "all",
                    "color": item.color or "",
                    "season": item.season or "",
                }
                for item in items
            ],
        }

    @staticmethod
    def get_all_items(db: Session, user_id: int) -> list[dict]:
        """获取用户所有衣物（不分页）"""
        items = db.query(ClosetItem).filter(ClosetItem.user_id == user_id).all()
        return [
            {"id": item.id, "url": item.url,
             "name": _extract_name(item.description or ""),
             "description": item.description, "category": item.category or "all"}
            for item in items
        ]

    @staticmethod
    def delete_item(db: Session, user_id: int, url: str) -> bool:
        """删除衣物（本地 + COS）"""
        item = db.query(ClosetItem).filter(
            ClosetItem.user_id == user_id,
            ClosetItem.url == url,
        ).first()
        if not item:
            return False

        # 删除本地文件
        if item.url and item.url.startswith("/uploads/"):
            filename = item.url.split("/uploads/")[-1]
            local_path = os.path.join(settings.upload_dir, filename) if hasattr(settings, 'upload_dir') else None
            if local_path and os.path.exists(local_path):
                os.remove(local_path)

        # 删除 COS 文件
        if item.url and item.url.startswith("http") and ".myqcloud.com" in item.url:
            delete_from_cos(item.url)

        # 从向量库删除
        try:
            from services.vector_store import VectorStore
            vs = VectorStore()
            vs.delete_item(item.id)
        except Exception:
            pass

        db.delete(item)
        db.commit()
        return True

    @staticmethod
    def rename_item(db: Session, user_id: int, item_id: int, name: str) -> bool:
        """重命名衣物（更新描述的第一行）"""
        item = db.query(ClosetItem).filter(
            ClosetItem.id == item_id,
            ClosetItem.user_id == user_id,
        ).first()
        if not item:
            return False
        # 在描述前插入名称标记
        item.description = f"名称: {name}\n{item.description or ''}"
        db.commit()
        return True

    @staticmethod
    def get_item_by_id(db: Session, item_id: int) -> Optional[ClosetItem]:
        return db.query(ClosetItem).filter(ClosetItem.id == item_id).first()
