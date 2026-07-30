from dataclasses import dataclass, field


@dataclass(frozen=True)
class Evidence:
    evidence_id: str
    document_id: str | None
    document_version: int
    page_number: int | None
    text: str
    source_type: str
    chunk_id: str | None = None
    section_id: str | None = None
    heading: str | None = None
    score: float = 1.0
    metadata: dict = field(default_factory=dict)
