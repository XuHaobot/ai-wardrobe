"""
AI 智能衣橱 - 配置管理
"""
import os
from pathlib import Path
from pydantic_settings import BaseSettings
from functools import lru_cache

# config.py 所在目录 = backend/
_BACKEND_DIR = Path(__file__).resolve().parent
_ENV_FILE = _BACKEND_DIR / ".env"


class Settings(BaseSettings):
    # DashScope (通义千问)
    dashscope_api_key: str = ""
    # 高德天气
    amap_api_key: str = ""
    # 火山引擎 (即梦)
    volc_access_key: str = ""
    volc_secret_key: str = ""
    volc_jimeng_model: str = "jimeng_t2i_v40"
    # 腾讯云 COS
    cos_secret_id: str = ""
    cos_secret_key: str = ""
    cos_region: str = ""
    cos_bucket: str = ""
    # JWT
    jwt_secret: str = "change-me"
    jwt_expire_seconds: int = 14400
    jwt_algorithm: str = "HS256"
    # 数据库
    database_url: str = f"sqlite:///{_BACKEND_DIR / 'data' / 'outfit.db'}"
    # OSS
    aliyun_oss_endpoint: str = ""
    aliyun_oss_access_key_id: str = ""
    aliyun_oss_access_key_secret: str = ""
    aliyun_oss_bucket_name: str = "java-cjm"
    # ChromaDB
    chroma_persist_dir: str = str(_BACKEND_DIR / "data" / "chroma")
    # 通义千问模型
    qwen_vl_model: str = "qwen-vl-plus"
    qwen_text_model: str = "qwen-plus"
    qwen_embedding_model: str = "text-embedding-v3"
    # 上传目录
    upload_dir: str = str(_BACKEND_DIR / "uploads")

    class Config:
        env_file = str(_ENV_FILE)
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
