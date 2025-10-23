"""Simple deterministic LLM stub used by the external runner example."""
from typing import Any

from typing_extensions import override

from openevolve.llm.base import LLMInterface


class DummyLLM(LLMInterface):
    """Very small synchronous LLM replacement.

    The implementation alternates between two canned rewrites so the evolution
    loop can observe "changes" without depending on a real LLM provider.
    """

    def __init__(self):
        pass

    @override
    async def generate(self, prompt: str, **__: Any) -> str:
        raise NotImplementedError("DummyLLM has no implementation for generate.")

    @override
    async def generate_with_context(
        self,
        system_message: str,
        messages: list[dict[str, str]],
        **__: Any,
    ) -> str:
        raise NotImplementedError("DummyLLM has no implementation for generate_with_context.")


def create_dummy_llm(_) -> DummyLLM:
    """Factory used from configuration files."""

    return DummyLLM()
