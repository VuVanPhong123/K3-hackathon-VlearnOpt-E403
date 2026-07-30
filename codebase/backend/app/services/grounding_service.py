from __future__ import annotations

from app.domain.evidence import Evidence
from app.services.text_utils import contains_prompt_injection


class GroundingService:
    def verify(self, answer: str, evidence: list[Evidence], answer_mode: str) -> dict:
        if not answer.strip():
            return {"valid": False, "confidence": 0.0, "reason": "empty_answer"}
        if contains_prompt_injection(answer):
            return {"valid": False, "confidence": 0.0, "reason": "prompt_injection_echo"}
        if answer_mode == "document_only" and not evidence:
            return {"valid": False, "confidence": 0.0, "reason": "no_evidence"}
        page_count = len({item.page_number for item in evidence if item.page_number})
        confidence = min(0.95, 0.35 + 0.18 * len(evidence) + 0.08 * page_count)
        return {"valid": True, "confidence": confidence, "reason": "ok"}

    def should_abstain(self, evidence: list[Evidence], answer_mode: str, confidence: float) -> bool:
        return answer_mode == "document_only" and (not evidence or confidence < 0.2)
