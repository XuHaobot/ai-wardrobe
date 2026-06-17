"""
高德天气查询工具
"""
import httpx
from config import get_settings


async def geocode_city(city: str) -> str:
    """将城市名转换为行政区划代码(adcode)"""
    settings = get_settings()
    # 如果已经是6位数字，直接返回
    if city.isdigit() and len(city) == 6:
        return city

    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(
            "https://restapi.amap.com/v3/geocode/geo",
            params={
                "key": settings.amap_api_key,
                "address": city,
            },
        )
    data = resp.json()
    geocodes = data.get("geocodes", [])
    if geocodes:
        return geocodes[0].get("adcode", "")
    return ""


async def get_weather(city: str = "北京") -> str:
    """
    查询指定城市的实时天气
    返回格式: "城市：北京，天气：晴，温度：28℃，..."
    """
    settings = get_settings()
    adcode = await geocode_city(city)
    if not adcode:
        return f"无法获取城市 {city} 的天气信息"

    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(
            "https://restapi.amap.com/v3/weather/weatherInfo",
            params={
                "key": settings.amap_api_key,
                "city": adcode,
                "extensions": "base",
            },
        )
    data = resp.json()
    lives = data.get("lives", [])
    if not lives:
        return f"无法获取城市 {city} 的天气信息"

    w = lives[0]
    return (
        f"城市：{w.get('city', city)}，"
        f"天气：{w.get('weather', '未知')}，"
        f"温度：{w.get('temperature', '?')}℃，"
        f"风向：{w.get('winddirection', '未知')}，"
        f"风力：{w.get('windpower', '?')}级，"
        f"湿度：{w.get('humidity', '?')}%"
    )
