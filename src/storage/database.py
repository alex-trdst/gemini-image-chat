"""
Database Configuration

SQLAlchemy Async 설정
"""

from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from src.config import get_settings


class Base(DeclarativeBase):
    """SQLAlchemy Base 클래스"""

    pass


settings = get_settings()

# SQLite URL을 async 버전으로 변환
database_url = settings.database_url
if database_url.startswith("sqlite:///"):
    # Ensure data directory exists
    db_path = database_url.replace("sqlite:///", "")
    if db_path.startswith("./"):
        db_path = db_path[2:]
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    async_database_url = database_url.replace("sqlite:///", "sqlite+aiosqlite:///")
else:
    async_database_url = database_url

# Async engine
async_engine = create_async_engine(
    async_database_url,
    echo=settings.debug,
)

# Async session
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Sync engine (for init)
sync_engine = create_engine(
    database_url,
    echo=settings.debug,
)

SyncSessionLocal = sessionmaker(bind=sync_engine)


def init_db() -> None:
    """데이터베이스 초기화 (테이블 생성)"""
    from src.storage import models  # noqa: F401

    Base.metadata.create_all(bind=sync_engine)


async def get_db():
    """데이터베이스 세션 의존성"""
    async with AsyncSessionLocal() as session:
        yield session
