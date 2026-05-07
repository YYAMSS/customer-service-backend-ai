import asyncio
import sys
from pathlib import Path

from sqlalchemy import text

sys.path.append(str(Path(__file__).resolve().parents[1]))

from atguigu_edu.infrastructure.database import close_db_engine, get_db_session


async def main() -> None:
    async for session in get_db_session():
        result = await session.execute(text("SHOW TABLES LIKE 'dialogue_state'"))
        print("table_exists_rows:", result.all())
        break
    await close_db_engine()


if __name__ == "__main__":
    asyncio.run(main())

