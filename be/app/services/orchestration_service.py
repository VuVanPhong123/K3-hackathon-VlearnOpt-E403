from __future__ import annotations

import asyncio
import logging
import re
import time
import unicodedata
import uuid
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from fastapi import HTTPException
from rapidfuzz import fuzz

from app.config import settings
from app.domain.evidence import Evidence
from app.repositories.conversation_repository import ConversationRepository
from app.schemas import BBox, ChatRequestV2, ChatResponseV2, Citation, TraceInfo
from app.services.answer_service import AnswerService
from app.services.conversation_memory_service import ConversationMemoryService
from app.services.conversation_service import ConversationService
from app.services.document_service import DocumentService
from app.services.grounding_service import GroundingService
from app.services.interaction_resolver import InteractionResolver
from app.services.page_context_service import PageContextService
from app.services.providers.base import (
    ProviderConfigurationError,
    ProviderRateLimitError,
    ProviderRequestError,
    ProviderResult,
<<<<<<< Updated upstream
    ProviderStreamChunk,
=======
>>>>>>> Stashed changes
    ProviderTemporaryError,
)
from app.services.retrieval_service import RetrievalResult, RetrievalService
from app.services.visual_context_service import VisualContextService

logger = logging.getLogger(__name__)


@dataclass
class ChatExecutionPlan:
    request: ChatRequestV2
    conversation_id: str
    trace_id: str
    mode: str
    action: str
    kwargs: dict[str, Any]
    citations: list[Citation] = field(default_factory=list)
    pages_used: list[int] = field(default_factory=list)
    confidence: float = 0.0
    image_used: bool = False
    conversation_document_id: str | None = None
    document_version: int | None = None


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
        grounding_service: GroundingService | None = None,
        conversation_repository: ConversationRepository | None = None,
    ) -> None:
        self.document_service = document_service or DocumentService()
        self.page_context_service = page_context_service or PageContextService(self.document_service)
        self.visual_context_service = visual_context_service or VisualContextService(self.document_service)
        self.retrieval_service = retrieval_service or RetrievalService()
        self.grounding_service = grounding_service or GroundingService()
        self.answer_service = answer_service or AnswerService()
        self.interaction_resolver = InteractionResolver(self.document_service)
        self.conversation_repository = conversation_repository or ConversationRepository()
        self.conversation_service = ConversationService(self.conversation_repository)
        self.memory_service = ConversationMemoryService(self.conversation_repository)

    async def chat(self, request: ChatRequestV2) -> ChatResponseV2:
        started_at = time.perf_counter()
        plan = self.prepare_chat(request)
        try:
<<<<<<< Updated upstream
            result, fallback_used = await self._execute(plan)
=======
            response, citations, pages_used, confidence, image_used, decision = await self._dispatch(
                request,
                resolved.mode,
                resolved.page_number,
                resolved.confidence,
                resolved.visual_query,
                resolved.exact_caption,
                resolved.clarification_reason,
            )
>>>>>>> Stashed changes
        except ProviderConfigurationError as exc:
            raise self._provider_http_error(exc, plan.image_used) from exc
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

<<<<<<< Updated upstream
        trace = self._trace(plan, result.provider, result.model, fallback_used, started_at)
        self._save_success(plan, result.text, trace)
        logger.info(
            "v2_chat trace_id=%s intent=%s pages=%s provider=%s fallback=%s image=%s",
            plan.trace_id,
            plan.mode,
            plan.pages_used,
=======
        result, fallback_used = response
        trace = TraceInfo(
            trace_id=trace_id,
            intent=resolved.mode,
            decision=decision,
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
            "v2_chat trace_id=%s intent=%s decision=%s pages=%s provider=%s fallback=%s image=%s",
            trace_id,
            resolved.mode,
            decision,
            pages_used,
>>>>>>> Stashed changes
            result.provider,
            fallback_used,
            plan.image_used,
        )
        return ChatResponseV2(
            answer=result.text,
<<<<<<< Updated upstream
            citations=plan.citations,
            confidence=plan.confidence,
            conversation_id=plan.conversation_id,
=======
            citations=citations,
            confidence=confidence,
            needs_clarification=decision == "clarify",
            abstained=decision == "abstain",
            conversation_id=conversation_id,
>>>>>>> Stashed changes
            trace=trace,
            provider=result.provider,
            model=result.model,
            fallback_used=fallback_used,
        )

<<<<<<< Updated upstream
    async def stream(self, request: ChatRequestV2) -> AsyncIterator[dict[str, Any]]:
        started_at = time.perf_counter()
        try:
            plan = self.prepare_chat(request)
        except HTTPException as exc:
            yield {
                "event": "error",
                "data": {"detail": str(exc.detail), "retryable": False},
            }
            return

        yield {
            "event": "meta",
            "data": {
                "conversation_id": plan.conversation_id,
                "trace_id": plan.trace_id,
                "mode": plan.mode,
            },
        }

        answer_parts: list[str] = []
        provider = ""
        model = ""
        fallback_used = False
        try:
            async for chunk in self._stream_execute(plan):
                provider = chunk.provider
                model = chunk.model
                fallback_used = chunk.fallback_used
                answer_parts.append(chunk.text)
                yield {"event": "delta", "data": {"text": chunk.text}}
        except asyncio.CancelledError:
            raise
        except ProviderConfigurationError as exc:
            yield {
                "event": "error",
                "data": {"detail": self._provider_http_error(exc, plan.image_used).detail, "retryable": False},
            }
            return
        except ProviderRequestError:
            yield {
                "event": "error",
                "data": {
                    "detail": "Cấu hình nhà cung cấp AI chưa hợp lệ. Hãy kiểm tra API key và tên mô hình.",
                    "retryable": False,
                },
            }
            return
        except (ProviderRateLimitError, ProviderTemporaryError):
            yield {
                "event": "error",
                "data": {
                    "detail": "Các nhà cung cấp AI đang tạm thời không khả dụng. Hãy thử lại sau.",
                    "retryable": True,
                },
            }
            return

        answer = "".join(answer_parts).strip()
        if not answer:
            yield {
                "event": "error",
                "data": {"detail": "Chưa tạo được câu trả lời từ nội dung hiện có.", "retryable": True},
            }
            return

        trace = self._trace(plan, provider, model, fallback_used, started_at)
        self._save_success(plan, answer, trace)
        yield {
            "event": "done",
            "data": {
                "answer": answer,
                "conversation_id": plan.conversation_id,
                "citations": [citation.model_dump() for citation in plan.citations],
                "confidence": plan.confidence,
                "provider": provider,
                "model": model,
                "fallback_used": fallback_used,
                "trace": trace.model_dump(),
            },
        }

    def prepare_chat(self, request: ChatRequestV2) -> ChatExecutionPlan:
        conversation_id = self.conversation_service.conversation_id(request.conversation_id)
        trace_id = str(uuid.uuid4())
        resolved = self.interaction_resolver.resolve(request)
        history = self.memory_service.context_for(
            conversation_id=conversation_id,
            fallback_history=request.history,
        )

        if resolved.mode == "GENERAL_CHAT":
            return ChatExecutionPlan(
                request=request,
                conversation_id=conversation_id,
                trace_id=trace_id,
                mode=resolved.mode,
                action="general",
                kwargs={"message": request.message, "history": history},
                confidence=resolved.confidence,
                image_used=False,
            )
=======
    async def _dispatch(
        self,
        request: ChatRequestV2,
        mode: str,
        page_number: int | None,
        confidence: float,
        visual_query: bool,
        exact_caption: str | None,
        clarification_reason: str | None,
    ):
        if clarification_reason:
            response = await self.answer_service.answer_clarification(
                message=request.message,
                history=request.history,
                reason=clarification_reason,
            )
            return response, [], [], 0.0, False, "clarify"

        if mode == "GENERAL_CHAT":
            response = await self.answer_service.answer_general(
                message=request.message,
                history=request.history,
            )
            return response, [], [], confidence, False, "answer"
>>>>>>> Stashed changes

        if not request.document_id:
            raise HTTPException(status_code=400, detail="Cần có tài liệu PDF để xử lý câu hỏi này.")

        metadata = self.document_service.get_metadata(request.document_id)
<<<<<<< Updated upstream
        document_version = getattr(metadata, "version", None)
=======
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
            return response, [self._citation(request.document_id, page_number)], [page_number], confidence, True, "answer"
>>>>>>> Stashed changes

        if resolved.mode == "PAGE_CHAT" and resolved.page_number:
            page = self.page_context_service.get_page_text(request.document_id, resolved.page_number)
            image_path = self.visual_context_service.render_page(request.document_id, resolved.page_number)
            image_bytes, mime_type = self._read_image(image_path)
            return ChatExecutionPlan(
                request=request,
                conversation_id=conversation_id,
                trace_id=trace_id,
                mode=resolved.mode,
                action="page",
                kwargs={
                    "message": request.message,
                    "history": history,
                    "filename": metadata.original_filename,
                    "page_number": resolved.page_number,
                    "page_text": page.text,
                    "image_bytes": image_bytes,
                    "mime_type": mime_type,
                },
                citations=[self._citation(request.document_id, resolved.page_number)],
                pages_used=[resolved.page_number],
                confidence=resolved.confidence,
                image_used=True,
                conversation_document_id=request.document_id,
                document_version=document_version,
            )

        if resolved.mode == "TEXT_SELECTION_CHAT" and request.context.text_selection:
            selection = request.context.text_selection
            page = self.page_context_service.get_page_text(request.document_id, selection.page_number)
            surrounding = self._validate_selection(selection.selected_text, page.text)
            return ChatExecutionPlan(
                request=request,
                conversation_id=conversation_id,
                trace_id=trace_id,
                mode=resolved.mode,
                action="selection",
                kwargs={
                    "message": request.message,
                    "history": history,
                    "filename": metadata.original_filename,
                    "page_number": selection.page_number,
                    "selected_text": selection.selected_text,
                    "surrounding_text": surrounding,
                },
                citations=[self._citation(request.document_id, selection.page_number)],
                pages_used=[selection.page_number],
                confidence=resolved.confidence,
                image_used=False,
                conversation_document_id=request.document_id,
                document_version=document_version,
            )
<<<<<<< Updated upstream
=======
            page_number = selection.page_number
            return response, [self._citation(request.document_id, page_number)], [page_number], confidence, False, "answer"
>>>>>>> Stashed changes

        if resolved.mode == "VISUAL_REGION_CHAT" and request.context.visual_region:
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
            return ChatExecutionPlan(
                request=request,
                conversation_id=conversation_id,
                trace_id=trace_id,
                mode=resolved.mode,
                action="visual_region",
                kwargs={
                    "message": request.message,
                    "history": history,
                    "filename": metadata.original_filename,
                    "page_number": region.page_number,
                    "overlapping_text": overlapping_text,
                    "image_bytes": image_bytes,
                    "mime_type": mime_type,
                },
                citations=[self._citation(request.document_id, region.page_number)],
                pages_used=[region.page_number],
                confidence=resolved.confidence,
                image_used=True,
                conversation_document_id=request.document_id,
                document_version=document_version,
            )
<<<<<<< Updated upstream
=======
            page_number = region.page_number
            return response, [self._citation(request.document_id, page_number)], [page_number], confidence, True, "answer"
>>>>>>> Stashed changes

        if resolved.mode == "DOCUMENT_SEARCH_CHAT":
            return self._document_search_plan(
                request,
                conversation_id=conversation_id,
                trace_id=trace_id,
                history=history,
                filename=metadata.original_filename,
                document_version=document_version,
                visual_query=resolved.visual_query,
                exact_caption=resolved.exact_caption,
                confidence=resolved.confidence,
            )

        raise HTTPException(status_code=400, detail="Chế độ tương tác không hợp lệ.")

    async def _execute(self, plan: ChatExecutionPlan) -> tuple[ProviderResult, bool]:
        if plan.action == "general":
            return await self.answer_service.answer_general(**plan.kwargs)
        if plan.action == "page":
            return await self.answer_service.answer_page(**plan.kwargs)
        if plan.action == "selection":
            return await self.answer_service.answer_selection(**plan.kwargs)
        if plan.action == "visual_region":
            return await self.answer_service.answer_visual_region(**plan.kwargs)
        if plan.action == "document_search":
            return await self.answer_service.answer_document_search(**plan.kwargs)
        if plan.action == "document_visual_search":
            return await self.answer_service.answer_document_visual_search(**plan.kwargs)
        raise HTTPException(status_code=400, detail="Chế độ tương tác không hợp lệ.")

    async def _stream_execute(self, plan: ChatExecutionPlan) -> AsyncIterator[ProviderStreamChunk]:
        method_by_action = {
            "general": self.answer_service.stream_general,
            "page": self.answer_service.stream_page,
            "selection": self.answer_service.stream_selection,
            "visual_region": self.answer_service.stream_visual_region,
            "document_search": self.answer_service.stream_document_search,
            "document_visual_search": self.answer_service.stream_document_visual_search,
        }
        method = method_by_action.get(plan.action)
        if method is None:
            raise HTTPException(status_code=400, detail="Chế độ tương tác không hợp lệ.")
        async for chunk in method(**plan.kwargs):
            yield chunk

    def _document_search_plan(
        self,
        request: ChatRequestV2,
        *,
        conversation_id: str,
        trace_id: str,
        history,
        filename: str,
        document_version: int | None,
        visual_query: bool,
        exact_caption: str | None,
        confidence: float,
    ) -> ChatExecutionPlan:
        document_id = request.document_id
        assert document_id is not None
        caption_page = self._find_caption_page(document_id, exact_caption) if exact_caption else None
        results = self.retrieval_service.search(document_id, request.message, top_k=4)
        grounding_evidence = self._grounding_evidence(document_id, results)
        retrieval_confidence = max(
            (item.score for item in grounding_evidence),
            default=0.0,
        )

        if caption_page is None and self.grounding_service.should_abstain(
            grounding_evidence,
            request.answer_mode,
            retrieval_confidence,
        ):
            return self._abstention_response(), [], [], 0.0, False, "abstain"

        if visual_query:
            visual_results = self._limit_distinct_pages(results, 2)
            evidence = self._evidence(visual_results)
            page_number = caption_page or self._first_result_page(visual_results)
            if page_number:
                page = self.page_context_service.get_page_text(document_id, page_number)
                image_path = self.visual_context_service.render_page(document_id, page_number)
                image_bytes, mime_type = self._read_image(image_path)
<<<<<<< Updated upstream
=======
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
                verification_evidence = list(grounding_evidence)
                if not any(item.page_number == page_number for item in verification_evidence):
                    verification_evidence.insert(
                        0,
                        Evidence(
                            evidence_id=f"page:{document_id}:{page_number}",
                            document_id=document_id,
                            document_version=1,
                            page_number=page_number,
                            text=page.text or "Bằng chứng hình ảnh từ trang PDF.",
                            source_type="page",
                            score=1.0,
                        ),
                    )
                result, _ = response
                if self._verification_failed(
                    result.text,
                    verification_evidence,
                    request.answer_mode,
                ):
                    return self._abstention_response(), [], [], 0.0, False, "abstain"
>>>>>>> Stashed changes
                citations = self._citations_from_results(document_id, visual_results)
                if not any(item.page_number == page_number for item in citations):
                    citations.insert(0, self._citation(document_id, page_number))
                pages = list(dict.fromkeys([page_number, *[item.page_number for item in citations if item.page_number]]))
<<<<<<< Updated upstream
                return ChatExecutionPlan(
                    request=request,
                    conversation_id=conversation_id,
                    trace_id=trace_id,
                    mode="DOCUMENT_SEARCH_CHAT",
                    action="document_visual_search",
                    kwargs={
                        "message": request.message,
                        "history": history,
                        "filename": filename,
                        "page_number": page_number,
                        "page_text": page.text,
                        "extra_evidence": evidence,
                        "image_bytes": image_bytes,
                        "mime_type": mime_type,
                    },
                    citations=citations,
                    pages_used=pages,
                    confidence=confidence,
                    image_used=True,
                    conversation_document_id=document_id,
                    document_version=document_version,
                )

        citations = self._citations_from_results(document_id, results)
        pages = list(dict.fromkeys(item.page_number for item in citations if item.page_number))
        return ChatExecutionPlan(
            request=request,
            conversation_id=conversation_id,
            trace_id=trace_id,
            mode="DOCUMENT_SEARCH_CHAT",
            action="document_search",
            kwargs={
                "message": request.message,
                "history": history,
                "filename": filename,
                "evidence_text": self._evidence(results) or "Không tìm thấy bằng chứng phù hợp trong tài liệu.",
            },
            citations=citations,
            pages_used=pages,
            confidence=confidence if results else 0.25,
            image_used=False,
            conversation_document_id=document_id,
            document_version=document_version,
        )

    def _save_success(self, plan: ChatExecutionPlan, answer: str, trace: TraceInfo) -> None:
        self.conversation_repository.ensure_conversation(
            plan.conversation_id,
            plan.conversation_document_id,
            plan.document_version,
        )
        self.conversation_repository.add_message(plan.conversation_id, "user", plan.request.message)
        self.conversation_repository.add_message(
            plan.conversation_id,
            "assistant",
            answer,
            [citation.model_dump() for citation in plan.citations],
            trace.model_dump(),
        )

    def _trace(
        self,
        plan: ChatExecutionPlan,
        provider: str,
        model: str,
        fallback_used: bool,
        started_at: float,
    ) -> TraceInfo:
        return TraceInfo(
            trace_id=plan.trace_id,
            intent=plan.mode,
            pages_used=plan.pages_used,
            provider=provider,
            model=model,
            fallback=fallback_used,
            latency_ms={"total": round((time.perf_counter() - started_at) * 1000, 2)},
            confidence=plan.confidence,
            image_used=plan.image_used,
        )

    @staticmethod
    def _provider_http_error(exc: ProviderConfigurationError, image_used: bool) -> HTTPException:
        detail = (
            "Chưa cấu hình API key cho chức năng đọc hình ảnh."
            if image_used
            else "Chưa cấu hình API key cho chatbot."
        )
        return HTTPException(status_code=503, detail=detail)
=======
                return response, citations, pages, confidence, True, "answer"

        response = await self.answer_service.answer_document_search(
            message=request.message,
            history=request.history,
            filename=filename,
            evidence_text=self._evidence(results) or "Không tìm thấy bằng chứng phù hợp trong tài liệu.",
        )
        result, _ = response
        if self._verification_failed(
            result.text,
            grounding_evidence,
            request.answer_mode,
        ):
            return self._abstention_response(), [], [], 0.0, False, "abstain"
        citations = self._citations_from_results(document_id, results)
        pages = list(dict.fromkeys(item.page_number for item in citations if item.page_number))
        return response, citations, pages, confidence if results else 0.25, False, "answer"
>>>>>>> Stashed changes

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
    def _grounding_evidence(
        document_id: str,
        results: list[RetrievalResult],
    ) -> list[Evidence]:
        evidence: list[Evidence] = []
        for index, item in enumerate(results):
            text = str(item.chunk.get("text", "")).strip()
            if not text:
                continue
            chunk_id = item.chunk.get("chunk_id")
            page_number = item.chunk.get("page_number")
            evidence.append(
                Evidence(
                    evidence_id=str(chunk_id or f"retrieval:{document_id}:{index}"),
                    document_id=document_id,
                    document_version=int(item.chunk.get("document_version", 1)),
                    page_number=int(page_number) if page_number is not None else None,
                    text=text,
                    source_type="retrieval",
                    chunk_id=str(chunk_id) if chunk_id is not None else None,
                    section_id=item.chunk.get("section_id"),
                    heading=item.chunk.get("heading"),
                    score=float(item.score),
                )
            )
        return evidence

    @staticmethod
    def _abstention_response() -> tuple[ProviderResult, bool]:
        return (
            ProviderResult(
                text=(
                    "Mình chưa tìm thấy bằng chứng đủ liên quan trong tài liệu để trả lời "
                    "đáng tin cậy. Bạn có thể nêu rõ từ khóa, mục hoặc trang cần tìm."
                ),
                provider="system",
                model="conditional-gate-v1",
            ),
            False,
        )

    def _verification_failed(
        self,
        answer: str,
        evidence: list[Evidence],
        answer_mode: str,
    ) -> bool:
        if not settings.verifier_enabled:
            return False
        verification = self.grounding_service.verify(answer, evidence, answer_mode)
        return not bool(verification.get("valid"))

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
