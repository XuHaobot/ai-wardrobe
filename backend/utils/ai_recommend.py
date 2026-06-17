"""
AI 推荐工具 - 通义千问 LLM 穿搭推荐
"""
import json
import re
import httpx
from config import get_settings
from utils.ai_weather import get_weather


async def generate_recommendation(
    closet_items: list[dict],
    purpose: str = "",
    city: str = "北京",
) -> list[dict]:
    """
    调用通义千问进行穿搭推荐
    closet_items: [{"url": str, "description": str}, ...]
    返回推荐列表: [{"title": str, "urls": list, "reason": str, "weather": str}, ...]
    """
    settings = get_settings()

    # 构建衣橱信息文本
    wardrobe_text = ""
    for i, item in enumerate(closet_items, 1):
        wardrobe_text += f"{i}. 图片URL: {item['url']}\n   描述: {item.get('description', '无描述')}\n\n"

    # 获取天气
    weather_info = await get_weather(city)

    system_prompt = """你是一位专业的穿搭推荐师。请根据用户的衣橱信息、当前天气和出行目的，推荐2套穿搭方案。

规则：
1. 每套方案必须从用户衣橱中选择实际存在的衣物（图片URL必须与衣橱中的完全一致）
2. 每套搭配：1件上衣 + 1件下装 + (可选)1件外套
3. 考虑天气适宜性、颜色搭配、场合需求
4. 返回JSON数组格式

输出格式（严格JSON数组）：
[
  {
    "title": "方案标题（简短有风格感）",
    "urls": ["选中的衣物图片URL1", "URL2"],
    "reason": "推荐理由（50-100字，涵盖风格/天气/场合/配色逻辑）",
    "weather": "适宜天气描述"
  }
]"""

    user_prompt = f"""当前天气：{weather_info}
出行目的：{purpose or '日常穿搭'}

我的衣橱：
{wardrobe_text}

请从以上衣橱中选择衣物，推荐2套穿搭方案。"""

    headers = {
        "Authorization": f"Bearer {settings.dashscope_api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": settings.qwen_text_model,
        "input": {
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ]
        },
        "parameters": {"temperature": 0.7, "max_tokens": 2000},
    }

    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation",
            headers=headers,
            json=payload,
        )

    data = resp.json()
    try:
        content = data["output"]["text"]
    except (KeyError, TypeError):
        return []

    # 解析JSON（处理可能的markdown代码块包裹）
    json_match = re.search(r"\[.*\]", content, re.DOTALL)
    if json_match:
        try:
            recommendations = json.loads(json_match.group())
        except json.JSONDecodeError:
            return []
    else:
        return []

    # 验证推荐中的URL是否存在于衣橱
    valid_urls = {item["url"] for item in closet_items}
    validated = []
    for rec in recommendations:
        urls = [u for u in rec.get("urls", []) if u in valid_urls]
        if urls:
            validated.append({
                "title": rec.get("title", "推荐方案"),
                "urls": urls,
                "reason": rec.get("reason", ""),
                "weather": rec.get("weather", weather_info),
            })

    return validated
