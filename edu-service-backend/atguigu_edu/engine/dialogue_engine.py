from __future__ import annotations

from dataclasses import dataclass

from atguigu_edu.domain.message import BotMessage, Message, MessageType, ProcessResult
from atguigu_edu.domain.state import DialogueState, Turn


@dataclass(slots=True)
class DialogueConfig:
    session_timeout_seconds: float = 60.0 * 60.0


class DialogueEngine:
    """
    教育版：最小可运行对话引擎（无 I/O）。

    - 输入：Message + DialogueState
    - 输出：ProcessResult
    - 直接更新 state（由 service 负责持久化）
    """

    def __init__(self, *, config: DialogueConfig | None = None) -> None:
        self.config = config or DialogueConfig()

    async def process(self, message: Message, state: DialogueState) -> ProcessResult:
        if message.type is MessageType.OBJECT:
            state.set_focused_object(message.object)

        turn = Turn(input_message=message)
        turn.assistant_messages.extend(self._respond(message, state))
        state.append_turn(turn)
        return ProcessResult(
            sender_id=message.sender_id,
            message_id=message.message_id,
            messages=list(turn.assistant_messages),
        )

    @staticmethod
    def _respond(message: Message, state: DialogueState) -> list[BotMessage]:
        if message.type is MessageType.OBJECT and message.object is not None:
            obj = message.object
            return [
                BotMessage(
                    text=f"我已收到你发送的对象：{obj.type}（ID：{obj.id}）。你想查询课程、订单、学习进度，还是要申请退款/提交工单？",
                    object=None,
                )
            ]

        user_text = (message.text or "").strip()
        if not user_text:
            return [
                BotMessage(text="我收到啦。你可以告诉我想咨询课程、查询订单/学习进度，或申请退款/提交工单。")
            ]

        return [
            BotMessage(
                text=(
                    "我理解你的问题了。为了更好地帮你处理：\n"
                    "- 课程咨询：告诉我课程名称/方向\n"
                    "- 订单查询：提供订单号\n"
                    "- 学习进度：提供班次名称/期数\n"
                    "- 退款/工单：说明订单号与问题描述\n"
                    f"\n你刚才说的是：{user_text}"
                )
            )
        ]

