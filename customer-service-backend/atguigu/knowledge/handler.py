from __future__ import annotations

from atguigu.domain.message import BotMessage, Message
from atguigu.domain.state import DialogueState
from atguigu.knowledge.context_builder import KnowledgeContextBuilder
from atguigu.knowledge.planner import KnowledgePlanner
from atguigu.knowledge.provider import KnowledgeProvider, KnowledgeProviderRegistry
from atguigu.knowledge.responder import KnowledgeResponder


class KnowledgeHandler:
    def __init__(
        self,
        *,
        responder: KnowledgeResponder,
        providers: list[KnowledgeProvider],
        context_builder: KnowledgeContextBuilder | None = None,
        planner: KnowledgePlanner | None = None,
    ) -> None:
        self.responder = responder
        self.registry = KnowledgeProviderRegistry(providers)
        self.context_builder = context_builder or KnowledgeContextBuilder()
        self.planner = planner or KnowledgePlanner()

    async def handle(
        self,
        *,
        message: Message,
        state: DialogueState,
        intent: str | None = None,
    ) -> list[BotMessage]:
        context = self.context_builder.build(message, state, intent=intent)
        plan = self.planner.plan(context)
        chunks = []
        for provider_id in plan.provider_ids:
            provider = self.registry.get(provider_id)
            if provider is not None:
                chunks.extend(await provider.retrieve(context.user_message, context))
        return await self.responder.respond(context, chunks)
