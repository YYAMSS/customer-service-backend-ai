import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from atguigu_edu.conf.config import settings
from atguigu_edu.infrastructure.business_client import BusinessServiceClient


async def main() -> None:
    client = BusinessServiceClient(base_url=settings.business_base_url, timeout_s=3.0)
    try:
        data = await client.health()
    finally:
        await client.aclose()
    print("business_ok")
    print(data)


if __name__ == "__main__":
    asyncio.run(main())

