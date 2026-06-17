"""
通用响应模型
"""
from typing import TypeVar, Generic, Optional
from pydantic import BaseModel

T = TypeVar("T")


class Result(BaseModel, Generic[T]):
    code: int = 1
    message: str = "success"
    data: Optional[T] = None

    @classmethod
    def success(cls, data=None, message="success"):
        return cls(code=1, message=message, data=data)

    @classmethod
    def error(cls, message="error", code=0):
        return cls(code=code, message=message)
