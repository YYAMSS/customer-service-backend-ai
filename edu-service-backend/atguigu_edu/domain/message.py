from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class MessageType(str, Enum):
    TEXT = "text"
    OBJECT = "object"


@dataclass(slots=True)
class MessageObject:
    type: str
    id: str
    title: str | None = None
    attributes: dict = field(default_factory=dict)


@dataclass(slots=True)
class Message:
    message_id: str
    sender_id: str
    type: MessageType
    text: str | None = None
    object: MessageObject | None = None


@dataclass(slots=True)
class BotMessage:
    text: str | None = None
    object: MessageObject | None = None


@dataclass(slots=True)
class ProcessResult:
    sender_id: str
    message_id: str
    messages: list[BotMessage]

