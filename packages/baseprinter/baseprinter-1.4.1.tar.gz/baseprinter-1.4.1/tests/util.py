import pytest

import os


def skip_if_jats_off():
    return pytest.mark.skipif(
        os.getenv("BASEPRINTER_JATS") == "OFF",
        reason="JATS mode is OFF"
    )
