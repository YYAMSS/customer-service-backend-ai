from pathlib import Path

from atguigu.engine.dialogue_engine import DialogueEngine, DialogueConfig
from atguigu.planning.clarify import ClarifyResponder
from atguigu.planning.validator import TurnPlanValidator
from atguigu.task.actions.builder import build_action_runner
from atguigu.task.commands.processor import CommandProcessor
from atguigu.task.flow.executor import FlowExecutor
from atguigu.task.flow.loader import FlowLoader
from atguigu.task.handler import TaskHandler
from atguigu.infrastructure.llm import llm
from atguigu.chitchat.handler import ChitchatHandler
from atguigu.chitchat.responder import ChitchatResponder
from atguigu.knowledge.handler import KnowledgeHandler
from atguigu.knowledge.intents import KNOWLEDGE_INTENTS
from atguigu.knowledge.planner import KnowledgePlanner
from atguigu.knowledge.provider import (
    FaqKnowledgeProvider,
    OrderApiProvider,
    ProductApiProvider,
    RagKnowledgeProvider,
)
from atguigu.knowledge.responder import KnowledgeResponder
from atguigu.planning.planner import TurnPlanner

_PROJECT_ROOT = Path(__file__).parents[2]
_FLOW_CONFIG_DIR = _PROJECT_ROOT / "flow_config"
_FLOW_CONFIG_FILES = ("user_flows.yml", "system_flows.yml")


def build_dialogue_engine() -> DialogueEngine:
    config = DialogueConfig()
    flow_paths = [_FLOW_CONFIG_DIR / f for f in _FLOW_CONFIG_FILES]
    flows = FlowLoader().load_many(flow_paths)
    return DialogueEngine(
        flows=flows,
        knowledge_intents=KNOWLEDGE_INTENTS,
        turn_planner=TurnPlanner(llm=llm),
        task_handler=TaskHandler(
            flows=flows,
            command_processor=CommandProcessor(),
            flow_executor=FlowExecutor(),
            action_runner=build_action_runner(llm=llm, include_custom_actions=True),
            max_steps=config.max_flow_steps,
        ),
        knowledge_handler=KnowledgeHandler(
            responder=KnowledgeResponder(llm=llm),
            providers=[
                ProductApiProvider(),
                OrderApiProvider(),
                FaqKnowledgeProvider(),
                RagKnowledgeProvider(),
            ],
            planner=KnowledgePlanner(intents=KNOWLEDGE_INTENTS),
        ),
        chitchat_handler=ChitchatHandler(
            responder=ChitchatResponder(llm=llm),
        ),
        clarify_responder=ClarifyResponder(llm=llm),
        turn_plan_validator=TurnPlanValidator(),
        config=config,
    )
