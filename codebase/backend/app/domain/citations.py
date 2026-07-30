from app.domain.evidence import Evidence
from app.schemas import Citation


def citations_from_evidence(evidence: list[Evidence]) -> list[Citation]:
    seen: set[tuple[str | None, int | None, str | None]] = set()
    citations: list[Citation] = []
    for item in evidence:
        key = (item.document_id, item.page_number, item.chunk_id)
        if key in seen:
            continue
        seen.add(key)
        citations.append(
            Citation(
                document_id=item.document_id,
                page_number=item.page_number,
                page_start=item.page_number,
                page_end=item.page_number,
                chunk_id=item.chunk_id,
                section_id=item.section_id,
                label=f"Page {item.page_number}" if item.page_number else item.source_type,
            )
        )
    return citations
