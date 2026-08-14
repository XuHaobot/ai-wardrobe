"""
推荐服务 - 调用AI推荐 + 向量检索增强
"""
import re
import json
from sqlalchemy.orm import Session
from utils.ai_recommend import generate_recommendation
from services.closet_service import ClosetService, _extract_name
from config import get_settings


class RecommendService:

    @staticmethod
    async def recommend(
        db: Session,
        user_id: int,
        purpose: str = "",
        city: str = "北京",
    ) -> list[dict]:
        """
        AI穿搭推荐：
        1. 获取用户衣橱全部衣物
        2. 调用LLM生成推荐
        3. 验证推荐中的衣物URL是否真实存在
        """
        items = ClosetService.get_all_items(db, user_id)
        if not items:
            return []

        recommendations = await generate_recommendation(items, purpose, city)
        return recommendations

    @staticmethod
    async def smart_search(db: Session, user_id: int, query: str) -> list[dict]:
        """
        智能搜索：结合向量语义搜索 + 关键词匹配
        """
        results = []

        # 1. 向量语义搜索
        try:
            from services.vector_store import VectorStore
            vs = VectorStore()
            semantic_results = vs.semantic_search(query, user_id, top_k=5)
            results.extend(semantic_results)
        except Exception:
            pass

        # 2. 关键词搜索补充
        from models.item import ClosetItem
        keyword_items = (
            db.query(ClosetItem)
            .filter(ClosetItem.user_id == user_id)
            .filter(
                ClosetItem.description.contains(query)
                | ClosetItem.category.contains(query)
                | ClosetItem.color.contains(query)
            )
            .limit(5)
            .all()
        )

        existing_ids = {r.get("id") for r in results}
        for item in keyword_items:
            if item.id not in existing_ids:
                results.append({
                    "id": item.id,
                    "url": item.url,
                    "name": _extract_name(item.description or ""),
                    "category": item.category or "all",
                    "score": 0.5,
                    "document": item.description or "",
                })

        return results[:10]

    @staticmethod
    async def generate_packing(
        db: Session,
        user_id: int,
        purpose: str = "",
        city: str = "北京",
        days: int = 3,
        season: str = "",
    ) -> dict:
        """
        旅行场景打包推荐：基于衣橱生成「胶囊衣橱」清单。
        返回：{ city, days, season, items:[{name, category, url, qty, reason}], tips:[...] }
        """
        items = ClosetService.get_all_items(db, user_id)
        if not items:
            return {"city": city, "days": days, "season": season, "items": [], "tips": []}

        settings = get_settings()
        wardrobe_text = ""
        for i, item in enumerate(items, 1):
            wardrobe_text += f"{i}. 图片URL: {item['url']}\n   描述: {item.get('description', '无描述')}\n\n"

        weather_info = await get_weather(city)
        season_hint = f"季节偏好：{season}\n" if season else ""

        system_prompt = """你是一位专业的旅行穿搭规划师。请根据用户衣橱、目的地天气、行程天数，生成一份「胶囊衣橱」打包清单。

规则：
1. 只能从用户衣橱中已有的衣物里挑选（图片URL必须与衣橱完全一致）
2. 优先覆盖：上装、下装、外套、鞋、配饰，按天数控制件数（避免过多）
3. 给出每件的建议携带数量(qty)与选择理由(reason)
4. 补充 2-4 条通用打包贴士(tips)
5. 返回严格 JSON 对象

输出格式（严格JSON）：
{
  "items": [
    {"name": "衣物名", "category": "品类", "url": "图片URL", "qty": 2, "reason": "选择理由"}
  ],
  "tips": ["贴士1", "贴士2"]
}"""

        user_prompt = f"""目的地：{city}
行程天数：{days} 天
出行场景：{purpose or '休闲旅行'}
{season_hint}当前天气：{weather_info}

我的衣橱：
{wardrobe_text}

请生成一份适合这次出行的胶囊衣橱打包清单（件数精简易带，覆盖主要场景）。"""

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
            return {"city": city, "days": days, "season": season, "items": [], "tips": []}

        # 提取 JSON 对象
        obj_match = re.search(r"\{.*\}", content, re.DOTALL)
        if not obj_match:
            return {"city": city, "days": days, "season": season, "items": [], "tips": []}
        try:
            parsed = json.loads(obj_match.group())
        except json.JSONDecodeError:
            return {"city": city, "days": days, "season": season, "items": [], "tips": []}

        valid_urls = {item["url"] for item in items}
        pack_items = []
        for it in parsed.get("items", []):
            url = it.get("url", "")
            if url not in valid_urls:
                continue
            pack_items.append({
                "name": it.get("name", "衣物"),
                "category": it.get("category", ""),
                "url": url,
                "qty": max(1, int(it.get("qty", 1) or 1)),
                "reason": it.get("reason", ""),
            })

        return {
            "city": city,
            "days": days,
            "season": season,
            "items": pack_items,
            "tips": parsed.get("tips", []),
        }
