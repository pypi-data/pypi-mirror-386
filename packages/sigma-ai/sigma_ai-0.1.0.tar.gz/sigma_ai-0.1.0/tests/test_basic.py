import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

import main


def test_probe():
    data = main.probe()
    assert data["ok"] is True
    assert "python" in data
    assert "platform" in data
