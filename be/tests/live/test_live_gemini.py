import os

import pytest


@pytest.mark.skipif(not os.getenv("GEMINI_API_KEY"), reason="GEMINI_API_KEY is not configured")
def test_live_gemini_key_present() -> None:
    assert os.getenv("GEMINI_API_KEY")
