from pydantic import ValidationError

from app.schemas import BBox, TextSelection


def test_bbox_validation_rejects_negative() -> None:
    try:
      BBox(x=-0.1, y=0, width=0.2, height=0.2)
    except ValidationError:
      return
    raise AssertionError("negative bbox should fail")


def test_selection_limits_text_length() -> None:
    selection = TextSelection(page_number=1, selected_text="x" * 6000)
    assert len(selection.selected_text) == 6000
