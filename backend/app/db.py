"""数据库连接。默认 SQLite，设置环境变量 DATABASE_URL 可切到 Postgres。

优先级：真实环境变量 > backend/.env > 代码里的默认值。
"""
import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

BASE_DIR = Path(__file__).resolve().parent.parent

# 读取 backend/.env（文件不存在就静默跳过）
load_dotenv(BASE_DIR / ".env")

DEFAULT_URL = f"sqlite:///{(BASE_DIR / 'dengdeng.db').as_posix()}"
DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_URL)

_connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=_connect_args, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
