"""
衣物相关Schema
"""
from typing import Optional, List
from pydantic import BaseModel


class ItemResponse(BaseModel):
    id: int
    url: str
    name: str = ""
    description: Optional[str] = None
    category: str = "all"


class ItemListResponse(BaseModel):
    count: int
    items: List[ItemResponse]


class PageQuery(BaseModel):
    page: int = 1
    size: int = 100


class ItemRename(BaseModel):
    id: int
    name: str
