from app.schemas import ChatContextV2, ChatRequestV2, TextSelection
from app.services.context_resolver import ContextResolver


def test_text_selection_has_priority() -> None:
    request = ChatRequestV2(
        message="Giải thích trang này",
        document_id="00000000-0000-0000-0000-000000000001",
        context=ChatContextV2(
            active_page=20,
            attached_pages=[5],
            text_selection=TextSelection(page_number=3, selected_text="selected evidence"),
        ),
    )
    resolved = ContextResolver().resolve(request)
    assert resolved.route_hint == "text_selection"
    assert resolved.pages_used == [3]
