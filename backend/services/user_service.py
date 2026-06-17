"""
用户服务 - 注册/登录/认证
"""
import bcrypt
from sqlalchemy.orm import Session

from models.user import User
from utils.jwt_util import create_token


def _hash_password(password: str) -> str:
    """使用 bcrypt 哈希密码"""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _verify_password(password: str, hashed: str) -> bool:
    """验证密码"""
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


class UserService:

    @staticmethod
    def register(db: Session, username: str, password: str) -> User:
        """注册新用户"""
        existing = db.query(User).filter(User.username == username).first()
        if existing:
            raise ValueError("用户名已存在")
        hashed = _hash_password(password)
        user = User(username=username, password=hashed)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def login(db: Session, username: str, password: str) -> dict:
        """登录，返回token和用户信息"""
        user = db.query(User).filter(User.username == username).first()
        if not user or not _verify_password(password, user.password):
            raise ValueError("用户名或密码错误")
        token = create_token(user.id, user.username)
        return {
            "token": token,
            "username": user.username,
            "user_id": user.id,
        }

    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> User:
        return db.query(User).filter(User.id == user_id).first()
