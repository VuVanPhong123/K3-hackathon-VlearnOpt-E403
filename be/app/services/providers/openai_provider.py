from __future__ import annotations

import asyncio

from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    AsyncOpenAI,
    AuthenticationError,
    BadRequestError,
    NotFoundError,
    RateLimitError,
)

from app.config import settings
from app.services.providers.base import (
    ProviderConfigurationError,
    ProviderRateLimitError,
    ProviderRequestError,
    ProviderResult,
    ProviderTemporaryError,
)


class OpenAIProvider:
    provider_name = "openai"

    def __init__(self) -> None:
        if not settings.openai_api_key:
            raise ProviderConfigurationError("OPENAI_API_KEY is not configured.")
        self.model = settings.openai_model
        self.timeout = settings.openai_timeout_seconds
        self.client = AsyncOpenAI(api_key=settings.openai_api_key, timeout=self.timeout)

    async def generate(
        self,
        *,
        system_prompt: str,
        messages: list[dict[str, str]],
    ) -> ProviderResult:
        try:
            response = await asyncio.wait_for(
                self.client.responses.create(
                    model=self.model,
                    instructions=system_prompt,
                    input=messages,
                ),
                timeout=self.timeout + 5,
            )
            text = getattr(response, "output_text", "") or ""
            if not text:
                text = "Mình chưa tạo được câu trả lời từ nội dung hiện có."
            return ProviderResult(text=text, provider=self.provider_name, model=self.model)
        except RateLimitError as exc:
            raise ProviderRateLimitError(str(exc)) from exc
        except (APITimeoutError, APIConnectionError, TimeoutError, asyncio.TimeoutError) as exc:
            raise ProviderTemporaryError(str(exc)) from exc
        except (AuthenticationError, BadRequestError, NotFoundError) as exc:
            raise ProviderRequestError(str(exc)) from exc
        except APIStatusError as exc:
            if exc.status_code in {429}:
                raise ProviderRateLimitError(str(exc)) from exc
            if 500 <= exc.status_code <= 599:
                raise ProviderTemporaryError(str(exc)) from exc
            raise ProviderRequestError(str(exc)) from exc
