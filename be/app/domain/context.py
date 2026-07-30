from dataclasses import dataclass, field

from app.domain.evidence import Evidence


@dataclass
class ResolvedContext:
    route_hint: str
    evidence: list[Evidence] = field(default_factory=list)
    pages_used: list[int] = field(default_factory=list)
    needs_vision: bool = False
    needs_retrieval: bool = False
    confidence: float = 0.0
