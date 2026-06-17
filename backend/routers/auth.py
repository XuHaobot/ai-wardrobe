"""
认证相关路由 - 注册/登录
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel

from database import get_db
from schemas.common import Result
from schemas.user import LoginForm, RegisterForm, LoginResponse
from services.user_service import UserService

router = APIRouter()


class RegisterRequest(BaseModel):
    username: str
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


@router.post("/users/register")
async def register(body: RegisterRequest, db: Session = Depends(get_db)):
    try:
        user = UserService.register(db, body.username, body.password)
        return Result.success({"user_id": user.id, "username": user.username})
    except ValueError as e:
        return Result.error(str(e))


@router.post("/users/login")
async def login(body: LoginRequest, db: Session = Depends(get_db)):
    try:
        result = UserService.login(db, body.username, body.password)
        return Result.success(result)
    except ValueError as e:
        return Result.error(str(e))
