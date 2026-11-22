"""LLM client abstractions, OpenAI-compatible client, and built-in offline demo engine."""

from inkforge.config import LLMConfig
from inkforge.llm.base import LLMClient, LLMError, extract_json
from inkforge.llm.demo_provider import DemoLLMClient
from inkforge.llm.openai_compat import OpenAICompatClient


def create_llm_client(config: LLMConfig) -> LLMClient:
    resolved = config.resolved()
    if resolved.provider == "demo":
        return DemoLLMClient()
    return OpenAICompatClient(resolved)


__all__ = [
    "LLMClient",
    "LLMError",
    "DemoLLMClient",
    "OpenAICompatClient",
    "create_llm_client",
    "extract_json",
]
