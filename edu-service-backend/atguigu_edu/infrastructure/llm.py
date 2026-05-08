"""LLM singleton for education backend, using config from atguigu_edu.conf.config."""
from __future__ import annotations

from langchain.chat_models import init_chat_model
from langchain_core.language_models import BaseChatModel

from atguigu_edu.conf.config import settings

llm: BaseChatModel = init_chat_model(
    model=settings.llm_model,
    model_provider="openai",
    api_key=settings.llm_api_key,
    base_url=settings.llm_base_url,
    temperature=0.7,
)
