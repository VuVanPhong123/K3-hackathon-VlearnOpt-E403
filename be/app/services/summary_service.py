from __future__ import annotations

from app.domain.evidence import Evidence
from app.repositories.chunk_repository import ChunkRepository
from app.repositories.document_repository import DocumentRepository
from app.repositories.summary_repository import SummaryRepository
from app.schemas import Citation
from app.services.text_utils import snippet


class SummaryService:
    def __init__(
        self,
        document_repository: DocumentRepository | None = None,
        chunk_repository: ChunkRepository | None = None,
        summary_repository: SummaryRepository | None = None,
    ) -> None:
        self.document_repository = document_repository or DocumentRepository()
        self.chunk_repository = chunk_repository or ChunkRepository()
        self.summary_repository = summary_repository or SummaryRepository()

    def summarize(self, document_id: str, summary_type: str = "short", language: str = "vi") -> dict:
        metadata = self.document_repository.get_document(document_id)
        if not metadata:
            raise ValueError("Document not found")
        cache_key = self.summary_repository.cache_key(
            document_id, metadata.checksum_sha256, metadata.version, summary_type, language
        )
        cached = self.summary_repository.get_summary(cache_key)
        if cached:
            return cached
        sections = self.document_repository.list_sections(document_id)
        chunks = self.chunk_repository.list_chunks(document_id)
        section_summaries = []
        citations = []
        for section in sections:
            section_chunks = [
                chunk
                for chunk in chunks
                if section["start_page"] <= chunk["page_number"] <= section["end_page"]
            ]
            combined = " ".join(chunk["text"] for chunk in section_chunks)
            if not combined:
                continue
            section_summaries.append(
                f"- {section['title']} (trang {section['start_page']}-{section['end_page']}): {snippet(combined, 420)}"
            )
            citations.append(
                {
                    "document_id": document_id,
                    "page_start": section["start_page"],
                    "page_end": section["end_page"],
                    "section_id": section["section_id"],
                    "label": section["title"],
                }
            )
        if summary_type == "outline":
            answer = "\n".join(section_summaries)
        elif summary_type == "key_concepts":
            answer = "Cac y chinh:\n" + "\n".join(section_summaries[:8])
        elif summary_type == "learning_objectives":
            answer = "Muc tieu hoc tap co the rut ra:\n" + "\n".join(section_summaries[:6])
        else:
            answer = "Tom tat tai lieu:\n" + "\n".join(section_summaries)
        coverage = [
            {
                "section_id": section["section_id"],
                "start_page": section["start_page"],
                "end_page": section["end_page"],
                "covered": True,
            }
            for section in sections
        ]
        self.summary_repository.save_summary(
            cache_key=cache_key,
            document_id=document_id,
            document_version=metadata.version,
            checksum_sha256=metadata.checksum_sha256,
            summary_type=summary_type,
            language=language,
            answer=answer,
            citations=citations,
            coverage=coverage,
        )
        return {
            "cache_key": cache_key,
            "document_id": document_id,
            "document_version": metadata.version,
            "checksum_sha256": metadata.checksum_sha256,
            "summary_type": summary_type,
            "language": language,
            "answer": answer,
            "citations": citations,
            "coverage": coverage,
        }

    def evidence_for_summary(self, document_id: str, summary_type: str = "short") -> list[Evidence]:
        summary = self.summarize(document_id, summary_type)
        return [
            Evidence(
                evidence_id=f"summary:{citation.get('section_id')}",
                document_id=document_id,
                document_version=summary["document_version"],
                page_number=citation.get("page_start"),
                text=summary["answer"],
                source_type="summary",
                section_id=citation.get("section_id"),
            )
            for citation in summary["citations"]
        ]
