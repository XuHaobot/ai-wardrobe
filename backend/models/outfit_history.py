"""
搭配历史模型 - 记录用户保存的穿搭方案（日常/旅行）
"""
from datetime import datetime
from sqlalchemy import Column, Integer, BigInteger, String, Text, DateTime

from database import Base


class OutfitHistory(Base):
    __tablename__ = "outfit_history"
    __table_args__ = {"mysql_charset": "utf8mb4", "mysql_collate": "utf8mb4_unicode_ci"}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False, index=True)
    title = Column(String(200), nullable=False, comment="搭配标题")
    # 衣物清单 JSON: [{"url":..., "name":...}, ...]
    items_json = Column(Text, nullable=False, default="[]")
    reason = Column(Text, nullable=True, comment="推荐理由")
    weather = Column(String(100), nullable=True, comment="适宜天气")
    purpose = Column(String(200), nullable=True, comment="出行目的/场景")
    scene_type = Column(String(20), default="daily", comment="daily / travel")
    created_at = Column(DateTime, default=datetime.now)
