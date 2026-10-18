import inspect
import re
import sys
from types import SimpleNamespace

import pytest

from alternative import _get_caller_path

MODULE = __name__
FALLBACK = "<unknown module>.<unknown> (<unknown location>)"


def test_callsite_normal(request: pytest.FixtureRequest):
    """A reasonable level of depth information is returned, as well as the line number."""

    def level1():
        def level2():
            return _get_caller_path()

        return level2()

    path = level1()
    assert path is not None
    func_name = request.node.originalname

    # Code objects acquired qualified names in Python 3.11.
    caller_name = (
        f"{func_name}.<locals>.level1" if sys.version_info >= (3, 11) else "level1"
    )
    prefix = f"{MODULE}.{caller_name} ({__file__}"
    assert re.fullmatch(re.escape(prefix) + r":\d+\)", path)


def test_callsite_no_two_up(monkeypatch):
    """If the caller is not python, a default is returned."""
    # Create a fake frame with no .f_back or only one level
    fake_frame_top = SimpleNamespace(f_back=None)
    # Monkeypatch currentframe to return our fake
    monkeypatch.setattr(inspect, "currentframe", lambda: fake_frame_top)

    path = _get_caller_path()
    assert path == FALLBACK
