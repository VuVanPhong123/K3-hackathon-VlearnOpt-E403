from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterator

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

logger = logging.getLogger(__name__)


class GeminiProvider:
    provider_name = "gemini"

    def __init__(self) -> None:
        if not settings.gemini_api_key:
            raise ProviderConfigurationError("Chưa cấu hình GEMINI_API_KEY.")
        self.model = settings.gemini_model
        self.vision_model = settings.gemini_vision_model or settings.gemini_model
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
            self._raise_provider_error(exc)
        except (TimeoutError, asyncio.TimeoutError) as exc:
            raise ProviderTemporaryError(str(exc)) from exc

    async def generate_multimodal(
        self,
        *,
        system_prompt: str,
        text_prompt: str,
        image_bytes: bytes,
        mime_type: str,
        history: list[dict[str, str]] | None = None,
    ) -> ProviderResult:
        history_prompt = "\n\n".join(
            f"{item['role']}: {item['content']}"
            for item in (history or [])[-settings.chat_recent_message_limit:]
        )
        prompt = f"{history_prompt}\n\nuser: {text_prompt}" if history_prompt else text_prompt
        try:
            response = await asyncio.wait_for(
                self.client.aio.models.generate_content(
                    model=self.vision_model,
                    contents=[
                        types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
                        prompt,
                    ],
                    config=types.GenerateContentConfig(system_instruction=system_prompt),
                ),
                timeout=self.timeout + 5,
            )
            text = getattr(response, "text", "") or "Mình chưa tạo được câu trả lời từ hình ảnh hiện có."
            return ProviderResult(text=text, provider=self.provider_name, model=self.vision_model)
        except errors.APIError as exc:
            self._raise_provider_error(exc)
        except (TimeoutError, asyncio.TimeoutError) as exc:
            raise ProviderTemporaryError(str(exc)) from exc

    async def stream_generate(
        self,
        *,
        system_prompt: str,
        messages: list[dict[str, str]],
    ) -> AsyncIterator[str]:
        prompt = "\n\n".join(f"{item['role']}: {item['content']}" for item in messages)
        yielded = False
        stream_failed_before_delta = False
        try:
            stream = await asyncio.wait_for(
                self.client.aio.models.generate_content_stream(
                    model=self.model,
                    contents=prompt,
                    config=types.GenerateContentConfig(system_instruction=system_prompt),
                ),
                timeout=self.timeout + 5,
            )
            async for chunk in stream:
                text = getattr(chunk, "text", "") or ""
                if text:
                    yielded = True
                    yield text
            if not yielded:
                raise ProviderTemporaryError("Gemini returned an empty stream.")
        except errors.APIError as exc:
            self._raise_provider_error(exc)
        except (TimeoutError, asyncio.TimeoutError) as exc:
            raise ProviderTemporaryError(str(exc)) from exc
        except Exception as exc:
            if yielded:
                raise ProviderTemporaryError(str(exc)) from exc
            stream_failed_before_delta = True
            logger.warning("Gemini text stream failed before first delta; falling back to non-stream call.", exc_info=True)

        if stream_failed_before_delta:
            result = await self.generate(system_prompt=system_prompt, messages=messages)
            yield result.text

    async def stream_generate_multimodal(
        self,
        *,
        system_prompt: str,
        text_prompt: str,
        image_bytes: bytes,
        mime_type: str,
        history: list[dict[str, str]] | None = None,
    ) -> AsyncIterator[str]:
        history_prompt = "\n\n".join(
            f"{item['role']}: {item['content']}"
            for item in (history or [])[-settings.chat_recent_message_limit:]
        )
        prompt = f"{history_prompt}\n\nuser: {text_prompt}" if history_prompt else text_prompt
        yielded = False
        stream_failed_before_delta = False
        try:
            stream = await asyncio.wait_for(
                self.client.aio.models.generate_content_stream(
                    model=self.vision_model,
                    contents=[
                        types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
                        prompt,
                    ],
                    config=types.GenerateContentConfig(system_instruction=system_prompt),
                ),
                timeout=self.timeout + 5,
            )
            async for chunk in stream:
                text = getattr(chunk, "text", "") or ""
                if text:
                    yielded = True
                    yield text
            if not yielded:
                raise ProviderTemporaryError("Gemini returned an empty multimodal stream.")
        except errors.APIError as exc:
            self._raise_provider_error(exc)
        except (TimeoutError, asyncio.TimeoutError) as exc:
            raise ProviderTemporaryError(str(exc)) from exc
        except Exception as exc:
            if yielded:
                raise ProviderTemporaryError(str(exc)) from exc
            stream_failed_before_delta = True
            logger.warning("Gemini multimodal stream failed before first delta; falling back to non-stream call.", exc_info=True)

        if stream_failed_before_delta:
            result = await self.generate_multimodal(
                system_prompt=system_prompt,
                text_prompt=text_prompt,
                image_bytes=image_bytes,
                mime_type=mime_type,
                history=history,
            )
            yield result.text

    @staticmethod
    def _raise_provider_error(exc: errors.APIError) -> None:
        status_code = getattr(exc, "code", None)
        if status_code == 429:
            raise ProviderRateLimitError(str(exc)) from exc
        if status_code and 500 <= int(status_code) <= 599:
            raise ProviderTemporaryError(str(exc)) from exc
        if status_code in {400, 401, 403, 404}:
            raise ProviderRequestError(str(exc)) from exc
        raise ProviderTemporaryError(str(exc)) from exc
