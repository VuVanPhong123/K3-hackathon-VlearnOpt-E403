import os

import pytest


@pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason="OPENAI_API_KEY is not configured")
def test_live_openai_key_present() -> None:
    assert os.getenv("OPENAI_API_KEY")
