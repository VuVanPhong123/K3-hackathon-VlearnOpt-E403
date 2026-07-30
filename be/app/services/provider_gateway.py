from __future__ import annotations

import logging

from app.config import settings
from app.services.providers.base import (
    ProviderConfigurationError,
    ProviderRateLimitError,
    ProviderRequestError,
    ProviderResult,
    ProviderTemporaryError,
)
from app.services.providers.gemini_provider import GeminiProvider
from app.services.providers.openai_provider import OpenAIProvider

logger = logging.getLogger(__name__)


class ProviderGateway:
    def configured(self) -> bool:
        return bool(settings.openai_api_key or settings.gemini_api_key)

    async def generate(self, *, system_prompt: str, messages: list[dict[str, str]]) -> tuple[ProviderResult, bool]:
        primary_name = settings.primary_text_provider or settings.primary_provider
        providers = []
        if primary_name == "gemini":
            providers = [GeminiProvider, OpenAIProvider]
        else:
            providers = [OpenAIProvider, GeminiProvider]
        last_error: Exception | None = None
        for index, provider_class in enumerate(providers):
            try:
                provider = provider_class()
                result = await provider.generate(system_prompt=system_prompt, messages=messages)
                return result, index > 0
            except ProviderConfigurationError as exc:
                last_error = exc
                continue
            except (ProviderRateLimitError, ProviderTemporaryError) as exc:
                last_error = exc
                logger.warning("Provider temporary failure: %s", type(exc).__name__)
                continue
            except ProviderRequestError as exc:
                last_error = exc
                logger.warning("Provider request failure: %s", type(exc).__name__)
                continue
        raise ProviderTemporaryError(str(last_error) if last_error else "No provider configured.")
