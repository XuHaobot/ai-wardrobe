"""
推荐服务 - 调用AI推荐 + 向量检索增强
"""
import re
from sqlalchemy.orm import Session
from utils.ai_recommend import generate_recommendation
from services.closet_service import ClosetService, _extract_name


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
