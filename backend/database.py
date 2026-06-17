"""
AI 智能衣橱 - 数据库初始化
支持 MySQL (腾讯云 CynosDB) 和 SQLite
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from config import get_settings

settings = get_settings()

connect_args = {}
pool_kwargs = {}

if settings.database_url.startswith("sqlite"):
    connect_args["check_same_thread"] = False
else:
    # MySQL: 连接池配置，处理断连
    pool_kwargs["pool_pre_ping"] = True
    pool_kwargs["pool_recycle"] = 3600
    pool_kwargs["pool_size"] = 5
    pool_kwargs["max_overflow"] = 10

engine = create_engine(
    settings.database_url,
    connect_args=connect_args,
    echo=False,
    **pool_kwargs,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    """FastAPI 依赖注入：获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """初始化数据库表结构（带重试，应对云数据库临时断连）"""
    import time
    for attempt in range(3):
        try:
            Base.metadata.create_all(bind=engine)
            return
        except Exception as e:
            if attempt < 2:
                wait = (attempt + 1) * 2
                print(f"[WARN] 数据库连接失败({e.__class__.__name__})，{wait}秒后重试...")
                time.sleep(wait)
            else:
                raise
