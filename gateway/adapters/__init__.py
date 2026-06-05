from adapters.base import BaseAdapter
from adapters.openai import OpenAIAdapter
from adapters.openai_compat import (
    DeepSeekAdapter, QwenAdapter, ZhipuAdapter, MoonshotAdapter,
    DoubaoAdapter, MinimaxAdapter, KlingAdapter,
)
from adapters.anthropic import AnthropicAdapter, GoogleAdapter

ADAPTER_CLASSES = [
    OpenAIAdapter, DeepSeekAdapter, QwenAdapter,
    AnthropicAdapter, GoogleAdapter,
    ZhipuAdapter, MoonshotAdapter, DoubaoAdapter,
    MinimaxAdapter, KlingAdapter,
]


def create_adapters(supplier_configs: dict[str, dict]) -> list[BaseAdapter]:
    adapters = []
    for name, config in supplier_configs.items():
        for cls in ADAPTER_CLASSES:
            if cls.provider_name == name:
                adapters.append(cls(
                    api_key=config["api_key"],
                    base_url=config["base_url"],
                ))
    return adapters


def find_adapter(model: str, adapters: list[BaseAdapter]) -> BaseAdapter | None:
    for adapter in adapters:
        if adapter.matches(model):
            return adapter
    return None
