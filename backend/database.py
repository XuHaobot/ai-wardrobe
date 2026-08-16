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


def _ensure_columns():
    """为已存在表补充模型新增的列（兼容 SQLite / MySQL，避免删数据重建）"""
    try:
        from sqlalchemy import inspect, text
        inspector = inspect(engine)
        if not inspector.has_table("closet_items"):
            return
        columns = [c["name"] for c in inspector.get_columns("closet_items")]
        # 模型相对数据库新增的列 -> ALTER TABLE 补齐
        expected = {
            "style": "VARCHAR(200)",
        }
        for col, col_type in expected.items():
            if col not in columns:
                with engine.connect() as conn:
                    conn.execute(text(f"ALTER TABLE closet_items ADD COLUMN {col} {col_type}"))
                    conn.commit()
                    print(f"[DB] 已为 closet_items 新增 {col} 列")
    except Exception as e:
        print(f"[WARN] 列迁移失败: {e}")


def init_db():
    """初始化数据库表结构（带重试，应对云数据库临时断连）"""
    import time
    for attempt in range(3):
        try:
            Base.metadata.create_all(bind=engine)
            _ensure_columns()
            return
        except Exception as e:
            if attempt < 2:
                wait = (attempt + 1) * 2
                print(f"[WARN] 数据库连接失败({e.__class__.__name__})，{wait}秒后重试...")
                time.sleep(wait)
            else:
                raise
