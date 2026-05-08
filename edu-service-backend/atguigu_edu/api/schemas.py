from __future__ import annotations

from pydantic import BaseModel, Field, model_validator


class ChatObjectPayload(BaseModel):
    type: str
    id: str
    title: str | None = None
    attributes: dict = Field(default_factory=dict)

    @model_validator(mode="after")
    def _validate_required_fields(self) -> "ChatObjectPayload":
        if not str(self.type or "").strip():
            raise ValueError("object.type must not be empty")
        if not str(self.id or "").strip():
            raise ValueError("object.id must not be empty")
        return self


class ChatRequest(BaseModel):
    sender_id: str
    text: str | None = None
    object: ChatObjectPayload | None = None
    message_id: str | None = None

    @model_validator(mode="after")
    def _validate_payload(self) -> "ChatRequest":
        if not str(self.sender_id or "").strip():
            raise ValueError("sender_id must not be empty")
        has_text = bool(str(self.text or "").strip())
        has_object = self.object is not None
        if not (has_text or has_object):
            raise ValueError("text and object must have at least one")
        return self


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


class SessionStateResponse(BaseModel):
    sender_id: str
    active_flow: str | None = None
    flow_step: str | None = None
    flow_slots: dict[str, str] = Field(default_factory=dict)
    suspended_flow: dict | None = None
    focused_object: ChatObjectPayload | None = None

