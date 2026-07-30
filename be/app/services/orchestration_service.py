from __future__ import annotations

import logging
import time
import uuid

from app.domain.citations import citations_from_evidence
from app.domain.evidence import Evidence
from app.domain.intents import Intent
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.document_repository import DocumentRepository
from app.schemas import ChatRequestV2, ChatResponseV2, TraceInfo
from app.services.answer_service import AnswerService
from app.services.context_resolver import ContextResolver
from app.services.conversation_service import ConversationService
from app.services.grounding_service import GroundingService
from app.services.intent_router import IntentRouter
from app.services.query_planner import QueryPlanner
from app.services.summary_service import SummaryService
from app.services.visual_context_service import VisualContextService

logger = logging.getLogger(__name__)


class OrchestrationService:
    def __init__(self) -> None:
        self.document_repository = DocumentRepository()
        self.conversation_repository = ConversationRepository()
        self.conversation_service = ConversationService(self.conversation_repository)
        self.intent_router = IntentRouter()
        self.query_planner = QueryPlanner()
        self.context_resolver = ContextResolver(self.document_repository)
        self.summary_service = SummaryService(self.document_repository)
        self.answer_service = AnswerService()
        self.grounding_service = GroundingService()
        self.visual_service = VisualContextService()

    async def chat(self, request: ChatRequestV2) -> ChatResponseV2:
        trace_id = str(uuid.uuid4())
        timings: dict[str, float] = {}
        total_start = time.perf_counter()
        conversation_id = self.conversation_service.conversation_id(request.conversation_id)
        document = self.document_repository.get_document(request.document_id) if request.document_id else None
        self.conversation_repository.ensure_conversation(
            conversation_id,
            request.document_id,
            document.version if document else None,
        )
        self.conversation_repository.add_message(conversation_id, "user", request.message)

        start = time.perf_counter()
        intent, route_confidence = self.intent_router.route(request)
        timings["router"] = self._elapsed_ms(start)

        evidence: list[Evidence]
        pages_used: list[int]
        if intent == Intent.SUMMARY and request.document_id:
            start = time.perf_counter()
            summary_type = self._summary_type(request)
            summary = self.summary_service.summarize(request.document_id, summary_type)
            timings["summary"] = self._elapsed_ms(start)
            answer = summary["answer"]
            citations = [citation for citation in summary["citations"]]
            pages_used = sorted(
                {
                    page
                    for citation in citations
                    for page in range(citation.get("page_start") or 0, (citation.get("page_end") or 0) + 1)
                    if page > 0
                }
            )
            confidence = 0.9 if summary["coverage"] else 0.3
            trace = TraceInfo(
                trace_id=trace_id,
                intent=intent.value,
                pages_used=pages_used,
                provider="deterministic",
                model="hierarchical-summary-v1",
                fallback=False,
                latency_ms={**timings, "total": self._elapsed_ms(total_start)},
                confidence=confidence,
            )
            self.conversation_repository.add_message(conversation_id, "assistant", answer, citations, trace.model_dump())
            return ChatResponseV2(
                answer=answer,
                citations=citations,
                confidence=confidence,
                conversation_id=conversation_id,
                trace=trace,
            )

        start = time.perf_counter()
        resolved = self.context_resolver.resolve(request)
        timings["context"] = self._elapsed_ms(start)
        evidence = resolved.evidence
        pages_used = resolved.pages_used
        if resolved.needs_vision and request.context.visual_region and request.document_id:
            start = time.perf_counter()
            try:
                crop = self.visual_service.render_crop(
                    request.document_id,
                    request.context.visual_region.page_number,
                    request.context.visual_region.bbox,
                )
                if evidence:
                    evidence[0].metadata["crop_path"] = str(crop)
            except Exception:
                pass
            timings["visual"] = self._elapsed_ms(start)

        if request.document_id and document and document.status not in {"READY", "NEEDS_INDEX"} and not evidence:
            answer = "Tai lieu dang duoc xu ly. Hay doi den khi trang thai READY roi hoi lai."
            confidence = 0.2
            citations = []
            trace = TraceInfo(
                trace_id=trace_id,
                intent=intent.value,
                pages_used=[],
                provider="deterministic",
                model="status-guard",
                fallback=False,
                latency_ms={**timings, "total": self._elapsed_ms(total_start)},
                confidence=confidence,
            )
            return ChatResponseV2(
                answer=answer,
                citations=citations,
                confidence=confidence,
                abstained=True,
                conversation_id=conversation_id,
                trace=trace,
            )

        if self.grounding_service.should_abstain(evidence, request.answer_mode, resolved.confidence):
            answer = "Minh chua tim thay du can cu trong tai lieu de tra loi cau nay."
            provider, model, fallback = "deterministic", "abstention-rule", False
        else:
            start = time.perf_counter()
            answer, provider, model, fallback = await self.answer_service.compose(
                message=request.message,
                intent=intent,
                evidence=evidence,
                answer_mode=request.answer_mode,
            )
            timings["answer"] = self._elapsed_ms(start)

        verification = self.grounding_service.verify(answer, evidence, request.answer_mode)
        confidence = max(route_confidence * 0.4, verification["confidence"], resolved.confidence)
        citations = citations_from_evidence(evidence)
        trace = TraceInfo(
            trace_id=trace_id,
            intent=intent.value,
            pages_used=pages_used,
            provider=provider,
            model=model,
            fallback=fallback,
            latency_ms={**timings, "total": self._elapsed_ms(total_start)},
            confidence=confidence,
        )
        debug = {
            "route_hint": resolved.route_hint,
            "evidence_ids": [item.evidence_id for item in evidence],
            "verification": verification,
        }
        response = ChatResponseV2(
            answer=answer,
            citations=citations,
            confidence=confidence,
            needs_clarification=intent == Intent.CLARIFY,
            abstained=not verification["valid"],
            conversation_id=conversation_id,
            trace=trace,
            debug=debug,
        )
        self.conversation_repository.add_message(
            conversation_id,
            "assistant",
            answer,
            [citation.model_dump() for citation in citations],
            trace.model_dump(),
        )
        logger.info(
            "v2_chat trace_id=%s intent=%s document_id=%s pages=%s evidence=%s provider=%s fallback=%s total_ms=%.1f",
            trace_id,
            intent.value,
            request.document_id,
            pages_used,
            len(evidence),
            provider,
            fallback,
            trace.latency_ms.get("total", 0.0),
        )
        return response

    @staticmethod
    def _elapsed_ms(start: float) -> float:
        return round((time.perf_counter() - start) * 1000, 2)

    @staticmethod
    def _summary_type(request: ChatRequestV2) -> str:
        if request.requested_output in {"short", "detailed", "outline", "key_concepts", "learning_objectives"}:
            return request.requested_output
        message = request.message.lower()
        if "outline" in message or "de cuong" in message:
            return "outline"
        if "key" in message or "khai niem" in message:
            return "key_concepts"
        if "muc tieu" in message:
            return "learning_objectives"
        return "short"
