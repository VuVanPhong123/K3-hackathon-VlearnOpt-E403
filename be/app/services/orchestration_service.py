from __future__ import annotations

import logging
import re
import time
import unicodedata
import uuid
from pathlib import Path

from fastapi import HTTPException
from rapidfuzz import fuzz

from app.config import settings
from app.repositories.conversation_repository import ConversationRepository
from app.schemas import BBox, ChatRequestV2, ChatResponseV2, Citation, TraceInfo
from app.services.answer_service import AnswerService
from app.services.conversation_service import ConversationService
from app.services.document_service import DocumentService
from app.services.interaction_resolver import InteractionResolver
from app.services.page_context_service import PageContextService
from app.services.providers.base import (
    ProviderConfigurationError,
    ProviderRateLimitError,
    ProviderRequestError,
    ProviderTemporaryError,
)
from app.services.retrieval_service import RetrievalResult, RetrievalService
from app.services.visual_context_service import VisualContextService

logger = logging.getLogger(__name__)


class OrchestrationService:
    """Điều phối một lần duy nhất cho mọi chế độ tương tác của chat v2."""

    def __init__(
        self,
        *,
        answer_service: AnswerService | None = None,
        document_service: DocumentService | None = None,
        page_context_service: PageContextService | None = None,
        visual_context_service: VisualContextService | None = None,
        retrieval_service: RetrievalService | None = None,
        conversation_repository: ConversationRepository | None = None,
    ) -> None:
        self.document_service = document_service or DocumentService()
        self.page_context_service = page_context_service or PageContextService(self.document_service)
        self.visual_context_service = visual_context_service or VisualContextService(self.document_service)
        self.retrieval_service = retrieval_service or RetrievalService()
        self.answer_service = answer_service or AnswerService()
        self.interaction_resolver = InteractionResolver(self.document_service)
        self.conversation_repository = conversation_repository or ConversationRepository()
        self.conversation_service = ConversationService(self.conversation_repository)

    async def chat(self, request: ChatRequestV2) -> ChatResponseV2:
        started_at = time.perf_counter()
        trace_id = str(uuid.uuid4())
        conversation_id = self.conversation_service.conversation_id(request.conversation_id)
        resolved = self.interaction_resolver.resolve(request)
        image_used = resolved.mode in {"PAGE_CHAT", "VISUAL_REGION_CHAT"} or (
            resolved.mode == "DOCUMENT_SEARCH_CHAT" and resolved.visual_query
        )

        try:
            response, citations, pages_used, confidence, image_used = await self._dispatch(
                request,
                resolved.mode,
                resolved.page_number,
                resolved.confidence,
                resolved.visual_query,
                resolved.exact_caption,
            )
        except ProviderConfigurationError as exc:
            detail = (
                "Chưa cấu hình API key cho chức năng đọc hình ảnh."
                if image_used
                else "Chưa cấu hình API key cho chatbot."
            )
            raise HTTPException(status_code=503, detail=detail) from exc
        except ProviderRequestError as exc:
            raise HTTPException(
                status_code=502,
                detail="Cấu hình nhà cung cấp AI chưa hợp lệ. Hãy kiểm tra API key và tên mô hình.",
            ) from exc
        except (ProviderRateLimitError, ProviderTemporaryError) as exc:
            raise HTTPException(
                status_code=503,
                detail="Các nhà cung cấp AI đang tạm thời không khả dụng. Hãy thử lại sau.",
            ) from exc

        result, fallback_used = response
        trace = TraceInfo(
            trace_id=trace_id,
            intent=resolved.mode,
            pages_used=pages_used,
            provider=result.provider,
            model=result.model,
            fallback=fallback_used,
            latency_ms={"total": round((time.perf_counter() - started_at) * 1000, 2)},
            confidence=confidence,
            image_used=image_used,
        )
        conversation_document_id = None if resolved.mode == "GENERAL_CHAT" else request.document_id
        self.conversation_repository.ensure_conversation(conversation_id, conversation_document_id, None)
        self.conversation_repository.add_message(conversation_id, "user", request.message)
        self.conversation_repository.add_message(
            conversation_id,
            "assistant",
            result.text,
            [citation.model_dump() for citation in citations],
            trace.model_dump(),
        )
        logger.info(
            "v2_chat trace_id=%s intent=%s pages=%s provider=%s fallback=%s image=%s",
            trace_id,
            resolved.mode,
            pages_used,
            result.provider,
            fallback_used,
            image_used,
        )
        return ChatResponseV2(
            answer=result.text,
            citations=citations,
            confidence=confidence,
            conversation_id=conversation_id,
            trace=trace,
            provider=result.provider,
            model=result.model,
            fallback_used=fallback_used,
        )

    async def _dispatch(
        self,
        request: ChatRequestV2,
        mode: str,
        page_number: int | None,
        confidence: float,
        visual_query: bool,
        exact_caption: str | None,
    ):
        if mode == "GENERAL_CHAT":
            response = await self.answer_service.answer_general(
                message=request.message,
                history=request.history,
            )
            return response, [], [], confidence, False

        if not request.document_id:
            raise HTTPException(status_code=400, detail="Cần có tài liệu PDF để xử lý câu hỏi này.")

        metadata = self.document_service.get_metadata(request.document_id)
        if mode == "PAGE_CHAT" and page_number:
            page = self.page_context_service.get_page_text(request.document_id, page_number)
            image_path = self.visual_context_service.render_page(request.document_id, page_number)
            image_bytes, mime_type = self._read_image(image_path)
            response = await self.answer_service.answer_page(
                message=request.message,
                history=request.history,
                filename=metadata.original_filename,
                page_number=page_number,
                page_text=page.text,
                image_bytes=image_bytes,
                mime_type=mime_type,
            )
            return response, [self._citation(request.document_id, page_number)], [page_number], confidence, True

        if mode == "TEXT_SELECTION_CHAT" and request.context.text_selection:
            selection = request.context.text_selection
            page = self.page_context_service.get_page_text(request.document_id, selection.page_number)
            surrounding = self._validate_selection(selection.selected_text, page.text)
            response = await self.answer_service.answer_selection(
                message=request.message,
                history=request.history,
                filename=metadata.original_filename,
                page_number=selection.page_number,
                selected_text=selection.selected_text,
                surrounding_text=surrounding,
            )
            page_number = selection.page_number
            return response, [self._citation(request.document_id, page_number)], [page_number], confidence, False

        if mode == "VISUAL_REGION_CHAT" and request.context.visual_region:
            region = request.context.visual_region
            image_path = self.visual_context_service.render_crop(
                request.document_id,
                region.page_number,
                region.bbox,
            )
            image_bytes, mime_type = self._read_image(image_path)
            overlapping_text = self.visual_context_service.get_overlapping_text(
                request.document_id,
                region.page_number,
                region.bbox,
            )
            response = await self.answer_service.answer_visual_region(
                message=request.message,
                history=request.history,
                filename=metadata.original_filename,
                page_number=region.page_number,
                overlapping_text=overlapping_text,
                image_bytes=image_bytes,
                mime_type=mime_type,
            )
            page_number = region.page_number
            return response, [self._citation(request.document_id, page_number)], [page_number], confidence, True

        if mode == "DOCUMENT_SEARCH_CHAT":
            return await self._document_search(
                request,
                metadata.original_filename,
                visual_query=visual_query,
                exact_caption=exact_caption,
                confidence=confidence,
            )

        raise HTTPException(status_code=400, detail="Chế độ tương tác không hợp lệ.")

    async def _document_search(
        self,
        request: ChatRequestV2,
        filename: str,
        *,
        visual_query: bool,
        exact_caption: str | None,
        confidence: float,
    ):
        document_id = request.document_id
        assert document_id is not None
        caption_page = self._find_caption_page(document_id, exact_caption) if exact_caption else None
        results = self.retrieval_service.search(document_id, request.message, top_k=4)

        if visual_query:
            visual_results = self._limit_distinct_pages(results, 2)
            evidence = self._evidence(visual_results)
            page_number = caption_page or self._first_result_page(visual_results)
            if page_number:
                page = self.page_context_service.get_page_text(document_id, page_number)
                image_path = self.visual_context_service.render_page(document_id, page_number)
                image_bytes, mime_type = self._read_image(image_path)
                response = await self.answer_service.answer_document_visual_search(
                    message=request.message,
                    history=request.history,
                    filename=filename,
                    page_number=page_number,
                    page_text=page.text,
                    extra_evidence=evidence,
                    image_bytes=image_bytes,
                    mime_type=mime_type,
                )
                citations = self._citations_from_results(document_id, visual_results)
                if not any(item.page_number == page_number for item in citations):
                    citations.insert(0, self._citation(document_id, page_number))
                pages = list(dict.fromkeys([page_number, *[item.page_number for item in citations if item.page_number]]))
                return response, citations, pages, confidence, True

        response = await self.answer_service.answer_document_search(
            message=request.message,
            history=request.history,
            filename=filename,
            evidence_text=self._evidence(results) or "Không tìm thấy bằng chứng phù hợp trong tài liệu.",
        )
        citations = self._citations_from_results(document_id, results)
        pages = list(dict.fromkeys(item.page_number for item in citations if item.page_number))
        return response, citations, pages, confidence if results else 0.25, False

    def _find_caption_page(self, document_id: str, caption: str) -> int | None:
        repository = getattr(self.document_service, "repository", None)
        if repository is None or not hasattr(repository, "list_pages"):
            return None
        label, number = caption.rsplit(" ", 1)
        if label == "figure":
            pattern = rf"\b(?:figure|fig\.?|hình)\s*{re.escape(number)}\b"
        elif label == "hình":
            pattern = rf"\b(?:hình|figure|fig\.?)\s*{re.escape(number)}\b"
        else:
            pattern = rf"\b(?:table|bảng)\s*{re.escape(number)}\b"
        for page in repository.list_pages(document_id):
            if re.search(pattern, page.get("raw_text", ""), re.IGNORECASE):
                return int(page["page_number"])
        chunk_repository = getattr(self.retrieval_service, "chunk_repository", None)
        if chunk_repository is not None:
            for chunk in chunk_repository.list_chunks(document_id):
                if re.search(pattern, chunk.get("text", ""), re.IGNORECASE):
                    return int(chunk["page_number"])
        return None

    @staticmethod
    def _normalize_text(value: str) -> str:
        normalized = unicodedata.normalize("NFKC", value).casefold()
        return re.sub(r"\s+", " ", normalized).strip()

    def _validate_selection(self, selected_text: str, page_text: str) -> str:
        selected = self._normalize_text(selected_text)
        page = self._normalize_text(page_text)
        if not selected or not page:
            raise HTTPException(
                status_code=400,
                detail="Đoạn được chọn không khớp với nội dung trang PDF.",
            )
        if selected not in page:
            score = fuzz.partial_ratio(selected, page)
            if score < settings.text_selection_match_threshold:
                raise HTTPException(
                    status_code=400,
                    detail="Đoạn được chọn không khớp với nội dung trang PDF.",
                )

        direct_index = page_text.casefold().find(selected_text.casefold())
        if direct_index < 0:
            return page_text[:4000]
        start = max(0, direct_index - 1200)
        end = min(len(page_text), direct_index + len(selected_text) + 1200)
        return page_text[start:end]

    @staticmethod
    def _evidence(results: list[RetrievalResult]) -> str:
        return "\n\n".join(
            f"[Trang {item.chunk['page_number']}] {item.chunk['text']}"
            for item in results
        )

    @staticmethod
    def _first_result_page(results: list[RetrievalResult]) -> int | None:
        return int(results[0].chunk["page_number"]) if results else None

    @staticmethod
    def _limit_distinct_pages(
        results: list[RetrievalResult],
        page_limit: int,
    ) -> list[RetrievalResult]:
        selected: list[RetrievalResult] = []
        pages: set[int] = set()
        for result in results:
            page_number = int(result.chunk["page_number"])
            if page_number not in pages and len(pages) >= page_limit:
                continue
            pages.add(page_number)
            selected.append(result)
        return selected

    @staticmethod
    def _citation(document_id: str, page_number: int, chunk_id: str | None = None) -> Citation:
        return Citation(
            document_id=document_id,
            page_number=page_number,
            chunk_id=chunk_id,
            label=f"Trang {page_number}",
        )

    def _citations_from_results(self, document_id: str, results: list[RetrievalResult]) -> list[Citation]:
        citations: list[Citation] = []
        seen: set[int] = set()
        for item in results:
            page_number = int(item.chunk["page_number"])
            if page_number in seen:
                continue
            seen.add(page_number)
            citations.append(self._citation(document_id, page_number, item.chunk.get("chunk_id")))
        return citations

    @staticmethod
    def _read_image(path: Path) -> tuple[bytes, str]:
        image_bytes = path.read_bytes()
        if len(image_bytes) > settings.max_visual_image_bytes:
            raise HTTPException(status_code=413, detail="Ảnh ngữ cảnh vượt quá dung lượng cho phép.")
        mime_type = "image/jpeg" if path.suffix.lower() in {".jpg", ".jpeg"} else "image/png"
        return image_bytes, mime_type
