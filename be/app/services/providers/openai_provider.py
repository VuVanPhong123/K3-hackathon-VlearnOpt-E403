from __future__ import annotations

import asyncio
import base64
from collections.abc import AsyncIterator

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
            raise ProviderConfigurationError("Chưa cấu hình OPENAI_API_KEY.")
        self.model = settings.openai_model
        self.vision_model = settings.openai_vision_model or settings.openai_model
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
            if exc.status_code == 429:
                raise ProviderRateLimitError(str(exc)) from exc
            if 500 <= exc.status_code <= 599:
                raise ProviderTemporaryError(str(exc)) from exc
            raise ProviderRequestError(str(exc)) from exc

    async def stream_generate(
        self,
        *,
        system_prompt: str,
        messages: list[dict[str, str]],
    ) -> AsyncIterator[str]:
        yielded = False
        try:
            async with self.client.responses.stream(
                model=self.model,
                instructions=system_prompt,
                input=messages,
            ) as stream:
                async for event in stream:
                    if getattr(event, "type", "") != "response.output_text.delta":
                        continue
                    delta = getattr(event, "delta", "") or ""
                    if delta:
                        yielded = True
                        yield delta
            if not yielded:
                raise ProviderTemporaryError("OpenAI returned an empty stream.")
        except RateLimitError as exc:
            raise ProviderRateLimitError(str(exc)) from exc
        except (APITimeoutError, APIConnectionError, TimeoutError, asyncio.TimeoutError) as exc:
            raise ProviderTemporaryError(str(exc)) from exc
        except (AuthenticationError, BadRequestError, NotFoundError) as exc:
            raise ProviderRequestError(str(exc)) from exc
        except APIStatusError as exc:
            if exc.status_code == 429:
                raise ProviderRateLimitError(str(exc)) from exc
            if 500 <= exc.status_code <= 599:
                raise ProviderTemporaryError(str(exc)) from exc
            raise ProviderRequestError(str(exc)) from exc

    async def generate_multimodal(
        self,
        *,
        system_prompt: str,
        text_prompt: str,
        image_bytes: bytes,
        mime_type: str,
        history: list[dict[str, str]] | None = None,
    ) -> ProviderResult:
        data_url = f"data:{mime_type};base64,{base64.b64encode(image_bytes).decode('ascii')}"
        input_items: list[dict] = []
        for item in (history or [])[-settings.chat_recent_message_limit:]:
            input_items.append({"role": item["role"], "content": item["content"]})
        input_items.append(
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": text_prompt},
                    {"type": "input_image", "image_url": data_url, "detail": "high"},
                ],
            }
        )
        try:
            response = await asyncio.wait_for(
                self.client.responses.create(
                    model=self.vision_model,
                    instructions=system_prompt,
                    input=input_items,
                ),
                timeout=self.timeout + 5,
            )
            text = getattr(response, "output_text", "") or ""
            if not text:
                text = "Mình chưa tạo được câu trả lời từ hình ảnh hiện có."
            return ProviderResult(text=text, provider=self.provider_name, model=self.vision_model)
        except RateLimitError as exc:
            raise ProviderRateLimitError(str(exc)) from exc
        except (APITimeoutError, APIConnectionError, TimeoutError, asyncio.TimeoutError) as exc:
            raise ProviderTemporaryError(str(exc)) from exc
        except (AuthenticationError, BadRequestError, NotFoundError) as exc:
            raise ProviderRequestError(str(exc)) from exc
        except APIStatusError as exc:
            if exc.status_code == 429:
                raise ProviderRateLimitError(str(exc)) from exc
            if 500 <= exc.status_code <= 599:
                raise ProviderTemporaryError(str(exc)) from exc
            raise ProviderRequestError(str(exc)) from exc

    async def stream_generate_multimodal(
        self,
        *,
        system_prompt: str,
        text_prompt: str,
        image_bytes: bytes,
        mime_type: str,
        history: list[dict[str, str]] | None = None,
    ) -> AsyncIterator[str]:
        data_url = f"data:{mime_type};base64,{base64.b64encode(image_bytes).decode('ascii')}"
        input_items: list[dict] = []
        for item in (history or [])[-settings.chat_recent_message_limit:]:
            input_items.append({"role": item["role"], "content": item["content"]})
        input_items.append(
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": text_prompt},
                    {"type": "input_image", "image_url": data_url, "detail": "high"},
                ],
            }
        )
        yielded = False
        try:
            async with self.client.responses.stream(
                model=self.vision_model,
                instructions=system_prompt,
                input=input_items,
            ) as stream:
                async for event in stream:
                    if getattr(event, "type", "") != "response.output_text.delta":
                        continue
                    delta = getattr(event, "delta", "") or ""
                    if delta:
                        yielded = True
                        yield delta
            if not yielded:
                raise ProviderTemporaryError("OpenAI returned an empty multimodal stream.")
        except RateLimitError as exc:
            raise ProviderRateLimitError(str(exc)) from exc
        except (APITimeoutError, APIConnectionError, TimeoutError, asyncio.TimeoutError) as exc:
            raise ProviderTemporaryError(str(exc)) from exc
        except (AuthenticationError, BadRequestError, NotFoundError) as exc:
            raise ProviderRequestError(str(exc)) from exc
        except APIStatusError as exc:
            if exc.status_code == 429:
                raise ProviderRateLimitError(str(exc)) from exc
            if 500 <= exc.status_code <= 599:
                raise ProviderTemporaryError(str(exc)) from exc
            raise ProviderRequestError(str(exc)) from exc
