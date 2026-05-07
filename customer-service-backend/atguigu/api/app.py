from contextlib import asynccontextmanager

from fastapi import FastAPI

from atguigu.api.dependencies import init_engine
from atguigu.api.routers import router
from atguigu.engine.dialogue_engine_builder import build_dialogue_engine
from atguigu.infrastructure.database import init_db_engine, close_db_engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_engine(build_dialogue_engine())
    init_db_engine()
    yield
    await close_db_engine()


app = FastAPI(lifespan=lifespan)
app.include_router(router)
