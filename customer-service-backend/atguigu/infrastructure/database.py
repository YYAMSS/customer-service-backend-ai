import asyncio

from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession, create_async_engine, AsyncEngine

from atguigu.conf.config import settings

engine: AsyncEngine | None = None
session_factory: async_sessionmaker[AsyncSession] | None = None


def init_db_engine() -> None:
    global engine, session_factory
    engine = create_async_engine(settings.database_url, echo=False, pool_pre_ping=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)


async def close_db_engine():
    if engine is not None:
        await engine.dispose()


if __name__ == '__main__':
    init_db_engine()


    async def test():
        async with session_factory() as session:
            result = await session.execute(text("select 1"))
            print(result.fetchone())

        await close_db_engine()


    asyncio.run(test())
