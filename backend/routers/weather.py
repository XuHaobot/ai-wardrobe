"""
天气查询路由
"""
from fastapi import APIRouter, Query
from schemas.common import Result
from utils.ai_weather import get_weather

router = APIRouter()


@router.get("/weather")
async def weather(city: str = Query("北京", description="城市名")):
    """查询实时天气"""
    try:
        result = await get_weather(city)
        return Result.success(result)
    except Exception as e:
        return Result.error(f"天气查询失败: {str(e)}")
