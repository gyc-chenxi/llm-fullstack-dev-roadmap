"""
数据库引擎与会话工厂
-------------------
使用 SQLModel（底层为 SQLAlchemy），为 FastAPI 提供依赖注入式的数据库会话。

架构说明：
  engine = create_engine(DATABASE_URL)   → 全局单例，管理连接池
  get_db()                              → FastAPI Depends 工厂，每个请求独立会话
  create_db_and_tables()                → 启动时建表（幂等操作）

SQLite 注意事项：
  - check_same_thread=False：允许在多线程 FastAPI 中共享同一 engine
  - SQLite 默认不支持并发写入，但本项目单用户场景不存在多写冲突
"""

from sqlmodel import create_engine, Session
from config import DATABASE_URL

# SQLite 连接引擎（全局单例）
# check_same_thread=False：SQLite 默认不允许跨线程使用，FastAPI 多线程需要此参数
# echo=False：设为 True 可打印所有 SQL 语句（调试用），生产环境关闭
engine = create_engine(
    DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False},
)


def get_db() -> Session:
    """
    FastAPI 依赖注入工厂函数。
    每个请求获得独立的数据库会话，请求结束后自动关闭并归还连接到连接池。

    使用方式：
        @app.get("/api/sessions")
        def list_sessions(db: Session = Depends(get_db)):
            ...

    原理：Session 实现了 context manager，yield 结束后 driver 自动 close()。
    """
    with Session(engine) as session:
        yield session


def create_db_and_tables():
    """
    在应用启动时调用，确保所有表已创建。
    调用 SQLModel.metadata.create_all() 自动扫描所有继承 SQLModel 且 table=True 的类，
    生成 CREATE TABLE IF NOT EXISTS 语句。如果表已存在则跳过（幂等操作，不会丢失数据）。
    """
    from sqlmodel import SQLModel
    SQLModel.metadata.create_all(engine)
