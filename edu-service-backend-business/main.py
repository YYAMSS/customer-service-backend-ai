#!/usr/bin/env python3
"""
Education 业务服务启动脚本
"""
from __future__ import annotations

import uvicorn

from app.config import settings


def main() -> None:
    # Avoid emoji in Windows consoles with GBK encoding.
    print("Starting Education business service...")
    print(f"Address: http://{settings.app_host}:{settings.app_port}")
    print(f"Docs: http://{settings.app_host}:{settings.app_port}/docs")
    uvicorn.run(
        "app.app:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=True,
        log_level="info",
    )


if __name__ == "__main__":
    main()

