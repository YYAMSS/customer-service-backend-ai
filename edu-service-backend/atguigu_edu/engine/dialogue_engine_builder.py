from atguigu_edu.engine.dialogue_engine import DialogueEngine, DialogueConfig


def build_dialogue_engine() -> DialogueEngine:
    config = DialogueConfig()
    return DialogueEngine(config=config)

