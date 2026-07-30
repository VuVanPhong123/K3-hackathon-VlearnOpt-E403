from app.domain.intents import Intent
from app.schemas import BBox, ChatContextV2, ChatRequestV2, VisualRegion
from app.services.intent_router import IntentRouter


def test_chat_v2_visual_route() -> None:
    request = ChatRequestV2(
        message="giai thich hinh",
        context=ChatContextV2(visual_region=VisualRegion(page_number=6, bbox=BBox(x=0.1, y=0.1, width=0.5, height=0.3))),
    )
    assert IntentRouter().route(request)[0] == Intent.VISUAL_QA
