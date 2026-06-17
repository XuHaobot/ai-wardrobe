"""
Agent 工具实现 - 执行各个工具的具体逻辑
"""
import json
from sqlalchemy.orm import Session
from services.closet_service import ClosetService
from services.recommend_service import RecommendService
from services.vector_store import VectorStore
from utils.ai_weather import get_weather


class ToolExecutor:
    """工具执行器"""

    def __init__(self, user_id: int, db: Session):
        self.user_id = user_id
        self.db = db

    async def execute(self, tool_name: str, arguments: dict) -> str:
        """执行工具并返回结果（JSON字符串）"""
        handler = getattr(self, f"_exec_{tool_name}", None)
        if not handler:
            return json.dumps({"error": f"未知工具: {tool_name}"}, ensure_ascii=False)

        try:
            result = await handler(arguments)
            return json.dumps(result, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"error": f"工具执行失败: {str(e)}"}, ensure_ascii=False)

    async def _exec_search_closet(self, args: dict) -> dict:
        """搜索衣橱"""
        query = args.get("query", "")
        category = args.get("category", "all")

        # 优先使用向量语义搜索
        try:
            vs = VectorStore()
            results = vs.semantic_search(query, self.user_id, top_k=10)
            if results:
                # 按分类过滤
                if category != "all":
                    results = [r for r in results if r.get("category") == category]
                return {
                    "count": len(results),
                    "items": results[:10],
                    "search_type": "semantic",
                }
        except Exception:
            pass

        # 降级为关键词搜索
        results = await RecommendService.smart_search(self.db, self.user_id, query)
        if category != "all":
            results = [r for r in results if r.get("category") == category]

        return {
            "count": len(results),
            "items": results,
            "search_type": "keyword",
        }

    async def _exec_get_weather(self, args: dict) -> dict:
        """查询天气"""
        city = args.get("city", "北京")
        weather_text = await get_weather(city)
        return {"city": city, "weather": weather_text}

    async def _exec_recommend_outfit(self, args: dict) -> dict:
        """穿搭推荐"""
        purpose = args.get("purpose", "日常")
        city = args.get("city", "北京")
        recommendations = await RecommendService.recommend(self.db, self.user_id, purpose, city)
        return {
            "count": len(recommendations),
            "recommendations": recommendations,
        }

    async def _exec_list_closet_categories(self, args: dict) -> dict:
        """列出衣橱分类统计"""
        items = ClosetService.get_all_items(self.db, self.user_id)
        categories = {}
        for item in items:
            cat = item.get("category", "all")
            if cat not in categories:
                categories[cat] = {"count": 0, "items": []}
            categories[cat]["count"] += 1
            categories[cat]["items"].append({
                "id": item["id"],
                "name": item["name"],
                "url": item["url"],
            })

        return {
            "total_items": len(items),
            "categories": categories,
        }

    async def _exec_get_outfit_advice(self, args: dict) -> dict:
        """穿搭建议（纯知识问答，由LLM直接回答）"""
        return {
            "style": args.get("style", ""),
            "occasion": args.get("occasion", ""),
            "note": "请根据你的穿搭知识直接回答用户的问题。",
        }
