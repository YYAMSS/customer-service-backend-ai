import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from atguigu_edu.infrastructure.database import close_db_engine, get_db_session


async def main() -> None:
    async for session in get_db_session():
        await session.close()
        break
    await close_db_engine()
    print("db_ok")


if __name__ == "__main__":
    asyncio.run(main())

