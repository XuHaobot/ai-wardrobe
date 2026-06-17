"""
虚拟试穿路由
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel

from database import get_db
from schemas.common import Result
from services.tryon_service import TryOnService
from main_deps import get_current_user_id

router = APIRouter()


class TryOnRequest(BaseModel):
    gender: str = "female"
    clothingUrls: list[str] = []


@router.post("/tryon")
async def try_on(
    body: TryOnRequest,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """AI虚拟试穿"""
    if not body.clothingUrls:
        return Result.error("请选择至少一件衣物")
    try:
        result = await TryOnService.try_on(db, user_id, body.gender, body.clothingUrls)
        return Result.success(result)
    except Exception as e:
        return Result.error(f"试穿失败: {str(e)}")
