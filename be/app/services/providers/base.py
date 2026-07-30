from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass
class ProviderResult:
    text: str
    provider: str
    model: str


class ProviderConfigurationError(Exception):
    pass


class ProviderRateLimitError(Exception):
    pass


class ProviderTemporaryError(Exception):
    pass


class ProviderRequestError(Exception):
    pass


class LLMProvider(Protocol):
    async def generate(
        self,
        *,
        system_prompt: str,
        messages: list[dict[str, str]],
    ) -> ProviderResult:
        ...
