from app.domain.citations import citations_from_evidence
from app.domain.evidence import Evidence


def test_citations_from_evidence_deduplicates() -> None:
    evidence = [
        Evidence("e1", "d1", 1, 4, "text", "page", chunk_id="c1"),
        Evidence("e1", "d1", 1, 4, "text", "page", chunk_id="c1"),
    ]
    citations = citations_from_evidence(evidence)
    assert len(citations) == 1
    assert citations[0].page_number == 4
