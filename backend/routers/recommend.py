"""
穿搭推荐路由
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from database import get_db
from schemas.common import Result
from services.recommend_service import RecommendService
from main_deps import get_current_user_id

router = APIRouter()


@router.get("/recommend")
async def get_recommendation(
    purpose: str = Query("", description="出行目的"),
    city: str = Query("北京", description="城市"),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """AI穿搭推荐"""
    try:
        result = await RecommendService.recommend(db, user_id, purpose, city)
        return Result.success(result)
    except Exception as e:
        return Result.error(f"推荐失败: {str(e)}")


@router.get("/closet/search")
async def search_closet(
    q: str = Query(..., description="搜索关键词"),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """智能搜索衣橱（向量语义 + 关键词混合）"""
    try:
        results = await RecommendService.smart_search(db, user_id, q)
        return Result.success(results)
    except Exception as e:
        return Result.error(f"搜索失败: {str(e)}")
