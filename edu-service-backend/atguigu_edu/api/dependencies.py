from __future__ import annotations

from typing import Annotated

from fastapi import Depends

from atguigu_edu.engine.dialogue_engine import DialogueEngine
from atguigu_edu.infrastructure.database import get_db_session
from atguigu_edu.repository.dialogue_repository import DialogueStateRepository
from atguigu_edu.service.dialogue_service import DialogueService

_engine: DialogueEngine | None = None


def init_engine(engine: DialogueEngine) -> None:
    global _engine
    _engine = engine


def get_engine() -> DialogueEngine:
    if _engine is None:
        raise RuntimeError("Dialogue engine not initialized. Call init_engine() at startup.")
    return _engine


def get_dialogue_state_repository(
    session=Depends(get_db_session),
) -> DialogueStateRepository:
    return DialogueStateRepository(session=session)


def get_dialogue_service(
    engine: Annotated[DialogueEngine, Depends(get_engine)],
    repo: Annotated[DialogueStateRepository, Depends(get_dialogue_state_repository)],
) -> DialogueService:
    return DialogueService(dialogue_state_repository=repo, dialogue_engine=engine)

