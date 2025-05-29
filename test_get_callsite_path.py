import inspect
import re
from types import SimpleNamespace

import pytest

from alternative import get_caller_path

MODULE = __name__
FALLBACK = "<unknown module>.<unknown> (<unknown location>)"


def test_callsite_normal(request: pytest.FixtureRequest):
    """A reasonable level of depth information is returned, as well as the line number."""

    def level1():
        def level2():
            return get_caller_path()

        return level2()

    path = level1()
    assert path is not None
    func_name = request.node.originalname

    # Should start with MODULE.level1.<locals>.level2
    prefix = f"{MODULE}.{func_name}.<locals>.level1 ({__file__}"
    assert re.fullmatch(re.escape(prefix) + r":\d+\)", path)


def test_callsite_no_two_up(monkeypatch):
    """If the caller is not python, a default is returned."""
    # Create a fake frame with no .f_back or only one level
    fake_frame_top = SimpleNamespace(f_back=None)
    # Monkeypatch currentframe to return our fake
    monkeypatch.setattr(inspect, "currentframe", lambda: fake_frame_top)

    path = get_caller_path()
    assert path == FALLBACK
