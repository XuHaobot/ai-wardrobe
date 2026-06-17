"""
FastAPI 依赖注入 - 认证相关
"""
from fastapi import Depends, HTTPException, Request
from utils.jwt_util import verify_token
from jose import JWTError


async def get_current_user_id(request: Request) -> int:
    """从 Authorization header 解析当前用户ID"""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header:
        raise HTTPException(status_code=401, detail="未提供认证令牌")

    token = auth_header
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]

    try:
        payload = verify_token(token)
        user_id = payload.get("userId")
        if user_id is None:
            raise HTTPException(status_code=401, detail="无效的令牌")
        return int(user_id)
    except JWTError:
        raise HTTPException(status_code=401, detail="令牌已过期或无效")
