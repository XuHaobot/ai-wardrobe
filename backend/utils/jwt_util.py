"""
JWT 工具 - 令牌创建与验证
"""
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from config import get_settings


def create_token(user_id: int, username: str) -> str:
    """生成 JWT token"""
    settings = get_settings()
    payload = {
        "userId": user_id,
        "username": username,
        "exp": datetime.now(timezone.utc) + timedelta(seconds=settings.jwt_expire_seconds),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def verify_token(token: str) -> dict:
    """验证 JWT token，返回 payload。失败时抛出 JWTError"""
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        return payload
    except JWTError:
        raise
