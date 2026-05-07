from __future__ import annotations

from collections.abc import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from atguigu_edu.conf.config import settings
from atguigu_edu.models.base import Base
from atguigu_edu.models import dialogue_state as _dialogue_state_model  # noqa: F401

_engine: AsyncEngine | None = None
_sessionmaker: async_sessionmaker[AsyncSession] | None = None


def init_db_engine() -> None:
    global _engine, _sessionmaker
    if _engine is not None:
        return
    _engine = create_async_engine(settings.database_url, future=True)
    _sessionmaker = async_sessionmaker(_engine, expire_on_commit=False)


async def _create_tables() -> None:
    if _engine is None:
        raise RuntimeError("DB engine not initialized")
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db_engine() -> None:
    global _engine, _sessionmaker
    if _engine is None:
        return
    await _engine.dispose()
    _engine = None
    _sessionmaker = None


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    if _engine is None or _sessionmaker is None:
        init_db_engine()
        await _create_tables()
    assert _sessionmaker is not None
    async with _sessionmaker() as session:
        yield session

