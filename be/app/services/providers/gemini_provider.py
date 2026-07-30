from __future__ import annotations

import asyncio

from google import genai
from google.genai import errors, types

from app.config import settings
from app.services.providers.base import (
    ProviderConfigurationError,
    ProviderRateLimitError,
    ProviderRequestError,
    ProviderResult,
    ProviderTemporaryError,
)


class GeminiProvider:
    provider_name = "gemini"

    def __init__(self) -> None:
        if not settings.gemini_api_key:
            raise ProviderConfigurationError("GEMINI_API_KEY is not configured.")
        self.model = settings.gemini_model
        self.timeout = settings.gemini_timeout_seconds
        self.client = genai.Client(api_key=settings.gemini_api_key)

    async def generate(
        self,
        *,
        system_prompt: str,
        messages: list[dict[str, str]],
    ) -> ProviderResult:
        prompt = "\n\n".join(f"{item['role']}: {item['content']}" for item in messages)
        try:
            response = await asyncio.wait_for(
                self.client.aio.models.generate_content(
                    model=self.model,
                    contents=prompt,
                    config=types.GenerateContentConfig(system_instruction=system_prompt),
                ),
                timeout=self.timeout + 5,
            )
            text = getattr(response, "text", "") or "Mình chưa tạo được câu trả lời từ nội dung hiện có."
            return ProviderResult(text=text, provider=self.provider_name, model=self.model)
        except errors.APIError as exc:
            status_code = getattr(exc, "code", None)
            if status_code == 429:
                raise ProviderRateLimitError(str(exc)) from exc
            if status_code and 500 <= int(status_code) <= 599:
                raise ProviderTemporaryError(str(exc)) from exc
            if status_code in {400, 401, 403, 404}:
                raise ProviderRequestError(str(exc)) from exc
            raise ProviderTemporaryError(str(exc)) from exc
        except (TimeoutError, asyncio.TimeoutError) as exc:
            raise ProviderTemporaryError(str(exc)) from exc
