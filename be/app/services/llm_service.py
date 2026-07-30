from __future__ import annotations

import logging

from fastapi import HTTPException

from app.config import settings
from app.schemas import ChatRequest, ChatResponse, DocumentMetadata, PageContextResponse
from app.services.document_service import DocumentService
from app.services.page_context_service import PageContextService
from app.services.providers.base import (
    ProviderConfigurationError,
    ProviderRateLimitError,
    ProviderRequestError,
    ProviderTemporaryError,
)
from app.services.providers.gemini_provider import GeminiProvider
from app.services.providers.openai_provider import OpenAIProvider

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "Bạn là VLearn Tutor, một trợ lý học tập bằng tiếng Việt. "
    "Hãy trả lời rõ ràng, ngắn gọn và thân thiện. "
    "Khi có nội dung trang PDF được cung cấp, hãy ưu tiên sử dụng nội dung đó. "
    "Đây là prototype nên nếu context chưa đầy đủ, hãy nói rõ thay vì khẳng định chắc chắn."
)


class LLMService:
    def __init__(self) -> None:
        self.document_service = DocumentService()
        self.page_context_service = PageContextService(self.document_service)

    def _build_user_prompt(
        self,
        request: ChatRequest,
        metadata: DocumentMetadata | None,
        page_context: PageContextResponse | None,
    ) -> str:
        if page_context and metadata:
            page_text = page_context.text or "(Trang PDF này không có text trích xuất được.)"
            return (
                f"Tên tài liệu: {metadata.original_filename}\n"
                f"Trang: {page_context.page_number}\n\n"
                "Nội dung trích xuất:\n"
                "--- NỘI DUNG TRANG ---\n"
                f"{page_text}\n"
                "--- KẾT THÚC NỘI DUNG ---\n\n"
                f"Câu hỏi học viên:\n{request.message}"
            )
        return request.message

    def _build_messages(
        self,
        request: ChatRequest,
        user_prompt: str,
    ) -> list[dict[str, str]]:
        history = [{"role": item.role, "content": item.content} for item in request.history[-8:]]
        return [*history, {"role": "user", "content": user_prompt}]

    async def chat(self, request: ChatRequest) -> ChatResponse:
        metadata = None
        page_context = None
        if request.document_id and request.page_number:
            metadata = self.document_service.get_metadata(request.document_id)
            page_context = self.page_context_service.get_page_text(
                request.document_id,
                request.page_number,
            )
        elif request.document_id or request.page_number:
            raise HTTPException(status_code=400, detail="Trang PDF không hợp lệ.")

        user_prompt = self._build_user_prompt(request, metadata, page_context)
        messages = self._build_messages(request, user_prompt)

        try:
            primary = OpenAIProvider()
            result = await primary.generate(system_prompt=SYSTEM_PROMPT, messages=messages)
            return ChatResponse(
                answer=result.text,
                provider=result.provider,
                model=result.model,
                fallback_used=False,
                document_id=request.document_id,
                page_number=request.page_number,
            )
        except ProviderConfigurationError as exc:
            logger.info("Chưa cấu hình OpenAI: %s", exc)
            if not (settings.enable_gemini_fallback and settings.gemini_api_key):
                raise HTTPException(
                    status_code=503,
                    detail="Chưa cấu hình API key cho chatbot.",
                ) from exc
        except (ProviderRateLimitError, ProviderTemporaryError) as exc:
            logger.warning("OpenAI temporary error, attempting Gemini fallback: %s", type(exc).__name__)
            if not settings.enable_gemini_fallback:
                raise HTTPException(
                    status_code=503,
                    detail="OpenAI đang tạm thời không khả dụng.",
                ) from exc
        except ProviderRequestError as exc:
            logger.warning("OpenAI request error: %s", type(exc).__name__)
            raise HTTPException(
                status_code=502,
                detail="Cấu hình OpenAI chưa hợp lệ. Hãy kiểm tra API key hoặc model.",
            ) from exc

        try:
            fallback = GeminiProvider()
            result = await fallback.generate(system_prompt=SYSTEM_PROMPT, messages=messages)
            return ChatResponse(
                answer=result.text,
                provider="gemini fallback",
                model=result.model,
                fallback_used=True,
                document_id=request.document_id,
                page_number=request.page_number,
            )
        except ProviderConfigurationError as exc:
            raise HTTPException(
                status_code=503,
                detail="Chưa cấu hình API key cho chatbot.",
            ) from exc
        except (ProviderRateLimitError, ProviderTemporaryError) as exc:
            logger.warning("Gemini fallback temporary error: %s", type(exc).__name__)
            raise HTTPException(
                status_code=503,
                detail="OpenAI đang tạm thời không khả dụng và Gemini fallback cũng thất bại.",
            ) from exc
        except ProviderRequestError as exc:
            logger.warning("Gemini fallback request error: %s", type(exc).__name__)
            raise HTTPException(
                status_code=502,
                detail="Gemini fallback chưa khả dụng. Hãy kiểm tra API key hoặc model.",
            ) from exc
