"""
虚拟试穿路由
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel

from database import get_db
from schemas.common import Result
from services.tryon_service import TryOnService
from main_deps import get_guest_context, GuestContext

router = APIRouter()


class TryOnRequest(BaseModel):
    gender: str = "female"
    clothingUrls: list[str] = []


@router.post("/tryon")
async def try_on(
    body: TryOnRequest,
    ctx: GuestContext = Depends(get_guest_context),
    db: Session = Depends(get_db),
):
    """AI虚拟试穿（游客可用演示衣橱试穿）"""
    user_id = ctx.user_id
    """AI虚拟试穿"""
    if not body.clothingUrls:
        return Result.error("请选择至少一件衣物")
    try:
        result = await TryOnService.try_on(db, user_id, body.gender, body.clothingUrls)
        return Result.success(result)
    except Exception as e:
        return Result.error(f"试穿失败: {str(e)}")
