"""
搭配历史路由 - 保存/查看/删除用户的穿搭方案
"""
import json

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from database import get_db
from models.outfit_history import OutfitHistory
from schemas.common import Result
from main_deps import get_guest_context, require_real_user, GuestContext

router = APIRouter()


class SaveOutfitRequest(BaseModel):
    title: str = "我的搭配"
    items: list = []          # [{"url":..., "name":...}, ...]
    reason: str = ""
    weather: str = ""
    purpose: str = ""
    scene_type: str = "daily"  # daily / travel


@router.post("/outfit/history")
async def save_outfit(
    body: SaveOutfitRequest,
    user_id: int = Depends(require_real_user),
    db: Session = Depends(get_db),
):
    """保存一套搭配（仅登录用户）"""
    try:
        if not body.items:
            return Result.error("搭配不能为空")
        record = OutfitHistory(
            user_id=user_id,
            title=body.title or "我的搭配",
            items_json=json.dumps(body.items, ensure_ascii=False),
            reason=body.reason or "",
            weather=body.weather or "",
            purpose=body.purpose or "",
            scene_type=body.scene_type or "daily",
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return Result.success({
            "id": record.id,
            "title": record.title,
            "scene_type": record.scene_type,
            "created_at": record.created_at.isoformat() if record.created_at else "",
        })
    except Exception as e:
        return Result.error(f"保存失败: {str(e)}")


@router.get("/outfit/history")
async def list_history(
    scene_type: str = Query(None, description="daily / travel / 不传返回全部"),
    limit: int = Query(50, ge=1, le=200),
    ctx: GuestContext = Depends(get_guest_context),
    db: Session = Depends(get_db),
):
    """查看搭配历史（游客返回演示账号历史，登录用户返回自己的）"""
    query = db.query(OutfitHistory).filter(OutfitHistory.user_id == ctx.user_id)
    if scene_type:
        query = query.filter(OutfitHistory.scene_type == scene_type)
    records = query.order_by(OutfitHistory.created_at.desc()).limit(limit).all()

    return Result.success({
        "is_guest": ctx.is_guest,
        "count": len(records),
        "items": [
            {
                "id": r.id,
                "title": r.title,
                "items": json.loads(r.items_json or "[]"),
                "reason": r.reason or "",
                "weather": r.weather or "",
                "purpose": r.purpose or "",
                "scene_type": r.scene_type or "daily",
                "created_at": r.created_at.isoformat() if r.created_at else "",
            }
            for r in records
        ],
    })


@router.delete("/outfit/history/{history_id}")
async def delete_history(
    history_id: int,
    user_id: int = Depends(require_real_user),
    db: Session = Depends(get_db),
):
    """删除一条搭配历史（仅登录用户，且只能删自己的）"""
    record = db.query(OutfitHistory).filter(
        OutfitHistory.id == history_id,
        OutfitHistory.user_id == user_id,
    ).first()
    if not record:
        return Result.error("未找到该记录")
    db.delete(record)
    db.commit()
    return Result.success(message="已删除")
