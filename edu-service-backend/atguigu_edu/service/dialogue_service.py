from atguigu_edu.domain.message import Message, ProcessResult
from atguigu_edu.engine.dialogue_engine import DialogueEngine
from atguigu_edu.repository.dialogue_repository import DialogueStateRepository


class DialogueService:
    def __init__(
        self,
        *,
        dialogue_state_repository: DialogueStateRepository,
        dialogue_engine: DialogueEngine,
    ) -> None:
        self.dialogue_state_repository = dialogue_state_repository
        self.dialogue_engine = dialogue_engine

    async def handle_message(self, message: Message) -> ProcessResult:
        state = await self.dialogue_state_repository.load(message.sender_id)
        result = await self.dialogue_engine.process(message, state)
        await self.dialogue_state_repository.save(state)
        return result

