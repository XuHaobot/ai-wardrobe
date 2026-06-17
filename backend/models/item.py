"""
衣橱物品模型
"""
from datetime import datetime
from sqlalchemy import Column, Integer, BigInteger, String, Text, DateTime
from database import Base


class ClosetItem(Base):
    __tablename__ = "closet_items"
    __table_args__ = {"mysql_charset": "utf8mb4", "mysql_collate": "utf8mb4_unicode_ci"}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False, index=True)
    url = Column(String(500), nullable=False, comment="图片URL或本地路径")
    category = Column(String(50), default="all", index=True, comment="衣物分类")
    description = Column(Text, nullable=True, comment="AI识别的衣物描述")
    color = Column(String(50), nullable=True, comment="颜色")
    season = Column(String(20), nullable=True, comment="适用季节")
    thickness = Column(String(20), nullable=True, comment="厚度")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
