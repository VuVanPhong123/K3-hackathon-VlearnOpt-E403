import pytest

from app.config import settings
from app.services.provider_gateway import ProviderGateway
from app.services.providers.base import (
    ProviderRequestError,
    ProviderResult,
    ProviderTemporaryError,
)


class FakeProvider:
    def __init__(
        self,
        name: str,
        error: Exception | None = None,
        stream_error_after_delta: Exception | None = None,
    ) -> None:
        self.name = name
        self.error = error
        self.stream_error_after_delta = stream_error_after_delta
        self.calls = 0

    async def generate(self, *, system_prompt: str, messages: list[dict[str, str]]) -> ProviderResult:
        self.calls += 1
        if self.error:
            raise self.error
        return ProviderResult(text="Câu trả lời", provider=self.name, model=f"fake-{self.name}")

    async def stream_generate(self, *, system_prompt: str, messages: list[dict[str, str]]):
        self.calls += 1
        if self.error:
            raise self.error
        yield f"{self.name}-delta"
        if self.stream_error_after_delta:
            raise self.stream_error_after_delta


@pytest.fixture
def provider_settings(monkeypatch):
    monkeypatch.setattr(settings, "primary_text_provider", "openai")
    monkeypatch.setattr(settings, "fallback_text_provider", "gemini")
    monkeypatch.setattr(settings, "openai_api_key", "openai-test")
    monkeypatch.setattr(settings, "gemini_api_key", "gemini-test")
    monkeypatch.setattr(settings, "enable_gemini_fallback", True)


@pytest.mark.asyncio
async def test_temporary_openai_failure_uses_gemini(provider_settings) -> None:
    openai = FakeProvider("openai", ProviderTemporaryError("timeout"))
    gemini = FakeProvider("gemini")
    gateway = ProviderGateway(lambda: openai, lambda: gemini)

    result, fallback_used = await gateway.generate(system_prompt="hệ thống", messages=[])

    assert result.provider == "gemini"
    assert fallback_used is True
    assert openai.calls == 1
    assert gemini.calls == 1


@pytest.mark.asyncio
async def test_openai_request_error_does_not_fallback(provider_settings) -> None:
    openai = FakeProvider("openai", ProviderRequestError("invalid key"))
    gemini = FakeProvider("gemini")
    gateway = ProviderGateway(lambda: openai, lambda: gemini)

    with pytest.raises(ProviderRequestError):
        await gateway.generate(system_prompt="hệ thống", messages=[])

    assert openai.calls == 1
    assert gemini.calls == 0


@pytest.mark.asyncio
async def test_gemini_runs_directly_when_openai_key_is_empty(provider_settings, monkeypatch) -> None:
    monkeypatch.setattr(settings, "openai_api_key", "")
    openai = FakeProvider("openai")
    gemini = FakeProvider("gemini")
    gateway = ProviderGateway(lambda: openai, lambda: gemini)

    result, fallback_used = await gateway.generate(system_prompt="hệ thống", messages=[])

    assert result.provider == "gemini"
    assert fallback_used is False
    assert openai.calls == 0
    assert gemini.calls == 1


@pytest.mark.asyncio
async def test_stream_temporary_failure_before_first_delta_uses_fallback(provider_settings) -> None:
    openai = FakeProvider("openai", ProviderTemporaryError("timeout"))
    gemini = FakeProvider("gemini")
    gateway = ProviderGateway(lambda: openai, lambda: gemini)

    chunks = [
        chunk
        async for chunk in gateway.stream_generate(system_prompt="hệ thống", messages=[])
    ]

    assert [chunk.text for chunk in chunks] == ["gemini-delta"]
    assert chunks[0].provider == "gemini"
    assert chunks[0].fallback_used is True
    assert openai.calls == 1
    assert gemini.calls == 1


@pytest.mark.asyncio
async def test_stream_failure_after_first_delta_does_not_fallback(provider_settings) -> None:
    openai = FakeProvider("openai", stream_error_after_delta=ProviderTemporaryError("late"))
    gemini = FakeProvider("gemini")
    gateway = ProviderGateway(lambda: openai, lambda: gemini)
    received = []

    with pytest.raises(ProviderTemporaryError):
        async for chunk in gateway.stream_generate(system_prompt="hệ thống", messages=[]):
            received.append(chunk.text)

    assert received == ["openai-delta"]
    assert openai.calls == 1
    assert gemini.calls == 0
