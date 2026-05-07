import uvicorn

from atguigu_edu.conf.config import settings


def main() -> None:
    uvicorn.run(
        "atguigu_edu.api.app:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=True,
        log_level="debug",
    )


if __name__ == "__main__":
    main()

