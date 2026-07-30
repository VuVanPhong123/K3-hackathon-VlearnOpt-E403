from app.services.intent_router import IntentRouter
from app.schemas import ChatRequestV2
from app.domain.intents import Intent


def test_chat_v2_summary_route() -> None:
    assert IntentRouter().route(ChatRequestV2(message="tom tat toan bo tai lieu", document_id="d1"))[0] == Intent.SUMMARY
