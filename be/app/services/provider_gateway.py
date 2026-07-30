from __future__ import annotations

import logging
from collections.abc import AsyncIterator, Callable

from app.config import settings
from app.services.providers.base import (
    LLMProvider,
    ProviderConfigurationError,
    ProviderRateLimitError,
    ProviderRequestError,
    ProviderResult,
    ProviderStreamChunk,
    ProviderTemporaryError,
)
from app.services.providers.gemini_provider import GeminiProvider
from app.services.providers.openai_provider import OpenAIProvider

logger = logging.getLogger(__name__)


class ProviderGateway:
    def __init__(
        self,
        openai_factory: Callable[[], LLMProvider] = OpenAIProvider,
        gemini_factory: Callable[[], LLMProvider] = GeminiProvider,
    ) -> None:
        self.factories = {
            "openai": openai_factory,
            "gemini": gemini_factory,
        }

    def configured(self) -> bool:
        return bool(settings.openai_api_key or settings.gemini_api_key)

    def _has_credentials(self, provider_name: str) -> bool:
        if provider_name == "openai":
            return bool(settings.openai_api_key)
        if provider_name == "gemini":
            return bool(settings.gemini_api_key)
        return False

    def _provider(self, provider_name: str) -> LLMProvider:
        factory = self.factories.get(provider_name)
        if factory is None:
            raise ProviderConfigurationError(f"Nhà cung cấp {provider_name} không được hỗ trợ.")
        return factory()

    async def _call(
        self,
        provider_name: str,
        *,
        system_prompt: str,
        messages: list[dict[str, str]],
    ) -> ProviderResult:
        return await self._provider(provider_name).generate(system_prompt=system_prompt, messages=messages)

    async def _call_multimodal(
        self,
        provider_name: str,
        *,
        system_prompt: str,
        text_prompt: str,
        image_bytes: bytes,
        mime_type: str,
        history: list[dict[str, str]] | None,
    ) -> ProviderResult:
        return await self._provider(provider_name).generate_multimodal(
            system_prompt=system_prompt,
            text_prompt=text_prompt,
            image_bytes=image_bytes,
            mime_type=mime_type,
            history=history,
        )

    async def _stream_call(
        self,
        provider_name: str,
        *,
        system_prompt: str,
        messages: list[dict[str, str]],
        fallback_used: bool,
    ) -> AsyncIterator[ProviderStreamChunk]:
        async for text in self._provider(provider_name).stream_generate(
            system_prompt=system_prompt,
            messages=messages,
        ):
            yield ProviderStreamChunk(
                text=text,
                provider=provider_name,
                model=self._model_for(provider_name, vision=False),
                fallback_used=fallback_used,
            )

    async def _stream_call_multimodal(
        self,
        provider_name: str,
        *,
        system_prompt: str,
        text_prompt: str,
        image_bytes: bytes,
        mime_type: str,
        history: list[dict[str, str]] | None,
        fallback_used: bool,
    ) -> AsyncIterator[ProviderStreamChunk]:
        async for text in self._provider(provider_name).stream_generate_multimodal(
            system_prompt=system_prompt,
            text_prompt=text_prompt,
            image_bytes=image_bytes,
            mime_type=mime_type,
            history=history,
        ):
            yield ProviderStreamChunk(
                text=text,
                provider=provider_name,
                model=self._model_for(provider_name, vision=True),
                fallback_used=fallback_used,
            )

    @staticmethod
    def _model_for(provider_name: str, *, vision: bool) -> str:
        if provider_name == "openai":
            return (settings.openai_vision_model or settings.openai_model) if vision else settings.openai_model
        if provider_name == "gemini":
            return (settings.gemini_vision_model or settings.gemini_model) if vision else settings.gemini_model
        return ""

    async def generate(
        self,
        *,
        system_prompt: str,
        messages: list[dict[str, str]],
    ) -> tuple[ProviderResult, bool]:
        primary_name = (settings.primary_text_provider or "openai").lower()
        fallback_name = (settings.fallback_text_provider or "gemini").lower()

        if not self._has_credentials(primary_name):
            if self._has_credentials(fallback_name):
                result = await self._call(fallback_name, system_prompt=system_prompt, messages=messages)
                return result, False
            raise ProviderConfigurationError("Chưa cấu hình API key cho chatbot.")

        try:
            result = await self._call(primary_name, system_prompt=system_prompt, messages=messages)
            return result, False
        except (ProviderRequestError, ProviderConfigurationError):
            raise
        except (ProviderRateLimitError, ProviderTemporaryError):
            logger.warning("Nhà cung cấp văn bản chính tạm thời gặp lỗi", exc_info=True)
            if (
                not settings.enable_gemini_fallback
                or fallback_name == primary_name
                or not self._has_credentials(fallback_name)
            ):
                raise

        result = await self._call(fallback_name, system_prompt=system_prompt, messages=messages)
        return result, True

    async def stream_generate(
        self,
        *,
        system_prompt: str,
        messages: list[dict[str, str]],
    ) -> AsyncIterator[ProviderStreamChunk]:
        primary_name = (settings.primary_text_provider or "openai").lower()
        fallback_name = (settings.fallback_text_provider or "gemini").lower()

        if not self._has_credentials(primary_name):
            if self._has_credentials(fallback_name):
                async for chunk in self._stream_call(
                    fallback_name,
                    system_prompt=system_prompt,
                    messages=messages,
                    fallback_used=False,
                ):
                    yield chunk
                return
            raise ProviderConfigurationError("Chưa cấu hình API key cho chatbot.")

        yielded = False
        try:
            async for chunk in self._stream_call(
                primary_name,
                system_prompt=system_prompt,
                messages=messages,
                fallback_used=False,
            ):
                yielded = True
                yield chunk
            return
        except (ProviderRequestError, ProviderConfigurationError):
            raise
        except (ProviderRateLimitError, ProviderTemporaryError):
            if yielded:
                raise
            logger.warning("Nhà cung cấp văn bản chính tạm thời gặp lỗi trước delta đầu", exc_info=True)
            if (
                not settings.enable_gemini_fallback
                or fallback_name == primary_name
                or not self._has_credentials(fallback_name)
            ):
                raise

        async for chunk in self._stream_call(
            fallback_name,
            system_prompt=system_prompt,
            messages=messages,
            fallback_used=True,
        ):
            yield chunk

    async def generate_multimodal(
        self,
        *,
        system_prompt: str,
        text_prompt: str,
        image_bytes: bytes,
        mime_type: str,
        history: list[dict[str, str]] | None = None,
    ) -> tuple[ProviderResult, bool]:
        primary_name = (settings.vision_primary_provider or "gemini").lower()
        fallback_name = (settings.vision_fallback_provider or "openai").lower()

        if not self._has_credentials(primary_name):
            if self._has_credentials(fallback_name):
                result = await self._call_multimodal(
                    fallback_name,
                    system_prompt=system_prompt,
                    text_prompt=text_prompt,
                    image_bytes=image_bytes,
                    mime_type=mime_type,
                    history=history,
                )
                return result, False
            raise ProviderConfigurationError("Chưa cấu hình API key cho chức năng đọc hình ảnh.")

        try:
            result = await self._call_multimodal(
                primary_name,
                system_prompt=system_prompt,
                text_prompt=text_prompt,
                image_bytes=image_bytes,
                mime_type=mime_type,
                history=history,
            )
            return result, False
        except (ProviderRequestError, ProviderConfigurationError):
            raise
        except (ProviderRateLimitError, ProviderTemporaryError):
            logger.warning("Nhà cung cấp hình ảnh chính tạm thời gặp lỗi", exc_info=True)
            if fallback_name == primary_name or not self._has_credentials(fallback_name):
                raise

        result = await self._call_multimodal(
            fallback_name,
            system_prompt=system_prompt,
            text_prompt=text_prompt,
            image_bytes=image_bytes,
            mime_type=mime_type,
            history=history,
        )
        return result, True

    async def stream_generate_multimodal(
        self,
        *,
        system_prompt: str,
        text_prompt: str,
        image_bytes: bytes,
        mime_type: str,
        history: list[dict[str, str]] | None = None,
    ) -> AsyncIterator[ProviderStreamChunk]:
        primary_name = (settings.vision_primary_provider or "gemini").lower()
        fallback_name = (settings.vision_fallback_provider or "openai").lower()

        if not self._has_credentials(primary_name):
            if self._has_credentials(fallback_name):
                async for chunk in self._stream_call_multimodal(
                    fallback_name,
                    system_prompt=system_prompt,
                    text_prompt=text_prompt,
                    image_bytes=image_bytes,
                    mime_type=mime_type,
                    history=history,
                    fallback_used=False,
                ):
                    yield chunk
                return
            raise ProviderConfigurationError("Chưa cấu hình API key cho chức năng đọc hình ảnh.")

        yielded = False
        try:
            async for chunk in self._stream_call_multimodal(
                primary_name,
                system_prompt=system_prompt,
                text_prompt=text_prompt,
                image_bytes=image_bytes,
                mime_type=mime_type,
                history=history,
                fallback_used=False,
            ):
                yielded = True
                yield chunk
            return
        except (ProviderRequestError, ProviderConfigurationError):
            raise
        except (ProviderRateLimitError, ProviderTemporaryError):
            if yielded:
                raise
            logger.warning("Nhà cung cấp hình ảnh chính tạm thời gặp lỗi trước delta đầu", exc_info=True)
            if fallback_name == primary_name or not self._has_credentials(fallback_name):
                raise

        async for chunk in self._stream_call_multimodal(
            fallback_name,
            system_prompt=system_prompt,
            text_prompt=text_prompt,
            image_bytes=image_bytes,
            mime_type=mime_type,
            history=history,
            fallback_used=True,
        ):
            yield chunk
