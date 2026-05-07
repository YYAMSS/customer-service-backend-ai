from typing import Any

from atguigu.task.actions.base import Action, ActionResult
from atguigu.domain.state import DialogueState


class ActionListen(Action):
    """The assistant waits for the next user message."""

    name = "action_listen"

    async def run(self, state: DialogueState, **kwargs: Any) -> ActionResult:
        return ActionResult()
