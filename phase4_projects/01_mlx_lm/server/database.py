"""
数据库引擎与会话工厂
-------------------
使用 SQLModel（底层是 SQLAlchemy），为 FastAPI 提供依赖注入式的数据库会话。
"""

from sqlmodel import create_engine, Session
from config import DATABASE_URL

# SQLite 需要 check_same_thread=False 才能在多线程环境下正常工作
# echo=False 关闭 SQL 日志（调试时可设为 True）
engine = create_engine(
    DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False},
)


def get_db() -> Session:
    """
    FastAPI 依赖注入工厂函数。
    每个请求获得独立的数据库会话，请求结束后自动关闭。

    使用方式：
        @app.get("/api/sessions")
        def list_sessions(db: Session = Depends(get_db)):
            ...
    """
    with Session(engine) as session:
        yield session


def create_db_and_tables():
    """
    在应用启动时调用，确保所有表已创建。
    使用 SQLModel.metadata.create_all 自动建表，
    如果表已存在则跳过（不会丢失数据）。
    """
    # 延迟导入避免循环依赖
    from sqlmodel import SQLModel
    SQLModel.metadata.create_all(engine)
