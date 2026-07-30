from app.domain.evidence import Evidence
from app.services.grounding_service import GroundingService


def test_document_only_requires_evidence() -> None:
    verifier = GroundingService()
    result = verifier.verify("answer", [], "document_only")
    assert result["valid"] is False


def test_grounded_answer_valid() -> None:
    verifier = GroundingService()
    result = verifier.verify("answer", [Evidence("e", "d", 1, 1, "text", "page")], "document_only")
    assert result["valid"] is True
