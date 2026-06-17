"""
数据迁移工具 - 从旧Java后端H2数据库迁移数据到新Python后端SQLite

使用方法:
    cd backend
    python migrate_data.py

说明:
    读取outfit.sql文件中的数据，导入到新的SQLite数据库
"""
import os
import sys
import re

# 确保可以导入项目模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import init_db, SessionLocal
from models.user import User
from models.item import ClosetItem
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def parse_sql_inserts(sql_file: str) -> dict:
    """解析SQL文件中的INSERT语句"""
    with open(sql_file, "r", encoding="utf-8") as f:
        content = f.read()

    data = {"users": [], "items": []}

    # 解析用户表
    user_pattern = r"INSERT INTO `user` VALUES \((\d+),\s*'([^']+)',\s*'([^']+)'\)"
    for match in re.finditer(user_pattern, content):
        data["users"].append({
            "id": int(match.group(1)),
            "username": match.group(2),
            "password": match.group(3),
        })

    # 解析closet_items表
    item_pattern = r"INSERT INTO `closet_items` VALUES \((\d+),\s*'([^']*)',\s*'((?:[^'\\]|\\.|'')*?)',\s*(\d+)\)"
    for match in re.finditer(item_pattern, content, re.DOTALL):
        item_id = int(match.group(1))
        url = match.group(2)
        description = match.group(3).replace("''", "'")
        user_id = int(match.group(4))
        data["items"].append({
            "id": item_id,
            "url": url,
            "description": description,
            "user_id": user_id,
        })

    return data


def migrate():
    """执行数据迁移"""
    sql_file = os.path.join(os.path.dirname(__file__), "..", "outfit.sql")
    if not os.path.exists(sql_file):
        print(f"[ERROR] 未找到 {sql_file}")
        return

    print("=" * 50)
    print("  AI 智能衣橱 - 数据迁移工具")
    print("=" * 50)
    print()

    # 初始化数据库
    init_db()
    print("[OK] 数据库表已创建")

    # 解析SQL
    data = parse_sql_inserts(sql_file)
    print(f"[OK] 解析到 {len(data['users'])} 个用户, {len(data['items'])} 件衣物")

    db = SessionLocal()

    try:
        # 迁移用户
        for u in data["users"]:
            existing = db.query(User).filter(User.username == u["username"]).first()
            if existing:
                print(f"  [SKIP] 用户 {u['username']} 已存在")
                continue
            user = User(
                id=u["id"],
                username=u["username"],
                password=u["password"],  # 已是bcrypt加密
            )
            db.add(user)
            print(f"  [OK] 迁移用户: {u['username']}")

        db.commit()

        # 迁移衣物
        from utils.ai_util import normalize_category, extract_name
        for item_data in data["items"]:
            existing = db.query(ClosetItem).filter(ClosetItem.id == item_data["id"]).first()
            if existing:
                print(f"  [SKIP] 衣物 #{item_data['id']} 已存在")
                continue

            desc = item_data["description"]
            category = normalize_category(desc)
            name = extract_name(desc)

            item = ClosetItem(
                id=item_data["id"],
                url=item_data["url"],
                name=name,
                description=f"category: {category}\n{desc}",
                category=category,
                user_id=item_data["user_id"],
            )
            db.add(item)

        db.commit()
        print(f"[OK] 迁移了 {len(data['items'])} 件衣物")

        # 构建向量索引
        print()
        print("[INFO] 正在构建向量搜索索引...")
        try:
            from services.vector_store import VectorStore
            vs = VectorStore()
            all_items = db.query(ClosetItem).all()
            items_list = [
                {
                    "id": item.id,
                    "description": item.description or "",
                    "name": item.name or "",
                    "category": item.category or "all",
                    "user_id": item.user_id,
                    "url": item.url,
                }
                for item in all_items
            ]
            vs.rebuild_index(items_list)
            print(f"[OK] 向量索引构建完成 ({len(items_list)} 件)")
        except Exception as e:
            print(f"[WARN] 向量索引构建跳过: {e}")
            print("  (可稍后通过 POST /closet/rebuild-index 重建)")

        print()
        print("=" * 50)
        print("  迁移完成! 可以启动后端了:")
        print("  python -m uvicorn main:app --port 8080 --reload")
        print("=" * 50)

    finally:
        db.close()


if __name__ == "__main__":
    migrate()
