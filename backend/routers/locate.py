"""
定位查询路由（IP 定位 + 浏览器坐标逆地理编码）

设计目的：前端不再直连高德 API，避免 API Key 被打包到前端 bundle
所有高德 Key 仅存在于后端 .env 中
"""
import os
import httpx
from fastapi import APIRouter, Query
from schemas.common import Result
from config import get_settings

router = APIRouter()

AMAP_BASE = "https://restapi.amap.com/v3"

# 复用后端 .env 的高德 Key（前端永远不会看到这个变量）
settings = get_settings()
AMAP_KEY = settings.amap_api_key


@router.get("/api/locate/ip")
async def locate_by_ip():
    """
    通过客户端 IP 定位城市（降级方案：浏览器定位失败时使用）
    返回 { adcode, province, city }
    """
    if not AMAP_KEY:
        return Result.error("后端未配置 AMAP_API_KEY")
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            res = await client.get(f"{AMAP_BASE}/ip", params={"key": AMAP_KEY})
            data = res.json()
        if data.get("status") == "1":
            return Result.success({
                "adcode": data.get("adcode", ""),
                "province": data.get("province", ""),
                "city": data.get("city", ""),
            })
        return Result.error(f"高德 IP 定位失败: {data.get('info', 'unknown')}")
    except Exception as e:
        return Result.error(f"IP 定位异常: {str(e)}")


@router.get("/api/locate/regeo")
async def reverse_geocode(lng: float = Query(..., description="经度"), lat: float = Query(..., description="纬度")):
    """
    经纬度 -> 城市名（浏览器 GPS 定位后使用）
    返回 { adcode, province, city }
    """
    if not AMAP_KEY:
        return Result.error("后端未配置 AMAP_API_KEY")
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            res = await client.get(
                f"{AMAP_BASE}/geocode/regeo",
                params={
                    "key": AMAP_KEY,
                    "location": f"{lng},{lat}",
                    "radius": 1000,
                    "extensions": "base",
                    "batch": "false",
                    "roadlevel": 0,
                },
            )
            data = res.json()
        if data.get("status") == "1":
            comp = data.get("regeocode", {}).get("addressComponent", {})
            return Result.success({
                "adcode": comp.get("adcode", ""),
                "province": comp.get("province", ""),
                "city": comp.get("city", ""),
            })
        return Result.error(f"高德逆地理失败: {data.get('info', 'unknown')}")
    except Exception as e:
        return Result.error(f"逆地理异常: {str(e)}")
