from __future__ import annotations

import re

from app.domain.context import ResolvedContext
from app.domain.evidence import Evidence
from app.repositories.chunk_repository import ChunkRepository
from app.repositories.document_repository import DocumentRepository
from app.schemas import ChatRequestV2
from app.services.retrieval_service import RetrievalService
from app.services.text_utils import snippet


class ContextResolver:
    def __init__(
        self,
        document_repository: DocumentRepository | None = None,
        chunk_repository: ChunkRepository | None = None,
        retrieval_service: RetrievalService | None = None,
    ) -> None:
        self.document_repository = document_repository or DocumentRepository()
        self.chunk_repository = chunk_repository or ChunkRepository()
        self.retrieval_service = retrieval_service or RetrievalService(self.chunk_repository)

    def resolve(self, request: ChatRequestV2) -> ResolvedContext:
        if request.context.text_selection and request.context.text_selection.selected_text.strip():
            selection = request.context.text_selection
            return ResolvedContext(
                route_hint="text_selection",
                evidence=[
                    Evidence(
                        evidence_id=f"selection:p{selection.page_number}",
                        document_id=request.document_id,
                        document_version=1,
                        page_number=selection.page_number,
                        text=selection.selected_text,
                        source_type="text_selection",
                    )
                ],
                pages_used=[selection.page_number],
                confidence=0.96,
            )
        if request.context.visual_region:
            visual = request.context.visual_region
            page = self.document_repository.get_page(request.document_id or "", visual.page_number) if request.document_id else None
            page_text = page["raw_text"] if page else ""
            return ResolvedContext(
                route_hint="visual_region",
                evidence=[
                    Evidence(
                        evidence_id=f"visual:p{visual.page_number}",
                        document_id=request.document_id,
                        document_version=1,
                        page_number=visual.page_number,
                        text=page_text or "Visual region selected. Text extraction is unavailable for this region.",
                        source_type="visual_region",
                        metadata={"bbox": visual.bbox.model_dump()},
                    )
                ],
                pages_used=[visual.page_number],
                needs_vision=True,
                confidence=0.74 if page_text else 0.42,
            )
        explicit_pages = self._attached_or_mentioned_pages(request)
        if explicit_pages and request.document_id:
            evidence = []
            for page_number in explicit_pages[:3]:
                page = self.document_repository.get_page(request.document_id, page_number)
                if page:
                    evidence.append(
                        Evidence(
                            evidence_id=f"page:p{page_number}",
                            document_id=request.document_id,
                            document_version=page["document_version"],
                            page_number=page_number,
                            text=page["raw_text"] or "This page has little extractable text and may require vision.",
                            source_type="page",
                            score=0.9 if page["raw_text"] else 0.35,
                        )
                    )
            if evidence:
                return ResolvedContext(
                    route_hint="exact_page",
                    evidence=evidence,
                    pages_used=explicit_pages[:3],
                    needs_vision=any(item.text.startswith("This page has little") for item in evidence),
                    confidence=max(item.score for item in evidence),
                )
        if request.context.active_page and request.document_id:
            page = self.document_repository.get_page(request.document_id, request.context.active_page)
            if page:
                return ResolvedContext(
                    route_hint="active_page",
                    evidence=[
                        Evidence(
                            evidence_id=f"active:p{request.context.active_page}",
                            document_id=request.document_id,
                            document_version=page["document_version"],
                            page_number=request.context.active_page,
                            text=page["raw_text"],
                            source_type="active_page",
                        )
                    ],
                    pages_used=[request.context.active_page],
                    confidence=0.72,
                )
        if request.document_id:
            results = self.retrieval_service.search(request.document_id, request.message)
            evidence = [
                Evidence(
                    evidence_id=result.chunk["chunk_id"],
                    document_id=request.document_id,
                    document_version=result.chunk["document_version"],
                    page_number=result.chunk["page_number"],
                    text=result.chunk["text"],
                    source_type="retrieval",
                    chunk_id=result.chunk["chunk_id"],
                    section_id=result.chunk.get("section_id"),
                    heading=result.chunk.get("heading"),
                    score=result.score,
                    metadata={"debug": result.debug},
                )
                for result in results
            ]
            return ResolvedContext(
                route_hint="retrieval",
                evidence=evidence,
                pages_used=sorted({item.page_number for item in evidence if item.page_number}),
                needs_retrieval=True,
                confidence=max([item.score for item in evidence], default=0.0),
            )
        return ResolvedContext(route_hint="general", evidence=[], pages_used=[], confidence=0.0)

    @staticmethod
    def _attached_or_mentioned_pages(request: ChatRequestV2) -> list[int]:
        pages = [page for page in request.context.attached_pages if page > 0]
        if pages:
            return pages
        mentioned = [int(match) for match in re.findall(r"trang\s*(\d+)", request.message.lower())]
        return mentioned
