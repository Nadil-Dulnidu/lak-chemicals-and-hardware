from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase


def get_config_value(*keys, default=None):
    """Lazy import to avoid circular dependency"""
    from app.config.config_loader import get_config_value as _get_config_value

    return _get_config_value(*keys, default=default)


DATABASE_URL = get_config_value(
    "database", "uri", default="sqlite+aiosqlite:///./test.db"
)


class Base(DeclarativeBase):
    pass


engine = create_async_engine(DATABASE_URL)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)


async def create_db_and_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session
