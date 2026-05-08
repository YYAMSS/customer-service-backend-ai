from contextlib import asynccontextmanager

from fastapi import FastAPI

from atguigu_edu.api.dependencies import init_engine
from atguigu_edu.api.routers import router
from atguigu_edu.engine.dialogue_engine_builder import build_dialogue_engine
from atguigu_edu.infrastructure.database import _create_tables, close_db_engine, init_db_engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_engine(build_dialogue_engine())
    init_db_engine()
    await _create_tables()
    yield
    await close_db_engine()


app = FastAPI(lifespan=lifespan, debug=True)
app.include_router(router)

