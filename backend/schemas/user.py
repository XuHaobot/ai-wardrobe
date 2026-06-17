"""
用户相关Schema
"""
from pydantic import BaseModel


class LoginForm(BaseModel):
    username: str
    password: str


class RegisterForm(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    token: str
    username: str
    user_id: int
