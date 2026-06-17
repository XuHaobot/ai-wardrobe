"""
向量语义搜索服务 - DashScope Embedding + ChromaDB
"""
import os
from typing import Optional
import httpx
import chromadb
from config import get_settings


class VectorStore:
    """衣橱向量语义搜索引擎"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        settings = get_settings()
        os.makedirs(settings.chroma_persist_dir, exist_ok=True)
        self.client = chromadb.PersistentClient(path=settings.chroma_persist_dir)
        self.collection = self.client.get_or_create_collection(
            name="closet_items",
            metadata={"hnsw:space": "cosine"},
        )
        self._initialized = True

    def _get_embeddings(self, texts: list[str]) -> list[list[float]]:
        """调用 DashScope text-embedding API"""
        settings = get_settings()
        # 使用同步调用（ChromaDB内部调用）
        import dashscope
        dashscope.api_key = settings.dashscope_api_key

        resp = dashscope.TextEmbedding.call(
            model=settings.qwen_embedding_model,
            input=texts,
        )
        if resp.status_code != 200:
            raise RuntimeError(f"Embedding API error: {resp.message}")

        embeddings = []
        for item in resp.output["embeddings"]:
            embeddings.append(item["embedding"])
        return embeddings

    def upsert_item(self, item_id: int, text: str, metadata: dict):
        """将衣物描述向量化并存入 ChromaDB"""
        if not text or not text.strip():
            return
        # 截取前500字避免超长
        text = text[:500]
        embedding = self._get_embeddings([text])[0]
        self.collection.upsert(
            ids=[f"item_{item_id}"],
            documents=[text],
            embeddings=[embedding],
            metadatas=[{**metadata, "item_id": item_id}],
        )

    def semantic_search(self, query: str, user_id: int, top_k: int = 5) -> list[dict]:
        """语义相似度搜索"""
        query_embedding = self._get_embeddings([query])[0]
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k * 2,  # 多取一些用于后过滤
            where={"user_id": user_id},
        )

        items = []
        if results and results["ids"] and results["ids"][0]:
            for i, doc_id in enumerate(results["ids"][0]):
                meta = results["metadatas"][0][i] if results["metadatas"] else {}
                distance = results["distances"][0][i] if results["distances"] else 0
                items.append({
                    "id": meta.get("item_id"),
                    "url": meta.get("url", ""),
                    "name": meta.get("name", ""),
                    "category": meta.get("category", "all"),
                    "score": 1 - distance,  # cosine distance → similarity
                    "document": results["documents"][0][i] if results["documents"] else "",
                })

        return items[:top_k]

    def delete_item(self, item_id: int):
        """从向量库删除衣物"""
        try:
            self.collection.delete(ids=[f"item_{item_id}"])
        except Exception:
            pass

    def rebuild_index(self, items: list[dict]):
        """重建整个索引（批量导入）"""
        if not items:
            return
        texts = []
        ids = []
        metadatas = []
        for item in items:
            desc = item.get("description", "")
            if desc:
                texts.append(desc[:500])
                ids.append(f"item_{item['id']}")
                metadatas.append({
                    "item_id": item["id"],
                    "name": item.get("name", ""),
                    "category": item.get("category", "all"),
                    "user_id": item.get("user_id", 0),
                    "url": item.get("url", ""),
                })

        if texts:
            # 分批处理，每批最多10条（DashScope限制）
            batch_size = 10
            for i in range(0, len(texts), batch_size):
                batch_texts = texts[i:i + batch_size]
                batch_ids = ids[i:i + batch_size]
                batch_metas = metadatas[i:i + batch_size]
                embeddings = self._get_embeddings(batch_texts)
                self.collection.upsert(
                    ids=batch_ids,
                    documents=batch_texts,
                    embeddings=embeddings,
                    metadatas=batch_metas,
                )
