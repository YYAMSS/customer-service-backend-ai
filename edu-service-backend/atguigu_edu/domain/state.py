from __future__ import annotations

import time
from dataclasses import dataclass, field

from atguigu_edu.domain.message import BotMessage, Message, MessageObject


@dataclass(slots=True)
class Turn:
    input_message: Message
    assistant_messages: list[BotMessage] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "input_message": _message_to_dict(self.input_message),
            "assistant_messages": [_bot_message_to_dict(m) for m in self.assistant_messages],
        }

    @staticmethod
    def from_dict(payload: dict) -> "Turn":
        return Turn(
            input_message=_message_from_dict(payload.get("input_message") or {}),
            assistant_messages=[_bot_message_from_dict(m) for m in (payload.get("assistant_messages") or [])],
        )


@dataclass(slots=True)
class Session:
    session_id: str
    created_at: float
    last_activity_at: float
    closed_at: float | None = None
    turns: list[Turn] = field(default_factory=list)

    def is_closed(self) -> bool:
        return self.closed_at is not None

    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "created_at": self.created_at,
            "last_activity_at": self.last_activity_at,
            "closed_at": self.closed_at,
            "turns": [t.to_dict() for t in self.turns],
        }

    @staticmethod
    def from_dict(payload: dict) -> "Session":
        return Session(
            session_id=str(payload.get("session_id") or ""),
            created_at=float(payload.get("created_at") or 0.0),
            last_activity_at=float(payload.get("last_activity_at") or 0.0),
            closed_at=payload.get("closed_at"),
            turns=[Turn.from_dict(t) for t in (payload.get("turns") or [])],
        )


@dataclass(slots=True)
class DialogueState:
    sender_id: str
    sessions: list[Session] = field(default_factory=list)
    focused_object: MessageObject | None = None

    def current_session(self) -> Session | None:
        for session in reversed(self.sessions):
            if not session.is_closed():
                return session
        return None

    def start_session(self) -> Session:
        now = time.time()
        session = Session(
            session_id=f"s_{int(now * 1000)}",
            created_at=now,
            last_activity_at=now,
        )
        self.sessions.append(session)
        return session

    def append_turn(self, turn: Turn) -> None:
        session = self.current_session() or self.start_session()
        session.turns.append(turn)
        session.last_activity_at = time.time()

    def set_focused_object(self, obj: MessageObject | None) -> None:
        self.focused_object = obj

    def to_dict(self) -> dict:
        return {
            "sender_id": self.sender_id,
            "focused_object": _object_to_dict(self.focused_object),
            "sessions": [s.to_dict() for s in self.sessions],
        }

    @staticmethod
    def from_dict(payload: dict) -> "DialogueState":
        return DialogueState(
            sender_id=str(payload.get("sender_id") or ""),
            focused_object=_object_from_dict(payload.get("focused_object")),
            sessions=[Session.from_dict(s) for s in (payload.get("sessions") or [])],
        )


def _object_to_dict(obj: MessageObject | None) -> dict | None:
    if obj is None:
        return None
    return {
        "type": obj.type,
        "id": obj.id,
        "title": obj.title,
        "attributes": dict(obj.attributes or {}),
    }


def _object_from_dict(payload: dict | None) -> MessageObject | None:
    if not isinstance(payload, dict):
        return None
    return MessageObject(
        type=str(payload.get("type") or ""),
        id=str(payload.get("id") or ""),
        title=None if payload.get("title") is None else str(payload.get("title")),
        attributes=dict(payload.get("attributes") or {}),
    )


def _message_to_dict(message: Message) -> dict:
    return {
        "message_id": message.message_id,
        "sender_id": message.sender_id,
        "type": message.type.value,
        "text": message.text,
        "object": _object_to_dict(message.object),
    }


def _message_from_dict(payload: dict) -> Message:
    msg_type = str(payload.get("type") or "text")
    from atguigu_edu.domain.message import MessageType  # local import to avoid cycles

    try:
        t = MessageType(msg_type)
    except Exception:
        t = MessageType.TEXT
    return Message(
        message_id=str(payload.get("message_id") or ""),
        sender_id=str(payload.get("sender_id") or ""),
        type=t,
        text=payload.get("text"),
        object=_object_from_dict(payload.get("object")),
    )


def _bot_message_to_dict(message: BotMessage) -> dict:
    return {
        "text": message.text,
        "object": _object_to_dict(message.object),
    }


def _bot_message_from_dict(payload: dict) -> BotMessage:
    if not isinstance(payload, dict):
        return BotMessage(text=None, object=None)
    return BotMessage(
        text=payload.get("text"),
        object=_object_from_dict(payload.get("object")),
    )

