from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter, Depends

from atguigu_edu.api.dependencies import get_dialogue_service, get_dialogue_state_repository
from atguigu_edu.api.schemas import (
    BotMessageResponse,
    ChatHistoryMessageResponse,
    ChatHistoryResponse,
    ChatObjectPayload,
    ChatRequest,
    ChatResponse,
)
from atguigu_edu.domain.message import BotMessage, Message, MessageObject, MessageType, ProcessResult
from atguigu_edu.repository.dialogue_repository import DialogueStateRepository
from atguigu_edu.service.dialogue_service import DialogueService

router = APIRouter()


@router.post("/api/chat", response_model=ChatResponse)
async def chat(
    chat_request: ChatRequest,
    dialogue_service: DialogueService = Depends(get_dialogue_service),
) -> ChatResponse:
    message: Message = _build_message(chat_request)
    process_result = await dialogue_service.handle_message(message)
    return _build_response(process_result)


@router.get("/api/chat/history", response_model=ChatHistoryResponse)
async def chat_history(
    sender_id: str,
    dialogue_state_repository: DialogueStateRepository = Depends(get_dialogue_state_repository),
) -> ChatHistoryResponse:
    state = await dialogue_state_repository.load(sender_id)
    messages: list[ChatHistoryMessageResponse] = []
    active_session = state.current_session()
    closed_sessions = [session for session in state.sessions if session is not active_session]
    for session in closed_sessions:
        for turn in session.turns:
            messages.append(_build_history_user_message(turn.input_message))
            messages.extend(_build_history_bot_message(message) for message in turn.assistant_messages)
    if active_session is not None:
        for turn in active_session.turns:
            messages.append(_build_history_user_message(turn.input_message))
            messages.extend(_build_history_bot_message(message) for message in turn.assistant_messages)
    return ChatHistoryResponse(sender_id=sender_id, messages=messages)


def _build_message(chat_request: ChatRequest) -> Message:
    message_id = chat_request.message_id or str(uuid4())
    if chat_request.object:
        return Message(
            message_id=message_id,
            sender_id=chat_request.sender_id,
            type=MessageType.OBJECT,
            object=MessageObject(
                type=chat_request.object.type,
                id=chat_request.object.id,
                title=chat_request.object.title,
                attributes=chat_request.object.attributes,
            ),
        )
    return Message(
        message_id=message_id,
        sender_id=chat_request.sender_id,
        type=MessageType.TEXT,
        text=chat_request.text,
    )


def _build_response(process_result: ProcessResult) -> ChatResponse:
    return ChatResponse(
        sender_id=process_result.sender_id,
        message_id=process_result.message_id,
        messages=[
            BotMessageResponse(text=message.text, object=_build_object(message.object))
            for message in process_result.messages
        ],
    )


def _build_object(message: MessageObject | None) -> ChatObjectPayload | None:
    if message is None:
        return None
    return ChatObjectPayload(
        type=message.type,
        id=message.id,
        title=message.title,
        attributes=message.attributes,
    )


def _build_history_user_message(message: Message) -> ChatHistoryMessageResponse:
    return ChatHistoryMessageResponse(
        role="user",
        text=message.text,
        object=_build_object(message.object),
    )


def _build_history_bot_message(message: BotMessage) -> ChatHistoryMessageResponse:
    return ChatHistoryMessageResponse(
        role="bot",
        text=message.text,
        object=_build_object(message.object),
    )

