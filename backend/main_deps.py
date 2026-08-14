"""
FastAPI 依赖注入 - 认证相关
"""
from fastapi import Depends, HTTPException, Request
from utils.jwt_util import verify_token
from jose import JWTError
from config import get_settings


class GuestContext:
    """游客上下文：真实用户或演示游客"""

    def __init__(self, user_id: int, is_guest: bool):
        self.user_id = user_id
        self.is_guest = is_guest


async def get_current_user_id(request: Request) -> int:
    """从 Authorization header 解析当前用户ID（必须登录，游客会被拒绝）"""
    return (await get_guest_context(request)).user_id


async def get_guest_context(request: Request) -> GuestContext:
    """
    解析当前身份：
    - 有效 JWT -> 真实用户（is_guest=False）
    - 带 X-Guest: 1 且开启游客模式 -> 演示用户（is_guest=True）
    - 否则 -> 401
    """
    settings = get_settings()
    auth_header = request.headers.get("Authorization", "")

    # 1. 优先解析真实 JWT
    if auth_header:
        token = auth_header[7:] if auth_header.startswith("Bearer ") else auth_header
        try:
            payload = verify_token(token)
            user_id = payload.get("userId")
            if user_id is not None:
                return GuestContext(int(user_id), is_guest=False)
        except JWTError:
            pass  # 落到游客分支

    # 2. 游客试玩模式
    if settings.allow_guest_mode and request.headers.get("X-Guest", "").strip() == "1":
        return GuestContext(settings.demo_user_id, is_guest=True)

    # 3. 未授权
    raise HTTPException(status_code=401, detail="未提供认证令牌")


async def require_real_user(request: Request) -> int:
    """写操作依赖：游客或游客头会被拒绝（403），必须真实登录用户"""
    ctx = await get_guest_context(request)
    if ctx.is_guest:
        raise HTTPException(status_code=403, detail="游客模式不可修改数据，请登录后操作")
    return ctx.user_id

