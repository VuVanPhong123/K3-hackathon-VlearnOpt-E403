from app.domain.intents import Intent
from app.schemas import ChatContextV2, ChatRequestV2, VisualRegion, BBox
from app.services.intent_router import IntentRouter


def test_summary_intent() -> None:
    intent, confidence = IntentRouter().route(ChatRequestV2(message="tom tat tai lieu", context=ChatContextV2()))
    assert intent == Intent.SUMMARY
    assert confidence > 0.8


def test_visual_context_wins() -> None:
    request = ChatRequestV2(
        message="giai thich cai nay",
        context=ChatContextV2(visual_region=VisualRegion(page_number=2, bbox=BBox(x=0.1, y=0.1, width=0.4, height=0.3))),
    )
    assert IntentRouter().route(request)[0] == Intent.VISUAL_QA
