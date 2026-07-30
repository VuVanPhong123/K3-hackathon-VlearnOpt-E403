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

    async def generate_multimodal(
        self,
        *,
        system_prompt: str,
        text_prompt: str,
        image_bytes: bytes,
        mime_type: str,
        history: list[dict[str, str]] | None = None,
    ) -> ProviderResult:
        ...
