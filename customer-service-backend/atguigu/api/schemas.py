from pydantic import BaseModel


class ChatObjectPayload(BaseModel):
    type: str
    id: str
    title: str | None = None
    attributes: dict = {}


class ChatRequest(BaseModel):
    sender_id: str
    text: str | None = None
    object: ChatObjectPayload | None = None
    message_id: str | None = None


class BotMessageResponse(BaseModel):
    text: str | None = None
    object: ChatObjectPayload | None = None


class ChatResponse(BaseModel):
    sender_id: str
    message_id: str
    messages: list[BotMessageResponse]


class ChatHistoryMessageResponse(BaseModel):
    role: str
    text: str | None = None
    object: ChatObjectPayload | None = None


class ChatHistoryResponse(BaseModel):
    sender_id: str
    messages: list[ChatHistoryMessageResponse]
